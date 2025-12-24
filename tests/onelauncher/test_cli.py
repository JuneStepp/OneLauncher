from pathlib import Path
from shutil import rmtree

import cyclopts
import pytest
from PySide6 import QtWidgets
from pytest_mock import MockerFixture

from onelauncher import cli, main
from onelauncher.config_manager import (
    PROGRAM_CONFIG_DEFAULT_NAME,
    ConfigFileError,
    ConfigManager,
)


@pytest.fixture
def app(
    monkeypatch: pytest.MonkeyPatch, config_dir: Path, games_dir: Path
) -> cyclopts.App:
    monkeypatch.setenv(name="ONELAUNCHER_CONFIG_DIRECTORY", value=str(config_dir))
    monkeypatch.setenv(name="ONELAUNCHER_GAMES_DIRECTORY", value=str(games_dir))
    app = cli.get_app()
    # The return value will be what would have been the exit code.
    app.result_action = "return_value"
    return app


async def test_normal(
    config_manager: ConfigManager, app: cyclopts.App, mocker: MockerFixture
) -> None:
    async_mock = mocker.patch.object(cli, "start_async_gui")
    async_mock.return_value = 0

    assert app([]) == 0
    async_mock.assert_called_once()

    main_window_mock = mocker.patch.object(main, "MainWindow", autospec=True)

    await async_mock.call_args.kwargs["entry"]()
    main_window_mock.assert_called_once()


async def test_no_config(app: cyclopts.App, mocker: MockerFixture) -> None:
    async_mock = mocker.patch.object(cli, "start_async_gui")
    async_mock.return_value = 0

    assert app([]) == 0
    async_mock.assert_called_once()

    mock = mocker.patch.object(main, "SetupWizard", autospec=True)
    mock_instance = mock.return_value
    mock_instance.result.return_value = QtWidgets.QDialog.DialogCode.Rejected

    await async_mock.call_args.kwargs["entry"]()
    mock_instance.run.assert_called_once()
    mock_instance.result.assert_called_once()


async def test_no_games(
    config_manager: ConfigManager, app: cyclopts.App, mocker: MockerFixture
) -> None:
    rmtree(config_manager.games_dir)

    async_mock = mocker.patch.object(cli, "start_async_gui")
    async_mock.return_value = 0

    assert app([]) == 0
    async_mock.assert_called_once()

    mocker.patch.object(QtWidgets.QMessageBox, "information")
    mock = mocker.patch.object(main, "SetupWizard", autospec=True)
    mock_instance = mock.return_value
    mock_instance.result.return_value = QtWidgets.QDialog.DialogCode.Rejected

    await async_mock.call_args.kwargs["entry"]()
    mock.assert_called_once()
    assert mock.call_args.kwargs["game_selection_only"] is True
    mock_instance.run.assert_called_once()
    mock_instance.result.assert_called_once()


def test_invalid_program_config(
    config_dir: Path, app: cyclopts.App, mocker: MockerFixture
) -> None:
    (config_dir / PROGRAM_CONFIG_DEFAULT_NAME).write_text("INVALID")

    mock = mocker.patch.object(main, "show_invalid_config_dialog")
    mock.return_value = None

    assert app([]) == 1
    mock.assert_called_once()
    assert isinstance(mock.call_args.kwargs["error"], ConfigFileError)
    assert not mock.call_args.kwargs.get("backup_available")


def test_invalid_program_config_with_backup(
    config_dir: Path, app: cyclopts.App, mocker: MockerFixture
) -> None:
    (config_dir / PROGRAM_CONFIG_DEFAULT_NAME).write_text("INVALID")
    (config_dir / f"{PROGRAM_CONFIG_DEFAULT_NAME}.backup").touch()

    mock = mocker.patch.object(main, "show_invalid_config_dialog")
    mock.return_value = False

    assert app([]) == 1
    mock.assert_called_once()
    assert isinstance(mock.call_args.kwargs["error"], ConfigFileError)
    assert mock.call_args.kwargs["backup_available"] is True


async def test_invalid_program_config_load_backup(
    app: cyclopts.App,
    mocker: MockerFixture,
    config_manager: ConfigManager,
) -> None:
    backup_program_config = config_manager.get_config_backup_path(
        config_manager.program_config_path
    )
    config_manager.program_config_path.rename(backup_program_config)
    config_manager.program_config_path.write_text("INVALID")

    mock = mocker.patch.object(main, "show_invalid_config_dialog")
    mock.return_value = True

    async_mock = mocker.patch.object(cli, "start_async_gui")
    async_mock.return_value = 0

    assert app([]) == 0
    async_mock.assert_called_once()

    main_window_mock = mocker.patch.object(main, "MainWindow", autospec=True)

    await async_mock.call_args.kwargs["entry"]()
    main_window_mock.assert_called_once()

    assert not backup_program_config.exists()
