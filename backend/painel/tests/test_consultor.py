import json
from unittest import mock

from django.core.cache import cache
from django.test import override_settings

from catalogo.models import Area, Curso, Peso_curso
from painel import consultor
from painel.tests.base import BasePainel
from quiz.delivery import PAUSA
from quiz.llm import LLMInvalidOutput, LLMResponse, LLMTimeout

DESCRICAO = "Instalação e manutenção de quadros de distribuição, circuitos elétricos residenciais e normas de segurança NR-10."
LIGADO = override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_MODEL="")


class ProvedorFixo:
    """Devolve sempre o mesmo texto, para testar a revisão da saída."""

    def __init__(self, texto):
        self.texto = texto

    def complete(self, prompt):
        return LLMResponse(text=self.texto, model="fixo")


def saida(**extra):
    dados = {
        "areas": [{"slug": Area.objects.filter(is_active=True).first().slug, "justificativa": "Liga.", "peso": 5}],
        "nenhuma_area_adequada": False,
        "nova_area_sugerida": "",
        "nome_sugerido": "Nome",
        "descricao_sugerida": "Descrição.",
        "observacoes": "",
    }
    dados.update(extra)
    return json.dumps(dados)


class ContextoTest(BasePainel):
    """O que é calculado em Python, sem LLM: áreas, parecidos e duplicidade."""

    def test_curso_com_o_mesmo_nome_vem_marcado_como_possivel_duplicado(self):
        existente = Curso.objects.filter(is_active=True).first()

        achados = consultor.cursos_semelhantes(existente.nome_curso, existente.descricao)

        self.assertIn(existente, [curso for curso, _, duplicado in achados if duplicado])
        self.assertTrue(achados[0][2])  # duplicados vêm primeiro

    def test_na_edicao_o_proprio_curso_nao_conta_como_parecido(self):
        existente = Curso.objects.filter(is_active=True).first()

        achados = consultor.cursos_semelhantes(existente.nome_curso, existente.descricao, ignorar_id=existente.pk)

        self.assertNotIn(existente, [curso for curso, _, _ in achados])

    def test_curso_inativo_nao_entra(self):
        inativo = self.criar_curso(nome_curso="Robótica Subaquática Avançada", is_active=False)

        achados = consultor.cursos_semelhantes(inativo.nome_curso, inativo.descricao)

        self.assertNotIn(inativo, [curso for curso, _, _ in achados])

    def test_area_nova_entra_sem_cursos_e_sem_pesos_no_quiz(self):
        nova = Area.objects.create(nome="Energia Solar", slug="energia-solar", descricao="Sistemas fotovoltaicos.")
        Area.objects.create(nome="Desativada", slug="desativada", descricao="x", is_active=False)

        areas = {area["slug"]: area for area in consultor.areas_do_catalogo()}

        self.assertEqual(areas[nova.slug]["cursos_ativos"], 0)
        self.assertFalse(areas[nova.slug]["tem_pesos_no_quiz"])
        self.assertNotIn("desativada", areas)
        self.assertTrue(any(area["tem_pesos_no_quiz"] for area in areas.values()))

    def test_descricao_curta_demais_e_recusada(self):
        with self.assertRaises(consultor.EntradaInvalida):
            consultor.montar_contexto("Elétrica", "curto")

    def test_prompt_leva_as_areas_e_o_curso_mas_nao_os_ids(self):
        Area.objects.create(nome="Energia Solar", slug="energia-solar", descricao="Sistemas fotovoltaicos.")
        contexto = consultor.montar_contexto("Eletricista", DESCRICAO)

        prompt = consultor.montar_prompt(contexto)

        self.assertIn('"slug": "energia-solar"', prompt)
        self.assertIn("NR-10", prompt)
        self.assertNotIn('"id":', prompt)


class SaidaTest(BasePainel):
    """A revisão da saída: área inventada nunca chega à tela."""

    def setUp(self):
        super().setUp()
        self.contexto = consultor.montar_contexto("Eletricista", DESCRICAO)
        self.slugs = [area["slug"] for area in self.contexto["areas"]]

    def area(self, slug, peso=4):
        return {"slug": slug, "justificativa": "Porque sim.", "peso": peso}

    def test_area_inventada_ou_repetida_sai_e_ficam_no_maximo_tres(self):
        areas = [self.area("inventada"), self.area(self.slugs[0])] + [self.area(s) for s in self.slugs[:4]]

        dados = consultor.saida_valida(saida(areas=areas), self.contexto)

        self.assertEqual([a["slug"] for a in dados["areas"]], self.slugs[:3])

    def test_so_area_inventada_e_saida_invalida(self):
        with self.assertRaises(LLMInvalidOutput):
            consultor.saida_valida(saida(areas=[self.area("inventada")]), self.contexto)

    def test_peso_fora_de_0_a_5_e_saida_invalida(self):
        with self.assertRaises(LLMInvalidOutput):
            consultor.saida_valida(saida(areas=[self.area(self.slugs[0], peso=9)]), self.contexto)

    def test_texto_sem_json_e_saida_invalida(self):
        with self.assertRaises(LLMInvalidOutput):
            consultor.saida_valida("Não sei.", self.contexto)


