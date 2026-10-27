    
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Area(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    slug = models.SlugField(unique=True)   # chave estavel para a engine de matching

    class Meta:
        ordering = ["nome"]
        
    def __str__(self):
        return self.nome
    

class Curso(models.Model):
    nome_curso = models.CharField(max_length=100)
    descricao = models.TextField()
    area_principal = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='cursos')
    duracao = models.PositiveIntegerField(help_text="Duração do curso em horas")
    inicio_dia = models.DateField(null=True, blank=True)
    fim_dia = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ["nome_curso"]
        
    def __str__(self):
        return self.nome_curso

    
class Peso_curso(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='curso_peso')
    area = models.ForeignKey(Area, on_delete=models.CASCADE, null=True, blank=True, related_name='area_peso')
    peso = models.FloatField( default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)],)
    
    class Meta:
        unique_together = ("curso", "area")
        ordering = ["-peso"]

    def __str__(self):
        return f"{self.curso.nome_curso} - {self.area.nome}: {self.peso}"