---
title: "Spec U3 · Cold start: o site acorda em segundos, e não em quase 1 minuto"
aliases: ["U3", "Cold start", "preparar_producao", "Boot rápido no F1"]
tags: [tcc, spec, producao, azure, deploy, desempenho]
status: proposto
projeto: TCC
branch: fix/cold-start
criado: 2026-10-22
---

> [!info] Origem: [[spec-urgente-producao-v0.3.1|🚨 Spec urgente da produção, seção U3]] · Depende de: [[spec-deploy-github-actions|🚀 Deploy automático]] (já no ar desde a `v0.3.1`) · Próxima: [[spec-manutencao-ci-e-branches|🧹 Manutenção do CI e das branches]]

# ⚡ U3: o site acorda em segundos

**Branch:** `fix/cold-start`, saindo da `develop`
**Risco:** baixo. Nenhuma migração, nenhuma tela muda. O que muda é **o que roda quando o site liga**.
**Testes ao final:** a suíte de hoje **+ 6**

> [!abstract] O que esta branch faz
> No plano F1 do Azure, o site "dorme" depois de uns 20 minutos sem acesso, e o `startup.sh` roda **inteiro** a cada vez que ele acorda. Hoje isso leva de **45 a 53 s** até a primeira página aparecer. Esta branch:
> 1. Junta `migrate`, `createcachetable` e os 4 seeds num comando só, **`preparar_producao`**, que **só trabalha quando a versão no ar mudou**.
> 2. Tira o **`collectstatic`** do boot e passa para o **build** do `deploy.yml`.

> [!success] O código desta spec já foi rodado
> Aplicado numa cópia da `develop` (`e3f9955`): **224 testes** (218 + 6 novos), e o único erro é o do fuso, que depende do MySQL. `makemigrations --check` limpo, `bash -n startup.sh` ok e o `deploy.yml` validado como YAML. O banco preparado pelo comando novo saiu completo: 12 áreas, 20 cursos, 10 questões e 7 perguntas da avaliação.

---

## 📏 1. A medição: para onde vão os segundos

Na **mesma máquina**, com o mesmo SQLite, cada etapa rodando como um processo separado, como no `startup.sh`:

| Etapa | 1º boot (banco vazio) | **Boot ao acordar** (o caso de todo dia) |
|---|:-:|:-:|
| `migrate` | 4,6 s | 2,6 s |
| `createcachetable` | 1,9 s | 1,9 s |
| 4 seeds | 9,8 s | 9,3 s |
| **`collectstatic`** | **12,2 s** | **11,4 s** |
| **Total antes do gunicorn** | **28,5 s** | **25,3 s** |

> [!important] As duas causas
> 1. **`collectstatic` sozinho é quase metade do tempo.** Com o `CompressedManifestStaticFilesStorage`, ele **recomprime** todo o CSS e o JS a cada boot, mesmo sem nada ter mudado.
> 2. **Cada comando sobe o Django do zero** (cerca de 1,9 s cada) para depois concluir que não há nada a fazer: as migrações já foram aplicadas, a tabela de cache existe e os seeds são `update_or_create`.
>
> O F1 tem uma CPU bem mais lenta que a de um notebook, e por isso os 25 s daqui viram 45 a 53 s lá.

**Depois desta branch, na mesma máquina:**

| | Antes | Depois |
|---|:-:|:-:|
| Primeiro boot de uma versão nova (logo depois do deploy) | 28,5 s | **6,0 s** |
| **Boot ao acordar** | **25,3 s** | **2,3 s** (−91%) |

---

## 🧩 2. O código

### 2.1 `backend/quiz/management/commands/preparar_producao.py` (novo)

```python
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

# O que o startup.sh rodava a cada boot, um processo por comando. Os seeds usam
# update_or_create: rodar de novo não duplica nada, só gasta tempo.
ETAPAS = (
    ("migrate", {"interactive": False}),
    ("createcachetable", {}),
    ("seed_areas", {}),
    ("seed_cursos", {}),
    ("seed_questoes", {}),
    ("seed_avaliacao", {}),
)


class Command(BaseCommand):
    help = (
        "Prepara o banco para a versão no ar (migrate, cache e seeds), num processo só. "
        "Se o banco já foi preparado para esta versão, não faz nada: é o caso de quase "
        "todo boot, quando o site só acordou depois de dormir."
    )

    def add_arguments(self, parser):
        parser.add_argument("--forcar", action="store_true", help="Prepara mesmo que a versão não tenha mudado.")

    def handle(self, *args, forcar, **options):
        marcador = Path(settings.MARCADOR_PREPARO)
        versao = settings.VERSAO
        # "dev" não identifica um commit: sem VERSAO (deploy manual ou máquina local), sempre prepara.
        if not forcar and versao != "dev" and marcador.exists() and marcador.read_text(encoding="utf-8").strip() == versao:
            self.stdout.write(f"Banco já preparado para {versao}: nada a fazer.")
            return

        for nome, opcoes in ETAPAS:
            self.stdout.write(f"-> {nome}")
            call_command(nome, stdout=self.stdout, **opcoes)

        # Só depois de tudo dar certo: se uma etapa falhar, o próximo boot tenta de novo.
        marcador.parent.mkdir(parents=True, exist_ok=True)
        marcador.write_text(versao, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Banco preparado para {versao}."))
```

