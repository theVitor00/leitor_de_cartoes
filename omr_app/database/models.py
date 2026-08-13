"""
Database models for OMR Application using Peewee ORM (SQLite).
Defines all 7 required entities and their relationships.
"""

from datetime import datetime
import json
from peewee import (
    SqliteDatabase, Model, AutoField, CharField, IntegerField,
    FloatField, DateField, DateTimeField, ForeignKeyField, TextField, CompositeKey
)

# SQLite database deferred initialization
db = SqliteDatabase(None)


class BaseModel(Model):
    class Meta:
        database = db


class Materia(BaseModel):
    id = AutoField()
    nome = CharField(max_length=100)
    codigo = CharField(max_length=20, unique=True)

    class Meta:
        table_name = 'materias'


class Turma(BaseModel):
    id = AutoField()
    nome = CharField(max_length=50)
    ano_letivo = IntegerField()

    class Meta:
        table_name = 'turmas'


class Aluno(BaseModel):
    id = AutoField()
    matricula = CharField(max_length=30, unique=True)
    nome = CharField(max_length=150)
    turma = ForeignKeyField(Turma, backref='alunos', on_delete='CASCADE')

    class Meta:
        table_name = 'alunos'


class Prova(BaseModel):
    id = AutoField()
    titulo = CharField(max_length=150)
    materia = ForeignKeyField(Materia, backref='provas', on_delete='CASCADE')
    turma = ForeignKeyField(Turma, backref='provas', on_delete='CASCADE')
    gabarito_oficial_json = TextField(default='{}')  # e.g., {"1": "A", "2": "C", ...}
    valor_total = FloatField(default=10.0)
    data_aplicacao = DateField(default=datetime.now)

    class Meta:
        table_name = 'provas'

    def get_gabarito(self) -> dict:
        try:
            return json.loads(self.gabarito_oficial_json)
        except Exception:
            return {}

    def set_gabarito(self, gabarito_dict: dict):
        self.gabarito_oficial_json = json.dumps(gabarito_dict, ensure_ascii=False)


class ProvaAluno(BaseModel):
    id = AutoField()
    prova = ForeignKeyField(Prova, backref='participantes', on_delete='CASCADE')
    aluno = ForeignKeyField(Aluno, backref='provas_participadas', on_delete='CASCADE')

    class Meta:
        table_name = 'provas_alunos'
        indexes = (
            (('prova', 'aluno'), True),  # Unique constraint
        )


class Resultado(BaseModel):
    STATUS_OK = 'OK'
    STATUS_REVISAO = 'REVISAO_NECESSARIA'
    STATUS_ERRO = 'ERRO_LEITURA'

    id = AutoField()
    prova = ForeignKeyField(Prova, backref='resultados', on_delete='CASCADE')
    aluno = ForeignKeyField(Aluno, backref='resultados', on_delete='CASCADE')
    respostas_marcadas_json = TextField(default='{}')  # e.g., {"1": "A", "2": "B|C", ...}
    nota_final = FloatField(default=0.0)
    acertos = IntegerField(default=0)
    total_questoes = IntegerField(default=0)
    caminho_imagem_scan = CharField(max_length=255, null=True)
    status = CharField(max_length=30, default=STATUS_OK)
    data_correcao = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'resultados'

    def get_respostas(self) -> dict:
        try:
            return json.loads(self.respostas_marcadas_json)
        except Exception:
            return {}

    def set_respostas(self, respostas_dict: dict):
        self.respostas_marcadas_json = json.dumps(respostas_dict, ensure_ascii=False)


class LogLeitura(BaseModel):
    id = AutoField()
    data_hora = DateTimeField(default=datetime.now)
    prova = ForeignKeyField(Prova, backref='logs', null=True, on_delete='SET NULL')
    quantidade_provas_corrigidas = IntegerField(default=0)
    sucessos = IntegerField(default=0)
    pendencias_revisao = IntegerField(default=0)
    erros = IntegerField(default=0)
    detalhes_json = TextField(default='[]')

    class Meta:
        table_name = 'logs_leitura'
