
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

from onelauncher.config.games import games_config
from onelauncher.config.program_config import program_config
from onelauncher.game_account import GameAccount
from onelauncher.games import ClientType, Game
from onelauncher.resources import available_locales
from onelauncher.utilities import CaseInsensitiveAbsolutePath


def get_config_from_game(game: Game) -> dict[str, Any]:
    game_dict: Dict[str, Any] = {
        "uuid": str(
            game.uuid),
        "sorting_priority": game.sorting_priority,
        "game_type": game.game_type,
        "name": game.name,
        "description": game.description,
        "game_directory": str(
            game.game_directory),
        "language": game.locale.lang_tag,
        "client_type": game.client_type.value,
        "high_res_enabled": game.high_res_enabled,
        "patch_client_filename": game.patch_client_filename,
    }
    if game.newsfeed is not None:
        game_dict["newsfeed"] = game.newsfeed
    if game.last_played is not None:
        game_dict["last_played"] = game.last_played
    
    if game.standard_game_launcher_filename:
        game_dict["standard_game_launcher_filename"] = game.standard_game_launcher_filename

    if game.accounts:
        game_dict["accounts"] = [
            {"account_name": account.username,
                "last_used_world_name": account.last_used_world_name}
            for account in game.accounts.values()]

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
                available_locales[game_config.get("language",
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
                game_config.get("description",
                                      ""),
                game_config.get("newsfeed",
                                      None),
                game_config.get("last_played", None),
                game_config.get("standard_game_launcher_filename", None),
                {account["account_name"]: GameAccount(account["account_name"],
                                                      uuid,
                                                      account["last_used_world_name"])
                    for account in game_config["accounts"]},
                )

def save_game(game: Game):
    config = get_config_from_game(game)
    games_config.save_game_config(game.uuid, config)
    
