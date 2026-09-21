---
title: "Passo a passo — BK-01 a BK-08 (API v1 para a SPA)"
aliases: ["Passo a passo BK", "Fase 0 do front", "Consertar a API", "API v1 EducMatch"]
tags: [tcc, api, drf, django, execucao, passo-a-passo, contrato]
status: proposto
projeto: TCC
criado: 2026-09-21
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front React + Vite]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|🗂️ Plano de execução]] · Contratos: [[Projetos/EducMatch(Secretária)/contratos-c1-a-c6|📜 C1–C6]] · Vem antes de: [[Projetos/EducMatch(Secretária)/passo-a-passo-fe-06-fe-10|🎯 FE-06 a FE-10]] · Irmã: [[Projetos/EducMatch(Secretária)/passo-a-passo-fe-01-fe-05|⚛️ FE-01 a FE-05]]

# 🔧 Passo a passo — BK-01 a BK-08

> [!abstract] O que esta nota é
> O **como** da Fase 0 do [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|plano]]: sair com `/api/v1/` respondendo exatamente o contrato da [[Projetos/EducMatch(Secretária)/spec-front-react-vite|spec §3]], provado por teste. Arquivo por arquivo, na ordem em que o código depende de si mesmo.
> Escrito contra o repositório em `~/Documents/vscode/educmatch/backend` (então `EducMatch/`), lido em 2026-09-21 (último commit do backend `3a6773e`).

> [!success] O que já foi verificado (2026-09-21)
> O código desta nota foi aplicado numa **cópia** do repositório, com SQLite no lugar do MySQL e **Django 6.1.1 + DRF 3.18.1** (as versões do `requirements.txt`):
> - `manage.py check` sem erros; `makemigrations` gera o `RenameField` (não drop + add) e depois `--check` fica limpo;
> - a migração `0002_explicacao_jsonfield` converteu uma linha no formato antigo (`str(dict)`, aspas simples) e uma linha vazia;
> - os **20 testes** da seção 8 passam;
> - todas as funções de `painel/metricas.py` rodam com banco semeado e 8 tentativas, e `/painel/metricas/` e `/painel/links/` respondem.
>
> **Não** verificado: o `ALTER` da coluna JSON no **MySQL**, e o CSRF pelo navegador (isso é a verificação da FE-11). A seção 9 continua obrigatória.

## 🧭 Estado das decisões

| | Decisão | Estado |
|---|---|---|
| **D-rank** | `rank_snapshot` / `era_principal` em `Interesse`: criar ou remover a métrica de aderência? | ✅ **criar** — já estava decidido e ninguém tinha notado: `quiz/tests/test_contratos.py::test_c4_interesse_tem_os_tres_campos_de_snapshot` exige `afinidade_snapshot`, `rank_snapshot`, `era_principal` **e** que a FK se chame `tentativa_origem`. O contrato C4 venceu a pergunta do plano |
| **D-nome** | `Usuario.username` ou `Usuario.nome`? | ✅ **`nome`** (= `first_name`). O `CadastroForm` grava `first_name`; `User.username` é herdado, sem `unique`, e fica vazio em todo usuário real |
| **D-cors** | `django-cors-headers` (o plano pedia na BK-08) | ✅ **não instalar**. Com o proxy do Vite (FE-01) o navegador vê mesma origem em dev; em produção é mesmo domínio (FE-23). CORS nunca acontece — mas `CSRF_TRUSTED_ORIGINS` **é** necessário, ver BK-08 |
| **D-401** | Anônimo em rota protegida: 401 ou 403? | ✅ **401**. O DRF devolve 403 por padrão com `SessionAuthentication`; uma classe de 3 linhas conserta (BK-07) |

> [!danger] Cinco achados que o plano não tinha
> 0. **A supressão k-anônima da conversão se desfaz com uma conta.** A `taxa` continuava na linha suprimida. Corrigido na BK-06.
> 1. **A API anônima nunca abriria o próprio resultado.** A regra C6 de `resultado_pagina` exige o `pk` em `session["minhas_tentativas"]` — e o `EnvioQuiz` não grava nada na sessão. Sem isso, `GET /tentativas/<pk>/` devolve 404 para todo visitante. Corrigido na BK-02.
> 2. **Remontar `quiz.urls` em `/api/v1/` leva o dashboard junto.** `quiz/urls.py` mistura API (`questoes/`, `envio/`) e páginas (`dashboard/`, `dashboard/gerar-link/`). As duas páginas mudam para `web_urls.py` na BK-06, ou o plano B da banca some.
> 3. **Nenhuma BK criava `/painel/metricas/` nem `/painel/links/`.** A spec §3 lista os dois; o plano não tinha tarefa. Entram na BK-06.
> 4. **A suíte de testes não roda verde hoje**, e não por causa desta fase: `test_api.py` chama `/api/quiz/enviar/` (a rota é `/quiz/envio/`) e `self.payload_valido()` (não existe em `base.py`); `test_c6_claim.py` usa `reverse("criar-conta")` (o nome é `cadastro_usuario`) e três helpers que não existem. Registre a linha de base **antes** de começar (seção 0).

---

## 0️⃣ Antes de abrir o editor

```bash
cd "$HOME/Documents/vscode/educmatch/backend"
source .venv/Scripts/activate
python -c "import django, rest_framework; print(django.__version__, rest_framework.__version__)"
```

> [!danger] O venv está com o Django errado — resolva isto primeiro
> Em 2026-09-21 o `.venv` tinha **Django 4.2.30**, enquanto o `requirements.txt` fixa **6.1.1**. Duas quebras concretas, as duas reproduzidas:
> 1. **DRF 3.18.1 exige Django ≥ 5.0**: qualquer `ModelSerializer` sobre `Interesse` estoura com `AttributeError: 'UniqueConstraint' object has no attribute 'nulls_distinct'` (o `nulls_distinct` nasceu no Django 5.0). É o `POST /interesses/` da BK-07.
> 2. **Django 4.2 não suporta Python 3.14** (o Python do venv): o test client quebra ao renderizar qualquer template com `AttributeError: 'super' object has no attribute 'dicts'` — inclusive a página de erro. É por isso que parte da suíte "já estava quebrada".
>
> ```bash
> pip install -r requirements.txt     # sobe para Django 6.1.1
> python manage.py migrate            # confira que nada estranho aparece
> ```

```bash
python manage.py test 2>&1 | tail -5     # agora sim: anote N testes, X falhas, Y erros
```

> [!important] A linha de base é o que separa "quebrei" de "já estava quebrado"
> Guarde o número. Ao fim da fase, os testes novos desta nota passam e **nenhuma falha nova** aparece. Consertar os testes antigos do C6 (nomes de rota e helpers) é da FE-24, quando os templates saírem — não misture.

> [!note] `quiz/tests.py` **e** `quiz/tests/` convivendo
> Com o pacote `quiz/tests/` presente, o Python importa o pacote e o arquivo `quiz/tests.py` **nunca roda** — em silêncio. Mova o conteúdo dele para `quiz/tests/test_resultado.py` e apague o arquivo. Mesmo caso em `accounts/` e `painel/` (lá os `tests.py` são só o esqueleto de 63 bytes: apague).

