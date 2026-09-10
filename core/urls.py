from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("quiz/", include("quiz.urls")),
    path("", include("accounts.urls")),
    path("", include("quiz.web_urls")),
]