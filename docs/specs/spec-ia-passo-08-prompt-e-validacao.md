---
title: "Spec IA · Passo 8 — prompt padrão v1 em arquivo e validação da saída"
aliases: ["Passo 8", "Prompt v1", "DeliverySerializer", "Validação da saída da LLM"]
tags: [tcc, ia, llm, spec, prompt, validacao]
status: proposto
projeto: TCC
branch: feature/llm-prompt-v1
criado: 2026-10-08
---

> [!info] Plano da IA: [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 Camada de IA]] · Prompt: [[Projetos/EducMatch(Secretária)/prompt-padrao-recomendacao|📝 Prompt padrão]] · Anterior: [[spec-ia-passo-07-provedor-fake|🔌 Passo 7]] · Próximo: [[spec-ia-passo-09-provedor-real|🌐 Passo 9]]

# 📝 Passo 8: prompt padrão v1 em arquivo e validação da saída

**Branch:** `feature/llm-prompt-v1`, saindo da `develop` **com o PR #40 (Passo 7) já mesclado**
**Risco:** baixo. Nenhuma migração, nenhuma tela muda e nada é gravado no banco.
**Testes ao final:** a suíte do Passo 7 **+ 11** (na cópia: 176)

> [!abstract] O que esta branch faz
> Congela o prompt que o grupo vai usar com **todos** os perfis e garante que nada do que a LLM devolver passe sem revista:
> 1. O prompt vira **arquivo** (`quiz/prompts/entrega_v1.md`), com os dados injetados por um carregador.
> 2. A saída passa por um **serializer do DRF** com as regras do contrato: só os ids enviados, os 5 e sem repetir, texto não vazio e dentro do limite, principal dentro do `tie_set`.
> 3. O `deliver()` passa a usar os dois: devolve uma `Entrega` **aprovada** ou levanta `LLMInvalidOutput`.
>
> Continua sem rede e sem gravar nada. Transformar o erro em fallback é o Passo 9.

> [!success] O código desta spec já foi rodado
> Aplicado numa cópia descartável do PR #40 (`81ce3d0`): os **11 testes novos** e os 15 do Passo 7 passaram, sem rede. A suíte inteira fechou em **176 testes**; o único erro é o do fuso (`FusoDoMySQL`), que depende do MySQL e passa na CI. `makemigrations --check`: **No changes detected**.

---

## 🎓 Entenda antes de começar

> [!tip] Por que o prompt é arquivo, e não string no código
> 1. Entra como **anexo da monografia** do jeito que está.
> 2. O `git diff` entre `entrega_v1.md` e uma futura `entrega_v2.md` mostra a **evolução do prompt**, que é material para a metodologia.
> 3. Trocar o texto não exige mexer em Python.

> [!important] O servidor revalida tudo o que o prompt pede
> O prompt **pede** à LLM que respeite as regras, e o serializer **confere** se ela respeitou. É o "cinto e suspensório": o prompt reduz os erros, a validação impede que um erro chegue ao aluno.