> [!warning] `painel/tests/` não tem `__init__.py` — os 10 testes do painel nunca rodaram
> Sem o arquivo, a pasta não é pacote e o `manage.py test` a ignora sem avisar. Crie `painel/tests/__init__.py` vazio. Ao fazer isso, **7 erros aparecem**, todos pré-existentes: os testes chamam helpers que nunca foram escritos (`criar_curso_com`, `criar_curso`, `criar_tentativa_com_explicacao`, `criar_tentativas`), e os 4 de `AcessoAoPainelTest` testam um dashboard HTML que a BK-06 transforma em API. Não bloqueia esta fase: registre na linha de base, e a regra que eles queriam provar (supressão, acesso, conversão sem produto cartesiano) passa a ser provada pelos testes de API da seção 8.

---

## 1️⃣ BK-01 — os serializers

### `catalogo/serializers.py` — arquivo novo

```python
from rest_framework import serializers

from catalogo.models import Area, Curso


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ("slug", "nome")


class CursoSerializer(serializers.ModelSerializer):
    area_principal = AreaSerializer(read_only=True)

    class Meta:
        model = Curso
        fields = ("id", "nome_curso", "descricao", "duracao", "area_principal")
```

### `quiz/serializers.py` — substitua o arquivo

```python
from rest_framework import serializers

from catalogo.serializers import CursoSerializer
from quiz.models import Alternativa, Questao, QuestionarioLink, Recomendacao, Tentativa_de_resposta


class AlternativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternativa
        # Nunca "__all__": com ele, um related futuro vazaria os pesos.
        fields = ("id", "texto", "order")


class QuestaoSerializer(serializers.ModelSerializer):
    alternativas = AlternativaSerializer(many=True, read_only=True)

    class Meta:
        model = Questao
        fields = ("id", "texto", "order", "alternativas")


class RecomendacaoSerializer(serializers.ModelSerializer):
    curso = CursoSerializer(read_only=True)
    match = serializers.SerializerMethodField()
    explicacao = serializers.SerializerMethodField()

    class Meta:
        model = Recomendacao
        fields = ("rank", "score", "match", "curso", "explicacao")

    def get_match(self, rec):
        return round(rec.score * 100)

    def get_explicacao(self, rec):
        dado = rec.explicacao if isinstance(rec.explicacao, dict) else {}
        return {"top_areas": dado.get("top_areas", [])}


class TentativaSerializer(serializers.ModelSerializer):
    tentativa_id = serializers.IntegerField(source="id", read_only=True)
    recomendacoes = RecomendacaoSerializer(many=True, read_only=True)

    class Meta:
        model = Tentativa_de_resposta
        fields = (
            "tentativa_id", "respondido_por", "criado_em",
            "confidence_band", "diferenca", "recomendacoes",
        )


class RespostaSerializer(serializers.Serializer):
    questao = serializers.PrimaryKeyRelatedField(queryset=Questao.objects.filter(is_active=True))
    alternativa = serializers.PrimaryKeyRelatedField(queryset=Alternativa.objects.all())

    def validate(self, dados):
        if dados["alternativa"].questao_id != dados["questao"].id:
            raise serializers.ValidationError(
                {"alternativa": "Esta alternativa não pertence à questão informada."}
            )
        return dados


class EnvioSerializer(serializers.Serializer):
    respondido_por = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    questionario_link = serializers.UUIDField(required=False, allow_null=True, default=None)
    respostas = RespostaSerializer(many=True, allow_empty=False)

    def validate_respostas(self, respostas):
        ids = [r["questao"].id for r in respostas]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Cada questão só pode ser respondida uma vez.")

        ativas = set(Questao.objects.filter(is_active=True).values_list("id", flat=True))
        faltando = ativas - set(ids)
        if faltando:
            raise serializers.ValidationError(f"Faltam respostas para {len(faltando)} questão(ões).")
        return respostas

    def validate_questionario_link(self, token):
        if token is None:
            return None
        link = QuestionarioLink.objects.filter(token=token, ativo=True).first()
        if link is None:
            raise serializers.ValidationError("Este link de questionário não existe ou foi encerrado.")
        return link  # validated_data já sai com o objeto, não com o UUID
```

> [!important] Os três nomes que o DRF exige ao pé da letra
> | Estava | O DRF chama | Por quê |
> |---|---|---|
> | `RespostaSerializer.validar` | `validate` | Só `validate` e `validate_<campo>` são ganchos; qualquer outro nome é método morto |
> | `EnvioSerializer.validate_resposta` | `validate_respostas` | O sufixo é o nome **exato** do campo — `respostas`, no plural |
> | campo `choice` | `alternativa` | É o nome que a `EnvioQuiz` lê (`item["alternativa"]`) e o que a spec congela |
>
> A mesma classe de bug de [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 lições]]: validação escrita, nunca executada, e nenhum erro dizendo isso.

> [!note] `area_name` e `area_nome` saem os dois
> A engine grava as duas chaves em `top_areas` (`quiz/engine.py::explicacao`). O front lê `area_name`, que é o contrato. Não apague `area_nome` da engine agora: os templates usam o normalizador de `web_views` e as tentativas antigas no banco já têm as duas.

---

## 2️⃣ BK-02 e BK-03 — as views do quiz

### `quiz/views.py` — substitua **só a parte de cima** (até `ResultadoQuestao`, inclusive)

`superuser_required`, `gerar_questionario_link` e `dashboard_view` ficam onde estão — são páginas, e a BK-06 só troca a rota delas.

```python
from django.db import transaction
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from quiz.engine import recomedacao
from quiz.models import Questao, QuestionarioLink, Resposta, Tentativa_de_resposta
from quiz.serializers import EnvioSerializer, QuestaoSerializer, TentativaSerializer

# ... (imports das páginas: wraps, settings, redirect_to_login, etc. — mantenha)


def tentativas_visiveis(request):
    """C6 em uma linha de SQL: a tentativa com dono só abre para o dono;
    a anônima só abre se estiver na sessão deste navegador.
    A mesma regra de web_views.resultado_pagina — agora reutilizável."""
    filtro = Q(user__isnull=True, pk__in=request.session.get("minhas_tentativas", []))
    if request.user.is_authenticated:
        filtro |= Q(user=request.user)
    return Tentativa_de_resposta.objects.filter(filtro)


class QuestaoList(generics.ListAPIView):
    serializer_class = QuestaoSerializer
    queryset = Questao.objects.filter(is_active=True).prefetch_related("alternativas")


class EnvioQuiz(APIView):
    def post(self, request):
        entrada = EnvioSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data

        usuario = request.user if request.user.is_authenticated else None
        respondido_por = dados["respondido_por"].strip() or (usuario.first_name if usuario else "")

        with transaction.atomic():
            tentativa = Tentativa_de_resposta.objects.create(
                user=usuario,
                respondido_por=respondido_por,
                questionario_link=dados["questionario_link"],
            )
            Resposta.objects.bulk_create(
                [
                    Resposta(tentativa=tentativa, questao=item["questao"], alternativa=item["alternativa"])
                    for item in dados["respostas"]
                ]
            )
            recomedacao(tentativa)

        # Sem isto o GET /tentativas/<pk>/ dá 404 para o próprio visitante,
        # e o claim do C6 no login não tem o que adotar.
        minhas = request.session.setdefault("minhas_tentativas", [])
        minhas.append(tentativa.pk)
        request.session.modified = True

        tentativa.refresh_from_db()  # confidence_band e diferenca vêm da engine
        return Response(TentativaSerializer(tentativa).data, status=status.HTTP_201_CREATED)


class TentativaDetalhe(generics.RetrieveAPIView):
    serializer_class = TentativaSerializer

    def get_queryset(self):
        return tentativas_visiveis(self.request).prefetch_related(
            "recomendacoes__curso__area_principal"
        )


class QuestionarioStatus(APIView):
    def get(self, request, token):
        link = QuestionarioLink.objects.filter(token=token, ativo=True).first()
        if link is None:
            return Response({"detail": "Link inválido ou encerrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"ativo": True})
```

