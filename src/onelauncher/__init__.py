import logging
__title__ = "OneLauncher"
__version__ = "1.2.6"
__description__ = ("Lord of the Rings Online and Dungeons & Dragons"
                   " Online\nLauncher for Linux, Mac, and Windows")
# Update checks only work with a repository hosted on GitHub.
__project_url__ = "https://GitHub.com/JuneStepp/OneLauncher"
__author__ = "June Stepp"
__author_email__ = "contact@JuneStepp.me"
__license__ = "GPL-3.0-or-later"
__copyright__ = "(C) 2019-2021 June Stepp"
__copyright_history__ = ("Based on PyLotRO\n(C) 2009-2010 AJackson\n"
                         "Based on CLI launcher for LOTRO\n(C) 2007-2010 SNy\n"
                         "Based on CLI launcher for LOTRO\n(C) 2007-2010 SNy")


def setup_settings():
    global program_settings
    global game_settings
    program_settings = settings.ProgramSettings()
    game_settings = settings.GamesSettings()

    set_ui_locale()


def set_ui_locale():
    """Set locale for OneLauncher UI"""
    if (
        not program_settings.always_use_default_language_for_ui
        and game_settings.games
    ):
        program_settings.ui_locale = game_settings.current_game.locale
    else:
        program_settings.ui_locale = program_settings.default_locale


logger = logging.Logger("temp_logger")

from onelauncher import settings, logs  # isort:skip # noqa
logger = logs.Logger(settings.platform_dirs.user_log_path, "main").logger

setup_settings()
