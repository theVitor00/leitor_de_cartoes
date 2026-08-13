"""
PDF Answer Sheet Generator using ReportLab.
Renders precise vector OMR answer sheets with 4 corner crop marks,
QR Code, institutional headers, instruction boxes, and bubble grids.
"""

import os
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.barcode import qr
from omr_app.core.security import generate_qr_payload

# Colors
TEAL_HEX = colors.HexColor("#00AEA7")
NAVY_HEX = colors.HexColor("#002970")
DARK_GRAY = colors.HexColor("#1E293B")
LIGHT_GRAY = colors.HexColor("#F1F5F9")
BORDER_GRAY = colors.HexColor("#CBD5E1")

# A4 dimensions in points (595.27 x 841.89)
PAGE_WIDTH, PAGE_HEIGHT = A4


class OMRPDFGenerator:
    """
    Generates vectorized PDF OMR Answer Sheets.
    Crop marks are 1cm x 1cm (28.35 pt) solid black squares in 4 outer corners.
    """

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.crop_mark_size = 28.35  # 1 cm in points
        self.margin_x = 28.35        # 1 cm margin
        self.margin_y = 28.35        # 1 cm margin

    def build_pdf(
        self,
        prova_title: str,
        materia_nome: str,
        turma_nome: str,
        data_str: str,
        prova_id: int,
        aluno_nome: str,
        aluno_matricula: str,
        aluno_id: int,
        num_questions: int = 10,
        num_options: int = 5  # A, B, C, D, E
    ):
        c = canvas.Canvas(self.output_path, pagesize=A4)
        c.setTitle(f"Cartão Resposta - {aluno_nome}")

        # 1. Draw 4 Solid Black Crop Marks (1cm x 1cm)
        self._draw_crop_marks(c)

        # 2. Draw Institutional Header & Logo Accents
        self._draw_header(c, prova_title, materia_nome, turma_nome, data_str)

        # 3. Draw Student Info & QR Code
        self._draw_student_info_and_qr(
            c, prova_id, aluno_id, aluno_nome, aluno_matricula
        )

        # 4. Draw Signature & Visual Instructions Box
        self._draw_instructions_and_signature(c)

        # 5. Draw OMR Bubble Grid
        self._draw_omr_bubble_grid(c, num_questions, num_options)

        c.save()
        return self.output_path

    def _draw_crop_marks(self, c: canvas.Canvas):
        """Draw 4 solid black 1cm x 1cm squares in outer corners."""
        s = self.crop_mark_size
        mx = self.margin_x
        my = self.margin_y

        c.setFillColor(colors.black)

        # Top-Left
        c.rect(mx, PAGE_HEIGHT - my - s, s, s, fill=1, stroke=0)
        # Top-Right
        c.rect(PAGE_WIDTH - mx - s, PAGE_HEIGHT - my - s, s, s, fill=1, stroke=0)
        # Bottom-Left
        c.rect(mx, my, s, s, fill=1, stroke=0)
        # Bottom-Right
        c.rect(PAGE_WIDTH - mx - s, my, s, s, fill=1, stroke=0)

    def _draw_header(
        self, c: canvas.Canvas, title: str, materia: str, turma: str, data_str: str
    ):
        """Institutional header bar with teal & navy accents."""
        top_y = PAGE_HEIGHT - 65.0

        # Top Teal Accent Bar
        c.setFillColor(TEAL_HEX)
        c.rect(65, top_y + 20, PAGE_WIDTH - 180, 5, fill=1, stroke=0)

        # Title
        c.setFillColor(NAVY_HEX)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(65, top_y, title.upper())

        # Subtitle details
        c.setFillColor(DARK_GRAY)
        c.setFont("Helvetica", 10)
        sub_info = f"Disciplina: {materia}   |   Turma: {turma}   |   Data: {data_str}"
        c.drawString(65, top_y - 16, sub_info)

    def _draw_student_info_and_qr(
        self, c: canvas.Canvas, prova_id: int, aluno_id: int, nome: str, matricula: str
    ):
        """Student identification box and QR code."""
        box_y = PAGE_HEIGHT - 170.0
        box_x = 65.0
        box_w = PAGE_WIDTH - 200.0  # leave room for QR code
        box_h = 75.0

        # Student Info Box
        c.setStrokeColor(BORDER_GRAY)
        c.setFillColor(LIGHT_GRAY)
        c.roundRect(box_x, box_y, box_w, box_h, 6, fill=1, stroke=1)

        c.setFillColor(NAVY_HEX)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(box_x + 12, box_y + box_h - 20, "DADOS DO ALUNO:")

        c.setFillColor(DARK_GRAY)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(box_x + 12, box_y + box_h - 40, f"Nome: {nome}")

        c.setFont("Helvetica", 11)
        c.drawString(box_x + 12, box_y + box_h - 60, f"Matrícula: {matricula}")

        # QR Code (Top Right) ~2.5cm x 2.5cm (70 x 70 pt)
        qr_size = 70.0
        qr_x = PAGE_WIDTH - 65.0 - qr_size
        qr_y = box_y

        payload = generate_qr_payload(prova_id, aluno_id)
        qr_code = qr.QrCodeWidget(payload)
        bounds = qr_code.getBounds()
        w = bounds[2] - bounds[0]
        h = bounds[3] - bounds[1]

        d = Drawing(qr_size, qr_size, transform=[qr_size / w, 0, 0, qr_size / h, 0, 0])
        d.add(qr_code)

        # Quiet zone background for QR code
        c.setFillColor(colors.white)
        c.setStrokeColor(BORDER_GRAY)
        c.roundRect(qr_x - 5, qr_y - 5, qr_size + 10, qr_size + 10, 4, fill=1, stroke=1)
        d.drawOn(c, qr_x, qr_y)

    def _draw_instructions_and_signature(self, c: canvas.Canvas):
        """Draws visual instructions and student signature area."""
        sec_y = PAGE_HEIGHT - 265.0

        # Signature Box (Left)
        sig_x = 65.0
        sig_w = 260.0
        sig_h = 75.0
        c.setStrokeColor(BORDER_GRAY)
        c.setFillColor(colors.white)
        c.roundRect(sig_x, sec_y, sig_w, sig_h, 6, fill=1, stroke=1)

        c.setStrokeColor(BORDER_GRAY)
        c.line(sig_x + 20, sec_y + 25, sig_x + sig_w - 20, sec_y + 25)
        c.setFillColor(DARK_GRAY)
        c.setFont("Helvetica", 9)
        c.drawCentredString(sig_x + sig_w / 2.0, sec_y + 12, "Assinatura do Aluno")

        # Instructions Box (Right)
        inst_x = sig_x + sig_w + 15.0
        inst_w = PAGE_WIDTH - 65.0 - inst_x
        inst_h = sig_h
        c.setFillColor(LIGHT_GRAY)
        c.roundRect(inst_x, sec_y, inst_w, inst_h, 6, fill=1, stroke=1)

        c.setFillColor(NAVY_HEX)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(inst_x + 10, sec_y + inst_h - 18, "INSTRUÇÕES DE PREENCHIMENTO:")

        c.setFillColor(DARK_GRAY)
        c.setFont("Helvetica", 8)
        c.drawString(inst_x + 10, sec_y + inst_h - 32, "• Preencha a bolha totalmente com caneta escura.")
        c.drawString(inst_x + 10, sec_y + inst_h - 45, "• Não rasure e não faça marcas fora das bolhas.")

        # Draw correct vs incorrect bubble example icons
        ex_y = sec_y + 12
        # Correct fill
        c.setFillColor(colors.black)
        c.circle(inst_x + 20, ex_y, 5, fill=1, stroke=1)
        c.setFillColor(colors.HexColor("#10B981"))
        c.drawString(inst_x + 30, ex_y - 3, "Correto")

        # Incorrect fill (X)
        c.setFillColor(colors.white)
        c.circle(inst_x + 85, ex_y, 5, fill=1, stroke=1)
        c.setStrokeColor(colors.HexColor("#EF4444"))
        c.line(inst_x + 82, ex_y - 3, inst_x + 88, ex_y + 3)
        c.line(inst_x + 82, ex_y + 3, inst_x + 88, ex_y - 3)
        c.setFillColor(colors.HexColor("#EF4444"))
        c.drawString(inst_x + 95, ex_y - 3, "Incorreto (X)")

    def _draw_omr_bubble_grid(
        self, c: canvas.Canvas, num_questions: int, num_options: int
    ):
        """
        Draws the OMR answer grid with question numbers and option bubbles A..E.
        Organizes questions in 1 or 2 columns based on question count.
        """
        start_y = PAGE_HEIGHT - 300.0
        box_w = PAGE_WIDTH - 130.0
        box_h = start_y - 65.0

        # Main Grid Container Box
        c.setStrokeColor(NAVY_HEX)
        c.setLineWidth(1.5)
        c.setFillColor(colors.white)
        c.roundRect(65.0, 65.0, box_w, box_h, 8, fill=1, stroke=1)

        # Header Title bar for Grid
        c.setFillColor(NAVY_HEX)
        c.rect(65.0, start_y - 25.0, box_w, 25.0, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(PAGE_WIDTH / 2.0, start_y - 17.0, "FOLHA DE RESPOSTAS (MARQUE UMA OPÇÃO POR QUESTÃO)")

        # Determine column layout
        cols = 2 if num_questions > 15 else 1
        q_per_col = (num_questions + cols - 1) // cols
        col_width = box_w / cols

        options_letters = ["A", "B", "C", "D", "E"][:num_options]
        bubble_radius = 8.0
        option_spacing = 30.0

        grid_top_y = start_y - 45.0

        for col_idx in range(cols):
            col_x_start = 65.0 + (col_idx * col_width) + 20.0

            # Column Header Letters (A B C D E)
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(NAVY_HEX)

            for opt_idx, letter in enumerate(options_letters):
                lx = col_x_start + 60.0 + (opt_idx * option_spacing)
                c.drawCentredString(lx, grid_top_y, letter)

            # Questions rows
            row_y = grid_top_y - 25.0
            row_height = 24.0

            for q_in_col in range(q_per_col):
                q_num = (col_idx * q_per_col) + q_in_col + 1
                if q_num > num_questions:
                    break

                # Draw row background alternating highlight
                if q_num % 2 == 0:
                    c.setFillColor(LIGHT_GRAY)
                    c.rect(col_x_start - 10, row_y - 6, col_width - 30, row_height, fill=1, stroke=0)

                # Question Number label
                c.setFont("Helvetica-Bold", 10)
                c.setFillColor(DARK_GRAY)
                c.drawString(col_x_start, row_y, f"{q_num:02d}.")

                # Draw option bubbles
                c.setStrokeColor(DARK_GRAY)
                c.setLineWidth(1.0)
                c.setFillColor(colors.white)

                for opt_idx in range(num_options):
                    bx = col_x_start + 60.0 + (opt_idx * option_spacing)
                    by = row_y + 3.0
                    c.circle(bx, by, bubble_radius, fill=1, stroke=1)

                    # Inside subtle option letter label
                    c.setFont("Helvetica", 7)
                    c.setFillColor(colors.HexColor("#94A3B8"))
                    c.drawCentredString(bx, by - 2.5, options_letters[opt_idx])

                row_y -= row_height
