---
title: "Spec pré-IA 03 — configuração da LLM, cache no banco e CI"
aliases: ["PRE-03", "Config da LLM", "Cache no banco"]
tags: [tcc, spec, settings, cache, ci, ia]
status: proposto
projeto: TCC
branch: feature/config-llm
criado: 2026-09-30
---

> [!info] Plano: [[plano-pre-ia-git-flow|🚧 Pré-IA e Git Flow]] · Anterior: [[spec-pre-ia-02-empate|02 — empate]] · Plano da IA: [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 variáveis de ambiente]]

# ⚙️ PRE-03: configuração da LLM, cache no banco e CI

**Branch:** `feature/config-llm`, saindo da `develop` **com a 02 já mesclada**
**Risco:** baixo. Nenhuma migração de model (a tabela de cache é criada por comando).
**Testes ao final:** 86 (84 + 2 novos)

> [!abstract] O que esta branch faz
> Prepara o terreno que os Passos 7 e 9 assumem que existe, **sem nenhuma linha de LLM**:
> 1. As variáveis `LLM_*` lidas pelo `settings.py`, com a IA **desligada por padrão**.
> 2. O cache sai da memória e vai para o banco.
> 3. A CI roda com a IA desligada e o provedor falso, de forma explícita.

---

## 1️⃣ Por que o cache precisa sair da memória

> [!danger] Hoje não há `CACHES` no `settings.py`
> Sem essa configuração, o Django usa o `LocMemCache`, que fica na memória do processo. O plano da IA conta com o cache para ter **reprodutibilidade na banca**: rodar os perfis de demonstração antes, para que na hora a resposta saia igual e sem rede. Com `LocMemCache`, **basta reiniciar o `runserver` para perder tudo**. Isso vale também para o autoreload, que reinicia o processo a cada arquivo salvo.

O `DatabaseCache` guarda o cache numa tabela do MySQL: sobrevive a reinício e não precisa de Redis nem de serviço novo. O `LOCATION` é o nome da tabela.

## 2️⃣ `core/settings.py`: no fim do arquivo

```python


# Cache no banco: sobrevive a reinício do servidor. É ele que garante a mesma
# resposta da LLM para o mesmo perfil na banca (Passo 9).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "educmatch_cache",
    }
}

# Camada de IA. Desligada por padrão: sem .env, o sistema é o da engine pura.
# LLM_ENABLED=0 é o botão de pânico da defesa.
LLM_ENABLED = os.environ.get("LLM_ENABLED", "0") == "1"
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "fake")  # gemini | fake
LLM_MODEL = os.environ.get("LLM_MODEL", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "8"))
LLM_PROMPT_VERSION = os.environ.get("LLM_PROMPT_VERSION", "v1")
```

> [!important] Três escolhas que diferem do plano original
> | Plano da IA | Aqui | Por quê |
> |---|---|---|
> | `LLM_ENABLED=true` | `LLM_ENABLED=1`, padrão **`0`** | Segue o `DJANGO_DEBUG=1` que o projeto já usa. E desligada por padrão significa que quem clona o repositório e não configura nada tem o sistema funcionando, sem tentar chamar a rede |
> | `LLM_PROVIDER=gemini` | padrão **`fake`** | Se alguém ligar a IA sem configurar o provedor, cai no falso, e não num Gemini sem chave |
> | `LLM_MODEL=gemini-2.0-flash` | padrão **vazio** | O nome do modelo muda com o tempo. Deixar vazio obriga a conferir no AI Studio qual está disponível **no dia do Passo 9**, em vez de herdar um nome que pode já ter sido desativado |

> [!warning] A chave **nunca** vai para o `.env.example`
> `LLM_API_KEY=` fica vazio no exemplo. A chave real vive só no `.env` de quem for responsável por ela, e isso ainda está em aberto: é a pergunta 5 da [[decisao-camada-ia 🟢|🤖 decisão]]. O `.env` já está no `.gitignore` da raiz e do `backend/`.

## 3️⃣ `backend/.env.example`: acrescente no fim

