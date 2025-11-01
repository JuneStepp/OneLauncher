from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6 import QtWidgets

from onelauncher.game_account_config import GameAccountConfig
from onelauncher.main_window import MainWindow


@pytest.fixture
def mock_config_manager():
    manager = MagicMock()
    manager.get_game_accounts.return_value = [
        GameAccountConfig(username="testuser", last_used_world_name="World1")
    ]
    manager.get_game_config.return_value.name = "Test Game"
    manager.get_program_config.return_value.games_sorting_mode = "alphabetical"
    manager.get_games_sorted.return_value = ["test_game"]
    manager.get_game_config_ids.return_value = ["test_game"]
    return manager


def test_world_not_saved_on_failed_login(mock_config_manager):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    with patch("onelauncher.main_window.StartGame") as mock_start_game, \
         patch("onelauncher.main_window.MainWindow.authenticate_account", new_callable=MagicMock) as mock_authenticate:
        # Simulate a failed game launch
        mock_start_game.return_value.start_game.side_effect = Exception(
            "Game launch failed"
        )
        mock_authenticate.return_value = MagicMock()

        main_window = MainWindow(
            config_manager=mock_config_manager, starting_game_id="test_game"
        )
        main_window.setup_ui()
        main_window.game_launcher_config = MagicMock()
        main_window.game_launcher_local_config = MagicMock()
        main_window.ui.cboAccount.setCurrentText("testuser")
        main_window.ui.cboWorld.addItem("World2")
        main_window.ui.cboWorld.setCurrentText("World2")

        def mock_start_soon(target, *args, **kwargs):
            target(*args, **kwargs)

        with patch('trio.open_nursery', new_callable=MagicMock) as mock_nursery:
            mock_nursery.start_soon = mock_start_soon
            with pytest.raises(Exception, match="Game launch failed"):
                main_window.btnLoginClicked()

        # Assert that the last used world was NOT updated
        mock_config_manager.update_game_accounts_config_file.assert_not_called()
