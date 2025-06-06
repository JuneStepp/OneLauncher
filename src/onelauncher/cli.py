# ruff: noqa: UP007
from __future__ import annotations

import inspect
import logging
import os
import subprocess
import sys
import sysconfig
import traceback
from collections.abc import Awaitable, Callable, Iterator
from enum import StrEnum
from functools import partial
from pathlib import Path
from typing import Annotated, Optional, assert_never

import attrs
import click
import rich
import typer
from PySide6 import QtCore, QtWidgets
from typer.core import TyperGroup as TyperGroupBase
from typing_extensions import override

import onelauncher

from .__about__ import __title__, __version__, version_parsed
from .addons.config import AddonsConfigSection
from .addons.startup_script import StartupScript
from .async_utils import AsyncHelper, app_cancel_scope
from .config import ConfigFieldMetadata
from .config_manager import (
    ConfigFileError,
    ConfigManager,
    WrongConfigVersionError,
    get_converter,
)
from .game_account_config import GameAccountConfig, GameAccountsConfig
from .game_config import ClientType, GameConfig, GameConfigID, GameType
from .logs import setup_application_logging
from .program_config import GamesSortingMode, ProgramConfig
from .qtapp import get_qapp
from .resources import OneLauncherLocale
from .setup_wizard import SetupWizard
from .ui import qtdesigner
from .ui.error_message_uic import Ui_errorDialog
from .utilities import CaseInsensitiveAbsolutePath
from .wine.config import WineConfigSection

logger = logging.getLogger(__name__)


class TyperGroup(TyperGroupBase):
    """Custom TyperGroup class."""

    @override
    def get_usage(self, context: click.Context) -> str:
        """Add app title above usage section"""
        usage = super().get_usage(context)
        return f"{__title__} {__version__} \n\n {usage}"


app = typer.Typer(
    context_settings={"help_option_names": ["--help", "-h"]},
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
    cls=TyperGroup,
)


def version_calback(value: bool) -> None:
    if value:
        rich.print(f"[bold]{__title__}[/bold] [cyan]{__version__}[/cyan]")
        raise typer.Exit()


def merge_program_config(
    program_config: ProgramConfig,
    *,
    default_locale: Optional[str],
    always_use_default_locale_for_ui: Optional[bool],
    games_sorting_mode: Optional[GamesSortingMode],
) -> ProgramConfig:
    """
    Merge `program_config` with CLI options. Any specified CLI options will
    override the existing values in `program_config`.
    """
    converter = get_converter()
    default_locale_structured = (
        converter.structure(default_locale, OneLauncherLocale)
        if default_locale
        else None
    )

    return attrs.evolve(
        program_config,
        default_locale=(default_locale_structured or program_config.default_locale),
        always_use_default_locale_for_ui=(
            always_use_default_locale_for_ui
            if always_use_default_locale_for_ui is not None
            else program_config.always_use_default_locale_for_ui
        ),
        games_sorting_mode=(games_sorting_mode or program_config.games_sorting_mode),
    )


def merge_game_config(
    game_config: GameConfig,
    *,
    game_directory: Path | None,
    locale: str | None,
    client_type: ClientType | None,
    high_res_enabled: bool | None,
    standard_game_launcher_filename: str | None,
    patch_client_filename: str | None,
    game_settings_directory: Path | None,
    newsfeed: str | None,
    # Addons Section
    enabled_startup_scripts: list[Path] | None,
    # WINE section
    builtin_prefix_enabled: bool | None,
    user_wine_executable_path: Path | None,
    user_prefix_path: Path | None,
    wine_debug_level: str | None,
) -> GameConfig:
    """
    Merge `game_config` with CLI options. Any specified CLI options will
    override the existing values in `game_config`.
    """
    converter = get_converter()
    locale_structured = (
        converter.structure(locale, OneLauncherLocale) if locale else None
    )

    startup_scripts_structured = (
        tuple(
            converter.structure(script, StartupScript)
            for script in enabled_startup_scripts
        )
        if enabled_startup_scripts
        else None
    )
    addons_section = attrs.evolve(
        game_config.addons,
        enabled_startup_scripts=(
            startup_scripts_structured
            if startup_scripts_structured is not None
            else game_config.addons.enabled_startup_scripts
        ),
    )

    wine_section = attrs.evolve(
        game_config.wine,
        builtin_prefix_enabled=(
            builtin_prefix_enabled
            if builtin_prefix_enabled is not None
            else game_config.wine.builtin_prefix_enabled
        ),
        user_wine_executable_path=(
            user_wine_executable_path
            if user_wine_executable_path is not None
            else game_config.wine.user_wine_executable_path
        ),
        user_prefix_path=(
            user_prefix_path
            if user_prefix_path is not None
            else game_config.wine.user_prefix_path
        ),
        debug_level=(
            wine_debug_level
            if wine_debug_level is not None
            else game_config.wine.debug_level
        ),
    )
    return attrs.evolve(
        game_config,
        game_directory=(
            CaseInsensitiveAbsolutePath(game_directory)
            if game_directory is not None
            else game_config.game_directory
        ),
        locale=(
            locale_structured if locale_structured is not None else game_config.locale
        ),
        client_type=(
            client_type if client_type is not None else game_config.client_type
        ),
        high_res_enabled=(
            high_res_enabled
            if high_res_enabled is not None
            else game_config.high_res_enabled
        ),
        standard_game_launcher_filename=(
            standard_game_launcher_filename
            if standard_game_launcher_filename is not None
            else game_config.standard_game_launcher_filename
        ),
        patch_client_filename=(
            patch_client_filename
            if patch_client_filename is not None
            else game_config.patch_client_filename
        ),
        game_settings_directory=(
            CaseInsensitiveAbsolutePath(game_settings_directory)
            if game_settings_directory is not None
            else game_config.game_settings_directory
        ),
        newsfeed=(newsfeed if newsfeed is not None else game_config.newsfeed),
        addons=addons_section,
        wine=wine_section,
    )


