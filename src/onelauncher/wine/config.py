from enum import Enum
from pathlib import Path

import attrs

from ..config import config_field


class WineMethod(Enum):
    LINUX = "linux"
    MOLTENVK_LEGACY = "legacy"
    MOLTENVK = "moltenvk"
    MOLTENVK_WINEHQ = "moltenvk_winehq"
    KOSMICKRISP = "kosmickrisp"


@attrs.frozen
class WineConfigSection:
    builtin_prefix_enabled: bool = config_field(
        default=True, help="If WINE should be automatically managed"
    )
    wine_method: WineMethod | None = config_field(  # noqa: RUF009
        default=None,
        help="WINE method. You should not normally need to change this.",
    )
    user_wine_executable_path: Path | None = config_field(  # noqa: RUF009
        default=None,
        help=(
            "Path to the WINE executable to use when WINE isn't automatically managed"
        ),
    )
    user_prefix_path: Path | None = config_field(  # noqa: RUF009
        default=None,
        help="Path to the WINE prefix to use when WINE isn't automatically managed",
    )
    debug_level: str | None = config_field(
        default=None, help="Value for the WINEDEBUG environment variable"
    )
