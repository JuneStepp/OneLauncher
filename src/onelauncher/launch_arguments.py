import sys
from typing import List
from uuid import UUID

from onelauncher import resources
from onelauncher.config.program_config import program_config
from onelauncher.config.games_config import games_config


def get_launch_argument(key: str, accepted_values: List[str]):
    launch_arguments = sys.argv
    try:
        modifier_index = launch_arguments.index(key)
    except ValueError:
        pass
    else:
        try:
            value = launch_arguments[modifier_index + 1]
        except IndexError:
            pass
        else:
            if value in accepted_values:
                return value


def process_game_launch_argument():
    """Launch into specific game type or game if specified in launch argument"""
    # Game types and game UUIDs are accepted values
    game = get_launch_argument(
        "--game", ["LOTRO", "DDO"] + [str(uuid) for uuid in games_config.games])
    if (not game or
        game == games_config.current_game.game_type or
            game == str(games_config.current_game.uuid)):
        return

    if game == "LOTRO":
        sorting_modes = games_config.lotro_sorting_modes
    elif game == "DDO":
        sorting_modes = games_config.ddo_sorting_modes
    elif UUID(game) in games_config.games:
        games_config.current_game = games_config.games[UUID(game)]
        return
    else:
        return

    games_config.current_game = sorting_modes[program_config.games_sorting_mode][0]


def process_launch_arguments():
    """Configure settings for any valid arguments OneLauncher is started with"""
    process_game_launch_argument()

    language = get_launch_argument(
        "--language", list(resources.available_locales))
    if language:
        games_config.current_game.locale = resources.available_locales[language]