> [!note] 🎓 Por que comparar com a **versão** (o `VERSAO` do U2)
> O deploy grava o commit em `backend/VERSAO`. Depois de cada deploy a versão muda, então o comando roda as migrações da versão nova. Quando o site só acorda, a versão é a mesma e o comando sai em 2 segundos. Sem o `VERSAO` (deploy manual por zip, ou a máquina de quem desenvolve), a versão é `"dev"`, e o comando **sempre** prepara, o que é o comportamento seguro.

> [!note] 🎓 Por que o marcador só é gravado no fim
> Se um seed falhar no meio, o `startup.sh` para (`set -e`) e o marcador **não** é gravado. No próximo boot, o comando tenta tudo de novo. Há um teste para isso.

### 2.2 `backend/core/settings.py`, no fim

```python
# Onde o preparar_producao anota a versão para a qual o banco já foi preparado.
# No Azure, o startup.sh aponta para /home/data, que sobrevive a reinícios.
MARCADOR_PREPARO = os.environ.get("MARCADOR_PREPARO", str(BASE_DIR / ".versao-preparada"))
```

### 2.3 `backend/startup.sh`

Troque **tudo** entre `cd "$(dirname "$0")"` e o comentário do gunicorn por:

```bash
#!/bin/bash
# Inicialização no Azure App Service (Linux).
# O site "dorme" no plano F1 e roda este arquivo a cada vez que acorda, então
# ele precisa ser rápido: só o que mudou de versão para versão.
set -e
cd "$(dirname "$0")"

mkdir -p /home/data

# Migrate, cache e seeds num processo só, e só quando a versão no ar mudou.
# O marcador fica em /home/data, que sobrevive aos reinícios.
export MARCADOR_PREPARO=/home/data/.versao-preparada
python manage.py preparar_producao

# O collectstatic roda no build (deploy.yml). Aqui só se o pacote veio sem ele,
# como num deploy manual por zip.
[ -f staticfiles/staticfiles.json ] || python manage.py collectstatic --noinput
```

O bloco do `gunicorn` no fim **não muda**.

> [!warning] Por que o marcador fica em `/home/data`, e não ao lado do código
> Com o build do Oryx ligado, o App Service pode rodar o código a partir de uma pasta temporária, recriada a cada boot. Um marcador ali sumiria toda vez, e o ganho também. O `/home/data` é o disco persistente, o mesmo do SQLite.

### 2.4 `.gitignore`

Logo abaixo de `backend/VERSAO`:

```
backend/.versao-preparada
```

### 2.5 `.github/workflows/deploy.yml`: `collectstatic` no build

No job `deploy`, **troque** o passo "Pacote com o commit dentro" por estes três passos:

```yaml
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"

      # Sai do boot (startup.sh): comprimir os estáticos levava ~11 s a cada vez que o site acordava.
      # Sem o mysqlclient: o collectstatic não abre o banco, e assim o build não precisa do apt-get.
      - name: collectstatic no build
        working-directory: backend
        env:
          DJANGO_SECRET_KEY: so-para-o-build
          DJANGO_DEBUG: "0"
          DB_ENGINE: sqlite
          DB_NAME: /tmp/build.sqlite3
        run: |
          grep -v '^mysqlclient' requirements.txt > /tmp/requisitos-build.txt
          pip install -q -r /tmp/requisitos-build.txt
          python manage.py collectstatic --noinput
          test -f staticfiles/staticfiles.json

      - name: Pacote com o commit dentro (backend/VERSAO)
        run: |
          COMMIT=$(git rev-parse --short HEAD)
          echo "COMMIT=$COMMIT" >> "$GITHUB_ENV"
          git archive --format=zip -o pacote.zip \
            --add-virtual-file=backend/VERSAO:$COMMIT \
            HEAD -- backend requirements.txt
          zip -qr pacote.zip backend/staticfiles
          unzip -l pacote.zip | tail -1
```

> [!note] 🎓 `DJANGO_DEBUG: "0"` é obrigatório
> Com `DEBUG` ligado, o `settings.py` usa o armazenamento simples, que **não** gera o `staticfiles.json`. Sem esse arquivo, a produção (com `DEBUG` desligado) devolveria erro 500 em toda página. O `test -f` no fim do passo faz o build falhar **antes** de publicar, se isso acontecer.

> [!tip] O plano B continua funcionando
> Num deploy manual por zip, sem passar pelo GitHub, o pacote vem sem `staticfiles/`. O `startup.sh` percebe isso e roda o `collectstatic` como antes, e a versão `"dev"` faz o `preparar_producao` preparar o banco.

