"""
Unit tests for pure Python ExamGrader.
"""

import unittest
from omr_app.core.grader import ExamGrader
from omr_app.core.types import OMRStatus
from omr_app.core.layout import SheetLayout


class TestExamGrader(unittest.TestCase):

    def test_perfect_score(self):
        gabarito = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}
        respostas = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}

        res = ExamGrader.grade(
            respostas_marcadas=respostas,
            gabarito_dict=gabarito,
            valor_total=10.0,
            num_questions=5,
            qr_valid=True
        )

        self.assertEqual(res.status, OMRStatus.OK)
        self.assertEqual(res.acertos, 5)
        self.assertEqual(res.nota_final, 10.0)
        self.assertEqual(len(res.flagged_boxes), 0)

    def test_partial_score_and_blank_answers(self):
        gabarito = {"1": "A", "2": "B", "3": "C", "4": "D"}
        respostas = {"1": "A", "2": "C", "3": "-", "4": "D"}

        res = ExamGrader.grade(
            respostas_marcadas=respostas,
            gabarito_dict=gabarito,
            valor_total=10.0,
            num_questions=4,
            qr_valid=True
        )

        self.assertEqual(res.status, OMRStatus.OK)
        self.assertEqual(res.acertos, 2)
        self.assertEqual(res.nota_final, 5.0)

    def test_double_marked_question_triggers_review(self):
        layout = SheetLayout(num_questions=5, num_options=5, colunas=2)
        gabarito = {"1": "A", "2": "B", "3": "C"}
        respostas = {"1": "A", "2": "A|B", "3": "C"}

        res = ExamGrader.grade(
            respostas_marcadas=respostas,
            gabarito_dict=gabarito,
            valor_total=10.0,
            num_questions=3,
            layout=layout,
            qr_valid=True
        )

        self.assertEqual(res.status, OMRStatus.REVISAO_NECESSARIA)
        self.assertEqual(res.acertos, 2)
        self.assertEqual(len(res.flagged_boxes), 1)
        self.assertEqual(res.flagged_boxes[0]["question"], "2")
        self.assertEqual(res.flagged_boxes[0]["reason"], "A|B")

    def test_invalid_qr_code_triggers_review(self):
        gabarito = {"1": "A"}
        respostas = {"1": "A"}

        res = ExamGrader.grade(
            respostas_marcadas=respostas,
            gabarito_dict=gabarito,
            valor_total=10.0,
            num_questions=1,
            qr_valid=False
        )

        self.assertEqual(res.status, OMRStatus.REVISAO_NECESSARIA)
        self.assertIn("QR Code", res.mensagem)

    def test_missing_gabarito(self):
        respostas = {"1": "A"}
        res = ExamGrader.grade(
            respostas_marcadas=respostas,
            gabarito_dict=None,
            valor_total=10.0,
            num_questions=1
        )
        self.assertEqual(res.status, OMRStatus.REVISAO_NECESSARIA)
        self.assertIn("Gabarito não fornecido", res.mensagem)


if __name__ == "__main__":
    unittest.main()
