// static/js/quiz.js
// Transforma o formulario (que funciona sem JS) num wizard de uma pergunta por vez.
(function () {
    const form = document.querySelector("[data-quiz]");
    if (!form) return;

    const passos = Array.from(form.querySelectorAll("[data-passo]"));
    if (passos.length < 2) return;

    const barraWrapper = form.querySelector("[data-barra-wrapper]");
    const barra = form.querySelector("[data-barra]");
    const contador = form.querySelector("[data-contador]");
    const totalPerguntas = passos.length - 1; // o primeiro passo e a apresentacao

    form.classList.add("quiz--wizard");
    if (barraWrapper) barraWrapper.hidden = false;

    // Se o servidor devolveu erro, comeca na primeira pergunta sem resposta.
    let atual = form.querySelector(".alerta") ? primeiraVazia() : 0;

    function primeiraVazia() {
        for (let i = 1; i < passos.length; i++) {
            if (!respondido(passos[i])) return i;
        }
        return passos.length - 1;
    }

    function respondido(passo) {
        return Boolean(passo.querySelector("input[type=radio]:checked"));
    }

    function mostrar(indice, foco) {
        atual = Math.max(0, Math.min(indice, passos.length - 1));
        passos.forEach((passo, i) => passo.classList.toggle("esta-ativo", i === atual));

        const respondidas = atual === 0 ? 0 : atual - 1;
        if (barra) barra.style.width = (respondidas / totalPerguntas) * 100 + "%";
        if (contador) {
            contador.textContent = atual === 0
                ? totalPerguntas + " perguntas"
                : "Pergunta " + atual + " de " + totalPerguntas;
        }

        esconderAviso(passos[atual]);
        if (foco) {
            const alvo = passos[atual].querySelector("input, button");
            if (alvo) alvo.focus({ preventScroll: true });
        }
        passos[atual].scrollIntoView({ behavior: "smooth", block: "center" });
    }

    function esconderAviso(passo) {
        const aviso = passo.querySelector("[data-aviso]");
        if (aviso) aviso.hidden = true;
    }

    function avancar() {
        const passo = passos[atual];
        if (atual > 0 && !respondido(passo)) {
            const aviso = passo.querySelector("[data-aviso]");
            if (aviso) aviso.hidden = false;
            passo.classList.remove("treme");
            void passo.offsetWidth; // reinicia a animacao
            passo.classList.add("treme");
            return;
        }
        mostrar(atual + 1, true);
    }

    form.addEventListener("click", (evento) => {
        if (evento.target.closest("[data-avancar]")) avancar();
        if (evento.target.closest("[data-voltar]")) mostrar(atual - 1, true);
    });

    // Marcou a resposta: segue sozinho, com uma pausa para o clique ser visto.
    form.addEventListener("change", (evento) => {
        if (evento.target.type !== "radio") return;
        esconderAviso(passos[atual]);
        if (atual < passos.length - 1) setTimeout(avancar, 320);
    });

    // Enter avanca em vez de enviar o formulario pela metade.
    form.addEventListener("keydown", (evento) => {
        if (evento.key !== "Enter") return;
        if (atual === passos.length - 1) return;
        evento.preventDefault();
        avancar();
    });

    mostrar(atual, false);
})();
