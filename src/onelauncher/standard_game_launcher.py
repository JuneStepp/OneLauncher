from .game import Game, GameType
from .network.game_launcher_config import GameLauncherConfig
from .utilities import CaseInsensitiveAbsolutePath


async def _get_launcher_path_based_on_client_filename(
    game: Game,
) -> CaseInsensitiveAbsolutePath | None:
    game_launcher_config = await GameLauncherConfig.from_game(game)
    if game_launcher_config is None:
        return None

    game_client_filename = game_launcher_config.get_client_filename()[0]
    lowercase_launcher_filename = (
        game_client_filename.lower().split("client")[0] + "launcher.exe"
    )
    launcher_path = game.game_directory / lowercase_launcher_filename
    return launcher_path if launcher_path.exists() else None


def _get_launcher_path_with_hardcoded_filenames(
    game: Game,
) -> CaseInsensitiveAbsolutePath | None:
    match game.game_type:
        case GameType.LOTRO:
            filenames = {"LotroLauncher.exe"}
        case GameType.DDO:
            filenames = {"DNDLauncher.exe"}
        case _:
            raise ValueError("Unexpected game type")

    for filename in filenames:
        launcher_path = game.game_directory / filename
        if launcher_path.exists():
            return launcher_path

    # No hard-coded launcher filenames existed
    return None


def _get_launcher_path_with_search(
    game_directory: CaseInsensitiveAbsolutePath,
) -> CaseInsensitiveAbsolutePath | None:
    return next(
        (
            file
            for file in game_directory.iterdir()
            if file.name.lower().endswith("launcher.exe")
        ),
        None,
    )


def _get_launcher_path_from_config(game: Game) -> CaseInsensitiveAbsolutePath | None:
    if game.standard_game_launcher_filename:
        launcher_path = game.game_directory / game.standard_game_launcher_filename
        if launcher_path.exists():
            return launcher_path

    return None


async def get_standard_game_launcher_path(
    game: Game,
) -> CaseInsensitiveAbsolutePath | None:
    launcher_path = _get_launcher_path_from_config(game)
    if launcher_path is not None:
        return launcher_path

    launcher_path = await _get_launcher_path_based_on_client_filename(game)
    if launcher_path is not None:
        return launcher_path

    launcher_path = _get_launcher_path_with_hardcoded_filenames(game)
    if launcher_path is not None:
        return launcher_path

    launcher_path = _get_launcher_path_with_search(game.game_directory)
    return launcher_path
