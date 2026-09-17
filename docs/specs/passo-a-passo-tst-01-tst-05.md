---
title: "Passo a passo — TST-01 a TST-05 (suíte de testes pelos contratos e CI)"
aliases: ["Passo a passo TST", "Testes por contrato", "Suíte de conformidade", "Fase 4 do plano v0.2", "CI do TCC"]
tags: [tcc, testes, contratos, django, drf, ci, execucao, passo-a-passo, auditoria]
status: proposto
projeto: TCC
criado: 2026-09-17
---

> [!info] Contratos: [[contratos-c1-a-c6 🟢|📜 C1 a C6]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-v02-supabase-a-testes|🗺️ Plano v0.2]] · Suíte antiga: [[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes e validação]] · Vem depois de: [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 PNL-01 a PNL-05]]

# 🧪 Passo a passo — TST-01 a TST-05

> [!abstract] O que esta nota é
> O **como** da Fase 4: transformar os contratos `C1` a `C6` de documento em **comando**. Hoje, responder *"o C4 foi cumprido?"* exige ler o código e traduzir de cabeça — foi o que a auditoria teve de fazer, e é por isso que os desvios sobreviveram. Depois desta fase, a resposta é `manage.py test`.
> É a fase que produz o artefato que a monografia precisa: uma tabela de conformidade **gerada**, não afirmada.

> [!warning] Nada disto foi executado
> Escrito contra [[contratos-c1-a-c6 🟢|C1 a C6]] e [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|REV-05 e REV-08]]. Os defeitos citados (`serializer_class = Questao`, `validar` em vez de `validate`, `signals.py` filtrando `Questao`) vêm de lá. **Confirme cada um antes de consertar** — alguns podem já ter sido corrigidos de passagem nas fases anteriores.

> [!important] Esta fase escreve código de produção, e não é desvio de escopo
> "Testar pelos contratos" descobre, na primeira hora, que três contratos **não têm o que testar**: os endpoints do `C3` respondem 500, e o *claim* do `C6` não existe em lugar nenhum. Um teste não pode ser escrito contra o vazio.
> Então a fase conserta o que precisa existir para ser testado — e é justamente esse o valor dela. **Escrever o teste é o que torna a não conformidade inegociável.** Enquanto era documento, dava para conviver.

## 🧭 O mapa da fase

| Tarefa | O que faz | Contrato | Achado |
|---|---|---|---|
| **TST-01** | a fundação: pacotes de teste, base comum, a suíte de matemática pura | — | a suíte perdida |
| **TST-02** | consertar e cobrir a camada REST | prepara o `C3` | `REV-05` |
| **TST-03** | matriz de rotas e autorização, limpeza de rota morta | `C5` | `REV-08` |
| **TST-04** | implementar e cobrir o *claim* da tentativa anônima | `C6` | `REV-08` |
| **TST-05** | o manifesto de conformidade, a CI e a proteção da `main` | `C1`…`C6` | — |

---

## 🚦 Antes de abrir o editor

```bash
git checkout main && git pull
git checkout -b test/contratos
```

Veja o tamanho do buraco antes de começar — este comando é o retrato que a monografia vai citar:

```bash
wc -l quiz/tests.py accounts/tests.py catalogo/tests.py
grep -rn "def test_" --include="*.py" . | wc -l
```

> [!warning] A suíte não foi "nunca escrita" — ela foi **perdida na tradução**
> [[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes e validação]] descreve 12 testes verdes em 17/08/2026, com nomes em inglês (`test_escala_nao_muda_o_score` sobre `Course`, `QuizAttempt`). A auditoria de 11/09 encontra os `tests.py` vazios e o código todo em português.
> A reescrita levou a suíte embora, e **ninguém percebeu por três semanas** — porque nada rodava `manage.py test` automaticamente. É o achado mais barato de defender do trabalho inteiro: *suíte de teste sem gatilho automático é documentação, não garantia.* A TST-05 é a correção estrutural disso, e vale mais do que qualquer teste individual desta nota.

---

## 1️⃣ TST-01 — a fundação

### De `tests.py` para pacote

```bash
mkdir quiz/tests accounts/tests catalogo/tests
git rm quiz/tests.py accounts/tests.py catalogo/tests.py
touch quiz/tests/__init__.py accounts/tests/__init__.py catalogo/tests/__init__.py
```

```
quiz/tests/
├── __init__.py
├── base.py                  # a classe comum, com os seeds
├── test_engine_puro.py      # SimpleTestCase — nao abre banco
├── test_recomendacao.py     # TestCase — fim a fim
└── test_api.py              # a camada REST (TST-02)

accounts/tests/
├── __init__.py
├── test_c4_interesse.py
├── test_c5_rotas.py
└── test_c6_claim.py

painel/tests/                # ja criado na Fase 3
```

> [!note] Pacote em vez de arquivo único porque a suíte vai passar de 40 testes
> Um `tests.py` de 600 linhas ninguém abre com vontade, e todo mundo acrescenta no fim sem ler o resto — o que produz cenários duplicados e `setUp` redundante. Um arquivo por assunto mantém cada um em torno de cem linhas.
> O Django encontra tudo sozinho, desde que os `__init__.py` existam. Esquecer um deles faz o app aparecer com **zero** testes, sem erro nenhum — é a armadilha desta tarefa, e o `manage.py test -v 2` a revela na hora.

### `quiz/tests/base.py`

