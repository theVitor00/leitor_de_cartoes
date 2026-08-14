"""
Unit tests for data types and dataclass serialization in omr_app.core.types.
"""

import unittest
from omr_app.core.types import (
    OMRStatus,
    QuestionBoundingBox,
    OMRReadingResult,
    ExamGradingResult,
    DetectedQuestion,
    DetectedBubble,
)


class TestTypes(unittest.TestCase):

    def test_question_bounding_box_to_list(self):
        box = QuestionBoundingBox(x=10, y=20, w=100, h=30)
        self.assertEqual(box.to_list(), [10, 20, 100, 30])

    def test_omr_reading_result_to_dict(self):
        res = OMRReadingResult(
            status=OMRStatus.OK,
            prova_id=1,
            aluno_id=10,
            qr_valid=True,
            respostas={"1": "A", "2": "B"},
            mensagem="OK"
        )
        d = res.to_dict()
        self.assertEqual(d["status"], "OK")
        self.assertEqual(d["aluno_id"], 10)
        self.assertEqual(d["prova_id"], 1)
        self.assertTrue(d["qr_valid"])
        self.assertEqual(d["respostas"], {"1": "A", "2": "B"})
        self.assertEqual(d["mensagem"], "OK")

    def test_exam_grading_result_to_dict(self):
        res = ExamGradingResult(
            status=OMRStatus.OK,
            nota_final=10.0,
            acertos=5,
            total_questoes=5,
            respostas={"1": "A"},
            mensagem="Sucesso"
        )
        d = res.to_dict()
        self.assertEqual(d["status"], "OK")
        self.assertEqual(d["nota_final"], 10.0)
        self.assertEqual(d["acertos"], 5)
        self.assertEqual(d["total_questoes"], 5)
        self.assertEqual(d["mensagem"], "Sucesso")


if __name__ == "__main__":
    unittest.main()
