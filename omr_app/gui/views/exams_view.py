"""
Exams & Subjects View (CRUD for Materias, Provas and Interactive Answer Key Editor).
Uses high-contrast Font Awesome icons and enforces mandatory Template & Gabarito rules.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
    QMessageBox, QDoubleSpinBox, QDateEdit, QRadioButton,
    QGridLayout, QScrollArea, QButtonGroup
)
from PySide6.QtCore import Qt, QDate
from omr_app.assets.icons import get_icon
from omr_app.database.models import Materia, Turma, Prova, ProvaAluno, Aluno, Template, Resultado
from omr_app.gui.views.templates_view import TemplatesView


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

        btn_add_mat = QPushButton(" Gerenciar Disciplinas")
        btn_add_mat.setIcon(get_icon("folder", color="white"))
        btn_add_mat.setProperty("class", "btn-secondary")
        btn_add_mat.setToolTip("Cadastrar ou excluir disciplinas")
        btn_add_mat.clicked.connect(self._open_manage_materias_dialog)
        top_layout.addWidget(btn_add_mat)

        btn_add_prova = QPushButton(" Criar Nova Prova")
        btn_add_prova.setIcon(get_icon("plus", color="white"))
        btn_add_prova.setProperty("class", "btn-primary")
        btn_add_prova.setToolTip("Criar uma nova prova com Modelo de Cartão e Gabarito Obrigatório")
        btn_add_prova.clicked.connect(self._open_add_prova_dialog)
        top_layout.addWidget(btn_add_prova)

        layout.addLayout(top_layout)

        self.table_provas = QTableWidget()
        self.table_provas.setColumnCount(8)
        self.table_provas.setHorizontalHeaderLabels([
            "ID", "Título da Prova", "Disciplina", "Turma", "Modelo / Template", "Valor Total", "Data Aplicação", "Ações"
        ])
        self.table_provas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_provas.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table_provas.setColumnWidth(7, 120)
        self.table_provas.verticalHeader().setDefaultSectionSize(44)
        layout.addWidget(self.table_provas)

        self.load_data()

    def load_data(self):
        self.table_provas.setRowCount(0)
        for p in Prova.select():
            row = self.table_provas.rowCount()
            self.table_provas.insertRow(row)

            tmpl_nome = p.template.nome if p.template else "Sem Modelo"

            item_id = QTableWidgetItem(str(p.id))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table_provas.setItem(row, 0, item_id)

            self.table_provas.setItem(row, 1, QTableWidgetItem(p.titulo))
            self.table_provas.setItem(row, 2, QTableWidgetItem(p.materia.nome if p.materia else "N/A"))
            self.table_provas.setItem(row, 3, QTableWidgetItem(p.turma.nome if p.turma else "N/A"))
            self.table_provas.setItem(row, 4, QTableWidgetItem(tmpl_nome))
            self.table_provas.setItem(row, 5, QTableWidgetItem(f"{p.valor_total:.2f}"))
            dt_str = p.data_aplicacao.strftime("%d/%m/%Y") if p.data_aplicacao else ""
            self.table_provas.setItem(row, 6, QTableWidgetItem(dt_str))

            # Action Column: Delete Prova Button
            cell_widget = QWidget()
            h_box = QHBoxLayout(cell_widget)
            h_box.setContentsMargins(4, 4, 4, 4)

            btn_del = QPushButton(" Excluir")
            btn_del.setIcon(get_icon("delete", color="white"))
            btn_del.setProperty("class", "btn-danger btn-sm")
            btn_del.setToolTip("Excluir permanentemente esta prova")
            btn_del.clicked.connect(lambda chk, prova=p: self._delete_prova(prova))

            h_box.addWidget(btn_del)
            self.table_provas.setCellWidget(row, 7, cell_widget)

    def _delete_prova(self, prova_obj: Prova):
        resultados_count = Resultado.select().where(Resultado.prova == prova_obj).count()
        if resultados_count > 0:
            QMessageBox.warning(
                self, "Atenção",
                f"Não é possível excluir a prova '{prova_obj.titulo}' porque existem {resultados_count} resultado(s) vinculado(s) a ela."
            )
            return

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir a prova '{prova_obj.titulo}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ProvaAluno.delete().where(ProvaAluno.prova == prova_obj).execute()
            prova_obj.delete_instance()
            self.load_data()

    def _delete_materia(self, materia_obj: Materia, dialog_parent: QDialog = None):
        provas_count = Prova.select().where(Prova.materia == materia_obj).count()
        if provas_count > 0:
            QMessageBox.warning(
                dialog_parent or self, "Atenção",
                f"Não é possível excluir a disciplina '{materia_obj.nome}' porque existem {provas_count} prova(s) vinculada(s) a ela."
            )
            return

        reply = QMessageBox.question(
            dialog_parent or self, "Confirmar Exclusão",
            f"Deseja realmente excluir a disciplina '{materia_obj.nome}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            materia_obj.delete_instance()
            self.load_data()

    def _open_manage_materias_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Gerenciar Disciplinas")
        dialog.setFixedWidth(500)

        vbox = QVBoxLayout(dialog)

        lbl_header = QLabel("Disciplinas Cadastradas:")
        lbl_header.setStyleSheet("font-weight: bold; color: #00AEA7;")
        vbox.addWidget(lbl_header)

        table_m = QTableWidget()
        table_m.setColumnCount(4)
        table_m.setHorizontalHeaderLabels(["ID", "Código", "Nome da Disciplina", "Ação"])
        table_m.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_m.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        table_m.setColumnWidth(3, 110)

        def load_dialog_materias():
            table_m.setRowCount(0)
            for m in Materia.select():
                r = table_m.rowCount()
                table_m.insertRow(r)
                table_m.setItem(r, 0, QTableWidgetItem(str(m.id)))
                table_m.setItem(r, 1, QTableWidgetItem(m.codigo))
                table_m.setItem(r, 2, QTableWidgetItem(m.nome))

                cell = QWidget()
                hb = QHBoxLayout(cell)
                hb.setContentsMargins(2, 2, 2, 2)
                btn_d = QPushButton("Excluir")
                btn_d.setIcon(get_icon("delete", color="white"))
                btn_d.setProperty("class", "btn-danger btn-sm")
                btn_d.clicked.connect(lambda chk, mat=m: [self._delete_materia(mat, dialog), load_dialog_materias()])
                hb.addWidget(btn_d)
                table_m.setCellWidget(r, 3, cell)

        load_dialog_materias()
        vbox.addWidget(table_m)

        lbl_new = QLabel("Cadastrar Nova Disciplina:")
        lbl_new.setStyleSheet("font-weight: bold; margin-top: 10px;")
        vbox.addWidget(lbl_new)

        form = QFormLayout()
        txt_nome = QLineEdit()
        txt_cod = QLineEdit()
        txt_cod.setPlaceholderText("Ex: MAT101")

        form.addRow("Nome da Disciplina:", txt_nome)
        form.addRow("Código da Disciplina:", txt_cod)

        btn_save = QPushButton("Salvar Disciplina")
        btn_save.setIcon(get_icon("check", color="white"))
        btn_save.setProperty("class", "btn-primary")

        def save():
            n, c = txt_nome.text().strip(), txt_cod.text().strip()
            if not n or not c:
                QMessageBox.warning(dialog, "Aviso", "Preencha o nome e o código da disciplina.")
                return
            try:
                Materia.create(nome=n, codigo=c)
                txt_nome.clear()
                txt_cod.clear()
                load_dialog_materias()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Código já existente ou erro ao salvar: {e}")

        btn_save.clicked.connect(save)
        form.addRow(btn_save)
        vbox.addLayout(form)

        dialog.exec()

    def _open_add_prova_dialog(self):
        if Materia.select().count() == 0 or Turma.select().count() == 0:
            QMessageBox.warning(self, "Aviso", "Cadastre disciplinas e turmas antes de criar provas.")
            return

        # Mandatory Card Template check
        if Template.select().count() == 0:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Modelo de Cartão Obrigatório")
            msg_box.setText("Para criar uma prova é necessário possuir um Modelo de Cartão.")
            btn_create_tmpl = msg_box.addButton("Criar Modelo de Cartão", QMessageBox.ActionRole)
            btn_cancel = msg_box.addButton("Cancelar", QMessageBox.RejectRole)
            msg_box.exec()

            if msg_box.clickedButton() == btn_create_tmpl:
                tmpl_view = TemplatesView()
                tmpl_view._open_template_dialog()
                if Template.select().count() == 0:
                    return
            else:
                return

        dialog = QDialog(self)
        dialog.setWindowTitle("Criar Nova Prova e Configurar Gabarito Oficial")
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
        def reload_template_combo():
            combo_template.clear()
            for tmpl in Template.select():
                combo_template.addItem(
                    f"{tmpl.nome} ({tmpl.quantidade_questoes}Q - {tmpl.alternativas_por_questao} Alt)", tmpl.id
                )

        reload_template_combo()

        spn_valor = QDoubleSpinBox()
        spn_valor.setRange(1.0, 100.0)
        spn_valor.setValue(10.0)

        dt_edit = QDateEdit(QDate.currentDate())
        dt_edit.setCalendarPopup(True)

        form.addRow("Título da Prova:", txt_titulo)
        form.addRow("Disciplina:", combo_mat)
        form.addRow("Turma Target:", combo_turma)
        form.addRow("Modelo de Cartão (Obrigatório):", combo_template)
        form.addRow("Valor Total da Nota:", spn_valor)
        form.addRow("Data Aplicação:", dt_edit)

        vbox.addLayout(form)

        lbl_gab = QLabel("Editor do Gabarito Oficial (Obrigatório - Selecione a resposta correta para cada questão):")
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
            tmpl = Template.get_or_none(Template.id == tmpl_id) if tmpl_id else None
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

            tmpl_id = combo_template.currentData()
            tmpl = Template.get_or_none(Template.id == tmpl_id) if tmpl_id else None
            if not tmpl:
                QMessageBox.warning(dialog, "Aviso", "Selecione um Modelo de Cartão válido para a prova.")
                return

            expected_questions = tmpl.quantidade_questoes
            valid_letters = ["A", "B", "C", "D", "E"][:tmpl.alternativas_por_questao]

            gabarito_dict = {}
            for q_num in range(1, expected_questions + 1):
                bg = question_groups.get(q_num)
                if not bg:
                    QMessageBox.warning(dialog, "Aviso", f"Gabarito incompleto para a questão Q{q_num:02d}.")
                    return
                checked_btn = bg.checkedButton()
                if not checked_btn:
                    QMessageBox.warning(dialog, "Aviso", f"Selecione uma resposta para a questão Q{q_num:02d}.")
                    return
                letter = checked_btn.text().strip()
                if letter not in valid_letters:
                    QMessageBox.warning(dialog, "Aviso", f"Resposta inválida para a questão Q{q_num:02d}: '{letter}'.")
                    return
                gabarito_dict[str(q_num)] = letter

            if len(gabarito_dict) != expected_questions:
                QMessageBox.warning(
                    dialog, "Aviso",
                    f"O gabarito deve possuir exatamente {expected_questions} respostas (foram fornecidas {len(gabarito_dict)})."
                )
                return

            m_id = combo_mat.currentData()
            t_id = combo_turma.currentData()
            dt_py = dt_edit.date().toPython()

            prova = Prova.create(
                titulo=tit,
                materia_id=m_id,
                turma_id=t_id,
                template_id=tmpl.id,
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
