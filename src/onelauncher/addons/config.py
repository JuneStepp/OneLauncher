from pathlib import Path

import attrs

from ..config import ConfigSection, config_field
from .startup_script import StartupScript


@attrs.frozen
class AddonsConfigSection(ConfigSection):
    enabled_startup_scripts: tuple[StartupScript, ...] = config_field(
        default=(), help="Startup scripts run before game launch"
    )
