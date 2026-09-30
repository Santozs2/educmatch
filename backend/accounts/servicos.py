from accounts.models import Interesse


def registrar_interesse(usuario, curso, tentativa=None):
    """Um lugar só grava interesse, para o snapshot do C4 sair sempre igual.

    Idempotente: devolve (interesse, criado). Se o interesse já existe,
    não mexe no snapshot: ele é a foto do momento em que foi salvo.
    Se o aluno tinha removido o curso e salva de novo, o MESMO registro
    volta para "interessado" com a foto ORIGINAL — é a do primeiro
    salvamento que aderencia_a_recomendacao() mede.
    """
    rec = tentativa.recomendacoes.filter(curso=curso).first() if tentativa else None
    interesse, criado = Interesse.objects.get_or_create(
        usuario=usuario,
        curso=curso,
        defaults={
            "tentativa_origem": tentativa,
            "rank_snapshot": rec.rank_final if rec else None,
            "rank_engine_snapshot": rec.rank_engine if rec else None,
            "afinidade_snapshot": rec.score if rec else None,
            "era_principal": bool(rec and rec.rank_final == 1),
        },
    )
    if not criado and interesse.status == "removido":
        interesse.status = "interessado"
        interesse.save(update_fields=["status"])
    return interesse, criado


def remover_da_lista(interesse):
    """O aluno tirou o curso da lista. Soft delete: a linha e a foto ficam."""
    interesse.status = "removido"
    interesse.save(update_fields=["status"])