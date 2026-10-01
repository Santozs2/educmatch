/* Painel: menu no celular, confirmação antes de POST, copiar link e campo de mês.
   Sem JS o painel continua funcionando: os forms enviam direto e o mês fica visível. */
(function () {
    const menu = document.getElementById("painel-menu");
    const fundo = document.querySelector("[data-fechar-menu]");
    const abridores = document.querySelectorAll("[data-abrir-menu]");

    function alternarMenu(abrir) {
        menu.classList.toggle("aberto", abrir);
        fundo.hidden = !abrir;
        abridores.forEach(function (botao) {
            botao.setAttribute("aria-expanded", String(abrir));
        });
    }

    abridores.forEach(function (botao) {
        botao.addEventListener("click", function () {
            alternarMenu(!menu.classList.contains("aberto"));
        });
    });
    fundo.addEventListener("click", function () {
        alternarMenu(false);
    });
    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") alternarMenu(false);
    });

    // O campo de mês só aparece quando o período escolhido é "Mês".
    const periodo = document.getElementById("periodo");
    const mes = document.getElementById("mes");
    function mostrarMes() {
        mes.hidden = periodo.value !== "mes";
    }
    periodo.addEventListener("change", mostrarMes);
    mostrarMes();

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
    // QR dos links: o qrcode.min.js só é carregado na tela de links, antes deste arquivo.
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