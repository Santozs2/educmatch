/* "Manifestar interesse" sem sair da página.
   Sem JS, o form salva e o servidor manda a aba para o site do SENAI; ao voltar,
   o navegador mostra a página guardada, ainda com "Manifestar interesse". Com JS,
   o SENAI abre em outra aba, o interesse é salvo em segundo plano e esta página
   recarrega já com "Inscrever-se". Só os forms com data-interesse (de quem está
   logado) mudam: quem não está logado precisa ir para a tela de entrar. */
(function () {
    document.addEventListener("submit", function (evento) {
        const form = evento.target.closest("form[data-interesse]");
        if (!form || evento.defaultPrevented) return;
        evento.preventDefault();

        const botao = form.querySelector('button[type="submit"]');
        if (botao) botao.disabled = true;
        // Abre agora, ainda no clique: depois do fetch o navegador bloquearia a nova aba.
        if (form.dataset.urlSenai) window.open(form.dataset.urlSenai, "_blank", "noopener");

        // redirect "manual": a resposta é o redirect para o SENAI, que não precisa ser seguido aqui.
        fetch(form.action, { method: "POST", body: new FormData(form), credentials: "same-origin", redirect: "manual" })
            .then(function () { window.location.reload(); })
            .catch(function () {
                // Sem rede: tenta pelo caminho de sempre.
                if (botao) botao.disabled = false;
                form.submit();
            });
    });

    // Voltando do SENAI pelo botão do navegador, a página sai do cache com o
    // botão antigo: recarrega para mostrar o que já foi salvo.
    window.addEventListener("pageshow", function (evento) {
        if (evento.persisted && document.querySelector("form[data-interesse]")) window.location.reload();
    });
})();
