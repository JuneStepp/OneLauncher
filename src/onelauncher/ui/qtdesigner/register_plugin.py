from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

from onelauncher.ui.qtdesigner.custom_widgets import (
    QDialogWithStylePreview,
    QMainWindowWithStylePreview,
    QWidgetWithStylePreview,
)
from onelauncher.ui.qtdesigner.style_preview_plugin import (
    CustomStylesheetPlugin,
)

if __name__ == "__main__":
    QPyDesignerCustomWidgetCollection.addCustomWidget(
        CustomStylesheetPlugin(widget_type=QWidgetWithStylePreview)
    )
    QPyDesignerCustomWidgetCollection.addCustomWidget(
        CustomStylesheetPlugin(widget_type=QDialogWithStylePreview)
    )
    QPyDesignerCustomWidgetCollection.addCustomWidget(
        CustomStylesheetPlugin(widget_type=QMainWindowWithStylePreview)
    )
