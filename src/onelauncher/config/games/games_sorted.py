from typing import List
from onelauncher.game import Game
from onelauncher.game_utilities import GamesSorted
from onelauncher.config.games import games_config
from onelauncher.config.games.game import get_game_from_config


def get_games_sorted() -> GamesSorted:
    game_configs = games_config.get_all_game_configs()
    games: List[Game] = [get_game_from_config(game_config)
                         for game_config in game_configs]
    return GamesSorted(games)
