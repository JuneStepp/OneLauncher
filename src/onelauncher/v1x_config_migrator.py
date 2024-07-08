import os
import shutil
from contextlib import suppress
from functools import partial
from pathlib import Path
from typing import Any, Literal, TypeAlias, assert_never
from uuid import uuid4

import attrs
import cattrs
import keyring
import xmlschema

from onelauncher.addons.config import AddonsConfigSection
from onelauncher.addons.startup_script import StartupScript
from onelauncher.config_manager import ConfigManager
from onelauncher.game_account_config import GameAccountConfig
from onelauncher.wine.config import WineConfigSection

from .game_config import ClientType, GameConfig, GameType
from .resources import OneLauncherLocale, available_locales, data_dir
from .utilities import CaseInsensitiveAbsolutePath


def get_v1x_config_dir() -> Path:
    """
    This directory held everything including cache info in 1.x OneLauncher versions.
    That means that all old 1.x non-install files can be removed by deleting this.
    """
    return (
        (
            Path(os.environ.get("APPDATA") or Path.home() / "AppData/Roaming")
            / "OneLauncher"
        )
        if os.name == "nt"
        else Path.home() / ".OneLauncher"
    )


def get_v1x_config_file_path() -> Path:
    return get_v1x_config_dir() / "OneLauncher.config"


@attrs.frozen
class V1xGameAccounts:
    accounts: tuple[GameAccountConfig, ...] = ()


@attrs.frozen
class V1xStatupScripts:
    startup_scripts: tuple[StartupScript, ...] = ()


@attrs.frozen(kw_only=True)
class V1xGameConfig:
    wine_program: Path | None = None
    wine_debug: str = "fixme-all"
    wine_prefix: Path | None = None
    high_res_enabled: bool = True
    client_type: ClientType = ClientType.WIN64
    x64_client_enabled: bool | None = None
    save_password: bool = False
    game_directory: CaseInsensitiveAbsolutePath
    language: OneLauncherLocale | None = None
    patch_client: str = "patchclient.dll"
    accounts: V1xGameAccounts | None = None
    startup_scripts: V1xStatupScripts | None = None


V1xGameType: TypeAlias = Literal["LOTRO", "LOTRO.Test", "DDO", "DDO.Test"]


@attrs.frozen
class V1xConfig:
    default_game: V1xGameType | None = None
    lotro: V1xGameConfig | None = None
    lotro_test: V1xGameConfig | None = None
    ddo: V1xGameConfig | None = None
    ddo_test: V1xGameConfig | None = None


def _structure_bool(bool_str: str, conversion_type: type[bool]) -> bool:
    if bool_str == "True":
        return True
    elif bool_str == "False":
        return False
    raise ValueError("Not a valid boolean option")


def _structure_client_type(
    client_type_str: Literal["WIN64", "WIN32", "WIN32Legacy"],
    conversion_type: type[ClientType],
) -> ClientType:
    if client_type_str == "WIN64":
        return ClientType.WIN64
    elif client_type_str == "WIN32":
        return ClientType.WIN32
    elif client_type_str == "WIN32Legacy":
        return ClientType.WIN32_LEGACY
    else:
        assert_never(client_type_str)


def _structure_locale(
    locale_str: Literal["DE", "EN", "FR"], conversion_type: type[OneLauncherLocale]
) -> OneLauncherLocale:
    if locale_str == "DE":
        lang_tag = "de"
    elif locale_str == "EN":
        lang_tag = "en-US"
    elif locale_str == "FR":
        lang_tag = "fr"
    else:
        assert_never(locale_str)
    return available_locales[lang_tag]


def _structure_game_accounts(
    input_dict: dict[str, list[dict[Literal["World"], list[str]] | None]],
    conversion_type: type[V1xGameAccounts],
) -> V1xGameAccounts:
    return V1xGameAccounts(
        accounts=tuple(
            GameAccountConfig(
                username=username,
                last_used_world_name=account_dicts[0]["World"][0]
                if account_dicts[0] and "World" in account_dicts[0]
                else None,
            )
            for username, account_dicts in input_dict.items()
        )
    )


def _structure_startup_script(
    relative_path: str, conversion_type: type[StartupScript]
) -> StartupScript:
    return StartupScript(relative_path=Path(relative_path))


