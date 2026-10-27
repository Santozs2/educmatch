from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0005_inicio_de_quiz_e_iniciado_em'),
    ]

    operations = [
        migrations.AddField(
            model_name='tentativa_de_resposta',
            name='reordered_alternatives',
            field=models.BooleanField(default=False),
        ),
    ]
