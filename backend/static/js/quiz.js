// Melhorias do quiz com JavaScript. SEM JS o quiz funciona igual: cada pergunta é
// um #questao-N, os links "Próxima"/"Voltar" trocam o # da URL e o CSS (:target)
// mostra só a pergunta da vez. Este arquivo só acrescenta conforto:
//   1. marcou a resposta com o mouse ou o dedo -> avança sozinho;
//   2. Enter avança em vez de enviar o formulário pela metade;
//   3. o foco vai para a pergunta nova (leitor de tela anuncia);
//   4. no envio, mostra a tela "Analisando seu perfil".
(function () {
    const form = document.querySelector("[data-quiz]");
    if (!form) return;

    const passos = Array.from(form.querySelectorAll("[data-passo]"));
    const analisando = document.querySelector("[data-analisando]");

    function passoAtual() {
        return passos.find((passo) => "#" + passo.id === location.hash);
    }

    function irPara(indice) {
        if (indice >= 0 && indice < passos.length) location.hash = passos[indice].id;
    }

    function respondido(passo) {
        return Boolean(passo.querySelector("input[type=radio]:checked"));
    }

    function avisar(passo) {
        const aviso = passo.querySelector("[data-aviso]");
        if (aviso) aviso.hidden = false;
    }

    // No teclado, as setas trocam a opção marcada e disparam "change" a cada toque.
    // Avançar sozinho aí jogaria a pessoa para a próxima pergunta antes de escolher:
    // no teclado, quem avança é o Enter.
    let pelaTeclado = false;
    form.addEventListener("pointerdown", () => { pelaTeclado = false; });
    form.addEventListener("keydown", () => { pelaTeclado = true; });

    // 1. Marcou a resposta com o mouse/dedo: segue sozinho, com uma pausa para o clique ser visto.
    form.addEventListener("change", (evento) => {
        if (evento.target.type !== "radio") return;
        const passo = evento.target.closest("[data-passo]");
        const aviso = passo.querySelector("[data-aviso]");
        if (aviso) aviso.hidden = true;
        const indice = passos.indexOf(passo);
        if (!pelaTeclado && indice < passos.length - 1) setTimeout(() => irPara(indice + 1), 320);
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
    window.addEventListener("hashchange", () => {
        const passo = passoAtual();
        if (passo) passo.querySelector("legend").focus({ preventScroll: true });
        window.scrollTo(0, 0);
    });

    // 4. Enviou: a tela "Analisando" cobre tudo enquanto o servidor calcula.
    //    Se faltar resposta, volta para a primeira pergunta em branco.
    form.addEventListener("submit", (evento) => {
        const vazio = passos.find((passo) => !respondido(passo));
        if (vazio) {
            evento.preventDefault();
            location.hash = vazio.id;
            avisar(vazio);
            return;
        }
        if (analisando) analisando.hidden = false;
    });
})();