def get_converter() -> cattrs.Converter:
    converter = cattrs.Converter()
    config_structure_hook = cattrs.gen.make_dict_structure_fn(
        V1xConfig,
        converter,
        default_game=cattrs.override(rename="Default.Game"),
        lotro=cattrs.override(rename="LOTRO"),
        lotro_test=cattrs.override(rename="LOTRO.Test"),
        ddo=cattrs.override(rename="DDO"),
        ddo_test=cattrs.override(rename="DDO.Test"),
    )
    converter.register_structure_hook(V1xConfig, config_structure_hook)
    game_config_structure_hook = cattrs.gen.make_dict_structure_fn(
        V1xGameConfig,
        converter,
        wine_program=cattrs.override(rename="Wine.Program"),
        wine_debug=cattrs.override(rename="Wine.Debug"),
        wine_prefix=cattrs.override(rename="Wine.Prefix"),
        high_res_enabled=cattrs.override(rename="HiRes"),
        client_type=cattrs.override(rename="Client"),
        x64_client_enabled=cattrs.override(rename="x64Client"),
        save_password=cattrs.override(rename="Save.Password"),
        game_directory=cattrs.override(rename="Game.Directory"),
        language=cattrs.override(rename="Language"),
        patch_client=cattrs.override(rename="PatchClient"),
        accounts=cattrs.override(rename="Accounts"),
        startup_scripts=cattrs.override(rename="StartupScripts"),
    )
    converter.register_structure_hook(V1xGameConfig, game_config_structure_hook)
    structure_startup_scripts = cattrs.gen.make_dict_structure_fn(
        V1xStatupScripts,
        converter=converter,
        startup_scripts=cattrs.override(rename="script"),
    )
    converter.register_structure_hook(V1xStatupScripts, structure_startup_scripts)
    converter.register_structure_hook(bool, _structure_bool)
    converter.register_structure_hook(ClientType, _structure_client_type)
    converter.register_structure_hook(OneLauncherLocale, _structure_locale)
    converter.register_structure_hook(V1xGameAccounts, _structure_game_accounts)
    converter.register_structure_hook(StartupScript, _structure_startup_script)
    return converter


@attrs.frozen(kw_only=True)
class V1xConfigParseError(Exception):
    msg: str = "Error parsing config XML"


def convert_v1x_config(xml_str: str) -> V1xConfig:
    """
    Raises:
        V1xConfigParseError: Error parsing config XML
    """
    schema = xmlschema.XMLSchema11(data_dir / "schemas/v1x_config.xsd")
    try:
        xml_dict: dict[str, Any] = schema.to_dict(xml_str)  # type: ignore[assignment]
    except xmlschema.XMLSchemaValidationError as e:
        raise V1xConfigParseError() from e
    converter = get_converter()
    try:
        return converter.structure(xml_dict, V1xConfig)
    except cattrs.ClassValidationError as e:
        raise V1xConfigParseError() from e


def get_partial_game_config(
    v1x_game_config: V1xGameConfig, config_dir: Path
) -> partial[GameConfig]:
    if v1x_game_config.x64_client_enabled is not None:
        client_type = (
            ClientType.WIN64 if v1x_game_config.x64_client_enabled else ClientType.WIN32
        )
    else:
        client_type = v1x_game_config.client_type
    builtin_wine_prefix = config_dir / "wine/prefix"
    builtin_prefix_enabled = (
        not v1x_game_config.wine_prefix
        or v1x_game_config.wine_prefix.resolve() == builtin_wine_prefix.resolve()
    )
    wine_config = WineConfigSection(
        builtin_prefix_enabled=builtin_prefix_enabled,
        user_wine_executable_path=None
        if builtin_prefix_enabled
        else v1x_game_config.wine_program,
        user_prefix_path=None
        if builtin_prefix_enabled
        else v1x_game_config.wine_prefix,
        debug_level=v1x_game_config.wine_debug,
    )
    return partial(
        GameConfig,
        game_directory=v1x_game_config.game_directory,
        locale=v1x_game_config.language,
        client_type=client_type,
        high_res_enabled=v1x_game_config.high_res_enabled,
        patch_client_filename=v1x_game_config.patch_client,
        wine=wine_config,
    )


