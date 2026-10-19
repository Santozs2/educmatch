"""Executor dos testes: para que a suíte nunca fale com uma LLM de verdade.

Sem ele, os testes herdam o .env de quem roda. Com LLM_ENABLED=1 no .env,
uma rodada fazia 111 chamadas reais ao provedor.
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