```python
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase

# CONFIRA OS NOMES antes de rodar: os models desta base sao importados dentro
# dos metodos, justamente para que um nome errado quebre um teste e nao a suite
# inteira. Os nomes reais estao no glossario (ver C1 a C6, secao 9).
SEEDS = ("seed_areas", "seed_cursos", "seed_questoes")


class BaseEducMatch(TestCase):
    """Base de todo teste que precisa do catalogo real.

    Os seeds rodam UMA vez por classe; cada teste roda em transacao com rollback.
    """

    @classmethod
    def setUpTestData(cls):
        silencio = StringIO()
        for comando in SEEDS:
            call_command(comando, stdout=silencio)

    def setUp(self):
        # DisallowedHost: 'testserver' -- ver Bugs e licoes, Ambiente (Windows)
        self.client = Client(SERVER_NAME="localhost")

    def criar_usuario(self, email="aluno@exemplo.com", **extra):
        return get_user_model().objects.create_user(
            email=email, password="afinidade-2026", **extra
        )

    def responder_tudo(self, nome="Visitante", coluna=0):
        """Responde o quiz inteiro escolhendo sempre a alternativa de indice `coluna`.

        Devolve a resposta HTTP. Usa `get()` na alternativa de proposito:
        trecho ambiguo tem que estourar, nao escolher em silencio.
        """
        from quiz.models import Questao

        dados = {"respondido_por": nome}
        for questao in Questao.objects.filter(is_active=True).order_by("id"):
            alternativas = list(questao.alternativas.order_by("id"))
            dados[f"questao_{questao.id}"] = alternativas[coluna % len(alternativas)].id

        return self.client.post("/", dados)
```

> [!danger] Os imports de model ficam **dentro** dos métodos, de propósito
> `from quiz.models import Questao` no topo do `base.py` faz um nome errado derrubar **toda** a suíte com o mesmo `ImportError` — o que parece catástrofe e é um import. Dentro do método, quebra só o teste que usa aquele model, e a mensagem aponta para o lugar certo.
> Confirme os nomes reais antes de rodar: [[contratos-c1-a-c6 🟢|📜 C1 a C6, seção 9]] tem a tabela, e `manage.py shell` tem a verdade:
> ```bash
> ./.venv/Scripts/python.exe manage.py shell -c "from django.apps import apps; print([m.__name__ for m in apps.get_models()])"
> ```
> Confira também os nomes dos comandos de seed com `manage.py help | grep -i seed` antes de preencher a constante `SEEDS`.

> [!success] Os seeds como *fixture* — dois benefícios de uma vez
> É a decisão que a suíte antiga tomou e que vale repetir: (1) os dados de teste são exatamente os dados reais do projeto, sem *fixture* paralela que envelhece; (2) **os seeds passam a ser testados de brinde** — se um deles quebrar, a suíte inteira cai e o erro aparece na hora.
> Vale lembrar que isso já salvou o projeto: o `KeyError` do `seed_cursos` que revertia os 20 cursos em silêncio ([[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Descoberta do seed]]) teria sido pego no primeiro `manage.py test`.

### `quiz/tests/test_engine_puro.py` — a suíte que se perdeu, de volta

```python
from django.test import SimpleTestCase

from quiz.engine import confianca, cosseno


class MatematicaTest(SimpleTestCase):
    """SimpleTestCase: nao abre banco, roda em milissegundos.

    Isso so e possivel porque a engine tem funcoes puras separadas do ORM --
    a decisao do Passo 4 se pagando, e um paragrafo pronto para a monografia.
    """

    def test_vetores_identicos_dao_1(self):
        self.assertAlmostEqual(cosseno({"ti": 3}, {"ti": 3}), 1.0)

    def test_sem_area_em_comum_da_0(self):
        self.assertAlmostEqual(cosseno({"ti": 3}, {"costura": 3}), 0.0)

    def test_vetor_vazio_nao_estoura(self):
        """Guarda do divisor zero: quiz em branco."""
        self.assertAlmostEqual(cosseno({}, {"ti": 3}), 0.0)

    def test_escala_nao_muda_o_score(self):
        """O teste que protege a DECISAO de usar cosseno, nao uma linha de codigo.

        Dobra todos os pesos do perfil e exige o mesmo resultado. Se alguem
        trocar o cosseno por soma de produtos, este e o primeiro a quebrar.
        """
        perfil = {"ti": 3, "eletrica": 1}
        curso = {"ti": 2, "eletrica": 2}
        self.assertAlmostEqual(
            cosseno(perfil, curso),
            cosseno({k: v * 2 for k, v in perfil.items()}, curso),
        )
```

> [!important] `test_escala_nao_muda_o_score` é o teste mais importante do repositório
> Ele não testa código — testa uma **decisão de projeto**. O cosseno foi escolhido para neutralizar o "curso gordo" que pesa muitas áreas, e essa propriedade é o que a monografia defende no capítulo de metodologia.
> Esse teste é a única coisa no projeto que impede alguém trocar o cálculo por uma soma de pontos — que é mais simples de entender e **erraria de um jeito plausível**, sem quebrar nada visivelmente.

### O desempate — a única mudança que esta fase manda de volta para a Fase 2

`test_resultado_e_reprodutivel` exige mesma entrada, mesma saída. O desempate hoje é **por nome**, e ordenação com acento muda entre MySQL e Postgres ([[Projetos/EducMatch(Secretária)/passo-a-passo-sb-01-sb-06|SB-04, diferença 3]]) — então o teste pode passar na sua máquina e falhar na CI.

