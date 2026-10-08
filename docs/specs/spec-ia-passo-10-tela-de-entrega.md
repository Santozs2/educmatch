---
title: "Spec IA · Passo 10 — a tela de entrega (principal + 4 alternativas com texto)"
aliases: ["Passo 10", "Tela de entrega", "Resultado com texto da LLM"]
tags: [tcc, ia, llm, spec, front, resultado]
status: proposto
projeto: TCC
branch: feature/llm-tela-de-entrega
criado: 2026-10-08
---

> [!info] Plano da IA: [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 Camada de IA]] · Anterior: [[spec-ia-passo-09-provedor-real|🌐 Passo 9]] · Próximo: [[spec-ia-passo-11-experimento|📊 Passo 11]]

# 🎨 Passo 10: a tela de entrega

**Branch:** `feature/llm-tela-de-entrega`, saindo da `develop` **com o Passo 9 já mesclado**
**Risco:** baixo. Só a tela de resultado muda, e sem LLM ela continua idêntica.
**Testes ao final:** a suíte do Passo 9 **+ 5** (na cópia: 196)

> [!abstract] O que esta branch faz
> O texto que a LLM gravou no Passo 9 aparece para o aluno:
> 1. **Curso principal:** o texto da LLM no lugar da descrição, com um **selo** dizendo que foi escrito com IA.
> 2. **As 4 alternativas:** a frase curta de cada uma, quebrando a linha em vez de cortar.
> 3. **A engine continua na tela:** o anel de afinidade e o "Por que este curso?" não mudam.
>
> Sem texto da LLM (desligada ou em fallback), a tela é **exatamente** a de hoje.

> [!success] O código desta spec já foi rodado
> Os **5 testes novos** passaram; a suíte fechou em **196**. A tela foi aberta no navegador com o provedor `fake` e textos do tamanho máximo (600 e 220 caracteres), em **1280 px** e em **375 px** (celular): **sem rolagem horizontal**, e as alternativas quebram a linha.

---

## 🎓 Entenda antes de começar

> [!quote] A regra do plano
> **"Não esconder a engine atrás da IA."** A engine é o núcleo defensável do trabalho; o texto é a embalagem. A banca vai querer ver o número por trás da frase.

> [!important] Três escolhas que diferem do plano original
> | Plano da IA | Aqui | Por quê |
> |---|---|---|
> | "Por que este curso?" **recolhível** | **Continua aberto** | Recolher esconderia a engine justamente na tela que a banca vai olhar. A regra do próprio plano é não esconder |
> | "Selo discreto de **fallback**" | **Selo de IA** quando há texto da LLM; no fallback, **nenhum selo** | O aluno não precisa saber que "a IA falhou": no fallback ele vê a tela da engine, completa. O que ele precisa saber é quando um texto foi **escrito por IA**, e isso é transparência. Para a banca, o fallback aparece no painel (Passo 11) e no atributo `data-entrega` da página |
> | Carregamento em duas etapas | Uma etapa | Decidido no [[spec-ia-passo-09-provedor-real\|Passo 9]]: a tela "Analisando" cobre a espera |

---

## 1️⃣ `backend/quiz/web_views.py`: cada item leva o texto

No `resultado_pagina`, dentro da lista `itens`:

```python
            "areas": areas_da_recomendacao(rec),
            "texto": rec.llm_text,  # vazio sem LLM ou no fallback: a tela mostra a descrição
        }
```

A ordem já é a `rank_final` (o `Meta.ordering` do `Recomendacao`), então o principal da LLM vira o `destaque` sem nenhuma outra mudança.

## 2️⃣ `backend/templates/quiz/resultado.html`

### A `<section>` diz de onde veio a entrega

```html
<section class="resultado" data-entrega="{% if destaque.texto %}ia{% else %}engine{% endif %}">
```

> [!tip] 🎓 Para que serve o `data-entrega`
> Não muda nada na tela. Na demo, um **Inspecionar elemento** mostra se aquele resultado veio da LLM ou da engine, e os testes usam o atributo para conferir o fallback.

### No destaque, troque a linha da descrição

