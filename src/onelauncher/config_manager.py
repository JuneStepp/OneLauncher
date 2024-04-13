from collections import OrderedDict
from collections.abc import Callable
from functools import cache, partial, update_wrapper
from pathlib import Path
from typing import Any, Final, Generic, ParamSpec, TypeVar
from uuid import UUID

import attrs
import cattrs
import tomlkit
from cattrs.preconf.tomlkit import make_converter
from tomlkit.items import Table

from .__about__ import __title__
from .config import Config, ConfigValWithMetadata, unstructure_config
from .config_old import platform_dirs
from .game_account_config import GameAccountConfig, GameAccountsConfig
from .game_config import GameConfig
from .program_config import ProgramConfig
from .resources import OneLauncherLocale, available_locales

PROGRAM_CONFIG_DEFAULT_PATH: Path = (
    platform_dirs.user_config_path / f"{__title__.lower()}1.toml"
)
GAMES_DIR_DEFAULT_PATH: Path = platform_dirs.user_data_path / "games"


def _structure_onelauncher_locale(
    lang_tag: str, type: type[OneLauncherLocale]
) -> OneLauncherLocale:
    return available_locales[lang_tag]


def _unstructure_uuid(uuid: UUID) -> str:
    return str(uuid)


def _unstructure_onelauncher_locale(locale: OneLauncherLocale) -> str:
    return locale.lang_tag


@cache
def get_converter() -> cattrs.Converter:
    converter = make_converter()

    converter.register_structure_hook(OneLauncherLocale, _structure_onelauncher_locale)

    converter.register_unstructure_hook(UUID, _unstructure_uuid)
    converter.register_unstructure_hook(
        OneLauncherLocale, _unstructure_onelauncher_locale
    )
    converter.register_unstructure_hook_func(
        check_func=attrs.has, func=partial(unstructure_config, converter)
    )

    return converter


def convert_to_toml(
    data_dict: dict[str, Any], container: tomlkit.TOMLDocument | Table
) -> None:
    """
    Convert unstructured config data to toml. None values are commented out.
    Config values can also have help text that is put in a comment above them.
    """
    for key, val in data_dict.items():
        if isinstance(val, ConfigValWithMetadata):
            metadata = val.metadata
            val = val.value
            if metadata.help and not isinstance(val, dict):
                container.add(tomlkit.comment(metadata.help))
        if isinstance(val, dict):
            table = tomlkit.table()
            convert_to_toml(val, table)
            container.add(key, table)
        elif isinstance(val, list) and all(isinstance(item, dict) for item in val):
            table_array = tomlkit.aot()
            for item in val:
                table = tomlkit.table()
                convert_to_toml(item, table)
                table_array.append(table)
            container.add(key, table_array)
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


_R_co = TypeVar("_R_co")
_P = ParamSpec("_P")


class RemovableKeysLRUCache(Generic[_P, _R_co]):
    """
    LRU Cache implementation with methods for removing or replacing specific
    cached calls.

    This is an edited version of Tim Child's code from
    [stackoverflow](https://stackoverflow.com/a/64816003).
    """

    def __init__(self, func: Callable[_P, _R_co], maxsize: int = 128):
        update_wrapper(self, func)
        self.cache: OrderedDict[int, _R_co] = OrderedDict()
        self.func = func
        self.maxsize = maxsize

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R_co:
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

    def cache_replace(self, value: _R_co, *args: _P.args, **kwargs: _P.kwargs) -> None:
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


# class MissingConfigSectionError(Exception):
#     """`Config` doesn't have the requested `ConfigSection`"""


# class MultipleConfigSectionsError(Exception):
#     """
#     `Config` has multiple sections matching the type of the requested
#     `ConfigSection`
#     """


# ConfigSectionTypeVar = TypeVar("ConfigSectionTypeVar", bound=ConfigSection)