Apague a classe `ResultadoQuestao` inteira — ela era `RetrieveAPIView` sobre `Questao`, com o método `recuerar` que o DRF nunca chama.

> [!important] Por que `tentativas_visiveis` devolve **404**, não 403
> 403 diria "existe, mas não é sua" — e aí basta iterar `pk` para descobrir quantas tentativas o sistema tem. 404 é indistinguível de "não existe". É a mesma escolha de `resultado_pagina` (`raise Http404`).

> [!note] CSRF no POST do quiz
> O `APIView` é `csrf_exempt` e a `SessionAuthentication` só exige o token **de quem está logado**. Visitante anônimo posta sem `X-CSRFToken`; logado, precisa — e o `api.ts` da FE-03 já manda.

---

## 3️⃣ BK-04 — `explicacao` vira `JSONField`

### `quiz/models.py`

```python
class Recomendacao(models.Model):
    # ...
    explicacao = models.JSONField(default=dict, blank=True)
    # ...

    def __str__(self):
        # "curso.nome" não existe — era um AttributeError esperando o admin abrir
        return f"Recomendação do curso {self.curso.nome_curso} para a tentativa {self.tentativa_id} - Score: {self.score}, Rank: {self.rank}"
```

### A migração — escrita à mão, em duas etapas

```bash
python manage.py makemigrations quiz --empty -n explicacao_jsonfield
```

Substitua o conteúdo do arquivo gerado (`quiz/migrations/0002_explicacao_jsonfield.py`):

```python
import ast
import json

from django.db import migrations, models


def repr_para_json(apps, schema_editor):
    """O TextField guardava str(dict): aspas simples, None, True.
    Isso não é JSON — e o MySQL recusa o ALTER para coluna JSON se
    uma linha só tiver valor inválido. Converte antes de alterar."""
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
        migrations.RunPython(repr_para_json, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="recomendacao",
            name="explicacao",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
```

> [!danger] A ordem das duas operações é o que faz a migração passar
> `AlterField` primeiro = `Invalid JSON text` no MySQL na primeira linha antiga. `RunPython` primeiro = cada linha vira JSON válido ainda dentro do `TextField`, e o `ALTER` só muda o tipo.

### `quiz/web_views.py` — o `ast` sai

```python
def areas_da_recomendacao(recomendacao):
    explicacao = recomendacao.explicacao
    if not isinstance(explicacao, dict):
        return []
    # ... o resto da função igual, a partir de `areas = explicacao.get(...)`
```

E apague o `import ast` do topo.

---

## 4️⃣ BK-05 — o C4 completo em `Interesse` e o `metricas.py` que roda

### `accounts/models.py` — só a classe `Interesse`

```python
class Interesse(models.Model):
    STATUS = [
        ("interessado", "Interessado"),
        ("contatado", "Contatado"),
        ("descartado", "Descartado"),
    ]
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interesses")
    curso = models.ForeignKey("catalogo.Curso", on_delete=models.PROTECT, related_name="interessados")
    tentativa_origem = models.ForeignKey(
        "quiz.Tentativa_de_resposta", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="interesses",
    )
    # C4 — foto do momento da manifestação. A tentativa pode ser refeita,
    # a recomendação regravada; o snapshot não muda.
    rank_snapshot = models.PositiveSmallIntegerField(null=True, blank=True)
    afinidade_snapshot = models.FloatField(null=True, blank=True)
    era_principal = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS, default="interessado")
    nota = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)  # era auto_now: reescrevia a cada save
    # Meta e __str__ iguais
```

```bash
python manage.py makemigrations accounts -n interesse_c4
```

> [!warning] O `makemigrations` vai perguntar se `envio_recurso` foi renomeado
> Responda **`y`**. Se responder `n`, ele apaga a coluna e cria outra — e todo interesse existente perde a tentativa de origem. Confira no arquivo gerado que a operação é `RenameField`, não `RemoveField` + `AddField`.
> Na troca de `auto_now` para `auto_now_add` ele pode pedir um default para linhas antigas: não pede, porque a coluna já tem valor. Se pedir, algo mais mudou — pare.

### `accounts/servicos.py` — arquivo novo

Um lugar só grava interesse, para as páginas e a API preencherem o snapshot do mesmo jeito:

```python
from accounts.models import Interesse


def registrar_interesse(usuario, curso, tentativa=None):
    """Idempotente: devolve (interesse, criado). Se já existe, não mexe no snapshot."""
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
```

### `accounts/views.py` — as duas chamadas passam a usar o serviço

Em `_salvar_interesse_pendente`, troque o `Interesse.objects.get_or_create(...)` por:

```python
    registrar_interesse(request.user, curso, tentativa)
```

Em `salvar_interesse`, troque o bloco da `tentativa` + `get_or_create` (o `rec` calculado ali nunca era usado — era o snapshot pela metade) por:

```python
    tentativa = None
    if tentativa_id:
        tentativa = Tentativa_de_resposta.objects.filter(pk=tentativa_id).first()

    item, criado = registrar_interesse(request.user, curso, tentativa)
    if not criado:
        item.delete()
```

E `from accounts.servicos import registrar_interesse` no topo.

### `painel/metricas.py` — seis consertos

| Função | Estava | Fica |
|---|---|---|
| `conversao_por_curso` | `annotate(interessados=Count("interessados"))` → **`ValueError: The annotation 'interessados' conflicts with a field on the model`**: `interessados` é o `related_name` de `Interesse.curso`. A função nunca rodou | Anota como `n_interessados` e devolve a chave `interessados` no dict — o teste e o front continuam lendo o mesmo nome |
| `top_cursos_com_manifestacoes` | Contava **recomendação rank 1** — cópia exata de `top_cursos_em_primeiro` com outro nome | Conta `Interesse` (é o que "manifestação" significa no C4) |
| `demanda_por_area` | `contagem.update(explicacao.keys())` → contava a string `"top_areas"` | A área dominante: `top_areas[0]["area"]` |
| `distribuicao_de_confianca` | `confidence_level` | `confidence_band` |
| `cobertura_de_areas` | `Count("pesos_alternativa")` | `Count("pesos__alternativa")` — o `related_name` de `Peso_alternativa.area` é `pesos` |
| todas as `values("curso_id", "curso__nome_curso")` | chave `curso__nome_curso` no JSON | `nome=F("curso__nome_curso")` — o front lê `nome` |

