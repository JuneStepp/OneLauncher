from PySide6 import QtGui

from onelauncher.resources import data_dir


def get_icon_font() -> QtGui.QFont:
    # Setup font for icons
    font_file = data_dir/"fonts/Font Awesome 5 Free-Solid-900.otf"
    font_db = QtGui.QFontDatabase()
    font_id = font_db.addApplicationFont(str(font_file))
    font_family = font_db.applicationFontFamilies(font_id)
    icon_font = QtGui.QFont(font_family)
    icon_font.setHintingPreference(QtGui.QFont.PreferNoHinting)
    icon_font.setPixelSize(16)

    return icon_font


icon_font = get_icon_font()
