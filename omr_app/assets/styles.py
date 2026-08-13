"""
Theme Manager and QSS Stylesheets for OMR Application.
Supports dynamic toggle between Light and Dark mode.
"""

# Color Palette Constants
COLOR_PRIMARY = "#00AEA7"      # Teal / Vibrant Cyan
COLOR_PRIMARY_HOVER = "#009690"
COLOR_SECONDARY = "#002970"    # Deep Navy
COLOR_SECONDARY_HOVER = "#001D50"

COLOR_SUCCESS = "#10B981"      # Green
COLOR_WARNING = "#F59E0B"      # Yellow / Amber
COLOR_DANGER = "#EF4444"       # Red

# QSS Templates
DARK_THEME_QSS = """
QMainWindow, QDialog {
    background-color: #0F172A;
    color: #F8FAFC;
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
    font-size: 13px;
}

QWidget {
    color: #F8FAFC;
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
}

/* Sidebar Navigation */
#SidebarWidget {
    background-color: #1E293B;
    border-right: 1px solid #334155;
}

#SidebarTitle {
    color: #00AEA7;
    font-size: 18px;
    font-weight: bold;
    padding: 15px 10px;
}

#SidebarSubtitle {
    color: #94A3B8;
    font-size: 11px;
}

QPushButton.nav-btn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
}

QPushButton.nav-btn:hover {
    background-color: #334155;
    color: #F8FAFC;
}

QPushButton.nav-btn:checked, QPushButton.nav-btn.active {
    background-color: #00AEA7;
    color: #FFFFFF;
    font-weight: bold;
}

/* Top Header Bar */
#TopHeaderBar {
    background-color: #1E293B;
    border-bottom: 1px solid #334155;
    padding: 8px 16px;
}

#HeaderTitle {
    font-size: 18px;
    font-weight: 600;
    color: #F8FAFC;
}

/* Cards & Frames */
.card-frame {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px;
}

.kpi-card {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px;
}

.kpi-title {
    color: #94A3B8;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
}

.kpi-value {
    color: #F8FAFC;
    font-size: 28px;
    font-weight: bold;
}

/* Input Controls */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    color: #F8FAFC;
    selection-background-color: #00AEA7;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
    border: 1px solid #00AEA7;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    gridline-color: #334155;
    color: #F8FAFC;
    selection-background-color: #00AEA7;
    selection-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #0F172A;
    color: #94A3B8;
    padding: 8px;
    font-weight: 600;
    border: none;
    border-bottom: 1px solid #334155;
}

/* Buttons */
QPushButton.btn-primary {
    background-color: #00AEA7;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 600;
}

QPushButton.btn-primary:hover {
    background-color: #009690;
}

QPushButton.btn-secondary {
    background-color: #002970;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 600;
}

QPushButton.btn-secondary:hover {
    background-color: #001D50;
}

QPushButton.btn-outline {
    background-color: transparent;
    color: #00AEA7;
    border: 1px solid #00AEA7;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton.btn-outline:hover {
    background-color: rgba(0, 174, 167, 0.15);
}

QPushButton.btn-danger {
    background-color: #EF4444;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton.btn-danger:hover {
    background-color: #DC2626;
}

/* Compact Table Action Buttons */
QPushButton.btn-sm {
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
    min-height: 26px;
}

/* Progress Bar */
QProgressBar {
    border: none;
    background-color: #334155;
    border-radius: 6px;
    text-align: center;
    color: #F8FAFC;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #00AEA7;
    border-radius: 6px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background-color: #0F172A;
    width: 8px;
    border-radius: 4px;
}

QScrollBar:handle:vertical {
    background-color: #334155;
    border-radius: 4px;
}

QScrollBar:handle:vertical:hover {
    background-color: #00AEA7;
}

QScrollBar:add-line:vertical, QScrollBar:sub-line:vertical {
    height: 0px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #334155;
    border-radius: 8px;
    background-color: #1E293B;
}

QTabBar::tab {
    background-color: #0F172A;
    color: #94A3B8;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1E293B;
    color: #00AEA7;
    font-weight: bold;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    color: #F8FAFC;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #00AEA7;
}
"""

LIGHT_THEME_QSS = """
QMainWindow, QDialog {
    background-color: #F8FAFC;
    color: #0F172A;
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
    font-size: 13px;
}

QWidget {
    color: #0F172A;
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
}

/* Sidebar Navigation */
#SidebarWidget {
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}

#SidebarTitle {
    color: #00AEA7;
    font-size: 18px;
    font-weight: bold;
    padding: 15px 10px;
}

#SidebarSubtitle {
    color: #64748B;
    font-size: 11px;
}

QPushButton.nav-btn {
    background-color: transparent;
    color: #475569;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
}

QPushButton.nav-btn:hover {
    background-color: #F1F5F9;
    color: #0F172A;
}

QPushButton.nav-btn:checked, QPushButton.nav-btn.active {
    background-color: #00AEA7;
    color: #FFFFFF;
    font-weight: bold;
}

/* Top Header Bar */
#TopHeaderBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 8px 16px;
}

#HeaderTitle {
    font-size: 18px;
    font-weight: 600;
    color: #0F172A;
}

/* Cards & Frames */
.card-frame {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px;
}

.kpi-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px;
}

.kpi-title {
    color: #64748B;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
}

.kpi-value {
    color: #0F172A;
    font-size: 28px;
    font-weight: bold;
}

/* Input Controls */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px 12px;
    color: #0F172A;
    selection-background-color: #00AEA7;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
    border: 1px solid #00AEA7;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: #F1F5F9;
    color: #0F172A;
    selection-background-color: #00AEA7;
    selection-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    padding: 8px;
    font-weight: 600;
    border: none;
    border-bottom: 1px solid #E2E8F0;
}

/* Buttons */
QPushButton.btn-primary {
    background-color: #00AEA7;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 600;
}

QPushButton.btn-primary:hover {
    background-color: #009690;
}

QPushButton.btn-secondary {
    background-color: #002970;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 600;
}

QPushButton.btn-secondary:hover {
    background-color: #001D50;
}

QPushButton.btn-outline {
    background-color: transparent;
    color: #00AEA7;
    border: 1px solid #00AEA7;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton.btn-outline:hover {
    background-color: rgba(0, 174, 167, 0.08);
}

QPushButton.btn-danger {
    background-color: #EF4444;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton.btn-danger:hover {
    background-color: #DC2626;
}

/* Compact Table Action Buttons */
QPushButton.btn-sm {
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
    min-height: 26px;
}

/* Progress Bar */
QProgressBar {
    border: none;
    background-color: #E2E8F0;
    border-radius: 6px;
    text-align: center;
    color: #0F172A;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #00AEA7;
    border-radius: 6px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background-color: #F8FAFC;
    width: 8px;
    border-radius: 4px;
}

QScrollBar:handle:vertical {
    background-color: #CBD5E1;
    border-radius: 4px;
}

QScrollBar:handle:vertical:hover {
    background-color: #00AEA7;
}

QScrollBar:add-line:vertical, QScrollBar:sub-line:vertical {
    height: 0px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background-color: #FFFFFF;
}

QTabBar::tab {
    background-color: #F8FAFC;
    color: #64748B;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #00AEA7;
    font-weight: bold;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    color: #0F172A;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #00AEA7;
}
"""