def merge_accounts_config(
    game_accounts_config: GameAccountsConfig,
    *,
    username: str | None,
    display_name: str | None,
    last_used_world_name: str | None,
) -> GameAccountsConfig:
    """
    Merge `game_accounts_config` with CLI options. Any specified CLI options
    will override the existing values in `game_accounts_config`.
    """
    accounts = list(game_accounts_config.accounts)
    if not username and not accounts:
        return game_accounts_config
    elif not username:
        account = accounts[0]
        accounts.remove(account)
    elif matching_accounts := tuple(
        account for account in accounts if account.username == username
    ):
        account = matching_accounts[0]
        accounts.remove(account)
    else:
        account = GameAccountConfig(username=username)
    evolved_account = attrs.evolve(
        account,
        display_name=(
            display_name if display_name is not None else account.display_name
        ),
        last_used_world_name=(
            last_used_world_name
            if last_used_world_name is not None
            else account.last_used_world_name
        ),
    )
    accounts.insert(0, evolved_account)

    return attrs.evolve(game_accounts_config, accounts=tuple(accounts))


class GameOptions(StrEnum):
    LOTRO = "lotro"
    LOTRO_PREVIEW = "lotro_preview"
    DDO = "ddo"
    DDO_PREVIEW = "ddo_preview"


def game_type_or_id(value: str) -> str:
    if value.lower() in list(GameOptions):
        return value.lower()
    return value


def _parse_game_arg(game_arg: str, config_manager: ConfigManager) -> GameConfigID:
    """
    Raises:
        typer.BadParameter
    """
    game_ids = config_manager.get_games_sorted(
        config_manager.get_program_config().games_sorting_mode
    )

    # Handle game config ID game arg
    if game_arg not in tuple(GameOptions):
        game_id = game_arg
        if game_id not in game_ids:
            raise typer.BadParameter(
                message="Provided game config ID does not exist", param_hint="--game"
            )
        return game_id

    game_option = GameOptions(game_arg)
    match game_option:
        case GameOptions.LOTRO:
            game_type = GameType.LOTRO
            is_preview = False
        case GameOptions.LOTRO_PREVIEW:
            game_type = GameType.LOTRO
            is_preview = True
        case GameOptions.DDO:
            game_type = GameType.DDO
            is_preview = False
        case GameOptions.DDO_PREVIEW:
            game_type = GameType.DDO
            is_preview = True
        case _:
            assert_never(game_option)
    for game_id in game_ids:
        game_config = config_manager.read_game_config_file(game_id=game_id)
        if (
            game_config.game_type == game_type
            and game_config.is_preview_client == is_preview
        ):
            return game_id
    raise typer.BadParameter(message=f"No {game_arg} games exist", param_hint="--game")


def _complete_game_arg(incomplete: str) -> Iterator[str]:
    config_manager = ConfigManager(lambda c: c, lambda c: c, lambda c: c)
    try:
        config_manager.verify_configs()
        game_ids = config_manager.get_game_config_ids()
    except ConfigFileError:
        game_ids = ()
    for option in tuple(GameOptions) + game_ids:
        if option.startswith(incomplete):
            yield option


def _complete_username_arg(incomplete: str, context: typer.Context) -> Iterator[str]:
    game_arg: str | None = context.params.get("game")
    if not game_arg:
        return
    config_manager = ConfigManager(lambda c: c, lambda c: c, lambda c: c)
    config_manager.verify_configs()
    try:
        game_id = _parse_game_arg(game_arg=game_arg, config_manager=config_manager)
    except typer.BadParameter:
        return
    usernames = (
        account.username
        for account in config_manager.read_game_accounts_config_file(game_id)
    )
    for option in usernames:
        if option.startswith(incomplete):
            yield option


