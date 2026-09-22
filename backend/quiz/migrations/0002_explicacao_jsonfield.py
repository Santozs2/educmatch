import ast
import json

from django.db import migrations, models


def texto_para_json(apps, schema_editor):
    """O TextField guardava str(dict): aspas simples, None, True.
    Isso não é JSON, e o MySQL recusa o ALTER para coluna JSON se uma
    linha só tiver valor inválido. Então converte ANTES de alterar."""
    Recomendacao = apps.get_model("quiz", "Recomendacao")
    for rec in Recomendacao.objects.all().only("id", "explicacao"):
        bruto = rec.explicacao
        if not bruto:
            valor = {}
        else:
            try:
                valor = ast.literal_eval(bruto)
            except (ValueError, SyntaxError):
                try:
                    valor = json.loads(bruto)
                except ValueError:
                    valor = {}
        rec.explicacao = json.dumps(valor, ensure_ascii=False)
        rec.save(update_fields=["explicacao"])


class Migration(migrations.Migration):
    dependencies = [("quiz", "0001_initial")]

    operations = [
        migrations.RunPython(texto_para_json, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="recomendacao",
            name="explicacao",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]