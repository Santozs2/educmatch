/* "Voltar" leva para a página de onde a pessoa veio, não sempre para o quiz.
   O href de cada link continua sendo o destino de reserva: vale sem JS, ao abrir
   a página direto (link compartilhado, nova aba) ou quando a página anterior não
   é do site. Links de âncora (#questao-N) e os marcados com data-voltar="fixo"
   não mudam: são navegação dentro da própria página. */
(function () {
    // Voltar para estas telas seria voltar para um formulário já enviado.
    const NAO_VOLTAR_PARA = /^\/(entrar|cadastro_usuario|logout)\//;

    function paginaAnteriorDoSite() {
        if (window.history.length < 2 || !document.referrer) return false;
        try {
            const anterior = new URL(document.referrer);
            return anterior.origin === window.location.origin
                && anterior.pathname !== window.location.pathname
                && !NAO_VOLTAR_PARA.test(anterior.pathname);
        } catch (erro) {
            return false;
        }
    }

    document.addEventListener("click", function (evento) {
        const link = evento.target.closest("a.voltar");
        if (!link || evento.defaultPrevented || link.dataset.voltar === "fixo") return;
        // Ctrl/Cmd/Shift + clique e botão do meio abrem em outra aba: o href decide.
        if (evento.button !== 0 || evento.ctrlKey || evento.metaKey || evento.shiftKey || evento.altKey) return;
        if ((link.getAttribute("href") || "").startsWith("#")) return;
        if (!paginaAnteriorDoSite()) return;

        evento.preventDefault();
        window.history.back();
    });
})();