# def _get_config_section_attr_name(
#         config_class: type[Config],
#         config_section_class: type[ConfigSectionTypeVar]) -> str:
#     """
#     Return the attribute name of the config section in the config class.

#     Raises:
#         MissingConfigSectionError: `Config` doesn't have the requested
#             `ConfigSection`
#         MultipleConfigSectionsError: `Config` has multiple sections matching
#             the type of the requested `ConfigSection`
#     """
#     matching_sections: list[attrs.Attribute] = [
#         field for field in attrs.fields(config_class)
#         if field.type == config_section_class]
#     if not matching_sections:
#         raise MissingConfigSectionError(
#             f"{config_class} doesn't have {config_section_class} config section"
#         )
#     elif len(matching_sections) > 1:
#         raise MultipleConfigSectionsError(
#             f"{config_class}  has multiple sections matching the type of "
#             f"{config_section_class} config section")
#     return matching_sections[0].name


# def read_config_file_section(
#         config_class: type[Config],
#         config_section_class: type[ConfigSectionTypeVar],
#         config_file_path: Path) -> ConfigSectionTypeVar:
#     """
#     Return a config section with values from a config file.
#     `get_config_section` should be used for general config access.

#     Raises:
#         MissingConfigSectionError: `Config` doesn't have the requested
#             `ConfigSection`
#         MultipleConfigSectionsError: `Config` has multiple sections matching
#             the type of the requested `ConfigSection`
#         ConfigFileParseError: Error parsing config file
#     """
#     attr_name = _get_config_section_attr_name(
#         config_class, config_section_class)

#     config = read_config_file(
#         config_class=config_class,
#         config_file_path=config_file_path)
#     config_section: ConfigSectionTypeVar = getattr(config, attr_name)
#     return config_section


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
        tuple(postconverted_unstructured.values())[0], dict
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
    read_config_file.cache_replace(
        config, config_class=type(config), config_file_path=config_file_path
    )


# def update_config_file_section(
#         config_class: type[Config],
#         config_section: ConfigSection,
#         config_file_path: Path) -> None:
#     """
#     Replace contents of a config file section with `config_section`

#     Raises:
#         ConfigFileParseError: Error parsing config file
#         MissingConfigSectionError: Config doesn't have the requested
#             ConfigSection
#         MultipleConfigSectionsError: Config has multiple sections matching
#             the type of the requested ConfigSection
#     """
#     config = read_config_file(
#         config_class=config_class,
#         config_file_path=config_file_path)
#     section_attr = _get_config_section_attr_name(
#         config_class, type(config_section))
#     updated_config = attrs.evolve(config, **{section_attr: config_section})
#     update_config_file(updated_config, config_file_path)


