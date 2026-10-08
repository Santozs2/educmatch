---
title: "Apresentação · Camada de IA (LLM em cima da engine)"
aliases: ["IA na apresentação", "LLM na apresentação", "Desenho B modificado"]
tags: [tcc, apresentacao, ia, llm, engine]
status: em-andamento
projeto: TCC
atualizado: 2026-10-08
---

> [!info] Apresentação: [[README|🎤 Roteiro]] · [[engine|🧮 Engine]] · [[backend|⚙️ Backend]] · [[frontend|🎨 Front]] · **🤖 Camada de IA** · [[demo-e-perguntas|🎬 Demo e banca]]
> Plano completo: [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 Camada de IA]] · Spec atual: [[spec-ia-passo-07-provedor-fake|🔌 Passo 7]]

# 🤖 Camada de IA: a LLM **entrega**, a engine **decide**

> [!abstract] O que esta nota é
> Como apresentar a camada de IA **sem ela roubar o lugar da engine**. A LLM não escolhe os cursos: ela recebe os 5 que a [[engine|🧮 engine]] escolheu, escreve o porquê em linguagem de gente e **só pode trocar o 1º lugar onde a engine diz que há empate**.

> [!warning] Status em 2026-10-08: **em construção**
> O Passo 7 (protocolo + `FakeProvider` + payload) está sendo feito na branch `feat/llm-fake-provider`. **Nada da IA aparece para o aluno ainda.** Atualize a tabela da §5 a cada passo que entrar e, na banca, **mostre só o que estiver mesclado**.

---

## 🧭 1. A decisão: Desenho B modificado

| Ponto | Decisão |
|---|---|
| Quem escolhe os cursos | A **engine** (cosseno), sempre |
| O que a LLM pode fazer | **Reordenar dentro do top 5**, sem tirar nem acrescentar curso |
| Quando pode trocar o 1º lugar | **Só** se o novo 1º estiver no `tie_set` (a menos de 0,02 do 1º da engine) |
| O que o aluno vê | 1 curso principal + 4 alternativas, com o texto da LLM |
| Provedor | Plugável pelo `.env`. Padrão: **Gemini Flash** (plano gratuito) |
| Prompt | **Um prompt fixo e versionado** (`LLM_PROMPT_VERSION`), igual para todos os perfis |

> [!quote] A frase para a banca
> "A engine é o núcleo **defensável**: determinístico, explicável e testado. A LLM é a **embalagem**: ela explica, e só desempata onde a engine mostrou que há empate. **Desligue a internet e o sistema continua recomendando.**"

---

## 🔀 2. O fluxo

```
POST do quiz
   │
   ▼
engine.recomendar(tentativa)  ── grava os 5 cursos (rank_engine = rank_final)
   │                              ◄── O RESULTADO JÁ EXISTE AQUI: é o fallback
   ▼
build_payload(tentativa)      ── perfil + 5 candidatos + tie_set (sem nome, sem e-mail)
   │
   ▼
provider.complete(prompt)     ── FakeProvider (testes) ou Gemini (real)
   │
   ▼
validação da saída            ── id fora da lista? repetido? faltando? 1º fora do tie_set?
   ├── ✅ válida   → grava rank_final, llm_text e os metadados
   └── ❌ inválida, timeout ou sem crédito → used_fallback = True, fica a ordem da engine
```

---

## 🛡️ 3. As travas (o que torna isso defensável)

| Trava | Como funciona | Onde está |
|---|---|---|
| **A engine grava antes** | O resultado determinístico vai para o banco antes de qualquer chamada de rede | `engine.recomendar` |
| **Regra 2 (empate)** | A LLM só põe em 1º um curso do `tie_set`. A mesma régua de 0,02 da confiança | `engine.conjunto_de_empate` + prompt |
| **Validação no servidor** | Só aceita os ids que foram enviados, os 5 e sem repetir | Passo 8 |
| **Fallback** | Qualquer erro → ordem da engine, **nunca** erro 500 | Passo 9 |
| **Botão de pânico** | `LLM_ENABLED=0` no `.env` desliga a camada inteira | `settings.py` (já existe) |
| **Sem dado pessoal** | O payload não leva `respondido_por`, usuário nem e-mail. Há teste para isso | `build_payload` |
| **Reprodutível** | `temperature=0` + **cache no banco** (`DatabaseCache`): mesmo perfil, mesma resposta | Passo 9 |
| **Divergência medida, não declarada** | O servidor compara `rank_final` com `rank_engine` e grava `diverged`. A LLM não "diz" se reordenou | Passo 9 |

