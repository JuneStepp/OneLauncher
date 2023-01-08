
from pathlib import Path
from typing import Any, Dict, Final

from onelauncher.addons.manager import AddonsManager
from onelauncher.addons.feed import LotroInterfaceFeed
from onelauncher.config.games import games_config
from onelauncher.games import Game

CONFIG_SECTION_NAME: Final = "addons"


def get_addons_manager_from_game(game: Game) -> AddonsManager:
    config = games_config.get_game_config_section(
        game.uuid, CONFIG_SECTION_NAME)
    return AddonsManager(game,
                         [Path(script) for script in config.get("startup_scripts",
                                                                [])],
                         {LotroInterfaceFeed(feed["name"],
                                             feed["description"],
                                             feed["addons_type"],
                                             feed["url"]) for feed in config.get(
                             "user_addons_feeds", [])},
                         config.get("override_default_addons_feeds", False)
                         )


def get_config_from_addons_manager(
        addons_manager: AddonsManager) -> Dict[str, Any]:
    config: Dict[str, Any] = {}
    if addons_manager.user_addons_feeds:
        config["override_default_addons_feeds"] = addons_manager.override_default_addons_feeds
        config["user_addons_feeds"] = [
            {
                "name": feed.name,
                "description": feed.description,
                "addons_type": feed.addons_type,
                "url": feed.url} for feed in addons_manager.user_addons_feeds]

    if addons_manager.startup_scripts:
        config["startup_scripts"] = [
            str(script) for script in addons_manager.startup_scripts]

    return config


def save_addons_manager(addons_manager: AddonsManager) -> None:
    config = get_config_from_addons_manager(addons_manager)
    games_config.save_game_config_section(
        addons_manager.game.uuid, CONFIG_SECTION_NAME, config)
