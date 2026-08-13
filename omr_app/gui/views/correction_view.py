"""
Batch Correction Execution View with Real-time Counters, Progress Bar,
Dynamic OMR Sensitivity QSlider, and Live Log Console.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QFileDialog, QProgressBar, QTextEdit, QFrame, QGridLayout, QMessageBox,
    QSlider
)
from PySide6.QtCore import Qt, Signal
from omr_app.database.models import Prova, Resultado
from omr_app.gui.threads import CorrectionWorker


class CorrectionView(QWidget):
    batch_completed = Signal()

    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Title
        lbl_title = QLabel("Executar Correção Automática em Lote")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00AEA7;")
        layout.addWidget(lbl_title)

        # Target Exam Selector & File Upload Row
        top_box = QFrame()
        top_box.setProperty("class", "card-frame")
        top_layout = QHBoxLayout(top_box)

        lbl_p = QLabel("Prova Alvo (opcional se auto-detect via QR Code):")
        lbl_p.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(lbl_p)

        self.combo_provas = QComboBox()
        top_layout.addWidget(self.combo_provas, stretch=1)

        btn_select = QPushButton("📁 Selecionar Imagens / PDFs")
        btn_select.setProperty("class", "btn-secondary")
        btn_select.clicked.connect(self._select_files)
        top_layout.addWidget(btn_select)

        self.btn_run = QPushButton("▶ Iniciar Correção")
        self.btn_run.setProperty("class", "btn-primary")
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self._start_correction)
        top_layout.addWidget(self.btn_run)

        layout.addWidget(top_box)

        self.lbl_selected_info = QLabel("Nenhum arquivo selecionado.")
        self.lbl_selected_info.setStyleSheet("color: #94A3B8; font-style: italic;")
        layout.addWidget(self.lbl_selected_info)

        # OMR SENSITIVITY QSLIDER CONTROL BOX
        sens_box = QFrame()
        sens_box.setProperty("class", "card-frame")
        sens_layout = QHBoxLayout(sens_box)

        self.lbl_sens_title = QLabel("🎚️ Sensibilidade OMR (Threshold de Preenchimento): 45%")
        self.lbl_sens_title.setStyleSheet("font-weight: bold; color: #00AEA7;")
        sens_layout.addWidget(self.lbl_sens_title)

        self.slider_sens = QSlider(Qt.Horizontal)
        self.slider_sens.setRange(10, 90)
        self.slider_sens.setValue(45)
        self.slider_sens.setTickInterval(5)
        self.slider_sens.setTickPosition(QSlider.TicksBelow)
        self.slider_sens.valueChanged.connect(self._on_sens_changed)
        sens_layout.addWidget(self.slider_sens, stretch=1)

        lbl_low = QLabel("10% (Mais Sensível)")
        lbl_low.setStyleSheet("font-size: 11px; color: #94A3B8;")
        lbl_high = QLabel("90% (Mais Rigoroso)")
        lbl_high.setStyleSheet("font-size: 11px; color: #94A3B8;")
        sens_layout.addWidget(lbl_low)
        sens_layout.addWidget(lbl_high)

        layout.addWidget(sens_box)

        # REAL-TIME COUNTERS GRID (5 KPI Cards)
        counters_grid = QGridLayout()
        counters_grid.setSpacing(12)

        self.card_lote = self._create_counter_card("Provas Corrigidas no Lote Atual", "0 de 0", "#00AEA7")
        self.card_historico = self._create_counter_card("Total Histórico no Sistema", "0", "#002970")
        self.card_sucesso = self._create_counter_card("Sucessos (OK)", "0", "#10B981")
        self.card_revisao = self._create_counter_card("Pendentes de Revisão", "0", "#F59E0B")
        self.card_erro = self._create_counter_card("Erros de Leitura", "0", "#EF4444")

        counters_grid.addWidget(self.card_lote["frame"], 0, 0)
        counters_grid.addWidget(self.card_historico["frame"], 0, 1)
        counters_grid.addWidget(self.card_sucesso["frame"], 0, 2)
        counters_grid.addWidget(self.card_revisao["frame"], 0, 3)
        counters_grid.addWidget(self.card_erro["frame"], 0, 4)

        layout.addLayout(counters_grid)

        # Fluid Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(24)
        layout.addWidget(self.progress_bar)

        # Live Log Console
        lbl_console = QLabel("Console de Execução ao Vivo:")
        lbl_console.setStyleSheet("font-weight: bold; margin-top: 5px;")
        layout.addWidget(lbl_console)

        self.txt_console = QTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setStyleSheet(
            "background-color: #0F172A; color: #10B981; font-family: 'Consolas', 'Courier New', monospace;"
        )
        layout.addWidget(self.txt_console)

        self.load_provas_combo()
        self.refresh_historical_counters()

    def _on_sens_changed(self, val: int):
        self.lbl_sens_title.setText(f"🎚️ Sensibilidade OMR (Threshold de Preenchimento): {val}%")

    def load_provas_combo(self):
        self.combo_provas.clear()
        self.combo_provas.addItem("Auto-detectar pelo QR Code de cada folha", None)
        for p in Prova.select():
            self.combo_provas.addItem(f"#{p.id} - {p.titulo}", p.id)

    def refresh_historical_counters(self):
        try:
            total_hist = Resultado.select().count()
            self.card_historico["val_lbl"].setText(str(total_hist))
        except Exception:
            pass

    def _create_counter_card(self, title: str, val: str, color_hex: str) -> dict:
        frame = QFrame()
        frame.setProperty("class", "kpi-card")

        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(10, 10, 10, 10)

        lbl_t = QLabel(title)
        lbl_t.setProperty("class", "kpi-title")

        lbl_v = QLabel(val)
        lbl_v.setProperty("class", "kpi-value")
        lbl_v.setStyleSheet(f"color: {color_hex}; font-size: 20px;")

        vbox.addWidget(lbl_t)
        vbox.addWidget(lbl_v)

        return {"frame": frame, "val_lbl": lbl_v}

    def _select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Cartões Escaneados",
            "",
            "Arquivos de Imagem / PDF (*.jpg *.jpeg *.png *.tif *.tiff *.pdf)"
        )
        if files:
            self.selected_files = files
            self.lbl_selected_info.setText(f"📁 {len(files)} arquivo(s) selecionado(s) para processamento.")
            self.btn_run.setEnabled(True)
        else:
            self.selected_files = []
            self.lbl_selected_info.setText("Nenhum arquivo selecionado.")
            self.btn_run.setEnabled(False)

    def _start_correction(self):
        if not self.selected_files:
            return

        self.btn_run.setEnabled(False)
        self.txt_console.clear()
        self.progress_bar.setValue(0)

        target_p_id = self.combo_provas.currentData()
        sens_pct = float(self.slider_sens.value())

        self.card_lote["val_lbl"].setText(f"0 de {len(self.selected_files)}")
        self.card_sucesso["val_lbl"].setText("0")
        self.card_revisao["val_lbl"].setText("0")
        self.card_erro["val_lbl"].setText("0")

        self.lote_sucessos = 0
        self.lote_revisoes = 0
        self.lote_erros = 0

        self.worker = CorrectionWorker(
            self.selected_files, target_prova_id=target_p_id, sensitivity_pct=sens_pct
        )
        self.worker.progress_changed.connect(self._on_progress)
        self.worker.sheet_processed.connect(self._on_sheet_processed)
        self.worker.log_emitted.connect(self.txt_console.append)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, current: int, total: int):
        pct = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.card_lote["val_lbl"].setText(f"{current} de {total}")

    def _on_sheet_processed(self, result: dict):
        st = result.get('status')
        if st == "OK":
            self.lote_sucessos += 1
            self.card_sucesso["val_lbl"].setText(str(self.lote_sucessos))
        elif st == "REVISAO_NECESSARIA":
            self.lote_revisoes += 1
            self.card_revisao["val_lbl"].setText(str(self.lote_revisoes))
        else:
            self.lote_erros += 1
            self.card_erro["val_lbl"].setText(str(self.lote_erros))

    def _on_finished(self, summary: dict):
        self.btn_run.setEnabled(True)
        self.refresh_historical_counters()
        self.batch_completed.emit()
        QMessageBox.information(
            self,
            "Processamento Concluído",
            f"Lote de {summary.get('total')} folhas concluído com sucesso!\n"
            f"🟢 Sucessos: {summary.get('sucessos')}\n"
            f"🟡 Pendentes de Revisão: {summary.get('revisoes')}\n"
            f"🔴 Erros: {summary.get('erros')}"
        )
