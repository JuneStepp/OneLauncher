from .config.games.games_sorted import get_games_sorted
from .logs import setup_application_logging

setup_application_logging()
games_sorted = get_games_sorted()