```python
# quiz/engine.py — desempate estavel em qualquer banco
ranking.sort(key=lambda r: (-r.afinidade, r.curso_id))
```

> [!warning] Isto é `quiz/engine.py`, e a regra do plano diz que engine é da Fase 2
> A regra existe para que duas branches não disputem o mesmo arquivo, e ela vale aqui. Duas saídas legítimas:
> - se a Fase 2 ainda não foi mesclada, **entre na REC** como uma sétima tarefa;
> - se já foi, abra um `fix/motor-desempate` de um commit, com aprovação da F2, e mescle antes de continuar esta fase.
>
> O que **não** fazer é mudar `engine.py` dentro da `test/contratos` "porque é uma linha". É assim que a fronteira entre frentes deixa de valer — e a auditoria já mostrou o que acontece com contrato que ninguém honra.

> [!note] `.sort()` muta e devolve `None`
> `rank_courses` sem `return` já custou um `TypeError: 'NoneType' object is not subscriptable` neste projeto ([[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições, Passo 4]]). Se for reescrever essa função, confira o `return`.

---

## 2️⃣ TST-02 — a camada REST: consertar, depois cobrir

Os três endpoints respondem **500** (`REV-05`). Não é um contrato quebrado — é uma API que nunca funcionou e que ninguém abriu.

### A decisão, primeiro

| Opção | Custo | Consequência |
|---|---|---|
| **Consertar** | ~1 h | a API volta a valer; `api-quiz-drf` deixa de ser nota mentirosa |
| Remover as rotas | 10 min | a API sai do escopo; a `F2-09` reintroduz DRF depois, do zero |

**Consertar.** Três razões: (1) [[Projetos/EducMatch(Secretária)/api-quiz-drf|🔌 API REST do quiz]] está marcada como entrega concluída, e nota que descreve 500 é pior do que nota nenhuma; (2) a [[Projetos/EducMatch(Secretária)/passo-a-passo-f2-09|F2-09]] vai construir o endpoint de entrega do `C3` **neste mesmo app**, e ela não começa bem sobre um DRF que nunca subiu; (3) três endpoints públicos estourando 500 é pior do que não ter API — a banca pode abrir.

### Os cinco defeitos

```python
# core/settings.py
INSTALLED_APPS = [
    ...
    "rest_framework",        # 1. nao estava aqui
    "quiz",
    "catalogo",
    "accounts",
    "painel",
]
```

```python
# quiz/views.py
class QuestaoList(ListAPIView):
    queryset = Questao.objects.filter(is_active=True)
    serializer_class = QuestaoSerializer      # 2. era `Questao`, o MODEL
```

```python
# quiz/views.py — 3. RetrieveAPIView numa rota sem pk
class ResultadoTentativa(RetrieveAPIView):
    queryset = Tentativa_de_resposta.objects.all()
    serializer_class = TentativaSerializer
    # e a rota passa a ser:  path("resultado/<int:pk>/", ...)
```

```python
# quiz/views.py — 4. e 5.
tentativa = Tentativa_de_resposta.objects.create(user=None)   # era `usuario=`
recomendar(tentativa)                                          # era `Recomendacao(tentativa)`
```

> [!danger] `serializer_class = Questao` é o erro que ensina a ler a mensagem
> ```
> TypeError: Questao() got unexpected keyword arguments: 'many'
> ```
> "`got unexpected keyword arguments: 'many'`" diz exatamente o que aconteceu: o DRF chamou `serializer_class(many=True)`, e quem estava ali era um **model**, que não aceita `many`. A mensagem parece obscura e é literal.

### O defeito que não dá erro nenhum — e é o mais grave

Os serializers têm `validar` e `validar_resposta` onde o DRF procura `validate` e `validate_<campo>`.

```python
# ANTES — escrito, e morto
class EnvioQuizSerializer(serializers.Serializer):
    respostas = ...

    def validar_resposta(self, valor):     # o DRF nunca chama isto
        ...
```

```python
# DEPOIS
    def validate_respostas(self, valor):   # o nome que o DRF procura
        ...
```

> [!danger] Validação escrita e morta em silêncio — a mesma lição, pela segunda vez
> [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições, Passo 5]] já registrou este padrão exato: o campo se chamava `answer` em vez de `answers`, então `validate_answers` **nunca rodava** — e a regra que barrava pergunta duplicada existia no arquivo e não existia no sistema.
> O defeito voltou na reescrita para o português, porque `validar` é a tradução natural de `validate` e **não dá erro**. O DRF não avisa que existe um método parecido com o que ele procura.
> Vale virar item permanente da revisão: **todo método de validação de serializer é conferido contra o nome que o DRF procura.** E a partir desta fase existe um teste que confere.

### `quiz/tests/test_api.py`

```python
from rest_framework import status

from quiz.tests.base import BaseEducMatch


class ApiQuizTest(BaseEducMatch):
    def test_lista_de_questoes_responde_200(self):
        """REV-05: este endpoint respondia 500 desde sempre."""
        resposta = self.client.get("/api/quiz/questoes/")
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.json()), 6)

    def test_envio_completo_gera_cinco_recomendacoes(self):
        resposta = self.client.post("/api/quiz/enviar/", self.payload_valido(), format="json")
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(resposta.json()["recomendacoes"]), 5)

    def test_duas_respostas_para_a_mesma_questao_da_400_e_nao_500(self):
        """O guardiao do validate_<campo>: se o metodo se chamar `validar`,
        a validacao nao roda, o unique_together estoura e isto vira 500."""
        payload = self.payload_valido()
        payload["respostas"].append(payload["respostas"][0])

        resposta = self.client.post("/api/quiz/enviar/", payload, format="json")

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quiz_incompleto_da_400(self):
        """O JS impede avancar sem responder; curl ignora o JS."""
        payload = self.payload_valido()
        payload["respostas"] = payload["respostas"][:2]

        resposta = self.client.post("/api/quiz/enviar/", payload, format="json")

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
```

