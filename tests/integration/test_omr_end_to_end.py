"""
End-to-End integration test proving geometric consistency between PDF generation and OMR reading.
Tests PDF generation -> Rasterization -> Synthetic bubble marking -> OMREngine reading -> Exact answer assertion.
Validates 2, 3, and 4 column layouts with 3, 4, and 5 option configurations.
"""

import os
import unittest
import cv2
import numpy as np

from omr_app.core.pdf_generator import OMRPDFGenerator
from omr_app.core.omr_engine import OMREngine
from omr_app.core.layout import SheetLayout
from omr_app.core.types import OMRStatus
from omr_app.utils.image_helpers import load_file_to_cv2_images


class TestOMREndToEndGeometricConsistency(unittest.TestCase):

    def setUp(self):
        self.test_pdf = "test_end_to_end_sheet.pdf"
        self.engine = OMREngine()

    def tearDown(self):
        if os.path.exists(self.test_pdf):
            try:
                os.remove(self.test_pdf)
            except Exception:
                pass

    def _run_e2e_test_for_layout(self, num_questions: int, num_options: int, colunas: int):
        # 1. Generate PDF Answer Sheet
        generator = OMRPDFGenerator(self.test_pdf)
        generator.build_pdf(
            prova_title=f"E2E Test {num_questions}Q {colunas}C {num_options}O",
            materia_nome="Matemática",
            turma_nome="Turma 101",
            data_str="14/08/2026",
            prova_id=99,
            aluno_nome="Aluno Teste E2E",
            aluno_matricula="2026999",
            aluno_id=77,
            num_questions=num_questions,
            num_options=num_options,
            colunas=colunas
        )
        self.assertTrue(os.path.exists(self.test_pdf))

        # 2. Rasterize PDF page to BGR image
        pages = load_file_to_cv2_images(self.test_pdf)
        self.assertGreater(len(pages), 0)
        _, img_bgr = pages[0]

        # 3. Define expected answers pattern and mark bubbles synthetically on the PDF rasterized image
        options_letters = ["A", "B", "C", "D", "E"][:num_options]
        layout = SheetLayout(num_questions=num_questions, num_options=num_options, colunas=colunas)

        expected_answers = {}
        gabarito = {}

        h_img, w_img = img_bgr.shape[:2]

        for q in range(1, num_questions + 1):
            opt_idx = (q - 1) % num_options
            letter = options_letters[opt_idx]
            expected_answers[str(q)] = letter
            gabarito[str(q)] = letter

            # Get bubble position in PDF points
            bx_pdf, by_pdf, r_pdf = layout.get_bubble_pdf_center(q, opt_idx)

            # Convert PDF points to rasterized image pixel coordinates
            px = int(round((bx_pdf / layout.PDF_PAGE_WIDTH) * w_img))
            py = int(round(((layout.PDF_PAGE_HEIGHT - by_pdf) / layout.PDF_PAGE_HEIGHT) * h_img))
            pr = int(round((r_pdf / layout.PDF_PAGE_WIDTH) * w_img))

            # Draw filled dark circle on the raw image
            cv2.circle(img_bgr, (px, py), max(2, pr - 1), (10, 10, 10), -1)

        # 4. Execute OMR Reading Phase
        reading_res = self.engine.read_sheet(
            image_bgr=img_bgr,
            expected_prova_id=99,
            num_questions=num_questions,
            num_options=num_options,
            colunas=colunas
        )

        self.assertEqual(reading_res.status, OMRStatus.OK)
        self.assertTrue(reading_res.qr_valid)
        self.assertEqual(reading_res.prova_id, 99)
        self.assertEqual(reading_res.aluno_id, 77)

        # 5. Assert exact match of detected answers vs expected answers
        for q_str, expected_letter in expected_answers.items():
            self.assertIn(q_str, reading_res.respostas)
            self.assertEqual(
                reading_res.respostas[q_str],
                expected_letter,
                f"Question {q_str} failed: expected {expected_letter}, detected {reading_res.respostas.get(q_str)}"
            )

        # 6. Execute Full Exam Grading Phase
        res_dict = self.engine.process_sheet_image(
            image_bgr=img_bgr,
            expected_prova_id=99,
            gabarito_dict=gabarito,
            valor_total=10.0,
            num_questions=num_questions,
            num_options=num_options,
            colunas=colunas
        )

        self.assertEqual(res_dict["status"], OMRStatus.OK.value)
        self.assertEqual(res_dict["acertos"], num_questions)
        self.assertEqual(res_dict["nota_final"], 10.0)

    def test_end_to_end_2_columns_5_options(self):
        self._run_e2e_test_for_layout(num_questions=10, num_options=5, colunas=2)

    def test_end_to_end_3_columns_4_options(self):
        self._run_e2e_test_for_layout(num_questions=15, num_options=4, colunas=3)

    def test_end_to_end_4_columns_3_options(self):
        self._run_e2e_test_for_layout(num_questions=20, num_options=3, colunas=4)


if __name__ == "__main__":
    unittest.main()
