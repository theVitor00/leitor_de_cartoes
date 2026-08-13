"""
Automated Logging system for OMR processing runs.
Saves log records into database LogLeitura and exports log reports as TXT/JSON files.
"""

import os
import json
from datetime import datetime
from omr_app.database.models import LogLeitura, Prova


class ProcessLogger:
    """
    Handles logging of execution metrics and details.
    """

    def __init__(self, logs_dir: str = None):
        if not logs_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            logs_dir = os.path.join(base_dir, "logs_export")
        os.makedirs(logs_dir, exist_ok=True)
        self.logs_dir = logs_dir

    def record_run_log(
        self,
        prova_id: int,
        total: int,
        sucessos: int,
        revisoes: int,
        erros: int,
        detalhes: list[dict]
    ) -> LogLeitura:
        """Saves a batch process run log entry into SQLite."""
        prova = Prova.get_or_none(Prova.id == prova_id) if prova_id else None

        log_entry = LogLeitura.create(
            data_hora=datetime.now(),
            prova=prova,
            quantidade_provas_corrigidas=total,
            sucessos=sucessos,
            pendencias_revisao=revisoes,
            erros=erros,
            detalhes_json=json.dumps(detalhes, ensure_ascii=False)
        )

        # Also write auto-backup TXT log file
        self.export_log_to_txt(log_entry.id)
        return log_entry

    def export_log_to_txt(self, log_id: int) -> str:
        """Exports a LogLeitura record to a formatted TXT file."""
        log_entry = LogLeitura.get_or_none(LogLeitura.id == log_id)
        if not log_entry:
            return ""

        filename = f"log_execucao_{log_entry.id}_{log_entry.data_hora.strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = os.path.join(self.logs_dir, filename)

        prova_nome = log_entry.prova.titulo if log_entry.prova else "N/A"

        lines = [
            "=" * 60,
            "REGISTRO DE PROCESSAMENTO DE LOTE - LEITOR OMR",
            "=" * 60,
            f"ID do Log: #{log_entry.id}",
            f"Data/Hora: {log_entry.data_hora.strftime('%d/%m/%Y %H:%M:%S')}",
            f"Prova: {prova_nome}",
            f"Total de Provas Corrigidas no Lote: {log_entry.quantidade_provas_corrigidas}",
            f"  - Sucessos (OK): {log_entry.sucessos}",
            f"  - Pendentes de Revisão: {log_entry.pendencias_revisao}",
            f"  - Erros de Leitura: {log_entry.erros}",
            "-" * 60,
            "DETALHES DAS FOLHAS PROCESSADAS:",
            "-" * 60
        ]

        try:
            detalhes = json.loads(log_entry.detalhes_json)
            for idx, item in enumerate(detalhes, 1):
                status_icon = "🟢" if item.get('status') == 'OK' else ("🟡" if item.get('status') == 'REVISAO_NECESSARIA' else "🔴")
                lines.append(
                    f"{idx:02d}. [{status_icon} {item.get('status')}] Aluno ID: {item.get('aluno_id', 'N/A')} | "
                    f"Nota: {item.get('nota_final', 0.0)} | Msg: {item.get('mensagem', '')}"
                )
        except Exception as e:
            lines.append(f"Erro ao parsear detalhes: {e}")

        lines.append("=" * 60)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return file_path