> [!important] `test_duas_respostas_para_a_mesma_questao_da_400_e_nao_500` é o teste que o nome errado do método desliga
> Se alguém reverter `validate_respostas` para `validar_respostas`, este teste passa de verde para vermelho imediatamente — porque sem a validação o `unique_together` estoura e o DRF devolve 500 em vez de 400.
> É o padrão desta fase inteira: **para cada defeito silencioso, um teste que o torna audível.**

> [!note] O `C3` de verdade não é este endpoint
> O `C3` é o **endpoint de entrega** que a [[Projetos/EducMatch(Secretária)/passo-a-passo-f2-09|F2-09]] vai construir, e hoje o papel dele é feito por `quiz/web_views.py:105`. O que a TST-02 faz é deixar o DRF funcionando para que a F2-09 comece de um lugar limpo — e escrever, na TST-05, o teste de conformidade que ela vai fazer passar.

---

## 3️⃣ TST-03 — `C5`: a matriz de rotas e autorização

O `C5` é o contrato que **conformou na parte que importa**: os nomes de rota derivaram, a regra de acesso foi honrada ([[contratos-c1-a-c6 🟢|📜 C5]]). O trabalho aqui é congelar a regra e limpar o que o `REV-08` encontrou.

### A limpeza (`REV-08`)

```bash
grep -rn "remover_interesse\|interesse_remover" --include="*.py" .
grep -rn "salvar" accounts/urls.py
```

- `remover_interesse` e `interesse_remover` são **a mesma view** duplicada — apague uma e ajuste a rota.
- A rota `lista_interesse/<pk>/salvar/` aponta para uma view que **não aceita `pk`** e estoura ao ser chamada. Ou a view passa a aceitar, ou a rota sai.
- `autcomplete_fields` está grafado errado no admin — ignorado sem aviso.
- `STATIC_URL` declarado duas vezes; `MAILERS` não é configuração do Django.

> [!warning] Rota que aponta para view incompatível é 500 esperando alguém clicar
> E o clique não vem de quem escreveu: vem de um colega testando, ou da banca explorando a URL. Testar o `C5` significa **percorrer todas as rotas** — e é nessa passada que essa rota aparece, porque é a única que não consegue nem ser chamada.

### `accounts/tests/test_c5_rotas.py`

```python
from django.test import TestCase
from django.urls import reverse

from accounts.tests_helpers import criar_usuario   # ou reaproveite a Base


class C5AutorizacaoTest(TestCase):
    """C5 -- Rotas e autorizacao.

    Tres perguntas por rota protegida:
      anonimo  -> e mandado para o login
      outro    -> NAO ve (e nao descobre que existe)
      dono     -> ve
    """

    ROTAS_PROTEGIDAS = [
        ("interesse-lista", {}),
        ("minhas-tentativas", {}),
        ("aluno-perfil", {}),
    ]

    def setUp(self):
        self.dono = criar_usuario("dono@exemplo.com")
        self.outro = criar_usuario("outro@exemplo.com")

    def test_anonimo_e_redirecionado_em_toda_rota_protegida(self):
        for nome, kwargs in self.ROTAS_PROTEGIDAS:
            with self.subTest(rota=nome):
                resposta = self.client.get(reverse(nome, kwargs=kwargs))
                self.assertEqual(resposta.status_code, 302)
                self.assertIn("/entrar/", resposta["Location"])

    def test_resultado_de_outro_usuario_da_404_e_nao_403(self):
        """404 de proposito: 403 confirma que a tentativa existe."""
        tentativa = self.criar_tentativa(dono=self.dono)
        self.client.force_login(self.outro)

        resposta = self.client.get(reverse("quiz-resultado", kwargs={"pk": tentativa.pk}))

        self.assertEqual(resposta.status_code, 404)

    def test_dono_ve_o_proprio_resultado(self):
        tentativa = self.criar_tentativa(dono=self.dono)
        self.client.force_login(self.dono)

        resposta = self.client.get(reverse("quiz-resultado", kwargs={"pk": tentativa.pk}))

        self.assertEqual(resposta.status_code, 200)

    def test_toda_rota_de_escrita_recusa_GET(self):
        """Salvar interesse e sair sao POST. Link que faz GET e 405, nao acao."""
        self.client.force_login(self.dono)
        for nome in ("interesse-salvar", "sair"):
            with self.subTest(rota=nome):
                resposta = self.client.get(reverse(nome))
                self.assertIn(resposta.status_code, (405, 302))
```

> [!important] `404` e não `403` — e isto é decisão de segurança, não de estilo
> `403 Forbidden` responde *"existe, e você não pode"*. `404` responde *"não existe para você"*. Num sistema em que a URL é `/resultado/34/`, o 403 permite a qualquer pessoa logada descobrir **quantas tentativas existem** e quais ids estão ocupados, incrementando o número.
> O `C5` já acertou isso no código de produção; o teste é o que impede alguém "melhorar a mensagem de erro" e regredir. É o tipo de mudança que passa em revisão porque parece gentileza com o usuário.

