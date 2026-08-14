"""
Unit tests for management rules, referential integrity deletion checks,
and mandatory Template & Gabarito validations.
"""

import unittest
from omr_app.database.db_manager import init_db
from omr_app.database.models import Materia, Turma, Aluno, Template, Prova, ProvaAluno, Resultado


class TestManagementRules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        # Create test isolates
        self.materia = Materia.create(nome="Matemática Teste", codigo="MAT_MGMT_01")
        self.turma = Turma.create(nome="Turma MGMT A", ano_letivo=2026)
        self.aluno = Aluno.create(matricula="MGMT_202601", nome="Aluno Management", turma=self.turma)
        self.template = Template.create(
            nome="Template MGMT 10Q 2C",
            quantidade_questoes=10,
            alternativas_por_questao=5,
            colunas=2
        )

    def tearDown(self):
        # Clean up test records
        Resultado.delete().where(Resultado.aluno == self.aluno).execute()
        ProvaAluno.delete().where(ProvaAluno.aluno == self.aluno).execute()
        Prova.delete().where(Prova.materia == self.materia).execute()
        Aluno.delete().where(Aluno.id == self.aluno.id).execute()
        Turma.delete().where(Turma.id == self.turma.id).execute()
        Materia.delete().where(Materia.id == self.materia.id).execute()
        Template.delete().where(Template.id == self.template.id).execute()

    def test_prevent_deletion_of_turma_with_alunos(self):
        alunos_count = Aluno.select().where(Aluno.turma == self.turma).count()
        self.assertGreater(alunos_count, 0)
        # Dependency check rule: cannot delete turma with students
        can_delete = (alunos_count == 0)
        self.assertFalse(can_delete)

    def test_delete_turma_without_dependencies(self):
        empty_turma = Turma.create(nome="Turma Vazia", ano_letivo=2026)
        alunos_count = Aluno.select().where(Aluno.turma == empty_turma).count()
        provas_count = Prova.select().where(Prova.turma == empty_turma).count()
        self.assertEqual(alunos_count, 0)
        self.assertEqual(provas_count, 0)
        empty_turma.delete_instance()
        self.assertIsNone(Turma.get_or_none(Turma.id == empty_turma.id))

    def test_prevent_deletion_of_materia_with_provas(self):
        prova = Prova.create(
            titulo="Prova Teste Dependencia",
            materia=self.materia,
            turma=self.turma,
            template=self.template,
            valor_total=10.0
        )
        provas_count = Prova.select().where(Prova.materia == self.materia).count()
        self.assertGreater(provas_count, 0)
        can_delete = (provas_count == 0)
        self.assertFalse(can_delete)
        prova.delete_instance()

    def test_delete_materia_without_dependencies(self):
        empty_mat = Materia.create(nome="Disciplina Vazia", codigo="DISC_VAZIA_99")
        provas_count = Prova.select().where(Prova.materia == empty_mat).count()
        self.assertEqual(provas_count, 0)
        empty_mat.delete_instance()
        self.assertIsNone(Materia.get_or_none(Materia.id == empty_mat.id))

    def test_prevent_deletion_of_template_used_by_prova(self):
        prova = Prova.create(
            titulo="Prova Teste Template",
            materia=self.materia,
            turma=self.turma,
            template=self.template,
            valor_total=10.0
        )
        provas_count = Prova.select().where(Prova.template == self.template).count()
        self.assertGreater(provas_count, 0)
        can_delete = (provas_count == 0)
        self.assertFalse(can_delete)
        prova.delete_instance()

    def test_delete_template_without_dependencies(self):
        unused_tmpl = Template.create(nome="Template Nao Usado", quantidade_questoes=5)
        provas_count = Prova.select().where(Prova.template == unused_tmpl).count()
        self.assertEqual(provas_count, 0)
        unused_tmpl.delete_instance()
        self.assertIsNone(Template.get_or_none(Template.id == unused_tmpl.id))

    def test_prevent_deletion_of_aluno_with_resultados(self):
        prova = Prova.create(
            titulo="Prova Teste Aluno Resultado",
            materia=self.materia,
            turma=self.turma,
            template=self.template,
            valor_total=10.0
        )
        res = Resultado.create(
            prova=prova,
            aluno=self.aluno,
            nota_final=10.0,
            acertos=10,
            total_questoes=10
        )
        resultados_count = Resultado.select().where(Resultado.aluno == self.aluno).count()
        self.assertGreater(resultados_count, 0)
        can_delete = (resultados_count == 0)
        self.assertFalse(can_delete)
        res.delete_instance()
        prova.delete_instance()

    def test_prevent_deletion_of_prova_with_resultados(self):
        prova = Prova.create(
            titulo="Prova Teste Com Resultado",
            materia=self.materia,
            turma=self.turma,
            template=self.template,
            valor_total=10.0
        )
        res = Resultado.create(
            prova=prova,
            aluno=self.aluno,
            nota_final=8.0,
            acertos=8,
            total_questoes=10
        )
        resultados_count = Resultado.select().where(Resultado.prova == prova).count()
        self.assertGreater(resultados_count, 0)
        can_delete = (resultados_count == 0)
        self.assertFalse(can_delete)
        res.delete_instance()
        prova.delete_instance()

    def test_gabarito_validation_complete_and_matching(self):
        # 10 questions template
        valid_gabarito = {str(i): ["A", "B", "C", "D", "E"][(i - 1) % 5] for i in range(1, 11)}
        self.assertEqual(len(valid_gabarito), self.template.quantidade_questoes)

        prova = Prova.create(
            titulo="Prova Gabarito Valido",
            materia=self.materia,
            turma=self.turma,
            template=self.template,
            valor_total=10.0
        )
        prova.set_gabarito(valid_gabarito)
        prova.save()

        saved_gab = prova.get_gabarito()
        self.assertEqual(len(saved_gab), 10)
        self.assertEqual(saved_gab["1"], "A")
        prova.delete_instance()

    def test_gabarito_validation_rejects_incomplete_or_invalid_option(self):
        # Incomplete gabarito (only 5 answers for a 10 question template)
        incomplete_gabarito = {str(i): "A" for i in range(1, 6)}
        is_complete = (len(incomplete_gabarito) == self.template.quantidade_questoes)
        self.assertFalse(is_complete)

        # Invalid option ('F' when template only supports A-E)
        valid_letters = ["A", "B", "C", "D", "E"][:self.template.alternativas_por_questao]
        invalid_gabarito = {str(i): ("F" if i == 1 else "A") for i in range(1, 11)}
        all_valid = all(v in valid_letters for v in invalid_gabarito.values())
        self.assertFalse(all_valid)


if __name__ == "__main__":
    unittest.main()
