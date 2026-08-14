"""
Pure Python Exam Grader.
Evaluates student answers against official answer keys independently of OpenCV.
"""

from typing import Optional
from omr_app.core.types import OMRStatus, ExamGradingResult
from omr_app.core.layout import SheetLayout


class ExamGrader:
    """
    Independent Exam Grader logic.
    Computes total score, correct answer count, double mark flags,
    and review status without any OpenCV or image dependencies.
    """

    @staticmethod
    def grade(
        respostas_marcadas: dict[str, str],
        gabarito_dict: Optional[dict[str, str]] = None,
        valor_total: float = 10.0,
        num_questions: int = 10,
        layout: Optional[SheetLayout] = None,
        qr_valid: bool = True
    ) -> ExamGradingResult:
        """
        Grades extracted OMR answers against official answer key dictionary.
        """
        acertos = 0
        status = OMRStatus.OK
        detalhes_status: list[str] = []
        flagged_boxes: list[dict] = []

        if not qr_valid:
            status = OMRStatus.REVISAO_NECESSARIA
            detalhes_status.append("QR Code não identificado ou hash de segurança inválido (clonagem/adulteração).")

        if not gabarito_dict:
            status = OMRStatus.REVISAO_NECESSARIA
            detalhes_status.append("Gabarito não fornecido.")

        total_q = num_questions if num_questions > 0 else 10

        # Check for structural inconsistency (more extracted answers than exam questions)
        if respostas_marcadas and len(respostas_marcadas) > total_q:
            status = OMRStatus.REVISAO_NECESSARIA
            detalhes_status.append(
                f"Inconsistência estrutural: prova espera {total_q} questões, mas leitura retornou {len(respostas_marcadas)}."
            )

        for q in range(1, total_q + 1):
            q_str = str(q)
            resp_lid = respostas_marcadas.get(q_str, "-")
            gab_resp = gabarito_dict.get(q_str, "") if gabarito_dict else ""

            is_double_marked = "|" in resp_lid
            is_unreadable = resp_lid in ("?", "UNREADABLE", "AMBIGUOUS")

            if is_double_marked:
                status = OMRStatus.REVISAO_NECESSARIA
                detalhes_status.append(f"Questão {q_str}: Dupla marcação ({resp_lid}).")
            elif is_unreadable:
                status = OMRStatus.REVISAO_NECESSARIA
                detalhes_status.append(f"Questão {q_str}: Marcação ilegível ou ambígua ({resp_lid}).")
            elif resp_lid == "-":
                pass
            elif gab_resp and resp_lid == gab_resp:
                acertos += 1

            if is_double_marked or is_unreadable:
                box_list = layout.get_question_bounding_box(q).to_list() if layout else [0, 0, 0, 0]
                flagged_boxes.append({
                    "question": q_str,
                    "box": box_list,
                    "reason": resp_lid
                })

        nota_final = (acertos / total_q) * valor_total if total_q > 0 else 0.0

        mensagem = " | ".join(detalhes_status) if detalhes_status else "Correção efetuada com sucesso."

        return ExamGradingResult(
            status=status,
            nota_final=round(nota_final, 2),
            acertos=acertos,
            total_questoes=total_q,
            respostas=respostas_marcadas,
            flagged_boxes=flagged_boxes,
            detalhes_status=detalhes_status,
            mensagem=mensagem
        )
