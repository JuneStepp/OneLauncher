from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Self, overload

import attrs
import cattrs
from cattrs.dispatch import StructuredValue, UnstructuredValue
from packaging.version import Version
from platformdirs import PlatformDirs

from .__about__ import __title__

platform_dirs = PlatformDirs(__title__.lower(), ensure_exists=True)


@attrs.frozen
class Config(ABC):
    @staticmethod
    @abstractmethod
    def get_config_file_description() -> str:
        """The description of this config shown to the user"""

    @staticmethod
    @abstractmethod
    def get_config_version() -> Version:
        """
        The version of this config. It should be updated when the config format
        changes.
        """


# The typing for the `config_field` overloads is based on
# https://github.com/python-attrs/attrs/blob/main/src/attrs/__init__.pyi
# field types.


if TYPE_CHECKING:
    from attr import (
        _T,
        _ConverterType,
        _EqOrderType,
        _OnSetAttrArgType,
        _ReprArgType,
        _ValidatorArgType,
    )

_CONFIG_METADATA = "__config"
_CONFIG_HELP_METADATA = "__config_help"


@overload
def config_field(
    *,
    default: None = ...,
    validator: None = ...,
    repr: _ReprArgType = ...,  # noqa: A002
    hash: bool | None = ...,  # noqa: A002
    init: bool = ...,
    metadata: Mapping[Any, Any] | None = ...,
    converter: None = ...,
    factory: None = ...,
    kw_only: bool = ...,
    eq: bool | None = ...,
    order: bool | None = ...,
    on_setattr: _OnSetAttrArgType | None = ...,
    alias: str | None = ...,
    type: type | None = ...,  # noqa: A002
    help: str | None = ...,  # noqa: A002
) -> Any: ...  # noqa: ANN401


@overload
def config_field(
    *,
    default: None = ...,
    validator: _ValidatorArgType[_T] | None = ...,
    repr: _ReprArgType = ...,  # noqa: A002
    hash: bool | None = ...,  # noqa: A002
    init: bool = ...,
    metadata: Mapping[Any, Any] | None = ...,
    converter: _ConverterType | None = ...,
    factory: Callable[[], _T] | None = ...,
    kw_only: bool = ...,
    eq: _EqOrderType | None = ...,
    order: _EqOrderType | None = ...,
    on_setattr: _OnSetAttrArgType | None = ...,
    alias: str | None = ...,
    type: type | None = ...,  # noqa: A002
    help: str | None = ...,  # noqa: A002
) -> _T:
    """
    This form catches an explicit None or no default and infers the type from
    the other arguments.
    """
    ...


@overload
def config_field(
    *,
    default: _T,
    validator: _ValidatorArgType[_T] | None = ...,
    repr: _ReprArgType = ...,  # noqa: A002
    hash: bool | None = ...,  # noqa: A002
    init: bool = ...,
    metadata: Mapping[Any, Any] | None = ...,
    converter: _ConverterType | None = ...,
    factory: Callable[[], _T] | None = ...,
    kw_only: bool = ...,
    eq: _EqOrderType | None = ...,
    order: _EqOrderType | None = ...,
    on_setattr: _OnSetAttrArgType | None = ...,
    alias: str | None = ...,
    type: type | None = ...,  # noqa: A002
    help: str | None = ...,  # noqa: A002
) -> _T:
    """
    This form catches an explicit default argument.
    """
    ...


@overload
def config_field(
    *,
    default: _T | None = ...,
    validator: _ValidatorArgType[_T] | None = ...,
    repr: _ReprArgType = ...,  # noqa: A002
    hash: bool | None = ...,  # noqa: A002
    init: bool = ...,
    metadata: Mapping[Any, Any] | None = ...,
    converter: _ConverterType | None = ...,
    factory: Callable[[], _T] | None = ...,
    kw_only: bool = ...,
    eq: _EqOrderType | None = ...,
    order: _EqOrderType | None = ...,
    on_setattr: _OnSetAttrArgType | None = ...,
    alias: str | None = ...,
    type: type | None = ...,  # noqa: A002
    help: str | None = ...,  # noqa: A002
) -> Any:  # noqa: ANN401
    """
    This form covers type=non-Type: e.g. forward references (str), Any
    """
    ...


def config_field(  # type: ignore[no-untyped-def]
    *,
    default=attrs.NOTHING,
    validator=None,
    repr=True,  # noqa: A002
    hash=None,  # noqa: A002
    init=True,
    metadata=None,
    type=None,  # noqa: A002
    converter=None,
    factory=None,
    kw_only=False,
    eq=None,
    order=None,
    on_setattr=None,
    alias=None,
    help: str | None = None,  # noqa: A002
):
    """
    Alias to `attrs.field()` with a config help parameter.
    """
    metadata = metadata or {}
    # Mark the field as a config field
    metadata[_CONFIG_METADATA] = True
    metadata[_CONFIG_HELP_METADATA] = help

    return attrs.field(
        default=default,
        validator=validator,
        repr=repr,
        hash=hash,
        init=init,
        metadata=metadata,
        type=type,
        converter=converter,
        factory=factory,
        kw_only=kw_only,
        eq=eq,
        order=order,
        on_setattr=on_setattr,
        alias=alias,
    )


class NotConfigAttributeError(ValueError):
    """Attribute doesn't have config metadata"""


@attrs.frozen
class ConfigFieldMetadata:
    help: str | None = None

    @classmethod
    def from_attribute(cls: type[Self], attribute: attrs.Attribute[Any]) -> Self:
        """
        Raises:
            NotConfigAttributeError: Attribute doesn't have config metadata
        """
        if not attribute.metadata.get(_CONFIG_METADATA):
            raise NotConfigAttributeError

        return cls(help=attribute.metadata.get(_CONFIG_HELP_METADATA))

    @classmethod
    def from_field_name(
        cls: type[Self], field_name: str, attrs_class: type[attrs.AttrsInstance]
    ) -> Self:
        return cls.from_attribute(attrs.fields_dict(attrs_class)[field_name])


@attrs.frozen
class ConfigValWithMetadata:
    value: Any
    metadata: ConfigFieldMetadata


def unstructure_config(
    converter: cattrs.Converter, obj: StructuredValue
) -> UnstructuredValue:
    """
    cattrs unstructure hook function for handling help/documentation metadata
    """
    base_unstructure_func = converter.gen_unstructure_attrs_fromdict(type(obj))
    destructured = base_unstructure_func(obj)
    # Convert config vals to `ConfigValWithMetadata`.
    if isinstance(destructured, dict) and attrs.has(type(obj)):
        for attribute in attrs.fields_dict(type(obj)).values():
            if attribute.name in destructured:
                destructured_val = destructured[attribute.name]
                if not isinstance(destructured_val, ConfigValWithMetadata):
                    with suppress(NotConfigAttributeError):
                        destructured[attribute.name] = ConfigValWithMetadata(
                            destructured_val,
                            ConfigFieldMetadata.from_attribute(attribute),
                        )
    return destructured
