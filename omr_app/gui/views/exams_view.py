"""
Exams & Subjects View (CRUD for Materias, Provas and Interactive Answer Key Editor).
Uses high-contrast Font Awesome icons.
"""

import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
    QMessageBox, QDoubleSpinBox, QDateEdit, QSpinBox, QButtonGroup, QRadioButton,
    QGridLayout, QScrollArea
)
from PySide6.QtCore import QDate
from omr_app.assets.icons import get_icon
from omr_app.database.models import Materia, Turma, Prova, ProvaAluno, Aluno, Template


class ExamsView(QWidget):

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        top_layout = QHBoxLayout()
        lbl_title = QLabel("Disciplinas e Provas Cadastradas")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00AEA7;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        btn_add_mat = QPushButton(" Nova Disciplina")
        btn_add_mat.setIcon(get_icon("plus", color="white"))
        btn_add_mat.setProperty("class", "btn-secondary")
        btn_add_mat.clicked.connect(self._open_add_materia_dialog)
        top_layout.addWidget(btn_add_mat)

        btn_add_prova = QPushButton(" Criar Nova Prova")
        btn_add_prova.setIcon(get_icon("plus", color="white"))
        btn_add_prova.setProperty("class", "btn-primary")
        btn_add_prova.clicked.connect(self._open_add_prova_dialog)
        top_layout.addWidget(btn_add_prova)

        layout.addLayout(top_layout)

        self.table_provas = QTableWidget()
        self.table_provas.setColumnCount(7)
        self.table_provas.setHorizontalHeaderLabels([
            "ID", "Título da Prova", "Disciplina", "Turma", "Modelo / Template", "Valor Total", "Data Aplicação"
        ])
        self.table_provas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_provas)

        self.load_data()

    def load_data(self):
        self.table_provas.setRowCount(0)
        for p in Prova.select():
            row = self.table_provas.rowCount()
            self.table_provas.insertRow(row)

            tmpl_nome = p.template.nome if p.template else "Padrão"

            self.table_provas.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.table_provas.setItem(row, 1, QTableWidgetItem(p.titulo))
            self.table_provas.setItem(row, 2, QTableWidgetItem(p.materia.nome if p.materia else "N/A"))
            self.table_provas.setItem(row, 3, QTableWidgetItem(p.turma.nome if p.turma else "N/A"))
            self.table_provas.setItem(row, 4, QTableWidgetItem(tmpl_nome))
            self.table_provas.setItem(row, 5, QTableWidgetItem(f"{p.valor_total:.2f}"))
            dt_str = p.data_aplicacao.strftime("%d/%m/%Y") if p.data_aplicacao else ""
            self.table_provas.setItem(row, 6, QTableWidgetItem(dt_str))

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
        btn.setIcon(get_icon("check", color="white"))
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

        if Template.select().count() == 0:
            QMessageBox.warning(self, "Aviso", "Cadastre pelo menos um Modelo de Cartão (Template) antes de criar provas.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Criar Nova Prova e Configurar Gabarito")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(650)

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

        combo_template = QComboBox()
        for tmpl in Template.select():
            combo_template.addItem(
                f"{tmpl.nome} ({tmpl.quantidade_questoes}Q - {tmpl.alternativas_por_questao} Alt)", tmpl.id
            )

        spn_valor = QDoubleSpinBox()
        spn_valor.setRange(1.0, 100.0)
        spn_valor.setValue(10.0)

        dt_edit = QDateEdit(QDate.currentDate())
        dt_edit.setCalendarPopup(True)

        form.addRow("Título da Prova:", txt_titulo)
        form.addRow("Disciplina:", combo_mat)
        form.addRow("Turma Target:", combo_turma)
        form.addRow("Modelo de Cartão (Template):", combo_template)
        form.addRow("Valor Total da Nota:", spn_valor)
        form.addRow("Data Aplicação:", dt_edit)

        vbox.addLayout(form)

        lbl_gab = QLabel("Editor do Gabarito Oficial (Selecione a resposta correta para cada questão):")
        lbl_gab.setStyleSheet("font-weight: bold; color: #00AEA7; margin-top: 10px;")
        vbox.addWidget(lbl_gab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container_widget = QWidget()
        matrix_grid = QGridLayout(container_widget)

        question_groups = {}

        def build_gabarito_matrix():
            for i in reversed(range(matrix_grid.count())):
                w = matrix_grid.itemAt(i).widget()
                if w:
                    w.setParent(None)
            question_groups.clear()

            tmpl_id = combo_template.currentData()
            tmpl = Template.get_or_none(Template.id == tmpl_id)
            if not tmpl:
                return

            n_q = tmpl.quantidade_questoes
            n_opts = tmpl.alternativas_por_questao
            letters = ["A", "B", "C", "D", "E"][:n_opts]

            for q in range(1, n_q + 1):
                lbl_q = QLabel(f"Q{q:02d}:")
                lbl_q.setStyleSheet("font-weight: bold;")
                matrix_grid.addWidget(lbl_q, q - 1, 0)

                bg = QButtonGroup(dialog)
                question_groups[q] = bg

                for opt_idx, letter in enumerate(letters):
                    rb = QRadioButton(letter)
                    if opt_idx == 0:
                        rb.setChecked(True)
                    bg.addButton(rb, opt_idx)
                    matrix_grid.addWidget(rb, q - 1, opt_idx + 1)

        combo_template.currentIndexChanged.connect(build_gabarito_matrix)
        build_gabarito_matrix()

        scroll.setWidget(container_widget)
        vbox.addWidget(scroll)

        btn_save = QPushButton("Salvar Prova com Gabarito")
        btn_save.setIcon(get_icon("check", color="white"))
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
            tmpl_id = combo_template.currentData()
            dt_py = dt_edit.date().toPython()

            prova = Prova.create(
                titulo=tit,
                materia_id=m_id,
                turma_id=t_id,
                template_id=tmpl_id,
                valor_total=spn_valor.value(),
                data_aplicacao=dt_py
            )
            prova.set_gabarito(gabarito_dict)
            prova.save()

            alunos_class = Aluno.select().where(Aluno.turma_id == t_id)
            for al in alunos_class:
                ProvaAluno.get_or_create(prova=prova, aluno=al)

            dialog.accept()
            self.load_data()

        btn_save.clicked.connect(save_prova)
        vbox.addWidget(btn_save)
        dialog.exec()
