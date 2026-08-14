"""
Students & Classes View (CRUD for Turmas & Alunos).
Uses high-contrast Font Awesome icons and referential integrity checks on deletion.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
    QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt
from omr_app.assets.icons import get_icon
from omr_app.database.models import Turma, Aluno, Resultado, Prova, ProvaAluno


class StudentsView(QWidget):

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        top_layout = QHBoxLayout()
        lbl_title = QLabel("Gestão de Alunos e Turmas")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00AEA7;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        btn_add_turma = QPushButton(" Gerenciar Turmas")
        btn_add_turma.setIcon(get_icon("folder", color="white"))
        btn_add_turma.setProperty("class", "btn-secondary")
        btn_add_turma.setToolTip("Cadastrar ou excluir turmas do sistema")
        btn_add_turma.clicked.connect(self._open_manage_turmas_dialog)
        top_layout.addWidget(btn_add_turma)

        btn_add_aluno = QPushButton(" Novo Aluno")
        btn_add_aluno.setIcon(get_icon("plus", color="white"))
        btn_add_aluno.setProperty("class", "btn-primary")
        btn_add_aluno.setToolTip("Cadastrar um novo aluno em uma turma")
        btn_add_aluno.clicked.connect(self._open_add_aluno_dialog)
        top_layout.addWidget(btn_add_aluno)

        layout.addLayout(top_layout)

        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nome ou matrícula...")
        self.search_input.textChanged.connect(self.load_data)
        filter_layout.addWidget(self.search_input)

        self.combo_turma_filter = QComboBox()
        self.combo_turma_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.combo_turma_filter)

        layout.addLayout(filter_layout)

        self.table_alunos = QTableWidget()
        self.table_alunos.setColumnCount(5)
        self.table_alunos.setHorizontalHeaderLabels([
            "ID", "Matrícula", "Nome do Aluno", "Turma", "Ações"
        ])
        self.table_alunos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_alunos.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table_alunos.setColumnWidth(4, 120)
        self.table_alunos.verticalHeader().setDefaultSectionSize(44)
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

        text = self.search_input.text().strip()
        if text:
            query = query.where((Aluno.nome.contains(text)) | (Aluno.matricula.contains(text)))

        t_id = self.combo_turma_filter.currentData()
        if t_id:
            query = query.where(Aluno.turma == t_id)

        self.table_alunos.setRowCount(0)
        for a in query:
            row = self.table_alunos.rowCount()
            self.table_alunos.insertRow(row)

            item_id = QTableWidgetItem(str(a.id))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table_alunos.setItem(row, 0, item_id)

            self.table_alunos.setItem(row, 1, QTableWidgetItem(a.matricula))
            self.table_alunos.setItem(row, 2, QTableWidgetItem(a.nome))
            self.table_alunos.setItem(row, 3, QTableWidgetItem(a.turma.nome if a.turma else "N/A"))

            # Action Column: Delete Aluno Button
            cell_widget = QWidget()
            h_box = QHBoxLayout(cell_widget)
            h_box.setContentsMargins(4, 4, 4, 4)

            btn_del = QPushButton(" Excluir")
            btn_del.setIcon(get_icon("delete", color="white"))
            btn_del.setProperty("class", "btn-danger btn-sm")
            btn_del.setToolTip("Excluir permanentemente este aluno")
            btn_del.clicked.connect(lambda chk, aluno=a: self._delete_aluno(aluno))

            h_box.addWidget(btn_del)
            self.table_alunos.setCellWidget(row, 4, cell_widget)

    def _delete_aluno(self, aluno_obj: Aluno):
        resultados_count = Resultado.select().where(Resultado.aluno == aluno_obj).count()
        if resultados_count > 0:
            QMessageBox.warning(
                self, "Atenção",
                f"Não é possível excluir o aluno '{aluno_obj.nome}' porque existem {resultados_count} resultado(s) vinculado(s) a ele."
            )
            return

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o aluno '{aluno_obj.nome}' (Matrícula: {aluno_obj.matricula})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ProvaAluno.delete().where(ProvaAluno.aluno == aluno_obj).execute()
            aluno_obj.delete_instance()
            self.load_data()

    def _delete_turma(self, turma_obj: Turma, dialog_parent: QDialog = None):
        alunos_count = Aluno.select().where(Aluno.turma == turma_obj).count()
        if alunos_count > 0:
            QMessageBox.warning(
                dialog_parent or self, "Atenção",
                f"Não é possível excluir esta turma porque existem {alunos_count} aluno(s) vinculado(s) a ela."
            )
            return

        provas_count = Prova.select().where(Prova.turma == turma_obj).count()
        if provas_count > 0:
            QMessageBox.warning(
                dialog_parent or self, "Atenção",
                f"Não é possível excluir esta turma porque existem {provas_count} prova(s) vinculada(s) a ela."
            )
            return

        reply = QMessageBox.question(
            dialog_parent or self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a turma '{turma_obj.nome}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            turma_obj.delete_instance()
            self.load_turmas_combo()
            self.load_data()

    def _open_manage_turmas_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Gerenciar Turmas")
        dialog.setFixedWidth(500)

        vbox = QVBoxLayout(dialog)

        lbl_header = QLabel("Turmas Cadastradas:")
        lbl_header.setStyleSheet("font-weight: bold; color: #00AEA7;")
        vbox.addWidget(lbl_header)

        table_t = QTableWidget()
        table_t.setColumnCount(4)
        table_t.setHorizontalHeaderLabels(["ID", "Nome da Turma", "Ano", "Ação"])
        table_t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_t.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        table_t.setColumnWidth(3, 110)

        def load_dialog_turmas():
            table_t.setRowCount(0)
            for t in Turma.select():
                r = table_t.rowCount()
                table_t.insertRow(r)
                table_t.setItem(r, 0, QTableWidgetItem(str(t.id)))
                table_t.setItem(r, 1, QTableWidgetItem(t.nome))
                table_t.setItem(r, 2, QTableWidgetItem(str(t.ano_letivo)))

                cell = QWidget()
                hb = QHBoxLayout(cell)
                hb.setContentsMargins(2, 2, 2, 2)
                btn_d = QPushButton("Excluir")
                btn_d.setIcon(get_icon("delete", color="white"))
                btn_d.setProperty("class", "btn-danger btn-sm")
                btn_d.clicked.connect(lambda chk, tm=t: [self._delete_turma(tm, dialog), load_dialog_turmas()])
                hb.addWidget(btn_d)
                table_t.setCellWidget(r, 3, cell)

        load_dialog_turmas()
        vbox.addWidget(table_t)

        lbl_new = QLabel("Cadastrar Nova Turma:")
        lbl_new.setStyleSheet("font-weight: bold; margin-top: 10px;")
        vbox.addWidget(lbl_new)

        form = QFormLayout()
        txt_nome = QLineEdit()
        txt_nome.setPlaceholderText("Ex: 3º Ano A")
        spn_ano = QSpinBox()
        spn_ano.setRange(2020, 2035)
        spn_ano.setValue(2026)

        form.addRow("Nome da Turma:", txt_nome)
        form.addRow("Ano Letivo:", spn_ano)

        btn_save = QPushButton("Salvar Nova Turma")
        btn_save.setIcon(get_icon("check", color="white"))
        btn_save.setProperty("class", "btn-primary")

        def save():
            if not txt_nome.text().strip():
                QMessageBox.warning(dialog, "Aviso", "Preencha o nome da turma.")
                return
            Turma.create(nome=txt_nome.text().strip(), ano_letivo=spn_ano.value())
            txt_nome.clear()
            load_dialog_turmas()
            self.load_turmas_combo()
            self.load_data()

        btn_save.clicked.connect(save)
        form.addRow(btn_save)
        vbox.addLayout(form)

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
        btn_save.setIcon(get_icon("check", color="white"))
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
