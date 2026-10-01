"""Avaliação de fim de curso: perguntas fixas, um link por turma, respostas anônimas.

Nenhum model deste app guarda usuário, nome, e-mail, IP ou horário. A resposta
sabe só o link (e por ele o curso e a turma) e o DIA em que chegou. É isso que
permite dizer à turma "é anônimo" sem precisar de promessa: não há onde guardar.
"""
import uuid

from django.conf import settings
from django.db import models


class Pergunta(models.Model):
    TIPOS = [
        ("nps", "Nota de 0 a 10"),
        ("escala", "Escala de 1 a 5"),
        ("escolha", "Escolha única"),
        ("texto", "Texto livre"),
    ]

    texto = models.CharField(max_length=200)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    # Só para "escolha": a lista de opções, na ordem em que aparecem.
    opcoes = models.JSONField(default=list, blank=True)
    obrigatoria = models.BooleanField(default=True)
    ordem = models.PositiveSmallIntegerField(unique=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["ordem"]

    def __str__(self):
        return f"{self.ordem}. {self.texto}"


class LinkDeAvaliacao(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    curso = models.ForeignKey("catalogo.Curso", on_delete=models.PROTECT, related_name="links_de_avaliacao")
    turma = models.CharField(max_length=60, help_text='Como a escola chama a turma. Ex.: "2026/1 · Noite"')
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "link de avaliação"
        verbose_name_plural = "links de avaliação"

    def __str__(self):
        return f"{self.curso} · {self.turma}"


class RespostaDeAvaliacao(models.Model):
    link = models.ForeignKey(LinkDeAvaliacao, on_delete=models.PROTECT, related_name="respostas")
    # Data e não data e hora: "respondeu às 10h14" junto com a turma aponta para uma pessoa.
    respondido_em = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "resposta de avaliação"
        verbose_name_plural = "respostas de avaliação"


class ItemDeResposta(models.Model):
    resposta = models.ForeignKey(RespostaDeAvaliacao, on_delete=models.CASCADE, related_name="itens")
    pergunta = models.ForeignKey(Pergunta, on_delete=models.PROTECT, related_name="itens")
    numero = models.PositiveSmallIntegerField(null=True, blank=True)  # nps e escala
    texto = models.TextField(blank=True)  # escolha e texto

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["resposta", "pergunta"], name="uma_resposta_por_pergunta"),
        ]