class RotaDoConsultorTest(BasePainel):
    URL = "/painel/cursos/consultor/"

    def setUp(self):
        super().setUp()
        cache.clear()
        self.client.force_login(self.criar_staff())

    def pedir(self, descricao=DESCRICAO, **extra):
        return self.client.post(self.URL, {"nome_curso": "Eletricista residencial", "descricao": descricao, **extra})

    def contagem(self):
        return (Curso.objects.count(), Area.objects.count(), Peso_curso.objects.count())

    @LIGADO
    def test_devolve_areas_do_catalogo_e_nao_grava_nada(self):
        antes = self.contagem()

        resposta = self.pedir()

        self.assertEqual(resposta.status_code, 200)
        dados = resposta.json()
        ativas = set(Area.objects.filter(is_active=True).values_list("pk", flat=True))
        self.assertTrue(dados["areas"])
        self.assertTrue({area["id"] for area in dados["areas"]} <= ativas)
        self.assertEqual(self.contagem(), antes)

    @LIGADO
    def test_a_segunda_consulta_igual_vem_do_cache(self):
        self.assertFalse(self.pedir().json()["cache_hit"])
        self.assertTrue(self.pedir().json()["cache_hit"])

    @LIGADO
    def test_area_criada_agora_ja_pode_ser_sugerida(self):
        nova = Area.objects.create(nome="AAA Energia Solar", slug="aaa-energia-solar", descricao="Fotovoltaica.")

        dados = self.pedir().json()

        # O FakeProvider sugere as primeiras áreas do prompt, que vêm por nome.
        self.assertEqual(dados["areas"][0]["id"], nova.pk)
        self.assertFalse(dados["areas"][0]["tem_pesos_no_quiz"])

    @LIGADO
    def test_descricao_curta_volta_400_com_a_mensagem(self):
        resposta = self.pedir(descricao="curta")

        self.assertEqual(resposta.status_code, 400)
        self.assertIn("descrição", resposta.json()["erro"])

    @LIGADO
    def test_provedor_fora_volta_503_e_nao_pausa_o_quiz(self):
        provedor = mock.Mock()
        provedor.complete.side_effect = LLMTimeout("lento")
        with mock.patch("painel.consultor.get_provider", return_value=provedor):
            resposta = self.pedir()

        self.assertEqual(resposta.status_code, 503)
        self.assertIsNone(cache.get(PAUSA))

    @LIGADO
    def test_saida_fora_do_formato_volta_502(self):
        with mock.patch("painel.consultor.get_provider", return_value=ProvedorFixo("sem json")):
            resposta = self.pedir()

        self.assertEqual(resposta.status_code, 502)

    @LIGADO
    def test_usa_o_timeout_proprio_do_consultor(self):
        with mock.patch("painel.consultor.get_provider", return_value=ProvedorFixo(saida())) as fabrica, \
                override_settings(LLM_TIMEOUT_CONSULTOR=25):
            self.pedir()

        fabrica.assert_called_once_with(timeout=25)

    @override_settings(LLM_ENABLED=False)
    def test_com_a_ia_desligada_volta_404(self):
        self.assertEqual(self.pedir().status_code, 404)

    @LIGADO
    def test_so_aceita_post_de_staff(self):
        self.assertEqual(self.client.get(self.URL).status_code, 405)
        self.client.logout()
        self.client.force_login(self.criar_usuario())
        self.assertEqual(self.pedir().status_code, 302)


class TelaDoConsultorTest(BasePainel):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.criar_staff())

    @LIGADO
    def test_modal_de_curso_mostra_o_consultor_com_a_ia_ligada(self):
        self.assertContains(self.client.get("/painel/cursos/"), "data-consultor ")

    @override_settings(LLM_ENABLED=False)
    def test_sem_ia_o_cadastro_fica_como_antes(self):
        self.assertNotContains(self.client.get("/painel/cursos/"), "data-consultor ")
