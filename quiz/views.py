from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from quiz.engine import Recomendacao
from quiz.models import Resposta, Questao, Tentativa_de_resposta
from quiz.serializers import RecomendacaoSerializer, Questao, EnvioSerializer, QuestaoSerializer

class QuestaoList(generics.ListAPIView):
    queryset = Questao.objects.all()
    serializer_class = Questao
    
class EnvioQuiz(APIView):
    def post(self, request):
        entrada = EnvioSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        
        with transaction.atomic():
            tentativa = Tentativa_de_resposta.objects.create(usuario=request.user)
            Resposta.objects.bulk_create(
                [
                    Resposta(tentativa=tentativa, questao=item["questao"], alternativa=item["alternativa"])
                    for item in dados["respostas"]
                ]
            )
            recomendacoes = Recomendacao(tentativa)
        return Response({"tentativa_id": tentativa.id, "recomendacoes" : RecomendacaoSerializer(recomendacoes, many=True). data}, status=status.HTTP_201_CREATED)
    
class ResultadoQuestao(generics.RetrieveAPIView):
    queryset = Questao.objects.all()
    serializer_class = QuestaoSerializer
    
    def recuerar(self, request, *args, **kwargs):
        tentativa = self.get_object.all()
        dados = RecomendacaoSerializer(tentativa, many=True).data
        return Response(dados, status=status.HTTP_200_OK)