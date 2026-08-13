"""
Core OMR OpenCV Engine for Perspective Calibration, QR Code Reading,
Dynamic Bubble Sampling (1-3 cols, 3-5 options), Custom Sensitivity Slider,
and Automatic Grading with Bounding Box Coordinates for Audit.
"""

import os
import cv2
import numpy as np
from datetime import datetime
from omr_app.core.security import verify_and_decode_qr_payload

# Target dimensions for warped perspective canvas (A4 ratio)
WARP_WIDTH = 1000
WARP_HEIGHT = 1414


class OMREngine:
    """
    OpenCV-based OMR Scanner and Grader.
    """

    def __init__(self, scans_dir: str = None):
        if not scans_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            scans_dir = os.path.join(base_dir, "scans")
        os.makedirs(scans_dir, exist_ok=True)
        self.scans_dir = scans_dir
        self.qr_detector = cv2.QRCodeDetector()

    def process_sheet_image(
        self,
        image_bgr: np.ndarray,
        expected_prova_id: int = None,
        gabarito_dict: dict = None,
        valor_total: float = 10.0,
        num_questions: int = 10,
        num_options: int = 5,
        colunas: int = 2,
        sensitivity_pct: float = 45.0
    ) -> dict:
        """
        Processes a single scanned sheet image.
        Returns a dict with extracted info, answers, score, status, annotated image path, and question bounding boxes.
        """
        if image_bgr is None or image_bgr.size == 0:
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
                "mensagem": "Imagem inválida ou vazia."
            }

        # 1. Perspective Warp based on 4 Corner Crop Marks
        warped_bgr, warp_success = self._warp_perspective(image_bgr)
        if not warp_success:
            warped_bgr = cv2.resize(image_bgr, (WARP_WIDTH, WARP_HEIGHT))

        # 2. QR Code Decoding & SHA256 Hash Verification
        qr_valid, prova_id_qr, aluno_id_qr = self._read_qr_code(warped_bgr)

        prova_id = prova_id_qr if qr_valid else expected_prova_id
        aluno_id = aluno_id_qr if qr_valid else None

        # 3. Read OMR Bubble Grid with Custom Sensitivity
        respostas_marcadas, debug_bubbles = self._read_bubble_grid(
            warped_bgr,
            num_questions=num_questions,
            num_options=num_options,
            colunas=colunas,
            sensitivity_pct=sensitivity_pct
        )

        # 4. Automatic Grading & Rule Evaluation
        acertos = 0
        status = "OK"
        detalhes_status = []
        flagged_boxes = []  # list of dicts with question bounding box coords for audit UI

        if not qr_valid:
            status = "REVISAO_NECESSARIA"
            detalhes_status.append("QR Code não identificado ou hash de segurança inválido (clonagem/adulteração).")

        if gabarito_dict:
            for q_str, resp_lid in respostas_marcadas.items():
                gab_resp = gabarito_dict.get(q_str, "")

                if "|" in resp_lid:
                    status = "REVISAO_NECESSARIA"
                    detalhes_status.append(f"Questão {q_str}: Dupla marcação ({resp_lid}).")
                elif resp_lid == "-":
                    pass  # Blank answer
                elif resp_lid == gab_resp:
                    acertos += 1

                # Extract bounding box for flagged question
                if "|" in resp_lid or not qr_valid:
                    q_num = int(q_str)
                    box = self._get_question_bounding_box(q_num, num_questions, num_options, colunas)
                    flagged_boxes.append({"question": q_str, "box": box, "reason": resp_lid})
        else:
            status = "REVISAO_NECESSARIA"
            detalhes_status.append("Gabarito não fornecido.")

        nota_final = (acertos / num_questions) * valor_total if num_questions > 0 else 0.0

        # 5. Draw Visual Overlay
        annotated_bgr = self._annotate_image(
            warped_bgr, respostas_marcadas, gabarito_dict, debug_bubbles
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        annotated_filename = f"scan_{prova_id}_{aluno_id}_{timestamp}.png"
        annotated_path = os.path.join(self.scans_dir, annotated_filename)
        cv2.imwrite(annotated_path, annotated_bgr)

        return {
            "status": status,
            "aluno_id": aluno_id,
            "prova_id": prova_id,
            "nota_final": round(nota_final, 2),
            "acertos": acertos,
            "total_questoes": num_questions,
            "respostas": respostas_marcadas,
            "flagged_boxes": flagged_boxes,
            "annotated_path": annotated_path,
            "mensagem": " | ".join(detalhes_status) if detalhes_status else "Correção efetuada com sucesso."
        }

    def _warp_perspective(self, img: np.ndarray) -> tuple[np.ndarray, bool]:
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        min_area = (w * h) * 0.0001
        max_area = (w * h) * 0.02

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
                if len(approx) == 4:
                    x, y, cw, ch = cv2.boundingRect(approx)
                    aspect_ratio = float(cw) / ch if ch > 0 else 0
                    if 0.7 <= aspect_ratio <= 1.3:
                        M = cv2.moments(cnt)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            candidates.append((cx, cy))

        if len(candidates) >= 4:
            candidates = sorted(candidates, key=lambda p: (p[1], p[0]))
            top_two = sorted(candidates[:2], key=lambda p: p[0])
            bottom_two = sorted(candidates[-2:], key=lambda p: p[0])

            tl, tr = top_two[0], top_two[1]
            bl, br = bottom_two[0], bottom_two[1]

            pts1 = np.float32([tl, tr, br, bl])
            pts2 = np.float32([[0, 0], [WARP_WIDTH, 0], [WARP_WIDTH, WARP_HEIGHT], [0, WARP_HEIGHT]])

            M = cv2.getPerspectiveTransform(pts1, pts2)
            warped = cv2.warpPerspective(img, M, (WARP_WIDTH, WARP_HEIGHT))
            return warped, True

        return img, False

    def _read_qr_code(self, img: np.ndarray) -> tuple[bool, int, int]:
        try:
            h, w = img.shape[:2]
            top_region = img[0:int(h * 0.35), int(w * 0.45):w]

            decoded_text, _, _ = self.qr_detector.detectAndDecode(top_region)
            if not decoded_text:
                decoded_text, _, _ = self.qr_detector.detectAndDecode(img)

            if decoded_text:
                return verify_and_decode_qr_payload(decoded_text)
        except Exception:
            pass

        return False, 0, 0

    def _read_bubble_grid(
        self,
        img: np.ndarray,
        num_questions: int = 10,
        num_options: int = 5,
        colunas: int = 2,
        sensitivity_pct: float = 45.0
    ) -> tuple[dict, list]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        cols = max(1, min(3, colunas))
        q_per_col = (num_questions + cols - 1) // cols
        options_letters = ["A", "B", "C", "D", "E"][:num_options]

        threshold_ratio = sensitivity_pct / 100.0

        respostas = {}
        debug_bubbles = []

        grid_top_y = 525
        grid_height = 780
        row_step = grid_height / max(q_per_col, 1)

        # Horizontal positioning based on 1, 2, or 3 columns
        for q in range(1, num_questions + 1):
            col_idx = (q - 1) // q_per_col
            q_in_col = (q - 1) % q_per_col

            if cols == 3:
                col_x_start = 110 + (col_idx * 280)
                opt_spacing = 38
                r = 10
            elif cols == 2:
                col_x_start = 120 + (col_idx * 450)
                opt_spacing = 52
                r = 12
            else:
                col_x_start = 180
                opt_spacing = 70
                r = 14

            row_y = grid_top_y + int(q_in_col * row_step)

            option_fills = []

            for opt_idx, letter in enumerate(options_letters):
                cx = col_x_start + 90 + (opt_idx * opt_spacing)
                cy = row_y

                y1, y2 = max(0, cy - r), min(WARP_HEIGHT, cy + r)
                x1, x2 = max(0, cx - r), min(WARP_WIDTH, cx + r)

                roi = thresh[y1:y2, x1:x2]
                total_pixels = roi.size
                dark_pixels = cv2.countNonZero(roi) if total_pixels > 0 else 0
                ratio = dark_pixels / float(total_pixels) if total_pixels > 0 else 0.0

                option_fills.append((letter, ratio, cx, cy))

            # Apply sensitivity threshold
            marked_opts = [opt for opt, fill_ratio, cx, cy in option_fills if fill_ratio >= threshold_ratio]

            if len(marked_opts) == 1:
                respostas[str(q)] = marked_opts[0]
            elif len(marked_opts) > 1:
                respostas[str(q)] = "|".join(marked_opts)
            else:
                respostas[str(q)] = "-"

            debug_bubbles.append((str(q), option_fills))

        return respostas, debug_bubbles

    def _get_question_bounding_box(
        self, q_num: int, num_questions: int, num_options: int, colunas: int
    ) -> list[int]:
        """Calculates exact bounding box [x, y, w, h] for a given question row."""
        cols = max(1, min(3, colunas))
        q_per_col = (num_questions + cols - 1) // cols

        col_idx = (q_num - 1) // q_per_col
        q_in_col = (q_num - 1) % q_per_col

        grid_top_y = 525
        grid_height = 780
        row_step = grid_height / max(q_per_col, 1)

        row_y = grid_top_y + int(q_in_col * row_step)

        if cols == 3:
            col_x_start = 110 + (col_idx * 280)
            box_w = 260
        elif cols == 2:
            col_x_start = 120 + (col_idx * 450)
            box_w = 400
        else:
            col_x_start = 180
            box_w = 550

        x = col_x_start - 20
        y = row_y - 15
        w = box_w
        h = max(24, int(row_step))

        return [x, y, w, h]

    def _annotate_image(
        self,
        img: np.ndarray,
        respostas: dict,
        gabarito: dict,
        debug_bubbles: list
    ) -> np.ndarray:
        annotated = img.copy()

        for q_str, option_fills in debug_bubbles:
            gab_ans = gabarito.get(q_str, "") if gabarito else ""
            marked_ans = respostas.get(q_str, "-")

            for letter, ratio, cx, cy in option_fills:
                color = (200, 200, 200)
                thickness = 1

                if letter in marked_ans.split("|"):
                    if "|" in marked_ans:
                        color = (0, 215, 255)  # Yellow for double mark
                        thickness = 3
                    elif gab_ans and letter == gab_ans:
                        color = (0, 200, 0)    # Green for correct
                        thickness = 3
                    elif gab_ans and letter != gab_ans:
                        color = (0, 0, 255)    # Red for wrong choice
                        thickness = 3

                cv2.circle(annotated, (cx, cy), 13, color, thickness)

        return annotated
