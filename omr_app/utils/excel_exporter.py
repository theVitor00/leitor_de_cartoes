"""
Excel and Bulletin Exporter using Pandas, OpenPyXL, and ReportLab.
"""

import os
import pandas as pd
from omr_app.database.models import Prova, Resultado, Aluno, Turma


def export_results_to_excel(prova_id: int, output_path: str) -> str:
    """
    Exports exam results into a styled Excel file (.xlsx) with batch metrics and student grades.
    """
    prova = Prova.get_or_none(Prova.id == prova_id)
    if not prova:
        raise ValueError("Prova não encontrada.")

    resultados = Resultado.select().where(Resultado.prova == prova)

    data = []
    for r in resultados:
        aluno_nome = r.aluno.nome if r.aluno else "N/A"
        aluno_mat = r.aluno.matricula if r.aluno else "N/A"
        turma_nome = r.aluno.turma.nome if (r.aluno and r.aluno.turma) else "N/A"

        data.append({
            "Matrícula": aluno_mat,
            "Nome do Aluno": aluno_nome,
            "Turma": turma_nome,
            "Acertos": r.acertos,
            "Total Questões": r.total_questoes,
            "Nota Final": r.nota_final,
            "Valor Prova": prova.valor_total,
            "Status Correção": r.status,
            "Data Correção": r.data_correcao.strftime("%d/%m/%Y %H:%M") if r.data_correcao else ""
        })

    df = pd.DataFrame(data)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Resultados_Provas", index=False)

    return output_path
