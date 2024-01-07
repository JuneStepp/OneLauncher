import argparse
import logging
import sys
from uuid import UUID

from . import __about__, games_sorted
from .config.program_config import program_config
from .game import Game, GameType
from .qtapp import setup_qtapplication
from .resources import available_locales


def setup_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__about__.__description__)
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"{__about__.__title__} {__about__.__version__}")

    game_type_choices = [str(game_type) for game_type in GameType]
    game_uuid_choices = [str(uuid) for uuid in games_sorted.games]

    def game_arg_type(arg_val: str):
        if arg_val.upper() in game_type_choices:
            arg_val = arg_val.upper()
            games_of_type = games_sorted.get_sorted_games_list(
                program_config.games_sorting_mode, GameType(arg_val))
            if not games_of_type:
                raise argparse.ArgumentTypeError(
                    f"no {arg_val} games found")
        return arg_val
    parser.add_argument(
        "-g",
        "--game",
        action="store",
        type=game_arg_type,
        choices=game_type_choices + game_uuid_choices,
        help=f"game to load ({', '.join(game_type_choices)} or game UUID)",
        metavar="")

    language_choices = list(available_locales)
    parser.add_argument(
        "-l",
        "--language",
        action="store",
        choices=language_choices,
        help=f"game language. ({', '.join(language_choices)})",
        metavar="")
    return parser


def handle_program_start_setup_wizard():
    """Run setup wizard if there are no settings"""
    # If game settings haven't been generated
    if not games_sorted.games:
        from .setup_wizard import SetupWizard
        setup_wizard = SetupWizard()
        setup_wizard.exec()

    # Close program if the user left the setup wizard
    # without generating the game settings
    if not games_sorted.games:
        sys.exit()


def start_main_window(game: Game):
    # Import has to be done here, because some code run when
    # main_window.py imports requires the QApplication to exist.
    from .main_window import MainWindow
    main_window = MainWindow(game)
    main_window.run()


def main() -> None:
    args = setup_arg_parser().parse_args()
    qapp = setup_qtapplication()
    handle_program_start_setup_wizard()

    last_played_game = games_sorted.get_games_sorted_by_last_played()[0]
    game = (
        last_played_game if last_played_game.last_played is not None
        else games_sorted.get_games_sorted_by_priority()[0])
    if args.game in [str(game_type) for game_type in GameType]:
        game = games_sorted.get_sorted_games_list(
            program_config.games_sorting_mode, GameType(args.game))[0]
    elif args.game:
        game = games_sorted.games[UUID(args.game)]
    if args.language:
        game.locale = available_locales[args.language]

    start_main_window(game)
    sys.exit(qapp.exec())


logger = logging.getLogger("main")
if __name__ == "__main__":
    main()
