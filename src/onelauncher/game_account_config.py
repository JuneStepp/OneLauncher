import attrs
from packaging.version import Version
from typing_extensions import override

from .__about__ import __title__
from .config import Config, config_field


@attrs.frozen
class GameAccountConfig:
    username: str = config_field(help="Login username")
    display_name: str | None = config_field(
        default=None, help="Name shown instead of account name"
    )
    last_used_world_name: str | None = config_field(
        default=None, help="World last logged into. Will be the default at next login"
    )


@attrs.frozen
class GameAccountsConfig(Config):
    accounts: tuple[GameAccountConfig, ...]

    @override
    @staticmethod
    def get_config_version() -> Version:
        return Version("2.0")

    @override
    @staticmethod
    def get_config_file_description() -> str:
        return f"A game accounts config file for {__title__}"
