import attrs

from ..config import config_field
from .startup_script import StartupScript


@attrs.frozen
class AddonsConfigSection:
    enabled_startup_scripts: tuple[StartupScript, ...] = config_field(
        default=(),
        help="Python scripts run before game launch. Paths are relative to the game's documents config directory",
    )
