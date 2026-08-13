"""
Templates Management View (Gerenciador e Configurador de Modelos de Cartão).
Supports 1, 2, 3, or 4 columns. Uses high-contrast Font Awesome icons
with clear labels, tooltips, and non-clipping compact button sizing.
"""

import os
import tempfile
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QDialog, QFormLayout,
    QMessageBox, QSpinBox, QCheckBox, QFileDialog, QColorDialog
)
from PySide6.QtGui import QColor
from omr_app.assets.icons import get_icon
from omr_app.database.models import Template, Prova
from omr_app.core.pdf_generator import OMRPDFGenerator


class TemplatesView(QWidget):

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        top_layout = QHBoxLayout()
        lbl_title = QLabel("Gerenciador de Modelos de Cartão-Resposta (Templates)")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00AEA7;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        btn_add_tmpl = QPushButton(" Novo Modelo de Cartão")
        btn_add_tmpl.setIcon(get_icon("plus", color="white"))
        btn_add_tmpl.setProperty("class", "btn-primary")
        btn_add_tmpl.setToolTip("Criar um novo modelo personalizado de cartão-resposta OMR")
        btn_add_tmpl.clicked.connect(lambda: self._open_template_dialog())
        top_layout.addWidget(btn_add_tmpl)

        layout.addLayout(top_layout)

        self.table_templates = QTableWidget()
        self.table_templates.setColumnCount(8)
        self.table_templates.setHorizontalHeaderLabels([
            "ID", "Nome do Modelo", "Questões", "Alternativas", "Colunas", "Assinatura", "Cor Cabeçalho", "Ações do Modelo"
        ])
        self.table_templates.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_templates.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table_templates.setColumnWidth(7, 310)
        self.table_templates.verticalHeader().setDefaultSectionSize(44)
        layout.addWidget(self.table_templates)

        self.load_data()

    def load_data(self):
        self.table_templates.setRowCount(0)
        for t in Template.select():
            row = self.table_templates.rowCount()
            self.table_templates.insertRow(row)

            opts_str = {3: "A-C", 4: "A-D", 5: "A-E"}.get(t.alternativas_por_questao, "A-E")
            ass_str = "Sim" if t.exibir_assinatura else "Não"

            self.table_templates.setItem(row, 0, QTableWidgetItem(str(t.id)))
            self.table_templates.setItem(row, 1, QTableWidgetItem(t.nome))
            self.table_templates.setItem(row, 2, QTableWidgetItem(str(t.quantidade_questoes)))
            self.table_templates.setItem(row, 3, QTableWidgetItem(opts_str))
            self.table_templates.setItem(row, 4, QTableWidgetItem(f"{t.colunas} Coluna(s)"))
            self.table_templates.setItem(row, 5, QTableWidgetItem(ass_str))

            color_item = QTableWidgetItem(t.cor_cabecalho_hex)
            color_item.setForeground(QColor(t.cor_cabecalho_hex))
            self.table_templates.setItem(row, 6, color_item)

            cell_widget = QWidget()
            h_box = QHBoxLayout(cell_widget)
            h_box.setContentsMargins(6, 4, 6, 4)
            h_box.setSpacing(6)

            # Action Button 1: PDF Preview
            btn_prev = QPushButton(" Prévia PDF")
            btn_prev.setIcon(get_icon("pdf"))
            btn_prev.setProperty("class", "btn-outline btn-sm")
            btn_prev.setToolTip("Gerar e abrir prévia do cartão-resposta em formato PDF")
            btn_prev.clicked.connect(lambda chk, tmpl=t: self._preview_template_pdf(tmpl))

            # Action Button 2: Edit Template
            btn_edit = QPushButton(" Editar")
            btn_edit.setIcon(get_icon("edit", color="white"))
            btn_edit.setProperty("class", "btn-secondary btn-sm")
            btn_edit.setToolTip("Editar nome, questões, colunas ou visual deste modelo")
            btn_edit.clicked.connect(lambda chk, tmpl=t: self._open_template_dialog(tmpl))

            # Action Button 3: Delete Template
            btn_del = QPushButton(" Excluir")
            btn_del.setIcon(get_icon("delete", color="white"))
            btn_del.setProperty("class", "btn-danger btn-sm")
            btn_del.setToolTip("Excluir permanentemente este modelo de cartão")
            btn_del.clicked.connect(lambda chk, tmpl=t: self._delete_template(tmpl))

            h_box.addWidget(btn_prev)
            h_box.addWidget(btn_edit)
            h_box.addWidget(btn_del)

            self.table_templates.setCellWidget(row, 7, cell_widget)

    def _open_template_dialog(self, template_obj: Template = None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Modelo de Cartão" if template_obj else "Novo Modelo de Cartão-Resposta")
        dialog.setFixedWidth(500)

        vbox = QVBoxLayout(dialog)
        form = QFormLayout()

        txt_nome = QLineEdit(template_obj.nome if template_obj else "")
        txt_nome.setPlaceholderText("Ex: Simulado 50 Questões - 2 Colunas")

        spn_questoes = QSpinBox()
        spn_questoes.setRange(1, 100)
        spn_questoes.setValue(template_obj.quantidade_questoes if template_obj else 10)

        combo_opts = QComboBox()
        combo_opts.addItem("3 Alternativas (A, B, C)", 3)
        combo_opts.addItem("4 Alternativas (A, B, C, D)", 4)
        combo_opts.addItem("5 Alternativas (A, B, C, D, E)", 5)
        if template_obj:
            idx = combo_opts.findData(template_obj.alternativas_por_questao)
            if idx >= 0:
                combo_opts.setCurrentIndex(idx)
        else:
            combo_opts.setCurrentIndex(2)

        combo_cols = QComboBox()
        combo_cols.addItem("1 Coluna", 1)
        combo_cols.addItem("2 Colunas", 2)
        combo_cols.addItem("3 Colunas", 3)
        combo_cols.addItem("4 Colunas", 4)
        if template_obj:
            idx = combo_cols.findData(template_obj.colunas)
            if idx >= 0:
                combo_cols.setCurrentIndex(idx)
        else:
            combo_cols.setCurrentIndex(1)

        chk_assinatura = QCheckBox("Exibir caixa de Assinatura do Aluno")
        chk_assinatura.setChecked(template_obj.exibir_assinatura if template_obj else True)

        color_layout = QHBoxLayout()
        txt_hex = QLineEdit(template_obj.cor_cabecalho_hex if template_obj else "#00AEA7")
        btn_pick_color = QPushButton(" Escolher Cor")
        btn_pick_color.setIcon(get_icon("color"))
        btn_pick_color.setProperty("class", "btn-outline")
        btn_pick_color.setToolTip("Abrir paleta para selecionar a cor do cabeçalho")

        def pick_color():
            c = QColorDialog.getColor(QColor(txt_hex.text().strip()), dialog, "Selecione a Cor do Cabeçalho")
            if c.isValid():
                txt_hex.setText(c.name())

        btn_pick_color.clicked.connect(pick_color)
        color_layout.addWidget(txt_hex)
        color_layout.addWidget(btn_pick_color)

        logo_layout = QHBoxLayout()
        txt_logo = QLineEdit(template_obj.caminho_logo if (template_obj and template_obj.caminho_logo) else "")
        txt_logo.setPlaceholderText("Caminho da imagem da logo (PNG/JPG)")
        btn_logo = QPushButton(" Buscar Logo")
        btn_logo.setIcon(get_icon("folder"))
        btn_logo.setProperty("class", "btn-outline")
        btn_logo.setToolTip("Selecionar imagem de logo para o cabeçalho do cartão")

        def pick_logo():
            f, _ = QFileDialog.getOpenFileName(dialog, "Selecionar Logo", "", "Imagens (*.png *.jpg *.jpeg)")
            if f:
                txt_logo.setText(f)

        btn_logo.clicked.connect(pick_logo)
        logo_layout.addWidget(txt_logo)
        logo_layout.addWidget(btn_logo)

        form.addRow("Nome do Modelo:", txt_nome)
        form.addRow("Número de Questões (1-100):", spn_questoes)
        form.addRow("Quantidade de Alternativas:", combo_opts)
        form.addRow("Disposição em Colunas:", combo_cols)
        form.addRow("Assinatura:", chk_assinatura)
        form.addRow("Cor do Cabeçalho (Hex):", color_layout)
        form.addRow("Logo da Instituição:", logo_layout)

        vbox.addLayout(form)

        btn_box = QHBoxLayout()

        btn_prev = QPushButton(" Gerar Prévia em PDF")
        btn_prev.setIcon(get_icon("pdf", color="white"))
        btn_prev.setProperty("class", "btn-secondary")
        btn_prev.setToolTip("Gerar prévia instantânea em PDF com os parâmetros acima")

        def generate_temp_preview():
            temp_pdf = os.path.join(tempfile.gettempdir(), "previa_template_omr.pdf")
            generator = OMRPDFGenerator(temp_pdf)
            generator.build_pdf(
                prova_title="PROVA DE TESTE - PRÉVIA DE TEMPLATE",
                materia_nome="Disciplina Modelo",
                turma_nome="Turma Modelo",
                data_str="13/08/2026",
                prova_id=999,
                aluno_nome="Aluno Exemplo da Silva",
                aluno_matricula="2026999",
                aluno_id=999,
                num_questions=spn_questoes.value(),
                num_options=combo_opts.currentData(),
                colunas=combo_cols.currentData(),
                exibir_assinatura=chk_assinatura.isChecked(),
                cor_cabecalho_hex=txt_hex.text().strip(),
                caminho_logo=txt_logo.text().strip() if txt_logo.text().strip() else None
            )

            try:
                if os.name == 'nt':
                    os.startfile(temp_pdf)
                else:
                    subprocess.run(["xdg-open", temp_pdf])
            except Exception:
                QMessageBox.information(dialog, "Prévia Gerada", f"PDF salvo em:\n{temp_pdf}")

        btn_prev.clicked.connect(generate_temp_preview)
        btn_box.addWidget(btn_prev)

        btn_save = QPushButton("Salvar Modelo")
        btn_save.setIcon(get_icon("check", color="white"))
        btn_save.setProperty("class", "btn-primary")
        btn_save.setToolTip("Salvar modelo no banco de dados")

        def save():
            n = txt_nome.text().strip()
            if not n:
                QMessageBox.warning(dialog, "Aviso", "Preencha o nome do modelo.")
                return

            q_val = spn_questoes.value()
            opt_val = combo_opts.currentData()
            col_val = combo_cols.currentData()
            ass_val = chk_assinatura.isChecked()
            hex_val = txt_hex.text().strip() or "#00AEA7"
            logo_val = txt_logo.text().strip() if txt_logo.text().strip() else None

            if template_obj:
                template_obj.nome = n
                template_obj.quantidade_questoes = q_val
                template_obj.alternativas_por_questao = opt_val
                template_obj.colunas = col_val
                template_obj.exibir_assinatura = ass_val
                template_obj.cor_cabecalho_hex = hex_val
                template_obj.caminho_logo = logo_val
                template_obj.save()
            else:
                Template.create(
                    nome=n,
                    quantidade_questoes=q_val,
                    alternativas_por_questao=opt_val,
                    colunas=col_val,
                    exibir_assinatura=ass_val,
                    cor_cabecalho_hex=hex_val,
                    caminho_logo=logo_val
                )

            dialog.accept()
            self.load_data()

        btn_save.clicked.connect(save)
        btn_box.addWidget(btn_save)

        vbox.addLayout(btn_box)
        dialog.exec()

    def _preview_template_pdf(self, template_obj: Template):
        temp_pdf = os.path.join(tempfile.gettempdir(), f"previa_template_{template_obj.id}.pdf")
        generator = OMRPDFGenerator(temp_pdf)
        generator.build_pdf(
            prova_title=f"PRÉVIA: {template_obj.nome}",
            materia_nome="Disciplina Demonstração",
            turma_nome="Turma 3º Ano A",
            data_str="13/08/2026",
            prova_id=template_obj.id,
            aluno_nome="João da Silva Santos",
            aluno_matricula="2026001",
            aluno_id=1,
            num_questions=template_obj.quantidade_questoes,
            num_options=template_obj.alternativas_por_questao,
            colunas=template_obj.colunas,
            exibir_assinatura=template_obj.exibir_assinatura,
            cor_cabecalho_hex=template_obj.cor_cabecalho_hex,
            caminho_logo=template_obj.caminho_logo
        )

        try:
            if os.name == 'nt':
                os.startfile(temp_pdf)
            else:
                subprocess.run(["xdg-open", temp_pdf])
        except Exception:
            QMessageBox.information(self, "Prévia Gerada", f"PDF gerado com sucesso em:\n{temp_pdf}")

    def _delete_template(self, template_obj: Template):
        provas_count = Prova.select().where(Prova.template == template_obj).count()
        if provas_count > 0:
            QMessageBox.warning(
                self, "Atenção",
                f"Este modelo não pode ser excluído pois está vinculado a {provas_count} prova(s) cadastrada(s)."
            )
            return

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir o modelo '{template_obj.nome}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            template_obj.delete_instance()
            self.load_data()
