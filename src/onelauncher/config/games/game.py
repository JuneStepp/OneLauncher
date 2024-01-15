
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

from . import games_config
from ..program_config import program_config
from ...game_account import GameAccount
from ...game import ClientType, Game
from ...resources import available_locales
from ...utilities import CaseInsensitiveAbsolutePath


def get_config_from_game(game: Game) -> dict[str, Any]:
    game_dict: Dict[str, Any] = {
        "uuid": str(
            game.uuid),
        "sorting_priority": game.sorting_priority,
        "game_type": str(game.game_type),
        "name": game.name,
        "description": game.description,
        "game_directory": str(game.game_directory),
        "language": game.locale.lang_tag,
        "client_type": str(game.client_type),
        "high_res_enabled": game.high_res_enabled,
        "patch_client_filename": game.patch_client_filename,
        "newsfeed": game.newsfeed,
        "last_played": game.last_played,
        "standard_game_launcher_filename": game.standard_game_launcher_filename
    }
    if game.accounts:
        account_dicts = []
        for account in game.accounts:
            account_dict = {
                "account_name": account.username,
                "last_used_world_name": account.last_used_world_name}
            if account.display_name is not None:
                account_dict["display_name"] = account.display_name
            account_dicts.append(account_dict)
        game_dict["accounts"] = account_dicts

    return game_dict


def generate_default_game_name(game_directory: Path, uuid: UUID) -> str:
    return f"{game_directory.name} ({uuid})"


def get_game_from_config(game_config: dict[str, Any],) -> Game:
    uuid = UUID(game_config["uuid"])
    game_directory = CaseInsensitiveAbsolutePath(
        game_config["game_directory"])

    # Deal with missing sections
    game_config["user_addons_feeds"] = game_config.get("user_addons_feeds", {})
    game_config["info"] = game_config.get("info", {})
    game_config["accounts"] = game_config.get("accounts", [])

    return Game(uuid,
                game_config.get("sorting_priority", -1),
                game_config["game_type"],
                game_directory,
                available_locales[
                    game_config.get("language",
                                    str(program_config.default_locale))],
                ClientType(game_config.get("client_type",
                                           "WIN64")),
                game_config.get("high_res_enabled",
                                True),
                game_config.get("patch_client_filename",
                                "patchclient.dll"),
                game_config.get("name",
                                generate_default_game_name(game_directory,
                                                           uuid)),
                game_config.get("description", ""),
                [
                    GameAccount(
                        game_uuid=uuid,
                        username=account["account_name"],
                        display_name=account.get("display_name"),
                        last_used_world_name=account["last_used_world_name"],
                    )
                    for account in game_config["accounts"]],
                game_config.get("newsfeed"),
                game_config.get("last_played"),
                game_config.get("standard_game_launcher_filename"),
                )


def save_game(game: Game):
    config = get_config_from_game(game)
    games_config.save_game_config(game.uuid, config)
