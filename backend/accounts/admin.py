from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import Interesse, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # O login é pelo e-mail: o username herdado fica vazio e sai das telas.
    ordering = ["email"]
    list_display = ["email", "first_name", "is_staff", "is_superuser", "date_joined"]
    search_fields = ["email", "first_name"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Dados pessoais", {"fields": ["first_name", "last_name"]}),
        ("Permissões", {"fields": ["is_active", "is_staff", "is_superuser", "groups", "user_permissions"]}),
        ("Datas", {"fields": ["last_login", "date_joined"]}),
    ]
    add_fieldsets = [
        (None, {"classes": ["wide"], "fields": ["email", "first_name", "password1", "password2"]}),
    ]


@admin.register(Interesse)
class InteresseAdmin(admin.ModelAdmin):
    list_display = ["usuario", "curso", "status", "rank_snapshot", "era_principal", "criado_em"]
    list_filter = ["status", "era_principal"]
    search_fields = ["usuario__email", "curso__nome_curso"]
    # O snapshot é a foto do momento: ninguém edita pelo admin.
    readonly_fields = ["tentativa_origem", "rank_snapshot", "rank_engine_snapshot", "afinidade_snapshot", "era_principal", "criado_em"]