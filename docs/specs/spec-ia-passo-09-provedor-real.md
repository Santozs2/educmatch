---
title: "Spec IA · Passo 9 — provedor real, cache, timeout, fallback e gravação"
aliases: ["Passo 9", "Provedor real", "OpenAICompatProvider", "Fallback da LLM"]
tags: [tcc, ia, llm, spec, provedor, cache, fallback]
status: proposto
projeto: TCC
branch: feature/llm-provedor-real
criado: 2026-10-08
---

> [!info] Plano da IA: [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 Camada de IA]] · Anterior: [[spec-ia-passo-08-prompt-e-validacao|📝 Passo 8]] · Próximo: [[spec-ia-passo-10-tela-de-entrega|🎨 Passo 10]]

# 🌐 Passo 9: provedor real, cache, timeout, fallback e gravação

**Branch:** `feature/llm-provedor-real`, saindo da `develop` **com o Passo 8 já mesclado**
**Risco:** médio. É o primeiro passo que **muda o quiz**: depois da engine, o `POST` chama a LLM (se `LLM_ENABLED=1`). Com a LLM desligada, que é o padrão, nada muda.
**Testes ao final:** a suíte do Passo 8 **+ 15** (na cópia: 191)

> [!abstract] O que esta branch faz
> 1. **Um provedor real** que fala com qualquer API no formato da OpenAI: Gemini, Groq, OpenRouter, OmniRoute ou Ollama, escolhido pelo `.env`.
> 2. **Cache no banco:** o mesmo perfil recebe a mesma resposta, sem nova chamada. É isso que garante a reprodutibilidade na banca.
> 3. **`entregar(tentativa)`:** grava `rank_final`, `llm_text` e os metadados ou, em **qualquer** falha (timeout, sem cota, saída inválida, bug), mantém a ordem da engine e marca `used_fallback`.
> 4. **O quiz chama o `entregar`** depois da engine, fora da transação.
> 5. **`python manage.py testar_llm`:** uma chamada de verdade, para conferir a chave.

> [!success] O código desta spec já foi rodado
> Aplicado numa cópia sobre o Passo 8: os **15 testes novos** passaram **sem rede** (o provedor real é testado com a rede trocada por um dublê). A suíte fechou em **191 testes**; o único erro é o do fuso, que depende do MySQL. Também foi rodado de ponta a ponta no navegador com `LLM_ENABLED=1` e o provedor `fake`: o quiz gravou `llm_model`, `latency_ms` e os textos.

---

## 🎓 Entenda antes de começar

```
POST do quiz
   │
   ├─ transaction.atomic():  Tentativa + Respostas + engine.recomendar()   ← já existia
   │                                                                         O RESULTADO JÁ ESTÁ GRAVADO
   └─ entregar(tentativa)     ← NOVO, fora da transação
         ├─ LLM_ENABLED=0 → não faz nada
         ├─ deliver(): prompt → cache? → provedor → validação → Entrega
         ├─ ✅ Entrega → grava rank_final, llm_text, llm_model, latency_ms, tokens, diverged, cache_hit
         └─ ❌ qualquer erro → rank_final = rank_engine, llm_text = "", used_fallback = True
```

> [!important] Quatro escolhas que diferem do plano original
> | Plano da IA | Aqui | Por quê |
> |---|---|---|
> | `quiz/llm/gemini.py` com o **SDK do Gemini** | `quiz/llm/openai_compat.py` com **`urllib`** (biblioteca padrão) | Gemini, Groq, OpenRouter, OmniRoute e Ollama aceitam o formato `/chat/completions` da OpenAI. Um provedor serve para todos e **nenhuma dependência nova** entra no `requirements.txt`. `LLM_PROVIDER=gemini` continua existindo e já aponta para o endereço do Google |
> | Chave do cache = hash das respostas + versão + modelo | Hash de **provedor + modelo + versão + prompt montado** | O prompt montado já contém o perfil, os candidatos e o `tie_set`. Se qualquer um deles mudar, a chave muda sozinha |
> | `diverged` = "comparar `rank_final` com `rank_engine`" | `diverged` = **o 1º entregue não é o 1º da engine** | É a métrica que o Passo 11 usa: "% em que a LLM trocou o 1º lugar". Reordenar as alternativas não conta como divergência |
> | Carregamento em duas etapas (Passo 10) | **Uma etapa**, com timeout de 8 s | A tela "Analisando" já cobre a espera, e o cache serve as repetições na hora. Duas etapas exigiriam JavaScript buscando o texto depois, para um ganho pequeno |

