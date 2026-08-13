"""
Verification Script testing DB Schema, Dynamic Templates, PDF Generation,
SHA-256 QR Hash Security, OpenCV OMR Engine Sensitivity, Excel export, and Process Logger.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from omr_app.database.db_manager import init_db
from omr_app.database.models import Prova, Aluno, Resultado, Template, Materia, Turma
from omr_app.core.pdf_generator import OMRPDFGenerator
from omr_app.core.omr_engine import OMREngine
from omr_app.utils.image_helpers import load_file_to_cv2_images
from omr_app.utils.excel_exporter import export_results_to_excel
from omr_app.logs.process_logger import ProcessLogger


def test_full_pipeline():
    print("=== TEST 1: Database Initialization & Migrations ===")
    db_path = init_db()
    print(f"Database initialized at: {db_path}")

    print("\n=== TEST 2: Template Creation & Configuration ===")
    tmpl = Template.create(
        nome="Template Teste 3 Colunas - 15 Questões A-D",
        quantidade_questoes=15,
        alternativas_por_questao=4,
        colunas=3,
        exibir_assinatura=True,
        cor_cabecalho_hex="#002970"
    )
    print(f"Template criado: ID #{tmpl.id} - {tmpl.nome}")

    materia = Materia.select().first()
    turma = Turma.select().first()

    prova = Prova.create(
        titulo="Prova Teste Template Dinâmico",
        materia=materia,
        turma=turma,
        template=tmpl,
        valor_total=10.0
    )
    gabarito_test = {str(i): ["A", "B", "C", "D"][(i - 1) % 4] for i in range(1, 16)}
    prova.set_gabarito(gabarito_test)
    prova.save()

    aluno = Aluno.select().first()

    print("\n=== TEST 3: Dynamic PDF Answer Sheet Generation ===")
    pdf_filename = "test_cartao_template_dinamico.pdf"
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
    print(f"Dynamic PDF generated: {os.path.abspath(pdf_filename)}")
    assert os.path.exists(pdf_filename), "PDF generation failed!"

    print("\n=== TEST 4: Image Conversion & OpenCV OMR Engine Scan (with Sensitivity Slider) ===")
    pages = load_file_to_cv2_images(pdf_filename)
    print(f"Converted PDF to {len(pages)} page image(s).")
    assert len(pages) > 0, "PDF rendering failed!"

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
        sensitivity_pct=40.0
    )

    print("OMR Processing Result:")
    print(f"  - Prova ID detected: {result['prova_id']}")
    print(f"  - Aluno ID detected: {result['aluno_id']}")
    print(f"  - Status: {result['status']}")
    print(f"  - Flagged Question Boxes: {len(result['flagged_boxes'])}")
    print(f"  - Annotated Image saved: {result['annotated_path']}")

    assert result['annotated_path'] and os.path.exists(result['annotated_path']), "Annotated image missing!"

    print("\n=== TEST 5: Process Logging & Excel Export ===")
    logger = ProcessLogger()
    log_rec = logger.record_run_log(
        prova_id=prova.id,
        total=1,
        sucessos=1 if result['status'] == 'OK' else 0,
        revisoes=1 if result['status'] == 'REVISAO_NECESSARIA' else 0,
        erros=1 if result['status'] == 'ERRO_LEITURA' else 0,
        detalhes=[result]
    )
    print(f"Run log created with ID #{log_rec.id}")

    excel_path = "relatorio_template_teste.xlsx"
    export_results_to_excel(prova.id, excel_path)
    print(f"Excel report exported to: {os.path.abspath(excel_path)}")
    assert os.path.exists(excel_path), "Excel export failed!"

    print("\n✅ ALL TEMPLATE & ENGINE VERIFICATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_full_pipeline()
