import logging
import sys
import urllib.error
import urllib.request
from contextlib import suppress
from json import loads as jsonLoads
from typing import List
from uuid import UUID

from pkg_resources import parse_version
from PySide6 import QtCore, QtWidgets

from onelauncher.qtapp import setup_qtapplication

from . import __project_url__, __title__, __version__, games_sorted, resources
from .config.program_config import program_config
from .logs import setup_application_logging
from .ui_utilities import show_message_box_details_as_markdown


def get_launch_argument(key: str, accepted_values: List[str]):
    launch_arguments = sys.argv
    try:
        modifier_index = launch_arguments.index(key)
    except ValueError:
        pass
    else:
        try:
            value = launch_arguments[modifier_index + 1]
        except IndexError:
            pass
        else:
            if value in accepted_values:
                return value


def process_game_launch_argument():
    """Launch into specific game type or game if specified in launch argument"""
    # Game types and game UUIDs are accepted values
    launch_arg_val = get_launch_argument(
        "--game", ["LOTRO", "DDO"] + [str(uuid) for uuid in games_sorted.games])
    # Return if current game matches one selected with launch arguments
    if (not launch_arg_val or
        launch_arg_val == games_sorted.current_game.game_type or
            launch_arg_val == str(games_sorted.current_game.uuid)):
        return

    # Handle game UUIDs
    with suppress(ValueError):
        uuid = UUID(launch_arg_val)
        try:
            games_sorted.current_game = games_sorted.games[uuid]
        except KeyError:
            logger.exception(f"Game UUID: {uuid} does not exist.")
        return

    games_sorted.current_game = games_sorted.get_sorted_games_list(
        launch_arg_val, program_config.games_sorting_mode)[0]


def process_launch_arguments():
    """Configure settings for any valid arguments OneLauncher is started with"""
    process_game_launch_argument()

    language = get_launch_argument(
        "--language", list(resources.available_locales))
    if language:
        games_sorted.current_game.locale = resources.available_locales[language]


def check_for_update():
    """Notifies user if their copy of OneLauncher is out of date"""
    current_version = parse_version(__version__)
    repository_url = __project_url__
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
            f"There is a new version of {__title__} available! {centered_href}"
        )
        messageBox.setDetailedText(description)
        show_message_box_details_as_markdown(messageBox)
        messageBox.exec()
    else:
        logger.info(f"{__title__} is up to date.")


def start_setup_wizard(**kwargs):
    from .setup_wizard import SetupWizard
    setup_wizard = SetupWizard(**kwargs)
    setup_wizard.exec()


def handle_program_start_setup_wizard():
    """Run setup wizard if there are no settings"""
    # If game settings haven't been generated
    if not games_sorted.games:
        start_setup_wizard()

    # Close program if the user left the setup wizard
    # without generating the game settings
    if not games_sorted.games:
        sys.exit()


def start_main_window():
    # Import has to be done here, because some code run when
    # main_window.py imports requires the QApplication to exist.
    from .main_window import MainWindow
    global main_window
    main_window = MainWindow()
    main_window.run()


def main() -> None:
    setup_application_logging()
    global logger
    logger = logging.getLogger("main")
    process_launch_arguments()
    qapp = setup_qtapplication()
    check_for_update()

    handle_program_start_setup_wizard()

    start_main_window()

    sys.exit(qapp.exec())


logger = logging.getLogger("main")
if __name__ == "__main__":
    main()