> [!example] Um caso real em que a LLM **poderia** trocar o 1º lugar
> No exemplo da [[engine#🔬 4. Um caso real, do banco|engine]], o Robô de Soldagem (0,8622) e o Caldeireiro (0,8514) estão a 0,0109 um do outro: `tie_set = [19, 16]`. A LLM pode apresentar o Caldeireiro como principal. Já o 3º colocado (0,8170) **não** pode ir para o 1º lugar.
> Nos 5.000 perfis simulados, **34%** têm empate no topo, ou seja, a LLM teria liberdade em cerca de 1 de cada 3 tentativas. Nas outras 2, ela só escreve o texto.

---

## 🧱 4. O que já está pronto no banco (desde a fase pré-IA)

| Onde | Campos | Para quê |
|---|---|---|
| `Recomendacao` | `rank_engine`, `rank_final`, `llm_text` | A ordem da engine, a ordem entregue e o texto que o aluno leu |
| `Tentativa_de_resposta` | `tie_set`, `confidence_band` | Quem pode ir para o 1º e o nível de confiança |
| `Tentativa_de_resposta` | `llm_model`, `prompt_version`, `latency_ms`, `tokens_in`, `tokens_out`, `used_fallback`, `diverged`, `cache_hit` | **As métricas do experimento** (uma vez por tentativa) |
| `Interesse` | `rank_snapshot`, `rank_engine_snapshot`, `era_principal` | Se o aluno salvou o curso que **a LLM** pôs em 1º ou o que **a engine** pôs |
| `settings.py` | `LLM_ENABLED`, `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_TIMEOUT`, `LLM_PROMPT_VERSION` | Tudo pelo `.env`; desligado por padrão |

---

## 🗓️ 5. Os passos e o status

| Passo | Entrega | Precisa de internet? | Status |
|:-:|---|:-:|:-:|
| **7** | Protocolo `LLMProvider`, `FakeProvider`, `build_payload`, `get_provider` | ❌ | 🔨 em andamento |
| **8** | Prompt v1 em arquivo + validação da saída | ❌ | ⬜ |
| **9** | Provedor real + cache + timeout + fallback + gravação | ✅ | ⬜ |
| **10** | Tela de entrega: principal + 4 alternativas com texto | ❌ | ⬜ |
| **11** | Experimento comparativo + capítulo da monografia | ✅ | ⬜ |

> [!tip] Por que existe um provedor "fake"
> O dublê responde no mesmo formato do Gemini, **sem internet, sem chave e sem custo**. Por isso os Passos 7, 8 e 10 andam mesmo sem a chave da API, e a CI nunca depende de um serviço externo. Também é com ele que se testam as respostas ruins de propósito (curso inventado, JSON quebrado, timeout).

---

## 📊 6. As métricas que o Passo 11 vai medir

| Métrica | Como se calcula | Campo |
|---|---|---|
| **Taxa de divergência** | % das tentativas em que `rank_final` ≠ `rank_engine` no 1º lugar | `diverged` |
| **Taxa de fallback** | % das tentativas em que a LLM falhou e valeu a engine | `used_fallback` |
| **Latência** | Mediana e pior caso do tempo da chamada | `latency_ms` |
| **Custo** | Tokens de entrada e saída por tentativa | `tokens_in`, `tokens_out` |
| **Acerto no cache** | % das respostas servidas sem chamar a API | `cache_hit` |
| **Avaliação humana** | O grupo classifica cada divergência: melhorou · indiferente · piorou | planilha do experimento |
| **Validação real** | Pergunta 6 da avaliação de fim de curso: *"O curso combinou com o que o quiz mostrou?"* | `avaliacao` |

> [!question] A pergunta que a banca vai fazer
> *"Por que IA, se a engine já recomendava?"* A resposta só existe com o Passo 11: com a **taxa de divergência** e a **avaliação humana**, a camada de IA vira **um experimento com resultado**, e não um "usamos IA". Se o Passo 11 não estiver pronto, apresente a camada como **arquitetura pronta e medível**, e mostre os campos e as travas.

---

## 🌐 7. Provedores gratuitos (para responder se perguntarem do custo)

| Opção | Limite gratuito (aprox., out/2026) | Uso no projeto |
|---|---|---|
| **Gemini Flash-Lite** (Google AI Studio) | cerca de 1.000 chamadas/dia | Provedor da defesa |
| **Groq** (Llama 3.3 70B) | cerca de 1.000 chamadas/dia | Reserva: troca-se pelo `.env` |
| **OpenRouter** (modelos `:free`) | 50 chamadas/dia sem créditos | Comparar modelos no desenvolvimento |
| **OmniRoute** (gateway que vocês mesmos hospedam) | junta vários planos gratuitos | Só no desenvolvimento: ele troca de modelo sozinho, o que atrapalha a reprodutibilidade |

Cada quiz faz **1 chamada**, e perfis repetidos saem do cache. Para um TCC, o plano gratuito sobra.
