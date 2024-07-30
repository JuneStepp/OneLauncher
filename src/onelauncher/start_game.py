import logging
import os
from pathlib import Path

from PySide6 import QtCore

from onelauncher.game_launcher_local_config import GameLauncherLocalConfig
from onelauncher.game_utilities import get_game_settings_dir

from .game_config import ClientType, GameConfig
from .network.game_launcher_config import GameLauncherConfig
from .network.world import World
from .resources import OneLauncherLocale
from .wine_environment import edit_qprocess_to_use_wine

logger = logging.getLogger("main")


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
) -> list[str]:
    """
    Return complete client launch arguments based on
        client_launch_args_template.

    Raises:
        MissingLaunchArgumentError

    The game's launch arguents can be found by running the client with no arguments through WINE.
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
            --wfilelog      : <64-bitmask> : activates file logging for the specified weenie event types. Alternately, logtype enums seperated by ',' are enummapped and or'ed together.
            --wprintlog     : <64-bitmask> : activates print logging for the specified weenie event types. Alternately, logtype enums seperated by ',' are enummapped and or'ed together.
    ```

    A couple aditional notes on these options:
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
                    f"{arg_key} launch argument is in template, " "but has None value"
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

    # Setting the `--prefs` command configure both the game user preferences file and the
    # game settings folder. The game settings folder is set to the folder of the
    # user preferences file passed to `--prefs`.
    # The filename "UserPreferences.ini" seems to be hardcoded into the launcher
    # and client executables as the default.
    game_settings_dir = get_game_settings_dir(
        game_config=game_config, launcher_local_config=game_launcher_local_config
    )
    launch_args.extend(("--prefs", str(game_settings_dir / "UserPreferences.ini")))

    redacted_launch_args = tuple(
        arg.replace(account_number, "******").replace(ticket, "******")
        for arg in launch_args
    )
    logger.debug(f"Game launch arguments generated: {redacted_launch_args}")
    return launch_args


async def get_qprocess(
    game_launcher_config: GameLauncherConfig,
    game_launcher_local_config: GameLauncherLocalConfig,
    game_config: GameConfig,
    default_locale: OneLauncherLocale,
    world: World,
    login_server: str,
    account_number: str,
    ticket: str,
) -> QtCore.QProcess:
    """Return QProcess configured to start game client.

    Raises:
        MissingLaunchArgumentError
    """
    client_filename, client_type = game_launcher_config.get_client_filename(
        game_config.client_type
    )
    # Fixes binary path for 64-bit client
    if client_type == ClientType.WIN64:
        client_relative_path = Path("x64") / client_filename
    else:
        client_relative_path = Path(client_filename)

    launch_args = await get_launch_args(
        game_launcher_config=game_launcher_config,
        game_launcher_local_config=game_launcher_local_config,
        game_config=game_config,
        default_locale=default_locale,
        world=world,
        login_server=login_server,
        account_number=account_number,
        ticket=ticket,
    )

    process = QtCore.QProcess()
    process.setProgram(str(client_relative_path))
    process.setArguments(launch_args)
    if os.name != "nt":
        edit_qprocess_to_use_wine(qprocess=process, wine_config=game_config.wine)

    process.setWorkingDirectory(str(game_config.game_directory))
    # Just setting the QProcess working directory isn't enough on Windows
    if os.name == "nt":
        os.chdir(process.workingDirectory())

    return process