ProgramOption = partial(
    typer.Option, show_default=False, rich_help_panel="Program Options"
)
GameOption = partial(typer.Option, show_default=False, rich_help_panel="Game Options")
AccountOption = partial(
    typer.Option, show_default=False, rich_help_panel="Game Account Options"
)
AddonsOption = partial(
    typer.Option, show_default=False, rich_help_panel="Game Addons Options"
)
WineOption = partial(
    typer.Option,
    show_default=False,
    rich_help_panel="Game WINE Options",
    hidden=os.name == "nt",
)
DevOption = partial(
    typer.Option,
    show_default=True,
    rich_help_panel="Dev Stuff",
    hidden=not version_parsed.is_devrelease,
)
dev_command = partial(
    app.command,
    hidden=not version_parsed.is_devrelease,
    rich_help_panel="Dev Stuff",
)


def get_help(field_name: str, /, attrs_class: type[attrs.AttrsInstance]) -> str | None:
    return ConfigFieldMetadata.from_field_name(
        field_name=field_name, attrs_class=attrs_class
    ).help


prog_help = partial(get_help, attrs_class=ProgramConfig)
game_help = partial(get_help, attrs_class=GameConfig)
account_help = partial(get_help, attrs_class=GameAccountConfig)
addons_help = partial(get_help, attrs_class=AddonsConfigSection)
wine_help = partial(get_help, attrs_class=WineConfigSection)


