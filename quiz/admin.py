from django.contrib import admin
from .models import (Alternativa, Tentativa_de_resposta, Questao, Recomendacao, Resposta, Peso_alternativa)


class AlternativaInline(admin.TabularInline):
    model = Alternativa
    extra = 7

@admin.register(Questao)
class QuestaoAdmin(admin.ModelAdmin):
    list_display = ['texto', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['texto']
    inlines = [AlternativaInline]
    
class AlternativaPeso(admin.TabularInline):
    model = Peso_alternativa
    extra = 7 
    autcomplete_fields = ['area']
    
@admin.register(Alternativa)
class AlternativaAdmin(admin.ModelAdmin):
    list_display = ['texto', 'questao', 'order']
    search_fields = ['texto']
    inlines = [AlternativaPeso]
    
class RespostaInline(admin.TabularInline):
    model = Resposta
    extra = 0
    
class RecomendacaoInline(admin.TabularInline):
    model = Recomendacao
    extra = 0
    readonly_fields = ['curso', 'score', 'rank', 'explicacao']
    can_delete = False
    
@admin.register(Tentativa_de_resposta)
class QuizTentativaAdmin(admin.ModelAdmin):
    list_display = ['id', 'respondido_por', 'user', 'criado_em']
    readonly_fields = ['criado_em']
    inlines = [RespostaInline, RecomendacaoInline]
    
