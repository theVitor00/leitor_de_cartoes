"""
Verification Script testing DB, PDF Generation, OpenCV OMR Engine, Excel export, and Logging.
"""

import os
import sys

# Ensure omr_app is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from omr_app.database.db_manager import init_db
from omr_app.database.models import Prova, Aluno, Resultado
from omr_app.core.pdf_generator import OMRPDFGenerator
from omr_app.core.omr_engine import OMREngine
from omr_app.utils.image_helpers import load_file_to_cv2_images
from omr_app.utils.excel_exporter import export_results_to_excel
from omr_app.logs.process_logger import ProcessLogger


def test_full_pipeline():
    print("=== TEST 1: Database Initialization ===")
    db_path = init_db()
    print(f"Database initialized at: {db_path}")

    print("\n=== TEST 2: PDF Answer Sheet Generation ===")
    prova = Prova.get_by_id(1)
    aluno = Aluno.get_by_id(1)

    pdf_filename = "test_cartao_resposta_aluno1.pdf"
    generator = OMRPDFGenerator(pdf_filename)
    generator.build_pdf(
        prova_title=prova.titulo,
        materia_nome=prova.materia.nome,
        turma_nome=prova.turma.nome,
        data_str=prova.data_aplicacao.strftime("%d/%m/%Y"),
        prova_id=prova.id,
        aluno_nome=aluno.nome,
        aluno_matricula=aluno.matricula,
        aluno_id=aluno.id,
        num_questions=10,
        num_options=5
    )
    print(f"PDF generated: {os.path.abspath(pdf_filename)}")
    assert os.path.exists(pdf_filename), "PDF generation failed!"

    print("\n=== TEST 3: Image Conversion & OMR Engine Scan ===")
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
        num_questions=10
    )

    print("OMR Processing Result:")
    print(f"  - Prova ID detected: {result['prova_id']}")
    print(f"  - Aluno ID detected: {result['aluno_id']}")
    print(f"  - Status: {result['status']}")
    print(f"  - Nota Final: {result['nota_final']}")
    print(f"  - Annotated Image saved: {result['annotated_path']}")

    assert result['annotated_path'] and os.path.exists(result['annotated_path']), "Annotated image missing!"

    print("\n=== TEST 4: Logging System ===")
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

    print("\n=== TEST 5: Excel Report Export ===")
    excel_path = "relatorio_teste.xlsx"
    export_results_to_excel(prova.id, excel_path)
    print(f"Excel report exported to: {os.path.abspath(excel_path)}")
    assert os.path.exists(excel_path), "Excel export failed!"

    print("\n✅ ALL BACKEND & ENGINE VERIFICATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_full_pipeline()
