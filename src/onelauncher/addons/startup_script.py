from pathlib import Path

import attrs

from ..utilities import CaseInsensitiveAbsolutePath


@attrs.frozen
class StartupScript:
    """Python script that runs whenever a game is started

    Args:
        relative_path (Path): Path from the game documents config dir to
                              the startup script.
    """

    relative_path: Path

    def get_absolute_path(
        self, documents_config_dir: CaseInsensitiveAbsolutePath
    ) -> CaseInsensitiveAbsolutePath:
        return documents_config_dir / self.relative_path


def run_startup_script(
    script: StartupScript,
    game_directory: CaseInsensitiveAbsolutePath,
    documents_config_dir: CaseInsensitiveAbsolutePath,
) -> None:
    """
    Run Python startup script file.
    Script is given access to globals with game information

    Raises:
        FileNotFoundError: Startup script does not exist.
        SyntaxError: Startup script has a syntax error.
    """
    with script.get_absolute_path(
        documents_config_dir=documents_config_dir
    ).open() as file:
        code = file.read()

    exec(  # noqa: S102
        code,
        {
            "__file__": str(script.get_absolute_path(documents_config_dir)),
            "__game_dir__": str(game_directory),
            "__game_config_dir__": str(documents_config_dir),
        },
    )
