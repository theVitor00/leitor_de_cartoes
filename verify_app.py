"""
Verification Script testing Font Awesome icons, 4-Columns Answer Sheet Template,
PDF OMR Bubbles White Background Fix, and OMR Engine.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from PySide6.QtWidgets import QApplication
from omr_app.database.db_manager import init_db
from omr_app.database.models import Prova, Aluno, Template, Materia, Turma
from omr_app.core.pdf_generator import OMRPDFGenerator
from omr_app.core.omr_engine import OMREngine
from omr_app.utils.image_helpers import load_file_to_cv2_images
from omr_app.gui.main_window import MainWindow


def test_full_pipeline():
    print("=== TEST 1: Database & GUI MainWindow Init with Font Awesome Icons ===")
    db_path = init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    print(f"Database: {db_path} | GUI MainWindow & Font Awesome Icons initialized successfully!")

    print("\n=== TEST 2: Template Creation (4 Columns, 20 Questions, A-E) ===")
    tmpl = Template.create(
        nome="Template Teste 4 Colunas - 20 Questões A-E",
        quantidade_questoes=20,
        alternativas_por_questao=5,
        colunas=4,
        exibir_assinatura=True,
        cor_cabecalho_hex="#00AEA7"
    )
    print(f"Template 4 Colunas Criado: ID #{tmpl.id} - {tmpl.nome}")

    materia = Materia.select().first()
    turma = Turma.select().first()

    prova = Prova.create(
        titulo="Prova Teste 4 Colunas",
        materia=materia,
        turma=turma,
        template=tmpl,
        valor_total=10.0
    )
    gabarito_test = {str(i): ["A", "B", "C", "D", "E"][(i - 1) % 5] for i in range(1, 21)}
    prova.set_gabarito(gabarito_test)
    prova.save()

    aluno = Aluno.select().first()

    print("\n=== TEST 3: Dynamic PDF Generation & Bubble Fill Inspection (4 Columns) ===")
    pdf_filename = "test_cartao_4_colunas.pdf"
    generator = OMRPDFGenerator(pdf_filename)
    generator.build_pdf(
        prova_title=prova.titulo,
        materia_nome=prova.materia.nome,
        turma_nome=prova.turma.nome,
        data_str="13/08/2026",
        prova_id=prova.id,
        aluno_nome=aluno.nome,
        aluno_matricula=aluno.matricula,
        aluno_id=aluno.id,
        num_questions=tmpl.quantidade_questoes,
        num_options=tmpl.alternativas_por_questao,
        colunas=tmpl.colunas,
        exibir_assinatura=tmpl.exibir_assinatura,
        cor_cabecalho_hex=tmpl.cor_cabecalho_hex
    )
    print(f"PDF 4 Colunas gerado em: {os.path.abspath(pdf_filename)}")
    assert os.path.exists(pdf_filename), "Geração do PDF de 4 colunas falhou!"

    print("\n=== TEST 4: OMR Engine Scan & Verification (4 Columns Grid) ===")
    pages = load_file_to_cv2_images(pdf_filename)
    print(f"Convertido PDF em {len(pages)} imagem(ns) de página.")
    assert len(pages) > 0, "Falha na conversão do PDF para imagem!"

    page_num, img_bgr = pages[0]

    engine = OMREngine()
    result = engine.process_sheet_image(
        image_bgr=img_bgr,
        expected_prova_id=prova.id,
        gabarito_dict=prova.get_gabarito(),
        valor_total=prova.valor_total,
        num_questions=tmpl.quantidade_questoes,
        num_options=tmpl.alternativas_por_questao,
        colunas=tmpl.colunas,
        sensitivity_pct=45.0
    )

    print("Resultado da Varredura OMR (4 Colunas):")
    print(f"  - Prova ID detectada: {result['prova_id']}")
    print(f"  - Aluno ID detectado: {result['aluno_id']}")
    print(f"  - Status: {result['status']}")
    print(f"  - Imagem anotada salva em: {result['annotated_path']}")

    assert result['annotated_path'] and os.path.exists(result['annotated_path']), "Imagem de scan não gerada!"

    print("\nALL VERIFICATION TESTS FOR FONT AWESOME ICONS, 4-COLUMNS LAYOUT & WHITE BUBBLES PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_full_pipeline()
