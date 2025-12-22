import logging
import traceback

from PySide6 import QtWidgets

from .__about__ import __title__
from .config_manager import (
    ConfigFileError,
    ConfigManager,
    NoValidGamesError,
    WrongConfigVersionError,
)
from .game_config import GameConfigID
from .main_window import MainWindow
from .setup_wizard import SetupWizard
from .ui.error_message_uic import Ui_errorDialog
from .ui.qtapp import get_qapp

logger = logging.getLogger(__name__)


def show_invalid_config_dialog(
    error: ConfigFileError, backup_available: bool = False
) -> bool | None:
    """
    Returns:
        None: When `backup_available` is `False`.
        bool: Whether the user wants to load the backup.
    """
    _ = get_qapp()
    dialog = QtWidgets.QDialog()
    ui = Ui_errorDialog()
    ui.setupUi(dialog)
    ui.textLabel.setText(error.msg)
    ui.detailsTextEdit.setPlainText(traceback.format_exc())

    if backup_available:
        ui.buttonBox.addButton("Load Backup", ui.buttonBox.ButtonRole.AcceptRole)
        return dialog.exec() == dialog.DialogCode.Accepted
    else:
        dialog.exec()
        return None


def verify_configs(config_manager: ConfigManager) -> bool:
    """
    Verify configs, notify user of problems, allow loading backups, and return whether
    the configs are valid.

    Returns:
        bool: Whether the configs after valid after all user prompting/potential backup
              loading.
    """
    try:
        config_manager.verify_configs()
    except ConfigFileError as e:
        if (
            isinstance(e, WrongConfigVersionError)
            and e.config_file_version < e.config_class.get_config_version()
        ):
            # This is where code to handle config migrations from 2.0+ config files should go.
            raise e
        logger.exception("")

        config_backup_path = config_manager.get_config_backup_path(
            config_path=e.config_file_path
        )
        # Replace config with backup, if the user clicks the "Load Backup" button.
        if config_backup_path.exists():
            if show_invalid_config_dialog(error=e, backup_available=True):
                e.config_file_path.unlink()
                config_backup_path.rename(e.config_file_path)
                return verify_configs(config_manager=config_manager)
        else:
            show_invalid_config_dialog(error=e)
        return False

    return True


async def start_ui(config_manager: ConfigManager, game_id: GameConfigID | None) -> None:
    # Run setup wizard.
    if not config_manager.program_config_path.exists():
        logger.info("No program config found. Starting setup wizard.")
        setup_wizard = SetupWizard(config_manager)
        await setup_wizard.run()
        if setup_wizard.result() == QtWidgets.QDialog.DialogCode.Rejected:
            # Close program if the user left the setup wizard without finishing.
            return
        return await start_ui(config_manager=config_manager, game_id=game_id)

    try:
        initial_game_id = config_manager.get_initial_game()
    # Run the games selection portion of the setup wizard.
    except NoValidGamesError:
        QtWidgets.QMessageBox.information(
            None,
            "No Games Found",
            f"No games have been registered with {__title__}.\n Opening games management wizard.",
        )
        setup_wizard = SetupWizard(config_manager, game_selection_only=True)
        await setup_wizard.run()
        if setup_wizard.result() == QtWidgets.QDialog.DialogCode.Rejected:
            # Close program if the user left the setup wizard without finishing.
            return
        return await start_ui(config_manager=config_manager, game_id=game_id)

    main_window = MainWindow(
        config_manager=config_manager, game_id=game_id or initial_game_id
    )
    await main_window.run()
