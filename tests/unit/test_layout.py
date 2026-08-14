"""
Unit tests for SheetLayout geometry calculation.
"""

import unittest
from omr_app.core.layout import SheetLayout


class TestSheetLayout(unittest.TestCase):

    def test_2_columns_layout_bounds(self):
        layout = SheetLayout(num_questions=10, num_options=5, colunas=2)
        self.assertEqual(layout.q_per_col, 5)
        self.assertEqual(layout.options_letters, ["A", "B", "C", "D", "E"])

        # Q1 is in col 0, row 0
        cx1, cy1, r1 = layout.get_bubble_center(q_num=1, opt_idx=0)
        self.assertEqual(r1, 12)
        self.assertEqual(cy1, 525)

        # Q6 is in col 1, row 0
        cx6, cy6, r6 = layout.get_bubble_center(q_num=6, opt_idx=0)
        self.assertEqual(cy6, 525)
        self.assertGreater(cx6, cx1)

    def test_bounding_box_format(self):
        layout = SheetLayout(num_questions=20, num_options=5, colunas=4)
        box = layout.get_question_bounding_box(q_num=1)
        self.assertEqual(len(box.to_list()), 4)
        self.assertGreater(box.w, 0)
        self.assertGreater(box.h, 0)


if __name__ == "__main__":
    unittest.main()
