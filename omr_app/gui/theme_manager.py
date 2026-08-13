"""
Theme Manager for dynamic switching between Light Mode and Dark Mode.
"""

from PySide6.QtWidgets import QApplication
from omr_app.assets.styles import DARK_THEME_QSS, LIGHT_THEME_QSS


class ThemeManager:
    _is_dark_mode = True

    @classmethod
    def is_dark_mode(cls) -> bool:
        return cls._is_dark_mode

    @classmethod
    def toggle_theme(cls, app: QApplication) -> bool:
        cls._is_dark_mode = not cls._is_dark_mode
        cls.apply_theme(app)
        return cls._is_dark_mode

    @classmethod
    def apply_theme(cls, app: QApplication):
        if cls._is_dark_mode:
            app.setStyleSheet(DARK_THEME_QSS)
        else:
            app.setStyleSheet(LIGHT_THEME_QSS)
