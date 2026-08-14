"""
Integration tests for complete OMR PDF generation and image reading pipeline.
"""

import os
import unittest
from omr_app.database.db_manager import init_db
from omr_app.database.models import Prova, Aluno, Template, Materia, Turma
from omr_app.core.pdf_generator import OMRPDFGenerator
from omr_app.core.omr_engine import OMREngine
from omr_app.core.types import OMRStatus
from omr_app.utils.image_helpers import load_file_to_cv2_images


class TestOMRPipelineIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_path = init_db()
        cls.test_pdf = "test_omr_integration_sheet.pdf"

        # Create test models
        materia = Materia.select().first()
        turma = Turma.select().first()
        aluno = Aluno.select().first()

        tmpl = Template.create(
            nome="Integration Test Template 10Q 2C",
            quantidade_questoes=10,
            alternativas_por_questao=5,
            colunas=2,
            exibir_assinatura=True,
            cor_cabecalho_hex="#00AEA7"
        )

        cls.prova = Prova.create(
            titulo="Prova Integracao Test",
            materia=materia,
            turma=turma,
            template=tmpl,
            valor_total=10.0
        )
        gabarito = {str(i): ["A", "B", "C", "D", "E"][(i - 1) % 5] for i in range(1, 11)}
        cls.prova.set_gabarito(gabarito)
        cls.prova.save()
        cls.aluno = aluno

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_pdf):
            try:
                os.remove(cls.test_pdf)
            except Exception:
                pass

    def test_pdf_generation_and_omr_reading(self):
        # 1. Build PDF
        generator = OMRPDFGenerator(self.test_pdf)
        generator.build_pdf(
            prova_title=self.prova.titulo,
            materia_nome=self.prova.materia.nome,
            turma_nome=self.prova.turma.nome,
            data_str="14/08/2026",
            prova_id=self.prova.id,
            aluno_nome=self.aluno.nome,
            aluno_matricula=self.aluno.matricula,
            aluno_id=self.aluno.id,
            num_questions=10,
            num_options=5,
            colunas=2
        )
        self.assertTrue(os.path.exists(self.test_pdf))

        # 2. Render PDF page to CV2 image
        pages = load_file_to_cv2_images(self.test_pdf)
        self.assertGreater(len(pages), 0)
        _, img_bgr = pages[0]

        # 3. Process sheet with OMREngine
        engine = OMREngine()

        # Pure OMR Reading phase
        reading_res = engine.read_sheet(
            image_bgr=img_bgr,
            expected_prova_id=self.prova.id,
            num_questions=10,
            num_options=5,
            colunas=2
        )
        self.assertTrue(reading_res.qr_valid)
        self.assertEqual(reading_res.prova_id, self.prova.id)
        self.assertEqual(reading_res.aluno_id, self.aluno.id)

        # Full processing & grading phase
        res_dict = engine.process_sheet_image(
            image_bgr=img_bgr,
            expected_prova_id=self.prova.id,
            gabarito_dict=self.prova.get_gabarito(),
            valor_total=self.prova.valor_total,
            num_questions=10,
            num_options=5,
            colunas=2
        )

        self.assertIn(res_dict["status"], [OMRStatus.OK.value, OMRStatus.REVISAO_NECESSARIA.value])
        self.assertEqual(res_dict["prova_id"], self.prova.id)
        self.assertEqual(res_dict["aluno_id"], self.aluno.id)
        self.assertTrue(os.path.exists(res_dict["annotated_path"]))


if __name__ == "__main__":
    unittest.main()
