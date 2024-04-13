from pathlib import Path
from typing import Any, Dict, Final, Self

from . import games_config
from ...game import Game
from ...wine.wine_management import WineManagement
from ...wine_environment import WineEnvironment

CONFIG_SECTION_NAME: Final = "wine"


class WineConfig():
    def __init__(self,
                 builtin_prefix_enabled: bool,
                 user_wine_executable_path: Path | None = None,
                 user_prefix_path: Path | None = None,
                 debug_level: str | None = None) -> None:
        self.builtin_prefix_enabled = builtin_prefix_enabled
        self.user_wine_executable_path = user_wine_executable_path
        self.user_prefix_path = user_prefix_path
        self.debug_level = debug_level

    @classmethod
    def from_config_dict(cls, config_dict: Dict[str, Any]) -> Self:
        # Deal with Paths
        user_wine_executable_path = None
        if "user_wine_executable_path" in config_dict:
            user_wine_executable_path = Path(
                config_dict["user_wine_executable_path"])

        user_prefix_path = None
        if "user_prefix_path" in config_dict:
            user_prefix_path = Path(config_dict["user_prefix_path"])

        return cls(
            config_dict.get(
                "builtin_prefix_enabled",
                True),
            user_wine_executable_path,
            user_prefix_path,
            config_dict.get("debug_level"))


def get_config_dict_from_wine_config(
        wine_config: WineConfig) -> Dict[str, Any]:
    config_dict: Dict[str, Any] = {
        "builtin_prefix_enabled": wine_config.builtin_prefix_enabled,
        "user_wine_executable_path": str(wine_config.user_wine_executable_path)
        if wine_config.user_wine_executable_path else None,
        "user_prefix_path": str(wine_config.user_prefix_path)
        if wine_config.user_prefix_path else None,
        "debug_level": wine_config.debug_level
    }
    return config_dict


def get_config_from_wine_environment(
        wine_env: WineEnvironment) -> Dict[str, Any]:
    config_dict: Dict[str, Any] = {
        "builtin_prefix_enabled": wine_env.builtin_prefix_enabled,
        "user_wine_executable_path": str(wine_env.user_wine_executable_path)
        if wine_env.user_wine_executable_path else None,
        "user_prefix_path": str(wine_env.user_prefix_path)
        if wine_env.user_prefix_path else None,
        "debug_level": wine_env.debug_level
    }
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


def get_wine_management_from_wine_config(
        wine_config: WineConfig) -> WineManagement:
    # Function is here for future config options relevent to initializing
    # WineManagement
    return WineManagement()


def get_wine_management_from_game(game: Game) -> WineManagement:
    return get_wine_management_from_wine_config(
        get_wine_config_from_game(game))


def get_wine_environment_from_game(game: Game) -> WineEnvironment:
    config = games_config.get_game_config_section(
        game.uuid, CONFIG_SECTION_NAME)
    return get_wine_environment_from_config(config)


def get_wine_config_from_game(game: Game) -> WineConfig:
    config_dict = games_config.get_game_config_section(
        game.uuid, CONFIG_SECTION_NAME)
    return WineConfig.from_config_dict(config_dict)


def save_wine_environment(game: Game, wine_env: WineEnvironment) -> None:
    config = get_config_from_wine_environment(wine_env)
    games_config.save_game_config_section(
        game.uuid, CONFIG_SECTION_NAME, config)


def save_wine_config(game: Game, wine_config: WineConfig) -> None:
    config_dict = get_config_dict_from_wine_config(wine_config)
    games_config.save_game_config_section(
        game.uuid, CONFIG_SECTION_NAME, config_dict)
