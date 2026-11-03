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

    // ---------- Tabela de cursos ----------
    // Todas as linhas já vêm no HTML (e cada uma tem seu modal de edição); aqui só
    // decidimos quais aparecem. Sem JS, a tabela mostra todos os cursos.
    const POR_PAGINA = 10;
    const linhasCurso = Array.from(document.querySelectorAll("tr[data-curso]"));
    const ferramentas = document.querySelector("[data-cursos-ferramentas]");
    if (ferramentas && linhasCurso.length) {
        const busca = ferramentas.querySelector("[data-cursos-busca]");
        const filtros = Array.from(ferramentas.querySelectorAll("[data-cursos-filtro]"));
        const menuFiltros = ferramentas.querySelector("[data-cursos-filtros]");
        const rotuloFiltros = ferramentas.querySelector("[data-cursos-filtros-rotulo]");
        const vazio = document.querySelector("[data-cursos-vazio]");
        const rodape = document.querySelector("[data-cursos-rodape]");
        const resumo = rodape.querySelector("[data-cursos-resumo]");
        const paginas = rodape.querySelector("[data-cursos-paginas]");
        let paginaAtual = 1;

        // Quem digita "gestao" ou "eletrica" também acha o curso.
        function normalizar(texto) {
            return texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
        }

        filtros.forEach(function (select) {
            const chave = select.dataset.cursosFiltro;
            const valores = new Set(linhasCurso.map(function (linha) { return linha.dataset[chave]; }));
            Array.from(valores).sort(function (a, b) { return a.localeCompare(b, "pt-BR"); }).forEach(function (valor) {
                select.add(new Option(valor, valor));
            });
        });

        function criarBotaoPagina(conteudo, rotulo, pagina, seta) {
            const botao = document.createElement("button");
            botao.type = "button";
            botao.className = "painel-cursos__pagina" + (seta ? " painel-cursos__pagina--seta" : "");
            botao.innerHTML = conteudo;
            botao.setAttribute("aria-label", rotulo);
            botao.dataset.pagina = pagina;
            return botao;
        }

        function desenharPaginas(total) {
            paginas.textContent = "";
            paginas.hidden = total < 2;
            if (total < 2) return;
            const anterior = criarBotaoPagina('<i class="fa-solid fa-chevron-left" aria-hidden="true"></i>', "Página anterior", paginaAtual - 1, true);
            anterior.disabled = paginaAtual === 1;
            paginas.append(anterior);
            for (let pagina = 1; pagina <= total; pagina += 1) {
                const botao = criarBotaoPagina(pagina, "Página " + pagina, pagina, false);
                if (pagina === paginaAtual) botao.setAttribute("aria-current", "page");
                paginas.append(botao);
            }
            const proxima = criarBotaoPagina('<i class="fa-solid fa-chevron-right" aria-hidden="true"></i>', "Próxima página", paginaAtual + 1, true);
            proxima.disabled = paginaAtual === total;
            paginas.append(proxima);
        }

        function aplicar() {
            const termo = normalizar(busca.value.trim());
            const ativos = filtros.filter(function (select) { return select.value; });
            const encontradas = linhasCurso.filter(function (linha) {
                return normalizar(linha.dataset.busca).includes(termo) && ativos.every(function (select) {
                    return linha.dataset[select.dataset.cursosFiltro] === select.value;
                });
            });
            const totalPaginas = Math.max(1, Math.ceil(encontradas.length / POR_PAGINA));
            paginaAtual = Math.min(paginaAtual, totalPaginas);
            const inicio = (paginaAtual - 1) * POR_PAGINA;
            const fim = Math.min(inicio + POR_PAGINA, encontradas.length);
            const visiveis = new Set(encontradas.slice(inicio, fim));

            linhasCurso.forEach(function (linha) { linha.hidden = !visiveis.has(linha); });
            vazio.hidden = encontradas.length > 0;
            rotuloFiltros.textContent = ativos.length ? "Filtros (" + ativos.length + ")" : "Filtros";
            if (!encontradas.length) {
                resumo.textContent = "Nenhum curso encontrado";
            } else {
                const nome = encontradas.length === 1 ? " curso" : " cursos";
                resumo.textContent = "Mostrando " + (inicio + 1) + " a " + fim + " de " + encontradas.length + nome;
            }
            desenharPaginas(totalPaginas);
        }

        function aplicarDoInicio() {
            paginaAtual = 1;
            aplicar();
        }

        busca.addEventListener("input", aplicarDoInicio);
        filtros.forEach(function (select) { select.addEventListener("change", aplicarDoInicio); });
        ferramentas.querySelector("[data-cursos-limpar]").addEventListener("click", function () {
            filtros.forEach(function (select) { select.value = ""; });
            aplicarDoInicio();
        });
        paginas.addEventListener("click", function (evento) {
            const botao = evento.target.closest("button");
            if (!botao || botao.disabled) return;
            paginaAtual = Number(botao.dataset.pagina);
            aplicar();
            // A navegação é redesenhada: sem isto, quem usa teclado perde o foco.
            paginas.querySelector('[aria-current="page"]').focus();
        });
        document.addEventListener("click", function (evento) {
            if (menuFiltros.open && !menuFiltros.contains(evento.target)) menuFiltros.open = false;
        });
        document.addEventListener("keydown", function (evento) {
            if (evento.key === "Escape") menuFiltros.open = false;
        });

        ferramentas.hidden = false;
        rodape.hidden = false;
        aplicar();
    }

    // ---------- Áreas cadastradas ----------
    // Os dois botões fazem o mesmo: mostram a lista inteira ou voltam às primeiras.
    const AREAS_INICIAIS = 5;
    const cardAreas = document.querySelector("[data-areas]");
    if (cardAreas) {
        const extras = Array.from(cardAreas.querySelectorAll("li")).slice(AREAS_INICIAIS);
        const alternadores = cardAreas.querySelectorAll("[data-areas-alternar]");

        function mostrarAreas(todas) {
            extras.forEach(function (area) { area.hidden = !todas; });
            alternadores.forEach(function (botao) {
                botao.textContent = todas ? "Ver menos" : botao.dataset.areasAlternar;
                botao.setAttribute("aria-expanded", String(todas));
            });
        }

        if (extras.length) {
            alternadores.forEach(function (botao) {
                botao.setAttribute("aria-controls", "painel-areas-lista");
                botao.hidden = false;
                botao.addEventListener("click", function () {
                    mostrarAreas(extras[0].hidden);
                });
            });
            mostrarAreas(false);
        }
    }

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
