(function () {
    const raiz = document.documentElement;

    document.querySelectorAll("[data-alternar]").forEach(function (botao) {
        const classe = botao.dataset.alternar;
        botao.setAttribute("aria-pressed", String(raiz.classList.contains(classe)));

        botao.addEventListener("click", function () {
            const ligado = raiz.classList.toggle(classe);
            botao.setAttribute("aria-pressed", String(ligado));
            try {
                localStorage.setItem(classe, ligado ? "1" : "0");
            } catch (e) {
            }
        });
    });
})();