"""
Manual Audit Queue (Fila de Auditoria) with Split View.
Displays cropped scan image with OpenCV overlays on left panel,
and interactive decision form on right panel.
"""

import os
import cv2
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QFormLayout,
    QComboBox, QLineEdit, QMessageBox, QScrollArea, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from omr_app.database.models import Resultado, Aluno, Prova
from omr_app.utils.image_helpers import cv2_to_qpixmap


class AuditView(QWidget):

    def __init__(self):
        super().__init__()
        self.current_resultado = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Title
        top_layout = QHBoxLayout()
        lbl_title = QLabel("Fila de Auditoria Manual (Revisão de Falhas & Rasuras)")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #F59E0B;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        btn_refresh = QPushButton("🔄 Atualizar Fila")
        btn_refresh.setProperty("class", "btn-secondary")
        btn_refresh.clicked.connect(self.load_pending_items)
        top_layout.addWidget(btn_refresh)

        layout.addLayout(top_layout)

        # Splitter Layout (Main Splitter)
        splitter = QSplitter(Qt.Horizontal)

        # Left Panel: Table of Pending Scans & Image Viewer
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        lbl_queue = QLabel("Folhas com Pendências de Leitura:")
        lbl_queue.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(lbl_queue)

        self.table_pending = QTableWidget()
        self.table_pending.setColumnCount(4)
        self.table_pending.setHorizontalHeaderLabels(["ID", "Aluno ID", "Prova ID", "Status"])
        self.table_pending.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_pending.itemSelectionChanged.connect(self._on_item_selected)
        left_layout.addWidget(self.table_pending, stretch=1)

        # Image Viewer Frame
        lbl_img_title = QLabel("Visualização da Folha Escaneada (OpenCV Overlays):")
        lbl_img_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(lbl_img_title)

        self.image_label = QLabel("Selecione um item da fila para visualizar a imagem.")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #0F172A; border: 1px solid #334155; border-radius: 8px;")

        scroll_img = QScrollArea()
        scroll_img.setWidgetResizable(True)
        scroll_img.setWidget(self.image_label)
        left_layout.addWidget(scroll_img, stretch=2)

        splitter.addWidget(left_widget)

        # Right Panel: Interactive Operator Form
        right_frame = QFrame()
        right_frame.setProperty("class", "card-frame")
        right_layout = QVBoxLayout(right_frame)

        lbl_form_title = QLabel("Formulário de Decisão do Operador")
        lbl_form_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00AEA7;")
        right_layout.addWidget(lbl_form_title)

        form_layout = QFormLayout()

        self.combo_aluno = QComboBox()
        self.combo_prova = QComboBox()

        self.txt_nota = QLineEdit()
        self.txt_acertos = QLineEdit()
        self.txt_respostas_json = QLineEdit()
        self.lbl_mensagem = QLabel("-")
        self.lbl_mensagem.setStyleSheet("color: #F59E0B; font-weight: bold;")
        self.lbl_mensagem.setWordWrap(True)

        form_layout.addRow("Aluno Vinculado:", self.combo_aluno)
        form_layout.addRow("Prova:", self.combo_prova)
        form_layout.addRow("Diagnóstico da Leitura:", self.lbl_mensagem)
        form_layout.addRow("Nota Final:", self.txt_nota)
        form_layout.addRow("Acertos:", self.txt_acertos)
        form_layout.addRow("Respostas (JSON):", self.txt_respostas_json)

        right_layout.addLayout(form_layout)

        # Decision Action Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_confirm = QPushButton("✅ Confirmar / Ajustar Nota")
        self.btn_confirm.setProperty("class", "btn-primary")
        self.btn_confirm.clicked.connect(self._confirm_override)
        btn_layout.addWidget(self.btn_confirm)

        self.btn_anular = QPushButton("🚫 Anular Prova / Descartar")
        self.btn_anular.setProperty("class", "btn-danger")
        self.btn_anular.clicked.connect(self._anular_prova)
        btn_layout.addWidget(self.btn_anular)

        right_layout.addLayout(btn_layout)
        right_layout.addStretch()

        splitter.addWidget(right_frame)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter)

        self.load_pending_items()

    def load_pending_items(self):
        query = Resultado.select().where(Resultado.status != "OK")

        self.table_pending.setRowCount(0)
        for r in query:
            row = self.table_pending.rowCount()
            self.table_pending.insertRow(row)

            self.table_pending.setItem(row, 0, QTableWidgetItem(str(r.id)))
            self.table_pending.setItem(row, 1, QTableWidgetItem(str(r.aluno.id if r.aluno else "N/A")))
            self.table_pending.setItem(row, 2, QTableWidgetItem(str(r.prova.id if r.prova else "N/A")))

            st_item = QTableWidgetItem(r.status)
            st_item.setForeground(Qt.yellow if r.status == "REVISAO_NECESSARIA" else Qt.red)
            self.table_pending.setItem(row, 3, st_item)

        # Load Aluno & Prova combo options
        self.combo_aluno.clear()
        for a in Aluno.select():
            self.combo_aluno.addItem(f"{a.nome} ({a.matricula})", a.id)

        self.combo_prova.clear()
        for p in Prova.select():
            self.combo_prova.addItem(f"{p.titulo}", p.id)

    def _on_item_selected(self):
        selected_rows = self.table_pending.selectedItems()
        if not selected_rows:
            return

        res_id = int(self.table_pending.item(selected_rows[0].row(), 0).text())
        r = Resultado.get_or_none(Resultado.id == res_id)
        if not r:
            return

        self.current_resultado = r

        # Set values on form
        if r.aluno:
            idx = self.combo_aluno.findData(r.aluno.id)
            if idx >= 0:
                self.combo_aluno.setCurrentIndex(idx)

        if r.prova:
            idx = self.combo_prova.findData(r.prova.id)
            if idx >= 0:
                self.combo_prova.setCurrentIndex(idx)

        self.txt_nota.setText(str(r.nota_final))
        self.txt_acertos.setText(str(r.acertos))
        self.txt_respostas_json.setText(r.respostas_marcadas_json)

        # Display image scan with OpenCV overlay
        if r.caminho_imagem_scan and os.path.exists(r.caminho_imagem_scan):
            pixmap = QPixmap(r.caminho_imagem_scan)
            scaled = pixmap.scaled(550, 750, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setText("Imagem de scan não localizada no disco.")

    def _confirm_override(self):
        if not self.current_resultado:
            QMessageBox.warning(self, "Aviso", "Selecione um item da fila.")
            return

        try:
            a_id = self.combo_aluno.currentData()
            p_id = self.combo_prova.currentData()
            nota = float(self.txt_nota.text().strip())
            acertos = int(self.txt_acertos.text().strip())
            resp_json = self.txt_respostas_json.text().strip()

            self.current_resultado.aluno = Aluno.get_by_id(a_id)
            self.current_resultado.prova = Prova.get_by_id(p_id)
            self.current_resultado.nota_final = nota
            self.current_resultado.acertos = acertos
            self.current_resultado.respostas_marcadas_json = resp_json
            self.current_resultado.status = "OK"  # Flag as resolved
            self.current_resultado.save()

            QMessageBox.information(self, "Sucesso", "Revisão confirmada com sucesso!")
            self.load_pending_items()
            self.image_label.clear()
            self.image_label.setText("Selecione um item da fila.")
            self.current_resultado = None
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar alteração: {e}")

    def _anular_prova(self):
        if not self.current_resultado:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Anulação",
            "Deseja realmente anular esta prova (definir nota como 0.0)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.current_resultado.nota_final = 0.0
            self.current_resultado.acertos = 0
            self.current_resultado.status = "ERRO_LEITURA"
            self.current_resultado.save()

            QMessageBox.information(self, "Anulada", "Prova anulada com sucesso.")
            self.load_pending_items()
            self.image_label.clear()
            self.image_label.setText("Selecione um item da fila.")
            self.current_resultado = None