---

## 1️⃣ `backend/quiz/llm/openai_compat.py` (arquivo novo)

```python
"""Provedor real: qualquer API no formato /chat/completions da OpenAI.

Gemini, Groq, OpenRouter, OmniRoute e Ollama aceitam esse formato: trocar de
provedor é trocar LLM_BASE_URL, LLM_MODEL e LLM_API_KEY no .env, sem código.
Usa só a biblioteca padrão (urllib): nenhuma dependência nova.
"""
import json
import urllib.error
import urllib.request

from django.conf import settings

from quiz.llm.base import LLMResponse, LLMTimeout, LLMUnavailable

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
MAX_TOKENS = 2048  # o JSON de saída tem ~1.500 caracteres; sobra para modelos que "pensam"


class OpenAICompatProvider:
    name = "openai_compat"

    def __init__(self, base_url=None, model=None, api_key=None, timeout=None):
        self.base_url = (settings.LLM_BASE_URL if base_url is None else base_url).rstrip("/")
        self.model = settings.LLM_MODEL if model is None else model
        self.api_key = settings.LLM_API_KEY if api_key is None else api_key
        self.timeout = settings.LLM_TIMEOUT if timeout is None else timeout
        if not self.base_url or not self.model:
            raise LLMUnavailable("LLM_BASE_URL e LLM_MODEL são obrigatórios")

    def complete(self, prompt: str) -> LLMResponse:
        corpo = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": MAX_TOKENS,
        }).encode("utf-8")
        pedido = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=corpo,
            method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
        )
        try:
            with urllib.request.urlopen(pedido, timeout=self.timeout) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
        except urllib.error.HTTPError as erro:
            # 401/403 = chave, 429 = cota do plano gratuito, 5xx = provedor fora
            raise LLMUnavailable(f"HTTP {erro.code} do provedor") from None
        except urllib.error.URLError as erro:
            if isinstance(erro.reason, TimeoutError):
                raise LLMTimeout(f"sem resposta em {self.timeout}s") from None
            raise LLMUnavailable(f"sem conexão: {erro.reason}") from None
        except TimeoutError:
            raise LLMTimeout(f"sem resposta em {self.timeout}s") from None
        except (OSError, ValueError) as erro:
            raise LLMUnavailable(f"resposta ilegível: {erro}") from None

        try:
            texto = dados["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise LLMUnavailable("a resposta não tem choices[0].message.content") from None
        uso = dados.get("usage") or {}
        return LLMResponse(
            text=texto or "",
            model=dados.get("model") or self.model,
            tokens_in=uso.get("prompt_tokens"),
            tokens_out=uso.get("completion_tokens"),
        )


def gemini():
    """O mesmo provedor, já apontado para o Gemini se LLM_BASE_URL estiver vazio."""
    return OpenAICompatProvider(base_url=settings.LLM_BASE_URL or GEMINI_BASE_URL)
```

> [!note] 🎓 A ordem dos `except` importa
> `HTTPError` é um tipo de `URLError`, e `TimeoutError` é um tipo de `OSError`. Por isso cada um vem **antes** do mais geral; senão, o mais geral pegaria tudo. O timeout pode chegar de dois jeitos: ao conectar (embrulhado num `URLError`) ou ao ler a resposta (um `TimeoutError` direto).

> [!note] 🎓 `temperature: 0` e `max_tokens: 2048`
> `temperature: 0` reduz a variação de uma chamada para outra, mas **não a elimina**: quem garante a mesma resposta é o cache. E 2048 tokens sobra para os ~1.500 caracteres do JSON, mesmo em modelos que gastam tokens "pensando" antes de responder.

> [!warning] A chave **nunca** sai do servidor
> Ela vai no cabeçalho `Authorization` e em nenhum outro lugar. A mensagem de erro mostra só o código HTTP, nunca o pedido nem a chave.

## 2️⃣ `backend/quiz/llm/__init__.py`: registrar os provedores

```python
from quiz.llm.fake import FakeProvider
from quiz.llm.openai_compat import OpenAICompatProvider, gemini

__all__ = [
    "FakeProvider", "LLMError", "LLMInvalidOutput", "LLMProvider", "LLMResponse", "LLMTimeout",
    "LLMUnavailable", "OpenAICompatProvider", "get_provider",
]

PROVIDERS = {
    "fake": FakeProvider,
    "openai_compat": OpenAICompatProvider,
    "gemini": gemini,
}
```

