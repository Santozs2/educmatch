from django.urls import reverse

from catalogo.models import Area, Peso_curso
from painel import metricas
from painel.tests.base import BasePainel


class GestaoDeAreasTest(BasePainel):
    """A tela de áreas: números de cada área, editar, desativar e reativar."""

    def setUp(self):
        super().setUp()
        self.staff = self.criar_staff()
        self.client.force_login(self.staff)

    def linha(self, area):
        return next(linha for linha in metricas.gestao_de_areas(None) if linha["id"] == area.pk)

    def test_area_nova_aparece_sem_curso_e_fora_do_quiz(self):
        nova = Area.objects.create(nome="Energia Solar", slug="energia-solar", descricao="Fotovoltaica.")

        linha = self.linha(nova)

        self.assertEqual((linha["principais"], linha["com_peso"], linha["alternativas"]), (0, 0, 0))
        resposta = self.client.get(reverse("painel-areas"))
        self.assertContains(resposta, "Energia Solar")
        self.assertContains(resposta, "Fora do quiz")
        self.assertGreaterEqual(resposta.context["resumo"]["fora_do_quiz"], 1)

    def test_conta_cursos_ativos_principais_e_com_peso(self):
        area = Area.objects.create(nome="Energia Solar", slug="energia-solar", descricao="Fotovoltaica.")
        principal = self.criar_curso(area_principal=area)
        self.criar_curso(area_principal=area, is_active=False)
        outro = self.criar_curso()
        Peso_curso.objects.create(curso=principal, area=area, peso=5)
        Peso_curso.objects.create(curso=outro, area=area, peso=2)

        linha = self.linha(area)

        self.assertEqual(linha["principais"], 1)    # o inativo não conta
        self.assertEqual(linha["com_peso"], 2)  # principal e o de outra área

    def test_area_do_seed_tem_alternativas_no_quiz(self):
        com_quiz = [linha for linha in metricas.gestao_de_areas(None) if linha["alternativas"]]
        self.assertTrue(com_quiz)

    def test_em_primeiro_usa_o_historico(self):
        area = Area.objects.filter(is_active=True).first()
        for _ in range(2):
            self.criar_tentativa_com_explicacao({"top_areas": [{"area": area.slug}]})

        self.assertEqual(self.linha(area)["em_primeiro"], 2)

    def test_ativas_vem_antes_das_inativas(self):
        Area.objects.create(nome="AAA Antiga", slug="aaa-antiga", descricao="x", is_active=False)

        linhas = metricas.gestao_de_areas(None)

        self.assertTrue(linhas[0]["is_active"])
        self.assertFalse(linhas[-1]["is_active"])

    def test_editar_muda_nome_e_descricao_mas_nao_o_slug(self):
        area = Area.objects.filter(is_active=True).first()
        slug = area.slug

        resposta = self.client.post(
            reverse("painel-editar-area", args=[area.pk]),
            {"nome": "Nome Novo da Área", "descricao": "Descrição nova."},
        )

        self.assertRedirects(resposta, reverse("painel-areas"))
        area.refresh_from_db()
        self.assertEqual((area.nome, area.descricao, area.slug), ("Nome Novo da Área", "Descrição nova.", slug))

    def test_editar_com_nome_de_outra_area_reabre_o_modal(self):
        primeira, segunda = Area.objects.filter(is_active=True)[:2]

        resposta = self.client.post(
            reverse("painel-editar-area", args=[primeira.pk]),
            {"nome": segunda.nome.upper(), "descricao": "x"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Já existe uma área com esse nome.")
        self.assertContains(resposta, f'id="painel-editar-area-{primeira.pk}"')
        self.assertContains(resposta, 'data-abrir="true"')

    def test_editar_mantendo_o_proprio_nome_vale(self):
        area = Area.objects.filter(is_active=True).first()

        resposta = self.client.post(
            reverse("painel-editar-area", args=[area.pk]), {"nome": area.nome, "descricao": "Outra."}
        )

        self.assertRedirects(resposta, reverse("painel-areas"))

    def test_desativar_e_reativar(self):
        area = Area.objects.filter(is_active=True).first()

        self.assertRedirects(self.client.post(reverse("painel-desativar-area", args=[area.pk])), reverse("painel-areas"))
        area.refresh_from_db()
        self.assertFalse(area.is_active)

        self.assertRedirects(self.client.post(reverse("painel-reativar-area", args=[area.pk])), reverse("painel-areas"))
        area.refresh_from_db()
        self.assertTrue(area.is_active)

    def test_desativar_nao_apaga_pesos_dos_cursos(self):
        area = Area.objects.filter(is_active=True).first()
        curso = self.criar_curso(area_principal=area)
        Peso_curso.objects.create(curso=curso, area=area, peso=4)

        self.client.post(reverse("painel-desativar-area", args=[area.pk]))

        self.assertTrue(Peso_curso.objects.filter(curso=curso, area=area).exists())
        self.assertTrue(Area.objects.filter(pk=area.pk).exists())

    def test_acoes_so_por_post_e_staff(self):
        area = Area.objects.filter(is_active=True).first()
        self.assertEqual(self.client.get(reverse("painel-desativar-area", args=[area.pk])).status_code, 405)

        self.client.logout()
        self.client.force_login(self.criar_usuario())
        self.client.post(reverse("painel-desativar-area", args=[area.pk]))
        area.refresh_from_db()
        self.assertTrue(area.is_active)
        self.assertEqual(self.client.get(reverse("painel-areas")).status_code, 302)

    def test_menu_marca_a_secao_areas(self):
        resposta = self.client.get(reverse("painel-areas"))

        self.assertEqual(resposta.context["secao"], "areas")
        self.assertContains(resposta, 'data-dica="Áreas" aria-current="page"')
