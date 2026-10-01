from django.urls import path

from . import views

urlpatterns = [
    path("<uuid:token>/", views.responder, name="avaliacao-responder"),
    path("<uuid:token>/obrigado/", views.obrigado, name="avaliacao-obrigado"),
]