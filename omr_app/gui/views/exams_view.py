"""
Exams & Subjects View (CRUD for Materias, Provas and Interactive Answer Key Editor).
"""

import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
    QMessageBox, QDoubleSpinBox, QDateEdit, QSpinBox, QButtonGroup, QRadioButton,
    QGridLayout, QScrollArea
)
from PySide6.QtCore import QDate
from omr_app.database.models import Materia, Turma, Prova, ProvaAluno, Aluno


class ExamsView(QWidget):

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Title Bar
        top_layout = QHBoxLayout()
        lbl_title = QLabel("Disciplinas e Provas Cadastradas")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00AEA7;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        btn_add_mat = QPushButton("+ Nova Disciplina")
        btn_add_mat.setProperty("class", "btn-secondary")
        btn_add_mat.clicked.connect(self._open_add_materia_dialog)
        top_layout.addWidget(btn_add_mat)

        btn_add_prova = QPushButton("+ Criar Nova Prova")
        btn_add_prova.setProperty("class", "btn-primary")
        btn_add_prova.clicked.connect(self._open_add_prova_dialog)
        top_layout.addWidget(btn_add_prova)

        layout.addLayout(top_layout)

        # Table of Exams
        self.table_provas = QTableWidget()
        self.table_provas.setColumnCount(6)
        self.table_provas.setHorizontalHeaderLabels([
            "ID", "Título da Prova", "Disciplina", "Turma", "Valor Total", "Data Aplicação"
        ])
        self.table_provas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_provas)

        self.load_data()

    def load_data(self):
        self.table_provas.setRowCount(0)
        for p in Prova.select():
            row = self.table_provas.rowCount()
            self.table_provas.insertRow(row)

            self.table_provas.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.table_provas.setItem(row, 1, QTableWidgetItem(p.titulo))
            self.table_provas.setItem(row, 2, QTableWidgetItem(p.materia.nome if p.materia else "N/A"))
            self.table_provas.setItem(row, 3, QTableWidgetItem(p.turma.nome if p.turma else "N/A"))
            self.table_provas.setItem(row, 4, QTableWidgetItem(f"{p.valor_total:.2f}"))
            dt_str = p.data_aplicacao.strftime("%d/%m/%Y") if p.data_aplicacao else ""
            self.table_provas.setItem(row, 5, QTableWidgetItem(dt_str))

    def _open_add_materia_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Cadastrar Disciplina")
        dialog.setFixedWidth(350)
        form = QFormLayout(dialog)

        txt_nome = QLineEdit()
        txt_cod = QLineEdit()
        txt_cod.setPlaceholderText("Ex: MAT101")

        form.addRow("Nome da Disciplina:", txt_nome)
        form.addRow("Código da Disciplina:", txt_cod)

        btn = QPushButton("Salvar")
        btn.setProperty("class", "btn-primary")

        def save():
            n, c = txt_nome.text().strip(), txt_cod.text().strip()
            if not n or not c:
                QMessageBox.warning(dialog, "Aviso", "Preencha todos os campos.")
                return
            try:
                Materia.create(nome=n, codigo=c)
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Erro ao criar disciplina: {e}")

        btn.clicked.connect(save)
        form.addRow(btn)
        dialog.exec()

    def _open_add_prova_dialog(self):
        if Materia.select().count() == 0 or Turma.select().count() == 0:
            QMessageBox.warning(self, "Aviso", "Cadastre disciplinas e turmas antes de criar provas.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Criar Nova Prova e Configurar Gabarito")
        dialog.setMinimumWidth(550)
        dialog.setMinimumHeight(600)

        vbox = QVBoxLayout(dialog)
        form = QFormLayout()

        txt_titulo = QLineEdit()
        txt_titulo.setPlaceholderText("Ex: Simulado 1º Bimestre")

        combo_mat = QComboBox()
        for m in Materia.select():
            combo_mat.addItem(m.nome, m.id)

        combo_turma = QComboBox()
        for t in Turma.select():
            combo_turma.addItem(t.nome, t.id)

        spn_valor = QDoubleSpinBox()
        spn_valor.setRange(1.0, 100.0)
        spn_valor.setValue(10.0)

        dt_edit = QDateEdit(QDate.currentDate())
        dt_edit.setCalendarPopup(True)

        spn_num_q = QSpinBox()
        spn_num_q.setRange(1, 100)
        spn_num_q.setValue(10)

        form.addRow("Título da Prova:", txt_titulo)
        form.addRow("Disciplina:", combo_mat)
        form.addRow("Turma Target:", combo_turma)
        form.addRow("Valor Total da Nota:", spn_valor)
        form.addRow("Data Aplicação:", dt_edit)
        form.addRow("Quantidade de Questões:", spn_num_q)

        vbox.addLayout(form)

        # Gabarito Matrix Header
        lbl_gab = QLabel("Interactive Gabarito Editor (Selecione a resposta correta A-E):")
        lbl_gab.setStyleSheet("font-weight: bold; color: #00AEA7; margin-top: 10px;")
        vbox.addWidget(lbl_gab)

        # Scroll Area for Questions matrix
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container_widget = QWidget()
        matrix_grid = QGridLayout(container_widget)

        question_groups = {}  # {q_num: QButtonGroup}

        def build_gabarito_matrix():
            # Clear previous grid
            for i in reversed(range(matrix_grid.count())):
                w = matrix_grid.itemAt(i).widget()
                if w:
                    w.setParent(None)
            question_groups.clear()

            n_q = spn_num_q.value()
            for q in range(1, n_q + 1):
                lbl_q = QLabel(f"Q{q:02d}:")
                lbl_q.setStyleSheet("font-weight: bold;")
                matrix_grid.addWidget(lbl_q, q - 1, 0)

                bg = QButtonGroup(dialog)
                question_groups[q] = bg

                for opt_idx, letter in enumerate(["A", "B", "C", "D", "E"]):
                    rb = QRadioButton(letter)
                    if opt_idx == 0:
                        rb.setChecked(True)  # default select A
                    bg.addButton(rb, opt_idx)
                    matrix_grid.addWidget(rb, q - 1, opt_idx + 1)

        spn_num_q.valueChanged.connect(build_gabarito_matrix)
        build_gabarito_matrix()

        scroll.setWidget(container_widget)
        vbox.addWidget(scroll)

        btn_save = QPushButton("Salvar Prova com Gabarito")
        btn_save.setProperty("class", "btn-primary")

        def save_prova():
            tit = txt_titulo.text().strip()
            if not tit:
                QMessageBox.warning(dialog, "Aviso", "Preencha o título da prova.")
                return

            gabarito_dict = {}
            for q_num, bg in question_groups.items():
                checked_btn = bg.checkedButton()
                letter = checked_btn.text() if checked_btn else "A"
                gabarito_dict[str(q_num)] = letter

            m_id = combo_mat.currentData()
            t_id = combo_turma.currentData()
            dt_py = dt_edit.date().toPython()

            prova = Prova.create(
                titulo=tit,
                materia_id=m_id,
                turma_id=t_id,
                valor_total=spn_valor.value(),
                data_aplicacao=dt_py
            )
            prova.set_gabarito(gabarito_dict)
            prova.save()

            # Automatically populate ProvaAluno list for all students in target class
            alunos_class = Aluno.select().where(Aluno.turma_id == t_id)
            for al in alunos_class:
                ProvaAluno.get_or_create(prova=prova, aluno=al)

            dialog.accept()
            self.load_data()

        btn_save.clicked.connect(save_prova)
        vbox.addWidget(btn_save)
        dialog.exec()
