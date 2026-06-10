from typing import override

from PySide6 import QtDesigner, QtGui, QtWidgets

from onelauncher.ui.style import ApplicationStyle


class CustomStylesheetPlugin(QtDesigner.QDesignerCustomWidgetInterface):
    def __init__(self, widget_type: type[QtWidgets.QWidget]) -> None:
        super().__init__()
        self.widget_type = widget_type
        self._form_editor: QtDesigner.QDesignerFormEditorInterface | None = None

    @override
    def createWidget(self, parent: QtWidgets.QWidget | None) -> QtWidgets.QWidget:
        widget = self.widget_type(parent)
        widget.setStyleSheet(self._app_stylesheet)
        return widget

    @override
    def domXml(self) -> str:
        return f"""
<ui language='c++'>
    <widget class="{self.name()}" >
    </widget>
</ui>
"""

    @override
    def group(self) -> str:
        return ""

    @override
    def icon(self) -> QtGui.QIcon:
        return QtGui.QIcon()

    @override
    def includeFile(self) -> str:
        return ".qtdesigner.custom_widgets"

    @override
    def initialize(self, form_editor: QtDesigner.QDesignerFormEditorInterface) -> None:
        self._form_editor = form_editor
        qapp = QtWidgets.QApplication.instance()
        if not qapp or not isinstance(qapp, QtWidgets.QApplication):
            raise RuntimeError("No QApplication found.")
        self._app_stylesheet = ApplicationStyle(qapp).generate_stylesheet(
            qtdesigner_version=True
        )

    @override
    def isInitialized(self) -> bool:
        return self._form_editor is not None

    @override
    def isContainer(self) -> bool:
        return True

    @override
    def name(self) -> str:
        return self.widget_type.__name__

    @override
    def toolTip(self) -> str:
        return f"{self.widget_type.mro()[1].__name__} with special stylesheet set for proper display in QtDesigner"

    @override
    def whatsThis(self) -> str:
        return self.toolTip()
