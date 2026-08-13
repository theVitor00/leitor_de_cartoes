"""
Dashboard View showing KPI cards, real-time metrics, quick actions, and recent activity.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from omr_app.database.models import Resultado, Prova, Aluno, Turma, LogLeitura


class DashboardView(QWidget):
    navigate_to = Signal(int)  # Signal to switch sidebar view

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header Title
        title_label = QLabel("Painel Principal (Dashboard)")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #00AEA7;")
        layout.addWidget(title_label)

        # KPI Cards Grid (4 Cards)
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(16)

        self.kpi_total_provas = self._create_kpi_card("Total Corrigidas (Histórico)", "0", "#00AEA7")
        self.kpi_sucessos = self._create_kpi_card("Sucessos (OK)", "0", "#10B981")
        self.kpi_revisoes = self._create_kpi_card("Pendentes de Revisão", "0", "#F59E0B")
        self.kpi_provas_ativas = self._create_kpi_card("Provas Cadastradas", "0", "#002970")

        kpi_grid.addWidget(self.kpi_total_provas["frame"], 0, 0)
        kpi_grid.addWidget(self.kpi_sucessos["frame"], 0, 1)
        kpi_grid.addWidget(self.kpi_revisoes["frame"], 0, 2)
        kpi_grid.addWidget(self.kpi_provas_ativas["frame"], 0, 3)

        layout.addLayout(kpi_grid)

        # Quick Actions Row
        actions_frame = QFrame()
        actions_frame.setProperty("class", "card-frame")
        actions_layout = QHBoxLayout(actions_frame)

        lbl_actions = QLabel("Ações Rápidas:")
        lbl_actions.setStyleSheet("font-weight: bold; font-size: 14px;")
        actions_layout.addWidget(lbl_actions)

        btn_corr = QPushButton("▶ Executar Nova Correção")
        btn_corr.setProperty("class", "btn-primary")
        btn_corr.clicked.connect(lambda: self.navigate_to.emit(4))  # Index 4 = Executar Correção
        actions_layout.addWidget(btn_corr)

        btn_audit = QPushButton("🔍 Fila de Auditoria")
        btn_audit.setProperty("class", "btn-secondary")
        btn_audit.clicked.connect(lambda: self.navigate_to.emit(5))  # Index 5 = Auditoria
        actions_layout.addWidget(btn_audit)

        btn_gen = QPushButton("🖨️ Gerar Cartões PDF")
        btn_gen.setProperty("class", "btn-outline")
        btn_gen.clicked.connect(lambda: self.navigate_to.emit(3))  # Index 3 = Gerador
        actions_layout.addWidget(btn_gen)

        actions_layout.addStretch()
        layout.addWidget(actions_frame)

        # Recent Activity Table
        lbl_table = QLabel("Últimas Correções Realizadas")
        lbl_table.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(lbl_table)

        self.table_recent = QTableWidget()
        self.table_recent.setColumnCount(6)
        self.table_recent.setHorizontalHeaderLabels([
            "Data/Hora", "Aluno", "Prova", "Nota", "Acertos", "Status"
        ])
        self.table_recent.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_recent)

        self.refresh_dashboard()

    def _create_kpi_card(self, title: str, initial_val: str, color_accent: str) -> dict:
        frame = QFrame()
        frame.setProperty("class", "kpi-card")

        vbox = QVBoxLayout(frame)
        lbl_t = QLabel(title)
        lbl_t.setProperty("class", "kpi-title")

        lbl_v = QLabel(initial_val)
        lbl_v.setProperty("class", "kpi-value")
        lbl_v.setStyleSheet(f"color: {color_accent};")

        vbox.addWidget(lbl_t)
        vbox.addWidget(lbl_v)
        return {"frame": frame, "value_label": lbl_v}

    def refresh_dashboard(self):
        """Reloads metrics from SQLite database."""
        try:
            total_corrigidas = Resultado.select().count()
            sucessos = Resultado.select().where(Resultado.status == "OK").count()
            revisoes = Resultado.select().where(Resultado.status == "REVISAO_NECESSARIA").count()
            total_provas = Prova.select().count()

            self.kpi_total_provas["value_label"].setText(str(total_corrigidas))
            self.kpi_sucessos["value_label"].setText(str(sucessos))
            self.kpi_revisoes["value_label"].setText(str(revisoes))
            self.kpi_provas_ativas["value_label"].setText(str(total_provas))

            # Populate recent table
            recentes = Resultado.select().order_by(Resultado.data_correcao.desc()).limit(8)
            self.table_recent.setRowCount(0)

            for r in recentes:
                row = self.table_recent.rowCount()
                self.table_recent.insertRow(row)

                dt_str = r.data_correcao.strftime("%d/%m/%Y %H:%M") if r.data_correcao else ""
                aluno_str = r.aluno.nome if r.aluno else "Desconhecido"
                prova_str = r.prova.titulo if r.prova else "Desconhecida"

                self.table_recent.setItem(row, 0, QTableWidgetItem(dt_str))
                self.table_recent.setItem(row, 1, QTableWidgetItem(aluno_str))
                self.table_recent.setItem(row, 2, QTableWidgetItem(prova_str))
                self.table_recent.setItem(row, 3, QTableWidgetItem(f"{r.nota_final:.2f}"))
                self.table_recent.setItem(row, 4, QTableWidgetItem(f"{r.acertos}/{r.total_questoes}"))

                st_item = QTableWidgetItem(r.status)
                if r.status == "OK":
                    st_item.setForeground(Qt.green)
                elif r.status == "REVISAO_NECESSARIA":
                    st_item.setForeground(Qt.yellow)
                else:
                    st_item.setForeground(Qt.red)
                self.table_recent.setItem(row, 5, st_item)
        except Exception:
            pass
