from datetime import datetime
from textwrap import dedent
from typing import Any
from zoneinfo import ZoneInfo

import onelauncher.config_manager
import pytest
import tomlkit
from onelauncher.config import ConfigFieldMetadata, ConfigValWithMetadata

test_key_val_params: list[tuple[dict[str, Any], str]] = [
    ({"key": "val"}, 'key = "val"\n'),
    (
        {"key": ConfigValWithMetadata(value="val", metadata=ConfigFieldMetadata(None))},
        'key = "val"\n',
    ),
    (
        {
            "key": ConfigValWithMetadata(
                value="val", metadata=ConfigFieldMetadata("Helpful words")
            )
        },
        dedent(
            text="""\
            # Helpful words
            key = "val"
            """
        ),
    ),
    (
        {"key": ConfigValWithMetadata(value=None, metadata=ConfigFieldMetadata(None))},
        "# key = \n",
    ),
    (
        {
            "key": ConfigValWithMetadata(
                value=None, metadata=ConfigFieldMetadata("Helpful words")
            )
        },
        dedent(
            text="""\
            # Helpful words
            # key = 
            """
        ),
    ),
]

test_table_params = [
    ({"table": data_dict}, f"[table]\n{final_output}")
    for data_dict, final_output in test_key_val_params
]

test_val_types_params: list[tuple[dict[str, Any], str]] = [
    ({"key": "val"}, 'key = "val"\n'),
    ({"key": 123}, "key = 123\n"),
    ({"key": 123.456}, "key = 123.456\n"),
    ({"key": True}, "key = true\n"),
    ({"key": False}, "key = false\n"),
    ({"key": ["a", 2, True]}, 'key = ["a", 2, true]\n'),
    ({"table": {}}, "[table]\n"),
    (
        {
            "key": datetime(
                year=2000,
                month=2,
                day=12,
                hour=2,
                minute=24,
                second=19,
                tzinfo=ZoneInfo("Asia/Bangkok"),
            )
        },
        "key = 2000-02-12T02:24:19+07:00\n",
    ),
    (
        {"tables": [{"key": "value"}, {"key": "value"}]},
        dedent(
            text="""\
            [[tables]]
            key = "value"

            [[tables]]
            key = "value"
            """
        ),
    ),
    (
        {
            "table": ConfigValWithMetadata(
                value={"key": "val"}, metadata=ConfigFieldMetadata(help="Helpful words")
            )
        },
        dedent(
            text="""\
            [table]
            key = "val"
            """
        ),
    ),
]


@pytest.mark.parametrize(
    ("data_dict", "final_toml_output"),
    test_key_val_params + test_table_params + test_val_types_params,
)
def test_convert_to_toml(
    data_dict: dict[str, Any | ConfigValWithMetadata], final_toml_output: str
) -> None:
    container = tomlkit.document()
    onelauncher.config_manager.convert_to_toml(data_dict=data_dict, container=container)
    assert container.as_string() == final_toml_output
