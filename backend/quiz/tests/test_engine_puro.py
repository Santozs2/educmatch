from django.test import SimpleTestCase

from quiz.engine import afinidade as cosseno


class MatematicaTest(SimpleTestCase):
    """SimpleTestCase: nao abre banco, roda em milissegundos.

    Isso so e possivel porque a engine tem funcoes puras separadas do ORM --
    a decisao do Passo 4 se pagando, e um paragrafo pronto para a monografia.
    """

    def test_vetores_identicos_dao_1(self):
        self.assertAlmostEqual(cosseno({"ti": 3}, {"ti": 3}), 1.0)

    def test_sem_area_em_comum_da_0(self):
        self.assertAlmostEqual(cosseno({"ti": 3}, {"costura": 3}), 0.0)

    def test_vetor_vazio_nao_estoura(self):
        """Guarda do divisor zero: quiz em branco."""
        self.assertAlmostEqual(cosseno({}, {"ti": 3}), 0.0)

    def test_escala_nao_muda_o_score(self):
        """O teste que protege a DECISAO de usar cosseno, nao uma linha de codigo.

        Dobra todos os pesos do perfil e exige o mesmo resultado. Se alguem
        trocar o cosseno por soma de produtos, este e o primeiro a quebrar.
        """
        perfil = {"ti": 3, "eletrica": 1}
        curso = {"ti": 2, "eletrica": 2}
        self.assertAlmostEqual(
            cosseno(perfil, curso),
            cosseno({k: v * 2 for k, v in perfil.items()}, curso),
        )