from django.urls import reverse

from accounts.models import Interesse
from accounts.servicos import registrar_interesse
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class C4SnapshotTest(BaseEducMatch):
    """C4: ao salvar um curso, o Interesse guarda a foto do ranking."""

    def setUp(self):
        super().setUp()
        self.usuario = self.criar_usuario()
        self.client.force_login(self.usuario)
        self.responder_tudo()
        self.tentativa = Tentativa_de_resposta.objects.latest("id")

    def salvar(self, rec):
        return self.client.post(
            reverse("interesse-salvar"),
            {"curso_id": rec.curso_id, "tentativa_id": self.tentativa.pk},
        )

    def test_salvar_o_primeiro_lugar_grava_o_snapshot(self):
        primeiro = self.tentativa.recomendacoes.get(rank=1)

        self.salvar(primeiro)

        item = Interesse.objects.get(usuario=self.usuario, curso=primeiro.curso)
        self.assertEqual(item.tentativa_origem, self.tentativa)
        self.assertEqual(item.rank_snapshot, 1)
        self.assertAlmostEqual(item.afinidade_snapshot, primeiro.score)
        self.assertTrue(item.era_principal)

    def test_salvar_o_terceiro_lugar_nao_e_principal(self):
        terceiro = self.tentativa.recomendacoes.get(rank=3)

        self.salvar(terceiro)

        item = Interesse.objects.get(usuario=self.usuario, curso=terceiro.curso)
        self.assertEqual(item.rank_snapshot, 3)
        self.assertFalse(item.era_principal)

    def test_registrar_de_novo_nao_reescreve_a_foto(self):
        """Idempotente: a segunda chamada devolve o mesmo interesse, intacto."""
        primeiro = self.tentativa.recomendacoes.get(rank=1)
        item, criado = registrar_interesse(self.usuario, primeiro.curso, self.tentativa)

        de_novo, criado_de_novo = registrar_interesse(self.usuario, primeiro.curso, None)

        self.assertTrue(criado)
        self.assertFalse(criado_de_novo)
        self.assertEqual(de_novo.pk, item.pk)
        self.assertEqual(de_novo.rank_snapshot, 1)

    def test_criado_em_nao_muda_quando_o_interesse_e_salvo_de_novo(self):
        """REV-01: com auto_now, a data mudava a cada save."""
        primeiro = self.tentativa.recomendacoes.get(rank=1)
        item, _ = registrar_interesse(self.usuario, primeiro.curso, self.tentativa)
        antes = item.criado_em

        item.status = "contatado"
        item.save()
        item.refresh_from_db()

        self.assertEqual(item.criado_em, antes)
        

class RemoverNaoApagaTest(BaseEducMatch):
    """A foto do C4 sobrevive a remover e salvar de novo."""

    def setUp(self):
        super().setUp()
        self.usuario = self.criar_usuario()
        self.client.force_login(self.usuario)
        self.responder_tudo()
        self.tentativa = Tentativa_de_resposta.objects.latest("id")
        self.primeiro = self.tentativa.recomendacoes.get(rank=1)

    def salvar(self):
        return self.client.post(
            reverse("interesse-salvar"),
            {"curso_id": self.primeiro.curso_id, "tentativa_id": self.tentativa.pk},
        )

    def remover(self):
        return self.client.post(reverse("interesse-remover"), {"curso_id": self.primeiro.curso_id})

    def item(self):
        return Interesse.objects.get(usuario=self.usuario, curso=self.primeiro.curso)

    def test_salvar_duas_vezes_nao_apaga(self):
        self.salvar()
        self.salvar()

        self.assertEqual(self.item().status, "interessado")

    def test_remover_muda_o_status_e_mantem_a_foto(self):
        self.salvar()
        self.remover()

        self.assertEqual(self.item().status, "removido")
        self.assertEqual(self.item().rank_snapshot, 1)

    def test_salvar_de_novo_religa_com_a_foto_original(self):
        self.salvar()
        self.remover()
        self.salvar()

        self.assertEqual(self.item().status, "interessado")
        self.assertEqual(self.item().rank_snapshot, 1)
        self.assertTrue(self.item().era_principal)

    def test_remover_pela_minha_lista_tambem_nao_apaga(self):
        self.salvar()

        self.client.post(reverse("remover_interesse", args=[self.item().pk]))

        self.assertEqual(self.item().status, "removido")

    def test_minha_lista_nao_mostra_removido(self):
        self.salvar()
        self.remover()

        resposta = self.client.get(reverse("lista_interesse"))

        self.assertNotContains(resposta, self.primeiro.curso.nome_curso)

    def test_remover_por_get_nao_funciona(self):
        self.salvar()

        resposta = self.client.get(reverse("interesse-remover"))

        self.assertEqual(resposta.status_code, 405)
        self.assertEqual(self.item().status, "interessado")

    def test_tentativa_de_outra_pessoa_nao_empresta_a_foto(self):
        """C6: o snapshot só vem de tentativa que a pessoa pode ver."""
        alheia = self.criar_tentativa(dono=self.criar_usuario("outra@exemplo.com"))
        rec = alheia.recomendacoes.get(rank=1)

        self.client.post(reverse("interesse-salvar"), {"curso_id": rec.curso_id, "tentativa_id": alheia.pk})

        item = Interesse.objects.get(usuario=self.usuario, curso=rec.curso)
        self.assertIsNone(item.tentativa_origem)
        self.assertIsNone(item.rank_snapshot)