Era isto que o Passo 7 prometia: **um arquivo novo e uma linha (aqui, duas) no `PROVIDERS`**. O `get_provider()` não muda.

## 3️⃣ Configuração

### `backend/core/settings.py`

No `CACHES`, acrescente o `OPTIONS`:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "educmatch_cache",
        # O padrão do Django é 300 entradas, e depois ele apaga um terço delas.
        "OPTIONS": {"MAX_ENTRIES": 10000},
    }
}
```

E troque a linha do `LLM_PROVIDER` por estas duas:

```python
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "fake")  # fake | gemini | openai_compat
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")  # vazio + gemini = endereço do Gemini
```

> [!danger] Sem o `MAX_ENTRIES`, o cache da banca some sozinho
> O `DatabaseCache` guarda no máximo **300** entradas por padrão. Passando disso, ele apaga um terço delas, **inclusive as que não expiram**. Com o experimento do Passo 11 rodando dezenas de perfis, os perfis de demonstração pré-aquecidos para a banca seriam apagados.

### `backend/.env.example`: depois de `LLM_PROVIDER=fake`

```env
LLM_BASE_URL=
```

### `backend/core/tests.py`: o provedor novo é válido

```python
        self.assertIn(settings.LLM_PROVIDER, {"fake", "gemini", "openai_compat"})
```

## 4️⃣ `backend/quiz/serializers.py`: a `Entrega` leva os dados da chamada

Substitua a classe `Entrega`:

```python
@dataclass(frozen=True)
class Entrega:
    """A saída aprovada: a ordem final (o principal primeiro) e o texto de cada curso.

    Os campos com padrão são os dados da chamada, preenchidos pelo deliver (Passo 9).
    """

    ordem: list[int]
    textos: dict[int, str]
    modelo: str = ""
    tokens_in: int | None = None
    tokens_out: int | None = None
    cache_hit: bool = False
```

> [!tip] 🎓 Campos com valor padrão: nada do Passo 8 quebra
> O `validate_delivery` continua criando `Entrega(ordem=..., textos=...)`, e os testes do Passo 8 continuam iguais. O `deliver` completa o resto com `dataclasses.replace`.

## 5️⃣ `backend/quiz/delivery.py`: cache, fallback e gravação

Troque os imports do topo:

```python
import hashlib
import logging
import time
from dataclasses import asdict, replace

from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from quiz.engine import TOP3, perfil_vetor
from quiz.llm import LLMError, LLMResponse, get_provider
from quiz.models import Recomendacao
from quiz.prompt import montar_prompt
from quiz.serializers import Entrega, validate_delivery

logger = logging.getLogger(__name__)
```

E substitua tudo **depois** do `build_payload` (que não muda) por:

```python
def chave_do_cache(prompt):
    """Mesmo provedor, modelo, versão e prompt = mesma chave. O prompt já traz o perfil."""
    bruto = "|".join([settings.LLM_PROVIDER, settings.LLM_MODEL, settings.LLM_PROMPT_VERSION, prompt])
    return "llm:" + hashlib.sha256(bruto.encode("utf-8")).hexdigest()


def deliver(attempt) -> Entrega | None:
    """A entrega da LLM, já revisada. Com a IA desligada, não chama nada.

    Saída fora do contrato vira LLMInvalidOutput: nada inválido sai daqui.
    Só resposta aprovada entra no cache; no acerto, não há tokens gastos.
    """
    if not settings.LLM_ENABLED:
        return None
    payload = build_payload(attempt)
    if not payload["candidatos"]:
        return None
    prompt = montar_prompt(payload, settings.LLM_PROMPT_VERSION)
    chave = chave_do_cache(prompt)

    guardada = cache.get(chave)
    resposta = LLMResponse(**guardada) if guardada else get_provider().complete(prompt)
    entrega = validate_delivery(resposta.text, payload)
    if not guardada:
        cache.set(chave, asdict(resposta), timeout=None)  # não expira: é a resposta da banca
    return replace(
        entrega,
        modelo=resposta.model,
        tokens_in=None if guardada else resposta.tokens_in,
        tokens_out=None if guardada else resposta.tokens_out,
        cache_hit=bool(guardada),
    )