```python
from django.db.models import Count, F, Q

def top_cursos_com_manifestacoes(inicio, limite=3):
    """Top N cursos com mais manifestações de interesse no período."""
    return list(
        Interesse.objects
        .filter(_no_periodo(inicio))
        .values("curso_id", nome=F("curso__nome_curso"))
        .annotate(total=Count("id"))
        .order_by("-total", "nome")[:limite]
    )


def top_cursos_em_primeiro(inicio, limite=10):
    return list(
        Recomendacao.objects
        .filter(rank=1)
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values("curso_id", nome=F("curso__nome_curso"))
        .annotate(total=Count("tentativa_id", distinct=True))
        .order_by("-total", "nome")[:limite]
    )


def top_cursos_no_top5(inicio, limite=10):
    return list(
        Recomendacao.objects
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values("curso_id", nome=F("curso__nome_curso"))
        .annotate(total=Count("tentativa_id", distinct=True))
        .order_by("-total", "nome")[:limite]
    )


def conversao_por_curso(inicio):
    linhas = (
        Curso.objects
        .filter(is_active=True)
        .annotate(
            recomendado=Count(
                "recomendacoes",
                filter=_no_periodo(inicio, "recomendacoes__tentativa__criado_em"),
                distinct=True,
            ),
            # "interessados" é o related_name de Interesse.curso: anotar com esse
            # nome é ValueError. O nome curto volta no dict, logo abaixo.
            n_interessados=Count(
                "interessados",
                filter=_no_periodo(inicio, "interessados__criado_em"),
                distinct=True,
            ),
        )
        .values("id", "nome_curso", "recomendado", "n_interessados")
        .order_by("-n_interessados", "nome_curso")
    )

    resultado = []
    for linha in linhas:
        linha["interessados"] = linha.pop("n_interessados")
        recomendado = linha["recomendado"]
        linha["taxa"] = (linha["interessados"] / recomendado * 100) if recomendado else None
        resultado.append(linha)
    return resultado


def demanda_por_area(inicio, limite=12):
    explicacoes = (
        Recomendacao.objects
        .filter(rank=1)
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values_list("explicacao", flat=True)
    )

    contagem = Counter()
    for explicacao in explicacoes:
        areas = (explicacao or {}).get("top_areas") or []
        if areas and isinstance(areas[0], dict) and areas[0].get("area"):
            contagem[areas[0]["area"]] += 1

    nomes = dict(Area.objects.values_list("slug", "nome"))
    return [
        {"area": slug, "nome": nomes.get(slug, slug), "total": total}
        for slug, total in contagem.most_common(limite)
    ]


def distribuicao_de_confianca(inicio):
    return list(
        Tentativa_de_resposta.objects
        .filter(_no_periodo(inicio))
        .values("confidence_band")
        .annotate(total=Count("id"))
        .order_by("confidence_band")
    )


def cobertura_de_areas():
    return list(
        Area.objects
        .annotate(alternativas=Count("pesos__alternativa", distinct=True))
        .values("slug", "nome", "alternativas")
        .order_by("alternativas", "nome")
    )
```

Remova `Peso_alternativa` do import (não é mais usado).

> [!warning] `painel/tests/test_metricas.py::test_demanda_por_area_le_o_jsonfield` precisa mudar junto
> Ele monta `explicacao={"eletrica": 0.6, "ti": 0.2}` — o formato antigo que a engine **nunca** gravou. Troque por `{"top_areas": [{"area": "eletrica", "area_name": "Elétrica", "contribuicao": 3.0, "percentual": 75.0}]}` e afirme `demanda[0]["area"] == "eletrica"`. O teste passava pelo motivo errado.

---

## 5️⃣ BK-06 — `/api/v1/` montado, e o painel ganha API

### `core/api_urls.py` — arquivo novo

```python
from django.urls import include, path

from quiz.views import QuestionarioStatus

urlpatterns = [
    path("quiz/", include("quiz.urls")),
    path("catalogo/", include("catalogo.urls")),
    path("painel/", include("painel.urls")),
    path("questionario/<uuid:token>/", QuestionarioStatus.as_view(), name="api-questionario"),
    path("", include("accounts.api_urls")),  # auth/, interesses/, tentativas/
]
```

### `core/urls.py` — substitua

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.api_urls")),
    # Templates — o plano B até a FE-24
    path("", include("accounts.urls")),
    path("", include("quiz.web_urls")),
]
```

### `quiz/urls.py` — só API

```python
from django.urls import path

from quiz import views

urlpatterns = [
    path("questoes/", views.QuestaoList.as_view(), name="api-questoes"),
    path("tentativas/", views.EnvioQuiz.as_view(), name="api-tentativa-criar"),
    path("tentativas/<int:pk>/", views.TentativaDetalhe.as_view(), name="api-tentativa"),
]
```

### `quiz/web_urls.py` — recebe o dashboard, **na mesma URL de antes**

```python
from django.urls import path

from quiz.views import dashboard_view, gerar_questionario_link
from quiz.web_views import acessar_questionario, pagina_quiz, resultado_pagina

urlpatterns = [
    path("", pagina_quiz, name="quiz-inicio"),
    path("questionario/<uuid:token>/", acessar_questionario, name="questionario-link"),
    path("resultado/<int:pk>/", resultado_pagina, name="quiz-resultado"),
    # Continuam em /quiz/dashboard/ para nenhum link ou favorito quebrar
    path("quiz/dashboard/", dashboard_view, name="dashboard"),
    path("quiz/dashboard/gerar-link/", gerar_questionario_link, name="gerar-questionario-link"),
]
```

### `catalogo/urls.py` e `catalogo/views.py` — arquivos novos / substituído

```python
# catalogo/views.py
from rest_framework import generics

from catalogo.models import Curso
from catalogo.serializers import CursoSerializer


class CursoDetalhe(generics.RetrieveAPIView):
    serializer_class = CursoSerializer
    queryset = Curso.objects.filter(is_active=True).select_related("area_principal")
```

```python
# catalogo/urls.py
from django.urls import path

from catalogo.views import CursoDetalhe

urlpatterns = [
    path("cursos/<int:pk>/", CursoDetalhe.as_view(), name="api-curso"),
]
```

### `painel/views.py` — substitua (o `render` de `painel/dashboard.html` apontava para um template que **não existe**)

```python
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from painel import metricas, privacidade
from quiz.models import QuestionarioLink


