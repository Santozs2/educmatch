from django.db import migrations, models


def copia_rank_engine_para_rank_final(apps, schema_editor):
    # Antes da LLM, a ordem entregue ERA a da engine.
    Recomendacao = apps.get_model("quiz", "Recomendacao")
    Recomendacao.objects.update(rank_final=models.F("rank_engine"))


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0003_recomendacao_idx_rec_rank_curso_and_more"),
    ]

    operations = [
        # O índice antigo aponta para "rank": sai antes do rename.
        migrations.RemoveIndex(model_name="recomendacao", name="idx_rec_rank_curso"),
        migrations.RenameField(model_name="recomendacao", old_name="rank", new_name="rank_engine"),
        migrations.AlterField(
            model_name="recomendacao",
            name="rank_engine",
            field=models.PositiveSmallIntegerField(
                default=0, help_text="Ordem determinística calculada pela engine."
            ),
        ),
        migrations.AddField(
            model_name="recomendacao",
            name="rank_final",
            field=models.PositiveSmallIntegerField(
                default=0, help_text="Ordem entregue ao aluno (a LLM pode reordenar)."
            ),
        ),
        migrations.RunPython(copia_rank_engine_para_rank_final, migrations.RunPython.noop),
        migrations.AddField(
            model_name="recomendacao",
            name="llm_text",
            field=models.TextField(blank=True),
        ),
        migrations.AlterModelOptions(
            name="recomendacao",
            options={"ordering": ["rank_final"]},
        ),
        migrations.AddIndex(
            model_name="recomendacao",
            index=models.Index(fields=["rank_final", "curso"], name="idx_rec_rank_final_curso"),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="llm_model",
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="prompt_version",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="latency_ms",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="tokens_in",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="tokens_out",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="used_fallback",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="diverged",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="cache_hit",
            field=models.BooleanField(default=False),
        ),
    ]