def entregar(attempt) -> bool:
    """Passo 9: grava a entrega da LLM ou, em qualquer falha, a ordem da engine.

    Nunca levanta exceção: a engine já gravou o resultado antes, e é ele que o
    aluno vê se a LLM falhar. Devolve True quando o texto da LLM foi gravado.
    """
    if not settings.LLM_ENABLED:
        return False
    inicio = time.monotonic()
    try:
        entrega = deliver(attempt)
    except LLMError as erro:
        logger.warning("LLM no fallback (tentativa %s): %s", attempt.pk, erro)
        entrega, falhou = None, True
    except Exception:  # um bug nosso também não pode virar erro 500 no quiz
        logger.exception("Erro inesperado na camada de IA (tentativa %s)", attempt.pk)
        entrega, falhou = None, True
    else:
        if entrega is None:
            return False  # sem candidatos: não houve chamada
        falhou = False

    _gravar(attempt, entrega, latencia_ms=round((time.monotonic() - inicio) * 1000))
    return not falhou


@transaction.atomic
def _gravar(attempt, entrega, latencia_ms):
    recomendacoes = list(attempt.recomendacoes.order_by("rank_engine"))
    if entrega is None:
        for rec in recomendacoes:
            rec.rank_final, rec.llm_text = rec.rank_engine, ""
    else:
        posicao = {curso_id: i for i, curso_id in enumerate(entrega.ordem, start=1)}
        for rec in recomendacoes:
            rec.rank_final, rec.llm_text = posicao[rec.curso_id], entrega.textos[rec.curso_id]
    Recomendacao.objects.bulk_update(recomendacoes, ["rank_final", "llm_text"])

    metadados = {
        "llm_model": (entrega.modelo if entrega else settings.LLM_MODEL or settings.LLM_PROVIDER)[:60],
        "prompt_version": settings.LLM_PROMPT_VERSION[:20],
        "latency_ms": latencia_ms,
        "tokens_in": entrega.tokens_in if entrega else None,
        "tokens_out": entrega.tokens_out if entrega else None,
        "used_fallback": entrega is None,
        # Medido pelo servidor, não declarado pela LLM: o 1º entregue é o 1º da engine?
        "diverged": bool(entrega) and entrega.ordem[0] != recomendacoes[0].curso_id,
        "cache_hit": bool(entrega) and entrega.cache_hit,
    }
    for campo, valor in metadados.items():
        setattr(attempt, campo, valor)
    attempt.save(update_fields=list(metadados))
```

> [!important] Só resposta **aprovada** entra no cache
> O `cache.set` vem **depois** do `validate_delivery`. Se a LLM devolver lixo, nada é guardado, e a próxima tentativa do mesmo perfil chama de novo, em vez de repetir o lixo para sempre. Há um teste para isso (`test_resposta_recusada_nao_entra_no_cache`).

> [!note] 🎓 `deliver` × `entregar`
> - **`deliver`** devolve a entrega ou **levanta** o erro. É fácil de testar, porque cada falha tem seu tipo.
> - **`entregar`** **nunca levanta**: transforma qualquer falha em fallback e grava. É o único que o quiz chama.
>
> O `except Exception` é de propósito: um bug **nosso** na camada de IA também não pode virar erro 500 no quiz. Ele vai para o log com o traceback (`logger.exception`), e o aluno vê o resultado da engine.

> [!note] 🎓 `llm_model` também é gravado no fallback
> Ele recebe o modelo que **deveria** ter respondido. É assim que o painel do Passo 11 sabe que a LLM foi **chamada** e falhou, e consegue diferenciar isso de uma tentativa com a LLM desligada (`llm_model` vazio).

## 6️⃣ `backend/quiz/web_views.py`: o quiz chama a LLM

No topo:

```python
from quiz.delivery import entregar
from quiz.engine import recomendar
```

E no `pagina_quiz`, **depois** do bloco `with transaction.atomic():` (no mesmo nível de indentação do `with`):

```python
        recomendar(tentativa)
    # Fora da transação: a chamada de rede (até LLM_TIMEOUT) não segura o banco,
    # e o resultado da engine já está gravado se a LLM falhar.
    entregar(tentativa)
    tentativas = request.session.setdefault("minhas_tentativas", [])
```

> [!danger] Fora do `with`, nunca dentro
> Dentro da transação, os 8 s de espera da rede segurariam o banco aberto, e um erro na gravação da LLM desfaria **também** a tentativa e a engine. Fora dela, o resultado da engine já está salvo antes da primeira chamada de rede.

## 7️⃣ `backend/quiz/management/commands/testar_llm.py` (arquivo novo)

```python
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from quiz.delivery import build_payload
from quiz.llm import LLMError, get_provider
from quiz.models import Tentativa_de_resposta
from quiz.prompt import montar_prompt
from quiz.serializers import validate_delivery


