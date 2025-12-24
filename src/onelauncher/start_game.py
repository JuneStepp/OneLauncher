import configparser
import logging
import os
import subprocess
import sys
from contextlib import suppress
from copy import deepcopy
from datetime import UTC, datetime
from functools import partial
from io import StringIO
from pathlib import Path
from types import MappingProxyType

import attrs
import trio

from onelauncher.async_utils import for_each_in_stream
from onelauncher.config_manager import ConfigManager
from onelauncher.game_launcher_local_config import GameLauncherLocalConfig
from onelauncher.game_utilities import get_game_user_preferences_path
from onelauncher.logs import ExternalProcessLogsFilter

from .game_config import ClientType, GameConfig, GameConfigID
from .network.game_launcher_config import GameLauncherConfig
from .network.world import World
from .resources import OneLauncherLocale
from .wine_environment import get_wine_process_args

logger = logging.getLogger(__name__)
logger.addFilter(ExternalProcessLogsFilter())


class MissingLaunchArgumentError(Exception):
    """Launch argument missing."""


async def get_launch_args(
    game_launcher_config: GameLauncherConfig,
    game_launcher_local_config: GameLauncherLocalConfig,
    game_config: GameConfig,
    default_locale: OneLauncherLocale,
    world: World,
    login_server: str,
    account_number: str,
    ticket: str,
) -> tuple[str, ...]:
    """
    Return complete client launch arguments based on
        client_launch_args_template.

    Raises:
        MissingLaunchArgumentError

    The game's launch arguments can be found by running the client with no arguments through WINE.
    As of 2024/07/10, the output for LOTRO is:
    ```text
            -a, --account       : <string>: Specifies the account name to logon with.
            --authserverurl : Auth server URL for refreshing the GLS ticket.
            --chatserver    : Specify the chat server to use.
            --connspeed     : <0.0-640.0>:Connection speed in Kilobits/sec for the server-client connection. 0 Defaults to speed searching
        -r, --create        : <name> : Character Name you would like to create/play
            --cwd           : Cause the client to change to the specified directory on startup.
            --debug         : <32 bitfield>: Controls what kinds of debug outputs are enabled.
        -f, --franchise     : <string>: Specifies the franchise name.
            --gametype      : <string> : Specifies the game type used for supporturl and supportserviceurl.
            --glsticket     : Load gls ticket data from specified registry key.
        -z, --glsticketdirect: <string>: Specify ticket data.
            --glsticketlifetime: The lifetime of GLS tickets.
            --HighResOutOfDate: Tells the client that the high resolution texture dat file was not updated. We will not switch into very high texture detail..
        -h, --host          : [host/IP]:Specifies where to find the server to talk to.
            --keymap        : <file> : Base file for the keymap.  Will also look for <filename>c.extension and <filename>s.extension for meta keys
            --language      : <string>: Language to run the client in.
            --loadfile      : <file> : Specify a loadfile for an autogen'd character to run on startup
        -m, --mps           : <monster play session>.wc : Monster Play Session to start with
            --outport       : <1-65535>: Specify the outgoing network port to use.
        -p, --port          : <1-65535>: Specify the server port to contact. See 'host'
            --prefs         : <string>: Specify the preferences file to use.
            --remotemouse   : Optimize for using a mouse over a remote connection.
            --resource-set  : <string>: A comma separated list of available resource sets. The last set is the default.
            --rodat         : noop. Left in for backward compatibility.
            --safe          : Force SAFE display settings.
        -s, --specify       : <race>,<class> : Race Class pair for a character you would like to create
            --surveyurl     : <url> : URL to use for quest surveys
            --usechat       : Specify that the client should connect to a chat server.
            --useexiturl    : launch a browser using an exit url
        -u, --user          : <name> : Character Name you would like to play
            --voicenetdelay : <int>: Specifies the voice network delay threshold in milliseconds.
            --voiceoff      : Disables the Voice chat system.
            --wfilelog      : <64-bitmask> : activates file logging for the specified weenie event types. Alternately, logtype enums separated by ',' are enummapped and or'ed together.
            --wprintlog     : <64-bitmask> : activates print logging for the specified weenie event types. Alternately, logtype enums separated by ',' are enummapped and or'ed together.
    ```

    A couple additional notes on these options:
    - When possible, the information from `GameLauncherConfig` should be used over hard
    coded values.
    - The `--prefs` option also changes the game settings directory to the parent folder
    of the provided user preferences file path.
    - The `--cwd` option doesn't seem to work. `os.chdir()` is still needed on Windows.

    """
    launch_args_template_mapping: dict[str, str | None] = {
        "{SUBSCRIPTION}": account_number,
        "{LOGIN}": login_server,
        "{GLS}": ticket,
        "{CHAT}": world.chat_server_url,
        "{LANG}": game_config.locale.game_language_name
        if game_config.locale
        else default_locale.game_language_name,
        "{CRASHRECEIVER}": game_launcher_config.client_crash_server_arg,
        "{UPLOADTHROTTLE}": game_launcher_config.client_default_upload_throttle_mbps_arg,
        "{BUGURL}": game_launcher_config.client_bug_url_arg,
        "{AUTHSERVERURL}": game_launcher_config.client_auth_server_arg,
        "{GLSTICKETLIFETIME}": game_launcher_config.client_gls_ticket_lifetime_arg,
        "{SUPPORTURL}": game_launcher_config.client_support_url_arg,
        "{SUPPORTSERVICEURL}": game_launcher_config.client_support_service_url_arg,
    }

    launch_args_template = game_launcher_config.client_launch_args_template
    for arg_key, arg_val in launch_args_template_mapping.items():
        if arg_key in launch_args_template:
            if arg_val is None:
                raise MissingLaunchArgumentError(
                    f"{arg_key} launch argument is in template, but has None value"
                )
            launch_args_template = launch_args_template.replace(arg_key, arg_val)

    if "{" in launch_args_template:
        raise MissingLaunchArgumentError(
            f"Template has unrecognized launch arguments: {launch_args_template}"
        )

    launch_args = launch_args_template.split(" ")

    # Tell the client that the high resolution texture dat file was not
    # updated. Client will not switch into high texture detail mode.
    if not game_config.high_res_enabled:
        launch_args.append(
            game_launcher_config.high_res_patch_arg or " --HighResOutOfDate"
        )

    # Setting the `--prefs` command configures both the game user preferences file and the
    # game settings folder. The game settings folder is set to the folder of the
    # user preferences file passed to `--prefs`.
    launch_args.extend(
        (
            "--prefs",
            str(
                get_game_user_preferences_path(
                    game_config=game_config,
                    game_launcher_local_config=game_launcher_local_config,
                )
            ),
        )
    )

    redacted_launch_args = tuple(
        arg.replace(account_number, "******").replace(ticket, "******")
        for arg in launch_args
    )
    logger.debug("Game launch arguments generated: %s", redacted_launch_args)
    return tuple(launch_args)


