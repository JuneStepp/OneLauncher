import datetime
from collections.abc import Callable
from contextlib import suppress
from functools import cache, partial
from pathlib import Path
from shutil import rmtree
from typing import Any, Final, TypeAlias, TypeVar

import attrs
import cattrs
import keyring
import tomlkit
from cattrs.preconf.tomlkit import make_converter
from packaging.version import InvalidVersion, Version
from tomlkit.items import Comment, Table, Whitespace

from .__about__ import __title__
from .addons.startup_script import StartupScript
from .config import Config, ConfigValWithMetadata, platform_dirs, unstructure_config
from .game_account_config import GameAccountConfig, GameAccountsConfig
from .game_config import GameConfig, GameConfigID, GameType
from .program_config import GamesSortingMode, ProgramConfig
from .resources import OneLauncherLocale, available_locales

PROGRAM_CONFIG_DIR_DEFAULT: Path = platform_dirs.user_config_path
PROGRAM_CONFIG_DEFAULT_NAME = f"{__title__.lower()}.toml"
GAMES_DIR_DEFAULT: Path = platform_dirs.user_data_path / "games"


def _structure_onelauncher_locale(
    lang_tag: str, conversion_type: type[OneLauncherLocale]
) -> OneLauncherLocale:
    return available_locales[lang_tag]


def _unstructure_startup_script(startup_scirpt: StartupScript) -> str:
    return str(startup_scirpt.relative_path)


def _structure_startup_script(
    relative_path: str, conversion_type: type[StartupScript]
) -> StartupScript:
    return StartupScript(relative_path=Path(relative_path))


def _unstructure_onelauncher_locale(locale: OneLauncherLocale) -> str:
    return locale.lang_tag


@cache
def get_converter() -> cattrs.Converter:
    converter = make_converter()

    converter.register_structure_hook(OneLauncherLocale, _structure_onelauncher_locale)

    converter.register_unstructure_hook(StartupScript, _unstructure_startup_script)
    converter.register_structure_hook(StartupScript, _structure_startup_script)

    converter.register_unstructure_hook(
        OneLauncherLocale, _unstructure_onelauncher_locale
    )
    converter.register_unstructure_hook_func(
        check_func=attrs.has, func=partial(unstructure_config, converter)
    )

    return converter


def convert_to_toml(
    data_dict: dict[str, Any | ConfigValWithMetadata],
    container: tomlkit.TOMLDocument | Table,
) -> None:
    """
    Convert unstructured config data to toml. None values are commented out.
    Config values can also have help text that is put in a comment above them.
    """
    tables: list[tuple[str, Table]] = []

    for key, unprocessed_val in data_dict.items():
        if isinstance(unprocessed_val, ConfigValWithMetadata):
            metadata = unprocessed_val.metadata
            val = unprocessed_val.value
            if metadata.help and not isinstance(val, dict):
                container.add(tomlkit.comment(metadata.help))
        else:
            val = unprocessed_val

        if isinstance(val, dict):
            if not val:
                continue
            table = tomlkit.table()
            convert_to_toml(val, table)
            tables.append((key, table))
        elif (
            isinstance(val, list)
            and len(val)
            and all(isinstance(item, dict) for item in val)
        ):
            table_array = tomlkit.aot()
            for item in val:
                table = tomlkit.table()
                convert_to_toml(item, table)
                table_array.append(table)
            container.add(key, table_array)
        elif isinstance(val, list):
            array = tomlkit.array()
            for item in val:
                array.append(item)
            container.add(key, array)
        elif val is None:
            container.add(tomlkit.comment(f"{key} = "))
        elif isinstance(val, str):
            container.add(key, tomlkit.string(val))
        else:
            container.add(key, tomlkit.item(val))

    # Non-inline tables should be after other items. tomlkit will do this
    # on its own, but mess up where the comments go.
    for key, table in tables:
        container.add(key, table)


