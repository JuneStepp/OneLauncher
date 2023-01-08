from pathlib import Path

from onelauncher.games import Game
from onelauncher.utilities import CaseInsensitiveAbsolutePath


class StartupScript():
    def __init__(self, relative_path: Path, game: Game) -> None:
        """Python script that runs whenever a game is started

        Args:
            relative_path (Path): Path from the game documents config dir to
                                  the startup script.
            game (Game): The `Game` object associated with this startup script.
        """ 
        self.relative_path = relative_path
        self.game = game

    def run(self) -> None:
        """
        Run Python startup script file.
        Script is given access to globals with game information

        Raises:
            FileNotFoundError: Startup script does not exist.
            SyntaxError: Startup script has a syntax error.
        """
        with self.absolute_path.open() as file:
            code = file.read()

        exec(
            code, {
                "__file__": str(self.absolute_path),
                "__game_dir__": str(self.game.game_directory),
                "__game_config_dir__": str(
                    self.game.documents_config_dir)
            }
        )

    @property
    def absolute_path(self) -> CaseInsensitiveAbsolutePath:
        return CaseInsensitiveAbsolutePath(
            self.relative_path.relative_to(
                self.game.documents_config_dir))