async def update_game_user_preferences(
    game_config: GameConfig, game_launcher_local_config: GameLauncherLocalConfig
) -> None:
    """
    Set important `UserPreferences.ini` values.
    """
    if sys.platform == "win32":
        return

    game_user_preferences_path = trio.Path(  # type: ignore[unreachable,unused-ignore]
        get_game_user_preferences_path(
            game_config=game_config,
            game_launcher_local_config=game_launcher_local_config,
        )
    )
    config = configparser.ConfigParser(delimiters=("=",))
    with suppress(FileNotFoundError):
        config.read_string(await game_user_preferences_path.read_text())
    unedited_config = deepcopy(config)

    # Set screen mode to `FullScreenWindowed` on macOS on first game launch.
    # The default `Fullscreen` mode bloacks the macOS prompt for allowing required game
    # permissions. It also causes issues with some Macintosh monitors and laptop screens,
    # especially when using multiple monitors.
    if sys.platform == "darwin" and game_config.last_played is None:
        with suppress(configparser.DuplicateSectionError):
            config.add_section("Display")
        config["Display"]["FullScreen"] = "False"
        config["Display"]["ScreenMode"] = "FullScreenWindowed"

    if game_config.wine.builtin_prefix_enabled and (
        sys.platform == "darwin" or "Render" not in config
    ):
        with suppress(configparser.DuplicateSectionError):
            config.add_section("Render")
        config["Render"]["D3DVersionPromptedForAtStartup"] = "11"
        config["Render"]["GraphicsCore"] = "D3D11"

    if config == unedited_config:
        return
    with StringIO() as string_io:
        config.write(string_io, space_around_delimiters=False)
        string_io.seek(0)
        await game_user_preferences_path.write_text(string_io.read())


async def start_game(
    config_manager: ConfigManager,
    game_id: GameConfigID,
    game_launcher_config: GameLauncherConfig,
    game_launcher_local_config: GameLauncherLocalConfig,
    world: World,
    login_server: str,
    account_number: str,
    ticket: str,
) -> int:
    """
    Raises:
        MissingLaunchArgumentError
        OSError: Error encountered starting or communicating with the process
    """
    # This must be called before `game_config.last_played` is updated.
    await update_game_user_preferences(
        game_config=config_manager.get_game_config(game_id),
        game_launcher_local_config=game_launcher_local_config,
    )

    # Game was last played right now.
    config_manager.update_game_config_file(
        game_id=game_id,
        config=attrs.evolve(
            config_manager.read_game_config_file(game_id),
            last_played=datetime.now(UTC),
        ),
    )
    game_config = config_manager.get_game_config(game_id)

    launch_args = await get_launch_args(
        game_launcher_config=game_launcher_config,
        game_launcher_local_config=game_launcher_local_config,
        game_config=game_config,
        default_locale=config_manager.get_program_config().default_locale,
        world=world,
        login_server=login_server,
        account_number=account_number,
        ticket=ticket,
    )
    client_filename, client_type = game_launcher_config.get_client_filename(
        game_config.client_type
    )
    # Fix binary path for 64-bit client.
    if client_type == ClientType.WIN64:
        client_relative_path = Path("x64") / client_filename
    else:
        client_relative_path = Path(client_filename)

    command: tuple[str | Path, ...] = (
        game_config.game_directory / client_relative_path,
        *launch_args,
    )
    environment = MappingProxyType(os.environ.copy() | game_config.environment)
    if os.name != "nt":
        command, environment = get_wine_process_args(
            command=command, environment=environment, wine_config=game_config.wine
        )

    async with trio.open_nursery() as nursery:
        process: trio.Process = await nursery.start(
            partial(
                trio.run_process,
                command,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environment,
                cwd=game_config.game_directory,
            )
        )
        process_logging_adapter = logging.LoggerAdapter(logger)
        process_logging_adapter.extra = {
            ExternalProcessLogsFilter.EXTERNAL_PROCESS_ID_KEY: process.pid
        }
        if process.stdout is None or process.stderr is None:
            raise TypeError("Process pipe is `None`")
        nursery.start_soon(
            partial(for_each_in_stream, process.stdout, process_logging_adapter.debug)
        )
        nursery.start_soon(
            partial(for_each_in_stream, process.stderr, process_logging_adapter.warning)
        )
        return await process.wait()