class Command(BaseCommand):
    help = (
        "Faz UMA chamada ao provedor do .env com a última tentativa do banco e mostra "
        "o resultado. Não grava nada e não usa o cache: serve para conferir a chave."
    )

    def handle(self, *args, **options):
        tentativa = (
            Tentativa_de_resposta.objects.filter(recomendacoes__isnull=False).order_by("-id").first()
        )
        if tentativa is None:
            raise CommandError("Responda o quiz uma vez antes: não há tentativa com recomendações.")
        if not settings.LLM_ENABLED:
            self.stdout.write(self.style.WARNING("LLM_ENABLED=0: o quiz não chama a LLM; este teste chama mesmo assim."))

        payload = build_payload(tentativa)
        self.stdout.write(f"Provedor: {settings.LLM_PROVIDER} | modelo: {settings.LLM_MODEL or '(vazio)'} | tentativa {tentativa.pk}")
        inicio = time.monotonic()
        try:
            resposta = get_provider().complete(montar_prompt(payload, settings.LLM_PROMPT_VERSION))
            latencia = round((time.monotonic() - inicio) * 1000)
            self.stdout.write(f"Respondeu em {latencia} ms | modelo {resposta.model} | tokens {resposta.tokens_in} → {resposta.tokens_out}")
            entrega = validate_delivery(resposta.text, payload)
        except LLMError as erro:
            raise CommandError(f"{type(erro).__name__}: {erro}") from None

        nomes = {c["course_id"]: c["nome"] for c in payload["candidatos"]}
        motor = [c["course_id"] for c in payload["candidatos"]]
        self.stdout.write(self.style.SUCCESS("Saída aprovada pela validação."))
        for posicao, curso_id in enumerate(entrega.ordem, start=1):
            marca = "" if motor[posicao - 1] == curso_id else f"  (engine: {motor.index(curso_id) + 1}º)"
            self.stdout.write(f"\n{posicao}. {nomes[curso_id]}{marca}\n   {entrega.textos[curso_id]}")
```

Saída real na cópia, com o provedor `fake`:

```
Provedor: fake | modelo: (vazio) | tentativa 1
Respondeu em 0 ms | modelo fake | tokens None → None
Saída aprovada pela validação.

1. Operação e Programação de Robô de Soldagem MAG
   Texto de teste do curso 19.

2. Caldeireiro Montador
   Texto de teste do curso 16.
...
```

---

## 8️⃣ Testes

### `backend/quiz/tests/test_llm_openai_compat.py` (arquivo novo)

```python
import json
import urllib.error
from unittest import mock

from django.test import SimpleTestCase, override_settings

from quiz.llm import LLMTimeout, LLMUnavailable, OpenAICompatProvider, get_provider
from quiz.llm.openai_compat import GEMINI_BASE_URL

URLOPEN = "quiz.llm.openai_compat.urllib.request.urlopen"


def resposta_http(corpo):
    """O objeto que o urlopen devolve, com o corpo em JSON."""
    resposta = mock.MagicMock()
    resposta.__enter__.return_value.read.return_value = json.dumps(corpo).encode("utf-8")
    return resposta


OK = {
    "model": "gemini-2.5-flash-lite",
    "choices": [{"message": {"content": '{"principal": {}}'}}],
    "usage": {"prompt_tokens": 1200, "completion_tokens": 350},
}


