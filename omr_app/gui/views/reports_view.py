"""
Reports and Historical Analytics View.
Includes Matplotlib performance charts, KPI cards, Excel export, and Process Logs drawer.
Uses Font Awesome icons (qtawesome) without text emojis.
"""

import os
import json
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QFileDialog,
    QMessageBox, QFrame, QGridLayout, QTextEdit
)
from omr_app.assets.icons import get_icon
from omr_app.database.models import Prova, Resultado, LogLeitura, Turma
from omr_app.utils.excel_exporter import export_results_to_excel
from omr_app.logs.process_logger import ProcessLogger


class ReportsView(QWidget):

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        top_layout = QHBoxLayout()
        lbl_title = QLabel("Relatórios & Análise Histórica de Desempenho")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00AEA7;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        btn_excel = QPushButton(" Exportar para Excel (.xlsx)")
        btn_excel.setIcon(get_icon("excel"))
        btn_excel.setProperty("class", "btn-secondary")
        btn_excel.clicked.connect(self._export_excel)
        top_layout.addWidget(btn_excel)

        layout.addLayout(top_layout)

        tabs = QTabWidget()

        tab_analytics = QWidget()
        an_layout = QVBoxLayout(tab_analytics)

        filter_layout = QHBoxLayout()
        lbl_p = QLabel("Selecione a Prova:")
        filter_layout.addWidget(lbl_p)

        self.combo_provas = QComboBox()
        self.combo_provas.currentIndexChanged.connect(self._refresh_analytics)
        filter_layout.addWidget(self.combo_provas, stretch=1)

        an_layout.addLayout(filter_layout)

        kpi_grid = QGridLayout()

        self.card_total = self._create_kpi_card("Provas Corrigidas nesta Prova", "0", "#00AEA7")
        self.card_media = self._create_kpi_card("Média da Turma", "0.0", "#002970")
        self.card_max = self._create_kpi_card("Maior Nota", "0.0", "#10B981")
        self.card_min = self._create_kpi_card("Menor Nota", "0.0", "#EF4444")

        kpi_grid.addWidget(self.card_total["frame"], 0, 0)
        kpi_grid.addWidget(self.card_media["frame"], 0, 1)
        kpi_grid.addWidget(self.card_max["frame"], 0, 2)
        kpi_grid.addWidget(self.card_min["frame"], 0, 3)

        an_layout.addLayout(kpi_grid)

        charts_layout = QHBoxLayout()

        self.table_results = QTableWidget()
        self.table_results.setColumnCount(5)
        self.table_results.setHorizontalHeaderLabels(["Matrícula", "Aluno", "Acertos", "Nota", "Status"])
        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        charts_layout.addWidget(self.table_results, stretch=1)

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.fig.patch.set_facecolor('#1E293B')
        self.canvas = FigureCanvas(self.fig)
        charts_layout.addWidget(self.canvas, stretch=1)

        an_layout.addLayout(charts_layout)
        tabs.addTab(tab_analytics, "Análise de Desempenho & Itens")

        tab_logs = QWidget()
        log_layout = QVBoxLayout(tab_logs)

        lbl_l = QLabel("Registros Históricos de Processamento de Lotes (logs_leitura)")
        lbl_l.setStyleSheet("font-weight: bold; font-size: 14px;")
        log_layout.addWidget(lbl_l)

        self.table_logs = QTableWidget()
        self.table_logs.setColumnCount(6)
        self.table_logs.setHorizontalHeaderLabels([
            "ID Log", "Data/Hora", "Prova", "Total Folhas", "Sucessos", "Pendências"
        ])
        self.table_logs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_logs.itemSelectionChanged.connect(self._on_log_selected)
        log_layout.addWidget(self.table_logs, stretch=1)

        lbl_det = QLabel("Detalhes do Registro Selecionado:")
        log_layout.addWidget(lbl_det)

        self.txt_log_details = QTextEdit()
        self.txt_log_details.setReadOnly(True)
        self.txt_log_details.setStyleSheet(
            "background-color: #0F172A; color: #F8FAFC; font-family: 'Consolas', monospace;"
        )
        log_layout.addWidget(self.txt_log_details, stretch=1)

        tabs.addTab(tab_logs, "Logs de Processamento")
        layout.addWidget(tabs)

        self.load_provas_combo()
        self.load_logs_table()

    def _create_kpi_card(self, title: str, val: str, color_hex: str) -> dict:
        frame = QFrame()
        frame.setProperty("class", "kpi-card")

        vbox = QVBoxLayout(frame)
        lbl_t = QLabel(title)
        lbl_t.setProperty("class", "kpi-title")

        lbl_v = QLabel(val)
        lbl_v.setProperty("class", "kpi-value")
        lbl_v.setStyleSheet(f"color: {color_hex}; font-size: 24px;")

        vbox.addWidget(lbl_t)
        vbox.addWidget(lbl_v)
        return {"frame": frame, "val_lbl": lbl_v}

    def load_provas_combo(self):
        self.combo_provas.clear()
        for p in Prova.select():
            self.combo_provas.addItem(f"{p.titulo}", p.id)

    def _refresh_analytics(self):
        p_id = self.combo_provas.currentData()
        if not p_id:
            return

        prova = Prova.get_or_none(Prova.id == p_id)
        if not prova:
            return

        resultados = list(Resultado.select().where(Resultado.prova == prova))

        total_c = len(resultados)
        notas = [r.nota_final for r in resultados]

        media_n = sum(notas) / float(total_c) if total_c > 0 else 0.0
        max_n = max(notas) if total_c > 0 else 0.0
        min_n = min(notas) if total_c > 0 else 0.0

        self.card_total["val_lbl"].setText(str(total_c))
        self.card_media["val_lbl"].setText(f"{media_n:.2f}")
        self.card_max["val_lbl"].setText(f"{max_n:.2f}")
        self.card_min["val_lbl"].setText(f"{min_n:.2f}")

        self.table_results.setRowCount(0)
        for r in resultados:
            row = self.table_results.rowCount()
            self.table_results.insertRow(row)

            aluno_nome = r.aluno.nome if r.aluno else "N/A"
            aluno_mat = r.aluno.matricula if r.aluno else "N/A"

            self.table_results.setItem(row, 0, QTableWidgetItem(aluno_mat))
            self.table_results.setItem(row, 1, QTableWidgetItem(aluno_nome))
            self.table_results.setItem(row, 2, QTableWidgetItem(f"{r.acertos}/{r.total_questoes}"))
            self.table_results.setItem(row, 3, QTableWidgetItem(f"{r.nota_final:.2f}"))
            self.table_results.setItem(row, 4, QTableWidgetItem(r.status))

        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#0F172A')

        if notas:
            ax.hist(notas, bins=5, color='#00AEA7', edgecolor='#002970', alpha=0.85)
            ax.set_title("Distribuição das Notas dos Alunos", color='#F8FAFC', fontsize=12)
            ax.set_xlabel("Nota Final", color='#94A3B8')
            ax.set_ylabel("Quantidade de Alunos", color='#94A3B8')
            ax.tick_params(colors='#94A3B8')
            for spine in ax.spines.values():
                spine.set_color('#334155')

        self.fig.tight_layout()
        self.canvas.draw()

    def load_logs_table(self):
        query = LogLeitura.select().order_by(LogLeitura.data_hora.desc())
        self.table_logs.setRowCount(0)

        for l in query:
            row = self.table_logs.rowCount()
            self.table_logs.insertRow(row)

            p_nome = l.prova.titulo if l.prova else "N/A"
            dt_str = l.data_hora.strftime("%d/%m/%Y %H:%M:%S")

            self.table_logs.setItem(row, 0, QTableWidgetItem(str(l.id)))
            self.table_logs.setItem(row, 1, QTableWidgetItem(dt_str))
            self.table_logs.setItem(row, 2, QTableWidgetItem(p_nome))
            self.table_logs.setItem(row, 3, QTableWidgetItem(str(l.quantidade_provas_corrigidas)))
            self.table_logs.setItem(row, 4, QTableWidgetItem(str(l.sucessos)))
            self.table_logs.setItem(row, 5, QTableWidgetItem(str(l.pendencias_revisao)))

    def _on_log_selected(self):
        selected = self.table_logs.selectedItems()
        if not selected:
            return

        log_id = int(self.table_logs.item(selected[0].row(), 0).text())
        log_entry = LogLeitura.get_or_none(LogLeitura.id == log_id)
        if not log_entry:
            return

        try:
            detalhes = json.loads(log_entry.detalhes_json)
            lines = [f"=== DETALHES DO LOG DE PROCESSAMENTO #{log_entry.id} ==="]
            lines.append(f"Data: {log_entry.data_hora.strftime('%d/%m/%Y %H:%M:%S')}")
            lines.append(f"Total Folhas Corrigidas: {log_entry.quantidade_provas_corrigidas}\n")

            for item in detalhes:
                lines.append(
                    f"• Status: {item.get('status')} | Aluno ID: {item.get('aluno_id')} | "
                    f"Nota: {item.get('nota_final')} | Msg: {item.get('mensagem')}"
                )
            self.txt_log_details.setText("\n".join(lines))
        except Exception as e:
            self.txt_log_details.setText(f"Erro ao carregar detalhes: {e}")

    def _export_excel(self):
        p_id = self.combo_provas.currentData()
        if not p_id:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova para exportação.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório Excel", "Relatorio_Provas.xlsx", "Excel Files (*.xlsx)"
        )
        if filepath:
            try:
                export_results_to_excel(p_id, filepath)
                QMessageBox.information(self, "Sucesso", f"Relatório Excel exportado com sucesso:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao exportar Excel: {e}")
