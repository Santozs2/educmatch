from datetime import timedelta
from pathlib import Path

from django.urls import reverse
from django.utils import timezone

from accounts.models import Interesse
from catalogo.models import Area, Curso
from painel import metricas
from painel.tests.base import BasePainel
from quiz.models import QuestionarioLink, Tentativa_de_resposta

# Uma quantidade qualquer de testes ou respostas. O painel mostra tudo (K_MINIMO = 0),
# então nenhum teste daqui depende da regra antiga dos 5.
ALGUNS = 5


PASTA_DE_TEMPLATES = Path(__file__).resolve().parents[1] / "templates" / "painel"
BOTOES_FANTASMA = ("botao--contorno", "botao--texto", "botao--fantasma")


class CascaDoPainelTest(BasePainel):
    """Etapa 1: menu, período e a regra de nenhum botão fantasma."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.criar_staff())

    def test_menu_leva_o_periodo_escolhido(self):
        resposta = self.client.get(reverse("painel-dashboard"), {"periodo": "anual"})

        self.assertContains(resposta, 'href="/painel/quiz/?periodo=anual"')

    def test_periodo_invalido_cai_no_mensal(self):
        resposta = self.client.get(reverse("painel-quiz"), {"periodo": "semanal"})

        self.assertEqual(resposta.context["periodo"], "mensal")

    def test_menu_marca_a_tela_atual(self):
        resposta = self.client.get(reverse("painel-quiz"))

        self.assertContains(resposta, 'href="/painel/quiz/?periodo=mensal" aria-current="page"')

    def test_painel_tem_link_para_voltar_ao_teste(self):
        link = QuestionarioLink.objects.create()
        resposta = self.client.get(reverse("painel-dashboard"))

        self.assertContains(resposta, 'Voltar ao teste')
        self.assertContains(resposta, reverse("questionario-link", args=[link.token]))

    def test_nenhum_template_do_painel_usa_botao_fantasma(self):
        for arquivo in PASTA_DE_TEMPLATES.glob("*.html"):
            texto = arquivo.read_text(encoding="utf-8")
            for classe in BOTOES_FANTASMA:
                with self.subTest(arquivo=arquivo.name, classe=classe):
                    self.assertNotIn(classe, texto)

    def test_tela_servida_tambem_nao_tem_botao_fantasma(self):
        self.criar_tentativas(quantidade=ALGUNS)
        for tela in ("painel-dashboard", "painel-quiz", "painel-cursos", "painel-links", "painel-interesse"):
            corpo = self.client.get(reverse(tela)).content.decode()
            for classe in BOTOES_FANTASMA:
                with self.subTest(tela=tela, classe=classe):
                    self.assertNotIn(classe, corpo)


class MetricasDoInicioTest(BasePainel):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.criar_staff())

    def test_dia_com_poucos_testes_aparece_na_serie(self):
        tentativas = self.criar_tentativas(quantidade=ALGUNS + 2)
        ontem = timezone.now() - timedelta(days=1)
        Tentativa_de_resposta.objects.filter(pk__in=[t.pk for t in tentativas[:2]]).update(criado_em=ontem)

        serie = self.client.get(reverse("painel-dashboard")).context["serie"]

        self.assertEqual([linha["total"] for linha in serie], [2, ALGUNS])

    def test_atividade_recente_mostra_tudo(self):
        self.criar_tentativas(quantidade=ALGUNS)

        atividade = self.client.get(reverse("painel-dashboard")).context["atividade"]

        testes_na_hora, _, cursos_salvos = atividade
        self.assertEqual(testes_na_hora["total"], ALGUNS)
        self.assertEqual(cursos_salvos["total"], 0)

    def test_conversao_geral_com_um_interesse(self):
        tentativas = self.criar_tentativas(quantidade=ALGUNS)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        Interesse.objects.create(usuario=self.criar_usuario("um@exemplo.com"), curso=curso)

        recomendacoes = sum(t.recomendacoes.count() for t in tentativas)
        self.assertAlmostEqual(metricas.conversao_geral(None), 1 / recomendacoes * 100)

    def test_conversao_geral_e_salvos_sobre_recomendados(self):
        tentativas = self.criar_tentativas(quantidade=ALGUNS)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        for i in range(ALGUNS):
            Interesse.objects.create(usuario=self.criar_usuario(f"aluno{i}@exemplo.com"), curso=curso)

        recomendacoes = sum(t.recomendacoes.count() for t in tentativas)
        self.assertAlmostEqual(metricas.conversao_geral(None), ALGUNS / recomendacoes * 100)

    def test_aderencia_com_um_primeiro(self):
        tentativas = self.criar_tentativas(quantidade=ALGUNS)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        Interesse.objects.create(
            usuario=self.criar_usuario("um@exemplo.com"), curso=curso, rank_snapshot=1, era_principal=True
        )

        aderencia = self.client.get(reverse("painel-quiz")).context["aderencia"]

        self.assertEqual(aderencia["taxa"], 100)

    def test_aderencia_sem_nenhum_curso_salvo_nao_quebra(self):
        self.criar_tentativas(quantidade=ALGUNS)

        resposta = self.client.get(reverse("painel-quiz"))

        self.assertEqual(resposta.status_code, 200)
        self.assertIsNone(resposta.context["aderencia"]["taxa"])

class TelasDeCadastroTest(BasePainel):
    """Etapa 2: Cursos e Áreas, Links de acesso e Lista de interesse."""

    TELAS = ("painel-cursos", "painel-links", "painel-interesse")

    def setUp(self):
        super().setUp()
        self.staff = self.criar_staff()

    def test_so_staff_entra(self):
        comum = self.criar_usuario("aluno@exemplo.com")
        for tela in self.TELAS:
            with self.subTest(tela=tela):
                self.client.logout()
                self.assertEqual(self.client.get(reverse(tela)).status_code, 302)
                self.client.force_login(comum)
                self.assertNotEqual(self.client.get(reverse(tela)).status_code, 200)
                self.client.force_login(self.staff)
                self.assertEqual(self.client.get(reverse(tela)).status_code, 200)

    def test_testes_por_link_aparecem(self):
        self.client.force_login(self.staff)
        link = QuestionarioLink.objects.create(criado_por=self.staff)
        tentativas = self.criar_tentativas(quantidade=2)
        Tentativa_de_resposta.objects.filter(pk__in=[t.pk for t in tentativas]).update(
            questionario_link=link,
            criado_em=timezone.now() - timedelta(days=40),
        )

        resposta = self.client.get(reverse("painel-links"), {"periodo": "diario"})
        linhas = resposta.context["links"]

        self.assertNotIn("suprimido", linhas[0])
        self.assertEqual(linhas[0]["total"], 2)
        self.assertContains(resposta, "Histórico completo")
        self.assertNotContains(resposta, "Aplicar")

    def test_novo_curso_abre_modal_no_painel(self):
        self.client.force_login(self.staff)

        resposta = self.client.get(reverse("painel-cursos"))

        self.assertContains(resposta, 'data-abrir-curso')
        self.assertContains(resposta, 'id="painel-criar-curso"')
        self.assertContains(resposta, 'name="nome_curso"')
        self.assertContains(resposta, 'name="descricao"')
        self.assertContains(resposta, 'name="area_principal"')
        self.assertContains(resposta, 'name="is_active"')
        self.assertNotContains(resposta, "admin:catalogo_curso_add")

    def test_cursos_e_areas_ignora_filtro_de_periodo(self):
        self.client.force_login(self.staff)
        curso = Curso.objects.first()
        area = curso.area_principal
        tentativa_antiga = self.criar_tentativa_com_explicacao({"top_areas": [{"area": area.slug}]})
        Tentativa_de_resposta.objects.filter(pk=tentativa_antiga.pk).update(
            criado_em=timezone.now() - timedelta(days=40)
        )
        self.criar_tentativa_com_explicacao({"top_areas": [{"area": area.slug}]})

        resposta = self.client.get(reverse("painel-cursos"), {"periodo": "diario"})

        linha = next(linha for linha in resposta.context["cursos"] if linha["id"] == curso.pk)
        demanda = next(linha for linha in resposta.context["demanda_por_area"] if linha["area"] == area.slug)
        self.assertEqual(linha["em_primeiro"], 2)
        self.assertEqual(linha["no_top5"], 2)
        self.assertEqual(demanda["total"], 2)
        self.assertContains(resposta, "Histórico completo")
        self.assertNotContains(resposta, "Aplicar")

    def test_editar_curso_abre_modal_com_dados_e_salva_alteracoes(self):
        self.client.force_login(self.staff)
        curso = self.criar_curso(nome_curso="Curso para editar")
        peso_existente = curso.curso_peso.create(area=curso.area_principal, peso=1)
        prefixo = f"curso_peso-{curso.pk}"

        pagina = self.client.get(reverse("painel-cursos"))

        self.assertContains(pagina, f'data-abrir-curso="painel-editar-curso-{curso.pk}"')
        self.assertContains(pagina, f'id="curso-{curso.pk}-nome_curso"')
        self.assertNotContains(pagina, "admin:catalogo_curso_change")

        dados = {
            "nome_curso": "Curso editado pelo painel",
            "descricao": curso.descricao,
            "area_principal": curso.area_principal_id,
            "duracao": 160,
            "inicio_dia": "",
            "fim_dia": "",
            "is_active": "on",
            f"{prefixo}-TOTAL_FORMS": "8",
            f"{prefixo}-INITIAL_FORMS": "1",
            f"{prefixo}-MIN_NUM_FORMS": "0",
            f"{prefixo}-MAX_NUM_FORMS": "1000",
            f"{prefixo}-0-id": peso_existente.pk,
            f"{prefixo}-0-area": curso.area_principal_id,
            f"{prefixo}-0-peso": "3",
        }
        for indice in range(8):
            dados[f"{prefixo}-{indice}-curso"] = curso.pk
        for indice in range(1, 8):
            dados[f"{prefixo}-{indice}-area"] = ""
            dados[f"{prefixo}-{indice}-peso"] = "0"

        resposta = self.client.post(
            reverse("painel-editar-curso", args=[curso.pk]),
            dados,
        )

        self.assertRedirects(resposta, reverse("painel-cursos"))
        curso.refresh_from_db()
        self.assertEqual(curso.nome_curso, "Curso editado pelo painel")
        self.assertEqual(curso.duracao, 160)
        peso_existente.refresh_from_db()
        self.assertEqual(curso.curso_peso.count(), 1)
        self.assertEqual(peso_existente.peso, 3)

    def test_remover_curso_desativa_sem_apagar_historico(self):
        self.client.force_login(self.staff)
        curso = self.criar_curso(nome_curso="Curso para remover")
        peso = curso.curso_peso.create(area=curso.area_principal, peso=2)

        resposta = self.client.post(reverse("painel-remover-curso", args=[curso.pk]))

        self.assertRedirects(resposta, reverse("painel-cursos"))
        curso.refresh_from_db()
        self.assertFalse(curso.is_active)
        self.assertTrue(curso.curso_peso.filter(pk=peso.pk).exists())

    def test_criar_curso_no_painel_salva_pesos_por_area(self):
        self.client.force_login(self.staff)
        area = self.criar_curso().area_principal
        dados = {
            "nome_curso": "Novo curso pelo painel",
            "descricao": "Descrição completa",
            "area_principal": area.pk,
            "duracao": 120,
            "inicio_dia": "",
            "fim_dia": "",
            "is_active": "on",
            "curso_peso-TOTAL_FORMS": "7",
            "curso_peso-INITIAL_FORMS": "0",
            "curso_peso-MIN_NUM_FORMS": "0",
            "curso_peso-MAX_NUM_FORMS": "1000",
        }
        for indice in range(7):
            dados[f"curso_peso-{indice}-area"] = str(area.pk) if indice == 0 else ""
            dados[f"curso_peso-{indice}-peso"] = "2" if indice == 0 else "0"

        resposta = self.client.post(reverse("painel-cursos"), dados)

        self.assertRedirects(resposta, reverse("painel-cursos"))
        curso = Curso.objects.get(nome_curso="Novo curso pelo painel")
        self.assertEqual(curso.curso_peso.get().area, area)
        self.assertEqual(curso.curso_peso.get().peso, 2)

    def test_peso_decimal_nao_cria_curso(self):
        self.client.force_login(self.staff)
        area = self.criar_curso().area_principal
        dados = {
            "nome_curso": "Curso com peso decimal",
            "descricao": "Descrição completa",
            "area_principal": area.pk,
            "duracao": 120,
            "inicio_dia": "",
            "fim_dia": "",
            "is_active": "on",
            "curso_peso-TOTAL_FORMS": "7",
            "curso_peso-INITIAL_FORMS": "0",
            "curso_peso-MIN_NUM_FORMS": "0",
            "curso_peso-MAX_NUM_FORMS": "1000",
        }
        for indice in range(7):
            dados[f"curso_peso-{indice}-area"] = str(area.pk) if indice == 0 else ""
            dados[f"curso_peso-{indice}-peso"] = "2.5" if indice == 0 else "0"

        resposta = self.client.post(reverse("painel-cursos"), dados)

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Curso.objects.filter(nome_curso="Curso com peso decimal").exists())
        self.assertContains(resposta, 'data-abrir="true"')

    def test_criar_area_no_painel_gera_slug_a_partir_do_nome(self):
        self.client.force_login(self.staff)

        resposta = self.client.post(
            reverse("painel-criar-area"),
            {"nome": "Elétrica Industrial", "descricao": "Área criada pelo painel"},
        )

        self.assertRedirects(resposta, reverse("painel-cursos"))
        area = Area.objects.get(nome="Elétrica Industrial")
        self.assertEqual(area.slug, "eletrica-industrial")

    def test_criar_area_com_nome_repetido_nao_duplica(self):
        self.client.force_login(self.staff)
        existente = Area.objects.first()

        resposta = self.client.post(
            reverse("painel-criar-area"),
            {"nome": existente.nome.lower(), "descricao": "Tentativa de duplicar"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Area.objects.filter(nome__iexact=existente.nome).count(), 1)
        self.assertContains(resposta, 'data-abrir="true"')

    def test_nomes_diferentes_com_mesmo_slug_nao_colidem(self):
        """Dois nomes distintos podem reduzir ao mesmo slug; a chave do matching é única."""
        self.client.force_login(self.staff)

        self.client.post(reverse("painel-criar-area"), {"nome": "Saúde & Bem-estar", "descricao": "Primeira"})
        resposta = self.client.post(
            reverse("painel-criar-area"), {"nome": "Saúde / Bem estar", "descricao": "Segunda"}
        )

        self.assertRedirects(resposta, reverse("painel-cursos"))
        slugs = sorted(Area.objects.filter(nome__startswith="Saúde").values_list("slug", flat=True))
        self.assertEqual(slugs, ["saude-bem-estar", "saude-bem-estar-2"])

    def test_area_criada_aparece_na_tela_de_cursos(self):
        self.client.force_login(self.staff)
        self.client.post(reverse("painel-criar-area"), {"nome": "Logística", "descricao": "Nova"})

        resposta = self.client.get(reverse("painel-cursos"))

        self.assertContains(resposta, "Logística")
        self.assertContains(resposta, "logistica")

    def test_criar_area_exige_staff(self):
        resposta = self.client.post(
            reverse("painel-criar-area"), {"nome": "Sem permissão", "descricao": "x"}
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(Area.objects.filter(nome="Sem permissão").exists())

    def test_fechar_um_link_nao_fecha_os_outros(self):
        self.client.force_login(self.staff)
        primeiro, segundo = (QuestionarioLink.objects.create(criado_por=self.staff) for _ in range(2))

        resposta = self.client.post(
            reverse("painel-fechar-um-link", args=[primeiro.pk]), {"voltar": "painel-links"}
        )

        self.assertRedirects(resposta, reverse("painel-links"))
        primeiro.refresh_from_db()
        segundo.refresh_from_db()
        self.assertFalse(primeiro.ativo)
        self.assertTrue(segundo.ativo)

    def test_voltar_para_endereco_de_fora_cai_no_inicio(self):
        self.client.force_login(self.staff)

        resposta = self.client.post(reverse("painel-gerar-link"), {"voltar": "https://exemplo.com/"})

        self.assertRedirects(resposta, reverse("painel-dashboard"))

    def test_lista_de_interesse_nao_mostra_quem_salvou(self):
        self.client.force_login(self.staff)
        tentativas = self.criar_tentativas(quantidade=ALGUNS)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        emails = [f"pessoa{i}@exemplo.com" for i in range(ALGUNS)]
        for email in emails:
            Interesse.objects.create(usuario=self.criar_usuario(email), curso=curso, era_principal=True)

        resposta = self.client.get(reverse("painel-interesse"))

        linha = next(l for l in resposta.context["por_curso"] if l["id"] == curso.id)
        self.assertEqual(linha["total"], ALGUNS)
        self.assertEqual(linha["taxa_principal"], 100)
        for email in emails:
            self.assertNotContains(resposta, email)

    def test_taxa_de_1o_colocado_aparece_com_contagem_pequena(self):
        self.client.force_login(self.staff)
        tentativas = self.criar_tentativas(quantidade=ALGUNS)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        for i in range(ALGUNS):
            Interesse.objects.create(
                usuario=self.criar_usuario(f"pessoa{i}@exemplo.com"), curso=curso, era_principal=(i == 0)
            )

        linhas = self.client.get(reverse("painel-interesse")).context["por_curso"]

        linha = next(l for l in linhas if l["id"] == curso.id)
        self.assertEqual(linha["principal"], 1)
        self.assertEqual(linha["taxa_principal"], 1 / ALGUNS * 100)

    def test_funil_segue_a_ordem_dos_status(self):
        self.client.force_login(self.staff)
        self.criar_tentativas(quantidade=ALGUNS)

        funil = self.client.get(reverse("painel-interesse")).context["funil"]

        self.assertEqual([etapa["status"] for etapa in funil], [chave for chave, _ in Interesse.STATUS])