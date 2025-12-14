import inspect
import logging
import os
import subprocess
import sysconfig
from collections.abc import Sequence
from enum import Enum
from functools import partial
from pathlib import Path
from typing import (
    Annotated,
    Literal,
    TypeVar,
    assert_never,
)

import attrs
import cyclopts
from cyclopts import Parameter, Token
from cyclopts.types import (
    ResolvedDirectory,
    ResolvedExistingDirectory,
    ResolvedExistingFile,
)

import onelauncher
from onelauncher.main import start_ui, verify_configs

from .__about__ import __title__, __version__, version_parsed
from .addons.config import AddonsConfigSection
from .addons.startup_script import StartupScript
from .async_utils import start_async_gui
from .config import ConfigFieldMetadata
from .config_manager import (
    GAMES_DIR_DEFAULT,
    PROGRAM_CONFIG_DIR_DEFAULT,
    ConfigManager,
    NoValidGamesError,
    get_converter,
)
from .game_account_config import GameAccountConfig, GameAccountsConfig
from .game_config import ClientType, GameConfig, GameConfigID, GameType
from .logs import LogLevel, setup_application_logging
from .program_config import GamesSortingMode, ProgramConfig
from .resources import OneLauncherLocale
from .ui import qtdesigner
from .utilities import CaseInsensitiveAbsolutePath
from .wine.config import WineConfigSection

logger = logging.getLogger(__name__)


class _GameParamGameType(Enum):
    LOTRO = "lotro"
    LOTRO_PREVIEW = "lotro_preview"
    DDO = "ddo"
    DDO_PREVIEW = "ddo_preview"


_ConverterTypeVar = TypeVar("_ConverterTypeVar", bound=type)


@Parameter(n_tokens=1)
def _cattrs_converter(
    type_: type[_ConverterTypeVar], tokens: Sequence[Token]
) -> _ConverterTypeVar:
    converter = get_converter()
    return converter.structure(tokens[0].value, type_)


def _get_help(field_name: str, /, attrs_class: type[attrs.AttrsInstance]) -> str | None:
    return ConfigFieldMetadata.from_field_name(
        field_name=field_name, attrs_class=attrs_class
    ).help


def _merge_program_config(
    program_config: ProgramConfig,
    *,
    default_locale: OneLauncherLocale | None,
    always_use_default_locale_for_ui: bool | None,
    games_sorting_mode: GamesSortingMode | None,
    log_verbosity: LogLevel | None,
) -> ProgramConfig:
    """
    Merge `program_config` with CLI options. Any specified CLI options will
    override the existing values in `program_config`.
    """
    return attrs.evolve(
        program_config,
        default_locale=(default_locale or program_config.default_locale),
        always_use_default_locale_for_ui=(
            always_use_default_locale_for_ui
            if always_use_default_locale_for_ui is not None
            else program_config.always_use_default_locale_for_ui
        ),
        games_sorting_mode=(games_sorting_mode or program_config.games_sorting_mode),
        log_verbosity=(
            log_verbosity if log_verbosity is not None else program_config.log_verbosity
        ),
    )


def _merge_game_config(
    game_config: GameConfig,
    *,
    game_directory: CaseInsensitiveAbsolutePath | None,
    locale: OneLauncherLocale | None,
    client_type: ClientType | None,
    high_res_enabled: bool | None,
    standard_game_launcher_filename: str | None,
    patch_client_filename: str | None,
    game_settings_directory: CaseInsensitiveAbsolutePath | None,
    newsfeed: str | None,
    # Addons Section
    enabled_startup_scripts: tuple[Path, ...] | None,
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
            game_directory if game_directory is not None else game_config.game_directory
        ),
        locale=(locale if locale is not None else game_config.locale),
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
            game_settings_directory
            if game_settings_directory is not None
            else game_config.game_settings_directory
        ),
        newsfeed=(newsfeed if newsfeed is not None else game_config.newsfeed),
        addons=addons_section,
        wine=wine_section,
    )


