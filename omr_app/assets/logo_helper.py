"""
Logo & Favicon Utility Helper.
Provides access to application logo in SVG and PNG formats.
"""

import os
from PySide6.QtGui import QIcon, QPixmap

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT_SVG = os.path.join(BASE_DIR, "logo_cortex.svg")
ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_SVG = os.path.join(ASSETS_DIR, "logo_cortex.svg")
ASSETS_PNG = os.path.join(ASSETS_DIR, "logo_cortex.png")


def get_logo_svg_path() -> str:
    """Returns absolute path to logo_cortex.svg"""
    if os.path.exists(ROOT_SVG):
        return ROOT_SVG
    if os.path.exists(ASSETS_SVG):
        return ASSETS_SVG
    return ""


def get_logo_png_path() -> str:
    """Returns absolute path to logo_cortex.png, generating PNG from SVG if missing."""
    if os.path.exists(ASSETS_PNG):
        return ASSETS_PNG

    svg_p = get_logo_svg_path()
    if svg_p and os.path.exists(svg_p):
        try:
            pixmap = QPixmap(svg_p)
            if not pixmap.isNull():
                pixmap.save(ASSETS_PNG, "PNG")
                return ASSETS_PNG
        except Exception:
            pass
    return ""


def get_app_icon() -> QIcon:
    """Returns QIcon window favicon derived from logo_cortex.svg"""
    svg_p = get_logo_svg_path()
    if svg_p and os.path.exists(svg_p):
        return QIcon(svg_p)
    png_p = get_logo_png_path()
    if png_p and os.path.exists(png_p):
        return QIcon(png_p)
    return QIcon()
