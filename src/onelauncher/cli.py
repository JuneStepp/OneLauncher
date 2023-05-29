from .ui_utilities import show_message_box_details_as_markdown
from .qtapp import setup_qtapplication
from .config.program_config import program_config
import argparse
import logging
import sys
import urllib.error
import urllib.request
from json import loads as jsonLoads
from uuid import UUID

from pkg_resources import parse_version
from PySide6 import QtCore, QtWidgets

from onelauncher.game import GameType

from . import __about__, games_sorted

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
                GameType(arg_val), program_config.games_sorting_mode)
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


def check_for_update():
    """Notifies user if their copy of OneLauncher is out of date"""
    current_version = parse_version(__about__.__version__)
    repository_url = __about__.__project_url__
    if "github.com" not in repository_url.lower():
        logger.warning(
            "Repository URL set in Information.py is not "
            "at github.com. The system for update notifications"
            " only supports this site."
        )
        return

    latest_release_template = (
        "https://api.github.com/repos/{user_and_repo}/releases/latest"
    )
    latest_release_url = latest_release_template.format(
        user_and_repo=repository_url.lower().split("github.com")[
            1].strip("/")
    )

    try:
        with urllib.request.urlopen(latest_release_url, timeout=4) as response:
            release_dictionary = jsonLoads(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError) as error:
        logger.error(error.reason, exc_info=True)
        return

    release_version = parse_version(release_dictionary["tag_name"])

    if release_version > current_version:
        url = release_dictionary["html_url"]
        name = release_dictionary["name"]
        description = release_dictionary["body"]

        messageBox = QtWidgets.QMessageBox()
        messageBox.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Information)
        messageBox.setStandardButtons(messageBox.StandardButton.Ok)

        centered_href = (
            f'<html><head/><body><p align="center"><a href="{url}">'
            f'<span>{name}</span></a></p></body></html>'
        )
        messageBox.setInformativeText(
            f"There is a new version of {__about__.__title__} available! {centered_href}"
        )
        messageBox.setDetailedText(description)
        show_message_box_details_as_markdown(messageBox)
        messageBox.exec()
    else:
        logger.info(f"{__about__.__title__} is up to date.")


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


def start_main_window():
    # Import has to be done here, because some code run when
    # main_window.py imports requires the QApplication to exist.
    from .main_window import MainWindow
    main_window = MainWindow()
    main_window.run()


def main() -> None:
    args = setup_arg_parser().parse_args()
    qapp = setup_qtapplication()
    handle_program_start_setup_wizard()  

    if args.game in [str(game_type) for game_type in GameType]:
        games_sorted.current_game = games_sorted.get_sorted_games_list(
            GameType(args.game), program_config.games_sorting_mode)[0]
    elif args.game:
        games_sorted.current_game = games_sorted.games[UUID(args.game)]
    if args.language:
        games_sorted.current_game.locale = available_locales[args.language]
    
    check_for_update()
    start_main_window()
    sys.exit(qapp.exec())


logger = logging.getLogger("main")
if __name__ == "__main__":
    main()
