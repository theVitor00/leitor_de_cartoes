"""
Students & Classes View (CRUD for Turmas & Alunos).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
    QMessageBox, QSpinBox
)
from omr_app.database.models import Turma, Aluno


class StudentsView(QWidget):

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title Bar & Action Buttons
        top_layout = QHBoxLayout()
        lbl_title = QLabel("Gestão de Alunos e Turmas")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00AEA7;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        btn_add_turma = QPushButton("+ Nova Turma")
        btn_add_turma.setProperty("class", "btn-secondary")
        btn_add_turma.clicked.connect(self._open_add_turma_dialog)
        top_layout.addWidget(btn_add_turma)

        btn_add_aluno = QPushButton("+ Novo Aluno")
        btn_add_aluno.setProperty("class", "btn-primary")
        btn_add_aluno.clicked.connect(self._open_add_aluno_dialog)
        top_layout.addWidget(btn_add_aluno)

        layout.addLayout(top_layout)

        # Filter Bar
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nome ou matrícula...")
        self.search_input.textChanged.connect(self.load_data)
        filter_layout.addWidget(self.search_input)

        self.combo_turma_filter = QComboBox()
        self.combo_turma_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.combo_turma_filter)

        layout.addLayout(filter_layout)

        # Students Table
        self.table_alunos = QTableWidget()
        self.table_alunos.setColumnCount(4)
        self.table_alunos.setHorizontalHeaderLabels([
            "ID", "Matrícula", "Nome do Aluno", "Turma"
        ])
        self.table_alunos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_alunos)

        self.load_turmas_combo()
        self.load_data()

    def load_turmas_combo(self):
        self.combo_turma_filter.clear()
        self.combo_turma_filter.addItem("Todas as Turmas", None)
        for t in Turma.select():
            self.combo_turma_filter.addItem(f"{t.nome} ({t.ano_letivo})", t.id)

    def load_data(self):
        query = Aluno.select()

        # Apply search text
        text = self.search_input.text().strip()
        if text:
            query = query.where((Aluno.nome.contains(text)) | (Aluno.matricula.contains(text)))

        # Apply turma filter
        t_id = self.combo_turma_filter.currentData()
        if t_id:
            query = query.where(Aluno.turma == t_id)

        self.table_alunos.setRowCount(0)
        for a in query:
            row = self.table_alunos.rowCount()
            self.table_alunos.insertRow(row)

            self.table_alunos.setItem(row, 0, QTableWidgetItem(str(a.id)))
            self.table_alunos.setItem(row, 1, QTableWidgetItem(a.matricula))
            self.table_alunos.setItem(row, 2, QTableWidgetItem(a.nome))
            self.table_alunos.setItem(row, 3, QTableWidgetItem(a.turma.nome if a.turma else "N/A"))

    def _open_add_turma_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Cadastrar Nova Turma")
        dialog.setFixedWidth(350)
        form = QFormLayout(dialog)

        txt_nome = QLineEdit()
        txt_nome.setPlaceholderText("Ex: 3º Ano A")
        spn_ano = QSpinBox()
        spn_ano.setRange(2020, 2035)
        spn_ano.setValue(2026)

        form.addRow("Nome da Turma:", txt_nome)
        form.addRow("Ano Letivo:", spn_ano)

        btn_save = QPushButton("Salvar Turma")
        btn_save.setProperty("class", "btn-primary")

        def save():
            if not txt_nome.text().strip():
                QMessageBox.warning(dialog, "Aviso", "Preencha o nome da turma.")
                return
            Turma.create(nome=txt_nome.text().strip(), ano_letivo=spn_ano.value())
            dialog.accept()
            self.load_turmas_combo()

        btn_save.clicked.connect(save)
        form.addRow(btn_save)
        dialog.exec()

    def _open_add_aluno_dialog(self):
        if Turma.select().count() == 0:
            QMessageBox.warning(self, "Aviso", "Cadastre pelo menos uma turma antes de adicionar alunos.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Cadastrar Novo Aluno")
        dialog.setFixedWidth(400)
        form = QFormLayout(dialog)

        txt_mat = QLineEdit()
        txt_mat.setPlaceholderText("Ex: 2026009")
        txt_nome = QLineEdit()
        txt_nome.setPlaceholderText("Nome completo do aluno")

        combo_t = QComboBox()
        for t in Turma.select():
            combo_t.addItem(t.nome, t.id)

        form.addRow("Matrícula:", txt_mat)
        form.addRow("Nome do Aluno:", txt_nome)
        form.addRow("Turma:", combo_t)

        btn_save = QPushButton("Salvar Aluno")
        btn_save.setProperty("class", "btn-primary")

        def save():
            mat = txt_mat.text().strip()
            nome = txt_nome.text().strip()
            turma_id = combo_t.currentData()

            if not mat or not nome:
                QMessageBox.warning(dialog, "Aviso", "Preencha matrícula e nome.")
                return

            try:
                Aluno.create(matricula=mat, nome=nome, turma=turma_id)
                dialog.accept()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Matrícula já existente ou erro ao salvar: {e}")

        btn_save.clicked.connect(save)
        form.addRow(btn_save)
        dialog.exec()
