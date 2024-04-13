from pathlib import Path
from typing import Any, Final

from ...addons.feed import LotroInterfaceFeed
from ...addons.manager import AddonsManager
from ...addons.startup_script import StartupScript
from ...game import Game
from . import games_config

CONFIG_SECTION_NAME: Final = "addons"


def get_addons_manager_from_game(game: Game) -> AddonsManager:
    config = games_config.get_game_config_section(game.uuid, CONFIG_SECTION_NAME)
    return AddonsManager(
        game,
        [
            StartupScript(Path(script), game)
            for script in config.get("enabled_startup_scripts", [])
        ],
        {
            LotroInterfaceFeed(
                feed["name"], feed["description"], feed["addons_type"], feed["url"]
            )
            for feed in config.get("user_addons_feeds", [])
        },
        config.get("override_default_addons_feeds", False),
    )


def get_config_from_addons_manager(addons_manager: AddonsManager) -> dict[str, Any]:
    config: dict[str, Any] = {}
    if addons_manager.user_addons_feeds:
        config["override_default_addons_feeds"] = (
            addons_manager.override_default_addons_feeds
        )
        config["user_addons_feeds"] = [
            {
                "name": feed.name,
                "description": feed.description,
                "addons_type": feed.addons_type,
                "url": feed.url,
            }
            for feed in addons_manager.user_addons_feeds
        ]

    if addons_manager.enabled_startup_scripts:
        config["enabled_startup_scripts"] = [
            str(startup_script.relative_path)
            for startup_script in addons_manager.enabled_startup_scripts
        ]
    else:
        config["enabled_startup_scripts"] = None

    return config


def save_addons_manager(addons_manager: AddonsManager) -> None:
    config = get_config_from_addons_manager(addons_manager)
    games_config.save_game_config_section(
        addons_manager.game.uuid, CONFIG_SECTION_NAME, config
    )
