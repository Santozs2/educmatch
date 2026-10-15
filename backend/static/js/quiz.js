(function () {
    const form = document.querySelector("[data-quiz]");
    if (!form) return;

    const passos = Array.from(form.querySelectorAll("[data-passo]"));
    const analisando = document.querySelector("[data-analisando]");

    function passoAtual() {
        return passos.find((passo) => "#" + passo.id === location.hash);
    }

    let indiceAnterior = passos.indexOf(passoAtual());

    // 5. A direção precisa estar no form ANTES do # mudar: a pergunta nova
    //    aparece (e começa a animar) no mesmo instante em que o # troca.
    function marcarDirecao(destino) {
        form.dataset.direcao = destino < indiceAnterior ? "voltar" : "avancar";
    }

    function irPara(indice) {
        if (indice < 0 || indice >= passos.length) return;
        marcarDirecao(indice);
        location.hash = passos[indice].id;
    }

    function respondido(passo) {
        return Boolean(passo.querySelector("input[type=radio]:checked"));
    }

    function avisar(passo) {
        const aviso = passo.querySelector("[data-aviso]");
        if (!aviso) return;
        // Reinicia a animação de "tremer" mesmo se o aviso já estava na tela
        aviso.hidden = true;
        void aviso.offsetWidth;
        aviso.hidden = false;
    }

    // Links "Voltar"/"Próxima" entre perguntas: só marcam a direção; quem troca é o link.
    form.addEventListener("click", (evento) => {
        const link = evento.target.closest('a[href^="#questao-"]');
        if (!link) return;
        marcarDirecao(passos.findIndex((passo) => "#" + passo.id === link.hash));
    });

    // 1. Marcou a resposta: some o aviso, e quem avança é o "Próxima" ou o Enter.
    //    Avançar sozinho atrapalharia o teclado: as setas disparam "change" a cada toque.
    form.addEventListener("change", (evento) => {
        if (evento.target.type !== "radio") return;
        const passo = evento.target.closest("[data-passo]");
        const aviso = passo.querySelector("[data-aviso]");
        if (aviso) aviso.hidden = true;
        // Não avança automaticamente - o usuário deve clicar em "Próxima"
    });

    // 2. Enter avança em vez de enviar o formulário pela metade.
    form.addEventListener("keydown", (evento) => {
        if (evento.key !== "Enter") return;
        const passo = passoAtual();
        if (!passo) return;
        const indice = passos.indexOf(passo);
        if (indice === passos.length - 1) return; // na última, Enter envia mesmo
        evento.preventDefault();
        if (respondido(passo)) irPara(indice + 1);
        else avisar(passo);
    });

    // 3. Pergunta nova na tela: o foco vai para o enunciado.
    //    Também cobre o voltar/avançar do navegador, que não passa pelos links.
    window.addEventListener("hashchange", () => {
        const passo = passoAtual();
        if (!passo) return;
        const indice = passos.indexOf(passo);
        marcarDirecao(indice);
        indiceAnterior = indice;
        passo.querySelector("legend").focus({ preventScroll: true });
        window.scrollTo(0, 0);
    });

    // 4. Enviou: a tela "Analisando" cobre tudo enquanto o servidor calcula.
    //    Se faltar resposta, volta para a primeira pergunta em branco.
    form.addEventListener("submit", (evento) => {
        const vazio = passos.find((passo) => !respondido(passo));
        if (vazio) {
            evento.preventDefault();
            irPara(passos.indexOf(vazio));
            avisar(vazio);
            return;
        }
        // Mostra o spinner de análise
        if (analisando) analisando.hidden = false;
        // Impede o envio imediato para mostrar o spinner por mais tempo
        evento.preventDefault();
        // Delay de 1,5 segundos antes de enviar realmente o formulário
        setTimeout(() => {
            form.submit();
        }, 1500);
    });
})();
