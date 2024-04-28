from collections import OrderedDict
from collections.abc import Callable
from contextlib import suppress
from datetime import datetime
from functools import cache, partial, update_wrapper
from pathlib import Path
from shutil import rmtree
from typing import Any, Final, Generic, ParamSpec, TypeVar
from uuid import UUID

import attrs
import cattrs
import keyring
import tomlkit
from cattrs.preconf.tomlkit import make_converter
from tomlkit.items import Table

from .__about__ import __title__
from .addons.startup_script import StartupScript
from .config import Config, ConfigValWithMetadata, platform_dirs, unstructure_config
from .game_account_config import GameAccountConfig, GameAccountsConfig
from .game_config import GameConfig, GameType
from .program_config import GamesSortingMode, ProgramConfig
from .resources import OneLauncherLocale, available_locales

PROGRAM_CONFIG_DEFAULT_PATH: Path = (
    platform_dirs.user_config_path / f"{__title__.lower()}.toml"
)
GAMES_DIR_DEFAULT_PATH: Path = platform_dirs.user_data_path / "games"


def _structure_onelauncher_locale(
    lang_tag: str, conversion_type: type[OneLauncherLocale]
) -> OneLauncherLocale:
    return available_locales[lang_tag]


def _unstructure_startup_script(startup_scirpt: StartupScript) -> str:
    return str(startup_scirpt.relative_path)


def _structure_startup_script(
    relative_path: Path, conversion_type: type[StartupScript]
) -> StartupScript:
    return StartupScript(relative_path=Path(relative_path))


def _unstructure_uuid(uuid: UUID) -> str:
    return str(uuid)


def _unstructure_onelauncher_locale(locale: OneLauncherLocale) -> str:
    return locale.lang_tag


@cache
def get_converter() -> cattrs.Converter:
    converter = make_converter()

    converter.register_structure_hook(OneLauncherLocale, _structure_onelauncher_locale)

    converter.register_unstructure_hook(StartupScript, _unstructure_startup_script)
    converter.register_structure_hook(StartupScript, _structure_startup_script)

    converter.register_unstructure_hook(UUID, _unstructure_uuid)
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
    for key, unprocessed_val in data_dict.items():
        if isinstance(unprocessed_val, ConfigValWithMetadata):
            metadata = unprocessed_val.metadata
            val = unprocessed_val.value
            if metadata.help and not isinstance(val, dict):
                container.add(tomlkit.comment(metadata.help))
        else:
            val = unprocessed_val
        if isinstance(val, dict):
            table = tomlkit.table()
            convert_to_toml(val, table)
            container.add(key, table)
        elif isinstance(val, list) and len(val) and all(isinstance(item, dict) for item in val):
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


