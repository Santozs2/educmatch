from quiz.tests.base import BaseEducMatch


class RotasSemApiRest(BaseEducMatch):
    """O front é de templates: a API REST do quiz saiu, e as páginas ficaram."""

    def test_endpoints_da_api_rest_nao_existem_mais(self):
        # Antes respondiam 500 (REV-05); agora simplesmente não existem.
        for rota in ("/quiz/questoes/", "/quiz/envio/", "/quiz/resultados/"):
            self.assertEqual(self.client.get(rota).status_code, 404, rota)

    def test_dashboard_continua_na_mesma_url(self):
        resposta = self.client.get("/quiz/dashboard/")
        self.assertEqual(resposta.status_code, 302)  # anônimo vai para o login
        self.assertIn("/entrar/", resposta["Location"])

    def test_pagina_do_quiz_continua_no_ar(self):
        self.assertEqual(self.client.get("/").status_code, 200)
