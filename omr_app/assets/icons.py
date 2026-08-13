"""
Icon Helper Utility using QtAwesome (Font Awesome 5 Solid Icons).
Replaces text emojis with clean, professional vector icons.
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
    If color is provided (hex string like '#00AEA7'), styles the icon accordingly.
    """
    fa_name = ICON_MAP.get(name, 'fa5s.circle')
    try:
        if color:
            return qta.icon(fa_name, color=color)
        return qta.icon(fa_name)
    except Exception:
        return QIcon()
