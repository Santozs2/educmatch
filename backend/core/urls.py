from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("painel/", include("painel.urls")),
    path("", include("accounts.urls")),
    path("", include("quiz.web_urls")),
    path("cursos/", include("catalogo.urls")),
]