@app.callback(invoke_without_command=True)
def main(
    context: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Print version and exit.",
            is_eager=True,
            callback=version_calback,
        ),
    ] = False,
    # Program options
    default_locale: Annotated[
        Optional[str], ProgramOption(help=prog_help("default_locale"))
    ] = None,
    always_use_default_locale_for_ui: Annotated[
        Optional[bool],
        ProgramOption(help=prog_help("always_use_default_locale_for_ui")),
    ] = None,
    games_sorting_mode: Annotated[
        Optional[GamesSortingMode], ProgramOption(help=prog_help("games_sorting_mode"))
    ] = None,
    # Game options
    game: Annotated[
        Optional[str],
        GameOption(
            help=(
                "Which game to load. ([yellow]"
                f"{', '.join(GameOptions)}, or a game config ID)"
            ),
            parser=game_type_or_id,
            autocompletion=_complete_game_arg,
        ),
    ] = None,
    game_directory: Annotated[
        Optional[Path],
        GameOption(
            help=game_help("game_directory"),
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
    locale: Annotated[Optional[str], GameOption(help=game_help("locale"))] = None,
    client_type: Annotated[
        Optional[ClientType],
        GameOption(help=game_help("client_type"), case_sensitive=False),
    ] = None,
    high_res_enabled: Annotated[
        Optional[bool], GameOption(help=game_help("high_res_enabled"))
    ] = None,
    standard_game_launcher_filename: Annotated[
        Optional[str], GameOption(help=game_help("standard_game_launcher_filename"))
    ] = None,
    patch_client_filename: Annotated[
        Optional[str], GameOption(help=game_help("patch_client_filename"))
    ] = None,
    game_settings_directory: Annotated[
        Optional[Path],
        GameOption(
            help=game_help("game_settings_directory"),
            exists=False,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
    newsfeed: Annotated[Optional[str], GameOption(help=game_help("newsfeed"))] = None,
    # Account options
    username: Annotated[
        Optional[str],
        AccountOption(
            help=account_help("username"), autocompletion=_complete_username_arg
        ),
    ] = None,
    display_name: Annotated[
        Optional[str], AccountOption(help=account_help("display_name"))
    ] = None,
    last_used_world_name: Annotated[
        Optional[str], AccountOption(help=account_help("last_used_world_name"))
    ] = None,
    # Addons options
    startup_script: Annotated[
        Optional[list[Path]],
        AddonsOption(
            help=addons_help("enabled_startup_scripts"),
            file_okay=True,
            dir_okay=False,
            resolve_path=False,
            exists=False,
        ),
    ] = None,
    # Game WINE options
    builtin_prefix_enabled: Annotated[
        Optional[bool], WineOption(help=wine_help("builtin_prefix_enabled"))
    ] = None,
    user_wine_executable_path: Annotated[
        Optional[Path],
        WineOption(
            help=wine_help("user_wine_executable_path"),
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    user_prefix_path: Annotated[
        Optional[Path],
        WineOption(
            help=wine_help("user_prefix_path"),
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
    wine_debug_level: Annotated[
        Optional[str], WineOption(help=wine_help("debug_level"))
    ] = None,
) -> None:
    # Don't run when other command or autocompletion is invoked
    if context.invoked_subcommand is not None or context.resilient_parsing:
        return
    setup_application_logging()
    get_merged_program_config = partial(
        merge_program_config,
        default_locale=default_locale,
        always_use_default_locale_for_ui=always_use_default_locale_for_ui,
        games_sorting_mode=games_sorting_mode,
    )
    get_merged_game_config = partial(
        merge_game_config,
        game_directory=game_directory,
        locale=locale,
        client_type=client_type,
        high_res_enabled=high_res_enabled,
        standard_game_launcher_filename=standard_game_launcher_filename,
        patch_client_filename=patch_client_filename,
        game_settings_directory=game_settings_directory,
        newsfeed=newsfeed,
        # Addons Section
        enabled_startup_scripts=startup_script,
        # WINE Section
        builtin_prefix_enabled=builtin_prefix_enabled,
        user_wine_executable_path=user_wine_executable_path,
        user_prefix_path=user_prefix_path,
        wine_debug_level=wine_debug_level,
    )
    get_merged_game_accounts_config = partial(
        merge_accounts_config,
        username=username,
        display_name=display_name,
        last_used_world_name=last_used_world_name,
    )
    config_manager = ConfigManager(
        get_merged_program_config=get_merged_program_config,
        get_merged_game_config=get_merged_game_config,
        get_merged_game_accounts_config=get_merged_game_accounts_config,
    )
    qapp = get_qapp()
    entry = partial(_start_ui, config_manager=config_manager, game_arg=game)
    async_helper = AsyncHelper(partial(_main, entry=entry))
    QtCore.QTimer.singleShot(0, async_helper.launch_guest_run)
    # qapp.exec() won't return until trio event loop finishes
    sys.exit(qapp.exec())


@dev_command()
def designer() -> None:
    """Start pyside6-designer with correct environment variables"""
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        f"{env['PYTHONPATH']}{os.pathsep}" if "PYTHONPATH" in env else ""
    )
    env["PYTHONPATH"] += (
        f"{sysconfig.get_path('purelib')}{os.pathsep}{Path(inspect.getabsfile(onelauncher)).parent.parent}"
    )
    env["PYSIDE_DESIGNER_PLUGINS"] = str(Path(inspect.getabsfile(qtdesigner)).parent)
    if nix_python := os.environ.get("NIX_PYTHON_ENV"):
        # Trick pyside6-designer into setting the right LD_PRELOAD path for Python
        # in Nix flake instead of the bare library name.
        env["PYENV_ROOT"] = nix_python
    subprocess.run(  # noqa: S603
        "pyside6-designer",  # noqa: S607
        env=env,
        check=True,
    )


async def _main(entry: Callable[[], Awaitable[None]]) -> None:
    with app_cancel_scope:
        await entry()


async def _start_ui(config_manager: ConfigManager, game_arg: str | None) -> None:
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
        dialog = QtWidgets.QDialog()
        ui = Ui_errorDialog()
        ui.setupUi(dialog)
        ui.textLabel.setText(e.msg)
        ui.detailsTextEdit.setPlainText(traceback.format_exc())
        config_backup_path = config_manager.get_config_backup_path(
            config_path=e.config_file_path
        )
        if config_backup_path.exists():
            ui.buttonBox.addButton("Load Backup", ui.buttonBox.ButtonRole.AcceptRole)
            # Replace config with backup, if the user clicks the "Load Backup" button
            if dialog.exec() == dialog.DialogCode.Accepted:
                e.config_file_path.unlink()
                config_backup_path.rename(e.config_file_path)
                return await _start_ui(config_manager=config_manager, game_arg=game_arg)
        else:
            dialog.exec()
        return

    # Run setup wizard
    if not config_manager.program_config_path.exists():
        setup_wizard = SetupWizard(config_manager)
        if setup_wizard.exec() == QtWidgets.QDialog.DialogCode.Rejected:
            # Close program if the user left the setup wizard without finishing
            return
        return await _start_ui(config_manager=config_manager, game_arg=game_arg)

    # Just run the games selection portion of the setup wizard
    if not config_manager.get_game_config_ids():
        QtWidgets.QMessageBox.information(
            None,  # type: ignore[arg-type]
            "No Games Found",
            f"No games have been registered with {__title__}.\n Opening games management wizard.",
        )
        setup_wizard = SetupWizard(config_manager, game_selection_only=True)
        if setup_wizard.exec() == QtWidgets.QDialog.DialogCode.Rejected:
            # Close program if the user left the setup wizard without finishing
            return
        return await _start_ui(config_manager=config_manager, game_arg=game_arg)

    # Import has to be done here, because some code run when
    # main_window.py imports requires the QApplication to exist.
    from .main_window import MainWindow

    game_id = _parse_game_arg(game_arg, config_manager) if game_arg else None
    main_window = MainWindow(config_manager=config_manager, starting_game_id=game_id)
    await main_window.run()
