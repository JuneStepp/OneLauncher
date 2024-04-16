"""
File analyzed with mypy as part of `test_mypy_plugin.py`. Has intentional type errors.
"""
from typing import Any

import attrs
from onelauncher.config import config_field


@attrs.define
class AttrsClassUsingConfigField:
    x: Any = config_field()


AttrsClassUsingConfigField()