def _merge_accounts_config(
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


ProgramGroup = cyclopts.Group.create_ordered(name="Program Options")
GameGroup = cyclopts.Group.create_ordered(name="Game Options")
AccountGroup = cyclopts.Group.create_ordered(name="Game Account Options")
AddonsGroup = cyclopts.Group.create_ordered(name="Game Addons Options")
WineGroup = cyclopts.Group.create_ordered(
    name="Game WINE Options", show=os.name != "nt"
)
DevGroup = cyclopts.Group.create_ordered(
    name="Dev Stuff", show=version_parsed.is_devrelease
)

prog_help = partial(_get_help, attrs_class=ProgramConfig)
game_help = partial(_get_help, attrs_class=GameConfig)
account_help = partial(_get_help, attrs_class=GameAccountConfig)
addons_help = partial(_get_help, attrs_class=AddonsConfigSection)
wine_help = partial(_get_help, attrs_class=WineConfigSection)


def get_app() -> cyclopts.App:
    app = cyclopts.App(
        name=__title__.lower(),
        version=__version__,
        help=(
            "Environment variables can also be used. For example, `--config-directory` "
            "can be set with `ONELAUNCHER_CONFIG_DIRECTORY`."
        ),
        config=cyclopts.config.Env(prefix=f"{__title__.upper()}_", show=False),
        default_parameter=Parameter(consume_multiple=True),
    )
    _config_manager: ConfigManager | None = None
    _game_id: GameConfigID | None = None

    def parse_game_arg(
        game_arg: _GameParamGameType | GameConfigID, config_manager: ConfigManager
    ) -> GameConfigID:
        """
        Raises:
            ValueError
        """
        game_ids = config_manager.get_games_sorted(
            config_manager.get_program_config().games_sorting_mode
        )

        if isinstance(game_arg, _GameParamGameType):
            match game_arg:
                case _GameParamGameType.LOTRO:
                    game_type = GameType.LOTRO
                    is_preview = False
                case _GameParamGameType.LOTRO_PREVIEW:
                    game_type = GameType.LOTRO
                    is_preview = True
                case _GameParamGameType.DDO:
                    game_type = GameType.DDO
                    is_preview = False
                case _GameParamGameType.DDO_PREVIEW:
                    game_type = GameType.DDO
                    is_preview = True
                case _:
                    assert_never(game_arg)
            for game_id in game_ids:
                game_config = config_manager.read_game_config_file(game_id=game_id)
                if (
                    game_config.game_type == game_type
                    and game_config.is_preview_client == is_preview
                ):
                    return game_id
            raise ValueError(f"No {game_arg} games exist")

        if game_arg in game_ids:
            return game_arg
        else:
            raise ValueError("Provided game type or game config ID does not exist")

    def validate_game_param(
        type_: type[_GameParamGameType | GameConfigID | None],
        value: _GameParamGameType | GameConfigID | None,
    ) -> None:
        if isinstance(value, _GameParamGameType | GameConfigID) and _config_manager:
            parse_game_arg(game_arg=value, config_manager=_config_manager)

    # --- Commands ---
    # They all return an exit code integer.

    @app.meta.meta.default
    def meta_meta(
        *tokens: Annotated[str, Parameter(show=False, allow_leading_hyphen=True)],
        config_directory: Annotated[
            ResolvedDirectory,
            Parameter(help=f"Where {__title__} settings are stored"),
        ] = PROGRAM_CONFIG_DIR_DEFAULT,
        games_directory: Annotated[
            ResolvedDirectory,
            Parameter(help=f"Where {__title__} game specific data is stored"),
        ] = GAMES_DIR_DEFAULT,
    ) -> int:
        nonlocal _config_manager
        _config_manager = ConfigManager(
            program_config_dir=config_directory,
            games_dir=games_directory,
        )
        if not verify_configs(config_manager=_config_manager):
            return 1

        _command, bound, _ignored = app.meta.parse_args(tokens)
        return meta(*bound.args, **bound.kwargs, config_manager=_config_manager)

    @app.meta.default
    def meta(
        *tokens: Annotated[str, Parameter(show=False, allow_leading_hyphen=True)],
        config_manager: Annotated[ConfigManager, Parameter(parse=False)],
        # Program options
        default_locale: Annotated[
            OneLauncherLocale | None,
            Parameter(
                group=ProgramGroup,
                help=prog_help("default_locale"),
                converter=_cattrs_converter,
            ),
        ] = None,
        always_use_default_locale_for_ui: Annotated[
            bool | None,
            Parameter(
                group=ProgramGroup, help=prog_help("always_use_default_locale_for_ui")
            ),
        ] = None,
        games_sorting_mode: Annotated[
            GamesSortingMode | None,
            Parameter(group=ProgramGroup, help=prog_help("games_sorting_mode")),
        ] = None,
        log_verbosity: Annotated[
            LogLevel | None,
            Parameter(group=ProgramGroup, help=prog_help("log_verbosity")),
        ] = None,
        # Game
        game: Annotated[
            _GameParamGameType | GameConfigID | None,
            Parameter(
                help=(
                    "Which game to load. Can be either a game type or game config ID."
                ),
                validator=validate_game_param,
            ),
        ] = None,
    ) -> int:
        config_manager.get_merged_program_config = partial(
            _merge_program_config,
            default_locale=default_locale,
            always_use_default_locale_for_ui=always_use_default_locale_for_ui,
            games_sorting_mode=games_sorting_mode,
            log_verbosity=log_verbosity,
        )
        nonlocal _game_id
        if game is None:
            try:
                _game_id = config_manager.get_initial_game()
            except NoValidGamesError:
                _game_id = None
        else:
            _game_id = parse_game_arg(game_arg=game, config_manager=config_manager)

        command, bound, _ignored = app.parse_args(tokens)
        if command is default:
            return default(*bound.args, **bound.kwargs, config_manager=config_manager)
        elif command is app["--install-completion"].default_command:
            command(*bound.args, **bound.kwargs)
            return 0
        else:
            raise ValueError(f"Unhandled command: {command}")

    @app.default
    def default(
        *,
        config_manager: Annotated[ConfigManager, Parameter(parse=False)],
        # Game options
        game_directory: Annotated[
            CaseInsensitiveAbsolutePath | None,
            Parameter(
                group=GameGroup,
                help=game_help("game_directory"),
                converter=_cattrs_converter,
                validator=cyclopts.validators.Path(exists=True, file_okay=False),
            ),
        ] = None,
        locale: Annotated[
            OneLauncherLocale | None,
            Parameter(
                group=GameGroup, help=game_help("locale"), converter=_cattrs_converter
            ),
        ] = None,
        client_type: Annotated[
            ClientType | None,
            Parameter(group=GameGroup, help=game_help("client_type")),
        ] = None,
        high_res_enabled: Annotated[
            bool | None, Parameter(group=GameGroup, help=game_help("high_res_enabled"))
        ] = None,
        standard_game_launcher_filename: Annotated[
            str | None,
            Parameter(
                group=GameGroup, help=game_help("standard_game_launcher_filename")
            ),
        ] = None,
        patch_client_filename: Annotated[
            str | None,
            Parameter(group=GameGroup, help=game_help("patch_client_filename")),
        ] = None,
        game_settings_directory: Annotated[
            CaseInsensitiveAbsolutePath | None,
            Parameter(
                group=GameGroup,
                help=game_help("game_settings_directory"),
                converter=_cattrs_converter,
                validator=cyclopts.validators.Path(file_okay=False),
            ),
        ] = None,
        newsfeed: Annotated[
            str | None, Parameter(group=GameGroup, help=game_help("newsfeed"))
        ] = None,
        # Account options
        username: Annotated[
            str | None,
            Parameter(
                group=AccountGroup,
                help=account_help("username"),
            ),
        ] = None,
        display_name: Annotated[
            str | None, Parameter(group=AccountGroup, help=account_help("display_name"))
        ] = None,
        last_used_world_name: Annotated[
            str | None,
            Parameter(group=AccountGroup, help=account_help("last_used_world_name")),
        ] = None,
        # Addons options
        startup_scripts: Annotated[
            tuple[Path, ...] | None,
            Parameter(
                group=AddonsGroup,
                help=addons_help("enabled_startup_scripts"),
                validator=cyclopts.validators.Path(
                    exists=False, file_okay=True, dir_okay=False, ext=("py",)
                ),
            ),
        ] = None,
        # Game WINE options
        builtin_prefix_enabled: Annotated[
            bool | None,
            Parameter(group=WineGroup, help=wine_help("builtin_prefix_enabled")),
        ] = None,
        user_wine_executable_path: Annotated[
            ResolvedExistingFile | None,
            Parameter(
                group=WineGroup,
                help=wine_help("user_wine_executable_path"),
            ),
        ] = None,
        user_prefix_path: Annotated[
            ResolvedExistingDirectory | None,
            Parameter(
                group=WineGroup,
                help=wine_help("user_prefix_path"),
            ),
        ] = None,
        wine_debug_level: Annotated[
            str | None, Parameter(group=WineGroup, help=wine_help("debug_level"))
        ] = None,
    ) -> int:
        setup_application_logging(
            log_level_override=config_manager.get_program_config().log_verbosity
        )
        config_manager.get_merged_game_config = partial(
            _merge_game_config,
            game_directory=game_directory,
            locale=locale,
            client_type=client_type,
            high_res_enabled=high_res_enabled,
            standard_game_launcher_filename=standard_game_launcher_filename,
            patch_client_filename=patch_client_filename,
            game_settings_directory=game_settings_directory,
            newsfeed=newsfeed,
            # Addons Section
            enabled_startup_scripts=startup_scripts,
            # WINE Section
            builtin_prefix_enabled=builtin_prefix_enabled,
            user_wine_executable_path=user_wine_executable_path,
            user_prefix_path=user_prefix_path,
            wine_debug_level=wine_debug_level,
        )
        config_manager.get_merged_game_accounts_config = partial(
            _merge_accounts_config,
            username=username,
            display_name=display_name,
            last_used_world_name=last_used_world_name,
        )

        return start_async_gui(
            entry=partial(start_ui, config_manager=config_manager, game_id=_game_id),
        )

    @app.meta.meta.command(group=DevGroup)
    def designer() -> int:
        """Start pyside6-designer with the correct plugins and environment variables."""
        env = os.environ.copy()
        env["PYTHONPATH"] = (
            f"{env['PYTHONPATH']}{os.pathsep}" if "PYTHONPATH" in env else ""
        )
        env["PYTHONPATH"] += (
            f"{sysconfig.get_path('purelib')}{os.pathsep}{Path(inspect.getabsfile(onelauncher)).parent.parent}"
        )
        env["PYSIDE_DESIGNER_PLUGINS"] = str(
            Path(inspect.getabsfile(qtdesigner)).parent
        )
        if nix_python := os.environ.get("NIX_PYTHON_ENV"):
            # Trick pyside6-designer into setting the right LD_PRELOAD path for Python
            # in Nix flake instead of the bare library name.
            env["PYENV_ROOT"] = nix_python
        subprocess.run(
            "pyside6-designer",  # noqa: S607
            env=env,
            check=True,
        )
        return 0

    app.register_install_completion_command()

    @app.meta.meta.command(show=False)
    def generate_shell_completion(
        shell: Literal["zsh", "bash", "fish"] | None = None,
    ) -> int:
        print(app.generate_completion(shell=shell))  # noqa: T201
        return 0

    return app.meta.meta
