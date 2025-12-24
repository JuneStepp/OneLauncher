from pathlib import Path

import pytest

from onelauncher.addons.config import AddonsConfigSection
from onelauncher.config_manager import ConfigManager
from onelauncher.game_config import GameConfig, GameType, generate_game_config_id
from onelauncher.utilities import CaseInsensitiveAbsolutePath
from onelauncher.wine.config import WineConfigSection


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def games_dir(tmp_path: Path) -> Path:
    games_dir = tmp_path / "games"
    games_dir.mkdir()
    return games_dir


@pytest.fixture
def config_manager(config_dir: Path, games_dir: Path, tmp_path: Path) -> ConfigManager:
    config_manager = ConfigManager(program_config_dir=config_dir, games_dir=games_dir)
    config_manager.verify_configs()

    config_manager.update_program_config_file(config_manager.read_program_config_file())

    mock_game_dir = CaseInsensitiveAbsolutePath(tmp_path / "lotro_game_dir")
    mock_game_dir.mkdir()
    game_config = GameConfig(
        addons=AddonsConfigSection(),
        wine=WineConfigSection(),
        game_type=GameType.LOTRO,
        is_preview_client=False,
        game_directory=mock_game_dir,
    )
    config_manager.update_game_config_file(
        game_id=generate_game_config_id(game_config), config=game_config
    )

    return config_manager
