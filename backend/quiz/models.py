import uuid

from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

class Questao(models.Model):
    texto = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.texto    
    

class Alternativa(models.Model):
    texto = models.TextField()
    order = models.IntegerField(default=0)
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name="alternativas")
    
    class Meta:
        ordering = ["order"]
        
    def __str__(self):
        return self.texto
    
class Peso_alternativa(models.Model):
    alternativa = models.ForeignKey(Alternativa, on_delete=models.CASCADE, related_name="pesos")
    area = models.ForeignKey('catalogo.Area', on_delete=models.CASCADE, related_name="pesos")
    peso = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5)])   
    
    class Meta:
        unique_together = ('alternativa', 'area')
        ordering = ["-peso"]
        
    def __str__(self):
        return f"{self.alternativa.texto} - Peso: {self.peso}"
    
class Tentativa_de_resposta(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tentativas",
    )
    questionario_link = models.ForeignKey(
        "quiz.QuestionarioLink",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tentativas",
    )
    respondido_por = models.TextField(blank=True)
    score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5)])   
    diferenca = models.FloatField(null=True, blank=True, help_text="Diferença entre o primeiro e o segundo colocado.")
    CONFIDENCE_CHOICE_NIVEIS = [
        ("alta", "Alta"),
        ("media", "Média"),
        ("baixa", "Baixa"),
    ]
    confidence_band = models.CharField(max_length=10, choices=CONFIDENCE_CHOICE_NIVEIS, default="")
    tie_set = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ["-criado_em"]
        indexes = [models.Index(fields=["criado_em"], name="idx_tentativa_criado_em")]
        
    def __str__(self):
        nome_usuario = self.user.email if self.user else "anônimo"
        return f"Tentativa de {nome_usuario} em {self.criado_em.strftime('%Y-%m-%d %H:%M:%S')} - Nota: {self.score}"


class QuestionarioLink(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="links_de_questionario",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Questionário {self.token}"

class Resposta(models.Model):
    tentativa = models.ForeignKey(Tentativa_de_resposta, on_delete=models.CASCADE, related_name="respostas")
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name="respostas")
    alternativa = models.ForeignKey(Alternativa, on_delete=models.CASCADE, related_name="respostas")
    
    class Meta:
        unique_together = ('tentativa', 'questao')
        
    def __str__(self):
        return f"Resposta da tentativa {self.tentativa.id} para a questão {self.questao.id}: {self.alternativa.texto}"


class Recomendacao(models.Model):
    tentativa = models.ForeignKey(Tentativa_de_resposta, on_delete=models.CASCADE, related_name="recomendacoes")
    curso = models.ForeignKey('catalogo.Curso', on_delete=models.CASCADE, related_name="recomendacoes")
    score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5)])
    rank = models.IntegerField(default=0)
    explicacao = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ('tentativa', 'curso')
        ordering = ["rank"]
        indexes = [models.Index(fields=["rank", "curso"], name="idx_rec_rank_curso")]
   
    @property
    def is_primary(self):
        return self.rank == 1
        
    def __str__(self):
        return f"Recomendação do curso {self.curso.nome_curso} para a tentativa {self.tentativa.id} - Score: {self.score}, Rank: {self.rank}"