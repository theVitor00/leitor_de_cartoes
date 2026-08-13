"""
Main Window for the PySide6 OMR Desktop Application.
Integrates Sidebar Navigation with Official Cortex Logo, Application Favicon,
Top Header with Theme Switcher, and View Stack.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QFrame, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from omr_app.assets.icons import get_icon
from omr_app.assets.logo_helper import get_app_icon, get_logo_svg_path
from omr_app.gui.theme_manager import ThemeManager
from omr_app.gui.views.dashboard_view import DashboardView
from omr_app.gui.views.students_view import StudentsView
from omr_app.gui.views.exams_view import ExamsView
from omr_app.gui.views.templates_view import TemplatesView
from omr_app.gui.views.generator_view import GeneratorView
from omr_app.gui.views.correction_view import CorrectionView
from omr_app.gui.views.audit_view import AuditView
from omr_app.gui.views.reports_view import ReportsView


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestão e Correção Automática de Cartões OMR")
        self.setWindowIcon(get_app_icon())
        self.resize(1320, 840)
        self.setMinimumSize(1080, 700)

        self._init_ui()

    def _init_ui(self):
        main_central = QWidget()
        self.setCentralWidget(main_central)

        main_layout = QHBoxLayout(main_central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Navigation Menu
        sidebar = QFrame()
        sidebar.setObjectName("SidebarWidget")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(8)

        # Sidebar Logo Header (Cortex SVG Logo + Title)
        logo_container = QHBoxLayout()
        logo_container.setContentsMargins(4, 8, 4, 8)
        logo_container.setSpacing(10)

        svg_path = get_logo_svg_path()
        if svg_path:
            pixmap = QPixmap(svg_path)
            if not pixmap.isNull():
                lbl_logo_img = QLabel()
                lbl_logo_img.setPixmap(pixmap.scaled(38, 38, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                logo_container.addWidget(lbl_logo_img)

        lbl_logo_text = QLabel("LEITOR OMR")
        lbl_logo_text.setObjectName("SidebarTitle")
        lbl_logo_text.setStyleSheet("font-size: 18px; font-weight: bold; color: #00AEA7; padding: 0;")
        logo_container.addWidget(lbl_logo_text)
        logo_container.addStretch()

        sidebar_layout.addLayout(logo_container)

        lbl_sub = QLabel("Gestão & Correção de Cartões")
        lbl_sub.setObjectName("SidebarSubtitle")
        sidebar_layout.addWidget(lbl_sub)
        sidebar_layout.addSpacing(16)

        self.nav_buttons = []

        self.nav_items = [
            ("Dashboard", "dashboard", 0),
            ("Alunos & Turmas", "students", 1),
            ("Disciplinas & Provas", "exams", 2),
            ("Modelos de Cartão", "templates", 3),
            ("Gerador de Cartões", "generator", 4),
            ("Executar Correção", "correction", 5),
            ("Fila de Auditoria", "audit", 6),
            ("Relatórios & Logs", "reports", 7),
        ]

        for text, icon_name, index in self.nav_items:
            btn = QPushButton(f"  {text}")
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self._switch_view(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        lbl_ver = QLabel("v3.3.0 - PySide6 / OpenCV")
        lbl_ver.setStyleSheet("color: #64748B; font-size: 11px; text-align: center;")
        lbl_ver.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(lbl_ver)

        main_layout.addWidget(sidebar)

        # 2. Right Workspace Container
        workspace = QWidget()
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setObjectName("TopHeaderBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 8, 16, 8)

        self.lbl_header_title = QLabel("Dashboard")
        self.lbl_header_title.setObjectName("HeaderTitle")
        top_layout.addWidget(self.lbl_header_title)

        top_layout.addStretch()

        self.btn_theme_toggle = QPushButton(" Modo Escuro")
        self.btn_theme_toggle.setProperty("class", "btn-outline")
        self.btn_theme_toggle.clicked.connect(self._toggle_theme)
        top_layout.addWidget(self.btn_theme_toggle)

        workspace_layout.addWidget(top_bar)

        # View Stack
        self.stack = QStackedWidget()

        self.view_dashboard = DashboardView()
        self.view_students = StudentsView()
        self.view_exams = ExamsView()
        self.view_templates = TemplatesView()
        self.view_generator = GeneratorView()
        self.view_correction = CorrectionView()
        self.view_audit = AuditView()
        self.view_reports = ReportsView()

        self.stack.addWidget(self.view_dashboard)
        self.stack.addWidget(self.view_students)
        self.stack.addWidget(self.view_exams)
        self.stack.addWidget(self.view_templates)
        self.stack.addWidget(self.view_generator)
        self.stack.addWidget(self.view_correction)
        self.stack.addWidget(self.view_audit)
        self.stack.addWidget(self.view_reports)

        workspace_layout.addWidget(self.stack)
        main_layout.addWidget(workspace)

        self.view_dashboard.navigate_to.connect(self._switch_view)
        self.view_correction.batch_completed.connect(self._refresh_all_views)

        self._switch_view(0)

    def _switch_view(self, index: int):
        self.stack.setCurrentIndex(index)

        is_dark = ThemeManager.is_dark_mode()

        for i, btn in enumerate(self.nav_buttons):
            is_active = (i == index)
            btn.setChecked(is_active)
            _, icon_name, _ = self.nav_items[i]

            if is_active:
                icon_color = "#FFFFFF"
            else:
                icon_color = "#F8FAFC" if is_dark else "#1E293B"

            btn.setIcon(get_icon(icon_name, color=icon_color))

        titles = [
            "Dashboard", "Alunos & Turmas", "Disciplinas & Provas",
            "Modelos de Cartão-Resposta (Templates)", "Gerador de Cartões (PDF)",
            "Executar Correção Automática em Lote", "Fila de Auditoria Manual", "Relatórios & Logs"
        ]
        if index < len(titles):
            self.lbl_header_title.setText(titles[index])

        if is_dark:
            self.btn_theme_toggle.setText(" Modo Escuro")
            self.btn_theme_toggle.setIcon(get_icon("moon", color="#F8FAFC"))
        else:
            self.btn_theme_toggle.setText(" Modo Claro")
            self.btn_theme_toggle.setIcon(get_icon("sun", color="#1E293B"))

        if index == 0:
            self.view_dashboard.refresh_dashboard()
        elif index == 1:
            self.view_students.load_data()
        elif index == 2:
            self.view_exams.load_data()
        elif index == 3:
            self.view_templates.load_data()
        elif index == 4:
            self.view_generator.load_provas_combo()
        elif index == 5:
            self.view_correction.load_provas_combo()
            self.view_correction.refresh_historical_counters()
        elif index == 6:
            self.view_audit.load_pending_items()
        elif index == 7:
            self.view_reports.load_provas_combo()
            self.view_reports.load_logs_table()

    def _toggle_theme(self):
        app = QApplication.instance()
        is_dark = ThemeManager.toggle_theme(app)
        self._switch_view(self.stack.currentIndex())

    def _refresh_all_views(self):
        self.view_dashboard.refresh_dashboard()
        self.view_audit.load_pending_items()
        self.view_reports.load_provas_combo()
        self.view_reports.load_logs_table()
