from typing import List

import sys
from uuid import UUID

from onelauncher.settings import game_settings, program_settings
from onelauncher import resources

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
        "--game", ["LOTRO", "DDO"] + [str(uuid) for uuid in game_settings.games])
    if (not game or
        game == game_settings.current_game.game_type or
            game == str(game_settings.current_game.uuid)):
        return

    if game == "LOTRO":
        sorting_modes = game_settings.lotro_sorting_modes
    elif game == "DDO":
        sorting_modes = game_settings.ddo_sorting_modes
    elif UUID(game) in game_settings.games:
        game_settings.current_game = game_settings.games[UUID(game)]
        return
    else:
        return

    game_settings.current_game = sorting_modes[program_settings.games_sorting_mode][0]


def process_launch_arguments():
    """Configure settings for any valid arguments OneLauncher is started with"""
    process_game_launch_argument()

    language = get_launch_argument(
        "--language", list(resources.available_locales))
    if language:
        game_settings.current_game.locale = resources.available_locales[language]