def _tables_to_array_of_tables(
    unstructured_tables: dict[str, dict[str, Any]],
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


_R = TypeVar("_R")
_P = ParamSpec("_P")


class RemovableKeysLRUCache(Generic[_P, _R]):
    """
    LRU Cache implementation with methods for removing or replacing specific
    cached calls.

    This is an edited version of Tim Child's code from
    [stackoverflow](https://stackoverflow.com/a/64816003).
    """

    def __init__(self, func: Callable[_P, _R], maxsize: int = 128):
        update_wrapper(self, func)
        self.cache: OrderedDict[int, _R] = OrderedDict()
        self.func = func
        self.maxsize = maxsize

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        cache = self.cache
        key = self._generate_hash_key(*args, **kwargs)
        if key in cache:
            cache.move_to_end(key)
            return cache[key]
        result = self.func(*args, **kwargs)
        cache[key] = result
        if len(cache) > self.maxsize:
            cache.popitem(last=False)
        return result

    def __repr__(self) -> str:
        return self.func.__repr__()

    def clear_cache(self) -> None:
        self.cache.clear()

    def cache_remove(self, *args: _P.args, **kwargs: _P.kwargs) -> None:
        """Remove an item from the cache by passing the same args and kwargs"""
        key = self._generate_hash_key(*args, **kwargs)
        if key in self.cache:
            self.cache.pop(key)

    def cache_replace(self, value: _R, *args: _P.args, **kwargs: _P.kwargs) -> None:
        key = self._generate_hash_key(*args, **kwargs)
        self.cache[key] = value

    @staticmethod
    def _generate_hash_key(*args: _P.args, **kwargs: _P.kwargs) -> int:
        return hash((args, frozenset(sorted(kwargs.items()))))


class ConfigFileParseError(Exception):
    """Error parsing config file"""


ConfigTypeVar = TypeVar("ConfigTypeVar", bound=Config)


@RemovableKeysLRUCache
def read_config_file(
    *,  # Paremeters are keyword only for cache entry clearing
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
    """
    try:
        unstructured_config: tomlkit.TOMLDocument = tomlkit.parse(
            config_file_path.read_text()
        )
    except tomlkit.exceptions.ParseError as e:
        raise ConfigFileParseError("Error parsing config TOML") from e

    preconverted_config = (
        preconverter(unstructured_config) if preconverter else unstructured_config
    )

    try:
        return get_converter().structure(preconverted_config, config_class)
    except cattrs.ClassValidationError as e:
        raise ConfigFileParseError("Error structuring config") from e


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
    config_file_path.touch(exist_ok=True)
    config_file_path.write_text(doc.as_string())
    read_config_file.cache_replace(
        config, config_class=type(config), config_file_path=config_file_path
    )


class ConfigManagerNotSetupError(Exception):
    """Config manager hasn't been setup."""


@attrs.define
class ConfigManager:
    """
    Before use, configs must be verified with `verify_configs` method.
    """

    get_merged_program_config: Callable[[ProgramConfig], ProgramConfig]
    get_merged_game_config: Callable[[GameConfig], GameConfig]
    get_merged_game_accounts_config: Callable[[GameAccountsConfig], GameAccountsConfig]
    program_config_path: Path = PROGRAM_CONFIG_DEFAULT_PATH
    games_dir_path: Path = GAMES_DIR_DEFAULT_PATH

    GAME_CONFIG_FILE_NAME: Final[str] = attrs.field(default="config.toml", init=False)
    configs_are_verified: bool = attrs.field(default=False, init=False)
    verified_game_uuids: list[UUID] = attrs.field(default=[], init=False)

    def __attrs_post_init__(self) -> None:
        self.program_config_path.parent.mkdir(parents=True, exist_ok=True)
        self.games_dir_path.mkdir(parents=True, exist_ok=True)

    def verify_configs(self) -> None:
        """
        Verify that all config files are present and can be parsed.

        Raises:
            ConfigFileParseError: Error parsing a config file
        """
        self.verified_game_uuids.clear()

        # ConfigFileParseError is handled by caller
        self._read_program_config_file()

        # Verify game configs
        for game_uuid in self._get_game_uuids():
            # FileNotFoundError is handled by using known to exist UUIDs
            # ConfigFileParseError is handled by caller
            self._read_game_config_file(game_uuid)
            try:
                # ConfigFileParseError is handled by caller
                self._read_game_accounts_config_file_full(game_uuid)
            except FileNotFoundError:
                self.update_game_accounts_config_file(game_uuid=game_uuid, accounts=())

            self.verified_game_uuids.append(game_uuid)
        self.configs_are_verified = True

    def get_game_config_dir(self, game_uuid: UUID) -> Path:
        return self.games_dir_path / str(game_uuid)

    def get_game_config_path(self, game_uuid: UUID) -> Path:
        return self.get_game_config_dir(game_uuid) / self.GAME_CONFIG_FILE_NAME

    def get_game_accounts_config_path(self, game_uuid: UUID) -> Path:
        return self.get_game_config_dir(game_uuid) / "accounts.toml"

    def get_program_config(self) -> ProgramConfig:
        """Get merged program config object."""
        return self.get_merged_program_config(self.read_program_config_file())

    def read_program_config_file(self) -> ProgramConfig:
        """Read and parse program config file into `ProgramConfig` object."""
        if self.configs_are_verified:
            return self._read_program_config_file()
        else:
            raise ConfigManagerNotSetupError("")

    def _read_program_config_file(self) -> ProgramConfig:
        """
        Read and parse program config file into `ProgramConfig` object.

        Raises:
            ConfigFileParseError: Error parsing config file
        """
        try:
            return read_config_file(
                config_class=ProgramConfig, config_file_path=self.program_config_path
            )
        except FileNotFoundError:
            # There should always be a program config.
            # Just returning an object, allows there to be no config written to disk
            # until a change is made. This is mainly useful for knowing when to run
            # the setup wizard
            return ProgramConfig()

    def update_program_config_file(self, config: ProgramConfig) -> None:
        """
        Replace contents of program config file with `config`.
        """
        update_config_file(config=config, config_file_path=self.program_config_path)

    def delete_program_config(self) -> None:
        """Delete program config"""
        self.program_config_path.unlink(missing_ok=True)
        read_config_file.clear_cache()

    def get_game_uuids(self) -> tuple[UUID, ...]:
        if self.configs_are_verified:
            return tuple(self.verified_game_uuids)
        else:
            raise ConfigManagerNotSetupError("")

    def _get_game_uuids(self) -> tuple[UUID, ...]:
        return tuple(
            UUID(config_file.parent.name)
            for config_file in self.games_dir_path.glob(
                f"*/{self.GAME_CONFIG_FILE_NAME}"
            )
        )

    def get_games_by_game_type(self, game_type: GameType) -> tuple[UUID, ...]:
        return tuple(
            game_uuid
            for game_uuid in self.get_game_uuids()
            if self.get_game_config(game_uuid).game_type == game_type
        )

    def get_games_sorted_by_priority(
        self, game_type: GameType | None = None
    ) -> tuple[UUID, ...]:
        game_uuids = (
            self.get_games_by_game_type(game_type)
            if game_type
            else self.get_game_uuids()
        )

        def sorter(game_uuid: UUID) -> str:
            game_config = self.get_game_config(game_uuid)
            return (
                "Z"
                if game_config.sorting_priority == -1
                else str(game_config.sorting_priority)
            )

        # Sort games by sorting_priority. Games with sorting_priority of -1 are
        # put at the end
        return tuple(sorted(game_uuids, key=sorter))

    def get_games_sorted_by_last_played(
        self, game_type: GameType | None = None
    ) -> tuple[UUID, ...]:
        game_uuids = (
            self.get_games_by_game_type(game_type)
            if game_type
            else self.get_game_uuids()
        )

        def sorter(game_uuid: UUID) -> datetime:
            game_config = self.get_game_config(game_uuid)
            return (
                datetime.max
                if game_config.last_played is None
                else game_config.last_played
            )

        # Get list of played games sorted by when they were last played
        return tuple(
            sorted(
                game_uuids,
                key=sorter,
                reverse=True,
            )
        )

    def get_games_sorted(
        self,
        sorting_mode: GamesSortingMode,
        game_type: GameType | None = None,
    ) -> tuple[UUID, ...]:
        match sorting_mode:
            case GamesSortingMode.PRIORITY:
                return self.get_games_sorted_by_priority(game_type)
            case GamesSortingMode.LAST_USED:
                return self.get_games_sorted_by_last_played(game_type)
            case GamesSortingMode.ALPHABETICAL:
                return self.get_games_sorted_alphabetically(game_type)

    def get_games_sorted_alphabetically(
        self, game_type: GameType | None
    ) -> tuple[UUID, ...]:
        game_uuids = (
            self.get_games_by_game_type(game_type)
            if game_type
            else self.get_game_uuids()
        )
        return tuple(
            sorted(
                game_uuids, key=lambda game_uuid: self.get_game_config(game_uuid).name
            )
        )

    def get_game_config(self, game_uuid: UUID) -> GameConfig:
        """
        Get merged game config object.
        """
        return self.get_merged_game_config(self.read_game_config_file(game_uuid))

    def read_game_config_file(self, game_uuid: UUID) -> GameConfig:
        """Read and parse game config file into `GameConfig` object."""
        if not self.configs_are_verified:
            raise ConfigManagerNotSetupError("")
        if game_uuid not in self.verified_game_uuids:
            raise ValueError(f"Game UUID: {game_uuid} has not been verified.")

        return self._read_game_config_file(game_uuid)

    def _read_game_config_file(self, game_uuid: UUID) -> GameConfig:
        """
        Read and parse game config file into `GameConfig` object.

        Raises:
            FileNotFoundError: Config file not found
            ConfigFileParseError: Error parsing config file
        """
        return read_config_file(
            config_class=GameConfig,
            config_file_path=self.get_game_config_path(game_uuid),
        )

    def update_game_config_file(self, game_uuid: UUID, config: GameConfig) -> None:
        """
        Replace contents of game config file with `config`.
        """
        game_config_path = self.get_game_config_path(game_uuid)
        game_config_path.parent.mkdir(exist_ok=True)
        update_config_file(config=config, config_file_path=game_config_path)
        if game_uuid not in self.verified_game_uuids:
            self.verified_game_uuids.append(game_uuid)

    def delete_game_config(self, game_uuid: UUID) -> None:
        """Delete game config including all files and saved accounts"""
        with suppress(FileNotFoundError):
            account_configs = self.read_game_accounts_config_file(game_uuid)
            for account_config in account_configs:
                self.delete_game_account_keyring_info(
                    game_uuid=game_uuid, game_account=account_config
                )
        rmtree(self.get_game_config_dir(game_uuid=game_uuid))
        read_config_file.clear_cache()
        self.verified_game_uuids.remove(game_uuid)

    def get_game_accounts(self, game_uuid: UUID) -> tuple[GameAccountConfig, ...]:
        if not self.configs_are_verified:
            raise ConfigManagerNotSetupError("")
        if game_uuid not in self.verified_game_uuids:
            raise ValueError(f"Game UUID: {game_uuid} has not been verified.")

        return self.get_merged_game_accounts_config(
            self._read_game_accounts_config_file_full(game_uuid)
        ).accounts

    def _read_game_accounts_config_file_full(
        self, game_uuid: UUID
    ) -> GameAccountsConfig:
        """
        Read and parse game accounts config file into `GameAccountsConfig`
        object.

        Raises:
            FileNotFoundError: Config file not found
            ConfigFileParseError: Error parsing config file
        """
        return read_config_file(
            config_class=GameAccountsConfig,
            config_file_path=self.get_game_accounts_config_path(game_uuid),
            preconverter=partial(
                _tables_to_array_of_tables,
                array_name="accounts",
                table_name_key_name="username",
            ),
        )

    def _read_game_accounts_config_file(
        self, game_uuid: UUID
    ) -> tuple[GameAccountConfig, ...]:
        """
        Read and parse game accounts config file into tuple of
        `GameAccountConfig` objects.

        Raises:
            ConfigFileParseError: Error parsing config file
        """
        return self._read_game_accounts_config_file_full(game_uuid).accounts

    def read_game_accounts_config_file(
        self, game_uuid: UUID
    ) -> tuple[GameAccountConfig, ...]:
        """
        Read and parse game accounts config file into tuple of
        `GameAccountConfig` objects.
        """
        if not self.configs_are_verified:
            raise ConfigManagerNotSetupError("")
        if game_uuid not in self.verified_game_uuids:
            raise ValueError(f"Game UUID: {game_uuid} has not been verified.")

        return self._read_game_accounts_config_file(game_uuid)

    def update_game_accounts_config_file(
        self, game_uuid: UUID, accounts: tuple[GameAccountConfig, ...]
    ) -> None:
        """
        Replace contents of game accounts config file with `accounts`.
        """
        update_config_file(
            config=GameAccountsConfig(accounts),
            config_file_path=self.get_game_accounts_config_path(game_uuid),
            postconverter=partial(
                _array_of_tables_to_tables,
                array_name="accounts",
                table_name_key_name="username",
            ),
        )

    def _get_account_keyring_username(
        self, game_uuid: UUID, game_account: GameAccountConfig
    ) -> str:
        return f"{game_uuid}{game_account.username}"

    def get_game_account_password(
        self, game_uuid: UUID, game_account: GameAccountConfig
    ) -> str | None:
        """
        Get account password that is saved in keyring.
        Will return `None` if no saved passwords are found
        """
        return keyring.get_password(
            service_name=__title__,
            username=self._get_account_keyring_username(
                game_uuid=game_uuid, game_account=game_account
            ),
        )

    def save_game_account_password(
        self, game_uuid: UUID, game_account: GameAccountConfig, password: str
    ) -> None:
        """Save account password with keyring"""
        keyring.set_password(
            service_name=__title__,
            username=self._get_account_keyring_username(
                game_uuid=game_uuid, game_account=game_account
            ),
            password=password,
        )

    def delete_game_account_password(
        self, game_uuid: UUID, game_account: GameAccountConfig
    ) -> None:
        """Delete account password saved with keyring"""
        with suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(
                service_name=__title__,
                username=self._get_account_keyring_username(
                    game_uuid=game_uuid, game_account=game_account
                ),
            )

    def _get_account_last_used_subscription_keyring_username(
        self, game_uuid: UUID, game_account: GameAccountConfig
    ) -> str:
        base_keyring_username = self._get_account_keyring_username(
            game_uuid=game_uuid, game_account=game_account
        )
        return f"{base_keyring_username}LastUsedSubscription"

    def get_game_account_last_used_subscription_name(
        self, game_uuid: UUID, game_account: GameAccountConfig
    ) -> str | None:
        """
        Get name of the subscription that was last played with from keyring.
        See `login_account.py`
        """
        return keyring.get_password(
            service_name=__title__,
            username=self._get_account_last_used_subscription_keyring_username(
                game_uuid=game_uuid, game_account=game_account
            ),
        )

    def save_game_account_last_used_subscription_name(
        self, game_uuid: UUID, game_account: GameAccountConfig, subscription_name: str
    ) -> None:
        """Save last used subscription name with keyring"""
        keyring.set_password(
            service_name=__title__,
            username=self._get_account_last_used_subscription_keyring_username(
                game_uuid=game_uuid, game_account=game_account
            ),
            password=subscription_name,
        )

    def delete_game_account_last_used_subscription_name(
        self,
        game_uuid: UUID,
        game_account: GameAccountConfig,
    ) -> None:
        """Delete last used subscription name saved with keyring"""
        with suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(
                service_name=__title__,
                username=self._get_account_last_used_subscription_keyring_username(
                    game_uuid=game_uuid, game_account=game_account
                ),
            )

    def delete_game_account_keyring_info(
        self, game_uuid: UUID, game_account: GameAccountConfig
    ) -> None:
        """
        Delete all information for account saved with keyring. ex. password
        """
        self.delete_game_account_password(
            game_uuid=game_uuid, game_account=game_account
        )
        self.delete_game_account_last_used_subscription_name(
            game_uuid=game_uuid, game_account=game_account
        )

    def get_ui_locale(self, game_uuid: UUID) -> OneLauncherLocale:
        program_config = self.get_program_config()
        game_config = self.get_game_config(game_uuid)
        return (
            program_config.default_locale
            if program_config.always_use_default_locale_for_ui or not game_config.locale
            else game_config.locale
        )
