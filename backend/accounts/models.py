from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True 
    
    def _criar_usuario(self, email, password, **extra_fields):
        if not email:
            raise ValueError("O e-mail e obrigatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        return self._criar_usuario(email, password, **extra_fields)
    
    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser precisa ter is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser precisa ter is_superuser=True")
        
        return self._criar_usuario(email, password, **extra_fields)




class Interesse(models.Model):
    
    STATUS = [
        ("interessado", "Interessado"),
        ("contatado", "Contatado"),
        ("descartado", "Descartado"),
        ("removido", "Removido pelo aluno"),
    ]
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interesses")
    curso = models.ForeignKey("catalogo.Curso", on_delete=models.PROTECT, related_name="interessados")
    tentativa_origem = models.ForeignKey(
        "quiz.Tentativa_de_resposta",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="interesses",
    )
    # C4: a "foto" do momento em que o aluno salvou o curso. A tentativa pode
    # ser refeita e a recomendação regravada; o snapshot não muda.
    rank_snapshot = models.PositiveSmallIntegerField("posição no momento", null=True, blank=True)
    afinidade_snapshot = models.FloatField("afinidade no momento", null=True, blank=True)
    era_principal = models.BooleanField("era o 1º colocado", default=False)
    status = models.CharField(max_length=20, choices=STATUS, default="interessado")
    nota = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)  # era auto_now: mudava a cada save
    
    
    class Meta:
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "curso"],
                name="unique_usuario_curso"
            )
        ]

    def __str__(self):
        return f"{self.usuario} -> {self.curso} ({self.status})"
    
class User(AbstractUser):
    username = models.CharField(max_length=100)
    email = models.EmailField("e-mail", unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.email