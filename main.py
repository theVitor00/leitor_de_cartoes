"""
Ponto de entrada principal da Aplicação Desktop OMR.
Inicializa o banco de dados SQLite, o tema PySide6 e a janela principal.
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from omr_app.database.db_manager import init_db
from omr_app.gui.theme_manager import ThemeManager
from omr_app.gui.main_window import MainWindow


def main():
    # 1. Initialize SQLite Database & Seed initial data if needed
    db_path = init_db()
    print(f"✅ Banco de dados SQLite inicializado em: {db_path}")

    # 2. Create PySide6 QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Leitor OMR Desktop")
    app.setOrganizationName("OMR System")

    # 3. Apply default Dark Theme QSS
    ThemeManager.apply_theme(app)

    # 4. Instantiate and show MainWindow
    window = MainWindow()
    window.show()

    # 5. Execute Qt Event Loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
