"""
Unified Geometric Layout Representation for Answer Sheets.
Shared between OMR Image Reader and PDF Generator.
Single source of truth for grid calculations and coordinate space transformations.
"""

from typing import Optional
from omr_app.core.config import OMRConfig, DEFAULT_OMR_CONFIG
from omr_app.core.types import QuestionBoundingBox


class SheetLayout:
    """
    Centralized Sheet Geometry Model for 1-4 columns and 3-5 options.
    Calculates bubble center coordinates and bounding boxes in both:
    1. ReportLab PDF Space (A4 page points: 595.27 x 841.89 pt, origin at bottom-left).
    2. OpenCV Canvas Space (Normalized image pixels: 1000 x 1414, origin at top-left).
    """

    # Page and Crop Mark Constants (ReportLab PDF points)
    PDF_PAGE_WIDTH = 595.27
    PDF_PAGE_HEIGHT = 841.89
    CROP_MARGIN_X = 28.35   # 1 cm
    CROP_MARGIN_Y = 28.35   # 1 cm
    CROP_MARK_SIZE = 28.35  # 1 cm

    # Bounding rectangle of 4 corner crop mark centers (ReportLab PDF points)
    X_CROP_MIN = CROP_MARGIN_X + CROP_MARK_SIZE / 2.0         # 42.525 pt
    X_CROP_MAX = PDF_PAGE_WIDTH - CROP_MARGIN_X - CROP_MARK_SIZE / 2.0 # 552.745 pt
    Y_CROP_MIN = CROP_MARGIN_Y + CROP_MARK_SIZE / 2.0         # 42.525 pt
    Y_CROP_MAX = PDF_PAGE_HEIGHT - CROP_MARGIN_Y - CROP_MARK_SIZE / 2.0# 799.365 pt

    CROP_WIDTH_PT = X_CROP_MAX - X_CROP_MIN    # 510.22 pt
    CROP_HEIGHT_PT = Y_CROP_MAX - Y_CROP_MIN   # 756.84 pt

    # Grid Specs for PDF layout per column count
    COLUMN_SPECS = {
        4: {"bubble_radius": 4.5, "option_spacing": 15.0, "label_offset_x": 35.0, "col_x_offset": 8.0},
        3: {"bubble_radius": 5.5, "option_spacing": 20.0, "label_offset_x": 42.0, "col_x_offset": 12.0},
        2: {"bubble_radius": 7.0, "option_spacing": 26.0, "label_offset_x": 55.0, "col_x_offset": 12.0},
        1: {"bubble_radius": 8.0, "option_spacing": 35.0, "label_offset_x": 70.0, "col_x_offset": 12.0},
    }

    def __init__(
        self,
        num_questions: int = 10,
        num_options: int = 5,
        colunas: int = 2,
        config: Optional[OMRConfig] = None
    ):
        if not isinstance(num_questions, int) or num_questions < 1:
            raise ValueError(f"num_questions deve ser um numero inteiro >= 1, recebido: {num_questions}")
        if not isinstance(num_options, int) or num_options not in (3, 4, 5):
            raise ValueError(f"num_options deve ser 3, 4 ou 5, recebido: {num_options}")
        if not isinstance(colunas, int) or colunas not in (1, 2, 3, 4):
            raise ValueError(f"colunas deve ser 1, 2, 3 ou 4, recebido: {colunas}")

        self.num_questions = num_questions
        self.num_options = num_options
        self.colunas = colunas
        self.config = config if config is not None else DEFAULT_OMR_CONFIG

        self.q_per_col = (self.num_questions + self.colunas - 1) // self.colunas
        self.options_letters = ["A", "B", "C", "D", "E"][:self.num_options]

        # PDF Grid Layout Parameters
        self.grid_box_x = 65.0
        self.grid_box_w = self.PDF_PAGE_WIDTH - 130.0  # 465.27 pt
        self.grid_start_y = self.PDF_PAGE_HEIGHT - 300.0  # 541.89 pt
        self.grid_top_y = self.grid_start_y - 45.0       # 496.89 pt (Label Y)
        self.first_row_y = self.grid_top_y - 22.0        # 474.89 pt (First Question Y)

        self.col_width = self.grid_box_w / float(self.colunas)
        self.available_height = self.grid_top_y - 80.0
        self.row_height = min(24.0, self.available_height / max(self.q_per_col, 1))

        self.spec = self.COLUMN_SPECS[self.colunas]
        self.bubble_radius_pt = self.spec["bubble_radius"]
        self.option_spacing_pt = self.spec["option_spacing"]
        self.label_offset_x_pt = self.spec["label_offset_x"]
        self.col_x_offset_pt = self.spec["col_x_offset"]

    def canvas_to_pdf(self, x_canvas: float, y_canvas: float) -> tuple[float, float]:
        """Converts canvas pixel coordinates (1000x1414) to PDF page points (A4)."""
        x_pdf = self.X_CROP_MIN + (x_canvas / self.config.warp_width) * self.CROP_WIDTH_PT
        y_pdf = self.Y_CROP_MAX - (y_canvas / self.config.warp_height) * self.CROP_HEIGHT_PT
        return x_pdf, y_pdf

    def pdf_to_canvas(self, x_pdf: float, y_pdf: float) -> tuple[float, float]:
        """Converts PDF page points (A4) to canvas pixel coordinates (1000x1414)."""
        x_canvas = ((x_pdf - self.X_CROP_MIN) / self.CROP_WIDTH_PT) * self.config.warp_width
        y_canvas = ((self.Y_CROP_MAX - y_pdf) / self.CROP_HEIGHT_PT) * self.config.warp_height
        return x_canvas, y_canvas

    def get_column_x_start_pdf(self, col_idx: int) -> float:
        """Returns starting X coordinate in PDF points for column index."""
        return self.grid_box_x + (col_idx * self.col_width) + self.col_x_offset_pt

    def get_question_row_y_pdf(self, q_num: int) -> tuple[int, int, float]:
        """Returns (col_idx, q_in_col, row_y_pdf) for a 1-indexed question number."""
        q_idx = q_num - 1
        col_idx = q_idx // self.q_per_col
        q_in_col = q_idx % self.q_per_col
        row_y_pdf = self.first_row_y - (q_in_col * self.row_height)
        return col_idx, q_in_col, row_y_pdf

    def get_bubble_pdf_center(self, q_num: int, opt_idx: int) -> tuple[float, float, float]:
        """Returns (bx_pdf, by_pdf, radius_pt) in PDF page points."""
        col_idx, _, row_y_pdf = self.get_question_row_y_pdf(q_num)
        col_x_start_pdf = self.get_column_x_start_pdf(col_idx)

        bx_pdf = col_x_start_pdf + self.label_offset_x_pt + (opt_idx * self.option_spacing_pt)
        by_pdf = row_y_pdf + 2.5
        r_pdf = self.bubble_radius_pt
        return bx_pdf, by_pdf, r_pdf

    def get_bubble_center(self, q_num: int, opt_idx: int) -> tuple[int, int, int]:
        """
        Returns (cx, cy, radius) in canvas pixel coordinates (1000x1414).
        """
        bx_pdf, by_pdf, r_pdf = self.get_bubble_pdf_center(q_num, opt_idx)
        cx_canvas, cy_canvas = self.pdf_to_canvas(bx_pdf, by_pdf)
        scale_x = self.config.warp_width / self.CROP_WIDTH_PT
        r_canvas = int(round(r_pdf * scale_x))
        return int(round(cx_canvas)), int(round(cy_canvas)), r_canvas

    def get_column_x_start(self, col_idx: int) -> int:
        """Returns starting X coordinate in canvas pixels for column index."""
        col_x_pdf = self.get_column_x_start_pdf(col_idx)
        cx, _ = self.pdf_to_canvas(col_x_pdf, self.grid_top_y)
        return int(round(cx))

    def get_question_row_y(self, q_num: int) -> tuple[int, int, int]:
        """Returns (col_idx, q_in_col, row_y_canvas) in canvas pixels."""
        col_idx, q_in_col, row_y_pdf = self.get_question_row_y_pdf(q_num)
        _, cy = self.pdf_to_canvas(self.X_CROP_MIN, row_y_pdf)
        return col_idx, q_in_col, int(round(cy))

    def get_question_bounding_box(self, q_num: int) -> QuestionBoundingBox:
        """
        Returns QuestionBoundingBox in canvas pixels.
        """
        col_idx, _, row_y_pdf = self.get_question_row_y_pdf(q_num)
        col_x_start_pdf = self.get_column_x_start_pdf(col_idx)

        x_pdf = col_x_start_pdf - 4.0
        y_top_pdf = row_y_pdf + (self.row_height / 2.0)
        y_bot_pdf = row_y_pdf - (self.row_height / 2.0)
        w_pdf = self.col_width - 8.0

        x_left_canvas, y_top_canvas = self.pdf_to_canvas(x_pdf, y_top_pdf)
        x_right_canvas, y_bot_canvas = self.pdf_to_canvas(x_pdf + w_pdf, y_bot_pdf)

        x = int(round(x_left_canvas))
        y = int(round(y_top_canvas))
        w = max(10, int(round(x_right_canvas - x_left_canvas)))
        h = max(10, int(round(y_bot_canvas - y_top_canvas)))

        return QuestionBoundingBox(x=x, y=y, w=w, h=h)
