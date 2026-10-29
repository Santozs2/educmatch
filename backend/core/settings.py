import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    return default


def _load_env_file():
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = [part.strip() for part in line.split("=", 1)]
        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


_load_env_file()

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-inseguro-troque-em-producao")
DEBUG = _env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1,0.0.0.0,testserver",
    ).split(",")
    if h and h.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o and o.strip()
]

if not DEBUG:
    # Atrás do proxy do Azure App Service o HTTPS termina no front-end.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'quiz',
    'catalogo',
    'accounts',
    'painel',
    'avaliacao',
]

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = 'entrar'
LOGIN_REDIRECT_URL = 'quiz-inicio'
LOGOUT_REDIRECT_URL = 'quiz-inicio'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.contexto.escola',
                'core.contexto.versao',
            ],
        },
    },
]


WSGI_APPLICATION = 'core.wsgi.application'

DB_ENGINE = os.environ.get("DB_ENGINE", "mysql")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "educmatch"),
        "USER": os.environ.get("DB_USER", "root"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "OPTIONS": {"ssl": {"ca": os.environ["DB_SSL_CA"]}} if os.environ.get("DB_SSL_CA") else {},
    }
}

# Com o gunicorn em threads (startup.sh), várias gravações chegam ao mesmo tempo.
# IMMEDIATE: a transação já pede a trava de escrita ao começar, e quem chega
# depois ESPERA a vez (até `timeout` segundos) em vez de falhar com "database is
# locked". Sem WAL: o /home do App Service é disco de rede.
# Medido: 0 gravações perdidas com 30 alunos ao mesmo tempo (scripts/carga_turma.py).
SQLITE_OPTIONS = {"timeout": 20, "transaction_mode": "IMMEDIATE"}

if DB_ENGINE == "sqlite":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "OPTIONS": SQLITE_OPTIONS,
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True 

USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Manifest só em produção: ele exige collectstatic, que os testes não rodam.
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
QUIZ_RECOMENDACAO_LIMIT = 5

ESCOLA = {
    "nome": os.environ.get("ESCOLA_NOME", "SENAI São José do Rio Preto · CFP 8.01 Antonio Devisate"),
    "endereco": os.environ.get("ESCOLA_ENDERECO", ""),
    "telefone": os.environ.get("ESCOLA_TELEFONE", ""),
}


# Cache no banco: sobrevive a reinício do servidor. É ele que garante a mesma
# resposta da LLM para o mesmo perfil na banca (Passo 9).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "educmatch_cache",
        # O padrão do Django é 300 entradas, e depois ele apaga um terço delas.
        "OPTIONS": {"MAX_ENTRIES": 10000},
    }
}

# Camada de IA. Desligada por padrão: sem .env, o sistema é o da engine pura.
# LLM_ENABLED=0 é o botão de pânico da defesa.
LLM_ENABLED = _env_bool("LLM_ENABLED", False)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "fake")  # fake | gemini | openai_compat
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")  # vazio + gemini = endereço do Gemini
LLM_MODEL = os.environ.get("LLM_MODEL", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "8"))
LLM_PROMPT_VERSION = os.environ.get("LLM_PROMPT_VERSION", "v1")
# Depois de um timeout ou provedor fora (429, 503, sem rede), o quiz para de
# chamar a LLM por estes segundos: os próximos alunos vão direto para a engine
# em vez de esperar LLM_TIMEOUT cada um. 0 desliga a pausa.
LLM_PAUSA = int(os.environ.get("LLM_PAUSA", "30"))

# O commit que está no ar. O deploy (deploy.yml) grava o arquivo VERSAO dentro
# do pacote; na máquina de quem desenvolve ele não existe e a versão é "dev".
_ARQUIVO_VERSAO = BASE_DIR / "VERSAO"
VERSAO = _ARQUIVO_VERSAO.read_text(encoding="utf-8").strip() if _ARQUIVO_VERSAO.exists() else "dev"
MARCADOR_PREPARO = os.environ.get("MARCADOR_PREPARO", str(BASE_DIR / ".versao-preparada"))