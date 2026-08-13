"""
PySide6 QThread Workers for non-blocking background processing.
Supports dynamic Template settings and custom OMR sensitivity.
"""

import os
from PySide6.QtCore import QThread, Signal
from omr_app.core.omr_engine import OMREngine
from omr_app.core.pdf_generator import OMRPDFGenerator
from omr_app.utils.image_helpers import load_file_to_cv2_images
from omr_app.database.models import Prova, Resultado, Aluno, ProvaAluno, Template
from omr_app.logs.process_logger import ProcessLogger


class CorrectionWorker(QThread):
    """
    Background worker thread for batch processing OMR scans.
    """
    progress_changed = Signal(int, int)       # current, total
    sheet_processed = Signal(dict)           # result dict for individual sheet
    finished = Signal(dict)                  # batch summary dict
    log_emitted = Signal(str)                # real-time text message for log console

    def __init__(self, file_paths: list[str], target_prova_id: int = None, sensitivity_pct: float = 45.0):
        super().__init__()
        self.file_paths = file_paths
        self.target_prova_id = target_prova_id
        self.sensitivity_pct = sensitivity_pct
        self.engine = OMREngine()
        self.logger = ProcessLogger()

    def run(self):
        self.log_emitted.emit(f"🚀 Iniciando varredura em lote com Sensibilidade OMR em {self.sensitivity_pct:.0f}%...")

        images_to_process = []
        for fp in self.file_paths:
            try:
                imgs = load_file_to_cv2_images(fp)
                for page_num, img_bgr in imgs:
                    images_to_process.append((fp, page_num, img_bgr))
            except Exception as e:
                self.log_emitted.emit(f"⚠️ Erro ao carregar arquivo '{os.path.basename(fp)}': {e}")

        total_sheets = len(images_to_process)
        if total_sheets == 0:
            self.log_emitted.emit("❌ Nenhum arquivo/página válido para processamento.")
            self.finished.emit({"total": 0, "sucessos": 0, "revisoes": 0, "erros": 0})
            return

        self.log_emitted.emit(f"📊 Total de páginas/folhas a processar: {total_sheets}")

        prova = Prova.get_or_none(Prova.id == self.target_prova_id) if self.target_prova_id else None
        gabarito = prova.get_gabarito() if prova else {}
        valor_total = prova.valor_total if prova else 10.0

        # Template settings
        tmpl = prova.template if (prova and prova.template) else None
        num_questions = tmpl.quantidade_questoes if tmpl else (len(gabarito) if gabarito else 10)
        num_options = tmpl.alternativas_por_questao if tmpl else 5
        colunas = tmpl.colunas if tmpl else 2

        sucessos = 0
        revisoes = 0
        erros = 0
        detalhes_lote = []

        for idx, (orig_fp, page_num, img_bgr) in enumerate(images_to_process, 1):
            self.progress_changed.emit(idx, total_sheets)
            self.log_emitted.emit(f"📄 Processando {os.path.basename(orig_fp)} (pág {page_num})...")

            res = self.engine.process_sheet_image(
                image_bgr=img_bgr,
                expected_prova_id=self.target_prova_id,
                gabarito_dict=gabarito,
                valor_total=valor_total,
                num_questions=num_questions,
                num_options=num_options,
                colunas=colunas,
                sensitivity_pct=self.sensitivity_pct
            )

            p_id = res['prova_id'] or self.target_prova_id
            a_id = res['aluno_id']

            if p_id and a_id:
                prova_obj = Prova.get_or_none(Prova.id == p_id)
                aluno_obj = Aluno.get_or_none(Aluno.id == a_id)

                if prova_obj and aluno_obj:
                    resultado_record, _ = Resultado.get_or_create(
                        prova=prova_obj,
                        aluno=aluno_obj,
                        defaults={
                            "respostas_marcadas_json": "{}",
                            "nota_final": res['nota_final'],
                            "acertos": res['acertos'],
                            "total_questoes": res['total_questoes'],
                            "caminho_imagem_scan": res['annotated_path'],
                            "status": res['status']
                        }
                    )
                    resultado_record.set_respostas(res['respostas'])
                    resultado_record.nota_final = res['nota_final']
                    resultado_record.acertos = res['acertos']
                    resultado_record.total_questoes = res['total_questoes']
                    resultado_record.caminho_imagem_scan = res['annotated_path']
                    resultado_record.status = res['status']
                    resultado_record.save()

                    res['resultado_db_id'] = resultado_record.id

            st = res['status']
            if st == "OK":
                sucessos += 1
                self.log_emitted.emit(f"  ✅ [OK] Aluno ID: {a_id or 'Desconhecido'} - Nota: {res['nota_final']}")
            elif st == "REVISAO_NECESSARIA":
                revisoes += 1
                self.log_emitted.emit(f"  🟡 [REVISÃO] {res['mensagem']}")
            else:
                erros += 1
                self.log_emitted.emit(f"  🔴 [ERRO] {res['mensagem']}")

            detalhes_lote.append(res)
            self.sheet_processed.emit(res)

        self.logger.record_run_log(
            prova_id=self.target_prova_id,
            total=total_sheets,
            sucessos=sucessos,
            revisoes=revisoes,
            erros=erros,
            detalhes=detalhes_lote
        )

        summary = {
            "total": total_sheets,
            "sucessos": sucessos,
            "revisoes": revisoes,
            "erros": erros
        }

        self.log_emitted.emit(
            f"🎉 Lote concluído! Total: {total_sheets} | Sucessos: {sucessos} | Revisões: {revisoes} | Erros: {erros}"
        )
        self.finished.emit(summary)