@attrs.frozen
class ConfigManager:
    get_merged_program_config: Callable[[ProgramConfig], ProgramConfig]
    get_merged_game_config: Callable[[GameConfig], GameConfig]
    get_merged_game_accounts_config: Callable[[GameAccountsConfig], GameAccountsConfig]
    program_config_path: Path = PROGRAM_CONFIG_DEFAULT_PATH
    games_dir_path: Path = GAMES_DIR_DEFAULT_PATH

    GAME_CONFIG_FILE_NAME: Final[str] = attrs.field(default="config1.toml", init=False)

    def get_game_config_dir(self, game_uuid: UUID) -> Path:
        return self.games_dir_path / str(game_uuid)

    def get_game_config_path(self, game_uuid: UUID) -> Path:
        return self.get_game_config_dir(game_uuid) / self.GAME_CONFIG_FILE_NAME

    def get_game_accounts_config_path(self, game_uuid: UUID) -> Path:
        return self.get_game_config_dir(game_uuid) / "accounts.toml"

    def get_program_config(self) -> ProgramConfig:
        """
        Get merged program config object.

        Raises:
            FileNotFoundError: Config file not found
            ConfigFileParseError: Error parsing config file
        """
        return self.get_merged_program_config(self.read_program_config_file())

    def read_program_config_file(self) -> ProgramConfig:
        """
        Read and parse program config file into `ProgramConfig` object.

        Raises:
            FileNotFoundError: Config file not found
            ConfigFileParseError: Error parsing config file
        """
        return read_config_file(
            config_class=ProgramConfig, config_file_path=self.program_config_path
        )

    def update_program_config_file(self, config: ProgramConfig) -> None:
        """
        Replace contents of program config file with `config`.
        """
        update_config_file(config, self.program_config_path)

    def get_game_uuids(self) -> tuple[UUID, ...]:
        return tuple(
            UUID(config_file.parent.name)
            for config_file in self.games_dir_path.glob(
                f"*/{self.GAME_CONFIG_FILE_NAME}"
            )
        )

    def get_game_config(self, game_uuid: UUID) -> GameConfig:
        """
        Get merged game config object.

        Raises:
            FileNotFoundError: Config file not found
            ConfigFileParseError: Error parsing config file
        """
        return self.get_merged_game_config(self.read_game_config_file(game_uuid))

    # def get_game_config_section(
    #         self,
    #         game_uuid: UUID,
    #         config_section: type[ConfigSectionTypeVar]
    # ) -> ConfigSectionTypeVar:
    #     """
    #     Raises:
    #         MissingConfigSectionError: `Config` doesn't have the requested
    #             `ConfigSection`_description_
    #         MultipleConfigSectionsError: `Config` has multiple sections
    #             matching the type of the requested `ConfigSection`
    #     """
    #     return self.read_game_config_file_section(game_uuid, config_section)

    def read_game_config_file(self, game_uuid: UUID) -> GameConfig:
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

    # def read_game_config_file_section(
    #         self,
    #         game_uuid: UUID,
    #         config_section: type[ConfigSectionTypeVar]
    # ) -> ConfigSectionTypeVar:
    #     """
    #     Raises:
    #         MissingConfigSectionError: Config doesn't have the requested
    #             ConfigSection
    #         MultipleConfigSectionsError: Config has multiple sections matching
    #             the type of the requested ConfigSection
    #         ConfigFileParseError: Error parsing config file
    #     """
    #     return read_config_file_section(
    #         config_class=GameConfig,
    #         config_section_class=config_section,
    #         config_file_path=self.get_game_config_path(game_uuid))

    def update_game_config_file(self, game_uuid: UUID, config: GameConfig) -> None:
        """
        Replace contents of game config file with `config`.
        """
        update_config_file(
            config=config, config_file_path=self.get_game_config_path(game_uuid)
        )

    # def update_game_config_file_section(
    #         self,
    #         game_uuid: UUID,
    #         config_section: ConfigSection) -> None:
    #     """
    #     Replace contents of game config file section with `config_section`.

    #     Raises:
    #         ConfigFileParseError: Error parsing config file
    #         MissingConfigSectionError: Config doesn't have the requested
    #             ConfigSection
    #         MultipleConfigSectionsError: Config has multiple sections matching
    #             the type of the requested ConfigSection
    #     """
    #     update_config_file_section(
    #         config_class=GameConfig,
    #         config_section=config_section,
    #         config_file_path=self.get_game_config_path(game_uuid))

    def get_game_accounts_config(
        self, game_uuid: UUID
    ) -> tuple[GameAccountConfig, ...]:
        """
        Raises:
            FileNotFoundError: Config file not found
            ConfigFileParseError: Error parsing config file
        """
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

    def read_game_accounts_config_file(
        self, game_uuid: UUID
    ) -> tuple[GameAccountConfig, ...]:
        """
        Read and parse game accounts config file into tuple of
        `GameAccountConfig` objects.

        Raises:
            ConfigFileParseError: Error parsing config file
        """
        return self._read_game_accounts_config_file_full(game_uuid).accounts

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
