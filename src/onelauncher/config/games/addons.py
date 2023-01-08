
from pathlib import Path
from typing import Any, Dict, Final

from onelauncher.addons.manager import AddonsManager
from onelauncher.config.games import games_config
from onelauncher.games import Game

CONFIG_SECTION_NAME: Final = "addons"


def get_addons_manager_from_game(game: Game) -> AddonsManager:
    config = games_config.get_game_config_section(
        game.uuid, CONFIG_SECTION_NAME)
    return AddonsManager(game,
                         [Path(script) for script in config.get("startup_scripts",
                                                                [])]
                         )


def get_config_from_addons_manager(
        addons_manager: AddonsManager) -> Dict[str, Any]:
    config: Dict[str, Any] = {}
    if addons_manager.startup_scripts:
        config["startup_scripts"] = [
            str(script) for script in addons_manager.startup_scripts]

    return config


def save_addons_manager(addons_manager: AddonsManager) -> None:
    config = get_config_from_addons_manager(addons_manager)
    games_config.save_game_config_section(
        addons_manager.game.uuid, CONFIG_SECTION_NAME, config)
