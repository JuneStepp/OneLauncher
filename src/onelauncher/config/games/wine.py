from pathlib import Path
from typing import Any, Dict, Final

from onelauncher.config.games import games_config
from onelauncher.games import Game
from onelauncher.wine_environment import WineEnvironment

CONFIG_SECTION_NAME: Final = "wine"


def get_config_from_wine_environment(
        wine_env: WineEnvironment) -> Dict[str, Any]:
    config_dict: Dict[str, Any] = {
        "builtin_prefix_enabled": wine_env.builtin_prefix_enabled}
    if wine_env.user_wine_executable_path:
        config_dict["user_wine_executable_path"] = str(
            wine_env.user_wine_executable_path)
    if wine_env.user_prefix_path:
        config_dict["user_prefix_path"] = str(wine_env.user_prefix_path)
    if wine_env.debug_level:
        config_dict["debug_level"] = wine_env.debug_level

    return config_dict


def get_wine_environment_from_config(
        wine_config: Dict[str, Any]) -> WineEnvironment:
    # Deal with Paths
    user_wine_executable_path = None
    if "user_wine_executable_path" in wine_config:
        user_wine_executable_path = Path(
            wine_config["user_wine_executable_path"])

    user_prefix_path = None
    if "user_prefix_path" in wine_config:
        user_prefix_path = Path(wine_config["user_prefix_path"])

    return WineEnvironment(
        wine_config.get(
            "builtin_prefix_enabled",
            True),
        user_wine_executable_path,
        user_prefix_path,
        wine_config.get("debug_level"))


def get_wine_environment_from_game(game: Game) -> WineEnvironment:
    config = games_config.get_game_config_section(
        game.uuid, CONFIG_SECTION_NAME)
    return get_wine_environment_from_config(config)


def save_wine_environment(game: Game, wine_env: WineEnvironment) -> None:
    config = get_config_from_wine_environment(wine_env)
    games_config.save_game_config_section(
        game.uuid, CONFIG_SECTION_NAME, config)
