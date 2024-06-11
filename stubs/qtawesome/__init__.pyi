from typing import Literal, TypedDict

from qtpy.QtGui import QColor, QIcon
from qtpy.QtWidgets import QWidget

class Spin:
    def __init__(
        self,
        parent_widget: QWidget,
        interval: int = 10,
        step: int = 1,
        autostart: bool = True,
    ): ...

class Pulse(Spin):
    def __init__(self, parent_widget: QWidget, autostart: bool = True): ...

Color = str | QColor | tuple[str, int]

def set_defaults(
    color: str | QColor = ...,
    offset: tuple[float, float] = ...,
    animation: Spin | Pulse | None = None,
    scale_factor: float = ...,
    active: str = ...,
    color_active: str | QColor = ...,
    disabled: str = ...,
    color_disabled: str | QColor = ...,
    selected: str = ...,
    color_selected: str | QColor = ...,
) -> None: ...

class OptionsDict(TypedDict, total=False):
    color: str | QColor
    offset: tuple[float, float]
    animation: Spin | Pulse | None
    draw: Literal["text", "path", "glphrun", "image"]
    scale_factor: float
    active: str
    color_active: str | QColor
    disabled: str
    color_disabled: str | QColor
    selected: str
    color_selected: str | QColor

def icon(
    *names: str,
    rotated: int = ...,
    hflip: bool = ...,
    vflip: bool = ...,
    options: list[OptionsDict] = ...,
    color: str | QColor = ...,
    offset: tuple[float, float] = ...,
    animation: Spin | Pulse | None = None,
    scale_factor: float = ...,
    active: str = ...,
    color_active: str | QColor = ...,
    disabled: str = ...,
    color_disabled: str | QColor = ...,
    selected: str = ...,
    color_selected: str | QColor = ...,
) -> QIcon: ...
def load_font(
    prefix: str, ttf_filename: str, charmap_filename: str, directory: str | None = None
) -> None: ...