> [!tip] `subTest` em vez de quatro testes iguais
> Com `subTest`, uma rota falhando **não interrompe** as outras, e a saída diz qual falhou. Quatro testes copiados dariam o mesmo resultado com quatro vezes o código — e no dia em que a quinta rota nascer, alguém vai esquecer de copiar. Acrescentar uma linha na lista `ROTAS_PROTEGIDAS` é difícil de esquecer.

---

## 4️⃣ TST-04 — `C6`: o *claim* que nunca existiu

O `C6` é *"o contrato mais bem argumentado dos seis, e o único cujo coração não foi implementado"*. Os passos 1, 2 e 4 do fluxo estão no código. **O passo 3 — a adoção da tentativa — não existe em lugar nenhum.**

Consequência verificável hoje: quem responde o quiz anônimo, cria conta e abre `/meus-testes/` **não vê nada**. A tentativa tem `user = None` para sempre.

### `accounts/signals.py` — o arquivo inteiro, reescrito

O arquivo atual tem três defeitos empilhados: consulta `Questao` com ids de `Tentativa`, descarta o resultado, e nunca é executado.

```python
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from quiz.models import Tentativa_de_resposta


@receiver(user_logged_in)
def adotar_tentativas_da_sessao(sender, request, user, **kwargs):
    """C6 -- passo 3: a tentativa anonima ganha dono ao entrar.

    Duas condicoes, as duas obrigatorias:
      1. o id esta na sessao DESTE navegador  -> nao adota tentativa alheia
      2. a tentativa ainda nao tem dono       -> nao readota a ja adotada
    """
    ids = request.session.get("minhas_tentativas", [])
    if not ids:
        return

    Tentativa_de_resposta.objects.filter(
        id__in=ids,
        user__isnull=True,
    ).update(user=user)
```

### `accounts/apps.py` — sem isto, o arquivo acima nunca roda

```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        # Sem este import o modulo nunca e carregado e o @receiver nunca se
        # registra -- exatamente o terceiro defeito do REV-08.
        from accounts import signals  # noqa: F401
```

> [!danger] `@receiver` num módulo que ninguém importa é código que **não existe**
> Este é o defeito mais instrutivo do repositório inteiro: o arquivo está lá, o decorador está correto, o `git blame` mostra que alguém pensou no problema — e nada acontece, porque o Python nunca importa o módulo. Sem erro, sem aviso, sem log.
> A regra: **todo `signals.py` precisa de um `import` no `ready()` do `AppConfig` correspondente.** Se o `INSTALLED_APPS` lista `"accounts"` em vez de `"accounts.apps.AccountsConfig"`, confira se o Django está achando a sua `AppConfig` — nas versões atuais ele acha automaticamente, mas vale o `manage.py shell` para confirmar.

> [!important] As duas condições do filtro são a regra de segurança do `C6`
> *"O claim só acontece para tentativas que estão na sessão daquele navegador **e** cujo `user` ainda é `None`."*
> Sem a primeira, qualquer pessoa logada adotaria tentativa alheia mandando ids na mão. Sem a segunda, adotaria as já adotadas de outra pessoa.
> O código de produção **já tinha as duas condições implementadas** — mas em `resultado_pagina`, para decidir se mostra a página, não num *claim*. A auditoria chamou isso de contrato parcialmente internalizado: *a lógica de autorização do C6 existe; o efeito do C6 não.* Um `.update()` de três linhas fecha o contrato.

> [!tip] `.update()` em vez de laço com `save()`
> Uma consulta em vez de N, e sem disparar `save()` em cada objeto — que, num sinal de login, seria o caminho mais curto para um efeito colateral inesperado. O `update()` também aplica o filtro **no banco**, de forma atômica: não há janela entre ler e escrever.

### `accounts/tests/test_c6_claim.py`

```python
from django.urls import reverse

from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class C6ClaimTest(BaseEducMatch):
    """C6 -- claim da tentativa anonima."""

    def test_tentativa_anonima_ganha_dono_ao_criar_conta(self):
        """O caminho completo: responde anonimo, cria conta, ve no historico."""
        self.responder_tudo(nome="Visitante")
        tentativa = Tentativa_de_resposta.objects.latest("id")
        self.assertIsNone(tentativa.user)

        self.client.post(
            reverse("criar-conta"),
            {
                "first_name": "Ana",
                "email": "ana@exemplo.com",
                "password1": "afinidade-2026",
                "password2": "afinidade-2026",
            },
        )

        tentativa.refresh_from_db()
        self.assertIsNotNone(tentativa.user)
        self.assertEqual(tentativa.user.email, "ana@exemplo.com")

    def test_historico_mostra_a_tentativa_adotada(self):
        """A consequencia verificavel que hoje devolve vazio."""
        self.responder_tudo()
        self.client.post(reverse("criar-conta"), self.dados_de_cadastro())

        resposta = self.client.get(reverse("minhas-tentativas"))

        self.assertEqual(len(resposta.context["tentativas"]), 1)

    def test_nao_adota_tentativa_que_nao_esta_na_minha_sessao(self):
        """Condicao 1: sem ela, ids na mao adotariam tentativa alheia."""
        outro_navegador = self.client_class(SERVER_NAME="localhost")
        outro_navegador.post("/", self.payload_do_quiz())
        alheia = Tentativa_de_resposta.objects.latest("id")

        self.client.post(reverse("criar-conta"), self.dados_de_cadastro())

        alheia.refresh_from_db()
        self.assertIsNone(alheia.user)

    def test_nao_readota_tentativa_que_ja_tem_dono(self):
        """Condicao 2: uma vez adotada, nao troca de dono."""
        primeiro = self.criar_usuario("primeiro@exemplo.com")
        tentativa = self.criar_tentativa(dono=primeiro)
        sessao = self.client.session
        sessao["minhas_tentativas"] = [tentativa.pk]
        sessao.save()

        self.client.post(reverse("criar-conta"), self.dados_de_cadastro())

        tentativa.refresh_from_db()
        self.assertEqual(tentativa.user, primeiro)
```