class OpenAICompatProviderTest(SimpleTestCase):
    """Passo 9: o provedor real, com a rede trocada por um dublê."""

    def provedor(self):
        return OpenAICompatProvider(base_url="https://api.exemplo/v1/", model="modelo-x", api_key="chave", timeout=8)

    def test_monta_o_pedido_e_le_a_resposta(self):
        with mock.patch(URLOPEN, return_value=resposta_http(OK)) as urlopen:
            resposta = self.provedor().complete("o prompt")

        pedido = urlopen.call_args.args[0]
        corpo = json.loads(pedido.data)
        self.assertEqual(pedido.full_url, "https://api.exemplo/v1/chat/completions")
        self.assertEqual(pedido.get_header("Authorization"), "Bearer chave")
        self.assertEqual(corpo["model"], "modelo-x")
        self.assertEqual(corpo["temperature"], 0)
        self.assertEqual(corpo["messages"], [{"role": "user", "content": "o prompt"}])
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 8)

        self.assertEqual(resposta.text, '{"principal": {}}')
        self.assertEqual(resposta.model, "gemini-2.5-flash-lite")
        self.assertEqual((resposta.tokens_in, resposta.tokens_out), (1200, 350))

    def test_erros_viram_erros_da_camada(self):
        casos = {
            "cota do plano gratuito (429)": (
                urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None), LLMUnavailable),
            "chave errada (401)": (urllib.error.HTTPError("u", 401, "Unauthorized", {}, None), LLMUnavailable),
            "timeout": (TimeoutError("timed out"), LLMTimeout),
            "timeout ao conectar": (urllib.error.URLError(TimeoutError("timed out")), LLMTimeout),
            "sem internet": (urllib.error.URLError("getaddrinfo failed"), LLMUnavailable),
        }
        for nome, (erro, esperado) in casos.items():
            with self.subTest(nome), mock.patch(URLOPEN, side_effect=erro):
                with self.assertRaises(esperado):
                    self.provedor().complete("o prompt")

    def test_corpo_fora_do_formato_e_erro_da_camada(self):
        with mock.patch(URLOPEN, return_value=resposta_http({"error": "?"})):
            with self.assertRaises(LLMUnavailable):
                self.provedor().complete("o prompt")

    def test_sem_endereco_ou_modelo_nao_monta(self):
        with self.assertRaises(LLMUnavailable):
            OpenAICompatProvider(base_url="", model="modelo-x", api_key="", timeout=8)
        with self.assertRaises(LLMUnavailable):
            OpenAICompatProvider(base_url="https://api.exemplo/v1", model="", api_key="", timeout=8)


class GetProviderRealTest(SimpleTestCase):
    @override_settings(LLM_PROVIDER="gemini", LLM_BASE_URL="", LLM_MODEL="gemini-2.5-flash-lite")
    def test_gemini_sem_endereco_usa_o_do_google(self):
        self.assertEqual(get_provider().base_url, GEMINI_BASE_URL)

    @override_settings(LLM_PROVIDER="openai_compat", LLM_BASE_URL="https://api.groq.com/openai/v1", LLM_MODEL="llama")
    def test_openai_compat_usa_o_endereco_do_env(self):
        self.assertEqual(get_provider().base_url, "https://api.groq.com/openai/v1")
```

> [!tip] 🎓 Testar o provedor real **sem** rede
> O `mock.patch(URLOPEN, ...)` troca o `urlopen` por um dublê só durante o teste. Assim se prova que o pedido sai certo (endereço, chave, `temperature`, timeout) e que **cada erro de rede** vira o erro certo da camada, sem gastar cota nem depender do Wi-Fi.

### `backend/quiz/tests/test_llm_gravacao.py` (arquivo novo)

```python
import json
from unittest import mock

from django.test import override_settings

from quiz.delivery import entregar
from quiz.llm import FakeProvider, LLMResponse, LLMTimeout
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch

PROVEDOR = "quiz.delivery.get_provider"


class Roteiro:
    """Provedor de teste que conta as chamadas e responde o que o teste mandar."""

    name = "roteiro"

    def __init__(self, responder=None, erro=None):
        self.chamadas = 0
        self.responder = responder
        self.erro = erro

    def complete(self, prompt):
        self.chamadas += 1
        if self.erro:
            raise self.erro
        if self.responder:
            return LLMResponse(text=self.responder(), model="roteiro", tokens_in=900, tokens_out=300)
        resposta = FakeProvider().complete(prompt)
        return LLMResponse(text=resposta.text, model="roteiro", tokens_in=900, tokens_out=300)


