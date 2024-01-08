import os
from pathlib import Path
import trio

from PySide6 import QtCore
from .config.games.wine import get_wine_environment_from_game

from .game import ClientType, Game
from .network.game_launcher_config import GameLauncherConfig
from .network.world import World
from .wine_environment import edit_qprocess_to_use_wine


class MissingLaunchArgumentError(Exception):
    """Launch argument missing."""


async def get_launch_args(
        game_launcher_config: GameLauncherConfig,
        game: Game,
        world: World,
        account_number: str,
        ticket: str) -> str:
    """Return complete client launch arguments based on
       client_launch_args_template.

    Raises:
        MissingLaunchArgumentError
    """
    launch_args_template_mapping = {
        "{SUBSCRIPTION}": account_number,
        "{LOGIN}": (await world.get_status()).login_server,
        "{GLS}": ticket,
        "{CHAT}": world.chat_server_url,
        "{LANG}": game.locale.game_language_name,
        "{CRASHRECEIVER}": game_launcher_config.client_crash_server_arg,
        "{UPLOADTHROTTLE}": game_launcher_config.client_default_upload_throttle_mbps_arg,
        "{BUGURL}": game_launcher_config.client_bug_url_arg,
        "{AUTHSERVERURL}": game_launcher_config.client_auth_server_arg,
        "{GLSTICKETLIFETIME}": game_launcher_config.client_gls_ticket_lifetime_arg,
        "{SUPPORTURL}": game_launcher_config.client_support_url_arg,
        "{SUPPORTSERVICEURL}": game_launcher_config.client_support_service_url_arg}

    launch_args_template = game_launcher_config.client_launch_args_template
    for arg_key, arg_val in launch_args_template_mapping.items():
        if arg_key in launch_args_template:
            try:
                launch_args_template = launch_args_template.replace(
                    arg_key, arg_val)
            except TypeError as e:
                raise MissingLaunchArgumentError(
                    f"{arg_key} launch argument is in template, "
                    "but has None value") from e

    if "{" in launch_args_template:
        raise MissingLaunchArgumentError(
            f"Template has unrecognized launch arguments: {launch_args_template}")

    launch_args = launch_args_template

    # Tell the client that the high resolution texture dat file was not
    # updated. Client will not switch into high texture detail mode.
    if not game.high_res_enabled:
        launch_args += (game_launcher_config.high_res_patch_arg or
                        " --HighResOutOfDate")

    return launch_args


async def get_qprocess(
        game_launcher_config: GameLauncherConfig,
        game: Game,
        world: World,
        account_number: str,
        ticket: str) -> QtCore.QProcess:
    """Return QProcess configured to start game client.

    Raises:
        MissingLaunchArgumentError
    """
    client_filename, client_type = game_launcher_config.get_client_filename(
        game.client_type)
    # Fixes binary path for 64-bit client
    if client_type == ClientType.WIN64:
        client_relative_path = Path("x64") / client_filename
    else:
        client_relative_path = Path(client_filename)

    launch_args = await get_launch_args(
        game_launcher_config,
        game,
        world,
        account_number,
        ticket)

    process = QtCore.QProcess()
    process.setProgram(str(client_relative_path))
    process.setArguments(launch_args.split(" "))
    if os.name != "nt":
        edit_qprocess_to_use_wine(
            process, get_wine_environment_from_game(game))

    process.setWorkingDirectory(str(game.game_directory))

    return process