class EhSuperusuario(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class Metricas(APIView):
    permission_classes = [EhSuperusuario]

    def get(self, request):
        escolhido = request.query_params.get("periodo", "90")
        if escolhido not in metricas.PERIODOS:
            return Response({"detail": "periodo deve ser 30, 90 ou 365."}, status=status.HTTP_400_BAD_REQUEST)

        inicio = metricas.inicio_do_periodo(metricas.PERIODOS[escolhido])
        total = metricas.total_de_tentativas(inicio)
        tem_massa = privacidade.periodo_tem_massa_suficiente(total)

        corpo = {
            "periodo": int(escolhido),
            "total_de_tentativas": total,
            "tem_massa": tem_massa,
            "k_minimo": privacidade.K_MINIMO,
        }
        if not tem_massa:
            return Response(corpo)  # nenhum número individual sai do servidor

        sup = privacidade.suprimir_pequenos

        conversao = sup(metricas.conversao_por_curso(inicio), campo="interessados")
        for linha in conversao:
            if linha.get("suprimido"):
                # taxa × recomendado reconstruiria o "interessados" que acabou de ser escondido
                linha["taxa"] = None

        aderencia = metricas.aderencia_a_recomendacao(inicio)
        aderencia["por_posicao"] = sup(aderencia["por_posicao"])

        corpo.update({
            "cursos_ativos": metricas.cursos_ativos(),
            "top_primeiro": sup(metricas.top_cursos_em_primeiro(inicio)),
            "top_manifestacoes": sup(metricas.top_cursos_com_manifestacoes(inicio)),
            "top_cinco": sup(metricas.top_cursos_no_top5(inicio)),
            "conversao": conversao,
            "aderencia": aderencia,
            "via_link": metricas.tentativas_via_link(inicio),
            "demanda_por_area": sup(metricas.demanda_por_area(inicio)),
            "confianca": sup(metricas.distribuicao_de_confianca(inicio)),
            "orfaos": metricas.cursos_nunca_recomendados(),
            "cobertura": metricas.cobertura_de_areas(),
        })
        return Response(corpo)


def _dados_do_link(link):
    return {
        "token": str(link.token),
        "url": f"{settings.FRONTEND_URL}/questionario/{link.token}",
        "criado_em": link.criado_em,
    }


class Links(APIView):
    permission_classes = [EhSuperusuario]

    def get(self, request):
        links = QuestionarioLink.objects.filter(ativo=True)[:5]
        return Response([_dados_do_link(link) for link in links])

    def post(self, request):
        link = QuestionarioLink.objects.create(criado_por=request.user)
        return Response(_dados_do_link(link), status=status.HTTP_201_CREATED)
```

```python
# painel/urls.py — substitua
from django.urls import path

from painel.views import Links, Metricas

urlpatterns = [
    path("metricas/", Metricas.as_view(), name="api-painel-metricas"),
    path("links/", Links.as_view(), name="api-painel-links"),
]
```

> [!important] `confianca` também passa por `suprimir_pequenos`
> Na view antiga ela saía crua. "1 tentativa de confiança baixa" num período de 6 é exatamente o número individual que o k-anonimato existe para esconder.

> [!danger] A supressão da conversão vazava pela `taxa`
> `conversao_por_curso` calcula `taxa = interessados / recomendado × 100` **antes** da supressão. Na view antiga, `interessados` virava `None` mas `taxa` e `recomendado` continuavam na linha — e `taxa × recomendado / 100` devolve o número escondido. Supressão que se desfaz com uma multiplicação não é supressão. O `for` acima zera a `taxa` das linhas suprimidas. Mesma lógica para `aderencia.por_posicao`, que saía sem supressão nenhuma.

Acrescente em `painel/metricas.py`:

```python
def tentativas_via_link(inicio):
    """Quantas tentativas do período vieram de um QuestionarioLink (FE-17)."""
    return Tentativa_de_resposta.objects.filter(_no_periodo(inicio), questionario_link__isnull=False).count()
```

> [!note] Por que `FRONTEND_URL` e não `request.build_absolute_uri`
> Através do proxy do Vite, o `Host` que chega ao Django é `localhost:8000` (`changeOrigin: true`). O link gerado apontaria para a página de template, não para a SPA. A variável resolve dev e produção com a mesma linha (BK-08).

---

## 6️⃣ BK-07 — conta, interesse e histórico por API

### `accounts/autenticacao.py` — arquivo novo

```python
from rest_framework.authentication import SessionAuthentication


class SessaoAutenticacao(SessionAuthentication):
    """Igual à do DRF, mas faz o anônimo receber 401 em vez de 403.

    O DRF só devolve 401 quando a classe de autenticação tem um
    `authenticate_header`; a SessionAuthentication não tem. Com 403,
    o front mostraria "sem permissão" para quem só precisa entrar."""

    def authenticate_header(self, request):
        return "Session"
```

### `accounts/serializers.py` — arquivo novo

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as ErroDjango
from rest_framework import serializers

from accounts.models import Interesse
from catalogo.models import Curso
from catalogo.serializers import CursoSerializer
from quiz.models import Tentativa_de_resposta
from quiz.serializers import RecomendacaoSerializer

User = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source="first_name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "nome", "is_superuser")


class EntrarSerializer(serializers.Serializer):
    email = serializers.EmailField()
    senha = serializers.CharField(trim_whitespace=False)


class CadastroSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    email = serializers.EmailField()
    senha = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate_email(self, email):
        email = User.objects.normalize_email(email)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def validate(self, dados):
        # Os mesmos AUTH_PASSWORD_VALIDATORS do cadastro por template
        try:
            validate_password(dados["senha"], user=User(email=dados["email"], first_name=dados["nome"]))
        except ErroDjango as erro:
            raise serializers.ValidationError({"senha": list(erro.messages)})
        return dados

    def create(self, dados):
        return User.objects.create_user(email=dados["email"], password=dados["senha"], first_name=dados["nome"])


class InteresseSerializer(serializers.ModelSerializer):
    curso = CursoSerializer(read_only=True)

    class Meta:
        model = Interesse
        fields = ("id", "curso", "status", "criado_em", "rank_snapshot", "era_principal")


class InteresseCriarSerializer(serializers.Serializer):
    curso = serializers.PrimaryKeyRelatedField(queryset=Curso.objects.filter(is_active=True))
    tentativa = serializers.IntegerField(required=False, allow_null=True, default=None)


class TentativaResumoSerializer(serializers.ModelSerializer):
    tentativa_id = serializers.IntegerField(source="id", read_only=True)
    principal = serializers.SerializerMethodField()

    class Meta:
        model = Tentativa_de_resposta
        fields = ("tentativa_id", "criado_em", "respondido_por", "confidence_band", "principal")

    def get_principal(self, tentativa):
        # prefetch ordenado por rank (Meta.ordering) → o primeiro é o rank 1
        rec = next(iter(tentativa.recomendacoes.all()), None)
        return RecomendacaoSerializer(rec).data if rec else None
```

> [!warning] Por que o `try/except` em volta do `validate_password`
> Ele levanta `django.core.exceptions.ValidationError`, não a do DRF. Sem a tradução, uma senha fraca vira **500** em vez de 400 com `{"senha": [...]}`. É o `test_senha_fraca_da_400` da seção 8 que pega isso se alguém "simplificar" o bloco.

### `accounts/api_views.py` — arquivo novo

```python
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Interesse
from accounts.serializers import (
    CadastroSerializer, EntrarSerializer, InteresseCriarSerializer,
    InteresseSerializer, TentativaResumoSerializer, UsuarioSerializer,
)
from accounts.servicos import registrar_interesse
from quiz.models import Tentativa_de_resposta
from quiz.views import tentativas_visiveis


@method_decorator(ensure_csrf_cookie, name="dispatch")
class Csrf(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class Eu(APIView):
    permission_classes = [IsAuthenticated]  # anônimo → 401 pela SessaoAutenticacao

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


class Entrar(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        entrada = EntrarSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        usuario = authenticate(
            request,
            username=entrada.validated_data["email"],  # USERNAME_FIELD = "email"
            password=entrada.validated_data["senha"],
        )
        if usuario is None:
            return Response({"detail": "E-mail ou senha incorretos."}, status=status.HTTP_400_BAD_REQUEST)
        login(request, usuario)  # dispara user_logged_in → claim do C6
        return Response(UsuarioSerializer(usuario).data)


class Cadastro(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        entrada = CadastroSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        usuario = entrada.save()
        login(request, usuario)
        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)


class Sair(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class Interesses(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InteresseSerializer

    def get_queryset(self):
        return Interesse.objects.filter(usuario=self.request.user).select_related("curso__area_principal")

    def create(self, request, *args, **kwargs):
        entrada = InteresseCriarSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        tentativa = None
        if entrada.validated_data["tentativa"]:
            # Só aceita tentativa que esta pessoa pode ver — senão o snapshot
            # poderia ser montado a partir do resultado de outra pessoa.
            tentativa = tentativas_visiveis(request).filter(pk=entrada.validated_data["tentativa"]).first()
        item, criado = registrar_interesse(request.user, entrada.validated_data["curso"], tentativa)
        return Response(
            InteresseSerializer(item).data,
            status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK,
        )


class InteresseDetalhe(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Interesse.objects.filter(usuario=self.request.user)  # de outro → 404


class MinhasTentativas(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TentativaResumoSerializer

    def get_queryset(self):
        return Tentativa_de_resposta.objects.filter(user=self.request.user).prefetch_related(
            "recomendacoes__curso__area_principal"
        )
```

### `accounts/api_urls.py` — arquivo novo

```python
from django.urls import path

from accounts import api_views as v

urlpatterns = [
    path("auth/csrf/", v.Csrf.as_view(), name="api-csrf"),
    path("auth/eu/", v.Eu.as_view(), name="api-eu"),
    path("auth/entrar/", v.Entrar.as_view(), name="api-entrar"),
    path("auth/cadastro/", v.Cadastro.as_view(), name="api-cadastro"),
    path("auth/sair/", v.Sair.as_view(), name="api-sair"),
    path("interesses/", v.Interesses.as_view(), name="api-interesses"),
    path("interesses/<int:pk>/", v.InteresseDetalhe.as_view(), name="api-interesse"),
    path("tentativas/", v.MinhasTentativas.as_view(), name="api-minhas-tentativas"),
]
```

> [!important] `POST /interesses/` é idempotente de propósito
> 201 na primeira vez, 200 nas seguintes, nunca 400 por duplicata. A FE-12 dispara esse POST **depois do login**, e se a rede cair no meio o usuário clica de novo — a segunda tentativa não pode virar erro. O `UniqueConstraint (usuario, curso)` continua sendo a garantia; o `get_or_create` só evita bater nela.

> [!note] O login gira o token de CSRF
> `login()` chama `rotate_token()`: o cookie `csrftoken` muda na resposta do `/auth/entrar/`. O `api.ts` lê o cookie a cada requisição, então o próximo POST já sai com o token novo. Um cliente que guardasse o token em memória quebraria aqui.

---

## 7️⃣ BK-08 — settings

### `core/settings.py` — os trechos que mudam

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-inseguro-troque-em-producao")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

# A SPA: dev pelo proxy do Vite, produção no mesmo domínio (FE-23)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
CSRF_TRUSTED_ORIGINS = [FRONTEND_URL]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "educmatch"),
        "USER": os.environ.get("DB_USER", "root"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "3306"),
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["accounts.autenticacao.SessaoAutenticacao"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"]
    + (["rest_framework.renderers.BrowsableAPIRenderer"] if DEBUG else []),
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  # no lugar de MAILERS

STATIC_URL = "static/"          # uma vez só
STATICFILES_DIRS = [BASE_DIR / "static"]
```

Apague o bloco `MAILERS` e a segunda linha `STATIC_URL`.

> [!danger] `CSRF_TRUSTED_ORIGINS` é obrigatório **mesmo com o proxy**
> O `changeOrigin: true` do Vite reescreve o `Host`, **não** o `Origin`. O navegador manda `Origin: http://localhost:5173`, o Django compara com `localhost:8000` e recusa todo POST de usuário logado com `CSRF Failed: Origin checking failed`. É o erro que parece "o CSRF não funciona com SPA" — e é uma linha.

### `.env.example` — arquivo novo, na raiz de `backend/`

```bash
DJANGO_SECRET_KEY=troque-por-uma-chave-longa
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
FRONTEND_URL=http://localhost:5173
DB_NAME=educmatch
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
```

> [!warning] A senha `devmysql` já está no histórico do git
> Tirar do `settings.py` impede o próximo vazamento, não desfaz este. Se esse MySQL for exposto em algum lugar além da sua máquina, troque a senha.

> [!note] Sem `python-dotenv`
> O `os.environ.get` com default de dev faz o projeto rodar sem arquivo nenhum. Para usar o `.env`, exporte no shell (`set -a; source .env; set +a`). Uma dependência a menos para a banca instalar.

### Models mortos

- Apague `Login` e `Cadastro` de `accounts/models.py` (guardavam **senha em texto puro**) e qualquer `admin.site.register` deles; `python manage.py makemigrations accounts -n remove_login_cadastro`.
- ✅ **Já feito na reorganização de pastas (2026-09-21):** o arquivo virou `requirements.txt` (sem o erro de digitação), com uma linha por pacote:

```text
asgiref==3.12.1
Django==6.1.1
djangorestframework==3.18.1
mysqlclient==2.2.8
sqlparse==0.6.0
tzdata==2026.3
```

---

## 8️⃣ Os testes de contrato

### `quiz/tests/base.py` — acrescente à `BaseEducMatch`

```python
from rest_framework.test import APIClient

    # dentro da classe:
    def api(self):
        """APIClient com o mesmo SERVER_NAME do Client — mesma sessão por instância."""
        return APIClient(SERVER_NAME="localhost")

    def payload_valido(self, coluna=0, nome="Visitante"):
        from quiz.models import Questao

        respostas = []
        for questao in Questao.objects.filter(is_active=True).order_by("id"):
            alternativas = list(questao.alternativas.order_by("id"))
            respostas.append({"questao": questao.id, "alternativa": alternativas[coluna % len(alternativas)].id})
        return {"respondido_por": nome, "respostas": respostas}
```

> [!important] `self.client.post(..., format="json")` não faz o que parece
> `format=` é argumento do `APIClient` do DRF. No `django.test.Client`, ele é ignorado e o corpo vai como multipart — a lista aninhada `respostas` chega vazia e o teste falha pelo motivo errado. Era um dos bugs do `test_api.py` atual.

### `quiz/tests/test_api.py` — substitua

```python
from rest_framework import status

from quiz.tests.base import BaseEducMatch

CHAVES_TENTATIVA = {"tentativa_id", "respondido_por", "criado_em", "confidence_band", "diferenca", "recomendacoes"}
CHAVES_REC = {"rank", "score", "match", "curso", "explicacao"}


class ApiQuizV1(BaseEducMatch):
    def test_questoes_tem_alternativas_e_nao_tem_pesos(self):
        corpo = self.api().get("/api/v1/quiz/questoes/").json()
        self.assertTrue(corpo)
        self.assertEqual(set(corpo[0]), {"id", "texto", "order", "alternativas"})
        self.assertEqual(set(corpo[0]["alternativas"][0]), {"id", "texto", "order"})

    def test_envio_devolve_o_contrato(self):
        resposta = self.api().post("/api/v1/quiz/tentativas/", self.payload_valido(), format="json")
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        corpo = resposta.json()
        self.assertEqual(set(corpo), CHAVES_TENTATIVA)
        self.assertEqual(set(corpo["recomendacoes"][0]), CHAVES_REC)
        self.assertIn("top_areas", corpo["recomendacoes"][0]["explicacao"])
        self.assertEqual(corpo["recomendacoes"][0]["rank"], 1)

    def test_alternativa_de_outra_questao_da_400(self):
        """BK-01: antes era 201 com perfil contaminado."""
        payload = self.payload_valido()
        a, b = payload["respostas"][0], payload["respostas"][1]
        a["alternativa"], b["alternativa"] = b["alternativa"], a["alternativa"]
        resposta = self.api().post("/api/v1/quiz/tentativas/", payload, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_questao_repetida_da_400_e_nao_500(self):
        payload = self.payload_valido()
        payload["respostas"].append(payload["respostas"][0])
        resposta = self.api().post("/api/v1/quiz/tentativas/", payload, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quiz_incompleto_da_400(self):
        payload = self.payload_valido()
        payload["respostas"] = payload["respostas"][:2]
        resposta = self.api().post("/api/v1/quiz/tentativas/", payload, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_visitante_abre_o_proprio_resultado(self):
        """O achado 1 desta nota: sem a sessão, isto era 404."""
        cliente = self.api()
        criado = cliente.post("/api/v1/quiz/tentativas/", self.payload_valido(), format="json").json()
        resposta = cliente.get(f"/api/v1/quiz/tentativas/{criado['tentativa_id']}/")
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(set(resposta.json()), CHAVES_TENTATIVA)

    def test_outro_navegador_nao_abre_tentativa_anonima(self):
        criado = self.api().post("/api/v1/quiz/tentativas/", self.payload_valido(), format="json").json()
        resposta = self.api().get(f"/api/v1/quiz/tentativas/{criado['tentativa_id']}/")
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_tentativa_de_outro_usuario_da_404(self):
        dono = self.criar_usuario("dono@exemplo.com")
        cliente_dono = self.api()
        cliente_dono.force_authenticate(dono)
        criado = cliente_dono.post("/api/v1/quiz/tentativas/", self.payload_valido(), format="json").json()

        intruso = self.api()
        intruso.force_authenticate(self.criar_usuario("intruso@exemplo.com"))
        resposta = intruso.get(f"/api/v1/quiz/tentativas/{criado['tentativa_id']}/")
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_logado_fica_dono_da_tentativa(self):
        """BK-02 / B5: antes, user=None sempre."""
        from quiz.models import Tentativa_de_resposta

        usuario = self.criar_usuario()
        cliente = self.api()
        cliente.force_authenticate(usuario)
        criado = cliente.post("/api/v1/quiz/tentativas/", self.payload_valido(), format="json").json()
        self.assertEqual(Tentativa_de_resposta.objects.get(pk=criado["tentativa_id"]).user, usuario)

    def test_curso_detalhe(self):
        from catalogo.models import Curso

        curso = Curso.objects.filter(is_active=True).first()
        corpo = self.api().get(f"/api/v1/catalogo/cursos/{curso.id}/").json()
        self.assertEqual(set(corpo), {"id", "nome_curso", "descricao", "duracao", "area_principal"})
```

> [!note] `force_authenticate` pula a sessão — e é isso que se quer aqui
> Ele testa a **regra de dono**, não o login. O login de verdade (sessão + claim) é testado em `accounts/tests/test_api_conta.py`, com `POST /auth/entrar/`.

### `accounts/tests/test_api_conta.py` — arquivo novo

```python
from rest_framework import status

from quiz.tests.base import BaseEducMatch


class ApiContaV1(BaseEducMatch):
    def test_eu_anonimo_da_401_e_nao_403(self):
        self.assertEqual(self.api().get("/api/v1/auth/eu/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_cria_sessao_e_eu_responde(self):
        self.criar_usuario("ana@exemplo.com", first_name="Ana")
        cliente = self.api()
        entrou = cliente.post("/api/v1/auth/entrar/", {"email": "ana@exemplo.com", "senha": "afinidade-2026"}, format="json")
        self.assertEqual(entrou.status_code, status.HTTP_200_OK)
        eu = cliente.get("/api/v1/auth/eu/").json()
        self.assertEqual(eu, {"id": eu["id"], "email": "ana@exemplo.com", "nome": "Ana", "is_superuser": False})

    def test_senha_errada_da_400_com_detail(self):
        self.criar_usuario("ana@exemplo.com")
        resposta = self.api().post("/api/v1/auth/entrar/", {"email": "ana@exemplo.com", "senha": "errada"}, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", resposta.json())

    def test_senha_fraca_da_400(self):
        resposta = self.api().post("/api/v1/auth/cadastro/", {"email": "b@exemplo.com", "senha": "123"}, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("senha", resposta.json())

    def test_login_adota_a_tentativa_anonima(self):
        """C6 pela API: responde anônimo, entra, vê no histórico."""
        self.criar_usuario("ana@exemplo.com")
        cliente = self.api()
        cliente.post("/api/v1/quiz/tentativas/", self.payload_valido(), format="json")
        cliente.post("/api/v1/auth/entrar/", {"email": "ana@exemplo.com", "senha": "afinidade-2026"}, format="json")
        historico = cliente.get("/api/v1/tentativas/").json()
        self.assertEqual(len(historico), 1)
        self.assertEqual(historico[0]["principal"]["rank"], 1)

    def test_interesse_grava_snapshot_e_e_idempotente(self):
        self.criar_usuario("ana@exemplo.com")
        cliente = self.api()
        tentativa = cliente.post("/api/v1/quiz/tentativas/", self.payload_valido(), format="json").json()
        cliente.post("/api/v1/auth/entrar/", {"email": "ana@exemplo.com", "senha": "afinidade-2026"}, format="json")
        principal = tentativa["recomendacoes"][0]["curso"]["id"]

        corpo = {"curso": principal, "tentativa": tentativa["tentativa_id"]}
        primeira = cliente.post("/api/v1/interesses/", corpo, format="json")
        segunda = cliente.post("/api/v1/interesses/", corpo, format="json")

        self.assertEqual(primeira.status_code, status.HTTP_201_CREATED)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)
        self.assertEqual(primeira.json()["rank_snapshot"], 1)
        self.assertTrue(primeira.json()["era_principal"])

    def test_nao_remove_interesse_alheio(self):
        from accounts.models import Interesse
        from catalogo.models import Curso

        alheio = Interesse.objects.create(usuario=self.criar_usuario("outro@exemplo.com"), curso=Curso.objects.first())
        cliente = self.api()
        cliente.force_authenticate(self.criar_usuario("eu@exemplo.com"))
        self.assertEqual(cliente.delete(f"/api/v1/interesses/{alheio.id}/").status_code, status.HTTP_404_NOT_FOUND)

    def test_painel_exige_superusuario(self):
        cliente = self.api()
        cliente.force_authenticate(self.criar_usuario())
        self.assertEqual(cliente.get("/api/v1/painel/metricas/").status_code, status.HTTP_403_FORBIDDEN)

    def test_conversao_suprimida_nao_vaza_pela_taxa(self):
        """5 tentativas iguais: os 5 cursos recomendados têm recomendado=5 e
        interessados=0 (< k) — suprimidos. A taxa não pode sobrar."""
        from painel.privacidade import K_MINIMO

        cliente = self.api()
        cliente.force_authenticate(self.criar_usuario(is_superuser=True, is_staff=True))
        for _ in range(K_MINIMO):
            cliente.post("/api/v1/quiz/tentativas/", self.payload_valido(), format="json")

        conversao = cliente.get("/api/v1/painel/metricas/?periodo=30").json()["conversao"]
        suprimidas = [linha for linha in conversao if linha.get("suprimido")]

        self.assertTrue(suprimidas)
        self.assertTrue(all(linha["taxa"] is None for linha in suprimidas))

    def test_painel_sem_massa_nao_devolve_numeros(self):
        cliente = self.api()
        cliente.force_authenticate(self.criar_usuario(is_superuser=True, is_staff=True))
        corpo = cliente.get("/api/v1/painel/metricas/?periodo=30").json()
        self.assertFalse(corpo["tem_massa"])
        self.assertEqual(set(corpo), {"periodo", "total_de_tentativas", "tem_massa", "k_minimo"})
```

> [!tip] `test_login_adota_a_tentativa_anonima` é o C6 inteiro em seis linhas
> Se ele passa, três coisas estão certas ao mesmo tempo: o POST grava na sessão (BK-02), o `login()` da API dispara o sinal (BK-07), e o histórico lê por `user` (BK-07). É o teste para mostrar à banca.

---

## 9️⃣ Verificação

```bash
python manage.py makemigrations --check --dry-run   # "No changes detected"
python manage.py migrate
python manage.py test quiz.tests.test_api accounts.tests.test_api_conta painel -v 2
python manage.py test 2>&1 | tail -5                 # compare com a linha de base da seção 0
python manage.py check --deploy                      # avisos de DEBUG/HSTS são esperados em dev; nenhum erro novo
```

Com `runserver` de pé, o roteiro no navegador (a API navegável do DRF aparece porque `DEBUG=1`):

| # | Abrir | Esperado |
|---|---|---|
| 1 | `/api/v1/quiz/questoes/` | Lista com `alternativas` aninhadas; **nenhum** `peso` na página |
| 2 | POST em `/api/v1/quiz/tentativas/` pelo formulário do DRF | 201 com `recomendacoes[0].explicacao.top_areas` como **objeto**, não string |
| 3 | `/api/v1/quiz/tentativas/<id do passo 2>/` | 200 — mesma aba, mesma sessão |
| 4 | O mesmo endereço numa janela anônima | 404 |
| 5 | `/api/v1/auth/eu/` deslogado | 401 |
| 6 | `/quiz/dashboard/` como superusuário | O dashboard de template de sempre — a BK-06 não o quebrou |
| 7 | `/` e `/resultado/<id>/` | Os templates continuam funcionando: plano B intacto |

---

## 🔟 O commit

Desde 2026-09-21 o projeto é **um repositório só** (monorepo: `backend/`, `frontend/`, `docs/`). Um PR, como manda o plano:

```bash
cd "$HOME/Documents/vscode/educmatch"
git switch -c fase-0-api-v1
git add -A
git status --short     # confira: nada de .env, nada de __pycache__
git commit -m "$(cat <<'EOF'
feat(api): API v1 para a SPA (BK-01 a BK-08)

Monta /api/v1/ com o contrato da spec do front e prova por teste de
contrato. Os templates continuam no ar: são o plano B até a FE-24.

- Serializers do quiz: validate/validate_respostas (estavam com nomes
  que o DRF nunca chama), campo alternativa, alternativas aninhadas sem
  expor Peso_alternativa, curso.nome_curso
- EnvioQuiz vincula o usuário logado, aceita questionario_link e grava a
  tentativa na sessão (sem isso o visitante não abria o próprio resultado)
- GET /quiz/tentativas/<pk>/ com a regra de dono do C6; 404, nunca 403
- Recomendacao.explicacao TextField -> JSONField, com migração que
  converte o repr antigo antes do ALTER; fim do ast.literal_eval
- Interesse com o C4 completo: tentativa_origem, rank/afinidade_snapshot,
  era_principal, criado_em auto_now_add; serviço único registrar_interesse
- painel/metricas.py sem FieldError; top de manifestações conta Interesse
- Endpoints de auth (sessão + CSRF), interesses, histórico, painel e links
- Anônimo recebe 401, não 403 (SessaoAutenticacao)
- settings por variável de ambiente, CSRF_TRUSTED_ORIGINS para o Vite,
  sem MAILERS nem STATIC_URL duplicado; models Login/Cadastro removidos

Spec: vault > EducMatch(Secretária) > passo-a-passo-bk-01-bk-08
EOF
)"
```

---

## ▶️ Próxima ação

Fechada a Fase 0, volte ao front: [[Projetos/EducMatch(Secretária)/passo-a-passo-fe-06-fe-10|🎯 FE-06 a FE-10 — fluxo público]]. É ali que o primeiro `fetch` de verdade acontece.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front]] — §2 (a auditoria B1–B15) e §3 (o contrato)
- [[Projetos/EducMatch(Secretária)/contratos-c1-a-c6|📜 C1–C6]] — o C4 que decidiu o D-rank e o C6 que o `tentativas_visiveis` implementa
- [[Projetos/EducMatch(Secretária)/api-quiz-drf|🔌 API REST do quiz]] — histórico: o vocabulário em inglês que esta fase aposenta
- [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições]] — onde o `validar`/`validate` merece virar entrada
- **Conceitos:** [[cs-csrf|🚨 CSRF]] · [[CORS|🌐 CORS]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]]
