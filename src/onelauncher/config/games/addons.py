
from pathlib import Path
from typing import Any, Dict, Final

from ...addons.manager import AddonsManager
from ...addons.startup_script import StartupScript
from . import games_config
from ...game import Game

CONFIG_SECTION_NAME: Final = "addons"


def get_addons_manager_from_game(game: Game) -> AddonsManager:
    config = games_config.get_game_config_section(
        game.uuid, CONFIG_SECTION_NAME)
    return AddonsManager(game,
                         [StartupScript(Path(script), game)
                          for script in config.get("enabled_startup_scripts", [])],
                         )


def get_config_from_addons_manager(
        addons_manager: AddonsManager) -> Dict[str, Any]:
    config: Dict[str, Any] = {}

    if addons_manager.enabled_startup_scripts:
        config["enabled_startup_scripts"] = [
            str(startup_script.relative_path)
            for startup_script in addons_manager.enabled_startup_scripts]
    else:
        config["enabled_startup_scripts"] = None

    return config


def save_addons_manager(addons_manager: AddonsManager) -> None:
    config = get_config_from_addons_manager(addons_manager)
    games_config.save_game_config_section(
        addons_manager.game.uuid, CONFIG_SECTION_NAME, config)
