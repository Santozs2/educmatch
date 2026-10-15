---
title: "Apresentação · Camada de IA (LLM em cima da engine)"
aliases: ["IA na apresentação", "LLM na apresentação", "Desenho B modificado"]
tags: [tcc, apresentacao, ia, llm, engine]
status: codigo-pronto
projeto: TCC
atualizado: 2026-10-15
---

> [!info] Apresentação: [[README|🎤 Roteiro]] · [[engine|🧮 Engine]] · [[backend|⚙️ Backend]] · [[frontend|🎨 Front]] · **🤖 Camada de IA** · [[demo-e-perguntas|🎬 Demo e banca]]
> Plano completo: [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 Camada de IA]] · Specs: [[spec-ia-passo-07-provedor-fake|7]] · [[spec-ia-passo-08-prompt-e-validacao|8]] · [[spec-ia-passo-09-provedor-real|9]] · [[spec-ia-passo-10-tela-de-entrega|10]] · [[spec-ia-passo-11-experimento|11]]

# 🤖 Camada de IA: a LLM **entrega**, a engine **decide**

> [!abstract] O que esta nota é
> Como apresentar a camada de IA **sem ela roubar o lugar da engine**. A LLM não escolhe os cursos: ela recebe os 5 que a [[engine|🧮 engine]] escolheu, escreve o porquê em linguagem de gente e **só pode trocar o 1º lugar onde a engine diz que há empate**.