---

## 🧪 3. Testes: `backend/quiz/tests/test_preparar_producao.py` (novo)

```python
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from quiz.management.commands.preparar_producao import ETAPAS

CHAMAR = "quiz.management.commands.preparar_producao.call_command"


class PrepararProducaoTest(SimpleTestCase):
    """U3: o boot só prepara o banco quando a versão no ar muda."""

    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.marcador = Path(pasta.name) / "data" / ".versao-preparada"

    def preparar(self, versao, **opcoes):
        with override_settings(VERSAO=versao, MARCADOR_PREPARO=str(self.marcador)), \
                mock.patch(CHAMAR) as chamar:
            call_command("preparar_producao", stdout=StringIO(), **opcoes)
        return [chamada.args[0] for chamada in chamar.call_args_list]

    def test_primeiro_boot_prepara_tudo_e_grava_o_marcador(self):
        self.assertEqual(self.preparar("abc1234"), [nome for nome, _ in ETAPAS])
        self.assertEqual(self.marcador.read_text(encoding="utf-8"), "abc1234")

    def test_boot_da_mesma_versao_nao_faz_nada(self):
        self.preparar("abc1234")
        self.assertEqual(self.preparar("abc1234"), [])

    def test_versao_nova_prepara_de_novo(self):
        self.preparar("abc1234")
        self.assertEqual(self.preparar("def5678"), [nome for nome, _ in ETAPAS])
        self.assertEqual(self.marcador.read_text(encoding="utf-8"), "def5678")

    def test_sem_versao_sempre_prepara(self):
        self.preparar("dev")
        self.assertEqual(self.preparar("dev"), [nome for nome, _ in ETAPAS])

    def test_forcar_prepara_mesmo_sem_mudanca(self):
        self.preparar("abc1234")
        self.assertEqual(self.preparar("abc1234", forcar=True), [nome for nome, _ in ETAPAS])

    def test_etapa_que_falha_nao_grava_o_marcador(self):
        with override_settings(VERSAO="abc1234", MARCADOR_PREPARO=str(self.marcador)), \
                mock.patch(CHAMAR, side_effect=[None, RuntimeError("seed quebrou")]):
            with self.assertRaises(RuntimeError):
                call_command("preparar_producao", stdout=StringIO())
        self.assertFalse(self.marcador.exists())
```

> [!tip] 🎓 Por que o `mock.patch` no `call_command`
> O teste confere **a decisão** (preparar ou não), e não as migrações em si, que já são testadas pelo próprio Django. Trocar o `call_command` por um espião deixa os 6 testes instantâneos, e cada um diz exatamente quais etapas rodaram.

---

## ✅ 4. Verificação

**Local:**

```bash
cd backend
python manage.py test quiz.tests.test_preparar_producao   # 6 testes, OK
python manage.py test                                       # a suíte + 6
bash -n startup.sh                                          # sem saída = sintaxe ok
```

**Em produção, depois do merge na `main`** (o deploy é automático):

1. O workflow **deploy** fica verde. No passo "collectstatic no build", aparece `N static files copied`.
2. **Deixe o site dormir:** 25 minutos sem ninguém abrir.
3. Meça a primeira página:

```bash
curl -s -o /dev/null -w "HTTP %{http_code} em %{time_total}s\n" https://educmatch-7249.azurewebsites.net/
```

4. Anote o tempo aqui e na spec urgente (DoD do U3).

> [!warning] O que esta branch **não** consegue tirar
> Parte do cold start é do próprio Azure: acordar o contêiner do F1 e importar o Python. Isso não depende do código. Se, depois desta branch, a primeira página ainda passar de 20 s, o que sobra é do plano F1. As saídas, então, são:
> - **Aquecer** o site 5 minutos antes da banca: abrir a página e responder o quiz uma vez;
> - **Subir para o B1** só na semana da banca, para ter o *Always On*, pagando com o crédito do *Azure for Students*, e voltar para o F1 depois.

## 📦 5. Commit e PR

```bash
git switch develop && git pull
git switch -c fix/cold-start
# ... aplica a spec ...
git add backend/quiz/management/commands/preparar_producao.py backend/quiz/tests/test_preparar_producao.py backend/core/settings.py backend/startup.sh .gitignore .github/workflows/deploy.yml
git commit -m "fix(deploy): boot rapido no F1 - preparar_producao e collectstatic no build (U3)"
git push -u origin fix/cold-start
```

PR com base **`develop`**. Depois, a release para a `main` publica sozinha.

> [!success] Definition of Done
> - [ ] 6 testes novos verdes; a suíte inteira verde na CI
> - [ ] Deploy verde, com o passo "collectstatic no build"
> - [ ] O site abre normalmente depois do deploy, com CSS e JS carregando
> - [ ] **Boot ao acordar medido** depois de 25 minutos parado, com o tempo anotado
> - [ ] Abaixo de 20 s, **ou** a decisão sobre aquecer ou o B1 registrada
