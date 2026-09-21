from django.urls import path
from painel.views import dashboard


urlpatterns = [
    path("", dashboard, name="painel-dashboard"),
]