> [!success] Status em 2026-10-15: **todo o código está pronto e mesclado**
> Os Passos 7 a 11 estão na `main` e na `develop` (PRs #40 a #44), com **203 testes verdes** no MySQL. O que falta **não é código**: é ligar a chave, rodar o experimento e escrever o capítulo (ver §5).
> Enquanto `LLM_ENABLED=0` (o padrão), o aluno vê exatamente o sistema de antes.

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
engine.recomendar(tentativa)  ── grava os 5 cursos (rank_engine = rank_final)   [transaction.atomic]
   │                              ◄── O RESULTADO JÁ EXISTE AQUI: é o fallback
   ▼
delivery.entregar(tentativa)  ── fora da transação; nunca levanta exceção
   ├─ build_payload()         ── perfil + 5 candidatos + tie_set (sem nome, sem e-mail)
   ├─ montar_prompt()         ── quiz/prompts/entrega_v1.md com os dados no bloco DADOS
   ├─ cache?                  ── mesmo prompt + modelo = mesma resposta, sem chamar a API
   ├─ provider.complete()     ── FakeProvider (testes) ou OpenAICompatProvider (Gemini, Groq…)
   └─ validate_delivery()     ── id fora da lista? repetido? faltando? texto longo? 1º fora do tie_set?
        ├── ✅ válida   → grava rank_final, llm_text e os metadados
        └── ❌ inválida, timeout, sem cota ou bug → used_fallback = True, fica a ordem da engine
```

---

## 🛡️ 3. As travas (o que torna isso defensável)

| Trava | Como funciona | Onde está |
|---|---|---|
| **A engine grava antes** | O resultado determinístico vai para o banco antes de qualquer chamada de rede | `engine.recomendar` |
| **Regra 2 (empate)** | A LLM só põe em 1º um curso do `tie_set`. A mesma régua de 0,02 da confiança | `engine.conjunto_de_empate` + prompt |
| **Validação no servidor** | Só aceita os ids que foram enviados, os 5 e sem repetir, com texto até 600/220 caracteres | `quiz/serializers.py` (`DeliverySerializer`) |
| **Fallback** | Qualquer erro → ordem da engine, **nunca** erro 500 | `delivery.entregar` |
| **Botão de pânico** | `LLM_ENABLED=0` no `.env` desliga a camada inteira | `settings.py` (já existe) |
| **Sem dado pessoal** | O payload não leva `respondido_por`, usuário nem e-mail. Há teste para isso | `build_payload` |
| **Reprodutível** | `temperature=0` + **cache no banco** (`DatabaseCache`): mesmo perfil, mesma resposta | `delivery.deliver` |
| **Divergência medida, não declarada** | O servidor compara o 1º entregue com o 1º da engine e grava `diverged`. A LLM não "diz" se reordenou | `delivery._gravar` |
| **Transparência** | Texto da LLM sempre com o selo *"Texto escrito com IA"*; nunca renderizado com `\|safe` | `resultado.html` |

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

| Passo | Entrega | PR | Código | Falta |
|:-:|---|:-:|:-:|---|
| **7** | Protocolo `LLMProvider`, `FakeProvider`, `build_payload`, `get_provider` | #40 | ✅ | — |
| **8** | Prompt `entrega_v1.md` + `DeliverySerializer` | #41 | ✅ | — |
| **9** | `OpenAICompatProvider`, cache, timeout, fallback, gravação, `testar_llm` | #42 | ✅ | 🔑 **chave real** + conferir `cache_hit` |
| **10** | Tela de entrega com texto e selo de IA | #43 | ✅ | Conferir com texto real do Gemini |
| **11** | `experimento_ia` + bloco "Camada de IA" no painel | #44 | ✅ | 🔑 Rodar com a chave, avaliação humana, capítulo |

> [!todo] O que falta, em ordem
> 1. **Decidir quem guarda a chave** (pergunta 5 da decisão, ainda em aberto) e criá-la no AI Studio.
> 2. `python manage.py testar_llm` com a chave → texto aprovado pela validação.
> 3. Responder o quiz 2 vezes com as mesmas respostas → a 2ª com `cache_hit = True`.
> 4. `python manage.py experimento_ia --so-empates --n 30` e `--n 30` → avaliação humana nas linhas com troca.
> 5. Configurar as `LLM_*` no App Service do Azure e **pré-aquecer o cache** com os perfis da demo.
> 6. Preencher a §6 com os números reais.

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
| **Seguiu a IA ou a engine** | Quando a IA trocou o 1º, o aluno salvou qual dos dois? | `Interesse.rank_snapshot` × `rank_engine_snapshot` |

> [!tip] Onde ver esses números
> - **Experimento:** `python manage.py experimento_ia` gera o CSV com uma linha por perfil e um resumo no terminal.
> - **Uso real:** o bloco **"Camada de IA"** na tela **Quiz** do painel (`/painel/quiz/`) mostra divergência, fallback, cache, latência mediana, tokens e "seguiu a IA / a engine". Ele só aparece quando a LLM foi chamada no período.

> [!example] A tabela do capítulo (preencher depois do experimento)
> | Métrica | Só empates (n=30) | Geral (n=30) |
> |---|:-:|:-:|
> | Divergência | ?% | ?% |
> | Melhorou / indiferente / piorou | ? / ? / ? | ? / ? / ? |
> | Fallback | ?% | ?% |
> | Latência mediana | ? ms | ? ms |
> | Tokens (entrada → saída) | ? → ? | ? → ? |

> [!question] A pergunta que a banca vai fazer
> *"Por que IA, se a engine já recomendava?"* A resposta só existe com o Passo 11: com a **taxa de divergência** e a **avaliação humana**, a camada de IA vira **um experimento com resultado**, e não um "usamos IA". Se o Passo 11 não estiver pronto, apresente a camada como **arquitetura pronta e medível**, e mostre os campos e as travas.

---

## 🌐 7. Provedores gratuitos (para responder se perguntarem do custo)

| Opção | Limite gratuito (aprox., out/2026) | Uso no projeto | `.env` |
|---|---|---|---|
| **Gemini Flash-Lite** (Google AI Studio) | cerca de 1.000 chamadas/dia | Provedor da defesa | `LLM_PROVIDER=gemini` |
| **Groq** (Llama 3.3 70B) | cerca de 1.000 chamadas/dia | Reserva | `openai_compat` + `LLM_BASE_URL=https://api.groq.com/openai/v1` |
| **OpenRouter** (modelos `:free`) | 50 chamadas/dia sem créditos | Comparar modelos no desenvolvimento | `openai_compat` + `https://openrouter.ai/api/v1` |
| **OmniRoute** (gateway que vocês mesmos hospedam) | junta vários planos gratuitos | Só no desenvolvimento: ele troca de modelo sozinho, o que atrapalha a reprodutibilidade | `openai_compat` + `http://localhost:20128/v1` |

Trocar de provedor é trocar 3 linhas do `.env` (`LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`), sem mexer no código: é o mesmo `OpenAICompatProvider` para todos.

Cada quiz faz **1 chamada**, e perfis repetidos saem do cache. Para um TCC, o plano gratuito sobra.
