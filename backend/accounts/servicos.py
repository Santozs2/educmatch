from accounts.models import Interesse


def registrar_interesse(usuario, curso, tentativa=None):
    """Um lugar só grava interesse, para o snapshot do C4 sair sempre igual.

    Idempotente: devolve (interesse, criado). Se o interesse já existe,
    não mexe no snapshot: ele é a foto do momento em que foi salvo.
    """
    rec = tentativa.recomendacoes.filter(curso=curso).first() if tentativa else None
    return Interesse.objects.get_or_create(
        usuario=usuario,
        curso=curso,
        defaults={
            "tentativa_origem": tentativa,
            "rank_snapshot": rec.rank if rec else None,
            "afinidade_snapshot": rec.score if rec else None,
            "era_principal": bool(rec and rec.rank == 1),
        },
    )