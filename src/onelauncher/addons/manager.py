from typing import List, Set

from .startup_script import StartupScript
from ..game import Game, GameType
from ..utilities import CaseInsensitiveAbsolutePath


class AddonsManager():
    def __init__(self,
                 game: Game,
                 enabled_startup_scripts: List[StartupScript]) -> None:
        self.game = game
        self.enabled_startup_scripts = enabled_startup_scripts
