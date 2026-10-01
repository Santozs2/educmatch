from django.contrib import admin

from .models import LinkDeAvaliacao, Pergunta


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ["ordem", "texto", "tipo", "obrigatoria", "ativa"]
    list_display_links = ["texto"]
    list_filter = ["tipo", "ativa"]


@admin.register(LinkDeAvaliacao)
class LinkDeAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ["curso", "turma", "criado_em", "ativo"]
    list_filter = ["ativo", "curso"]
    readonly_fields = ["token", "criado_em", "criado_por"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)

# As respostas não entram no admin de propósito: o lugar delas é o painel,
# agregado e com supressão. Uma lista resposta a resposta no admin desfaria isso.