def _tables_to_array_of_tables(
    unstructured_tables: dict[str, dict[str, Any] | Any],
    array_name: str,
    table_name_key_name: str,
) -> dict[str, list[dict[str, Any]]]:
    """
    Convert unstructured TOML tables to an array of tables with the table name
    included within the table as as the value of `table_name_key_name`.

    Args:
        unstructured_tables (dict[str, dict[str, Any]]): The unstructured
            tables. The dict top-level dictionary keys are the table names.
        array_name: (str): The name of the array of tables.
        table_name_key_name (str): The key to add to each table that will have
            the value of the table name.
    """
    array_of_tables: list[dict[str, Any]] = []
    final_dict: dict[str, Any] = {}
    for table_name, table in unstructured_tables.items():
        # Handle normal key-value pares
        if not isinstance(table, dict):
            final_dict[table_name] = table
            continue
        table[table_name_key_name] = table_name
        array_of_tables.append(table)
    final_dict[array_name] = array_of_tables
    return final_dict


def _array_of_tables_to_tables(
    array_of_tables: dict[str, list[dict[str, Any]]],
    array_name: str,
    table_name_key_name: str,
) -> dict[str, dict[str, Any]]:
    """
    Convert an unstructured TOML array of tables to individual top-level
        tables.

    Args:
        array_of_tables (dict[str, list[dict[str, Any]]]): The unstructured
            array of tables.
        array_name: (str): The name of the array of tables.
        table_name_key_name (str): The key from each table that will be removed
            and have its value used as the table name.
    """
    final_dict: dict[str, dict[str, Any]] = {}
    for table in array_of_tables[array_name]:
        table_name = table.pop(table_name_key_name)
        final_dict[
            table_name.value
            if isinstance(table_name, ConfigValWithMetadata)
            else table_name
        ] = table
    return final_dict


def get_toml_doc_config_version(document: tomlkit.TOMLDocument) -> Version | None:
    for _key, val in document.body:
        if isinstance(val, Whitespace):
            continue
        if not isinstance(val, Comment):
            return None

        if val.as_string().startswith("#:version "):
            try:
                return Version(val.as_string().split("#:version ")[1].strip())
            except InvalidVersion:
                continue
    return None


@attrs.frozen(kw_only=True)
class ConfigFileError(Exception):
    msg: str = "Config file error"
    config_class: type[Config]
    config_file_path: Path


@attrs.frozen(kw_only=True)
class ConfigFileParseError(ConfigFileError):
    """Error parsing config file"""

    msg: str = "Error parsing config file"


@attrs.frozen(kw_only=True)
class WrongConfigVersionError(ConfigFileError):
    msg: str = "Config file has wrong config version"
    config_file_version: Version


ConfigTypeVar = TypeVar("ConfigTypeVar", bound=Config)


