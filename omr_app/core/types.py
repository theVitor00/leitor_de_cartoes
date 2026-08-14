"""
Data structures, Enums, and Dataclasses representing OMR status and pipeline results.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional
import numpy as np


class OMRStatus(str, Enum):
    """Status enumeration for OMR Sheet Reading and Exam Grading."""
    OK = "OK"
    REVISAO_NECESSARIA = "REVISAO_NECESSARIA"
    ERRO_LEITURA = "ERRO_LEITURA"
    PERSPECTIVE_ERROR = "PERSPECTIVE_ERROR"
    QR_ERROR = "QR_ERROR"
    INVALID_IMAGE = "INVALID_IMAGE"


@dataclass
class QuestionBoundingBox:
    """Bounding box coordinates for a question on the OMR sheet [x, y, w, h]."""
    x: int
    y: int
    w: int
    h: int

    def to_list(self) -> list[int]:
        return [self.x, self.y, self.w, self.h]


@dataclass
class DetectedBubble:
    """Information for a single bubble option sample."""
    letter: str
    fill_ratio: float
    cx: int
    cy: int


@dataclass
class DetectedQuestion:
    """OMR reading output for a single question."""
    question_num: int
    marked_answer: str          # e.g., "A", "B|C", "-"
    options: list[DetectedBubble] = field(default_factory=list)
    box: Optional[QuestionBoundingBox] = None


@dataclass
class OMRReadingResult:
    """
    Data payload returned by OMR image reading phase (pure OMR extraction).
    """
    status: OMRStatus
    prova_id: Optional[int] = None
    aluno_id: Optional[int] = None
    qr_valid: bool = False
    respostas: dict[str, str] = field(default_factory=dict)
    detected_questions: list[DetectedQuestion] = field(default_factory=list)
    flagged_boxes: list[dict] = field(default_factory=list)
    annotated_path: Optional[str] = None
    warped_image: Optional[np.ndarray] = None
    mensagem: str = ""

    def to_dict() -> dict[str, Any]:
        """Converts result into backwards-compatible dict for existing GUI & legacy consumers."""
        return {
            "status": self.status.value if isinstance(self.status, Enum) else str(self.status),
            "aluno_id": self.aluno_id,
            "prova_id": self.prova_id,
            "qr_valid": self.qr_valid,
            "respostas": self.respostas,
            "flagged_boxes": self.flagged_boxes,
            "annotated_path": self.annotated_path,
            "mensagem": self.mensagem,
        }


@dataclass
class ExamGradingResult:
    """
    Data payload returned by Exam Grader (pure business logic grading phase).
    """
    status: OMRStatus
    nota_final: float
    acertos: int
    total_questoes: int
    respostas: dict[str, str]
    flagged_boxes: list[dict] = field(default_factory=list)
    detalhes_status: list[str] = field(default_factory=list)
    mensagem: str = ""

    def to_dict() -> dict[str, Any]:
        """Converts result into backwards-compatible dict."""
        return {
            "status": self.status.value if isinstance(self.status, Enum) else str(self.status),
            "nota_final": self.nota_final,
            "acertos": self.acertos,
            "total_questoes": self.total_questoes,
            "respostas": self.respostas,
            "flagged_boxes": self.flagged_boxes,
            "mensagem": self.mensagem,
        }
