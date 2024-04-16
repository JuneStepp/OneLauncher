"""
Mypy plugin that makes mypy recognize the the OneLauncher `config_field` `attrs.field()` wrapper.
"""

from mypy.options import Options
from mypy.plugin import Plugin
from mypy.plugins.attrs import attr_attrib_makers

ATTRS_MAKER = "onelauncher.config.config_field"


class AttrsFieldWrapperPlugin(Plugin):
    def __init__(self, options: Options) -> None:
        super().__init__(options)
        # These are our `attr.ib` makers.
        attr_attrib_makers.add(ATTRS_MAKER)


def plugin(version: str) -> type[AttrsFieldWrapperPlugin]:
    """
    Return the class for our plugin.
    """
    return AttrsFieldWrapperPlugin
