"""
Database Manager module for initializing SQLite and inserting seed data.
"""

import os
from datetime import datetime, date
from omr_app.database.models import (
    db, Materia, Turma, Aluno, Prova, ProvaAluno, Resultado, LogLeitura, Template
)

DB_FILENAME = "omr_database.db"


def init_db(db_path: str = None) -> str:
    """Initialize database connection, create tables and seed initial data if needed."""
    if not db_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, DB_FILENAME)

    db.init(db_path)
    db.connect(reuse_if_open=True)
    db.create_tables([
        Materia, Turma, Aluno, Template, Prova, ProvaAluno, Resultado, LogLeitura
    ])

    # Check and migrate columns if needed
    _migrate_schema()
    _seed_initial_data()
    return db_path


def _migrate_schema():
    """Adds template_id column to provas table if missing."""
    try:
        columns = [c.name for c in db.get_columns('provas')]
        if 'template_id' not in columns:
            db.execute_sql('ALTER TABLE provas ADD COLUMN template_id INTEGER REFERENCES templates(id) ON DELETE SET NULL;')
    except Exception:
        pass


def _seed_initial_data():
    """Populate sample data if database is brand new."""
    # Seed default Template
    default_template = None
    if Template.select().count() == 0:
        default_template = Template.create(
            nome="Modelo Padrão - 10 Questões A-E (2 Colunas)",
            quantidade_questoes=10,
            alternativas_por_questao=5,
            colunas=2,
            exibir_assinatura=True,
            cor_cabecalho_hex="#00AEA7"
        )
        Template.create(
            nome="Simulado Curto - 15 Questões A-D (1 Coluna)",
            quantidade_questoes=15,
            alternativas_por_questao=4,
            colunas=1,
            exibir_assinatura=True,
            cor_cabecalho_hex="#002970"
        )

    if Materia.select().count() == 0:
        m1 = Materia.create(nome="Matemática", codigo="MAT101")
        m2 = Materia.create(nome="Português", codigo="POR101")
        m3 = Materia.create(nome="Física", codigo="FIS101")

        t1 = Turma.create(nome="3º Ano A - Ensino Médio", ano_letivo=2026)
        t2 = Turma.create(nome="3º Ano B - Ensino Médio", ano_letivo=2026)

        alunos_sample = [
            ("2026001", "Ana Silva", t1),
            ("2026002", "Bruno Oliveira", t1),
            ("2026003", "Carla Souza", t1),
            ("2026004", "Daniel Santos", t1),
            ("2026005", "Eduarda Lima", t1),
            ("2026006", "Felipe Rocha", t2),
            ("2026007", "Gabriela Costa", t2),
            ("2026008", "Heitor Ferreira", t2),
        ]

        created_alunos = []
        for mat, nome, turma in alunos_sample:
            created_alunos.append(Aluno.create(matricula=mat, nome=nome, turma=turma))

        gabarito_sample = {
            "1": "A", "2": "C", "3": "B", "4": "D", "5": "E",
            "6": "A", "7": "B", "8": "C", "9": "D", "10": "E"
        }

        tmpl = default_template or Template.select().first()

        prova1 = Prova.create(
            titulo="Simulado ENEM - Matemática",
            materia=m1,
            turma=t1,
            template=tmpl,
            valor_total=10.0,
            data_aplicacao=date.today()
        )
        prova1.set_gabarito(gabarito_sample)
        prova1.save()

        for a in created_alunos:
            if a.turma == t1:
                ProvaAluno.create(prova=prova1, aluno=a)