def migrate_v1x_config(config_manager: ConfigManager, delete_old_config: bool) -> None:
    """
    Migrate v1.x a.k.a pre-2.0 configs to current format and add to config manager.
    Nothing will be done, if no v1.x configs are found.

    Raises:
        V1xConfigParseError: Error parsing config
    """
    config_dir = get_v1x_config_dir()
    config_file = get_v1x_config_file_path()
    if not config_file.exists():
        return None
    v1x_config = convert_v1x_config(config_file.read_text())
    game_configs: list[tuple[GameConfig, tuple[GameAccountConfig, ...]]] = []
    lotro_addons_config: AddonsConfigSection | None = None
    if v1x_config.lotro:
        partial_game_config = get_partial_game_config(
            v1x_game_config=v1x_config.lotro, config_dir=config_dir
        )
        lotro_addons_config = AddonsConfigSection(
            enabled_startup_scripts=v1x_config.lotro.startup_scripts.startup_scripts
            if v1x_config.lotro.startup_scripts
            else ()
        )
        game_configs.append(
            (
                partial_game_config(
                    game_type=GameType.LOTRO,
                    is_preview_client=False,
                    addons=lotro_addons_config,
                ),
                v1x_config.lotro.accounts.accounts if v1x_config.lotro.accounts else (),
            )
        )
    if v1x_config.lotro_test:
        partial_game_config = get_partial_game_config(
            v1x_game_config=v1x_config.lotro_test, config_dir=config_dir
        )
        game_configs.append(
            (
                partial_game_config(
                    game_type=GameType.LOTRO,
                    is_preview_client=True,
                    # In v1.x, Preview clients shared startup scripts with the main client
                    addons=lotro_addons_config or AddonsConfigSection(),
                ),
                # In v1.x, Preview clients shared accounts with the main client
                v1x_config.lotro.accounts.accounts
                if v1x_config.lotro and v1x_config.lotro.accounts
                else (),
            )
        )
    ddo_addons_config: AddonsConfigSection | None = None
    if v1x_config.ddo:
        partial_game_config = get_partial_game_config(
            v1x_game_config=v1x_config.ddo, config_dir=config_dir
        )
        ddo_addons_config = AddonsConfigSection(
            enabled_startup_scripts=v1x_config.ddo.startup_scripts.startup_scripts
            if v1x_config.ddo.startup_scripts
            else ()
        )
        game_configs.append(
            (
                partial_game_config(
                    game_type=GameType.DDO,
                    is_preview_client=False,
                    addons=ddo_addons_config,
                ),
                v1x_config.ddo.accounts.accounts if v1x_config.ddo.accounts else (),
            )
        )
    if v1x_config.ddo_test:
        partial_game_config = get_partial_game_config(
            v1x_game_config=v1x_config.ddo_test, config_dir=config_dir
        )
        game_configs.append(
            (
                partial_game_config(
                    game_type=GameType.DDO,
                    is_preview_client=True,
                    # In v1.x, Preview clients shared startup scripts with the main client
                    addons=ddo_addons_config or AddonsConfigSection(),
                ),
                # In v1.x, Preview clients shared accounts with the main client
                v1x_config.ddo.accounts.accounts
                if v1x_config.ddo and v1x_config.ddo.accounts
                else (),
            )
        )
    for i, configs in enumerate(game_configs):
        game_uuid = uuid4()
        game_config = configs[0]
        account_configs = configs[1]
        config_manager.update_game_config_file(
            game_uuid, attrs.evolve(game_config, sorting_priority=i)
        )
        config_manager.update_game_accounts_config_file(
            game_uuid, accounts=account_configs
        )
        # Add account passwords to Keyring
        service_name = f"OneLauncher{'LOTRO' if game_config.game_type == GameType.LOTRO else 'DDO'}"
        for account_config in account_configs:
            if password := keyring.get_password(
                service_name=service_name,
                username=account_config.username,
            ):
                config_manager.save_game_account_password(
                    game_uuid=game_uuid, game_account=account_config, password=password
                )
                if delete_old_config:
                    with suppress(keyring.errors.PasswordDeleteError):
                        keyring.delete_password(
                            service_name=service_name, username=account_config.username
                        )
    if delete_old_config:
        shutil.rmtree(config_dir)