> [!important] Os dois últimos testes são os que provam que o contrato foi lido, e não só implementado
> Qualquer pessoa escreve o primeiro teste — é o caminho feliz. Os dois últimos são as **condições de segurança** do `C6`, e a única forma de tê-los é ter lido o contrato.
> Escrever esses dois é o que transforma *"implementei o claim"* em *"implementei o C6"*. É a diferença que esta fase inteira existe para demonstrar, e é material direto para o artigo.

> [!warning] O quiz anônimo continua tendo de funcionar
> A [[Projetos/EducMatch(Secretária)/passo-a-passo-aut-01-aut-03|AUT-01]] deixou um teste guardando a **D2** (*"o quiz continua anônimo"*). Se ele não existe mais, recrie-o nesta fase: é o único teste que defende uma decisão de produto sozinho, e o `C6` é justamente a área onde alguém pode pôr um `login_required` um nível acima do que devia.

---

## 5️⃣ TST-05 — o manifesto de conformidade, a CI e a `main`

### `quiz/tests/test_contratos.py` — a saída do teste vira a tabela do artigo

```python
import unittest

from django.test import SimpleTestCase

from accounts.models import Interesse
from quiz.models import Recomendacao, Tentativa_de_resposta


class ConformidadeDosContratos(SimpleTestCase):
    """Um teste por contrato. A saida de `manage.py test -v 2` E a tabela
    de conformidade -- gerada, nao afirmada.

    Contrato ainda nao implementado usa `skip` com a razao. Skip aparece no
    relatorio a cada execucao, entao a pendencia fica visivel em vez de
    silenciosa -- que foi exatamente o problema da v0.1.
    """

    @unittest.skip("C1: build_payload chega com o Passo 7 da camada de IA")
    def test_c1_build_payload_existe_e_tem_os_campos_do_contrato(self):
        from quiz.engine import build_payload  # noqa

    @unittest.skip("C2: saida da LLM e as 5 regras chegam com o Passo 8")
    def test_c2_saida_da_llm_passa_pelas_cinco_regras(self):
        pass

    @unittest.skip("C3: endpoint de entrega chega com a F2-09")
    def test_c3_endpoint_de_entrega_responde_no_formato_do_contrato(self):
        pass

    def test_c4_interesse_tem_os_tres_campos_de_snapshot(self):
        campos = {f.name for f in Interesse._meta.get_fields()}
        for exigido in ("afinidade_snapshot", "rank_snapshot", "era_principal"):
            with self.subTest(campo=exigido):
                self.assertIn(exigido, campos)

    def test_c4_garantias_estruturais_continuam_de_pe(self):
        """PROTECT no curso, SET_NULL na tentativa, unico por (usuario, curso)."""
        curso = Interesse._meta.get_field("curso")
        origem = Interesse._meta.get_field("tentativa_origem")

        self.assertEqual(curso.remote_field.on_delete.__name__, "PROTECT")
        self.assertEqual(origem.remote_field.on_delete.__name__, "SET_NULL")
        self.assertTrue(
            any(
                set(getattr(c, "fields", [])) == {"usuario", "curso"}
                for c in Interesse._meta.constraints
            )
        )

    def test_c4_criado_em_nao_e_auto_now(self):
        """REV-01: a diferenca de uma palavra que invalidava a serie temporal."""
        campo = Interesse._meta.get_field("criado_em")
        self.assertTrue(campo.auto_now_add)
        self.assertFalse(campo.auto_now)

    def test_c6_o_claim_esta_conectado(self):
        """Sem o import no ready() do AppConfig, o receiver nao existe."""
        from django.contrib.auth.signals import user_logged_in

        registrados = [r[1]() for r in user_logged_in.receivers]
        nomes = {getattr(f, "__name__", "") for f in registrados if f}
        self.assertIn("adotar_tentativas_da_sessao", nomes)
```

> [!success] `skip` com razão, em vez de teste ausente
> Um contrato não implementado que **não tem teste** é invisível. Um que tem `skip` com a razão escrita aparece no relatório a cada execução:
> ```
> test_c1_build_payload ... skipped 'C1: build_payload chega com o Passo 7 da camada de IA'
> ```
> A pendência passa a se anunciar sozinha, e quando a F2 implementar o Passo 7, o caminho é apagar um `@unittest.skip` — não descobrir que havia um teste para escrever.
> É a resposta direta ao achado central da auditoria: os desvios sobreviveram porque **não havia nome comum para procurar**. Agora há um arquivo, e ele fala.

> [!important] `test_c6_o_claim_esta_conectado` testa a fiação, não o comportamento
> Os testes da TST-04 já cobrem o comportamento. Este cobre a causa do defeito original: o `@receiver` existia e **nunca se registrava**. É um teste sobre o Django, não sobre o negócio — e é exatamente por isso que ele pega o que os outros não pegam.

