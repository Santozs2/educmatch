import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_initial"),
        ("quiz", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuestionarioLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("ativo", models.BooleanField(default=True)),
                ("criado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="links_de_questionario", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-criado_em"]},
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="questionario_link",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tentativas", to="quiz.questionariolink"),
        ),
    ]