class PDFGeneratorWorker(QThread):
    """
    Background worker thread for bulk generating PDF Answer Sheets based on Exam Template settings.
    """
    progress_changed = Signal(int, int)
    finished = Signal(str)
    log_emitted = Signal(str)

    def __init__(self, prova_id: int, aluno_ids: list[int], output_dir: str):
        super().__init__()
        self.prova_id = prova_id
        self.aluno_ids = aluno_ids
        self.output_dir = output_dir

    def run(self):
        prova = Prova.get_or_none(Prova.id == self.prova_id)
        if not prova:
            self.log_emitted.emit("❌ Prova não encontrada.")
            self.finished.emit("")
            return

        tmpl = prova.template
        num_questions = tmpl.quantidade_questoes if tmpl else 10
        num_options = tmpl.alternativas_por_questao if tmpl else 5
        colunas = tmpl.colunas if tmpl else 2
        exibir_assinatura = tmpl.exibir_assinatura if tmpl else True
        cor_cabecalho_hex = tmpl.cor_cabecalho_hex if tmpl else "#00AEA7"
        caminho_logo = tmpl.caminho_logo if tmpl else None

        alunos = Aluno.select().where(Aluno.id.in_(self.aluno_ids))
        total = len(alunos)

        filename = f"Cartoes_Resposta_{prova.titulo.replace(' ', '_')}_{prova.id}.pdf"
        final_pdf_path = os.path.join(self.output_dir, filename)

        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        c_master = canvas.Canvas(final_pdf_path, pagesize=A4)

        generator = OMRPDFGenerator(final_pdf_path)

        self.log_emitted.emit(f"🖨️ Gerando cartões de resposta (Template: {tmpl.nome if tmpl else 'Padrão'}) para {total} alunos...")

        for idx, aluno in enumerate(alunos, 1):
            self.progress_changed.emit(idx, total)
            self.log_emitted.emit(f"  📄 Desenhando cartão do aluno: {aluno.nome} ({aluno.matricula})")

            header_color = OMRPDFGenerator(final_pdf_path)
            from reportlab.lib import colors
            color_obj = colors.HexColor(cor_cabecalho_hex) if cor_cabecalho_hex else colors.HexColor("#00AEA7")

            generator._draw_crop_marks(c_master)
            generator._draw_header(
                c_master,
                prova.titulo,
                prova.materia.nome if prova.materia else "Geral",
                prova.turma.nome if prova.turma else "Geral",
                prova.data_aplicacao.strftime("%d/%m/%Y"),
                color_obj,
                caminho_logo
            )
            generator._draw_student_info_and_qr(
                c_master, prova.id, aluno.id, aluno.nome, aluno.matricula
            )
            generator._draw_instructions_and_signature(c_master, exibir_assinatura)
            generator._draw_omr_bubble_grid(
                c_master,
                num_questions=num_questions,
                num_options=num_options,
                colunas=colunas
            )

            c_master.showPage()

        c_master.save()
        self.log_emitted.emit(f"✅ Arquivo PDF gerado com sucesso: {final_pdf_path}")
        self.finished.emit(final_pdf_path)
