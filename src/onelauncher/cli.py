# ruff: noqa: UP007
from __future__ import annotations

import logging
import os
import sys
import traceback
from collections.abc import Awaitable, Callable, Iterator
from enum import StrEnum
from functools import partial
from pathlib import Path
from typing import Annotated, Optional
from uuid import UUID

import attrs
import click
import rich
import typer
from PySide6 import QtCore, QtWidgets
from typer.core import TyperGroup as TyperGroupBase

from .__about__ import __title__, __version__
from .async_utils import AsyncHelper, app_cancel_scope
from .config import ConfigFieldMetadata
from .config_manager import (
    ConfigFileParseError,
    ConfigManager,
    get_converter,
)
from .game_account_config import GameAccountConfig, GameAccountsConfig
from .game_config import ClientType, GameConfig, GameType
from .logs import setup_application_logging
from .program_config import GamesSortingMode, ProgramConfig
from .qtapp import setup_qtapplication
from .resources import OneLauncherLocale
from .setup_wizard import SetupWizard
from .ui.error_message_uic import Ui_errorDialog
from .utilities import CaseInsensitiveAbsolutePath
from .wine.config import WineConfigSection

setup_application_logging()
logger = logging.getLogger("main")


class TyperGroup(TyperGroupBase):
    """Custom TyperGroup class."""

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
    save_accounts: Optional[bool],
    save_accounts_passwords: Optional[bool],
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
        save_accounts=(
            save_accounts if save_accounts is not None else program_config.save_accounts
        ),
        save_accounts_passwords=(
            save_accounts_passwords
            if save_accounts_passwords is not None
            else program_config.save_accounts_passwords
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
    newsfeed: str | None,
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
        newsfeed=(newsfeed if newsfeed is not None else game_config.newsfeed),
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


def game_type_or_uuid(value: str) -> str:
    if value.lower() in list(GameOptions):
        return value.lower()

    try:
        UUID(value)
    except ValueError as e:
        raise typer.BadParameter("Invalid UUID or game type") from e

    return value


def _parse_game_arg(game_arg: str, config_manager: ConfigManager) -> UUID:
    """
    Raises:
        typer.BadParameter
    """
    game_uuids = config_manager.get_games_sorted(
        config_manager.get_program_config().games_sorting_mode
    )

    # Handle UUID game arg
    if game_arg not in tuple(GameOptions):
        game_uuid = UUID(game_arg)
        if game_uuid not in game_uuids:
            raise typer.BadParameter(
                message="Provided game UUID does not exist", param_hint="--game"
            )
        return game_uuid

    match GameOptions(game_arg):
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
    for game_uuid in game_uuids:
        game_config = config_manager.read_game_config_file(game_uuid=game_uuid)
        if (
            game_config.game_type == game_type
            and game_config.is_preview_client == is_preview
        ):
            return game_uuid
    raise typer.BadParameter(message=f"No {game_arg} games exist", param_hint="--game")


def _complete_game_arg(incomplete: str) -> Iterator[str]:
    config_manager = ConfigManager(lambda c: c, lambda c: c, lambda c: c)
    try:
        config_manager.verify_configs()
        game_uuids = tuple(str(uuid) for uuid in config_manager.get_game_uuids())
    except ConfigFileParseError:
        game_uuids = ()
    for option in tuple(GameOptions) + game_uuids:
        if option.startswith(incomplete):
            yield option


def _complete_username_arg(incomplete: str, context: typer.Context) -> Iterator[str]:
    game_arg: str | None = context.params.get("game")
    if not game_arg:
        return
    config_manager = ConfigManager(lambda c: c, lambda c: c, lambda c: c)
    config_manager.verify_configs()
    try:
        game_uuid = _parse_game_arg(game_arg=game_arg, config_manager=config_manager)
    except typer.BadParameter:
        return
    usernames = (
        account.username
        for account in config_manager.read_game_accounts_config_file(game_uuid)
    )
    for option in usernames:
        if option.startswith(incomplete):
            yield option


ProgramOption = partial(
    typer.Option, show_default=False, rich_help_panel="Program Options"
)

GameOption = partial(typer.Option, show_default=False, rich_help_panel="Game Options")

WineOption = partial(
    typer.Option,
    show_default=False,
    rich_help_panel="Game WINE Options",
    hidden=os.name == "nt",
)

AccountOption = partial(
    typer.Option, show_default=False, rich_help_panel="Game Account Options"
)


def get_help(field_name: str, /, attrs_class: type[attrs.AttrsInstance]) -> str | None:
    return ConfigFieldMetadata.from_field_name(
        field_name=field_name, attrs_class=attrs_class
    ).help


prog_help = partial(get_help, attrs_class=ProgramConfig)
game_help = partial(get_help, attrs_class=GameConfig)
wine_help = partial(get_help, attrs_class=WineConfigSection)
account_help = partial(get_help, attrs_class=GameAccountConfig)


@app.callback(invoke_without_command=True)
def main(
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
    save_accounts: Annotated[
        Optional[bool], ProgramOption(help=prog_help("save_accounts"))
    ] = None,
    save_accounts_passwords: Annotated[
        Optional[bool], ProgramOption(help=prog_help("save_accounts_passwords"))
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
                f"{', '.join(GameOptions)}, or a game UUID)"
            ),
            parser=game_type_or_uuid,
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
    newsfeed: Annotated[Optional[str], GameOption(help=game_help("newsfeed"))] = None,
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
) -> None:
    get_merged_program_config = partial(
        merge_program_config,
        default_locale=default_locale,
        always_use_default_locale_for_ui=always_use_default_locale_for_ui,
        save_accounts=save_accounts,
        save_accounts_passwords=save_accounts_passwords,
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
        newsfeed=newsfeed,
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
    qapp = setup_qtapplication()
    entry = partial(_start_ui, config_manager=config_manager, game_arg=game)
    async_helper = AsyncHelper(partial(_main, entry=entry))
    QtCore.QTimer.singleShot(0, async_helper.launch_guest_run)
    # qapp.exec() won't return until trio event loop finishes
    sys.exit(qapp.exec())


async def _main(entry: Callable[[], Awaitable[None]]) -> None:
    with app_cancel_scope:
        await entry()


async def _start_ui(config_manager: ConfigManager, game_arg: str | None) -> None:
    # Check before verifying configs, because the config manager will make a new config,
    # if one doesn't exist.
    program_config_exists = config_manager.program_config_path.exists()

    try:
        config_manager.verify_configs()
    except ConfigFileParseError:
        logger.exception("")
        dialog = QtWidgets.QDialog()
        ui = Ui_errorDialog()
        ui.setupUi(dialog)  # type: ignore
        ui.textLabel.setText("Error parsing config file:")
        ui.detailsTextEdit.setPlainText(traceback.format_exc())
        dialog.exec()
        return

    # Run setup wizard
    if not program_config_exists:
        setup_wizard = SetupWizard(config_manager)
        if setup_wizard.exec() == QtWidgets.QDialog.DialogCode.Rejected:
            # Close program if the user left the setup wizard without finishing
            return
        return await _start_ui(config_manager=config_manager, game_arg=game_arg)

    # Just run the games selection portion of the setup wizard
    if not config_manager.get_game_uuids():
        QtWidgets.QMessageBox.information(  # type: ignore[call-overload]
            None,
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

    game_uuid = _parse_game_arg(game_arg, config_manager) if game_arg else None
    main_window = MainWindow(
        config_manager=config_manager, starting_game_uuid=game_uuid
    )
    await main_window.run()
