import logging
import sys
from contextlib import suppress
from typing import List
from uuid import UUID

from onelauncher import games_sorted, resources
from onelauncher.config.program_config import program_config


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
    launch_arg_val = get_launch_argument(
        "--game", ["LOTRO", "DDO"] + [str(uuid) for uuid in games_sorted.games])
    # Return if current game matches one selected with launch arguments
    if (not launch_arg_val or
        launch_arg_val == games_sorted.current_game.game_type or
            launch_arg_val == str(games_sorted.current_game.uuid)):
        return

    # Handle game UUIDs
    with suppress(ValueError):
        uuid = UUID(launch_arg_val)
        try:
            games_sorted.current_game = games_sorted.games[uuid]
        except KeyError:
            logger.exception(f"Game UUID: {uuid} does not exist.")
        return

    games_sorted.current_game = games_sorted.get_sorted_games_list(
        launch_arg_val, program_config.games_sorting_mode)[0]


def process_launch_arguments():
    """Configure settings for any valid arguments OneLauncher is started with"""
    process_game_launch_argument()

    language = get_launch_argument(
        "--language", list(resources.available_locales))
    if language:
        games_sorted.current_game.locale = resources.available_locales[language]


logger = logging.getLogger("main")
