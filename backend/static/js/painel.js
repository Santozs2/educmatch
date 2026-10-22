/* Painel: folha "Mais" do celular, animação da troca de aba, confirmação antes de
   POST, copiar link e campo de mês.
   Sem JS o painel continua navegável: as abas e o menu lateral são links de verdade,
   os forms enviam direto e o campo de mês fica visível. */
(function () {
    // ---------- Folha "Mais" (celular) ----------
    const folha = document.getElementById("painel-mais");
    const fundo = document.querySelector(".mais__fundo");
    const abridores = document.querySelectorAll("[data-abrir-mais]");
    const fechadores = document.querySelectorAll("[data-fechar-mais]");

    function alternarMais(abrir) {
        if (!folha) return;
        folha.classList.toggle("aberta", abrir);
        if (fundo) {
            fundo.hidden = false;
            fundo.classList.toggle("aberta", abrir);
        }
        document.body.classList.toggle("sem-rolagem", abrir);
        abridores.forEach(function (botao) {
            botao.setAttribute("aria-expanded", String(abrir));
        });
    }

    abridores.forEach(function (botao) {
        botao.addEventListener("click", function () {
            alternarMais(!folha.classList.contains("aberta"));
        });
    });
    fechadores.forEach(function (botao) {
        botao.addEventListener("click", function () {
            alternarMais(false);
        });
    });
    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") alternarMais(false);
    });

    // ---------- Barra de abas ----------
    // A aba ativa vem do servidor. No toque a troca é antecipada para a animação
    // do ícone (contorno -> preenchido) rodar antes da próxima página carregar.
    const abas = document.querySelector(".abas");
    if (abas) {
        abas.addEventListener("click", function (evento) {
            const alvo = evento.target.closest(".abas__link");
            if (!alvo || alvo.hasAttribute("aria-expanded")) return;
            abas.removeAttribute("data-pristine");
            const atual = abas.querySelector('[aria-current="page"]');
            if (atual && atual !== alvo) atual.removeAttribute("aria-current");
            alvo.setAttribute("aria-current", "page");
        });
    }

    // ---------- Período ----------
    // O campo de mês só aparece quando o período escolhido é "Mês". O filtro existe
    // duas vezes no HTML (barra do topo e folha "Mais"), por isso o laço.
    document.querySelectorAll("[data-periodo]").forEach(function (form) {
        const escolha = form.querySelector("[data-periodo-escolha]");
        const mes = form.querySelector("[data-periodo-mes]");
        if (!escolha || !mes) return;

        function mostrarMes() {
            mes.hidden = escolha.value !== "mes";
        }
        escolha.addEventListener("change", mostrarMes);
        mostrarMes();
    });

    // ---------- Confirmação ----------
    // Todo form com data-confirmar passa por um <dialog> antes de enviar.
    const modal = document.getElementById("painel-confirmar");
    const ok = modal.querySelector("[data-confirmar-ok]");
    let pendente = null;

    document.querySelectorAll("form[data-confirmar]").forEach(function (form) {
        form.addEventListener("submit", function (evento) {
            if (form.dataset.confirmado === "1") return;
            evento.preventDefault();
            pendente = form;
            modal.querySelector("[data-mensagem]").textContent = form.dataset.confirmar;
            ok.className = "perigo" in form.dataset ? "botao botao--perigo" : "botao";
            modal.showModal();
        });
    });

    ok.addEventListener("click", function () {
        modal.close();
        if (pendente) {
            pendente.dataset.confirmado = "1";
            pendente.requestSubmit();
        }
    });
    modal.querySelector("[data-cancelar]").addEventListener("click", function () {
        pendente = null;
        modal.close();
    });

    // ---------- Cadastro de curso ----------
    document.querySelectorAll(".painel-modal--curso").forEach(function (cursoModal) {
        function abrirModalCurso() {
            document.body.classList.add("sem-rolagem");
            cursoModal.showModal();
        }

        document.querySelectorAll("[data-abrir-curso]").forEach(function (botao) {
            if (botao.dataset.abrirCurso !== cursoModal.id) return;
            botao.addEventListener("click", abrirModalCurso);
        });
        cursoModal.addEventListener("close", function () {
            document.body.classList.remove("sem-rolagem");
        });
        cursoModal.querySelectorAll("[data-fechar-curso]").forEach(function (botao) {
            botao.addEventListener("click", function () {
                cursoModal.close();
            });
        });
        cursoModal.addEventListener("click", function (evento) {
            if (evento.target === cursoModal) cursoModal.close();
        });
        if (cursoModal.dataset.abrir === "true") abrirModalCurso();
    });

    // ---------- QR e copiar ----------
    // O qrcode.min.js só é carregado nas telas de links, antes deste arquivo.
    if (window.QRCode) {
        document.querySelectorAll("[data-qr]").forEach(function (caixa) {
            new QRCode(caixa, { text: caixa.dataset.qr, width: 160, height: 160 });
        });
    }
    document.querySelectorAll("[data-copiar]").forEach(function (botao) {
        botao.addEventListener("click", function () {
            const campo = botao.parentElement.querySelector("input");
            navigator.clipboard.writeText(campo.value).then(function () {
                const original = botao.innerHTML;
                botao.textContent = "Copiado!";
                setTimeout(function () {
                    botao.innerHTML = original;
                }, 1600);
            });
        });
    });
})();
