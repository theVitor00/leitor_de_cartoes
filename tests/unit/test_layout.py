"""
Unit tests for SheetLayout geometry calculation, coordinate conversion, and parameter validation.
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
        self.assertGreater(r1, 0)
        self.assertGreater(cy1, 0)

        # Q6 is in col 1, row 0
        cx6, cy6, r6 = layout.get_bubble_center(q_num=6, opt_idx=0)
        self.assertEqual(cy6, cy1)
        self.assertGreater(cx6, cx1)

    def test_bounding_box_format(self):
        layout = SheetLayout(num_questions=20, num_options=5, colunas=4)
        box = layout.get_question_bounding_box(q_num=1)
        self.assertEqual(len(box.to_list()), 4)
        self.assertGreater(box.w, 0)
        self.assertGreater(box.h, 0)

    def test_coordinate_space_transformations(self):
        layout = SheetLayout(num_questions=10, num_options=5, colunas=2)
        # Test crop mark corners mapping
        # Top-Left crop mark center in PDF: (42.525, 799.365) -> Canvas: (0, 0)
        cx_tl, cy_tl = layout.pdf_to_canvas(layout.X_CROP_MIN, layout.Y_CROP_MAX)
        self.assertAlmostEqual(cx_tl, 0.0, delta=0.01)
        self.assertAlmostEqual(cy_tl, 0.0, delta=0.01)

        # Bottom-Right crop mark center in PDF: (552.745, 42.525) -> Canvas: (1000, 1414)
        cx_br, cy_br = layout.pdf_to_canvas(layout.X_CROP_MAX, layout.Y_CROP_MIN)
        self.assertAlmostEqual(cx_br, 1000.0, delta=0.01)
        self.assertAlmostEqual(cy_br, 1414.0, delta=0.01)

        # Bi-directional roundtrip check
        pdf_x, pdf_y = layout.canvas_to_pdf(cx_tl, cy_tl)
        self.assertAlmostEqual(pdf_x, layout.X_CROP_MIN, delta=0.01)
        self.assertAlmostEqual(pdf_y, layout.Y_CROP_MAX, delta=0.01)

    def test_invalid_parameters_raise_value_error(self):
        with self.assertRaises(ValueError):
            SheetLayout(num_questions=0, num_options=5, colunas=2)

        with self.assertRaises(ValueError):
            SheetLayout(num_questions=10, num_options=2, colunas=2)

        with self.assertRaises(ValueError):
            SheetLayout(num_questions=10, num_options=6, colunas=2)

        with self.assertRaises(ValueError):
            SheetLayout(num_questions=10, num_options=5, colunas=5)

    def test_multiple_column_configurations(self):
        for cols in [1, 2, 3, 4]:
            for opts in [3, 4, 5]:
                layout = SheetLayout(num_questions=12, num_options=opts, colunas=cols)
                self.assertEqual(len(layout.options_letters), opts)
                cx, cy, r = layout.get_bubble_center(1, 0)
                self.assertGreater(cx, 0)
                self.assertGreater(cy, 0)
                self.assertGreater(r, 0)


if __name__ == "__main__":
    unittest.main()