def read_config_file(
    *,
    config_class: type[ConfigTypeVar],
    config_file_path: Path,
    preconverter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> ConfigTypeVar:
    """
    Read and parse config file into config_class object.

    Args:
        config_class (Config): The config class to convert to
        config_file_path (Path): Path to the config file.
        preconverter (Callable[[dict[str, Any]], dict[str, Any]] | None):
            Optional function used to change the unstructured config before
            converting it to `config_class`

    Raises:
        FileNotFoundError: Config file not found
        ConfigFileParseError: Error parsing config file
        WrongConfigVersionError: Config file has wrong config version
    """
    try:
        unstructured_config: tomlkit.TOMLDocument = tomlkit.parse(
            config_file_path.read_text(encoding="UTF-8")
        )
    except tomlkit.exceptions.ParseError as e:
        raise ConfigFileParseError(
            msg="Error parsing config TOML",
            config_class=config_class,
            config_file_path=config_file_path,
        ) from e

    config_file_version = get_toml_doc_config_version(unstructured_config)
    if config_file_version is None:
        raise ConfigFileParseError(
            msg="Config has no version specified.",
            config_class=config_class,
            config_file_path=config_file_path,
        )
    elif config_file_version != config_class.get_config_version():
        raise WrongConfigVersionError(
            msg=f"Config file's version is too "
            f"{'low' if config_file_version < config_class.get_config_version() else 'high'}.",
            config_class=config_class,
            config_file_path=config_file_path,
            config_file_version=config_file_version,
        )

    preconverted_config = (
        preconverter(unstructured_config) if preconverter else unstructured_config
    )

    try:
        return get_converter().structure(preconverted_config, config_class)
    except cattrs.ClassValidationError as e:
        raise ConfigFileParseError(
            msg="Error structuring config",
            config_class=config_class,
            config_file_path=config_file_path,
        ) from e


def update_config_file(
    config: Config,
    config_file_path: Path,
    postconverter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> None:
    """
    Replace contents of config file with `config`.
    """
    unstructured = get_converter().unstructure(config)
    postconverted_unstructured = (
        postconverter(unstructured) if postconverter else unstructured
    )
    doc = tomlkit.document()
    if config.get_config_file_description().strip():
        doc.add(tomlkit.comment(config.get_config_file_description()))

    # Make sure there's always a single newline between the version directive
    # comment and config contents
    if postconverted_unstructured and isinstance(
        next(iter(postconverted_unstructured.values())), dict
    ):
        trail = "\n"
    else:
        trail = "\n\n"
    doc.add(
        tomlkit.items.Comment(
            tomlkit.items.Trivia(
                comment=f"#:version {config.get_config_version()}", trail=trail
            )
        )
    )

    convert_to_toml(postconverted_unstructured, doc)
    config_file_path.write_text(doc.as_string())


ConfigManagerConfigClass: TypeAlias = ProgramConfig | GameConfig | GameAccountsConfig


class ConfigManagerNotSetupError(Exception):
    """Config manager hasn't been setup."""


@attrs.frozen(kw_only=True)
class NoValidGamesError(Exception):
    msg: str = "There are no valid games registered."


@attrs.define(kw_only=True)
class ConfigManager:
    """
    Before use, configs must be verified with `verify_configs` method.
    """

    get_merged_program_config: Callable[[ProgramConfig], ProgramConfig] = (
        lambda config: config
    )
    get_merged_game_config: Callable[[GameConfig], GameConfig] = lambda config: config
    get_merged_game_accounts_config: Callable[
        [GameAccountsConfig], GameAccountsConfig
    ] = lambda config: config
    program_config_dir: Final[Path] = PROGRAM_CONFIG_DIR_DEFAULT
    games_dir: Final[Path] = GAMES_DIR_DEFAULT

    GAME_CONFIG_FILE_NAME: Final[str] = attrs.field(default="config.toml", init=False)
    configs_are_verified: bool = attrs.field(default=False, init=False)
    verified_game_config_ids: list[GameConfigID] = attrs.field(default=[], init=False)
    _cached_program_config: ProgramConfig | None = attrs.field(default=None, init=False)
    _cached_game_configs: dict[GameConfigID, GameConfig] = attrs.field(
        default={}, init=False
    )
    _cached_game_accounts_configs: dict[GameConfigID, GameAccountsConfig] = attrs.field(
        default={}, init=False
    )

    def __attrs_post_init__(self) -> None:
        self.program_config_dir.mkdir(parents=True, exist_ok=True)
        self.games_dir.mkdir(parents=True, exist_ok=True)

    def verify_configs(self) -> None:
        """
        Verify that all config files are present and can be parsed.

        Raises:
            ConfigFileParseError: Error parsing a config file
            WrongConfigVersionError: Config file has wrong config version
        """
        self.verified_game_config_ids.clear()

        # ConfigFileParseError and WrongConfigVersionError are handled by caller
        self._read_program_config_file()

        # Verify game configs
        for game_id in self._get_game_config_ids():
            # FileNotFoundError is handled by using known to exist game IDs
            # ConfigFileParseError and WrongConfigVersionError are handled by caller
            self._read_game_config_file(game_id)
            try:
                # ConfigFileParseError and WrongConfigVersionError are handled by caller
                self._read_game_accounts_config_file_full(game_id)
            except FileNotFoundError:
                self.update_game_accounts_config_file(game_id=game_id, accounts=())

            self.verified_game_config_ids.append(game_id)
        self.configs_are_verified = True

    @property
    def program_config_path(self) -> Path:
        return self.program_config_dir / PROGRAM_CONFIG_DEFAULT_NAME

    def get_game_config_dir(self, game_id: GameConfigID) -> Path:
        return self.games_dir / str(game_id)

    def get_game_config_path(self, game_id: GameConfigID) -> Path:
        return self.get_game_config_dir(game_id) / self.GAME_CONFIG_FILE_NAME

    def get_game_id_from_config_path(self, config_path: Path) -> GameConfigID:
        return GameConfigID(config_path.parent.name)

    def get_game_accounts_config_path(self, game_id: GameConfigID) -> Path:
        return self.get_game_config_dir(game_id) / "accounts.toml"

    def get_config_backup_path(self, config_path: Path) -> Path:
        """Get config backup file path"""
        return config_path.with_suffix("".join([*config_path.suffixes, ".backup"]))

    def get_program_config(self) -> ProgramConfig:
        """Get merged program config object."""
        return self.get_merged_program_config(self.read_program_config_file())

    def read_program_config_file(self) -> ProgramConfig:
        """Read and parse program config file into `ProgramConfig` object."""
        if self.configs_are_verified and self._cached_program_config:
            return self._cached_program_config
        else:
            raise ConfigManagerNotSetupError("")

    def _read_program_config_file(self) -> ProgramConfig:
        """
        Read and parse program config file into `ProgramConfig` object.

        Raises:
            ConfigFileParseError: Error parsing config file
            WrongConfigVersionError: Config file has wrong config version
        """
        try:
            config = read_config_file(
                config_class=ProgramConfig, config_file_path=self.program_config_path
            )
        except FileNotFoundError:
            # There should always be a program config.
            # Just returning an object, allows there to be no config written to disk
            # until a change is made. This is mainly useful for knowing when to run
            # the setup wizard
            config = ProgramConfig()
        self._cached_program_config = config
        return config

    def update_program_config_file(self, config: ProgramConfig) -> None:
        """
        Replace contents of program config file with `config`.
        """
        update_config_file(config=config, config_file_path=self.program_config_path)
        self._cached_program_config = config

    def delete_program_config(self) -> None:
        """Delete program config"""
        self.program_config_path.unlink(missing_ok=True)
        # Update the cache.
        # Parse error and config version errors are handled, because there is no file
        # to parse.
        self._read_program_config_file()

    def get_game_config_ids(self) -> tuple[GameConfigID, ...]:
        if self.configs_are_verified:
            return tuple(self.verified_game_config_ids)
        else:
            raise ConfigManagerNotSetupError("")

    def _get_game_config_ids(self) -> tuple[GameConfigID, ...]:
        return tuple(
            self.get_game_id_from_config_path(config_path=config_file)
            for config_file in self.games_dir.glob(f"*/{self.GAME_CONFIG_FILE_NAME}")
        )

    def get_games_by_game_type(self, game_type: GameType) -> tuple[GameConfigID, ...]:
        return tuple(
            game_id
            for game_id in self.get_game_config_ids()
            if self.get_game_config(game_id).game_type == game_type
        )

    def get_games_sorted_by_priority(
        self, game_type: GameType | None = None
    ) -> tuple[GameConfigID, ...]:
        game_ids = (
            self.get_games_by_game_type(game_type)
            if game_type
            else self.get_game_config_ids()
        )

        def sorter(game_id: GameConfigID) -> str:
            game_config = self.get_game_config(game_id)
            return (
                "Z"
                if game_config.sorting_priority == -1
                else str(game_config.sorting_priority)
            )

        # Sort games by sorting_priority. Games with sorting_priority of -1 are
        # put at the end
        return tuple(sorted(game_ids, key=sorter))

    def get_games_sorted_by_last_played(
        self, game_type: GameType | None = None
    ) -> tuple[GameConfigID, ...]:
        game_ids = (
            self.get_games_by_game_type(game_type)
            if game_type
            else self.get_game_config_ids()
        )

        def sorter(game_id: GameConfigID) -> datetime.datetime:
            game_config = self.get_game_config(game_id)
            return (
                datetime.datetime(
                    datetime.MINYEAR, 1, 1, 0, 0, 0, 0, tzinfo=datetime.UTC
                )
                if game_config.last_played is None
                else game_config.last_played
            )

        # Get list of played games sorted by when they were last played
        return tuple(
            sorted(
                game_ids,
                key=sorter,
                reverse=True,
            )
        )

    def get_games_sorted(
        self,
        sorting_mode: GamesSortingMode,
        game_type: GameType | None = None,
    ) -> tuple[GameConfigID, ...]:
        match sorting_mode:
            case GamesSortingMode.PRIORITY:
                return self.get_games_sorted_by_priority(game_type)
            case GamesSortingMode.LAST_PLAYED:
                return self.get_games_sorted_by_last_played(game_type)
            case GamesSortingMode.ALPHABETICAL:
                return self.get_games_sorted_alphabetically(game_type)

    def get_games_sorted_alphabetically(
        self, game_type: GameType | None
    ) -> tuple[GameConfigID, ...]:
        game_ids = (
            self.get_games_by_game_type(game_type)
            if game_type
            else self.get_game_config_ids()
        )
        return tuple(
            sorted(game_ids, key=lambda game_id: self.get_game_config(game_id).name)
        )

    def get_initial_game(self) -> GameConfigID:
        """
        Get which game has the highest priority/should be presented first.

        Raises:
            NoValidGamesError: No valid games are registered.
        """
        if not (games_by_last_played := self.get_games_sorted_by_last_played()):
            raise NoValidGamesError()
        return (
            games_by_last_played[0]
            if self.get_game_config(games_by_last_played[0]).last_played is not None
            else self.get_games_sorted(self.get_program_config().games_sorting_mode)[0]
        )

    def get_game_config(self, game_id: GameConfigID) -> GameConfig:
        """
        Get merged game config object.
        """
        return self.get_merged_game_config(self.read_game_config_file(game_id))

    def read_game_config_file(self, game_id: GameConfigID) -> GameConfig:
        """Read and parse game config file into `GameConfig` object."""
        if not self.configs_are_verified:
            raise ConfigManagerNotSetupError("")
        if game_id not in self.verified_game_config_ids:
            raise ValueError(f"Game config ID: {game_id} has not been verified")

        return self._cached_game_configs[game_id]

    def _read_game_config_file(self, game_id: GameConfigID) -> GameConfig:
        """
        Read and parse game config file into `GameConfig` object.

        Raises:
            FileNotFoundError: Config file not found
            ConfigFileParseError: Error parsing config file
            WrongConfigVersionError: Config file has wrong config version
        """
        config = read_config_file(
            config_class=GameConfig,
            config_file_path=self.get_game_config_path(game_id),
        )
        self._cached_game_configs[game_id] = config
        return config

    def update_game_config_file(
        self, game_id: GameConfigID, config: GameConfig
    ) -> None:
        """
        Replace contents of game config file with `config`.
        """
        game_config_path = self.get_game_config_path(game_id)
        game_config_path.parent.mkdir(exist_ok=True)
        update_config_file(config=config, config_file_path=game_config_path)
        if game_id not in self.verified_game_config_ids:
            # Veriefed game config IDs are expected to have an accounts config file
            self.update_game_accounts_config_file(game_id=game_id, accounts=())
            self.verified_game_config_ids.append(game_id)
        self._cached_game_configs[game_id] = config

    def delete_game_config(self, game_id: GameConfigID) -> None:
        """Delete game config including all files and saved accounts"""
        with suppress(FileNotFoundError):
            account_configs = self.read_game_accounts_config_file(game_id)
            for account_config in account_configs:
                self.delete_game_account_keyring_info(
                    game_id=game_id, game_account=account_config
                )
        rmtree(self.get_game_config_dir(game_id=game_id))
        if game_id in self.verified_game_config_ids:
            self.verified_game_config_ids.remove(game_id)
            del self._cached_game_configs[game_id]
            del self._cached_game_accounts_configs[game_id]

    def get_game_accounts(self, game_id: GameConfigID) -> tuple[GameAccountConfig, ...]:
        if not self.configs_are_verified:
            raise ConfigManagerNotSetupError("")
        if game_id not in self.verified_game_config_ids:
            raise ValueError(f"Game config ID: {game_id} has not been verified")

        return self.get_merged_game_accounts_config(
            self._cached_game_accounts_configs[game_id]
        ).accounts

    def _read_game_accounts_config_file_full(
        self, game_id: GameConfigID
    ) -> GameAccountsConfig:
        """
        Read and parse game accounts config file into `GameAccountsConfig`
        object.

        Raises:
            FileNotFoundError: Config file not found
            ConfigFileParseError: Error parsing config file
            WrongConfigVersionError: Config file has wrong config version
        """
        config = read_config_file(
            config_class=GameAccountsConfig,
            config_file_path=self.get_game_accounts_config_path(game_id),
            preconverter=partial(
                _tables_to_array_of_tables,
                array_name="accounts",
                table_name_key_name="username",
            ),
        )
        self._cached_game_accounts_configs[game_id] = config
        return config

    def read_game_accounts_config_file(
        self, game_id: GameConfigID
    ) -> tuple[GameAccountConfig, ...]:
        """
        Read and parse game accounts config file into tuple of
        `GameAccountConfig` objects.
        """
        if not self.configs_are_verified:
            raise ConfigManagerNotSetupError("")
        if game_id not in self.verified_game_config_ids:
            raise ValueError(f"Game config ID: {game_id} has not been verified")

        return self._cached_game_accounts_configs[game_id].accounts

    def update_game_accounts_config_file(
        self, game_id: GameConfigID, accounts: tuple[GameAccountConfig, ...]
    ) -> None:
        """
        Replace contents of game accounts config file with `accounts`.
        """
        # Delete keyring info for any removed accounts
        with suppress(FileNotFoundError, ConfigFileError):
            existing_accounts = self._read_game_accounts_config_file_full(
                game_id=game_id
            ).accounts
            updated_accounts_usernames = [account.username for account in accounts]
            for existing_account in existing_accounts:
                if existing_account.username not in updated_accounts_usernames:
                    self.delete_game_account_keyring_info(
                        game_id=game_id, game_account=existing_account
                    )
        config = GameAccountsConfig(accounts)
        update_config_file(
            config=config,
            config_file_path=self.get_game_accounts_config_path(game_id),
            postconverter=partial(
                _array_of_tables_to_tables,
                array_name="accounts",
                table_name_key_name="username",
            ),
        )
        self._cached_game_accounts_configs[game_id] = config

    def _get_account_keyring_username(
        self, game_id: GameConfigID, game_account: GameAccountConfig
    ) -> str:
        return f"{game_id}{game_account.username}"

    def get_game_account_password(
        self, game_id: GameConfigID, game_account: GameAccountConfig
    ) -> str | None:
        """
        Get account password that is saved in keyring.
        Will return `None` if no saved passwords are found
        """
        return keyring.get_password(
            service_name=__title__,
            username=self._get_account_keyring_username(
                game_id=game_id, game_account=game_account
            ),
        )

    def save_game_account_password(
        self, game_id: GameConfigID, game_account: GameAccountConfig, password: str
    ) -> None:
        """Save account password with keyring"""
        keyring.set_password(
            service_name=__title__,
            username=self._get_account_keyring_username(
                game_id=game_id, game_account=game_account
            ),
            password=password,
        )

    def delete_game_account_password(
        self, game_id: GameConfigID, game_account: GameAccountConfig
    ) -> None:
        """Delete account password saved with keyring"""
        with suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(
                service_name=__title__,
                username=self._get_account_keyring_username(
                    game_id=game_id, game_account=game_account
                ),
            )

    def _get_account_last_used_subscription_keyring_username(
        self, game_id: GameConfigID, game_account: GameAccountConfig
    ) -> str:
        base_keyring_username = self._get_account_keyring_username(
            game_id=game_id, game_account=game_account
        )
        return f"{base_keyring_username}LastUsedSubscription"

    def get_game_account_last_used_subscription_name(
        self, game_id: GameConfigID, game_account: GameAccountConfig
    ) -> str | None:
        """
        Get name of the subscription that was last played with from keyring.
        See `login_account.py`
        """
        return keyring.get_password(
            service_name=__title__,
            username=self._get_account_last_used_subscription_keyring_username(
                game_id=game_id, game_account=game_account
            ),
        )

    def save_game_account_last_used_subscription_name(
        self,
        game_id: GameConfigID,
        game_account: GameAccountConfig,
        subscription_name: str,
    ) -> None:
        """Save last used subscription name with keyring"""
        keyring.set_password(
            service_name=__title__,
            username=self._get_account_last_used_subscription_keyring_username(
                game_id=game_id, game_account=game_account
            ),
            password=subscription_name,
        )

    def delete_game_account_last_used_subscription_name(
        self,
        game_id: GameConfigID,
        game_account: GameAccountConfig,
    ) -> None:
        """Delete last used subscription name saved with keyring"""
        with suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(
                service_name=__title__,
                username=self._get_account_last_used_subscription_keyring_username(
                    game_id=game_id, game_account=game_account
                ),
            )

    def delete_game_account_keyring_info(
        self, game_id: GameConfigID, game_account: GameAccountConfig
    ) -> None:
        """
        Delete all information for account saved with keyring. ex. password
        """
        self.delete_game_account_password(game_id=game_id, game_account=game_account)
        self.delete_game_account_last_used_subscription_name(
            game_id=game_id, game_account=game_account
        )

    def get_ui_locale(self, game_id: GameConfigID) -> OneLauncherLocale:
        program_config = self.get_program_config()
        game_config = self.get_game_config(game_id)
        return (
            program_config.default_locale
            if program_config.always_use_default_locale_for_ui or not game_config.locale
            else game_config.locale
        )
