from collections.abc import Generator
from pathlib import Path

import mypy.api
import mypy.plugins.attrs
import mypy.version
import pytest
from mypy.options import Options

from onelauncher import mypy_plugin
from onelauncher.config import config_field


@pytest.fixture(autouse=True)
def _reset_attrs_mypy_plugin() -> Generator[None, None, None]:
    initial_attrib_makers: set[str] = mypy.plugins.attrs.attr_attrib_makers.copy()
    yield
    mypy.plugins.attrs.attr_attrib_makers.clear()
    mypy.plugins.attrs.attr_attrib_makers.update(initial_attrib_makers)


def test_attrs_attrib_maker_name() -> None:
    """
    Test that the attrib maker name passed to mypy points to the right function in
    OneLauncher
    """
    assert (
        f"{config_field.__module__}.{config_field.__qualname__}"
        == mypy_plugin.ATTRS_MAKER
    )


def test_injecting_attrs_attrib_maker() -> None:
    assert mypy_plugin.ATTRS_MAKER not in mypy.plugins.attrs.attr_attrib_makers
    mypy_plugin.plugin(mypy.version.__version__)(Options())
    assert mypy_plugin.ATTRS_MAKER in mypy.plugins.attrs.attr_attrib_makers


def test_running_plugin_with_mypy() -> None:
    normal_report, error_report, exit_status = mypy.api.run(
        [str(Path(__file__).parent / "_test_mypy_plugin.mypy_test_data.py")]
    )
    assert (
        """error: Missing positional argument "x" in call to "AttrsClassUsingConfigField"  [call-arg]"""
        in normal_report
    )
    assert """Found 1 error in 1 file""" in normal_report
