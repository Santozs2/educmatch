    
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Area(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    slug = models.SlugField(unique=True)   # chave estavel para a engine de matching
    # Área inativa some das listas, mas continua no banco: o histórico cita ela.
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        
    def __str__(self):
        return self.nome
    

class Curso(models.Model):
    NIVEIS = [
        ("livre", "Cursos Livres"),
        ("aprendiz", "Aprendiz SENAI"),
        ("graduacao", "Graduação"),
    ]
    UNIDADES_DE_CARGA = [
        ("horas", "horas"),
        ("horas_aula", "horas/aula"),
    ]

    nome_curso = models.CharField(max_length=150)
    # Número final do link do SENAI. O nome não serve de chave: há cursos com o mesmo nome.
    codigo_senai = models.CharField(max_length=20, unique=True, null=True, blank=True)
    descricao = models.TextField()
    area_principal = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='cursos')
    nivel = models.CharField(max_length=20, choices=NIVEIS, default="livre")
    modalidade = models.CharField(max_length=30, default="Presencial")
    duracao = models.PositiveIntegerField(help_text="Carga horária do curso, na unidade escolhida")
    unidade_carga = models.CharField(max_length=20, choices=UNIDADES_DE_CARGA, default="horas")
    url_senai = models.URLField(max_length=300, blank=True)
    consultado_em = models.DateField(null=True, blank=True)
    inicio_dia = models.DateField(null=True, blank=True)
    fim_dia = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ["nome_curso"]
        
    def __str__(self):
        return self.nome_curso

    @property
    def carga_horaria(self):
        return f"{self.duracao} {self.get_unidade_carga_display()}"

    @property
    def aceita_inscricao_direta(self):
        """Aprendiz e graduação têm processo próprio: o botão não promete inscrição."""
        return self.nivel == "livre"

    
class Peso_curso(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='curso_peso')
    area = models.ForeignKey(Area, on_delete=models.CASCADE, null=True, blank=True, related_name='area_peso')
    peso = models.FloatField( default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)],)
    
    class Meta:
        unique_together = ("curso", "area")
        ordering = ["-peso"]

    def __str__(self):
        return f"{self.curso.nome_curso} - {self.area.nome}: {self.peso}"