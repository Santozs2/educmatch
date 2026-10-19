---
title: "Spec · Testes sem rede — a suíte nunca chama a LLM de verdade"
aliases: ["Testes sem rede", "Runner sem rede", "Testes chamando o Gemini", "U4"]
tags: [tcc, spec, testes, ia, llm, ci]
status: proposto
projeto: TCC
branch: fix/testes-sem-rede
criado: 2026-10-19
---

> [!info] Relacionadas: [[spec-urgente-producao-v0.3.1|🚨 Spec urgente da produção (v0.3.1)]] · [[../apresentacao/ia|🤖 Camada de IA]] · Precedente: o teste `test_provedor_ainda_nao_implementado_e_erro_da_camada`, que também dependia do `.env` (corrigido no PR #51)

# 🔌 Spec: testes sem rede

> [!abstract] O problema em uma frase
> Com a LLM ligada no `.env` (como precisa estar para desenvolver a camada de IA), **`python manage.py test` faz 111 chamadas reais ao Gemini** a cada rodada. Isso gasta a cota grátis, deixa a suíte 11 vezes mais lenta e faz o resultado depender da internet.

> [!success] Medido em 19/10/2026
> Os números abaixo vêm da suíte rodando com a IA apontada para um endereço local inexistente (`http://127.0.0.1:9`). Assim, toda chamada falha na hora, sem gastar cota, e deixa uma linha `LLM no fallback` no log, que foi contada.

---

## 🔍 1. O diagnóstico

### Os sintomas

| Com o `.env` de desenvolvimento (`LLM_ENABLED=1`, `LLM_PROVIDER=gemini`) | Valor |
|---|:-:|
| Tempo da suíte | **336 s** (com a IA desligada: **29 s**) |
| Chamadas à LLM por rodada | **111** |
| Rodadas até esgotar a cota diária (500) | **~4,5** |
| Limite por minuto (15) | Estourado em segundos: a maior parte das chamadas leva **429** e cai no fallback |

Na **CI** isso não acontece, porque lá não existe `.env` e a LLM fica com o padrão `LLM_ENABLED=0`. Por isso o problema passou despercebido: **a CI está verde, e é a máquina de quem desenvolve que paga a conta.**

### De onde vêm as 111 chamadas

| Chamadas | Módulo de teste | Por que chama |
|:-:|---|---|
| 54 | `painel.tests.test_telas` | Monta cenários respondendo o quiz pelo formulário (`responder_tudo`) |
| 20 | `painel.tests.test_privacidade` | Idem |
| 11 | `accounts.tests.test_c4_interesse` | Responde o quiz para depois salvar interesse |
| 6 | `quiz.tests.test_curso_so_com_resultado` | Idem |
| 5 | `quiz.tests.test_telas` | Idem |
| 3 | `quiz.tests.test_paginas` · `test_motor` · `test_inicio` | Idem (3 cada) |
| 3 | `accounts.tests.test_c6_claim` | Responde anônimo e depois entra na conta |
| 2 | `painel.tests.test_metricas` | Idem |
| 1 | `quiz.tests.test_rank_final` | Idem |
| **111** | **11 módulos** | **Nenhum deles é teste da camada de IA** |

> [!important] A causa
> Os **testes da IA estão certos**: ligam a LLM de propósito com `@override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake")` e simulam a rede com `mock.patch` no `urlopen`. O problema está nos **outros**: eles **herdam o `.env` de quem roda**. Um teste do painel que só quer "uma tentativa respondida" passa a chamar o Gemini porque, nesta máquina, a LLM está ligada.
>
> É a mesma classe de defeito do teste que dependia do `LLM_MODEL` (PR #51): **o resultado do teste dependia da configuração da máquina, e não só do código.**

### Por que não corrigir nos 11 arquivos

Colocar `@override_settings(LLM_ENABLED=False)` em cada classe resolve hoje, mas **o 12º arquivo vai esquecer**. A garantia precisa estar num lugar só, valendo para qualquer teste, inclusive os que ainda não existem.

---

## 🛠️ 2. A solução: duas travas no *test runner*

O Django permite trocar o executor dos testes (`TEST_RUNNER`). O nosso executor faz duas coisas **antes do primeiro teste**:

| Trava | O que faz | Protege contra |
|---|---|---|
| **1 · LLM desligada por padrão** | Força `LLM_ENABLED=False`, `LLM_PROVIDER="fake"` e zera `LLM_BASE_URL`, `LLM_MODEL` e `LLM_API_KEY`, **seja qual for o `.env`** | O caso de hoje: 111 chamadas herdadas do `.env` |
| **2 · Rede externa bloqueada** | Qualquer conexão para fora de `localhost` levanta `RedeBloqueada` e é contada. No fim, a suíte avisa quantas houve | Um teste futuro que ligue um provedor real sem simular a rede |

Teste que **precisa** da IA continua ligando a LLM, como já faz hoje:

```python
@override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake")
```

O `override_settings` do teste vale **por cima** do executor. Os testes da camada de IA não mudam nada.

### 2.1 `backend/core/test_runner.py` (arquivo novo)

```python
"""Executor dos testes: a suíte nunca fala com uma LLM de verdade.

Sem ele, os testes herdam o .env de quem roda. Com LLM_ENABLED=1 no .env,
uma rodada fazia 111 chamadas reais ao Gemini (medido em 19/10/2026).
"""
import socket

from django.test.runner import DiscoverRunner
from django.test.utils import override_settings

# Teste que precisa da IA liga de propósito, por cima disto:
#   @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake")
LLM_DOS_TESTES = {
    "LLM_ENABLED": False,
    "LLM_PROVIDER": "fake",
    "LLM_BASE_URL": "",
    "LLM_MODEL": "",
    "LLM_API_KEY": "",
}

LOCAL = {"localhost", "127.0.0.1", "::1"}


class RedeBloqueada(RuntimeError):
    """Um teste tentou sair para a internet."""


class TravaDeRede:
    """Troca o connect() do socket por um que só aceita a própria máquina."""

    def __init__(self):
        self.tentativas = []
        self._connect_original = socket.socket.connect

    def ligar(self):
        trava = self

        def connect(sock, endereco):
            # Internet é sempre (host, porta). Outros formatos (caminho de
            # arquivo, por exemplo) não saem da máquina. Não use socket.AF_UNIX:
            # ele não existe no Python do Windows.
            if isinstance(endereco, tuple) and endereco[0] not in LOCAL:
                host = endereco[0]
                trava.tentativas.append(host)
                raise RedeBloqueada(f"teste tentou conectar em {host}: simule a rede com mock")
            return trava._connect_original(sock, endereco)

        socket.socket.connect = connect

    def desligar(self):
        socket.socket.connect = self._connect_original


class RunnerSemRede(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._llm = override_settings(**LLM_DOS_TESTES)
        self._llm.enable()
        self.rede = TravaDeRede()
        self.rede.ligar()

    def teardown_test_environment(self, **kwargs):
        self.rede.desligar()
        self._llm.disable()
        if self.rede.tentativas:
            print(f"\n⚠️  {len(self.rede.tentativas)} tentativa(s) de rede bloqueada(s): "
                  f"{sorted(set(self.rede.tentativas))}")
        super().teardown_test_environment(**kwargs)
```

> [!note] Por que a trava fica no `socket`, e não no `urlopen`
> O `urlopen` é só **um** jeito de sair para a rede. Um provedor futuro com o SDK do Google ou o `requests` passaria por fora. O `socket.connect` é o ponto por onde **toda** conexão Python passa. O MySQL da CI não é afetado por dois motivos: o `mysqlclient` conecta pela biblioteca em C, e não pelo `socket` do Python, e o host dele é `127.0.0.1`.

### 2.2 `backend/core/settings.py`

```python
# Testes nunca chamam a LLM de verdade, seja qual for o .env (core/test_runner.py)
TEST_RUNNER = "core.test_runner.RunnerSemRede"
```

### 2.3 Testes que provam as travas (`backend/core/tests.py`)

```python
import socket

from core.test_runner import RedeBloqueada


class TestesSemRede(SimpleTestCase):
    """U4: a suíte não depende do .env de quem roda e não sai para a internet."""

    def test_llm_desligada_seja_qual_for_o_env(self):
        self.assertFalse(settings.LLM_ENABLED)
        self.assertEqual(settings.LLM_PROVIDER, "fake")
        self.assertEqual(settings.LLM_API_KEY, "")

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake")
    def test_teste_de_ia_ainda_liga_a_llm(self):
        self.assertTrue(settings.LLM_ENABLED)

    def test_rede_externa_e_bloqueada(self):
        with self.assertRaises(RedeBloqueada):
            socket.create_connection(("192.0.2.1", 443), timeout=1)  # IP de documentação: sem DNS
```

Os dois primeiros testes **falham hoje** na máquina de quem tem `LLM_ENABLED=1` no `.env`. O terceiro **falha hoje em qualquer máquina**, porque a conexão sai de verdade. É a regra do time: pelo menos um teste novo que falharia antes.

> [!warning] Um detalhe do teste de bloqueio
> O `test_rede_externa_e_bloqueada` provoca **uma** tentativa de propósito, então o aviso do fim da suíte vai mostrar `1 tentativa(s) de rede bloqueada(s): ['192.0.2.1']`. Isso é esperado. **Qualquer número acima de 1 é um teste novo saindo para a rede.**

---

> [!success] O código desta spec já foi rodado
> Aplicado numa cópia da `develop` (`37884f3`), no Windows, **com o `.env` real de desenvolvimento** (`LLM_ENABLED=1`, `LLM_PROVIDER=gemini`):
> - **218 testes** (215 + os 3 novos). A única falha é o teste do fuso do MySQL, porque a validação rodou em SQLite.
> - **0 chamadas à LLM** na conferência com o endereço inexistente (antes: 111).
> - O aviso do fim mostrou exatamente `1 tentativa(s) de rede bloqueada(s): ['192.0.2.1']`.
> - Os 29 testes da camada de IA (`test_llm_openai_compat`, `test_llm_gravacao`, `test_llm_tela`, `test_experimento_ia`) passaram sem nenhuma mudança.
>
> A validação pegou um bug na primeira versão: ela usava `socket.AF_UNIX`, que **não existe no Python do Windows**. A versão acima já está corrigida.

## ✅ 3. Critérios de aceite (DoD)

- [ ] `core/test_runner.py` criado e `TEST_RUNNER` no `settings.py`
- [ ] Os 3 testes de `TestesSemRede` passando
- [ ] **Com `LLM_ENABLED=1` e `LLM_PROVIDER=gemini` no `.env`**, a suíte inteira:
  - [ ] roda em **~30 s** (era 336 s)
  - [ ] faz **0 chamadas** à LLM. Para conferir sem gastar cota:
    ```bash
    LLM_ENABLED=1 LLM_PROVIDER=openai_compat LLM_BASE_URL=http://127.0.0.1:9 LLM_MODEL=sonda LLM_PAUSA=0 python manage.py test 2>&1 | grep -c "LLM no fallback"
    ```
    Resultado esperado: **0** (hoje: 111). As falhas de propósito dos testes da IA ficam dentro do `assertLogs` e não aparecem na saída.
  - [ ] termina avisando **exatamente 1** tentativa de rede bloqueada (a do teste de bloqueio)
- [ ] A CI continua verde e com o mesmo número de testes + 3
- [ ] Linha no `README.md`, seção "Testes": *"Os testes nunca chamam a LLM de verdade, mesmo com `LLM_ENABLED=1` no `.env` (ver `core/test_runner.py`)."*

---

## 🗓️ 4. Onde entra

| | |
|---|---|
| **Prioridade** | **P0 para o desenvolvimento.** Cada rodada local gasta ~22% da cota diária, a mesma cota que a produção e a demonstração da banca vão usar |
| **Tamanho** | Pequeno: 1 arquivo novo, 1 linha no `settings.py`, 3 testes, 1 linha no README |
| **Branch** | `fix/testes-sem-rede`, saindo da `develop` |
| **Release** | Junto com a **v0.3.1** (U1 e U2 da spec urgente). Não muda nada em produção, mas protege a cota que a v0.3.1 vai começar a usar |
| **Revisão** | De quem cuida de **testes/CI** (frente de Infra) |

> [!tip] Até esta spec entrar
> Rode a suíte com a IA desligada só naquela execução, sem mexer no `.env`:
> ```powershell
> $env:LLM_ENABLED="0"; python manage.py test
> ```