```env
LLM_ENABLED=0
LLM_PROVIDER=fake
LLM_MODEL=
LLM_API_KEY=
LLM_TIMEOUT=8
LLM_PROMPT_VERSION=v1
```

## 4️⃣ `.github/workflows/test.yml`: no bloco `env:` do job

```yaml
    env:
      DJANGO_SECRET_KEY: so-para-a-ci
      DB_NAME: educmatch
      DB_USER: root
      DB_PASSWORD: raiz
      DB_HOST: 127.0.0.1
      DB_PORT: "3306"
      # A CI nunca chama a rede: gasta free tier e reprova PR por instabilidade da API.
      LLM_ENABLED: "0"
      LLM_PROVIDER: fake
```

> [!note] Por que declarar, se o padrão já é desligado
> Porque o padrão pode mudar num PR distraído. Com a variável escrita no workflow, a CI continua offline mesmo que alguém troque o padrão do `settings.py`. A spec TST já pedia isso e ainda não tinha sido feito.

> [!success] A CI não precisa de `createcachetable`
> O *test runner* do Django roda o `createcachetable` sozinho ao criar o banco de teste. Isso foi conferido: o teste abaixo passa sem nenhum passo novo no workflow.

## 5️⃣ `README.md`: seção "Como rodar"

Depois de `python manage.py migrate`, acrescente:

```bash
python manage.py createcachetable
```

E, depois da seção de configuração do `.env`, uma linha:

> As variáveis `LLM_*` controlam a camada de IA. Com `LLM_ENABLED=0` (o padrão), o resultado é o da engine pura.

---

## 6️⃣ Testes: acrescente ao fim de `core/tests.py`

```python


class CacheNoBanco(TestCase):
    """PRE-03: o cache da LLM tem de sobreviver a um reinício do servidor."""

    def test_cache_e_de_banco_e_a_tabela_existe(self):
        from django.core.cache import cache

        self.assertEqual(
            settings.CACHES["default"]["BACKEND"],
            "django.core.cache.backends.db.DatabaseCache",
        )
        cache.set("pre-ia", "ok", 30)
        self.assertEqual(cache.get("pre-ia"), "ok")


class ConfiguracaoDaLLM(TestCase):
    def test_variaveis_existem_com_o_tipo_certo(self):
        self.assertIsInstance(settings.LLM_ENABLED, bool)
        self.assertIn(settings.LLM_PROVIDER, {"gemini", "fake"})
        self.assertIsInstance(settings.LLM_TIMEOUT, float)
        self.assertTrue(settings.LLM_PROMPT_VERSION)
```

> [!tip] Por que não testar `LLM_ENABLED is False`
> O `settings.py` lê o seu `.env` local. Se amanhã você ligar a IA na sua máquina para o Passo 9, esse teste quebraria sem haver bug nenhum. O que a CI garante (desligada) está no workflow. O teste confere só **o tipo**, que não depende da máquina.

---

## ✅ Verificação

```bash
cd backend
python manage.py createcachetable                    # no banco local, uma vez
python manage.py test                                # 86 testes
python manage.py check                               # no issues
python -c "import os; os.environ['DJANGO_SETTINGS_MODULE']='core.settings'; import django; django.setup(); from django.conf import settings; print(settings.LLM_ENABLED, settings.LLM_PROVIDER)"
# False fake
```

## 📦 Commit e PR

```bash
git add -A
git commit -m "feat(config): variaveis da LLM, cache no banco e CI offline

- settings: LLM_* com a IA desligada por padrao; CACHES em DatabaseCache
- .env.example e README com LLM_* e createcachetable
- ci: LLM_ENABLED=0 e LLM_PROVIDER=fake explicitos"
git push -u origin feature/config-llm
gh pr create --base develop --fill
```

> [!success] Definition of Done
> 86 testes, CI verde, `.env.example` sem chave, cache persistindo depois de reiniciar o `runserver`. Para conferir à mão: `cache.set` no `shell`, reinicie o servidor e faça `cache.get`.
>
> Com esta branch mesclada, a `develop` está pronta para a release `0.4.0-pre-ia` (ver [[plano-pre-ia-git-flow|🚧 plano]]).
