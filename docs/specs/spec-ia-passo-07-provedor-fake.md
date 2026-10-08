---
title: "Spec IA · Passo 7 — protocolo do provedor, FakeProvider e payload"
aliases: ["Passo 7", "FakeProvider", "Protocolo da LLM", "build_payload"]
tags: [tcc, ia, llm, spec, provedor, testes]
status: proposto
projeto: TCC
branch: feature/llm-fake-provider
criado: 2026-10-08
---

> [!info] Plano da IA: [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 Camada de IA]] · Prompt: [[Projetos/EducMatch(Secretária)/prompt-padrao-recomendacao|📝 Prompt padrão]] · Antes: [[plano-pre-ia-git-flow|🚧 Pré-IA]] ([[spec-pre-ia-03-config-llm|PRE-03]])

# 🔌 Passo 7: protocolo do provedor, `FakeProvider` e payload

**Branch:** `feature/llm-fake-provider`, saindo da `develop` (que primeiro precisa receber a `main`, ver §0)
**Risco:** baixíssimo. **Nenhuma migração**, nenhuma tela muda e nenhuma view chama o código novo.
**Testes ao final:** a suíte de hoje **+ 15**

> [!abstract] O que esta branch faz
> Monta a camada de IA inteira **sem nenhuma chamada de rede**:
> 1. O **contrato do provedor** (`LLMProvider`): todo provedor, falso ou real, tem um método só, `complete(prompt)`.
> 2. O **`FakeProvider`**, um dublê que responde no formato combinado sem internet e sem chave.
> 3. O **`build_payload(tentativa)`**, que monta o JSON de entrada do prompt a partir do que a engine já gravou.
> 4. O **`deliver(tentativa)`**, que junta as peças: confere se a IA está ligada, monta o payload e chama o provedor.
>
> Ele **não grava nada** e **não está ligado à tela**. Isso é o Passo 9. Aqui só se prova que as peças se encaixam.

> [!success] O código desta spec já foi rodado
> Tudo foi aplicado numa **cópia descartável** da `main` em `06baffc`:
> - os 15 testes novos passaram, **sem rede**;
> - a suíte inteira fechou em **165 testes** (150 de antes + 15). O único erro é o do fuso (`FusoDoMySQL`), que depende do MySQL e passa na CI;
> - `makemigrations --check` respondeu **No changes detected**.
>
> O exemplo de payload da §5 foi gerado a partir dos seeds reais.

---

## 🎓 Entenda antes de começar

> [!tip] Por que escrever o dublê antes do provedor de verdade
> Se o grupo travar na chave da API ou no limite do plano gratuito, os Passos 7, 8 e 10 **continuam andando**, porque todos rodam com o `FakeProvider`. Quando a chave chegar, o Passo 9 só **acrescenta um provedor**: nenhum outro arquivo muda.

O caminho que esta branch cria (as setas tracejadas são dos próximos passos):

```
engine.recomendar(tentativa)        ← já existe: grava os 5 cursos com rank_engine
        │
        ▼
delivery.deliver(tentativa)         ← NOVO
   ├─ LLM_ENABLED=0? → devolve None, não chama nada
   ├─ build_payload(tentativa)      ← NOVO: o JSON de entrada do contrato
   ├─ get_provider()                ← NOVO: lê LLM_PROVIDER do .env
   └─ provider.complete(prompt)     ← NOVO: FakeProvider por enquanto
        ┆
        ┆  Passo 8: prompt em arquivo + validação da saída
        ┆  Passo 9: provedor real, cache, timeout, fallback e gravação
```

> [!important] Quatro escolhas que diferem do plano original
> | Plano da IA | Aqui | Por quê |
> |---|---|---|
> | `complete(prompt) -> str` | `complete(prompt) -> LLMResponse` | O Passo 9 precisa gravar `llm_model`, `tokens_in` e `tokens_out`. Uma `str` não carrega esses números, e cada provedor teria de inventar seu jeito de devolvê-los |
> | "Migration dos campos novos" | **nenhuma migração** | Os campos já existem desde a PRE-01 (`quiz/migrations/0004_...metadados_llm.py`) |
> | Payload sem `tie_set` | **com `tie_set`** | A regra 2 do prompt v1 cita o `tie_set`, e ele só passou a existir na PRE-02 |
> | `get_provider()` com `gemini` | só `fake` por enquanto | O provedor real é o Passo 9. Até lá, pedir outro provedor gera `LLMUnavailable`, um erro da camada que o Passo 9 transforma em fallback |

