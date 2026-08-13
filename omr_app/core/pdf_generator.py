"""
Dynamic PDF Answer Sheet Generator using ReportLab.
Supports 1, 2, 3, or 4 columns layout, 3-5 options (A-C, A-D, A-E),
custom header accent colors, optional logo images, and optional student signature box.
Explicitly ensures all OMR bubbles (A, B, C, D, E) render with clean white background.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr
from omr_app.core.security import generate_qr_payload

NAVY_HEX = colors.HexColor("#002970")
DARK_GRAY = colors.HexColor("#1E293B")
LIGHT_GRAY = colors.HexColor("#F1F5F9")
BORDER_GRAY = colors.HexColor("#CBD5E1")

PAGE_WIDTH, PAGE_HEIGHT = A4  # 595.27 x 841.89 pt


class OMRPDFGenerator:
    """
    Generates vectorized PDF OMR Answer Sheets with dynamic layout parameters.
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
        num_options: int = 5,       # 3, 4, 5 (A-C, A-D, A-E)
        colunas: int = 2,           # 1, 2, 3, 4
        exibir_assinatura: bool = True,
        cor_cabecalho_hex: str = "#00AEA7",
        caminho_logo: str = None
    ):
        c = canvas.Canvas(self.output_path, pagesize=A4)
        c.setTitle(f"Cartão Resposta - {aluno_nome}")

        header_color = colors.HexColor(cor_cabecalho_hex) if cor_cabecalho_hex else colors.HexColor("#00AEA7")

        # 1. Solid Black Crop Marks (1cm x 1cm)
        self._draw_crop_marks(c)

        # 2. Institutional Header & Logo
        self._draw_header(c, prova_title, materia_nome, turma_nome, data_str, header_color, caminho_logo)

        # 3. Student Info & QR Code
        self._draw_student_info_and_qr(c, prova_id, aluno_id, aluno_nome, aluno_matricula)

        # 4. Signature & Instructions Box
        self._draw_instructions_and_signature(c, exibir_assinatura)

        # 5. Dynamic OMR Bubble Grid
        self._draw_omr_bubble_grid(c, num_questions, num_options, colunas)

        c.save()
        return self.output_path

    def _draw_crop_marks(self, c: canvas.Canvas):
        s = self.crop_mark_size
        mx = self.margin_x
        my = self.margin_y

        c.setFillColor(colors.black)
        c.rect(mx, PAGE_HEIGHT - my - s, s, s, fill=1, stroke=0)
        c.rect(PAGE_WIDTH - mx - s, PAGE_HEIGHT - my - s, s, s, fill=1, stroke=0)
        c.rect(mx, my, s, s, fill=1, stroke=0)
        c.rect(PAGE_WIDTH - mx - s, my, s, s, fill=1, stroke=0)

    def _draw_header(
        self,
        c: canvas.Canvas,
        title: str,
        materia: str,
        turma: str,
        data_str: str,
        header_color: colors.Color,
        logo_path: str = None
    ):
        top_y = PAGE_HEIGHT - 65.0
        text_x = 65.0

        if logo_path and os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, 65.0, top_y - 12, width=45, height=35, preserveAspectRatio=True, mask='auto')
                text_x = 120.0
            except Exception:
                text_x = 65.0

        c.setFillColor(header_color)
        c.rect(text_x, top_y + 20, PAGE_WIDTH - 180 - (text_x - 65.0), 5, fill=1, stroke=0)

        c.setFillColor(NAVY_HEX)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(text_x, top_y, title.upper())

        c.setFillColor(DARK_GRAY)
        c.setFont("Helvetica", 9)
        sub_info = f"Disciplina: {materia}   |   Turma: {turma}   |   Data: {data_str}"
        c.drawString(text_x, top_y - 16, sub_info)

    def _draw_student_info_and_qr(
        self, c: canvas.Canvas, prova_id: int, aluno_id: int, nome: str, matricula: str
    ):
        box_y = PAGE_HEIGHT - 170.0
        box_x = 65.0
        box_w = PAGE_WIDTH - 200.0
        box_h = 75.0

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

        c.setFillColor(colors.white)
        c.setStrokeColor(BORDER_GRAY)
        c.roundRect(qr_x - 5, qr_y - 5, qr_size + 10, qr_size + 10, 4, fill=1, stroke=1)
        d.drawOn(c, qr_x, qr_y)

    def _draw_instructions_and_signature(self, c: canvas.Canvas, exibir_assinatura: bool):
        sec_y = PAGE_HEIGHT - 265.0

        if exibir_assinatura:
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

            inst_x = sig_x + sig_w + 15.0
            inst_w = PAGE_WIDTH - 65.0 - inst_x
        else:
            inst_x = 65.0
            inst_w = PAGE_WIDTH - 130.0

        inst_h = 75.0
        c.setFillColor(LIGHT_GRAY)
        c.setStrokeColor(BORDER_GRAY)
        c.roundRect(inst_x, sec_y, inst_w, inst_h, 6, fill=1, stroke=1)

        c.setFillColor(NAVY_HEX)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(inst_x + 10, sec_y + inst_h - 18, "INSTRUÇÕES DE PREENCHIMENTO:")

        c.setFillColor(DARK_GRAY)
        c.setFont("Helvetica", 8)
        c.drawString(inst_x + 10, sec_y + inst_h - 32, "• Preencha a bolha totalmente com caneta escura.")
        c.drawString(inst_x + 10, sec_y + inst_h - 45, "• Não rasure e não faça marcas fora das bolhas.")

        ex_y = sec_y + 12
        c.setFillColor(colors.black)
        c.circle(inst_x + 20, ex_y, 4, fill=1, stroke=1)
        c.setFillColor(colors.HexColor("#10B981"))
        c.drawString(inst_x + 28, ex_y - 3, "Correto")

        c.setFillColor(colors.white)
        c.circle(inst_x + 85, ex_y, 4, fill=1, stroke=1)
        c.setStrokeColor(colors.HexColor("#EF4444"))
        c.line(inst_x + 82, ex_y - 3, inst_x + 88, ex_y + 3)
        c.line(inst_x + 82, ex_y + 3, inst_x + 88, ex_y - 3)
        c.setFillColor(colors.HexColor("#EF4444"))
        c.drawString(inst_x + 93, ex_y - 3, "Incorreto (X)")

    def _draw_omr_bubble_grid(
        self, c: canvas.Canvas, num_questions: int, num_options: int, colunas: int
    ):
        start_y = PAGE_HEIGHT - 300.0
        box_w = PAGE_WIDTH - 130.0
        box_h = start_y - 65.0

        c.setStrokeColor(NAVY_HEX)
        c.setLineWidth(1.5)
        c.setFillColor(colors.white)
        c.roundRect(65.0, 65.0, box_w, box_h, 8, fill=1, stroke=1)

        c.setFillColor(NAVY_HEX)
        c.rect(65.0, start_y - 25.0, box_w, 25.0, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(PAGE_WIDTH / 2.0, start_y - 17.0, "FOLHA DE RESPOSTAS (MARQUE UMA OPÇÃO POR QUESTÃO)")

        cols = max(1, min(4, colunas))
        q_per_col = (num_questions + cols - 1) // cols
        col_width = box_w / float(cols)

        options_letters = ["A", "B", "C", "D", "E"][:num_options]

        # Spacing and radius adjustments for 1, 2, 3, or 4 columns
        if cols == 4:
            bubble_radius = 4.5
            option_spacing = 15.0
            label_offset_x = 35.0
        elif cols == 3:
            bubble_radius = 5.5
            option_spacing = 20.0
            label_offset_x = 42.0
        elif cols == 2:
            bubble_radius = 7.0
            option_spacing = 26.0
            label_offset_x = 55.0
        else:
            bubble_radius = 8.0
            option_spacing = 35.0
            label_offset_x = 70.0

        grid_top_y = start_y - 45.0
        available_height = grid_top_y - 80.0
        row_height = min(24.0, available_height / max(q_per_col, 1))

        for col_idx in range(cols):
            col_x_start = 65.0 + (col_idx * col_width) + (8.0 if cols == 4 else 12.0)

            c.setFont("Helvetica-Bold", 8 if cols >= 3 else 10)
            c.setFillColor(NAVY_HEX)

            for opt_idx, letter in enumerate(options_letters):
                lx = col_x_start + label_offset_x + (opt_idx * option_spacing)
                c.drawCentredString(lx, grid_top_y, letter)

            row_y = grid_top_y - 22.0

            for q_in_col in range(q_per_col):
                q_num = (col_idx * q_per_col) + q_in_col + 1
                if q_num > num_questions:
                    break

                if q_num % 2 == 0:
                    c.setFillColor(LIGHT_GRAY)
                    c.rect(col_x_start - 4, row_y - 4, col_width - 8, row_height, fill=1, stroke=0)

                c.setFont("Helvetica-Bold", 7 if cols == 4 else (8 if cols == 3 else 9))
                c.setFillColor(DARK_GRAY)
                c.drawString(col_x_start, row_y, f"{q_num:02d}.")

                # DRAW BUBBLES - CRITICAL FIX: EXPLICITLY RESET FILL TO WHITE BEFORE EACH CIRCLE!
                for opt_idx in range(num_options):
                    bx = col_x_start + label_offset_x + (opt_idx * option_spacing)
                    by = row_y + 2.5

                    c.setFillColor(colors.white)
                    c.setStrokeColor(DARK_GRAY)
                    c.setLineWidth(0.8)
                    c.circle(bx, by, bubble_radius, fill=1, stroke=1)

                    c.setFont("Helvetica", 6 if cols >= 3 else 7)
                    c.setFillColor(colors.HexColor("#64748B"))
                    c.drawCentredString(bx, by - (1.8 if cols >= 3 else 2.0), options_letters[opt_idx])

                row_y -= row_height
