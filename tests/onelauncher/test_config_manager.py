from datetime import datetime, timedelta, timezone
from pathlib import Path
from textwrap import dedent
from typing import Any

import onelauncher.config_manager
import pytest
import tomlkit
from onelauncher.config import ConfigFieldMetadata, ConfigValWithMetadata
from onelauncher.program_config import ProgramConfig

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
    ({"array": [1, 2]}, "array = [1, 2]\n"),
    ({"empty_array": []}, "empty_array = []\n"),
    (
        {
            "key": datetime(
                year=2000,
                month=2,
                day=12,
                hour=2,
                minute=24,
                second=19,
                tzinfo=timezone(timedelta(hours=7)),
            )
        },
        "key = 2000-02-12T02:24:19+07:00\n",
    ),
    # Table
    (
        {"table": {"key": "val"}},
        dedent(
            text="""\
            [table]
            key = "val"
            """
        ),
    ),
    ({"empty_table": {}}, ""),
    # Table with description
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
    # List of tables
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
]


@pytest.mark.parametrize(
    ("data_dict", "final_toml_output"),
    test_key_val_params + test_table_params + test_val_types_params,
)
def test_convert_to_toml(  # type: ignore[misc]
    data_dict: dict[str, Any | ConfigValWithMetadata], final_toml_output: str
) -> None:
    container = tomlkit.document()
    onelauncher.config_manager.convert_to_toml(data_dict=data_dict, container=container)
    assert container.as_string() == final_toml_output


def test_allow_unknown_config_keys(tmp_path: Path) -> None:
    UNKNOWN_KEY_NAME = "test_unknown_key_name"
    assert not hasattr(ProgramConfig, UNKNOWN_KEY_NAME)

    config_path = tmp_path / "test_config.toml"
    # Initialize the config file
    onelauncher.config_manager.update_config_file(
        config=ProgramConfig(), config_file_path=config_path
    )
    with config_path.open(mode="a") as f:
        f.write(f"{UNKNOWN_KEY_NAME} = 3.14")

    onelauncher.config_manager.read_config_file(
        config_class=ProgramConfig, config_file_path=config_path
    )
