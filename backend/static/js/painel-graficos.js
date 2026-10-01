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