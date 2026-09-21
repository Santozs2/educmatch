from django.contrib import admin
from .models import Area, Curso, Peso_curso

class Peso_curso(admin.TabularInline):
    model = Peso_curso
    extra = 7
    
@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug']
    search_fields = ['nome']
    prepopulated_fields = {'slug': ('nome',)}
    
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ['nome_curso', 'area_principal', 'duracao', 'is_active']
    list_filter = ['area_principal', 'is_active']
    search_fields = ['nome_curso', 'descricao']
    inlines = [Peso_curso]
    
    