@override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_MODEL="", LLM_PROMPT_VERSION="v1")
class EntregarTest(BaseEducMatch):
    """Passo 9: grava a entrega ou cai na engine, e mede tudo."""

    def ordem_engine(self, tentativa):
        return list(tentativa.recomendacoes.order_by("rank_engine").values_list("curso_id", flat=True))

    def assertOrdemDaEngine(self, tentativa):
        for rec in tentativa.recomendacoes.all():
            self.assertEqual(rec.rank_final, rec.rank_engine)
            self.assertEqual(rec.llm_text, "")

    @override_settings(LLM_ENABLED=False)
    def test_desligada_nao_grava_nada(self):
        tentativa = self.criar_tentativa()

        self.assertFalse(entregar(tentativa))

        tentativa.refresh_from_db()
        self.assertEqual(tentativa.llm_model, "")
        self.assertOrdemDaEngine(tentativa)

    def test_entrega_valida_e_gravada_com_os_metadados(self):
        tentativa = self.criar_tentativa()

        self.assertTrue(entregar(tentativa))

        tentativa.refresh_from_db()
        self.assertTrue(all(rec.llm_text for rec in tentativa.recomendacoes.all()))
        self.assertEqual(tentativa.llm_model, "fake")
        self.assertEqual(tentativa.prompt_version, "v1")
        self.assertIsNotNone(tentativa.latency_ms)
        self.assertFalse(tentativa.used_fallback)
        self.assertFalse(tentativa.diverged)
        self.assertFalse(tentativa.cache_hit)

    def test_troca_dentro_do_tie_set_e_gravada_como_divergencia(self):
        tentativa = self.criar_tentativa()
        primeiro, segundo, *resto = self.ordem_engine(tentativa)
        tentativa.tie_set = [primeiro, segundo]
        tentativa.save(update_fields=["tie_set"])

        def segundo_em_primeiro():
            return json.dumps({
                "principal": {"course_id": segundo, "texto": "Principal."},
                "alternativas": [{"course_id": i, "texto": "Alternativa."} for i in [primeiro, *resto]],
            })

        with mock.patch(PROVEDOR, return_value=Roteiro(responder=segundo_em_primeiro)):
            self.assertTrue(entregar(tentativa))

        tentativa.refresh_from_db()
        trocado = tentativa.recomendacoes.get(curso_id=segundo)
        self.assertEqual((trocado.rank_final, trocado.rank_engine), (1, 2))
        self.assertTrue(trocado.is_primary)
        self.assertTrue(tentativa.diverged)
        self.assertEqual((tentativa.tokens_in, tentativa.tokens_out), (900, 300))

    def test_falhas_caem_na_engine_sem_erro(self):
        casos = {
            "saída inválida": Roteiro(responder=lambda: '{"principal": {"course_id": 999, "texto": "x"}}'),
            "timeout": Roteiro(erro=LLMTimeout("8s")),
            "bug inesperado": Roteiro(erro=RuntimeError("bug")),
        }
        for nome, provedor in casos.items():
            with self.subTest(nome):
                tentativa = self.criar_tentativa()
                with mock.patch(PROVEDOR, return_value=provedor), self.assertLogs("quiz.delivery", "WARNING"):
                    self.assertFalse(entregar(tentativa))

                tentativa.refresh_from_db()
                self.assertTrue(tentativa.used_fallback)
                self.assertFalse(tentativa.diverged)
                self.assertOrdemDaEngine(tentativa)

    def test_mesmo_perfil_sai_do_cache(self):
        provedor = Roteiro()
        with mock.patch(PROVEDOR, return_value=provedor):
            primeira = self.criar_tentativa()
            entregar(primeira)
            segunda = self.criar_tentativa()  # mesmas respostas
            entregar(segunda)

        self.assertEqual(provedor.chamadas, 1)
        segunda.refresh_from_db()
        self.assertTrue(segunda.cache_hit)
        self.assertIsNone(segunda.tokens_in)  # no cache não se gasta token
        self.assertEqual(
            list(segunda.recomendacoes.values_list("llm_text", flat=True)),
            list(primeira.recomendacoes.values_list("llm_text", flat=True)),
        )

    def test_resposta_recusada_nao_entra_no_cache(self):
        lixo = Roteiro(responder=lambda: "não é JSON")
        with mock.patch(PROVEDOR, return_value=lixo), self.assertLogs("quiz.delivery", "WARNING"):
            entregar(self.criar_tentativa())
            entregar(self.criar_tentativa())

        self.assertEqual(lixo.chamadas, 2)

    def test_trocar_o_modelo_nao_reaproveita_o_cache(self):
        provedor = Roteiro()
        with mock.patch(PROVEDOR, return_value=provedor):
            entregar(self.criar_tentativa())
            with self.settings(LLM_MODEL="outro-modelo"):
                entregar(self.criar_tentativa())

        self.assertEqual(provedor.chamadas, 2)


@override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
class QuizComLLMTest(BaseEducMatch):
    """Passo 9: o quiz chama a LLM depois da engine, e nunca quebra por causa dela."""

    def test_quiz_grava_a_entrega(self):
        resposta = self.responder_tudo()

        self.assertEqual(resposta.status_code, 302)
        tentativa = Tentativa_de_resposta.objects.latest("id")
        self.assertEqual(tentativa.llm_model, "fake")
        self.assertTrue(all(rec.llm_text for rec in tentativa.recomendacoes.all()))

    def test_provedor_fora_do_ar_nao_quebra_o_quiz(self):
        with mock.patch(PROVEDOR, return_value=Roteiro(erro=LLMTimeout("8s"))), self.assertLogs("quiz.delivery", "WARNING"):
            resposta = self.responder_tudo()

        self.assertEqual(resposta.status_code, 302)
        tentativa = Tentativa_de_resposta.objects.latest("id")
        self.assertTrue(tentativa.used_fallback)
        self.assertEqual(self.client.get(resposta.url).status_code, 200)
