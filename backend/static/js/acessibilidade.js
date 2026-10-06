/* Fonte grande e alto contraste. Os mesmos botões aparecem em mais de um lugar
   (barra do topo e folha "Mais" do celular), por isso o estado é escrito em todos
   os botões da mesma classe, não só no que foi clicado. */
(function () {
    const raiz = document.documentElement;
    const botoes = document.querySelectorAll("[data-alternar]");

    function marcar(classe, ligado) {
        botoes.forEach(function (botao) {
            if (botao.dataset.alternar === classe) {
                botao.setAttribute("aria-pressed", String(ligado));
            }
        });
    }

    botoes.forEach(function (botao) {
        const classe = botao.dataset.alternar;
        botao.setAttribute("aria-pressed", String(raiz.classList.contains(classe)));

        botao.addEventListener("click", function () {
            const ligado = raiz.classList.toggle(classe);
            marcar(classe, ligado);
            try {
                localStorage.setItem(classe, ligado ? "1" : "0");
            } catch (e) {
            }
        });
    });
})();
