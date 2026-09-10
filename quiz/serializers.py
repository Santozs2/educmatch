from rest_framework import serializers
from quiz.models import Alternativa, Questao, Recomendacao

class AlternativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternativa
        fields = '__all__'
        
class QuestaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questao
        fields = '__all__'
        
class RecomendacaoSerializer(serializers.ModelSerializer):
    nome_curso = serializers.CharField(source='curso.nome', read_only=True)
    descricao_curso = serializers.CharField(source='curso.descricao', read_only=True)
    duracao_curso = serializers.IntegerField(source='curso.duracao', read_only=True)
    id_curso = serializers.IntegerField(source='curso.id', read_only=True)
    
    class Meta:
        model = Recomendacao
        fields = '__all__'
        
class RespostaSerializer(serializers.Serializer):
    questao = serializers.PrimaryKeyRelatedField(queryset=Questao.objects.all())
    choice = serializers.PrimaryKeyRelatedField(queryset=Alternativa.objects.all())
    
    def validar(self, data):
        questao = data['questao']
        choice = data['choice']
        
        if choice.questao != questao:
            raise serializers.ValidationError("A alternativa selecionada não pertence à questão fornecida.")
        return data
    
class EnvioSerializer(serializers.Serializer):
    respondido_por = serializers.CharField(max_length=100, required=False, allow_blank=True)
    respostas = RespostaSerializer(many=True)
    
    def validar_resposta(self, resposta):
        questao = resposta['questao']
        choice = resposta['choice']
        
        if choice.questao != questao:
            raise serializers.ValidationError("A alternativa selecionada não pertence à questão fornecida.")
        
        return resposta