```

> [!tip] 🎓 `assertLogs` faz duas coisas
> Prova que a falha foi **registrada no log**, que é por onde o grupo descobre o motivo de um fallback, e evita que o traceback do caso "bug inesperado" suje a saída dos testes.

---

## 🔑 9️⃣ Ligando de verdade (só depois dos testes verdes)

1. Crie a chave em **Google AI Studio** (aistudio.google.com → *Get API key*). **Confira os limites do plano gratuito no painel do AI Studio**, porque eles mudam.
2. No **seu** `backend/.env`, **nunca** no `.env.example`:

```env
LLM_ENABLED=1
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash-lite
LLM_API_KEY=cole-a-chave-aqui
LLM_TIMEOUT=8
LLM_PROMPT_VERSION=v1
```

> [!warning] Confira o nome do modelo no dia
> `gemini-2.5-flash-lite` é um exemplo. Os nomes mudam e modelos antigos são desativados: copie o nome exato da lista de modelos do AI Studio. Prefira um modelo **Flash-Lite**, que tem a maior cota gratuita e responde rápido.

3. Responda o quiz uma vez e rode:

```bash
python manage.py testar_llm
```

> [!example] Outros provedores, só trocando o `.env`
> | Provedor | `LLM_PROVIDER` | `LLM_BASE_URL` |
> |---|---|---|
> | Gemini | `gemini` | *(vazio)* |
> | Groq | `openai_compat` | `https://api.groq.com/openai/v1` |
> | OpenRouter | `openai_compat` | `https://openrouter.ai/api/v1` |
> | OmniRoute (local) | `openai_compat` | `http://localhost:20128/v1` |
> | Ollama (local) | `openai_compat` | `http://localhost:11434/v1` |

> [!danger] A chave é de **uma** pessoa
> Quem cria a chave guarda no `.env` dela e configura no App Service do Azure (**Configuration → Application settings**). Se uma chave aparecer num commit, ela está queimada: apague-a no AI Studio e gere outra. Antes do push, `git diff --stat` não pode mostrar o `.env`.

---

## ✅ Verificação

```bash
cd backend
python manage.py test quiz.tests.test_llm_openai_compat quiz.tests.test_llm_gravacao   # 15 testes, OK
python manage.py test                                                                 # a suíte + 15
python manage.py makemigrations --check --dry-run                                     # No changes detected
```

À mão, com a chave configurada:

1. `python manage.py testar_llm` → "Saída aprovada pela validação" e os 5 textos.
2. Responda o quiz → a tela de resultado continua igual (o texto aparece no Passo 10), mas no `/admin`, a tentativa tem `llm_model`, `latency_ms` e `tokens_*` preenchidos.
3. Responda **de novo com as mesmas respostas** → a nova tentativa tem **`cache_hit = True`** e `tokens_in` vazio.
4. Troque `LLM_ENABLED=0`, reinicie e responda → nenhum campo `llm_*` preenchido. **Esse é o botão de pânico da defesa.**

## 📦 Commit e PR

```bash
git switch develop && git pull
git switch -c feature/llm-provedor-real
# ... aplica a spec ...
git add backend/quiz backend/core/settings.py backend/core/tests.py backend/.env.example
git status --short        # nada de .env
git commit -m "feat(ia): provedor real, cache, fallback e gravacao (Passo 9)

- quiz/llm/openai_compat.py: Gemini, Groq, OpenRouter e OmniRoute pelo .env
- deliver com cache no banco; entregar grava ou cai na engine, nunca levanta
- o quiz chama entregar depois da engine, fora da transacao
- testar_llm confere a chave com uma chamada real
- CACHES com MAX_ENTRIES=10000 e LLM_BASE_URL no .env.example"
git push -u origin feature/llm-provedor-real
```

> [!success] Definition of Done (o do plano)
> - [ ] 15 testes novos verdes **sem internet**; a CI continua com a LLM desligada
> - [ ] Uma tentativa real volta com texto do Gemini e `latency_ms` gravado
> - [ ] A segunda execução do mesmo perfil sai do cache com **`cache_hit=True`**
> - [ ] Com o Wi-Fi desligado e `LLM_ENABLED=1`, o quiz **continua respondendo** (fallback)