> [!important] Duas escolhas que diferem do plano original
> | Plano / nota do prompt | Aqui | Por quê |
> |---|---|---|
> | Dois placeholders: `{{PERFIL_JSON}}` e `{{CANDIDATOS_JSON}}` | **Três**: mais `{{TIE_SET_JSON}}` | A regra 2 do prompt fala do `tie_set`, mas a nota não o colocava nos DADOS. Sem ele, a LLM não tem como cumprir a regra |
> | "Parser tolera cerca de código **ou** cai no fallback" | **Tolera** | Pega do primeiro `{` ao último `}`. Muitos modelos embrulham o JSON em ` ```json `, e recusar isso jogaria fora uma resposta boa |

---

## 1️⃣ `backend/quiz/prompts/entrega_v1.md` (arquivo novo)

O texto é o da nota [[Projetos/EducMatch(Secretária)/prompt-padrao-recomendacao|📝 Prompt padrão]], com **uma** seção a mais nos DADOS (o `tie_set`):

````markdown
# PAPEL

Você é um orientador de carreira de uma escola técnica profissionalizante.
Você está falando diretamente com um estudante que acabou de responder a um
quiz de perfil. Um sistema já analisou as respostas dele e selecionou os 5
cursos mais compatíveis. Seu trabalho é **entregar essa recomendação** em
linguagem humana: apresentar o curso principal e mencionar as alternativas.

Você não é o sistema que escolheu os cursos. Você é quem explica a escolha.

# DADOS

## Perfil do estudante
{{PERFIL_JSON}}

## Cursos candidatos (em ordem de compatibilidade calculada)
{{CANDIDATOS_JSON}}

## tie_set (os únicos `course_id` que podem ser o curso principal)
{{TIE_SET_JSON}}

# REGRAS

1. Escolha o curso principal **apenas** entre os `course_id` da lista de
   candidatos. Nunca cite, sugira ou invente um curso que não esteja ali.
2. **Por padrão, respeite a ordem recebida**: Só coloque em 1º lugar um curso cujo `course_id` esteja em `tie_set`. Se `tie_set` tiver um único id, o 1º lugar não muda.
3. Os 5 candidatos precisam aparecer na resposta: 1 como principal e 4 como
   alternativas. Não repita nenhum e não omita nenhum.
4. Só afirme sobre um curso o que estiver no campo `descricao`. **Não** fale de
   duração, preço, unidade, mercado de trabalho, salário, empregabilidade ou
   qualquer promessa de resultado.
5. Escreva em português do Brasil, na segunda pessoa ("você"), com tom acolhedor
   e direto. Nada de jargão do sistema: não use as palavras *score*, *cosseno*,
   *vetor*, *algoritmo*, *ranking*, *pontuação* nem *inteligência artificial*.
6. Ao justificar, cite as áreas do perfil pelo `area_name` (ex.: "Elétrica",
   "Mecânica") e conecte-as ao que o curso faz.
7. Tamanhos: o texto do principal tem de 3 a 5 frases (máximo 600 caracteres);
   o de cada alternativa tem de 1 a 2 frases (máximo 220 caracteres).
8. Não comece duas alternativas com a mesma palavra ou com a mesma fórmula.
9. Não faça perguntas ao estudante, não peça mais informações e não sugira que
   ele refaça o quiz.
10. Responda **somente** com o JSON do formato abaixo: sem cercas de código,
    sem comentários, sem texto antes ou depois.
11. Se por qualquer motivo você não conseguir cumprir as regras acima, devolva
    o JSON mantendo exatamente a ordem recebida em `rank_engine`.

# FORMATO DE SAÍDA

{
  "principal": {
    "course_id": <int>,
    "texto": "<3 a 5 frases>"
  },
  "alternativas": [
    {"course_id": <int>, "texto": "<1 a 2 frases>"},
    {"course_id": <int>, "texto": "<1 a 2 frases>"},
    {"course_id": <int>, "texto": "<1 a 2 frases>"},
    {"course_id": <int>, "texto": "<1 a 2 frases>"}
  ]
}
````

> [!warning] A v1 congela no primeiro uso real
> Assim que o Passo 9 rodar com um modelo de verdade, **não edite mais este arquivo**: os registros gravados apontam para ele por `prompt_version`. Mudou o texto? Crie `entrega_v2.md` e troque `LLM_PROMPT_VERSION=v2` no `.env`.

> [!note] 🎓 O `FakeProvider` continua funcionando sem mudança
> Ele procura `"course_id": <número>` no prompt. No `.md`, os números só aparecem dentro do bloco de candidatos, na ordem da engine; nas REGRAS e no FORMATO, `course_id` aparece sem número. Foi por isso que o Passo 7 usou regex.

## 2️⃣ `backend/quiz/prompt.py` (arquivo novo): o carregador

```python
"""O prompt padrão da camada de IA: um arquivo .md por versão, nunca string no código.

A versão vem de LLM_PROMPT_VERSION e é gravada em cada tentativa (Passo 9).
Uma versão já usada não se edita: muda o texto, nasce entrega_v2.md.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

from quiz.llm import LLMUnavailable

PASTA = Path(__file__).resolve().parent / "prompts"


@lru_cache
def carregar(versao):
    if not re.fullmatch(r"[\w.-]+", versao):
        raise LLMUnavailable(f"versão de prompt inválida: {versao!r}")
    try:
        return (PASTA / f"entrega_{versao}.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        raise LLMUnavailable(f"não existe prompt para a versão {versao!r}") from None


def _json(valor):
    return json.dumps(valor, ensure_ascii=False, indent=2)


def montar_prompt(payload, versao):
    """O texto da versão pedida, com os dados desta tentativa no bloco DADOS."""
    return (
        carregar(versao)
        .replace("{{PERFIL_JSON}}", _json(payload["perfil"]))
        .replace("{{CANDIDATOS_JSON}}", _json(payload["candidatos"]))
        .replace("{{TIE_SET_JSON}}", _json(payload["tie_set"]))
    )
```

> [!note] 🎓 Por que `.replace` e não `.format` ou f-string
> O prompt tem chaves `{ }` no bloco FORMATO e o JSON injetado também tem. O `.format` tentaria interpretar todas elas e quebraria. O `.replace` troca só o texto exato `{{PERFIL_JSON}}`.

> [!note] 🎓 `lru_cache` e a checagem da versão
> - `@lru_cache` lê o arquivo do disco **uma vez** por versão e guarda na memória.
> - A regex `[\w.-]+` impede que uma versão como `../settings` leia outro arquivo do servidor. A versão vem do `.env`, mas a checagem custa uma linha.

> [!tip] Nome do arquivo: `prompt.py`, no singular
> A pasta é `prompts/` e o módulo é `prompt.py`. Se os dois tivessem o mesmo nome, o `import` ficaria ambíguo.

## 3️⃣ `backend/quiz/llm/base.py`: uma exceção nova

Logo depois de `LLMUnavailable`:

```python
class LLMInvalidOutput(LLMError):
    """A resposta chegou, mas quebra o contrato de saída (Passo 8)."""
```

E em `backend/quiz/llm/__init__.py`, exporte a exceção:

```python
from quiz.llm.base import (
    LLMError, LLMInvalidOutput, LLMProvider, LLMResponse, LLMTimeout, LLMUnavailable,
)
from quiz.llm.fake import FakeProvider

__all__ = [
    "FakeProvider", "LLMError", "LLMInvalidOutput", "LLMProvider", "LLMResponse", "LLMTimeout",
    "LLMUnavailable", "get_provider",
]
```

## 4️⃣ `backend/quiz/serializers.py` (arquivo novo): a revista da saída

```python
"""Revista da saída da LLM: nada entra no banco sem passar por aqui."""
import json
from dataclasses import dataclass

from rest_framework import serializers

from quiz.llm import LLMInvalidOutput

LIMITE_PRINCIPAL = 600   # regra 7 do prompt
LIMITE_ALTERNATIVA = 220


class PrincipalSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    texto = serializers.CharField(max_length=LIMITE_PRINCIPAL)  # já recusa vazio


class AlternativaSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    texto = serializers.CharField(max_length=LIMITE_ALTERNATIVA)


class DeliverySerializer(serializers.Serializer):
    """As regras do contrato de saída. Precisa de `candidatos` e `tie_set` no context."""

    principal = PrincipalSerializer()
    alternativas = AlternativaSerializer(many=True)

    def validate(self, dados):
        ids = [dados["principal"]["course_id"]] + [a["course_id"] for a in dados["alternativas"]]
        candidatos = self.context["candidatos"]

        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("curso repetido")
        if set(ids) - set(candidatos):
            raise serializers.ValidationError("curso fora da lista de candidatos")
        if set(candidatos) - set(ids):
            raise serializers.ValidationError("faltou curso: a LLM não pode descartar candidato")
        if ids[0] not in self.context["tie_set"]:
            raise serializers.ValidationError("regra 2: o principal não está no tie_set")
        return dados


@dataclass(frozen=True)
class Entrega:
    """A saída aprovada: a ordem final (o principal primeiro) e o texto de cada curso."""

    ordem: list[int]
    textos: dict[int, str]


def ler_json(texto):
    """Tolera cerca de código e texto em volta: pega do primeiro { ao último }."""
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim < inicio:
        raise LLMInvalidOutput("a resposta não tem JSON")
    try:
        return json.loads(texto[inicio:fim + 1])
    except ValueError as erro:
        raise LLMInvalidOutput(f"JSON quebrado: {erro}") from None


def validate_delivery(texto, payload):
    """Entrega aprovada, ou LLMInvalidOutput com o motivo."""
    serializer = DeliverySerializer(
        data=ler_json(texto),
        context={
            "candidatos": [c["course_id"] for c in payload["candidatos"]],
            "tie_set": payload["tie_set"],
        },
    )
    if not serializer.is_valid():
        raise LLMInvalidOutput(f"saída recusada: {serializer.errors}")

    dados = serializer.validated_data
    itens = [dados["principal"], *dados["alternativas"]]
    return Entrega(
        ordem=[item["course_id"] for item in itens],
        textos={item["course_id"]: item["texto"] for item in itens},
    )
```

| Regra do contrato | Quem confere |
|---|---|
| `texto` não vazio | `CharField` (por padrão recusa em branco e apara os espaços) |
| Principal até 600 caracteres, alternativa até 220 | `max_length` |
| `course_id` é número | `IntegerField` |
| Nenhum id repetido | `validate()` |
| Nenhum id fora da lista (alucinação) | `validate()` |
| Nenhum candidato sumiu | `validate()` |
| **Principal dentro do `tie_set`** (regra 2) | `validate()` |

> [!note] 🎓 Por que um serializer do DRF
> O `djangorestframework` já está instalado. O serializer dá, de graça, os tipos, os limites, a recusa de texto vazio e a mensagem de erro de cada campo, e o `validate()` cuida das regras que envolvem mais de um campo. Os `PrincipalSerializer` e `AlternativaSerializer` existem separados porque os limites de tamanho são diferentes.

## 5️⃣ `backend/quiz/delivery.py`: o `deliver` passa a usar prompt e validação

Troque os imports do topo:

```python
from django.conf import settings

from quiz.engine import TOP3, perfil_vetor
from quiz.llm import get_provider
from quiz.prompt import montar_prompt
from quiz.serializers import Entrega, validate_delivery
```

E substitua o `deliver` inteiro (o `build_payload` não muda):

```python
def deliver(attempt) -> Entrega | None:
    """A entrega da LLM, já revisada. Com a IA desligada, não chama nada.

    Saída fora do contrato vira LLMInvalidOutput: nada inválido sai daqui.
    """
    if not settings.LLM_ENABLED:
        return None
    payload = build_payload(attempt)
    if not payload["candidatos"]:
        return None
    prompt = montar_prompt(payload, settings.LLM_PROMPT_VERSION)
    resposta = get_provider().complete(prompt)
    return validate_delivery(resposta.text, payload)
```

O `import json` do topo sai: o `deliver` não monta mais o prompt com `json.dumps`.

---

## 6️⃣ Testes

### Ajuste em `backend/quiz/tests/test_llm_base.py`

O `deliver` agora devolve uma `Entrega`, e não o texto cru. No `test_ligada_com_fake_devolve_os_cinco_candidatos`, troque:

```python
        saida = json.loads(deliver(tentativa).text)

        entregues = [saida["principal"]["course_id"]] + [a["course_id"] for a in saida["alternativas"]]
```

por:

```python
        entrega = deliver(tentativa)

        entregues = entrega.ordem
```

### `backend/quiz/tests/test_llm_entrega_v1.py` (arquivo novo)

```python
import json
from unittest import mock

from django.test import SimpleTestCase, override_settings

from quiz.delivery import build_payload, deliver
from quiz.llm import LLMInvalidOutput, LLMResponse, LLMUnavailable
from quiz.prompt import carregar, montar_prompt
from quiz.serializers import LIMITE_ALTERNATIVA, LIMITE_PRINCIPAL, validate_delivery
from quiz.tests.base import BaseEducMatch

# Um payload pequeno, à mão: os testes de validação não precisam de banco.
PAYLOAD = {
    "perfil": {"areas_fortes": [{"area": "eletrica", "area_name": "Elétrica", "pontuacao": 18.0}]},
    "candidatos": [
        {"course_id": i, "nome": f"Curso {i}", "descricao": "…", "score": 0.9, "rank_engine": r, "top_areas": []}
        for r, i in enumerate([19, 16, 2, 11, 1], start=1)
    ],
    "tie_set": [19, 16],
}


def saida(principal=19, alternativas=(16, 2, 11, 1), texto="Um texto curto.", texto_principal=None):
    return json.dumps({
        "principal": {"course_id": principal, "texto": texto_principal or texto},
        "alternativas": [{"course_id": i, "texto": texto} for i in alternativas],
    })


class PromptV1Test(SimpleTestCase):
    """Passo 8: o prompt é arquivo, com os quatro blocos e os dados no lugar."""

    def test_arquivo_tem_os_quatro_blocos(self):
        texto = carregar("v1")
        for bloco in ("# PAPEL", "# DADOS", "# REGRAS", "# FORMATO DE SAÍDA"):
            with self.subTest(bloco=bloco):
                self.assertIn(bloco, texto)

    def test_montar_preenche_todos_os_placeholders(self):
        prompt = montar_prompt(PAYLOAD, "v1")

        self.assertNotIn("{{", prompt)
        self.assertIn('"course_id": 19', prompt)
        self.assertIn('"area_name": "Elétrica"', prompt)
        self.assertIn("[\n  19,\n  16\n]", prompt)  # o tie_set, no bloco DADOS

    def test_versao_que_nao_existe_e_erro_da_camada(self):
        with self.assertRaises(LLMUnavailable):
            montar_prompt(PAYLOAD, "v99")

    def test_versao_com_caminho_e_recusada(self):
        with self.assertRaises(LLMUnavailable):
            carregar("../settings")


class ValidacaoDaSaidaTest(SimpleTestCase):
    """Passo 8: as regras do contrato de saída, uma por teste."""

    def test_saida_valida_vira_entrega(self):
        entrega = validate_delivery(saida(), PAYLOAD)

        self.assertEqual(entrega.ordem, [19, 16, 2, 11, 1])
        self.assertEqual(entrega.textos[19], "Um texto curto.")

    def test_principal_trocado_dentro_do_tie_set_e_aceito(self):
        entrega = validate_delivery(saida(principal=16, alternativas=(19, 2, 11, 1)), PAYLOAD)
        self.assertEqual(entrega.ordem[0], 16)

    def test_cerca_de_codigo_e_tolerada(self):
        entrega = validate_delivery("```json\n" + saida() + "\n```", PAYLOAD)
        self.assertEqual(entrega.ordem[0], 19)

    def test_recusas(self):
        casos = {
            "JSON quebrado": '{"principal": {"course_id": 19,',
            "sem JSON": "Desculpe, não consigo ajudar.",
            "objeto sem os campos do contrato": '{"ordem": [19, 16, 2, 11, 1]}',
            "curso inventado": saida(alternativas=(16, 2, 11, 999)),
            "curso repetido": saida(alternativas=(16, 2, 11, 16)),
            "só 3 alternativas": saida(alternativas=(16, 2, 11)),
            "texto vazio": saida(texto="   "),
            "principal fora do tie_set": saida(principal=2, alternativas=(19, 16, 11, 1)),
            "principal longo demais": saida(texto_principal="x" * (LIMITE_PRINCIPAL + 1)),
            "alternativa longa demais": saida(texto="x" * (LIMITE_ALTERNATIVA + 1)),
            "id que não é número": saida().replace('"course_id": 19', '"course_id": "dezenove"'),
        }
        for nome, texto in casos.items():
            with self.subTest(nome):
                with self.assertRaises(LLMInvalidOutput):
                    validate_delivery(texto, PAYLOAD)


class LixoProposital:
    """Provedor que devolve uma resposta fora do contrato."""

    name = "lixo"

    def complete(self, prompt):
        return LLMResponse(text='{"principal": {"course_id": 999, "texto": "curso inventado"}}', model="lixo")


@override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
class DeliverComPromptTest(BaseEducMatch):
    def test_fake_atravessa_o_prompt_v1_e_a_validacao(self):
        tentativa = self.criar_tentativa()

        entrega = deliver(tentativa)

        esperados = [c["course_id"] for c in build_payload(tentativa)["candidatos"]]
        self.assertEqual(entrega.ordem, esperados)
        self.assertTrue(all(entrega.textos.values()))

    def test_lixo_do_provedor_vira_erro_e_nao_grava_nada(self):
        tentativa = self.criar_tentativa()
        antes = list(tentativa.recomendacoes.values_list("curso_id", "rank_final", "llm_text"))

        with mock.patch("quiz.delivery.get_provider", return_value=LixoProposital()):
            with self.assertRaises(LLMInvalidOutput):
                deliver(tentativa)

        depois = list(tentativa.recomendacoes.values_list("curso_id", "rank_final", "llm_text"))
        self.assertEqual(antes, depois)

    def test_prompt_enviado_nao_leva_dado_pessoal(self):
        tentativa = self.criar_tentativa()
        tentativa.respondido_por = "Maria Souza"
        tentativa.save(update_fields=["respondido_por"])
        enviado = {}

        class Espiao(LixoProposital):
            def complete(self, prompt):
                enviado["prompt"] = prompt
                return super().complete(prompt)

        with mock.patch("quiz.delivery.get_provider", return_value=Espiao()):
            with self.assertRaises(LLMInvalidOutput):
                deliver(tentativa)

        self.assertIn("# REGRAS", enviado["prompt"])
        self.assertNotIn("Maria", enviado["prompt"])
```

> [!tip] 🎓 Os casos de "saída maliciosa" do plano estão todos no `test_recusas`
> Id inexistente, id repetido, só 3 cursos, JSON quebrado e texto vazio, mais os limites de tamanho e a regra 2. Cada caso é um `subTest`: se um falhar, a mensagem diz **qual**.

---

## ✅ Verificação

```bash
cd backend
python manage.py test quiz.tests.test_llm_base quiz.tests.test_llm_entrega_v1   # 26 testes, OK
python manage.py test                                                           # a suíte + 11
python manage.py makemigrations --check --dry-run                               # No changes detected
```

E à mão, no `shell`, para **ler** o prompt que a LLM vai receber:

```python
from quiz.models import Tentativa_de_resposta
from quiz.delivery import build_payload
from quiz.prompt import montar_prompt

print(montar_prompt(build_payload(Tentativa_de_resposta.objects.latest("id")), "v1"))
```

## 📦 Commit e PR

```bash
git switch develop && git pull
git switch -c feature/llm-prompt-v1
# ... aplica a spec ...
git add backend/quiz/prompts backend/quiz/prompt.py backend/quiz/serializers.py backend/quiz/llm backend/quiz/delivery.py backend/quiz/tests/test_llm_base.py backend/quiz/tests/test_llm_entrega_v1.py
git status --short
git commit -m "feat(ia): prompt padrao v1 em arquivo e validacao da saida (Passo 8)

- quiz/prompts/entrega_v1.md: o prompt da nota, com o tie_set nos DADOS
- quiz/prompt.py: carregador com placeholders e versao do .env
- quiz/serializers.py: DeliverySerializer com as regras do contrato
- deliver devolve Entrega aprovada ou LLMInvalidOutput"
git push -u origin feature/llm-prompt-v1
```

Depois, abra o PR para a `develop` no GitHub.

> [!success] Definition of Done
> - [ ] 11 testes novos verdes, **sem internet**
> - [ ] Um provedor que devolve lixo **não grava nada**: `test_lixo_do_provedor_vira_erro_e_nao_grava_nada`
> - [ ] O prompt montado foi lido por alguém do grupo pelo menos uma vez (comando do `shell` acima)
> - [ ] CI verde e PR revisado por quem não escreveu