### `.github/workflows/test.yml` — o que faltava quando a suíte se perdeu

```yaml
name: testes
on: [pull_request, push]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: educmatch_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready --health-interval 10s
          --health-timeout 5s --health-retries 5

    env:
      DJANGO_SECRET_KEY: chave-de-ci-sem-valor-em-producao
      DJANGO_DEBUG: "false"
      DJANGO_ALLOWED_HOSTS: localhost,127.0.0.1,testserver
      DATABASE_URL: postgresql://postgres:postgres@localhost:5432/educmatch_test
      PYTHONIOENCODING: utf-8
      LLM_ENABLED: "false"

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python manage.py makemigrations --check --dry-run
      - run: python manage.py test -v 2
```

> [!danger] O `services: postgres` é o que torna a CI honesta
> Sem ele a única saída seria rodar em SQLite — e a CI passaria a garantir menos do que a sua máquina. As quatro diferenças MySQL → Postgres da [[Projetos/EducMatch(Secretária)/passo-a-passo-sb-01-sb-06|SB-04]] existem justamente para não serem descobertas na véspera.
> **Nunca aponte a CI para o Supabase.** Cada PR criaria e apagaria um banco no servidor compartilhado, com quatro pessoas abrindo PR na mesma tarde.

> [!important] `makemigrations --check --dry-run` como passo separado, antes do teste
> É o passo que pega o esquecimento mais comum do Django: mudar o `models.py` e não gerar a migração. Sem ele, os testes passam (o Django cria as tabelas a partir do `models.py`) e o `migrate` de outra pessoa falha depois. O erro aparece para quem não cometeu.

> [!note] `LLM_ENABLED=false` na CI não é detalhe
> Sem isso, cada PR chamaria o Gemini de verdade: gasta *free tier*, deixa o teste lento e o torna dependente de rede — um PR reprovaria por instabilidade da API, não por bug. É exatamente para isso que o `FakeProvider` existe ([[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 Plano da camada de IA]]). A variável já entra aqui, antes de o provedor existir, para que o dia em que ele existir não exija mexer na CI.

### A proteção da `main` — cinco minutos, e a suíte nunca se perde de novo

Em **Settings → Branches → Add rule**, para a `main`:

- [ ] Require a pull request before merging
- [ ] Require approvals: **1**
- [ ] **Require status checks to pass** → marcar `testes`
- [ ] Automatically delete head branches

> [!danger] O terceiro item é a razão de existir desta fase inteira
> A suíte de 12 testes se perdeu numa reescrita porque **nada rodava `manage.py test`**. Escrever 40 testes novos sem esse marcador é repetir a história com mais código.
> Com "Require status checks", um PR que apaga testes ou que os quebra **não consegue ser mesclado**. É a única linha deste plano que protege o plano de si mesmo.

---

## 6️⃣ Verificação

```bash
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/educmatch_test \
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe manage.py test -v 2
```

A saída com `-v 2` é o relatório de conformidade. Guarde-a — é anexo de monografia:

```
test_c4_interesse_tem_os_tres_campos_de_snapshot ... ok
test_c4_garantias_estruturais_continuam_de_pe ... ok
test_c4_criado_em_nao_e_auto_now ... ok
test_c6_o_claim_esta_conectado ... ok
test_c1_build_payload ... skipped 'C1: chega com o Passo 7'
test_c2_saida_da_llm ... skipped 'C2: chega com o Passo 8'
test_c3_endpoint_de_entrega ... skipped 'C3: chega com a F2-09'
```

```bash
./.venv/Scripts/python.exe manage.py test -v 2 2>&1 | grep -c "\.\.\. ok"
./.venv/Scripts/python.exe manage.py test quiz.tests.test_contratos -v 2
```

E a verificação que nenhum comando faz: **quebre de propósito e veja o teste acusar.** Para cada um dos cinco abaixo, desfaça, rode a suíte, confirme o vermelho, refaça.

| # | Desfaça | Teste que tem de ficar vermelho |
|---|---|---|
| 1 | `validate_respostas` → `validar_respostas` | `test_duas_respostas...da_400_e_nao_500` |
| 2 | o `import signals` do `ready()` | `test_c6_o_claim_esta_conectado` |
| 3 | `auto_now_add` → `auto_now` em `criado_em` | `test_c4_criado_em_nao_e_auto_now` |
| 4 | `404` → `403` no acesso de outro usuário | `test_resultado_de_outro_usuario_da_404` |
| 5 | o cosseno por uma soma de produtos | `test_escala_nao_muda_o_score` |

> [!important] Este exercício é o único que prova que a suíte serve para algo
> Teste verde não prova nada por si: pode estar medindo a coisa errada, ou nada. Teste que **fica vermelho quando você quebra o que ele deveria proteger** prova.
> Faça os cinco, uma vez, antes de abrir o PR. Leva vinte minutos e é o parágrafo mais forte que a monografia pode ter sobre validação — porque descreve um experimento, com procedimento e resultado, e não uma intenção.

---

## 7️⃣ Commit, push, PR e o recado

```bash
git add -A
git commit -m "fix(api): conserta os tres endpoints DRF e os nomes de validate"
git commit -m "feat(contas): implementa o claim da tentativa anonima (C6)"
git commit -m "test(contratos): suite de conformidade C4/C5/C6 e matriz de rotas"
git commit -m "chore(ci): roda a suite contra Postgres em cada PR"
git push -u origin test/contratos
```

