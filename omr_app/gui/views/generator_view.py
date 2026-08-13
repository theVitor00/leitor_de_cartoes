"""
PDF Answer Sheet Generator View.
Selects Exam and Class students to emit PDF files.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QProgressBar, QTextEdit
)
from omr_app.database.models import Prova, Aluno, ProvaAluno
from omr_app.gui.threads import PDFGeneratorWorker


class GeneratorView(QWidget):

    def __init__(self):
        super().__init__()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Title
        lbl_title = QLabel("Gerador de Cartões-Resposta (PDF Vetorial)")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00AEA7;")
        layout.addWidget(lbl_title)

        # Selection Bar
        sel_layout = QHBoxLayout()
        lbl_p = QLabel("Selecione a Prova:")
        sel_layout.addWidget(lbl_p)

        self.combo_provas = QComboBox()
        self.combo_provas.currentIndexChanged.connect(self._on_prova_selected)
        sel_layout.addWidget(self.combo_provas, stretch=1)

        btn_gen = QPushButton("🖨️ Gerar PDF de Cartões")
        btn_gen.setProperty("class", "btn-primary")
        btn_gen.clicked.connect(self._generate_pdf)
        sel_layout.addWidget(btn_gen)

        layout.addLayout(sel_layout)

        # Table of Students included in exam
        lbl_st = QLabel("Alunos Nominalizados para esta Prova:")
        lbl_st.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_st)

        self.table_alunos = QTableWidget()
        self.table_alunos.setColumnCount(3)
        self.table_alunos.setHorizontalHeaderLabels(["ID", "Matrícula", "Nome do Aluno"])
        self.table_alunos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_alunos)

        # Progress bar & log output
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(120)
        layout.addWidget(self.txt_log)

        self.load_provas_combo()

    def load_provas_combo(self):
        self.combo_provas.clear()
        for p in Prova.select():
            self.combo_provas.addItem(f"{p.titulo} - Turma: {p.turma.nome if p.turma else 'N/A'}", p.id)

    def _on_prova_selected(self):
        p_id = self.combo_provas.currentData()
        if not p_id:
            return

        prova = Prova.get_or_none(Prova.id == p_id)
        if not prova:
            return

        self.table_alunos.setRowCount(0)
        participantes = ProvaAluno.select().where(ProvaAluno.prova == prova)

        for pa in participantes:
            aluno = pa.aluno
            row = self.table_alunos.rowCount()
            self.table_alunos.insertRow(row)

            self.table_alunos.setItem(row, 0, QTableWidgetItem(str(aluno.id)))
            self.table_alunos.setItem(row, 1, QTableWidgetItem(aluno.matricula))
            self.table_alunos.setItem(row, 2, QTableWidgetItem(aluno.nome))

    def _generate_pdf(self):
        p_id = self.combo_provas.currentData()
        if not p_id:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova.")
            return

        # Fetch student IDs
        aluno_ids = []
        for r in range(self.table_alunos.rowCount()):
            a_id = int(self.table_alunos.item(r, 0).text())
            aluno_ids.append(a_id)

        if not aluno_ids:
            QMessageBox.warning(self, "Aviso", "Nenhum aluno cadastrado nesta prova.")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Selecione o diretório para salvar os cartões PDF")
        if not output_dir:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.txt_log.clear()

        self.worker = PDFGeneratorWorker(p_id, aluno_ids, output_dir)
        self.worker.progress_changed.connect(lambda current, total: self.progress_bar.setValue(int((current / total) * 100)))
        self.worker.log_emitted.connect(self.txt_log.append)
        self.worker.finished.connect(self._on_pdf_finished)
        self.worker.start()

    def _on_pdf_finished(self, pdf_path: str):
        self.progress_bar.setVisible(False)
        if pdf_path and os.path.exists(pdf_path):
            QMessageBox.information(self, "Sucesso", f"Cartões-Resposta PDF gerados com sucesso:\n{pdf_path}")