Troque:

```html
                <p class="subtitulo">{{ destaque.curso.descricao|truncatewords:30 }}</p>
```

por:

```html
                {% if destaque.texto %}
                <p class="destaque__texto">{{ destaque.texto }}</p>
                <p class="selo-ia"><i class="fa-solid fa-wand-magic-sparkles" aria-hidden="true"></i> Texto escrito com IA a partir do cálculo do EducMatch</p>
                {% else %}
                <p class="subtitulo">{{ destaque.curso.descricao|truncatewords:30 }}</p>
                {% endif %}
```

O bloco `{% if destaque.areas %}` com o **"Por que este curso?"** continua logo abaixo, **sem mudança**.

### Nas alternativas, troque a linha da descrição

Troque:

```html
                <p class="outro__descricao">{{ item.curso.descricao }}</p>
```

por:

```html
                {% if item.texto %}
                <p class="outro__descricao outro__descricao--ia">{{ item.texto }}</p>
                {% else %}
                <p class="outro__descricao">{{ item.curso.descricao }}</p>
                {% endif %}
```

> [!warning] 🎓 Nunca use `|safe` no texto da LLM
> O texto vem de fora do sistema. O Django **escapa** tudo por padrão: se a LLM devolver `<script>`, a tela mostra o texto `<script>`, e nada é executado. Há um teste para isso (`test_texto_da_llm_e_escapado`). Um `|safe` aqui abriria uma brecha de XSS.

## 3️⃣ `backend/static/css/resultado.css`

Antes do bloco `/* ---------- Por que este curso ---------- */`:

```css
/* ---------- Texto da LLM (Passo 10) ---------- */

.destaque__texto {
  margin-bottom: 8px;
  color: var(--tinta);
  line-height: 1.55;
}

.selo-ia {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 16px;
  color: var(--texto-3);
  font-size: 0.75rem;
  font-weight: 600;
}
```

E logo depois da regra `.outro__descricao` que já existe:

```css
/* O texto da LLM tem até 220 caracteres: quebra a linha em vez de cortar. */
.outro__descricao--ia {
  white-space: normal;
}
```

> [!note] 🎓 Por que a classe modificadora
> A descrição das alternativas é cortada numa linha só (`white-space: nowrap` + `text-overflow: ellipsis`), o que é ótimo para uma descrição longa do catálogo. A frase da LLM foi **escrita** para ser lida inteira (até 220 caracteres), então ela ganha `outro__descricao--ia` e quebra a linha. Só cores e tamanhos dos **tokens**: o alto contraste continua funcionando.

---

## 4️⃣ Testes: `backend/quiz/tests/test_llm_tela.py` (arquivo novo)

