from pathlib import Path
from typing import List, Set

from onelauncher.games import Game
from onelauncher.utilities import CaseInsensitiveAbsolutePath


class AddonsManager():
    def __init__(self,
                 game: Game,
                 startup_scripts: List[Path]) -> None:
        self.game = game
        self.startup_scripts = startup_scripts
