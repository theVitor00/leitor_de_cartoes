"""
Unified Geometric Layout Representation for Answer Sheets.
Shared between OMR Image Reader and PDF Generator.
"""

from dataclasses import dataclass
from omr_app.core.config import OMRConfig, DEFAULT_OMR_CONFIG
from omr_app.core.types import QuestionBoundingBox


@dataclass
class ColumnLayoutSpecs:
    """Column grid parameters for a specific column count (1, 2, 3, 4)."""
    col_x_start_base: int
    col_x_stride: int
    opt_spacing: int
    bubble_radius: int
    label_offset_x: int
    box_width: int


class SheetLayout:
    """
    Centralized Sheet Geometry Model for 1-4 columns and 3-5 options.
    Calculates bubble sample center coordinates and bounding boxes on the normalized canvas.
    """

    # Grid specs for normalized canvas (1000 x 1414)
    SPECS = {
        4: ColumnLayoutSpecs(col_x_start_base=80,  col_x_stride=210, opt_spacing=30, bubble_radius=8,  label_offset_x=60, box_width=200),
        3: ColumnLayoutSpecs(col_x_start_base=110, col_x_stride=280, opt_spacing=38, bubble_radius=10, label_offset_x=90, box_width=260),
        2: ColumnLayoutSpecs(col_x_start_base=120, col_x_stride=450, opt_spacing=52, bubble_radius=12, label_offset_x=90, box_width=400),
        1: ColumnLayoutSpecs(col_x_start_base=180, col_x_stride=0,   opt_spacing=70, bubble_radius=14, label_offset_x=90, box_width=550),
    }

    def __init__(
        self,
        num_questions: int = 10,
        num_options: int = 5,
        colunas: int = 2,
        config: OMRConfig = DEFAULT_OMR_CONFIG
    ):
        self.num_questions = max(1, num_questions)
        self.num_options = max(3, min(5, num_options))
        self.colunas = max(1, min(4, colunas))
        self.config = config

        self.q_per_col = (self.num_questions + self.colunas - 1) // self.colunas
        self.options_letters = ["A", "B", "C", "D", "E"][:self.num_options]

        # Vertical grid bounds on normalized canvas (1000 x 1414)
        self.grid_top_y = 525
        self.grid_height = 780
        self.row_step = self.grid_height / max(self.q_per_col, 1)

        self.col_specs = self.SPECS.get(self.colunas, self.SPECS[2])

    def get_column_x_start(self, col_idx: int) -> int:
        """Returns starting X coordinate for column index."""
        return self.col_specs.col_x_start_base + (col_idx * self.col_specs.col_x_stride)

    def get_question_row_y(self, q_num: int) -> tuple[int, int, int]:
        """
        Returns (col_idx, q_in_col, row_y) for a 1-indexed question number.
        """
        q_idx = q_num - 1
        col_idx = q_idx // self.q_per_col
        q_in_col = q_idx % self.q_per_col
        row_y = self.grid_top_y + int(q_in_col * self.row_step)
        return col_idx, q_in_col, row_y

    def get_bubble_center(self, q_num: int, opt_idx: int) -> tuple[int, int, int]:
        """
        Returns (cx, cy, radius) for a specific question number and option index.
        """
        col_idx, _, row_y = self.get_question_row_y(q_num)
        col_x_start = self.get_column_x_start(col_idx)

        cx = col_x_start + self.col_specs.label_offset_x + (opt_idx * self.col_specs.opt_spacing)
        cy = row_y
        r = self.col_specs.bubble_radius

        return cx, cy, r

    def get_question_bounding_box(self, q_num: int) -> QuestionBoundingBox:
        """
        Returns QuestionBoundingBox for visual audit flagging.
        """
        col_idx, _, row_y = self.get_question_row_y(q_num)
        col_x_start = self.get_column_x_start(col_idx)

        x = col_x_start - 15
        y = row_y - 15
        w = self.col_specs.box_width
        h = max(24, int(self.row_step))

        return QuestionBoundingBox(x=x, y=y, w=w, h=h)