```markdown
## O que muda
Suite de testes reconstruida como pacote, com base comum e seeds como fixture.
Conserta REV-05 (3 endpoints em 500) e REV-08 (rota morta, view duplicada,
signals nunca conectado). Implementa o claim do C6. Manifesto de conformidade
C1..C6. CI rodando a suite contra Postgres em cada PR.

## Por quê
Os tres tests.py estavam vazios: a suite de 12 testes descrita na nota de
17/08 se perdeu na reescrita para o portugues e ninguem percebeu, porque nada
rodava manage.py test. O C6 estava escrito e nunca executava.

## Como testar
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/educmatch_test \
PYTHONIOENCODING=utf-8 manage.py test -v 2
Responder o quiz anonimo, criar conta, abrir /meus-testes/: a tentativa aparece.

## Toca contrato de outra frente? (x) sim → C3 (F2), C5 e C6 (contas/F4)
```

> [!danger] Este PR precisa de duas aprovações, e uma é a F2
> A TST-02 mexe em `quiz/serializers.py` e `quiz/views.py`, que é onde a [[Projetos/EducMatch(Secretária)/passo-a-passo-f2-09|F2-09]] vai construir o endpoint do `C3`. A TST-04 muda o comportamento de login, que é território de quem levou a trilha AUT.
> E o `test_contratos.py` é, na prática, **a definição operacional de "contrato cumprido"** neste projeto. Não é um arquivo para uma pessoa aprovar sozinha.

Recado para o grupo:

> Subi o PR da `test/contratos`. É o maior dos quatro, mas quase tudo é teste — o que muda de comportamento são três coisas.
>
> ```
> git checkout main && git pull
> ```
>
> **O que muda de verdade:**
>
> 1. **Os três endpoints da API voltaram a funcionar.** Estavam respondendo erro 500 desde sempre, e ninguém tinha aberto.
> 2. **Quem responde o quiz sem estar logado e depois cria conta agora vê aquela tentativa em `/meus-testes/`.** Antes ficava perdida para sempre. Era o `C6`, o passo que faltava.
> 3. **A partir de agora, PR com teste vermelho não mescla.** Configurei a proteção da `main`.
>
> **Por que o item 3 importa:** a gente **tinha** 12 testes em agosto, descritos na nota de testes. Eles se perderam quando o código foi reescrito para o português, e ninguém percebeu por três semanas — porque nada rodava os testes automaticamente. Agora roda, em cada PR, contra um Postgres igual ao do Supabase.
>
> **Como rodar na sua máquina** (precisa do Postgres local, instruções no README):
>
> ```
> PYTHONIOENCODING=utf-8 python manage.py test -v 2
> ```
>
> Se algum teste ficar vermelho na sua máquina e verde na CI, **me chame antes de mexer no teste**. Quase sempre é `.env` faltando variável, não teste errado.
>
> 📌 **F2:** existe um `quiz/tests/test_contratos.py` com um teste por contrato. Os do `C1`, `C2` e `C3` estão como `skip`, com a razão escrita ("chega com o Passo 7 / 8 / F2-09"). Quando você implementar, é só apagar o `@unittest.skip` — o teste já está lá esperando, e é a definição de pronto daqueles passos.

---

## ▶️ Próxima ação

**Passo 7 da camada de IA — `LLMProvider` + `FakeProvider`, tudo offline.** As quatro fases deixaram exatamente o terreno que ele pedia:

| Pré-condição do Passo 7 | Onde foi resolvida |
|---|---|
| `.env` e carregamento de segredo já existirem | SB-01 |
| `REV-03` antes do Passo 8 (as `top_areas` em JSON) | REC-03 |
| `REV-04` antes do Passo 11 (o `confidence_level` que segmenta) | REC-04 |
| métrica de resultado por comportamento (`era_principal`) | REC-06 |
| **teste do motor antes do Passo 7** | TST-01 |

A última linha era a que a [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|spec do painel]] apontava como bloqueadora: *"se a LLM reordenar o top-5, é preciso saber que o ranking mudou por isso e não por acidente"*. Agora se sabe.

Ver [[Projetos/EducMatch(Secretária)/passo-a-passo-f2-01-f2-03|🔌 Passo a passo F2-01 a F2-03]].

## 📎 Veja também

- [[contratos-c1-a-c6 🟢|📜 Os contratos C1 a C6]] — o documento que esta fase transforma em comando
- [[Projetos/EducMatch(Secretária)/plano-execucao-v02-supabase-a-testes|🗺️ Plano v0.2]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 Fase 3 — painel]]
- [[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes e validação]] — a suíte de agosto, e o que dela volta na TST-01
- [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições]] — `validate` × `validar`, pela segunda vez
- [[Projetos/EducMatch(Secretária)/api-quiz-drf|🔌 API REST do quiz]] — atualizar depois da TST-02
- [[Projetos/EducMatch(Secretária)/passo-a-passo-f2-09|🔌 F2-09]] — quem vai apagar o `skip` do `C3`
- [[ci-github-actions|🤖 CI com GitHub Actions]] · [[git-protecao-e-permissoes|🔒 Proteção e permissões]]
- **Conceitos:** [[tst-testes-django|Testes em Django]] · [[Serializers|Serializers]] · [[REST API|REST API]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]] · [[Projetos|🚀 Projetos]]
