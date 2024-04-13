from typing import List
from ...game import Game
from ...game_utilities import GamesSorted
from . import games_config
from .game import get_game_from_config


def get_games_sorted() -> GamesSorted:
    game_configs = games_config.get_all_game_configs()
    games: List[Game] = [get_game_from_config(game_config)
                         for game_config in game_configs]
    return GamesSorted(games)
