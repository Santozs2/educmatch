---
title: "Spec do dashboard — Pessoa C · Estilo, comportamento e testes"
aliases: ["Dashboard pessoa C", "Spec C dashboard", "CSS, JS e testes do painel"]
tags: [tcc, painel, dashboard, avaliacao, css, javascript, testes, acessibilidade, spec, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-10-01
---

> [!info] Mapa: [[guia-dashboard-live-share|🖥️ Guia do grupo]] · Colegas: [[spec-dashboard-pessoa-a-dados|🧮 A · Dados]] · [[spec-dashboard-pessoa-b-telas|🖼️ B · Telas]]

# 🎨 Pessoa C · Estilo, comportamento e testes

> [!abstract] A sua missão
> Você decide **como a tela se parece e se comporta**, e **prova que tudo funciona**. Escreve o CSS (botões sólidos, casca, cards, celular), o JavaScript (menu do celular, janela de confirmação, copiar link, gráficos, QR code) e **todos os testes**.
> Você é dona de todo `.css`, todo `.js` e toda a pasta `tests/`. As classes que você estiliza são as que B escreve no HTML (lista no [[guia-dashboard-live-share|guia]]); as funções que você testa são as de A.

> [!tip] Como ler esta spec
> Em cada etapa: primeiro o **CSS e o JS** (dá para fazer junto com A e B), depois os **testes**. Escreva os testes enquanto os outros trabalham, mas só **rode** quando A avisar "views prontas". Quem roda é quem hospeda, e você acompanha pelo terminal compartilhado.

> [!important] 🎓 Como rodar os testes
> ```bash
> cd backend
> python manage.py test                       # todos
> python manage.py test painel                # só os do painel
> python manage.py test painel.tests.test_telas.CascaDoPainelTest   # uma classe só
> ```
> Rodar só a parte nova é mais rápido enquanto vocês trabalham. No **ponto de encontro**, rode **todos**: é o número total que precisa bater.

---

## 🧭 O mapa

| Etapa | Estilo e comportamento | Testes | Testes novos |
|---|---|---|---|
| **1** | `componentes.css` (botões), `painel.css`, `painel.js`, `painel-graficos.js` | `test_privacidade.py` (ajuste), `test_telas.py` (novo) | 10 |
| **2** | `painel.css` (funil e QR), `painel.js` (QR) | `test_telas.py` (mais uma classe) | 7 |
| **3** | — | `quiz/tests/test_inicio.py` | 11 |
| **4** | `avaliacao.css` | `avaliacao/tests/` | 11 |
| **5** | `painel.css` (resultados) | `painel/tests/test_avaliacoes.py` | 12 |

---

# Etapa 1 · Casca do painel, Início e Quiz

## 1.1 `static/css/componentes.css`: os botões sólidos

Acrescente no fim do arquivo:

```css
/* ---------- Botões sólidos (regra do painel: nenhum botão fantasma) ----------
   .botao é o principal (vermelho). As variantes abaixo trocam só o fundo:
   todas são preenchidas, sem borda aparente e com alvo de 48px. */

.botao--secundario {
  border-color: var(--preto-2);
  background: var(--preto-2);
  color: var(--branco);
}

.botao--secundario:hover {
  border-color: var(--preto);
  background: var(--preto);
  color: var(--branco);
  box-shadow: 0 6px 16px rgba(9, 9, 11, 0.2);
}

.botao--suave {
  border-color: var(--marca-claro);
  background: var(--marca-claro);
  color: var(--marca-escuro);
}

.botao--suave:hover {
  border-color: #f9d6d3;
  background: #f9d6d3;
  color: var(--marca-escuro);
  box-shadow: none;
}

.botao--neutro {
  border-color: var(--gelo);
  background: var(--gelo);
  color: var(--preto-2);
}

.botao--neutro:hover {
  border-color: #e4deda;
  background: #e4deda;
  color: var(--preto);
  box-shadow: none;
}

.botao--perigo {
  border-color: var(--erro);
  background: var(--erro);
  color: var(--branco);
}

.botao--perigo:hover {
  border-color: #b91c1c;
  background: #b91c1c;
  color: var(--branco);
  box-shadow: 0 6px 16px rgba(220, 38, 38, 0.22);
}

.botao--icone {
  width: var(--alvo);
  padding: 0;
}
```

> [!warning] 🎓 Entenda: o que é botão fantasma, e por que não
> Botão fantasma tem fundo transparente ou branco só com borda. Ele some no fundo claro e parece desativado. No painel, todo botão é uma destas variantes:
>
> | Classe | Fundo | Uso |
> |---|---|---|
> | `botao` | vermelho | A ação principal da tela |
> | `botao botao--secundario` | grafite | Copiar, Cancelar, abrir menu |
> | `botao botao--suave` | rosado | Ações de linha de tabela, opções de menu |
> | `botao botao--neutro` | gelo | Botões de ícone da barra do topo |
> | `botao botao--perigo` | vermelho de erro | Fechar link |
>
> O `botao--contorno` e o `botao--texto` continuam existindo para o **site do aluno**, mas não podem aparecer no painel.

## 1.2 `static/css/painel.css`: substitua o arquivo inteiro

```css
/* Painel da coordenação. Usa os tokens do tokens.css; os botões vêm do componentes.css.
   Regra da tela: nenhum botão fantasma. Todo botão tem fundo sólido. */

.pagina-painel .conteudo {
  max-width: none;
  padding: 0;
}

.painel-app {
  --menu: 248px;
  --barra: 72px;
  display: flex;
  min-height: 100vh;
}

/* ---------- Menu lateral ---------- */

.painel-menu {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 40;
  width: var(--menu);
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 18px 12px;
  overflow-y: auto;
  background: var(--preto);
  color: var(--branco);
}

.painel-menu__marca {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  font-size: 1.15rem;
  font-weight: 700;
  text-decoration: none;
}

.painel-menu__selo {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: var(--marca);
}

.painel-menu__nav {
  display: grid;
  gap: 6px;
}

.painel-menu__item {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: var(--alvo);
  padding: 0 14px;
  border-radius: 9px;
  background: #17171a;
  color: #d4d4d8;
  font-weight: 600;
  text-decoration: none;
  transition: background var(--dur-rapida) var(--ease-padrao);
}

.painel-menu__item:hover {
  background: #242428;
  color: var(--branco);
}

.painel-menu__item[aria-current="page"] {
  background: var(--marca);
  color: var(--branco);
}

.painel-menu__item i {
  width: 20px;
  text-align: center;
}

.painel-menu__chamada {
  margin-top: auto;
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid #29292d;
  border-radius: var(--raio);
  background: #17171a;
  font-size: 0.85rem;
}

/* ---------- Barra do topo ---------- */

.painel-principal {
  flex: 1;
  min-width: 0;
  margin-left: var(--menu);
}

.painel-barra {
  position: sticky;
  top: 0;
  z-index: 25;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: var(--barra);
  padding: 12px 28px;
  border-bottom: 1px solid var(--linha);
  background: rgba(249, 250, 251, 0.96);
  backdrop-filter: blur(10px);
}

.painel-barra__menu {
  display: none;
}

.painel-periodo {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.painel-campo {
  min-height: var(--alvo);
  padding: 0 12px;
  border: 0;
  border-radius: var(--raio-botao);
  background: var(--gelo);
  color: var(--tinta);
  font: inherit;
  font-weight: 600;
}

.painel-acessibilidade {
  position: relative;
  margin-left: auto;
}

.painel-acessibilidade summary {
  list-style: none;
}

.painel-acessibilidade summary::-webkit-details-marker {
  display: none;
}

.painel-acessibilidade__menu {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  z-index: 30;
  display: grid;
  gap: 6px;
  min-width: 210px;
  padding: 8px;
  border: 1px solid var(--linha);
  border-radius: var(--raio);
  background: var(--superficie);
  box-shadow: var(--sombra);
}

.painel-acessibilidade__menu [aria-pressed="true"] {
  border-color: var(--marca);
  background: var(--marca);
  color: var(--branco);
}

.painel-perfil {
  display: flex;
  align-items: center;
  gap: 10px;
}

.painel-perfil__avatar {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--marca-claro);
  color: var(--marca-escuro);
  font-weight: 700;
}

.painel-perfil__texto {
  display: grid;
  line-height: 1.2;
  font-size: 0.85rem;
}

.painel-perfil__texto small {
  color: var(--texto-3);
}

/* ---------- Conteúdo ---------- */

.painel-conteudo {
  max-width: 1600px;
  margin: 0 auto;
  padding: 26px 28px 48px;
}

.painel-cabecalho {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 3px solid var(--marca);
}

.painel-cabecalho h1 {
  margin: 0;
  font-size: var(--h2);
}

.painel-cabecalho p {
  margin: 4px 0 0;
  color: var(--texto-2);
}

.painel-cabecalho__acoes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.painel-kpis,
.painel-grade {
  display: grid;
  gap: 16px;
  margin-bottom: 16px;
}

.painel-kpis {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.painel-grade--2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.painel-grade--3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.painel-grade--2-1 {
  grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
}

.painel-card {
  min-width: 0;
  padding: 18px;
  border: 1px solid var(--linha);
  border-radius: 14px;
  background: var(--superficie);
  box-shadow: var(--sombra);
}

.painel-card--destaque {
  border-left: 4px solid var(--marca);
}

.painel-kpi h2,
.painel-card__titulo {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  font-size: 0.8rem;
  letter-spacing: 0.075em;
  text-transform: uppercase;
  color: var(--marca-escuro);
}

.painel-kpi h2 {
  min-height: 24px;
}

.painel-kpi__valor {
  margin: 0;
  font-size: 1.9rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.03em;
}

.painel-ajuda {
  position: relative;
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--gelo);
  color: var(--texto-2);
  font-size: 0.75rem;
  letter-spacing: 0;
  text-transform: none;
  cursor: help;
}

.painel-ajuda:hover::after,
.painel-ajuda:focus::after {
  content: attr(data-dica);
  position: absolute;
  bottom: 30px;
  left: 50%;
  z-index: 20;
  width: 240px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--preto);
  color: var(--branco);
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.35;
  transform: translateX(-50%);
}

.painel-grafico {
  position: relative;
  height: 260px;
}

.painel-grafico--rosca {
  height: 200px;
}

.painel-legenda,
.painel-lista,
.painel-barras,
.painel-ranking,
.painel-atividade {
  display: grid;
  gap: 10px;
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
  font-size: 0.85rem;
}

.painel-legenda li,
.painel-lista li,
.painel-barras li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--linha);
}

.painel-ranking li {
  display: grid;
  grid-template-columns: 32px 1fr auto;
  align-items: center;
  gap: 8px;
}

.painel-ranking__pos {
  color: var(--marca);
  font-weight: 700;
}

.painel-ranking__nome {
  font-weight: 600;
}

.painel-atividade li {
  display: flex;
  align-items: center;
  gap: 10px;
}

.painel-atividade__icone {
  display: grid;
  flex: none;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--marca-claro);
  color: var(--marca);
}

.painel-progresso {
  height: 10px;
  overflow: hidden;
  border-radius: var(--raio-pilula);
  background: #f0eeee;
}

.painel-progresso i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--marca);
}

.painel-selo {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: var(--raio-pilula);
  font-size: 0.75rem;
  font-weight: 700;
}

.painel-selo--sucesso { background: #eaf7ee; color: #15803d; }
.painel-selo--alerta { background: #fff5df; color: #92400e; }
.painel-selo--perigo { background: #feecec; color: #b91c1c; }
.painel-selo--neutro { background: #f1f1f3; color: var(--texto-2); }

.painel-alerta {
  color: var(--erro);
}

.painel-suprimido {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--marca-escuro);
  font-weight: 700;
  white-space: nowrap;
}

.painel-aviso {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 12px 14px;
  border: 1px solid #f6cbc7;
  border-radius: 10px;
  background: var(--marca-clarinho);
  color: var(--marca-escuro);
}

.painel-aviso p {
  margin: 0;
}

.painel-vazio {
  margin: 6px 0;
  color: var(--texto-3);
}

.painel-link {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.painel-link__url {
  flex: 1;
  min-width: 0;
  min-height: var(--alvo);
  padding: 0 10px;
  border: 1px solid var(--linha);
  border-radius: var(--raio-botao);
  background: var(--fundo);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.8rem;
}

/* Tabelas */

.painel-tabela {
  overflow-x: auto;
}

.painel-tabela table {
  width: 100%;
  min-width: 640px;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.painel-tabela th {
  padding: 10px 12px;
  background: #fafafa;
  color: var(--texto-3);
  font-size: 0.75rem;
  letter-spacing: 0.07em;
  text-align: left;
  text-transform: uppercase;
}

.painel-tabela td {
  padding: 10px 12px;
  border-top: 1px solid var(--linha);
}

.painel-tabela td.numero,
.painel-tabela th.numero {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* Modal de confirmação */

.painel-modal {
  width: min(480px, calc(100% - 32px));
  padding: 22px;
  border: 0;
  border-radius: 16px;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.22);
}

.painel-modal::backdrop {
  background: rgba(9, 9, 11, 0.52);
}

.painel-modal h2 {
  margin: 0 0 8px;
  color: var(--titulo);
}

.painel-modal__acoes {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 18px;
}

.painel-inferior,
.painel-fundo {
  display: none;
}

/* ---------- Alto contraste ---------- */

:root.alto-contraste .painel-card {
  border-color: var(--linha);
  box-shadow: none;
}

/* ---------- Tablet ---------- */

@media (max-width: 1100px) {
  .painel-grade--2-1,
  .painel-grade--3 {
    grid-template-columns: 1fr;
  }
}

/* ---------- Celular ---------- */

@media (max-width: 760px) {
  .painel-app {
    --menu: 0px;
  }

  .painel-menu {
    width: min(300px, 86vw);
    transform: translateX(-100%);
    transition: transform var(--dur-media) var(--ease-saida);
  }

  .painel-menu.aberto {
    transform: none;
    box-shadow: 20px 0 60px rgba(0, 0, 0, 0.25);
  }

  .painel-fundo:not([hidden]) {
    position: fixed;
    inset: 0;
    z-index: 35;
    display: block;
    background: rgba(9, 9, 11, 0.48);
  }

  .painel-barra {
    padding: 10px 14px;
  }

  .painel-barra__menu {
    display: inline-flex;
  }

  .painel-perfil {
    display: none;
  }

  .painel-conteudo {
    padding: 18px 14px 96px;
  }

  .painel-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .painel-grade--2 {
    grid-template-columns: 1fr;
  }

  .painel-inferior {
    position: fixed;
    inset: auto 0 0 0;
    z-index: 30;
    display: flex;
    justify-content: space-around;
    gap: 6px;
    padding: 6px;
    background: var(--preto);
  }

  .painel-inferior a,
  .painel-inferior button {
    display: flex;
    flex: 1;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    min-height: 56px;
    border: 0;
    border-radius: 8px;
    background: #17171a;
    color: #d4d4d8;
    font: inherit;
    font-size: 0.75rem;
    text-decoration: none;
  }

  .painel-inferior [aria-current="page"] {
    background: var(--marca);
    color: var(--branco);
  }
}
```

> [!tip] 🎓 Entenda: o painel no celular
> No `@media (max-width: 760px)`, o menu lateral sai da tela (`transform: translateX(-100%)`) e só volta quando ganha a classe `aberto`. A barra de baixo (`painel-inferior`) aparece no lugar. Os KPIs passam para 2 por linha. Abra o DevTools (`F12`), ative o modo celular e escolha 375px de largura para conferir.

## 1.3 `static/js/painel.js` (novo)

```js
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
```

> [!tip] 🎓 Entenda: o painel funciona **sem** JavaScript
> Sem JS, os forms enviam direto (sem a janela de confirmação) e o campo de mês fica sempre visível. O JS só **melhora** o que já funciona. Isso se chama *progressive enhancement*, e é por isso que os testes do Django, que não rodam JS, conseguem testar as telas.

> [!tip] 🎓 Entenda: por que `<dialog>`
> O `<dialog>` com `showModal()` já prende o foco dentro dele, fecha com `Esc` e escurece o fundo com `::backdrop`. Uma janela feita de `<div>` precisaria de tudo isso escrito à mão, e ainda assim seria pior para quem usa leitor de tela.

## 1.4 `static/js/painel-graficos.js` (novo)

```js
/* Gráficos da tela Início. Os dados chegam por json_script, já suprimidos:
   um dia com menos de K testes vem como null e vira um buraco na linha. */
(function () {
    if (typeof Chart === "undefined") {
        console.warn("Chart.js não carregou; os números continuam nas legendas.");
        return;
    }

    const estilo = getComputedStyle(document.documentElement);
    const marca = estilo.getPropertyValue("--marca").trim();
    const fonte = estilo.getPropertyValue("--fonte").trim();
    const tons = [marca, "#8e2520", "#a8564f", "#bda09c", "#d7c8c4"];
    Chart.defaults.font.family = fonte;

    function dados(id) {
        const elemento = document.getElementById(id);
        return elemento ? JSON.parse(elemento.textContent) : [];
    }

    const serie = dados("dados-serie");
    new Chart(document.getElementById("grafico-serie"), {
        type: "line",
        data: {
            labels: serie.map(function (linha) { return linha.rotulo; }),
            datasets: [{
                label: "Testes",
                data: serie.map(function (linha) { return linha.total; }),
                borderColor: marca,
                backgroundColor: marca,
                tension: 0.3,
                spanGaps: false,
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
    });

    // Rosca: as 4 maiores áreas e o resto somado em "Outras".
    const areas = dados("dados-areas").filter(function (linha) { return linha.total !== null; });
    const principais = areas.slice(0, 4);
    const outras = areas.slice(4).reduce(function (soma, linha) { return soma + linha.total; }, 0);
    const rotulos = principais.map(function (linha) { return linha.nome; });
    const valores = principais.map(function (linha) { return linha.total; });
    if (outras) {
        rotulos.push("Outras");
        valores.push(outras);
    }
    new Chart(document.getElementById("grafico-areas"), {
        type: "doughnut",
        data: { labels: rotulos, datasets: [{ data: valores, backgroundColor: tons, borderWidth: 0 }] },
        options: { maintainAspectRatio: false, cutout: "62%", plugins: { legend: { display: false } } },
    });
})();
```

> [!note] 🎓 Entenda: o buraco na linha
> Um dia com menos de 5 testes chega como `null` (A escondeu). O `spanGaps: false` faz o Chart.js **não ligar** os pontos por cima do buraco: a linha para e recomeça. Ligar seria inventar um número.

O botão de acessibilidade **não precisa de JS seu**: os botões dele têm `data-alternar`, e o `acessibilidade.js` que já existe no projeto cuida deles.

## 1.5 Testes: `painel/tests/test_privacidade.py`

Os testes de privacidade abriam uma tela só. Agora os dados estão em duas (Início e Quiz). Substitua a classe `PrivacidadeNaTelaTest` inteira, do `class PrivacidadeNaTelaTest` até o fim do arquivo:

```python
class PrivacidadeNaTelaTest(BasePainel):
    TELAS = ("painel-dashboard", "painel-quiz")

    def setUp(self):
        super().setUp()
        self.staff = self.criar_staff()

    def abrir_painel(self, tela="painel-dashboard"):
        self.client.force_login(self.staff)
        return self.client.get(reverse(tela))

    def test_sem_massa_so_o_total_sai_do_servidor(self):
        self.criar_tentativas(quantidade=K_MINIMO - 1)

        for tela in self.TELAS:
            with self.subTest(tela=tela):
                contexto = self.abrir_painel(tela).context
                self.assertFalse(contexto["tem_massa"])
                self.assertEqual(contexto["total_de_tentativas"], K_MINIMO - 1)
                for chave in ("conversao", "top_primeiro", "confianca", "demanda_por_area", "serie", "atividade"):
                    self.assertNotIn(chave, contexto)

    def test_conversao_suprimida_nao_vaza_pela_taxa(self):
        """taxa x recomendado / 100 reconstruiria o número escondido."""
        tentativas = self.criar_tentativas(quantidade=K_MINIMO + 1)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        Interesse.objects.create(usuario=self.criar_usuario("um@exemplo.com"), curso=curso)

        conversao = self.abrir_painel("painel-quiz").context["conversao"]

        linha = next(l for l in conversao if l["id"] == curso.id)
        self.assertTrue(linha["suprimido"])
        self.assertIsNone(linha["interessados"])
        self.assertIsNone(linha["taxa"])

    def test_confianca_tambem_e_suprimida(self):
        self.criar_tentativas(quantidade=K_MINIMO + 1)

        confianca = self.abrir_painel("painel-quiz").context["confianca"]

        for linha in confianca:
            if linha["total"] is not None:
                self.assertGreaterEqual(linha["total"], K_MINIMO)

    def test_nenhum_nome_de_respondente_aparece_na_pagina(self):
        """A regra de privacidade, verificada no HTML servido."""
        nomes = ["Ana Zoraide", "Bento Kling", "Cleo Vasquez", "Dora Pimm", "Eli Nunes", "Fabi Ros"]
        self.criar_tentativas(nomes=nomes)

        for tela in self.TELAS:
            corpo = self.abrir_painel(tela).content.decode()
            for nome in nomes:
                with self.subTest(tela=tela, nome=nome):
                    self.assertNotIn(nome, corpo)
```

> [!important] 🎓 Entenda: nenhum teste de privacidade ficou mais fraco
> Os quatro testes continuam, com as mesmas verificações. A diferença é que dois deles agora rodam **nas duas telas**, usando `subTest`: se falhar, o relatório diz em **qual tela** falhou.

## 1.6 Testes: `painel/tests/test_telas.py` (novo)

```python
from datetime import timedelta
from pathlib import Path

from django.urls import reverse
from django.utils import timezone

from accounts.models import Interesse
from painel import metricas
from painel.privacidade import K_MINIMO
from painel.tests.base import BasePainel
from quiz.models import Tentativa_de_resposta

PASTA_DE_TEMPLATES = Path(__file__).resolve().parents[1] / "templates" / "painel"
BOTOES_FANTASMA = ("botao--contorno", "botao--texto", "botao--fantasma")


class CascaDoPainelTest(BasePainel):
    """Etapa 1: menu, período e a regra de nenhum botão fantasma."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.criar_staff())

    def test_menu_leva_o_periodo_escolhido(self):
        resposta = self.client.get(reverse("painel-dashboard"), {"periodo": "anual"})

        self.assertContains(resposta, 'href="/painel/quiz/?periodo=anual"')

    def test_periodo_invalido_cai_no_mensal(self):
        resposta = self.client.get(reverse("painel-quiz"), {"periodo": "semanal"})

        self.assertEqual(resposta.context["periodo"], "mensal")

    def test_menu_marca_a_tela_atual(self):
        resposta = self.client.get(reverse("painel-quiz"))

        self.assertContains(resposta, 'href="/painel/quiz/?periodo=mensal" aria-current="page"')

    def test_nenhum_template_do_painel_usa_botao_fantasma(self):
        for arquivo in PASTA_DE_TEMPLATES.glob("*.html"):
            texto = arquivo.read_text(encoding="utf-8")
            for classe in BOTOES_FANTASMA:
                with self.subTest(arquivo=arquivo.name, classe=classe):
                    self.assertNotIn(classe, texto)

    def test_tela_servida_tambem_nao_tem_botao_fantasma(self):
        self.criar_tentativas(quantidade=K_MINIMO)
        for tela in ("painel-dashboard", "painel-quiz"):
            corpo = self.client.get(reverse(tela)).content.decode()
            for classe in BOTOES_FANTASMA:
                with self.subTest(tela=tela, classe=classe):
                    self.assertNotIn(classe, corpo)


class MetricasDoInicioTest(BasePainel):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.criar_staff())

    def test_dia_com_poucos_testes_some_da_serie(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO + 2)
        ontem = timezone.now() - timedelta(days=1)
        Tentativa_de_resposta.objects.filter(pk__in=[t.pk for t in tentativas[:2]]).update(criado_em=ontem)

        serie = self.client.get(reverse("painel-dashboard")).context["serie"]

        self.assertEqual([linha["total"] for linha in serie], [None, K_MINIMO])

    def test_atividade_recente_tambem_e_suprimida(self):
        self.criar_tentativas(quantidade=K_MINIMO)

        atividade = self.client.get(reverse("painel-dashboard")).context["atividade"]

        testes_na_hora, _, cursos_salvos = atividade
        self.assertEqual(testes_na_hora["total"], K_MINIMO)
        self.assertIsNone(cursos_salvos["total"], "zero cursos salvos é menos que K")

    def test_conversao_geral_some_com_poucos_interesses(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        Interesse.objects.create(usuario=self.criar_usuario("um@exemplo.com"), curso=curso)

        self.assertIsNone(metricas.conversao_geral(None))

    def test_conversao_geral_e_salvos_sobre_recomendados(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        for i in range(K_MINIMO):
            Interesse.objects.create(usuario=self.criar_usuario(f"aluno{i}@exemplo.com"), curso=curso)

        recomendacoes = sum(t.recomendacoes.count() for t in tentativas)
        self.assertAlmostEqual(metricas.conversao_geral(None), K_MINIMO / recomendacoes * 100)

    def test_aderencia_some_com_poucos_primeiros(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        Interesse.objects.create(
            usuario=self.criar_usuario("um@exemplo.com"), curso=curso, rank_snapshot=1, era_principal=True
        )

        aderencia = self.client.get(reverse("painel-quiz")).context["aderencia"]

        self.assertIsNone(aderencia["taxa"])
```

> [!tip] 🎓 Entenda: o teste que prova "nenhum botão fantasma"
> `test_nenhum_template_do_painel_usa_botao_fantasma` abre **cada arquivo** da pasta de templates do painel e procura as classes proibidas. `test_tela_servida_tambem_nao_tem_botao_fantasma` faz o mesmo no **HTML que o servidor manda**, que pega também o que vem de `include`. Para a banca, é a prova de que a regra do design vale no código.

### 🤝 Ponto de encontro da etapa 1

Quem hospeda roda tudo:

```bash
cd backend
python manage.py test                                # 96 testes
python manage.py makemigrations --check --dry-run   # No changes detected
python manage.py runserver
```

E o grupo confere junto, com um usuário staff:

- [ ] `/painel/` mostra o menu preto, os 4 KPIs, a linha, a rosca, o link ativo e a atividade recente
- [ ] Trocar o período para "Anual" e clicar em "Quiz" no menu mantém "Anual"
- [ ] "Gerar link" e "Fechar links" abrem a janela de confirmação; "Cancelar" não envia nada; "Fechar links" tem o botão vermelho de perigo
- [ ] Acessibilidade: "Fonte grande" e "Alto contraste" funcionam e continuam ligados depois de recarregar
- [ ] No celular (375px): barra de baixo, KPIs em 2×2, e "Mais" abre o menu por cima
- [ ] Com menos de 5 testes no período, só o total aparece, com o aviso de privacidade

---

# Etapa 2 · Cursos e Áreas, Links e Lista de interesse

## 2.1 `static/css/painel.css`

Antes do bloco `/* Modal de confirmação */`:

```css
/* Funil da lista de interesse e QR dos links */

.painel-funil {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 0 0 16px;
  padding: 0;
  list-style: none;
}

.painel-funil li {
  display: grid;
  gap: 4px;
  border-left: 4px solid var(--marca);
  background: var(--marca-clarinho);
  text-align: center;
}

.painel-funil b {
  color: var(--titulo);
  font-size: 1.5rem;
}

.painel-qr {
  width: 88px;
  height: 88px;
  padding: 4px;
  border: 1px solid var(--linha);
  border-radius: 8px;
  background: var(--branco);
}

.painel-qr img,
.painel-qr canvas {
  width: 100% !important;
  height: 100% !important;
}
```

E dentro do `@media (max-width: 760px)`, depois de `.painel-grade--2`:

```css
  .painel-funil {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
```

## 2.2 `static/js/painel.js`: o QR code

Antes do bloco `data-copiar`:

```js
    // QR dos links: o qrcode.min.js só é carregado na tela de links, antes deste arquivo.
    if (window.QRCode) {
        document.querySelectorAll("[data-qr]").forEach(function (caixa) {
            new QRCode(caixa, { text: caixa.dataset.qr, width: 160, height: 160 });
        });
    }
```

> [!warning] Combine com B
> Esse código só funciona se a biblioteca de QR rodar **antes** do `painel.js`. B muda a ordem dos scripts no `base_painel.html` nesta etapa. Se o QR não aparecer e o console não mostrar erro nenhum, é a ordem.

## 2.3 Testes: `painel/tests/test_telas.py`

No topo, o import de `quiz.models` passa a trazer o link:

```python
from quiz.models import QuestionarioLink, Tentativa_de_resposta
```

No `test_tela_servida_tambem_nao_tem_botao_fantasma`, as telas novas entram na volta do `for`:

```python
        for tela in ("painel-dashboard", "painel-quiz", "painel-cursos", "painel-links", "painel-interesse"):
```

E uma classe nova no fim do arquivo:

```python
class TelasDeCadastroTest(BasePainel):
    """Etapa 2: Cursos e Áreas, Links de acesso e Lista de interesse."""

    TELAS = ("painel-cursos", "painel-links", "painel-interesse")

    def setUp(self):
        super().setUp()
        self.staff = self.criar_staff()

    def test_so_staff_entra(self):
        comum = self.criar_usuario("aluno@exemplo.com")
        for tela in self.TELAS:
            with self.subTest(tela=tela):
                self.client.logout()
                self.assertEqual(self.client.get(reverse(tela)).status_code, 302)
                self.client.force_login(comum)
                self.assertNotEqual(self.client.get(reverse(tela)).status_code, 200)
                self.client.force_login(self.staff)
                self.assertEqual(self.client.get(reverse(tela)).status_code, 200)

    def test_testes_por_link_sao_suprimidos(self):
        self.client.force_login(self.staff)
        link = QuestionarioLink.objects.create(criado_por=self.staff)
        tentativas = self.criar_tentativas(quantidade=2)
        Tentativa_de_resposta.objects.filter(pk__in=[t.pk for t in tentativas]).update(questionario_link=link)

        linhas = self.client.get(reverse("painel-links")).context["links"]

        self.assertTrue(linhas[0]["suprimido"])
        self.assertIsNone(linhas[0]["total"])

    def test_fechar_um_link_nao_fecha_os_outros(self):
        self.client.force_login(self.staff)
        primeiro, segundo = (QuestionarioLink.objects.create(criado_por=self.staff) for _ in range(2))

        resposta = self.client.post(
            reverse("painel-fechar-um-link", args=[primeiro.pk]), {"voltar": "painel-links"}
        )

        self.assertRedirects(resposta, reverse("painel-links"))
        primeiro.refresh_from_db()
        segundo.refresh_from_db()
        self.assertFalse(primeiro.ativo)
        self.assertTrue(segundo.ativo)

    def test_voltar_para_endereco_de_fora_cai_no_inicio(self):
        self.client.force_login(self.staff)

        resposta = self.client.post(reverse("painel-gerar-link"), {"voltar": "https://exemplo.com/"})

        self.assertRedirects(resposta, reverse("painel-dashboard"))

    def test_lista_de_interesse_nao_mostra_quem_salvou(self):
        self.client.force_login(self.staff)
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        emails = [f"pessoa{i}@exemplo.com" for i in range(K_MINIMO)]
        for email in emails:
            Interesse.objects.create(usuario=self.criar_usuario(email), curso=curso, era_principal=True)

        resposta = self.client.get(reverse("painel-interesse"))

        linha = next(l for l in resposta.context["por_curso"] if l["id"] == curso.id)
        self.assertEqual(linha["total"], K_MINIMO)
        self.assertEqual(linha["taxa_principal"], 100)
        for email in emails:
            self.assertNotContains(resposta, email)

    def test_taxa_de_1o_colocado_some_se_a_contagem_for_pequena(self):
        self.client.force_login(self.staff)
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        for i in range(K_MINIMO):
            Interesse.objects.create(
                usuario=self.criar_usuario(f"pessoa{i}@exemplo.com"), curso=curso, era_principal=(i == 0)
            )

        linhas = self.client.get(reverse("painel-interesse")).context["por_curso"]

        linha = next(l for l in linhas if l["id"] == curso.id)
        self.assertTrue(linha["principal_suprimido"])
        self.assertIsNone(linha["taxa_principal"])

    def test_funil_segue_a_ordem_dos_status(self):
        self.client.force_login(self.staff)
        self.criar_tentativas(quantidade=K_MINIMO)

        funil = self.client.get(reverse("painel-interesse")).context["funil"]

        self.assertEqual([etapa["status"] for etapa in funil], [chave for chave, _ in Interesse.STATUS])
```

> [!tip] 🎓 Entenda: testar o que **não** pode acontecer
> `test_voltar_para_endereco_de_fora_cai_no_inicio` manda `voltar=https://exemplo.com/` e confere que o painel **não** obedece. Muitos dos testes mais importantes são assim: provam que o ataque não funciona, e não só que o caminho feliz funciona.

### 🤝 Ponto de encontro da etapa 2

```bash
python manage.py test                                # 103 testes
```

- [ ] O menu tem 5 itens e marca a tela atual
- [ ] **Links**: um link ativo mostra o QR; "Gerar link" no topo da tela volta para a própria tela de links; "Fechar" fecha só aquele link e pede confirmação em vermelho
- [ ] **Cursos**: os 20 cursos ativos, com cadeado onde a contagem é menor que 5; "Novo curso" e o lápis abrem o admin
- [ ] **Lista de interesse**: o funil na ordem Interessado → Contatado → Descartado → Removido; nenhum e-mail na página (`Ctrl+F` por `@`)

---

# Etapa 3 · % concluídos e tempo típico

Nesta etapa não há CSS nem JS: só testes. Escreva enquanto A trabalha, mas só rode depois que A avisar que a migração foi aplicada. O arquivo importa o `InicioDeQuiz` logo na primeira linha, então, antes do model existir, **nenhum** teste dele roda, nem o do filtro `duracao`.

## 3.1 `quiz/tests/test_inicio.py` (novo)

```python
from datetime import timedelta

from django.urls import reverse

from painel import metricas
from painel.privacidade import K_MINIMO
from painel.templatetags.painel_extras import duracao
from quiz.models import InicioDeQuiz, Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class InicioDoQuizTest(BaseEducMatch):
    """Etapa 3: o início do quiz é contado uma vez e vira iniciado_em na tentativa."""

    def comecar(self, nome="Visitante"):
        return self.client.get(reverse("quiz-inicio"), {"respondido_por": nome, "etapa": 1})

    def test_abrir_a_primeira_questao_conta_um_inicio(self):
        self.comecar()

        self.assertEqual(InicioDeQuiz.objects.count(), 1)

    def test_recarregar_nao_conta_de_novo(self):
        self.comecar()
        self.comecar()

        self.assertEqual(InicioDeQuiz.objects.count(), 1)

    def test_concluir_grava_o_inicio_na_tentativa_e_limpa_a_sessao(self):
        self.comecar()
        inicio = InicioDeQuiz.objects.get()

        self.responder_tudo()

        tentativa = Tentativa_de_resposta.objects.get()
        self.assertEqual(tentativa.iniciado_em, inicio.criado_em)
        self.assertNotIn("quiz_iniciado_em", self.client.session)

    def test_proximo_quiz_conta_outro_inicio(self):
        self.comecar()
        self.responder_tudo()
        self.comecar()

        self.assertEqual(InicioDeQuiz.objects.count(), 2)

    def test_post_direto_fica_sem_inicio(self):
        self.responder_tudo()

        self.assertIsNone(Tentativa_de_resposta.objects.get().iniciado_em)

    def test_inicio_nao_guarda_quem_comecou(self):
        campos = {campo.name for campo in InicioDeQuiz._meta.get_fields()}

        self.assertEqual(campos, {"id", "criado_em", "questionario_link"})


class MetricasDeConclusaoTest(BaseEducMatch):
    def concluir(self, quantidade, minutos=8):
        for _ in range(quantidade):
            tentativa = self.criar_tentativa()
            tentativa.iniciado_em = tentativa.criado_em - timedelta(minutes=minutos)
            tentativa.save(update_fields=["iniciado_em"])

    def test_taxa_de_conclusao(self):
        for _ in range(K_MINIMO * 2):
            InicioDeQuiz.objects.create()
        self.concluir(K_MINIMO)

        self.assertEqual(metricas.taxa_de_conclusao(None), 50.0)

    def test_taxa_some_com_poucos_inicios(self):
        InicioDeQuiz.objects.create()

        self.assertIsNone(metricas.taxa_de_conclusao(None))

    def test_tempo_tipico_e_a_mediana(self):
        self.concluir(K_MINIMO - 1, minutos=8)
        self.concluir(1, minutos=60 * 24)  # aba esquecida aberta por um dia

        self.assertEqual(metricas.tempo_tipico(None), timedelta(minutes=8))

    def test_tempo_some_com_poucas_tentativas(self):
        self.concluir(K_MINIMO - 1)

        self.assertIsNone(metricas.tempo_tipico(None))

    def test_formato_da_duracao(self):
        self.assertEqual(duracao(timedelta(minutes=8, seconds=42)), "08:42")
        self.assertEqual(duracao(timedelta(hours=1, minutes=5)), "1h05")
```

> [!tip] 🎓 Entenda: os testes contam uma história
> Leia os nomes em sequência: abrir conta um início → recarregar **não** conta de novo → concluir grava o início e limpa a sessão → o próximo quiz conta outro → o envio direto fica sem início → o início não guarda quem começou. Cada linha da tabela da spec de A virou um teste. Quando alguém perguntar "e se recarregar a página?", a resposta é o nome do teste.

> [!note] 🎓 Entenda: o teste da mediana
> `test_tempo_tipico_e_a_mediana` cria 4 tentativas de 8 minutos e **uma de um dia inteiro**. A mediana tem de continuar 8 minutos. É o exemplo da aba esquecida, transformado em prova.

### 🤝 Ponto de encontro da etapa 3

```bash
python manage.py makemigrations --check --dry-run   # No changes detected
python manage.py test                                # 114 testes
```

- [ ] Responda o quiz uma vez pela tela de introdução. No `python manage.py shell`: `InicioDeQuiz.objects.count()` dá 1 e a última tentativa tem `iniciado_em` preenchido
- [ ] Recarregue a 1ª questão antes de terminar: continua 1 início
- [ ] Em `/painel/quiz/`, com 5 ou mais testes novos, "% concluídos" e "Tempo típico" aparecem; com menos, "—"

---

# Etapa 4 · Avaliação de fim de curso (página do aluno)

## 4.1 `static/css/avaliacao.css` (novo)

```css
/* Avaliação de fim de curso (página do aluno). */

.avaliacao {
  display: grid;
  gap: 22px;
  max-width: 720px;
  margin: 0 auto;
}

.avaliacao__topo h1 {
  margin-bottom: 4px;
}

.avaliacao__anonimo {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.avaliacao__pergunta {
  margin: 0;
  padding: 18px 0 0;
  border: 0;
  border-top: 1px solid var(--linha);
}

.avaliacao__pergunta legend {
  padding: 0;
  margin-bottom: 12px;
  font-weight: 700;
}

.avaliacao__pergunta--erro legend {
  color: var(--erro);
}

.avaliacao__opcoes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.avaliacao__opcoes--nps {
  display: grid;
  grid-template-columns: repeat(11, minmax(0, 1fr));
  gap: 6px;
}

/* O rádio continua no lugar (teclado e leitor de tela), só fica invisível. */
.avaliacao__opcao {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--alvo);
  min-height: var(--alvo);
  padding: 0 14px;
  border-radius: var(--raio-botao);
  background: var(--gelo);
  color: var(--tinta);
  font-weight: 600;
  cursor: pointer;
  transition: background var(--dur-rapida) var(--ease-padrao);
}

.avaliacao__opcao input {
  position: absolute;
  inset: 0;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}

.avaliacao__opcao:hover {
  background: #e4deda;
}

.avaliacao__opcao:has(input:checked) {
  background: var(--marca);
  color: var(--branco);
}

.avaliacao__opcao:has(input:focus-visible) {
  outline: 3px solid var(--foco);
  outline-offset: 2px;
}

.avaliacao__opcoes--nps .avaliacao__opcao {
  min-width: 0;
  padding: 0;
}

.avaliacao__legenda {
  display: flex;
  justify-content: space-between;
  margin: 6px 0 0;
  color: var(--texto-3);
  font-size: var(--pequeno);
}

.avaliacao textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--linha);
  border-radius: var(--raio-botao);
  font: inherit;
}

@media (max-width: 560px) {
  /* 11 botões não cabem numa linha de celular: 0 a 5 em cima, 6 a 10 embaixo. */
  .avaliacao__opcoes--nps {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}
```

> [!tip] 🎓 Entenda: rádio de verdade, com cara de botão
> As notas são `<input type="radio">` de verdade, só invisíveis (`opacity: 0`) por cima do rótulo. Setas do teclado, `Tab` e leitor de tela funcionam sem nenhuma linha de JS. O `:has(input:checked)` pinta de vermelho o rótulo cujo rádio está marcado, e o `:has(input:focus-visible)` desenha o contorno de foco de quem navega pelo teclado.

## 4.2 Testes: a pasta `avaliacao/tests/`

Crie `avaliacao/tests/__init__.py` vazio e a base, que todos os testes da avaliação usam:

### `avaliacao/tests/base.py`

```python
from io import StringIO

from django.core.management import call_command
from django.urls import reverse

from avaliacao.models import LinkDeAvaliacao, Pergunta
from catalogo.models import Curso
from quiz.tests.base import BaseEducMatch


class BaseAvaliacao(BaseEducMatch):
    """Catálogo real + as perguntas do seed_avaliacao."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("seed_avaliacao", stdout=StringIO())

    def criar_link(self, curso=None, turma="2026/1 · Noite", **extra):
        return LinkDeAvaliacao.objects.create(curso=curso or Curso.objects.first(), turma=turma, **extra)

    def respostas_validas(self, nota=9, escala=4, escolha="Sim", texto=""):
        dados = {}
        for pergunta in Pergunta.objects.filter(ativa=True):
            chave = f"pergunta_{pergunta.id}"
            dados[chave] = {"nps": nota, "escala": escala, "escolha": escolha, "texto": texto}[pergunta.tipo]
        return dados

    def enviar(self, link, dados):
        return self.client.post(reverse("avaliacao-responder", args=[link.token]), dados)
```

> [!tip] 🎓 Entenda: `setUpTestData`
> Roda **uma vez por classe**, e não uma vez por teste. Os seeds do catálogo e das perguntas são lentos; rodar 11 vezes seria desperdício. Cada teste, por sua vez, roda dentro de uma transação que é desfeita no fim, então um teste nunca suja o outro.

### `avaliacao/tests/test_resposta.py`

```python
from io import StringIO

from django.core.management import call_command
from django.db import models
from django.urls import reverse

from avaliacao.models import ItemDeResposta, Pergunta, RespostaDeAvaliacao
from avaliacao.tests.base import BaseAvaliacao


class RespostaDoAlunoTest(BaseAvaliacao):
    """Etapa 4: o aluno responde pelo link da turma, sem conta e sem se identificar."""

    def test_seed_cria_sete_perguntas_e_pode_rodar_de_novo(self):
        call_command("seed_avaliacao", stdout=StringIO())

        self.assertEqual(Pergunta.objects.count(), 7)

    def test_pagina_mostra_curso_e_turma(self):
        link = self.criar_link()

        resposta = self.client.get(reverse("avaliacao-responder", args=[link.token]))

        self.assertContains(resposta, link.curso.nome_curso)
        self.assertContains(resposta, "2026/1 · Noite")

    def test_resposta_completa_e_gravada(self):
        link = self.criar_link()

        resposta = self.enviar(link, self.respostas_validas(texto="Mais aulas práticas"))

        self.assertRedirects(resposta, reverse("avaliacao-obrigado", args=[link.token]))
        gravada = RespostaDeAvaliacao.objects.get()
        self.assertEqual(gravada.link, link)
        self.assertEqual(gravada.itens.count(), 7)
        self.assertEqual(gravada.itens.get(pergunta__tipo="nps").numero, 9)
        self.assertEqual(gravada.itens.get(pergunta__tipo="texto").texto, "Mais aulas práticas")

    def test_opcional_em_branco_nao_vira_item(self):
        link = self.criar_link()

        self.enviar(link, self.respostas_validas(texto=""))

        self.assertEqual(ItemDeResposta.objects.count(), 6)

    def test_falta_obrigatoria_nao_grava(self):
        link = self.criar_link()
        dados = self.respostas_validas()
        dados.pop(f"pergunta_{Pergunta.objects.get(ordem=1).id}")

        resposta = self.enviar(link, dados)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Faltou responder")
        self.assertFalse(RespostaDeAvaliacao.objects.exists())

    def test_nota_fora_da_escala_e_recusada(self):
        link = self.criar_link()

        self.enviar(link, self.respostas_validas(nota=11))

        self.assertFalse(RespostaDeAvaliacao.objects.exists())

    def test_link_fechado_da_404(self):
        link = self.criar_link(ativo=False)

        resposta = self.client.get(reverse("avaliacao-responder", args=[link.token]))

        self.assertEqual(resposta.status_code, 404)

    def test_mesmo_navegador_nao_envia_duas_vezes(self):
        link = self.criar_link()
        self.enviar(link, self.respostas_validas())

        resposta = self.enviar(link, self.respostas_validas())

        self.assertRedirects(resposta, reverse("avaliacao-obrigado", args=[link.token]))
        self.assertEqual(RespostaDeAvaliacao.objects.count(), 1)

    def test_pergunta_inativa_some_do_formulario(self):
        link = self.criar_link()
        Pergunta.objects.filter(ordem=5).update(ativa=False)

        resposta = self.client.get(reverse("avaliacao-responder", args=[link.token]))

        self.assertNotContains(resposta, Pergunta.objects.get(ordem=5).texto)


class AnonimatoTest(BaseAvaliacao):
    def test_resposta_nao_tem_onde_guardar_quem_respondeu(self):
        for model in (RespostaDeAvaliacao, ItemDeResposta):
            with self.subTest(model=model.__name__):
                ligados_a_usuario = [
                    campo.name for campo in model._meta.get_fields()
                    if campo.is_relation and campo.related_model and campo.related_model._meta.label == "accounts.User"
                ]
                self.assertEqual(ligados_a_usuario, [])

    def test_resposta_guarda_o_dia_e_nao_a_hora(self):
        campo = RespostaDeAvaliacao._meta.get_field("respondido_em")

        self.assertIs(type(campo), models.DateField)
```

> [!important] 🎓 Entenda: testar o desenho, e não só o comportamento
> `AnonimatoTest` não envia formulário nenhum. Ele olha os **campos dos models** e falha se um dia alguém acrescentar um campo ligado ao usuário, ou trocar o dia por data e hora. É um teste que protege uma **decisão**, e não só um comportamento.

### 🤝 Ponto de encontro da etapa 4

```bash
python manage.py makemigrations --check --dry-run   # No changes detected
python manage.py test                                # 125 testes
```

- [ ] No admin, crie um **Link de avaliação** para um curso e uma turma
- [ ] Abra `/avaliacao/<token>/` no celular (375px): curso e turma no topo, o aviso de anonimato, e a nota de 0 a 10 em duas linhas
- [ ] Envie sem responder nada: as obrigatórias ficam vermelhas e nada é gravado
- [ ] Responda tudo: aparece a tela de agradecimento; abrir o link de novo no mesmo navegador volta para o agradecimento
- [ ] Desmarque `ativo` do link no admin: o endereço mostra "link encerrado"

---

# Etapa 5 · Avaliações no painel

## 5.1 `static/css/painel.css`

Antes do bloco `/* Modal de confirmação */`:

```css
/* Avaliações de fim de curso */

.painel-form-linha {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.painel-form-linha .painel-campo {
  flex: 1 1 220px;
}

.painel-distribuicao {
  display: grid;
  gap: 8px;
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
  font-size: 0.85rem;
}

.painel-distribuicao li {
  display: grid;
  grid-template-columns: minmax(48px, 120px) 1fr 56px;
  align-items: center;
  gap: 10px;
}

.painel-distribuicao b {
  text-align: right;
}

.painel-comentarios {
  display: grid;
  gap: 8px;
  max-height: 320px;
  margin: 8px 0 0;
  padding: 0;
  overflow-y: auto;
  list-style: none;
}

.painel-comentarios li {
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--fundo);
  font-size: 0.9rem;
}
```

## 5.2 Testes: `painel/tests/test_avaliacoes.py` (novo)

```python
from django.urls import reverse

from avaliacao.models import LinkDeAvaliacao, RespostaDeAvaliacao
from avaliacao.tests.base import BaseAvaliacao
from catalogo.models import Curso
from painel import metricas_avaliacao
from painel.privacidade import K_MINIMO
from painel.tests.test_telas import BOTOES_FANTASMA


class AvaliacoesNoPainelTest(BaseAvaliacao):
    """Etapa 5: links por turma, resultados agregados e CSV, sempre com k = 5."""

    def setUp(self):
        super().setUp()
        self.staff = self.criar_usuario("coord@exemplo.com", is_staff=True)
        self.client.force_login(self.staff)
        self.curso = Curso.objects.filter(is_active=True).first()

    def responder(self, link, quantidade, **valores):
        """Cada resposta num navegador novo: a trava de sessão não deixa repetir no mesmo."""
        for _ in range(quantidade):
            self.client.logout()
            self.enviar(link, self.respostas_validas(**valores))
        self.client.force_login(self.staff)

    def test_so_staff_entra(self):
        comum = self.criar_usuario("aluno@exemplo.com")
        for tela in ("painel-avaliacoes", "painel-avaliacoes-resultados", "painel-avaliacoes-csv"):
            with self.subTest(tela=tela):
                self.client.force_login(comum)
                self.assertNotEqual(self.client.get(reverse(tela)).status_code, 200)

    def test_gerar_link_para_turma(self):
        resposta = self.client.post(
            reverse("painel-avaliacoes-gerar"), {"curso": self.curso.id, "turma": "2026/1 · Noite"}
        )

        self.assertRedirects(resposta, reverse("painel-avaliacoes"))
        link = LinkDeAvaliacao.objects.get()
        self.assertEqual((link.curso, link.turma, link.criado_por), (self.curso, "2026/1 · Noite", self.staff))

    def test_curso_inativo_nao_ganha_link(self):
        inativo = Curso.objects.create(
            nome_curso="Antigo", descricao="-", area_principal=self.curso.area_principal, duracao=10, is_active=False
        )

        self.client.post(reverse("painel-avaliacoes-gerar"), {"curso": inativo.id, "turma": "X"})

        self.assertFalse(LinkDeAvaliacao.objects.exists())

    def test_fechar_link_de_avaliacao(self):
        link = self.criar_link(self.curso)

        self.client.post(reverse("painel-avaliacoes-fechar", args=[link.pk]))

        link.refresh_from_db()
        self.assertFalse(link.ativo)

    def test_poucas_respostas_nao_mostram_perguntas(self):
        self.responder(self.criar_link(self.curso), K_MINIMO - 1)

        contexto = self.client.get(reverse("painel-avaliacoes-resultados")).context

        self.assertFalse(contexto["avaliacoes_com_massa"])
        self.assertNotIn("blocos", contexto)
        linha = next(l for l in contexto["resumo"] if l["curso_id"] == self.curso.id)
        self.assertIsNone(linha["nps"])
        self.assertIsNone(linha["media"])

    def test_resultados_com_massa(self):
        link = self.criar_link(self.curso)
        self.responder(link, K_MINIMO, nota=10, escala=4, texto="Mais prática")

        contexto = self.client.get(reverse("painel-avaliacoes-resultados"), {"curso": self.curso.id}).context

        blocos = {bloco["pergunta"].tipo: bloco for bloco in contexto["blocos"]}
        self.assertEqual(blocos["nps"]["nps"], 100)
        self.assertEqual(blocos["escala"]["media"], 4)
        self.assertEqual(blocos["texto"]["textos"], ["Mais prática"] * K_MINIMO)
        opcoes = {item["rotulo"]: item for item in blocos["escolha"]["distribuicao"]}
        self.assertEqual(opcoes["Sim"]["total"], K_MINIMO)
        self.assertTrue(opcoes["Não"]["suprimido"], "zero também é menos que K")

    def test_curso_pequeno_fica_fora_do_todos(self):
        """Sem isso, NPS geral - NPS do curso grande devolveria a opinião do curso pequeno."""
        outro = Curso.objects.filter(is_active=True).exclude(pk=self.curso.pk).first()
        self.responder(self.criar_link(self.curso), K_MINIMO, nota=10)
        self.responder(self.criar_link(outro), 2, nota=0)

        contexto = self.client.get(reverse("painel-avaliacoes-resultados")).context

        nps = next(bloco for bloco in contexto["blocos"] if bloco["pergunta"].tipo == "nps")
        self.assertEqual(nps["nps"], 100)
        self.assertEqual(contexto["fora_do_todos"], 1)

    def test_nps_conta_promotores_menos_detratores(self):
        self.assertEqual(metricas_avaliacao.nps([10, 9, 8, 6]), 25)
        self.assertIsNone(metricas_avaliacao.nps([]))

    def test_csv_sai_sem_turma_data_e_em_ordem(self):
        self.responder(self.criar_link(self.curso, turma="Turma Secreta"), K_MINIMO)

        resposta = self.client.get(reverse("painel-avaliacoes-csv"))

        corpo = resposta.content.decode("utf-8-sig")
        linhas = corpo.strip().splitlines()
        self.assertEqual(linhas[0], "curso;pergunta;resposta")
        self.assertEqual(len(linhas) - 1, K_MINIMO * 6, "6 itens por resposta (o texto ficou em branco)")
        self.assertNotIn("Turma Secreta", corpo)
        # Cada pergunta num bloco só: nada na ordem liga um item ao seu vizinho de resposta.
        perguntas = [linha.split(";")[1] for linha in linhas[1:]]
        blocos = [p for i, p in enumerate(perguntas) if i == 0 or p != perguntas[i - 1]]
        self.assertEqual(len(blocos), len(set(perguntas)))

    def test_csv_com_poucas_respostas_e_negado(self):
        self.responder(self.criar_link(self.curso), K_MINIMO - 1)

        resposta = self.client.get(reverse("painel-avaliacoes-csv"))

        self.assertRedirects(resposta, reverse("painel-avaliacoes-resultados"))

    def test_kpi_na_inicio(self):
        self.responder(self.criar_link(self.curso), 2)

        contexto = self.client.get(reverse("painel-dashboard")).context

        self.assertEqual(contexto["avaliacoes_no_periodo"], 2)
        self.assertEqual(RespostaDeAvaliacao.objects.count(), 2)

    def test_telas_novas_sem_botao_fantasma(self):
        self.responder(self.criar_link(self.curso), K_MINIMO)
        for tela in ("painel-avaliacoes", "painel-avaliacoes-resultados"):
            corpo = self.client.get(reverse(tela)).content.decode()
            for classe in BOTOES_FANTASMA:
                with self.subTest(tela=tela, classe=classe):
                    self.assertNotIn(classe, corpo)
```

> [!danger] 🎓 Entenda: o teste do vazamento por diferença
> `test_curso_pequeno_fica_fora_do_todos` monta exatamente o ataque: um curso com 5 notas 10 e outro com 2 notas 0. Se o curso pequeno entrasse no "Todos", o NPS geral cairia e, comparando com o do curso grande, daria para descobrir as notas dos 2. O teste exige que o NPS de "Todos" seja **100**, ou seja, que o curso pequeno ficou de fora.

> [!tip] 🎓 Entenda: um navegador por aluno
> O método `responder` do teste faz `logout` antes de cada envio. Sem isso, a trava de "já respondeu" (que usa a sessão) bloquearia do segundo envio em diante, e o teste mediria a trava, e não os resultados.

### 🤝 Ponto de encontro da etapa 5 (o último)

```bash
python manage.py test                                # 137 testes
python manage.py makemigrations --check --dry-run   # No changes detected
```

- [ ] **Avaliações**: gerar um link (curso + turma) pede confirmação, mostra a mensagem de sucesso dentro do painel, e o link aparece com QR
- [ ] Respondam pelo link em **5 janelas anônimas** diferentes (a trava impede repetir na mesma)
- [ ] **Resultados**: com 4 respostas, só a tabela por curso aparece, com cadeado; com 5, os cards por pergunta aparecem
- [ ] Um segundo curso com 1 ou 2 respostas: em "Todos", aparece o aviso de que ele ficou fora, e os números dos cards não mudam
- [ ] **Exportar CSV** abre no Excel com acentos certos, sem turma e sem data
- [ ] A Início mostra o KPI "Avaliações de curso"

> [!success] Fim
> Com os 137 testes passando e os cinco pontos de encontro conferidos, o dashboard está pronto. Voltem ao [[guia-dashboard-live-share|guia]] para o checklist final.
