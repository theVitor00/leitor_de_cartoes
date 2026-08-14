"""
Core OMR OpenCV Engine for Perspective Calibration, QR Code Reading,
Dynamic Bubble Sampling using SheetLayout, and Exam Grading.
"""

import os
from datetime import datetime
from typing import Optional
import cv2
import numpy as np

from omr_app.core.config import OMRConfig, DEFAULT_OMR_CONFIG
from omr_app.core.layout import SheetLayout
from omr_app.core.types import (
    OMRStatus, OMRReadingResult, DetectedQuestion, DetectedBubble
)
from omr_app.core.grader import ExamGrader
from omr_app.core.security import verify_and_decode_qr_payload

# Legacy export constants for backwards compatibility
WARP_WIDTH = DEFAULT_OMR_CONFIG.warp_width
WARP_HEIGHT = DEFAULT_OMR_CONFIG.warp_height


class OMREngine:
    """
    OpenCV-based OMR Scanner and Image Reader.
    Refactored to separate OMR reading from Exam Grading.
    """

    def __init__(self, scans_dir: Optional[str] = None, config: Optional[OMRConfig] = None):
        if not scans_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            scans_dir = os.path.join(base_dir, "scans")
        os.makedirs(scans_dir, exist_ok=True)
        self.scans_dir = scans_dir
        self.config = config if config is not None else DEFAULT_OMR_CONFIG
        self.qr_detector = cv2.QRCodeDetector()

    def read_sheet(
        self,
        image_bgr: np.ndarray,
        expected_prova_id: Optional[int] = None,
        num_questions: int = 10,
        num_options: int = 5,
        colunas: int = 2,
        sensitivity_pct: float = 45.0
    ) -> OMRReadingResult:
        """
        Pure OMR Extraction Pipeline:
        1. Image Validation
        2. Perspective Calibration & Canvas Normalization
        3. QR Code Decoding
        4. Bubble Grid Reading (via SheetLayout)
        5. Visual Annotation
        """
        # 1. Validation
        if image_bgr is None or image_bgr.size == 0:
            return OMRReadingResult(
                status=OMRStatus.INVALID_IMAGE,
                prova_id=expected_prova_id,
                aluno_id=None,
                qr_valid=False,
                respostas={},
                mensagem="Imagem inválida ou vazia."
            )

        layout = SheetLayout(
            num_questions=num_questions,
            num_options=num_options,
            colunas=colunas,
            config=self.config
        )

        # 2. Perspective Warp
        warped_bgr, warp_success = self._warp_perspective(image_bgr)
        status = OMRStatus.OK
        detalhes: list[str] = []

        if not warp_success:
            warped_bgr = cv2.resize(image_bgr, (self.config.warp_width, self.config.warp_height))
            status = OMRStatus.PERSPECTIVE_ERROR
            detalhes.append("Marcadores de perspectiva não encontrados ou desalinhados. Geometria não confiável.")

        # 3. QR Code Reading
        qr_valid, prova_id_qr, aluno_id_qr = self._read_qr_code(warped_bgr)
        prova_id = prova_id_qr if qr_valid else expected_prova_id
        aluno_id = aluno_id_qr if qr_valid else None

        if not qr_valid:
            if status == OMRStatus.OK:
                status = OMRStatus.REVISAO_NECESSARIA
            detalhes.append("QR Code não identificado ou hash de segurança inválido.")

        # 4. Bubble Grid Extraction
        respostas, detected_questions, debug_bubbles = self._read_bubble_grid(
            warped_bgr,
            layout=layout,
            sensitivity_pct=sensitivity_pct
        )

        return OMRReadingResult(
            status=status,
            prova_id=prova_id,
            aluno_id=aluno_id,
            qr_valid=qr_valid,
            respostas=respostas,
            detected_questions=detected_questions,
            warped_image=warped_bgr,
            mensagem=" | ".join(detalhes) if detalhes else "Leitura efetuada com sucesso."
        )

    def process_sheet_image(
        self,
        image_bgr: np.ndarray,
        expected_prova_id: Optional[int] = None,
        gabarito_dict: Optional[dict] = None,
        valor_total: float = 10.0,
        num_questions: int = 10,
        num_options: int = 5,
        colunas: int = 2,
        sensitivity_pct: float = 45.0
    ) -> dict:
        """
        Full end-to-end process: OMR Sheet Reading + Exam Grading + Visual Annotation.
        Maintains complete backwards compatibility by returning a dictionary.
        """
        # Step A: Perform OMR Reading
        reading_res = self.read_sheet(
            image_bgr=image_bgr,
            expected_prova_id=expected_prova_id,
            num_questions=num_questions,
            num_options=num_options,
            colunas=colunas,
            sensitivity_pct=sensitivity_pct
        )

        if reading_res.status == OMRStatus.INVALID_IMAGE:
            return {
                "status": "ERRO_LEITURA",
                "aluno_id": None,
                "prova_id": expected_prova_id,
                "nota_final": 0.0,
                "acertos": 0,
                "total_questoes": num_questions,
                "respostas": {},
                "flagged_boxes": [],
                "annotated_path": None,
                "mensagem": reading_res.mensagem
            }

        layout = SheetLayout(
            num_questions=num_questions,
            num_options=num_options,
            colunas=colunas,
            config=self.config
        )

        # Step B: Perform Exam Grading
        grading_res = ExamGrader.grade(
            respostas_marcadas=reading_res.respostas,
            gabarito_dict=gabarito_dict,
            valor_total=valor_total,
            num_questions=num_questions,
            layout=layout,
            qr_valid=reading_res.qr_valid
        )

        # Determine final combined status without hiding errors
        if reading_res.status in (OMRStatus.PERSPECTIVE_ERROR, OMRStatus.INVALID_IMAGE):
            final_status = reading_res.status.value
        elif reading_res.status != OMRStatus.OK:
            final_status = reading_res.status.value
        elif grading_res.status != OMRStatus.OK:
            final_status = grading_res.status.value
        else:
            final_status = OMRStatus.OK.value

        mensagens = []
        if reading_res.mensagem and "sucesso" not in reading_res.mensagem.lower():
            mensagens.append(reading_res.mensagem)
        if grading_res.mensagem and "sucesso" not in grading_res.mensagem.lower():
            mensagens.append(grading_res.mensagem)
        mensagem_final = " | ".join(mensagens) if mensagens else "Correção efetuada com sucesso."

        # Step C: Visual Annotation
        debug_bubbles = [
            (str(q.question_num), [(b.letter, b.fill_ratio, b.cx, b.cy) for b in q.options])
            for q in reading_res.detected_questions
        ]
        annotated_bgr = self._annotate_image(
            reading_res.warped_image, reading_res.respostas, gabarito_dict, debug_bubbles
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        p_id = reading_res.prova_id or expected_prova_id
        a_id = reading_res.aluno_id or 0
        annotated_filename = f"scan_{p_id}_{a_id}_{timestamp}.png"
        annotated_path = os.path.join(self.scans_dir, annotated_filename)
        cv2.imwrite(annotated_path, annotated_bgr)

        # If perspective calibration failed, do not produce a valid grade
        nota_final = grading_res.nota_final if reading_res.status == OMRStatus.OK else 0.0
        acertos = grading_res.acertos if reading_res.status == OMRStatus.OK else 0

        return {
            "status": final_status,
            "aluno_id": reading_res.aluno_id,
            "prova_id": reading_res.prova_id,
            "nota_final": nota_final,
            "acertos": acertos,
            "total_questoes": grading_res.total_questoes,
            "respostas": reading_res.respostas,
            "flagged_boxes": grading_res.flagged_boxes,
            "annotated_path": annotated_path,
            "mensagem": mensagem_final
        }

    def _warp_perspective(self, img: np.ndarray) -> tuple[np.ndarray, bool]:
        """
        Detects 4 corner crop marks, validates quadrant placement and area consistency,
        and warps perspective to normalized canvas (1000x1414).
        Returns (warped_image, success_boolean).
        """
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, self.config.gaussian_blur_kernel, 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, self.config.adaptive_thresh_block_size, self.config.adaptive_thresh_c
        )

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area = (w * h) * self.config.min_marker_area_ratio
        max_area = (w * h) * self.config.max_marker_area_ratio

        # Partition candidates into 4 corner quadrants
        quad_tl, quad_tr, quad_bl, quad_br = [], [], [], []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
                if 4 <= len(approx) <= 8:
                    _, _, cw, ch = cv2.boundingRect(approx)
                    aspect_ratio = float(cw) / ch if ch > 0 else 0
                    if self.config.marker_aspect_ratio_min <= aspect_ratio <= self.config.marker_aspect_ratio_max:
                        M = cv2.moments(cnt)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            cand = (cx, cy, area)

                            if cx < 0.45 * w and cy < 0.45 * h:
                                quad_tl.append(cand)
                            elif cx > 0.55 * w and cy < 0.45 * h:
                                quad_tr.append(cand)
                            elif cx < 0.45 * w and cy > 0.55 * h:
                                quad_bl.append(cand)
                            elif cx > 0.55 * w and cy > 0.55 * h:
                                quad_br.append(cand)

        # Must find candidates in all 4 corner quadrants
        if quad_tl and quad_tr and quad_bl and quad_br:
            tl = min(quad_tl, key=lambda c: (c[0]**2 + c[1]**2))
            tr = min(quad_tr, key=lambda c: ((w - c[0])**2 + c[1]**2))
            bl = min(quad_bl, key=lambda c: (c[0]**2 + (h - c[1])**2))
            br = min(quad_br, key=lambda c: ((w - c[0])**2 + (h - c[1])**2))

            selected = [tl, tr, br, bl]
            areas = [c[2] for c in selected]
            max_a, min_a = max(areas), min(areas)

            # Marker size consistency validation across corners
            if min_a > 0 and (max_a / min_a) <= 3.5:
                pts1 = np.float32([[tl[0], tl[1]], [tr[0], tr[1]], [br[0], br[1]], [bl[0], bl[1]]])
                pts2 = np.float32([
                    [0, 0],
                    [self.config.warp_width, 0],
                    [self.config.warp_width, self.config.warp_height],
                    [0, self.config.warp_height]
                ])

                M = cv2.getPerspectiveTransform(pts1, pts2)
                warped = cv2.warpPerspective(img, M, (self.config.warp_width, self.config.warp_height))
                return warped, True

        return img, False

    def _read_qr_code(self, img: np.ndarray) -> tuple[bool, int, int]:
        """Reads and decodes QR Code in top right region of normalized canvas."""
        try:
            h, w = img.shape[:2]
            crop_h = int(h * self.config.qr_crop_height_ratio)
            crop_w = int(w * self.config.qr_crop_width_start_ratio)
            top_region = img[0:crop_h, crop_w:w]

            decoded_text, _, _ = self.qr_detector.detectAndDecode(top_region)
            if not decoded_text:
                decoded_text, _, _ = self.qr_detector.detectAndDecode(img)

            if decoded_text:
                return verify_and_decode_qr_payload(decoded_text)
        except cv2.error as e:
            pass
        except Exception:
            pass

        return False, 0, 0

    def _read_bubble_grid(
        self,
        img: np.ndarray,
        layout: SheetLayout,
        sensitivity_pct: float = 45.0
    ) -> tuple[dict[str, str], list[DetectedQuestion], list]:
        """Reads OMR bubble grid using geometry from SheetLayout."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        threshold_ratio = sensitivity_pct / 100.0
        respostas = {}
        detected_questions = []
        debug_bubbles = []

        for q in range(1, layout.num_questions + 1):
            option_fills = []
            detected_bubbles = []

            for opt_idx, letter in enumerate(layout.options_letters):
                cx, cy, r = layout.get_bubble_center(q, opt_idx)

                y1, y2 = max(0, cy - r), min(self.config.warp_height, cy + r)
                x1, x2 = max(0, cx - r), min(self.config.warp_width, cx + r)

                roi = thresh[y1:y2, x1:x2]
                total_pixels = roi.size
                dark_pixels = cv2.countNonZero(roi) if total_pixels > 0 else 0
                ratio = dark_pixels / float(total_pixels) if total_pixels > 0 else 0.0

                option_fills.append((letter, ratio, cx, cy))
                detected_bubbles.append(DetectedBubble(letter=letter, fill_ratio=ratio, cx=cx, cy=cy))

            marked_opts = [opt for opt, fill_ratio, cx, cy in option_fills if fill_ratio >= threshold_ratio]

            if len(marked_opts) == 1:
                ans_str = marked_opts[0]
            elif len(marked_opts) > 1:
                ans_str = "|".join(marked_opts)
            else:
                ans_str = "-"

            q_str = str(q)
            respostas[q_str] = ans_str
            debug_bubbles.append((q_str, option_fills))

            q_box = layout.get_question_bounding_box(q)
            detected_questions.append(
                DetectedQuestion(
                    question_num=q,
                    marked_answer=ans_str,
                    options=detected_bubbles,
                    box=q_box
                )
            )

        return respostas, detected_questions, debug_bubbles

    def _get_question_bounding_box(
        self, q_num: int, num_questions: int, num_options: int, colunas: int
    ) -> list[int]:
        """Legacy helper for question bounding box calculation."""
        layout = SheetLayout(
            num_questions=num_questions,
            num_options=num_options,
            colunas=colunas,
            config=self.config
        )
        return layout.get_question_bounding_box(q_num).to_list()

    def _annotate_image(
        self,
        img: np.ndarray,
        respostas: dict,
        gabarito: Optional[dict],
        debug_bubbles: list
    ) -> np.ndarray:
        """Draws debugging overlay onto the scanned sheet image."""
        annotated = img.copy()

        for q_str, option_fills in debug_bubbles:
            gab_ans = gabarito.get(q_str, "") if gabarito else ""
            marked_ans = respostas.get(q_str, "-")

            for letter, ratio, cx, cy in option_fills:
                color = (200, 200, 200)
                thickness = 1

                if letter in marked_ans.split("|"):
                    if "|" in marked_ans:
                        color = (0, 215, 255)  # Cyan/Yellow for double mark
                        thickness = 3
                    elif gab_ans and letter == gab_ans:
                        color = (0, 200, 0)    # Green for correct
                        thickness = 3
                    elif gab_ans and letter != gab_ans:
                        color = (0, 0, 255)    # Red for incorrect
                        thickness = 3

                cv2.circle(annotated, (cx, cy), 11, color, thickness)

        return annotated
