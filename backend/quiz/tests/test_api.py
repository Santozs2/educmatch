from rest_framework import status

from quiz.tests.base import BaseEducMatch


class ApiQuizTest(BaseEducMatch):
    def test_lista_de_questoes_responde_200(self):
        """REV-05: este endpoint respondia 500 desde sempre."""
        resposta = self.client.get("/api/quiz/questoes/")
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.json()), 6)

    def test_envio_completo_gera_cinco_recomendacoes(self):
        resposta = self.client.post("/api/quiz/enviar/", self.payload_valido(), format="json")
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(resposta.json()["recomendacoes"]), 5)

    def test_duas_respostas_para_a_mesma_questao_da_400_e_nao_500(self):
        """O guardiao do validate_<campo>: se o metodo se chamar `validar`,
        a validacao nao roda, o unique_together estoura e isto vira 500."""
        payload = self.payload_valido()
        payload["respostas"].append(payload["respostas"][0])

        resposta = self.client.post("/api/quiz/enviar/", payload, format="json")

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quiz_incompleto_da_400(self):
        """O JS impede avancar sem responder; curl ignora o JS."""
        payload = self.payload_valido()
        payload["respostas"] = payload["respostas"][:2]

        resposta = self.client.post("/api/quiz/enviar/", payload, format="json")

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)