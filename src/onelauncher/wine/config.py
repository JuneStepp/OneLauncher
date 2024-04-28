from pathlib import Path

import attrs

from ..config import config_field


@attrs.frozen
class WineConfigSection:
    builtin_prefix_enabled: bool = config_field(
        default=True, help="If WINE should be automatically managed"
    )
    user_wine_executable_path: Path | None = config_field(
        default=None,
        help=(
            "Path to the WINE executable to use when WINE isn't "
            "automatically managed"
        ),
    )
    user_prefix_path: Path | None = config_field(
        default=None,
        help=(
            "Path to the WINE prefix to use when WINE isn't automatically " "managed"
        ),
    )
    debug_level: str | None = config_field(default=None, help="WINE debug level to use")