```python
from django.test import override_settings

from quiz.models import Recomendacao, Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch

SELO = "Texto escrito com IA"


class TelaDeEntregaTest(BaseEducMatch):
    """Passo 10: a tela mostra o texto da LLM sem esconder a engine."""

    def resultado(self):
        resposta = self.responder_tudo()
        return Tentativa_de_resposta.objects.latest("id"), self.client.get(resposta.url)

    @override_settings(LLM_ENABLED=False)
    def test_sem_llm_a_tela_e_a_da_engine(self):
        tentativa, pagina = self.resultado()

        self.assertEqual(pagina.status_code, 200)
        self.assertContains(pagina, 'data-entrega="engine"')
        self.assertNotContains(pagina, SELO)
        self.assertContains(pagina, "Por que este curso?")
        self.assertEqual(len(pagina.context["outros"]) + 1, tentativa.recomendacoes.count())

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
    def test_com_llm_mostra_os_textos_e_o_selo(self):
        tentativa, pagina = self.resultado()

        self.assertContains(pagina, 'data-entrega="ia"')
        self.assertContains(pagina, SELO, count=1)
        for rec in tentativa.recomendacoes.all():
            with self.subTest(curso=rec.curso_id):
                self.assertContains(pagina, rec.llm_text)
        # A engine continua na tela: a banca quer ver o número por trás da frase.
        self.assertContains(pagina, "Por que este curso?")
        self.assertContains(pagina, "de afinidade")

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
    def test_destaque_e_o_principal_entregue_com_o_texto_dele(self):
        self.responder_tudo()
        tentativa = Tentativa_de_resposta.objects.latest("id")
        primeiro = tentativa.recomendacoes.get(rank_engine=1)
        segundo = tentativa.recomendacoes.get(rank_engine=2)
        primeiro.rank_final, segundo.rank_final = 2, 1
        segundo.llm_text = "Este é o texto do novo principal."
        Recomendacao.objects.bulk_update([primeiro, segundo], ["rank_final", "llm_text"])

        pagina = self.client.get(f"/resultado/{tentativa.pk}/")

        self.assertEqual(pagina.context["destaque"]["curso"], segundo.curso)
        self.assertEqual(pagina.context["destaque"]["texto"], "Este é o texto do novo principal.")

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
    def test_texto_da_llm_e_escapado(self):
        self.responder_tudo()
        tentativa = Tentativa_de_resposta.objects.latest("id")
        tentativa.recomendacoes.filter(rank_final=1).update(llm_text='<script>alert("x")</script>')

        pagina = self.client.get(f"/resultado/{tentativa.pk}/")

        self.assertNotContains(pagina, '<script>alert("x")</script>')
        self.assertContains(pagina, "&lt;script&gt;")

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="gemini", LLM_BASE_URL="", LLM_MODEL="")
    def test_no_fallback_a_tela_volta_a_ser_a_da_engine(self):
        # gemini sem modelo: o provedor nem monta, e a camada cai na engine.
        with self.assertLogs("quiz.delivery", "WARNING"):
            tentativa, pagina = self.resultado()

        self.assertTrue(tentativa.used_fallback)
        self.assertContains(pagina, 'data-entrega="engine"')
        self.assertNotContains(pagina, SELO)
```

> [!tip] 🎓 O último teste usa uma falha **de verdade**, sem dublê
> `LLM_PROVIDER=gemini` sem `LLM_MODEL` faz o provedor recusar a montagem (`LLMUnavailable`). É o mesmo caminho de uma chave esquecida no dia da banca, e o teste prova que o aluno vê a tela da engine.

---

## ✅ Verificação

```bash
cd backend
python manage.py test quiz.tests.test_llm_tela    # 5 testes, OK
python manage.py test                             # a suíte + 5
```

À mão, no navegador:

| Situação | O que conferir |
|---|---|
| `LLM_ENABLED=0` | A tela de sempre: descrição no destaque, sem selo |
| `LLM_ENABLED=1` + Gemini | Texto no destaque, selo "Texto escrito com IA…", "Por que este curso?" **visível**, frases nas 4 alternativas |
| Celular (375 px, ou o modo dispositivo do navegador) | Sem rolagem para o lado; as frases das alternativas quebram a linha |
| Alto contraste ligado (pelo painel) | O texto e o selo continuam legíveis |
| Uma resposta em que a LLM trocou o 1º (`diverged=True` no admin) | O destaque é o curso que a LLM escolheu; o anel mostra a afinidade **dele** |

## 📦 Commit e PR

```bash
git switch develop && git pull
git switch -c feature/llm-tela-de-entrega
# ... aplica a spec ...
git add backend/quiz/web_views.py backend/templates/quiz/resultado.html backend/static/css/resultado.css backend/quiz/tests/test_llm_tela.py
git commit -m "feat(ia): tela de resultado com o texto da LLM (Passo 10)

- destaque com o texto da LLM e selo de IA; a engine continua visivel
- alternativas com a frase da LLM, quebrando a linha
- sem texto (LLM desligada ou fallback), a tela e a de antes"
git push -u origin feature/llm-tela-de-entrega
```

> [!success] Definition of Done (o do plano)
> - [ ] Com `LLM_ENABLED=0`, a tela responde 200 e mostra os 5 cursos, como antes
> - [ ] Com `LLM_ENABLED=1`, mostra a entrega da LLM **e** o "Por que este curso?"
> - [ ] Conferido no celular e com alto contraste
> - [ ] Nenhum `|safe` no texto da LLM