---

## 0️⃣ Antes de criar a branch: atualizar a `develop`

> [!warning] Hoje a `develop` está **7 commits atrás da `main`**
> O deploy no Azure (PR #38) e a responsividade do painel (PR #39) entraram direto na `main`. Se a branch sair da `develop` como ela está, o PR vai trazer conflito com coisas que não têm nada a ver com a IA.

```bash
git switch develop
git pull
git merge origin/main        # só avança, não deve dar conflito
git push
git switch -c feature/llm-fake-provider
```

Confira: `git log --oneline -1 develop` mostra `06baffc` (ou um commit mais novo).

---

## 1️⃣ `backend/quiz/llm/base.py` (arquivo novo)

O contrato. Quem fala com a LLM implementa isto, e quem usa a LLM só conhece isto.

```python
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class LLMError(Exception):
    """Qualquer falha da camada de IA. O Passo 9 transforma isso em fallback."""


class LLMTimeout(LLMError):
    """O provedor passou de LLM_TIMEOUT segundos."""


class LLMUnavailable(LLMError):
    """Sem provedor: nome desconhecido, sem chave, sem crédito ou sem rede."""


@dataclass(frozen=True)
class LLMResponse:
    """O que todo provedor devolve. Os números vão para a Tentativa no Passo 9."""

    text: str
    model: str
    tokens_in: int | None = None
    tokens_out: int | None = None


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def complete(self, prompt: str) -> LLMResponse: ...
```

> [!note] 🎓 Entenda: `Protocol` não é herança
> O `FakeProvider` **não** escreve `class FakeProvider(LLMProvider)`. Basta ter um atributo `name` e um método `complete` com essa assinatura para "ser" um `LLMProvider`. O `@runtime_checkable` permite conferir isso num teste com `isinstance`. Por isso o provedor real do Passo 9 pode morar num arquivo que importa o SDK do Gemini sem que o resto do sistema precise desse SDK instalado.

> [!note] 🎓 Entenda: por que todas as exceções herdam de `LLMError`
> No Passo 9, o fallback vai ser um único `except LLMError:`. Timeout, provedor sem chave ou provedor desconhecido caem todos no mesmo lugar, e o aluno vê o resultado da engine.

## 2️⃣ `backend/quiz/llm/fake.py` (arquivo novo)

```python
import json
import re

from quiz.llm.base import LLMResponse, LLMUnavailable

# Acha os ids em qualquer prompt: no JSON cru do Passo 7 e no .md do Passo 8.
COURSE_ID = re.compile(r'"course_id"\s*:\s*(\d+)')


class FakeProvider:
    """Provedor de teste: nada de rede, e sempre a mesma resposta para o mesmo prompt.

    Entrega os cursos na ordem em que vieram, no formato de saída do contrato.
    """

    name = "fake"

    def complete(self, prompt: str) -> LLMResponse:
        ids = list(dict.fromkeys(int(i) for i in COURSE_ID.findall(prompt)))
        if not ids:
            raise LLMUnavailable("o prompt não tem nenhum course_id")

        principal, *alternativas = ids
        saida = {
            "principal": {"course_id": principal, "texto": f"Texto de teste do curso {principal}."},
            "alternativas": [
                {"course_id": i, "texto": f"Texto de teste do curso {i}."} for i in alternativas
            ],
        }
        return LLMResponse(text=json.dumps(saida, ensure_ascii=False), model="fake")
```

> [!tip] 🎓 Entenda: por que o fake procura `"course_id"` com regex
> No Passo 7, o prompt é o próprio payload em JSON. No Passo 8, ele vira o texto do `entrega_v1.md`, com o JSON no meio do bloco DADOS. A regex acha os ids nos dois casos, então **o fake não muda no Passo 8**. O `dict.fromkeys` tira repetições sem perder a ordem, porque o `.md` pode citar o mesmo id mais de uma vez.

## 3️⃣ `backend/quiz/llm/__init__.py` (arquivo novo)

```python
from django.conf import settings

from quiz.llm.base import LLMError, LLMProvider, LLMResponse, LLMTimeout, LLMUnavailable
from quiz.llm.fake import FakeProvider

__all__ = [
    "FakeProvider", "LLMError", "LLMProvider", "LLMResponse", "LLMTimeout",
    "LLMUnavailable", "get_provider",
]

# O Passo 9 acrescenta o provedor real aqui. Nenhum outro arquivo muda.
PROVIDERS = {
    "fake": FakeProvider,
}


def get_provider() -> LLMProvider:
    """O provedor escolhido em LLM_PROVIDER, no .env."""
    try:
        return PROVIDERS[settings.LLM_PROVIDER]()
    except KeyError:
        raise LLMUnavailable(f"provedor não implementado: {settings.LLM_PROVIDER!r}") from None
```

## 4️⃣ `backend/quiz/delivery.py` (arquivo novo)

```python
"""Camada de IA: monta o que vai para a LLM e chama o provedor.

Passo 7: monta o payload e chama o provedor.
Passo 8: o prompt em arquivo e a validação da saída.
Passo 9: grava rank_final, llm_text e os metadados, com cache e fallback.
"""
import json

from django.conf import settings

from quiz.engine import TOP3, perfil_vetor
from quiz.llm import LLMResponse, get_provider


def build_payload(attempt):
    """O JSON de entrada do contrato. Não leva nome, e-mail nem usuário."""
    respostas = list(
        attempt.respostas.select_related("alternativa").prefetch_related("alternativa__pesos__area")
    )
    perfil = perfil_vetor([resposta.alternativa for resposta in respostas])
    nomes = {}
    for resposta in respostas:
        for peso in resposta.alternativa.pesos.all():
            nomes[peso.area.slug] = peso.area.nome
    fortes = sorted(perfil.items(), key=lambda item: item[1], reverse=True)[:TOP3]

    recomendacoes = attempt.recomendacoes.select_related("curso").order_by("rank_engine")
    return {
        "perfil": {
            "areas_fortes": [
                {"area": slug, "area_name": nomes[slug], "pontuacao": round(valor, 2)}
                for slug, valor in fortes
                if valor > 0
            ]
        },
        "candidatos": [
            {
                "course_id": rec.curso_id,
                "nome": rec.curso.nome_curso,
                "descricao": rec.curso.descricao,
                "score": round(rec.score, 4),
                "rank_engine": rec.rank_engine,
                "top_areas": [
                    {"area_name": area.get("area_name"), "percentual": area.get("percentual")}
                    for area in (rec.explicacao or {}).get("top_areas", [])
                ],
            }
            for rec in recomendacoes
        ],
        # Regra 2 do prompt: só estes ids podem ir para o 1º lugar.
        "tie_set": list(attempt.tie_set),
    }


def deliver(attempt) -> LLMResponse | None:
    """Chama a LLM para esta tentativa. Com a IA desligada, não chama nada."""
    if not settings.LLM_ENABLED:
        return None
    payload = build_payload(attempt)
    if not payload["candidatos"]:
        return None
    # Provisório: o Passo 8 troca pelo prompt em arquivo (quiz/prompts/entrega_v1.md).
    prompt = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return get_provider().complete(prompt)
```

> [!note] 🎓 Entenda: o perfil é recalculado, e não lido do banco
> A `Tentativa` não guarda o vetor do perfil, só as respostas. O `build_payload` usa a **mesma** função da engine (`perfil_vetor`), então o perfil que a LLM recebe é exatamente o que a engine usou. Se alguém mudar o cálculo da engine, o payload acompanha sozinho.

> [!note] 🎓 Entenda: por que `list(...)` nas respostas
> O código percorre as respostas duas vezes: uma para o perfil e outra para os nomes das áreas. Sem o `list`, cada volta faria as consultas de novo no banco.

> [!warning] O payload **nunca** leva dado pessoal
> Nada de `respondido_por`, `user`, e-mail ou link da turma. A LLM recebe só áreas, cursos e números. Há um teste que confere isso (`test_nao_leva_dado_pessoal`). Se alguém acrescentar um campo ao payload, esse teste é a primeira barreira.

---

## 5️⃣ Como ficam a entrada e a saída (gerado a partir dos seeds reais)

Quiz respondido sempre com a 1ª alternativa. As descrições foram cortadas aqui só para caber na nota:

```json
{
  "perfil": {
    "areas_fortes": [
      {"area": "eletrica", "area_name": "Elétrica", "pontuacao": 18.0},
      {"area": "metalurgia", "area_name": "Metalurgia", "pontuacao": 14.0},
      {"area": "eletromecanica", "area_name": "Eletromecânica", "pontuacao": 13.0}
    ]
  },
  "candidatos": [
    {"course_id": 19, "nome": "Operação e Programação de Robô de Soldagem MAG", "descricao": "Programação e operação de robôs de soldagem MAG, incluindo s…",
     "score": 0.8622, "rank_engine": 1,
     "top_areas": [{"area_name": "Metalurgia", "percentual": 37.8}, {"area_name": "Eletromecânica", "percentual": 21.1}, {"area_name": "Elétrica", "percentual": 19.5}]},
    {"course_id": 16, "nome": "Caldeireiro Montador", "score": 0.8514, "rank_engine": 2, "…": "…"},
    {"course_id": 2,  "nome": "Comandos Elétricos e CLP", "score": 0.817, "rank_engine": 3, "…": "…"},
    {"course_id": 11, "nome": "Manutenção Eletromecânica Industrial", "score": 0.81, "rank_engine": 4, "…": "…"},
    {"course_id": 1,  "nome": "Eletricista Instalador", "score": 0.8063, "rank_engine": 5, "…": "…"}
  ],
  "tie_set": [19, 16]
}
```

E a resposta do `FakeProvider` para esse payload:

```json
{
  "principal": {"course_id": 19, "texto": "Texto de teste do curso 19."},
  "alternativas": [
    {"course_id": 16, "texto": "Texto de teste do curso 16."},
    {"course_id": 2,  "texto": "Texto de teste do curso 2."},
    {"course_id": 11, "texto": "Texto de teste do curso 11."},
    {"course_id": 1,  "texto": "Texto de teste do curso 1."}
  ]
}
```

> [!example] Repare no `tie_set: [19, 16]`
> O 1º e o 2º estão a menos de 0,02 de distância (0,8622 contra 0,8514). Pela regra 2, a LLM **pode** colocar o Caldeireiro em 1º lugar. Já o 3º (0,817) não pode. É exatamente esse caso que o Passo 11 vai medir como divergência.

---

## 6️⃣ Testes: `backend/quiz/tests/test_llm_base.py` (arquivo novo)

```python
import json
from unittest import mock

from django.test import SimpleTestCase, override_settings

from quiz.delivery import build_payload, deliver
from quiz.llm import FakeProvider, LLMProvider, LLMResponse, LLMUnavailable, get_provider
from quiz.tests.base import BaseEducMatch


class FakeProviderTest(SimpleTestCase):
    """Passo 7: o dublê respeita o contrato de saída sem tocar a rede."""

    def test_segue_o_protocolo(self):
        self.assertIsInstance(FakeProvider(), LLMProvider)

    def test_entrega_os_ids_na_ordem_recebida(self):
        prompt = json.dumps({"candidatos": [{"course_id": 7}, {"course_id": 3}, {"course_id": 11}]})

        resposta = FakeProvider().complete(prompt)
        saida = json.loads(resposta.text)

        self.assertIsInstance(resposta, LLMResponse)
        self.assertEqual(resposta.model, "fake")
        self.assertEqual(saida["principal"]["course_id"], 7)
        self.assertEqual([a["course_id"] for a in saida["alternativas"]], [3, 11])
        self.assertTrue(all(a["texto"] for a in saida["alternativas"]))

    def test_acha_os_ids_no_meio_de_um_prompt_em_texto(self):
        prompt = '# DADOS\n[{"course_id": 2}, {"course_id":5}]\n# REGRAS\n... "course_id": 2 ...'

        saida = json.loads(FakeProvider().complete(prompt).text)

        self.assertEqual(saida["principal"]["course_id"], 2)
        self.assertEqual([a["course_id"] for a in saida["alternativas"]], [5])

    def test_prompt_sem_curso_e_erro_da_camada(self):
        with self.assertRaises(LLMUnavailable):
            FakeProvider().complete("sem candidatos")


class GetProviderTest(SimpleTestCase):
    @override_settings(LLM_PROVIDER="fake")
    def test_fake(self):
        self.assertIsInstance(get_provider(), FakeProvider)

    @override_settings(LLM_PROVIDER="gemini")
    def test_provedor_ainda_nao_implementado_e_erro_da_camada(self):
        with self.assertRaises(LLMUnavailable):
            get_provider()


class BuildPayloadTest(BaseEducMatch):
    """Passo 7: o JSON de entrada do contrato."""

    def test_candidatos_seguem_a_ordem_da_engine(self):
        tentativa = self.criar_tentativa()
        payload = build_payload(tentativa)

        esperados = list(
            tentativa.recomendacoes.order_by("rank_engine").values_list("curso_id", flat=True)
        )
        self.assertEqual([c["course_id"] for c in payload["candidatos"]], esperados)
        self.assertEqual([c["rank_engine"] for c in payload["candidatos"]], [1, 2, 3, 4, 5])

    def test_cada_candidato_tem_os_campos_do_contrato(self):
        candidato = build_payload(self.criar_tentativa())["candidatos"][0]

        self.assertEqual(
            set(candidato),
            {"course_id", "nome", "descricao", "score", "rank_engine", "top_areas"},
        )
        self.assertTrue(candidato["top_areas"])
        self.assertEqual(set(candidato["top_areas"][0]), {"area_name", "percentual"})

    def test_perfil_traz_ate_tres_areas_da_mais_forte_para_a_mais_fraca(self):
        areas = build_payload(self.criar_tentativa())["perfil"]["areas_fortes"]

        self.assertTrue(1 <= len(areas) <= 3)
        pontuacoes = [a["pontuacao"] for a in areas]
        self.assertEqual(pontuacoes, sorted(pontuacoes, reverse=True))
        self.assertTrue(all(a["area_name"] for a in areas))

    def test_tie_set_vai_junto_e_so_tem_candidatos(self):
        payload = build_payload(self.criar_tentativa())

        ids = {c["course_id"] for c in payload["candidatos"]}
        self.assertTrue(payload["tie_set"])
        self.assertLessEqual(set(payload["tie_set"]), ids)

    def test_nao_leva_dado_pessoal(self):
        dono = self.criar_usuario(email="maria.souza@exemplo.com", first_name="Maria")
        tentativa = self.criar_tentativa(dono=dono)
        tentativa.respondido_por = "Maria Souza"
        tentativa.save(update_fields=["respondido_por"])

        texto = json.dumps(build_payload(tentativa), ensure_ascii=False)

        self.assertNotIn("Maria", texto)
        self.assertNotIn("maria.souza", texto)


class DeliverTest(BaseEducMatch):
    @override_settings(LLM_ENABLED=False)
    def test_desligada_nao_chama_nenhum_provedor(self):
        tentativa = self.criar_tentativa()
        with mock.patch("quiz.delivery.get_provider") as provedor:
            self.assertIsNone(deliver(tentativa))
        provedor.assert_not_called()

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake")
    def test_ligada_com_fake_devolve_os_cinco_candidatos(self):
        tentativa = self.criar_tentativa()

        saida = json.loads(deliver(tentativa).text)

        entregues = [saida["principal"]["course_id"]] + [a["course_id"] for a in saida["alternativas"]]
        esperados = list(
            tentativa.recomendacoes.order_by("rank_engine").values_list("curso_id", flat=True)
        )
        self.assertEqual(entregues, esperados)

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake")
    def test_nao_muda_nada_no_banco(self):
        tentativa = self.criar_tentativa()
        antes = list(tentativa.recomendacoes.values_list("curso_id", "rank_final", "llm_text"))

        deliver(tentativa)

        depois = list(tentativa.recomendacoes.values_list("curso_id", "rank_final", "llm_text"))
        self.assertEqual(antes, depois)

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake")
    def test_tentativa_sem_recomendacao_nao_chama_o_provedor(self):
        from quiz.models import Tentativa_de_resposta

        vazia = Tentativa_de_resposta.objects.create(respondido_por="")
        with mock.patch("quiz.delivery.get_provider") as provedor:
            self.assertIsNone(deliver(vazia))
        provedor.assert_not_called()
```

> [!tip] 🎓 Entenda: `SimpleTestCase` e `BaseEducMatch`
> Os testes do `FakeProvider` e do `get_provider` não usam banco, então ficam em `SimpleTestCase`, que é mais rápido e **reprova** se alguém tentar consultar o banco ali. Os do payload precisam do catálogo real e usam a `BaseEducMatch`, que roda os seeds uma vez por classe.

> [!tip] 🎓 Entenda: `mock.patch` no `get_provider`
> Para provar que a IA desligada **não chama nada**, o teste troca o `get_provider` por um espião e confere que ele nunca foi chamado. Só olhar o retorno `None` não bastaria: a função poderia chamar o provedor e descartar a resposta.

---

## ✅ Verificação

```bash
cd backend
python manage.py test quiz.tests.test_llm_base     # 15 testes, OK
python manage.py test                               # a suíte inteira + 15
python manage.py makemigrations --check --dry-run   # No changes detected
```

> [!success] O teste do modo avião (Definition of Done do plano)
> Desligue o Wi-Fi e rode `python manage.py test quiz.tests.test_llm_base` de novo. Tem de passar igual: nada neste passo depende de rede.

E à mão, no `shell`, para **ver** a entrada e a saída:

```bash
python manage.py shell
```

```python
import json
from django.test.utils import override_settings
from quiz.models import Tentativa_de_resposta
from quiz.delivery import build_payload, deliver

t = Tentativa_de_resposta.objects.latest("id")         # responda um quiz antes, se não houver nenhuma
print(json.dumps(build_payload(t), ensure_ascii=False, indent=2))
with override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake"):
    print(deliver(t).text)
```

## 📦 Commit e PR

```bash
git add backend/quiz/llm backend/quiz/delivery.py backend/quiz/tests/test_llm_base.py
git status --short        # só esses 5 arquivos, nada de .env
git commit -m "feat(ia): protocolo do provedor, FakeProvider e payload (Passo 7)

- quiz/llm: LLMProvider, LLMResponse, erros da camada e get_provider()
- FakeProvider responde no contrato de saida, sem rede
- delivery: build_payload no contrato de entrada e deliver()
- nada ligado a tela ainda: o Passo 9 grava e faz o fallback"
git push -u origin feature/llm-fake-provider
gh pr create --base develop --fill
```

> [!success] Definition of Done
> - [ ] `develop` atualizada com a `main` **antes** de criar a branch (§0)
> - [ ] 15 testes novos verdes, **com a máquina sem internet**
> - [ ] Suíte inteira verde na CI
> - [ ] `makemigrations --check` sem mudanças
> - [ ] Nenhuma view, template ou `settings.py` alterado: o aluno não vê diferença nenhuma
> - [ ] PR para a `develop`, revisado por alguém que não escreveu o código

---

## ➡️ Próximos passos

| Passo | O que entra | Onde encaixa no código deste passo |
|---|---|---|
| **8** | `quiz/prompts/entrega_v1.md` + validação da saída | Troca a linha "Provisório" do `deliver` pelo carregador do prompt. A validação recebe o `LLMResponse.text` |
| **9** | Provedor real + cache + timeout + fallback + gravação | Um arquivo novo em `quiz/llm/` e **uma linha** no `PROVIDERS` |
| **10** | Tela de entrega (principal + 4 alternativas) | Lê `rank_final` e `llm_text`, gravados no 9 |

> [!tip] Sugestão para o Passo 9: um provedor "compatível com OpenAI"
> Em vez de um `GeminiProvider` preso ao SDK do Google, vale um `OpenAICompatProvider` com uma variável `LLM_BASE_URL`. Gemini, Groq, OpenRouter e OmniRoute aceitam o mesmo formato (`/chat/completions`), então trocar de provedor vira trocar 3 linhas do `.env`. Pelo protocolo deste passo, isso é **um arquivo** em `quiz/llm/` e uma linha no `PROVIDERS`. Na defesa, Gemini Flash-Lite direto; OmniRoute e OpenRouter só para comparar modelos no desenvolvimento.
