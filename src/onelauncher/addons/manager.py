from pathlib import Path
from typing import List, Set

from onelauncher.addons.startup_script import StartupScript
from onelauncher.games import Game
from onelauncher.utilities import CaseInsensitiveAbsolutePath


class AddonsManager():
    def __init__(self,
                 game: Game,
                 enabled_startup_scripts: List[StartupScript],
        self.game = game
        self.enabled_startup_scripts = enabled_startup_scripts
