"""
Icon Helper Utility using QtAwesome (Font Awesome 5 Solid Icons).
Dynamically adjusts default icon colors for Light and Dark modes
to ensure maximum contrast and visibility.
"""

import qtawesome as qta
from PySide6.QtGui import QIcon


ICON_MAP = {
    'dashboard': 'fa5s.chart-bar',
    'students': 'fa5s.users',
    'exams': 'fa5s.book',
    'templates': 'fa5s.ruler-combined',
    'generator': 'fa5s.print',
    'correction': 'fa5s.play',
    'audit': 'fa5s.search',
    'reports': 'fa5s.file-alt',
    'moon': 'fa5s.moon',
    'sun': 'fa5s.sun',
    'plus': 'fa5s.plus',
    'edit': 'fa5s.pen',
    'delete': 'fa5s.trash-alt',
    'preview': 'fa5s.eye',
    'check': 'fa5s.check-circle',
    'warning': 'fa5s.exclamation-triangle',
    'danger': 'fa5s.ban',
    'sync': 'fa5s.sync-alt',
    'excel': 'fa5s.file-excel',
    'folder': 'fa5s.folder-open',
    'zoom-in': 'fa5s.search-plus',
    'zoom-out': 'fa5s.search-minus',
    'reset': 'fa5s.undo',
    'slider': 'fa5s.sliders-h',
    'color': 'fa5s.palette',
    'user': 'fa5s.user',
    'class': 'fa5s.graduation-cap',
    'list': 'fa5s.list-ol'
}


def get_icon(name: str, color: str = None) -> QIcon:
    """
    Returns a QIcon corresponding to the specified key.
    Automatically adapts default color based on current Light/Dark mode for maximum contrast.
    """
    fa_name = ICON_MAP.get(name, 'fa5s.circle')
    try:
        if not color:
            from omr_app.gui.theme_manager import ThemeManager
            if ThemeManager.is_dark_mode():
                color = "#F8FAFC"  # High contrast crisp off-white for dark mode
            else:
                color = "#1E293B"  # High contrast dark slate for light mode
        elif color == "white":
            color = "#FFFFFF"
        elif color == "primary":
            color = "#00AEA7"
        elif color == "secondary":
            color = "#002970"
        elif color == "danger":
            color = "#EF4444"

        return qta.icon(fa_name, color=color)
    except Exception:
        return QIcon()
