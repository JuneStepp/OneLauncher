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

from onelauncher.config.games.games_sorted import get_games_sorted

games_sorted = get_games_sorted()
