from PySide6.QtWidgets import QDialog, QMainWindow, QWidget

class TitleBarBase(QWidget): ...
class TitleBar(TitleBarBase): ...

class FramelessWindow:
    titleBar: TitleBar

class FramelessDialog(FramelessWindow, QDialog): ...
class FramelessMainWindow(FramelessWindow, QMainWindow): ...
