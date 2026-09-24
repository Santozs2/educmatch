// Números que contam de 0 até o valor final, no mesmo ritmo do anel e das
// barras (ver --dur-preencher no tokens.css). Uso: <span data-contar>87%</span>.
(function () {
    const estilo = getComputedStyle(document.documentElement);
    const duracao = parseFloat(estilo.getPropertyValue("--dur-preencher")) || 1200;
    const atraso = 250;

    // Começa rápido e freia no fim, igual ao --ease-saida das barras
    function desacelerar(t) {
        return 1 - Math.pow(1 - t, 4);
    }

    function contar(elemento) {
        const texto = elemento.textContent.trim();
        const partes = texto.match(/^(\D*)(\d+)(.*)$/);
        if (!partes) return;

        const [, antes, numero, depois] = partes;
        const final = parseInt(numero, 10);
        let inicio = null;

        elemento.textContent = antes + "0" + depois;

        function quadro(agora) {
            if (inicio === null) inicio = agora;
            const t = Math.min((agora - inicio) / duracao, 1);
            elemento.textContent = antes + Math.round(final * desacelerar(t)) + depois;
            if (t < 1) requestAnimationFrame(quadro);
        }

        setTimeout(function () { requestAnimationFrame(quadro); }, atraso);
    }

    document.querySelectorAll("[data-contar]").forEach(contar);
})();
