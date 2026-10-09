//frontend/script.js 

const API_URL = "http://localhost:8000/api";

// Controle de estado global da paginação
let paginaAtual = 1;
let tipoAtual = 'estagios';
let filtroVigentesAtivo = false;

// Quando a página carregar, puxa os estágios por padrão
window.onload = () => {
    carregarDados('estagios');
};

function toggleFiltroVigentes() {
    const checkbox = document.getElementById('filtroVigentes');
    filtroVigentesAtivo = checkbox.checked;
    carregarDados(tipoAtual, 1);
}

async function carregarDados(tipo, novaPagina = 1) {
    tipoAtual = tipo;
    paginaAtual = novaPagina;

    const container = document.getElementById('container-vagas');
    container.style.display = 'grid';
    container.innerHTML = '<p class="carregando">Buscando dados no banco...</p>';

    document.querySelectorAll('.filtro-btn').forEach(botao => {
        botao.classList.remove('ativo');
    });

    const botaoAtivo = document.getElementById(`btn-${tipo}`);
    if(botaoAtivo) botaoAtivo.classList.add('ativo');

    try {
        let url = `${API_URL}/${tipo}?pagina=${paginaAtual}&limite=6`;
        if (filtroVigentesAtivo) {
            url += `&apenas_vigentes=true`;
        }

        const resposta = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            // Add timeout to avoid hanging requests
            signal: AbortSignal.timeout(10000) // 10 seconds timeout
        });
        
        if (!resposta.ok) {
            throw new Error(`Erro na requisição: ${resposta.status} - ${resposta.statusText}`);
        }
        
        const objetoPaginado = await resposta.json();

        renderizarCards(objetoPaginado.dados);
        renderizarControlesPaginacao(objetoPaginado.pagina_atual, objetoPaginado.total_documentos, objetoPaginado.limite_por_pagina);

    } catch (erro) {
        console.error("Erro ao buscar dados paginados:", erro);
        container.innerHTML = `<p class="carregando" style="color: red;">Erro ao conectar com a API: ${erro.message || 'O FastAPI está rodando?'}</p>`;
        
        // Additional troubleshooting info
        console.log("Tentando verificar status da API...");
        try {
            const statusResponse = await fetch(`${API_URL}/../`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                signal: AbortSignal.timeout(5000)
            });
            console.log("Resposta do status da API:", statusResponse.status);
        } catch (statusError) {
            console.log("Erro ao verificar status da API:", statusError);
        }
    }
}
function renderizarControlesPaginacao(atual, total, limite) {
    const antigo = document.getElementById('bloco-paginacao');
    if(antigo) antigo.remove();

    const totalPaginas = Math.max(1, Math.ceil((total || 0) / (limite || 6)));

    // Se houver apenas 1 página e poucos itens, não precisa exibir os botões
    if (totalPaginas <= 1 && total <= limite) return;

    const mainContainer = document.querySelector('main');
    const blocoPaginacao = document.createElement('div');
    blocoPaginacao.id = 'bloco-paginacao';

    blocoPaginacao.style.cssText = `
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 15px;
        margin-top: 40px;
    `;
    blocoPaginacao.innerHTML = `
        <button ${atual === 1 ? 'disabled' : ''} onclick="carregarDados('${tipoAtual}', ${atual - 1})"
            style="background: #fff; color: var(--azul-escuro); border: 3px solid var(--azul-escuro); padding: 8px 16px; font-weight: bold; border-radius: 8px; cursor: pointer; box-shadow: 3px 3px 0 var(--azul-escuro); opacity: ${atual === 1 ? '0.5' : '1'}">
            ◀ Anterior
        </button>
        <span style="font-weight: bold; color: var(--azul-escuro);">Página ${atual} de ${totalPaginas}</span>
        <button ${atual >= totalPaginas ? 'disabled' : ''} onclick="carregarDados('${tipoAtual}', ${atual + 1})"
            style="background: #fff; color: var(--azul-escuro); border: 3px solid var(--azul-escuro); padding: 8px 16px; font-weight: bold; border-radius: 8px; cursor: pointer; box-shadow: 3px 3px 0 var(--azul-escuro); opacity: ${atual >= totalPaginas ? '0.5' : '1'}">
            Próximo ▶
        </button>
    `;

    mainContainer.appendChild(blocoPaginacao);
}
// 1. Pesquisa Textual via Índices Otimizados do MongoDB
async function realizarPesquisa() {
    const termo = document.getElementById('input-busca').value;
    if (!termo) return;

    const container = document.getElementById('container-vagas');
    container.innerHTML = '<p class="carregando">Consultando índices no MongoDB...</p>';

    const antigo = document.getElementById('bloco-paginacao');
    if(antigo) antigo.remove();

    try {
        const resposta = await fetch(`${API_URL}/pesquisar?termo=${termo}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: AbortSignal.timeout(10000)
        });
        
        if (!resposta.ok) {
            throw new Error(`Erro na pesquisa: ${resposta.status} - ${resposta.statusText}`);
        }
        
        const dados = await resposta.json();
        renderizarCards(dados);
        document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('ativo'));
    } catch (e) {
        console.error("Erro na pesquisa:", e);
        container.innerHTML = `<div class="status-box" style="border-color: var(--color-red);"><h3 class="status-box-titulo" style="color: var(--color-red);">Erro na Pesquisa</h3><p class="status-box-texto">${e.message}</p></div>`;
    }
}
async function carregarEstatisticas() {
    const antigo = document.getElementById('bloco-paginacao');
    if(antigo) antigo.remove();

    const container = document.getElementById('container-vagas');
    container.style.display = 'block';
    container.innerHTML = '<p class="carregando">Gerando painel visual...</p>';

    document.querySelectorAll('.filtro-btn').forEach(botao => {
        botao.classList.remove('ativo');
    });
    document.getElementById('btn-analises').classList.add('ativo');

    try {
        const resposta = await fetch(`${API_URL}/estatisticas`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: AbortSignal.timeout(10000)
        });
        
        if (!resposta.ok) {
            throw new Error(`Erro ao carregar estatísticas: ${resposta.status} - ${resposta.statusText}`);
        }
        
        const dados = await resposta.json();

        let html = `
            <div class="dashboard-container">
                <div class="dashboard-header">
                    <h2 class="dashboard-titulo">Indicadores Globais <span>(Tempo Real)</span></h2>
                    <p class="dashboard-subtitulo">Distribuição analítica volumétrica de oportunidades coletadas por agentes automatizados.</p>
                </div>

                <div class="dash-grid-contadores">
                    <div class="dash-card-contador contador-prae">
                        <span class="contador-icone">🎓</span>
                        <div class="contador-info">
                            <h4 class="contador-label">Estágios (PRAE)</h4>
                            <p class="contador-numero">${dados.totais.estagios}</p>
                        </div>
                    </div>
                    <div class="dash-card-contador contador-proex">
                        <span class="contador-icone">💰</span>
                        <div class="contador-info">
                            <h4 class="contador-label">Bolsas (PROEX)</h4>
                            <p class="contador-numero">${dados.totais.bolsas}</p>
                        </div>
                    </div>
                    <div class="dash-card-contador contador-ufersa">
                        <span class="contador-icone">🏛️</span>
                        <div class="contador-info">
                            <h4 class="contador-label">UFERSA Editais</h4>
                            <p class="contador-numero">${dados.totais.ufersa}</p>
                        </div>
                    </div>
                    <div class="dash-card-contador contador-noticias">
                        <span class="contador-icone">⚡</span>
                        <div class="contador-info">
                            <h4 class="contador-label">Notícias Tech</h4>
                            <p class="contador-numero">${dados.totais.noticias}</p>
                        </div>
                    </div>
                    <div class="dash-card-contador" style="border: 3px solid var(--azul-escuro); box-shadow: 4px 4px 0 var(--azul-escuro);">
                        <span class="contador-icone">🔍</span>
                        <div class="contador-info">
                            <h4 class="contador-label">Portal UERN (Minerado)</h4>
                            <p class="contador-numero">${dados.totais.portal_uern || 0}</p>
                        </div>
                    </div>
                </div>

                <div class="dash-secao-grafico">
                    <h3 class="grafico-titulo">📂 Distribuição de Editais de Vagas por Setor</h3>
                    <span class="grafico-metadado">Métrica baseada na agregação de categorias transacionais ativas</span>

                    <div class="grafico-barras-container">
        `;

        if (dados.prae_categorias.length === 0) {
            html += `<p style="text-align: center; color: gray; font-style: italic; padding: 2rem;">Não existem dados analíticos disponíveis.</p>`;
        } else {
            const maxVal = Math.max(...dados.prae_categorias.map(i => i.total));

            dados.prae_categorias.forEach(item => {
                const percentual = maxVal > 0 ? (item.total / maxVal) * 100 : 0;

                html += `
                    <div class="grafico-item-barra">
                        <div class="barra-legenda">
                            <span class="legenda-nome">${item.categoria}</span>
                            <span class="legenda-valor">${item.total} editais</span>
                        </div>
                        <div class="barra-estrutura">
                            <div class="barra-preenchimento" style="width: ${percentual}%;"></div>
                        </div>
                    </div>
                `;
            });
        }

        html += `
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;

    } catch (erro) {
        console.error("Erro no Dashboard:", erro);
        container.innerHTML = `<p class="carregando" style="color: red;">Falha ao gerar o painel visual das estatísticas: ${erro.message}</p>`;
    }
}
function renderizarCards(listaDeVagas) {
    const container = document.getElementById('container-vagas');
    container.innerHTML = '';

    if (!listaDeVagas || listaDeVagas.length === 0) {
        container.innerHTML = `
            <div class="status-box">
                <div class="status-box-decor"></div>
                <h3 class="status-box-titulo">Nenhum Resultado Encontrado</h3>
                <p class="status-box-texto">Não foram localizadas oportunidades para o filtro ou termo pesquisado.</p>
            </div>
        `;
        return;
    }

    // Mapa de cores para tags Memphis
    const corCategoriaMap = {
        "Estágios (PRAE)": "var(--color-navy)",
        "Bolsas (PROEX)": "var(--color-orange)",
        "UFERSA": "var(--color-purple)",
        "Vagas CIEE": "var(--color-navy)",
        "Portal UERN": "var(--color-orange)",
        "Notícia Tech": "var(--color-green)"
    };

    listaDeVagas.forEach(vaga => {
        const ehNoticia = vaga.categoria === "Notícia Tech" || tipoAtual === "noticias";
        const temaVerde = ehNoticia ? "card-verde" : "";

        // Cor da tag
        const corTag = corCategoriaMap[vaga.categoria] || "var(--color-navy)";

        // Badge dinâmica de prazo
        let badgeDataHTML = "";
        const estiloBadgeBase = "border: 2px solid var(--color-navy); padding: 3px 8px; font-size: 0.75rem; font-weight: 800; display: inline-flex; align-items: center; gap: 4px; box-shadow: 2px 2px 0 var(--color-navy);";

        let status = vaga.status_prazo || "";

        if (!ehNoticia && vaga.data_vencimento_formatada) {
            let dias = vaga.dias_restantes;
            if (typeof dias !== "number") {
                const [d, m, a] = vaga.data_vencimento_formatada.split("/").map(Number);
                const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
                dias = Math.round((new Date(a, m - 1, d) - hoje) / 86400000);
                status = dias >= 0 ? "vigente" : "vencido";
            }

            if (status === "vencido") {
                const decorridos = Math.abs(dias);
                badgeDataHTML = `
                    <div style="background: #EAEAEA; color: #555; ${estiloBadgeBase}">
                        ⛔ Encerrado em ${vaga.data_vencimento_formatada} (há ${decorridos} d)
                    </div>
                `;
            } else {
                const complemento = dias === 0 ? " (último dia!)" : ` (${dias} d)`;
                badgeDataHTML = `
                    <div style="background: #FFF5F5; color: var(--color-red); ${estiloBadgeBase}">
                        🔥 Até ${vaga.data_vencimento_formatada}${complemento}
                    </div>
                `;
            }
        }

        const classeVencido = status === "vencido" ? "card-vencido" : "";

        // Metadados das Fontes Normalizadas
        let linkFonteHTML = `Fonte: ${vaga.fonte || 'Não Especificada'}`;
        if (vaga.meta_fonte) {
            linkFonteHTML = `
                <a href="${vaga.meta_fonte.url_oficial}" target="_blank"
                   title="Portal Mestre: ${vaga.meta_fonte.nome_oficial} &#10;Ciclo do Robô: ${vaga.meta_fonte.frequencia}"
                   style="color: var(--color-navy); text-decoration: underline; font-weight: 800; cursor: pointer;">
                    📍 ${vaga.meta_fonte.nome_oficial.split(" - ")[0]} ℹ️
                </a>
            `;
        }

        const cardHTML = `
            <div class="card ${temaVerde} ${classeVencido}">
                <div class="card-topo">
                    <div class="card-tags-row">
                        <span class="card-categoria-tag" style="background-color: ${corTag};">
                            ${vaga.categoria || 'Geral'}
                        </span>
                        ${badgeDataHTML}
                    </div>
                    <h3 class="card-titulo">${vaga.nome}</h3>
                    <p class="card-fonte">${linkFonteHTML}</p>
                </div>
                <a href="${vaga.link}" target="_blank" class="card-link-btn">
                    Ver Detalhes →
                </a>
            </div>
        `;
        container.innerHTML += cardHTML;
    });
}
async function carregarInspector() {
    const antigo = document.getElementById('bloco-paginacao');
    if(antigo) antigo.remove();

    const container = document.getElementById('container-vagas');
    container.style.display = 'block';
    container.innerHTML = '<p class="carregando">Lendo integridade dos nós e volumes de armazenamento...</p>';

    document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('ativo'));
    const btnInsp = document.getElementById('btn-inspector');
    if(btnInsp) btnInsp.classList.add('ativo');

    try {
        const res = await fetch(`${API_URL}/db-status`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: AbortSignal.timeout(10000)
        });
        
        if (!res.ok) {
            throw new Error(`Erro ao carregar status do banco: ${res.status} - ${res.statusText}`);
        }
        
        const info = await res.json();

        let html = `
            <div style="background: white; border: 3px solid var(--azul-escuro); border-radius: 12px; padding: 2.5rem; box-shadow: 6px 6px 0px var(--azul-claro); margin-bottom: 2rem; animation: surgimento 0.4s ease-out;">
                <h2 style="color: var(--azul-escuro); margin-bottom: 0.5rem; border-bottom: 4px solid var(--azul-escuro); padding-bottom: 8px; font-weight: 800;">
                    🖥️ Status da Infraestrutura e Governança NoSQL
                </h2>
                <p style="color: #555; margin-bottom: 2rem; font-size: 0.95rem;">
                    Relatório transparente volumétrico do cluster NoSQL e integridade estrutural das coleções.
                </p>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr); gap: 20px;">
        `;

        if (info && info.colecoes) {
            info.colecoes.forEach(col => {
                const indexBadges = col.indices.map(idx => `<span class="badge-index">${idx}</span>`).join(' ');
                const validadorStatus = col.has_validator
                    ? `<span style="background: #E8F5E9; color: #1B5E20; font-size: 0.7rem; padding: 3px 8px; border-radius: 4px; border: 2px solid var(--azul-escuro); font-weight: bold; margin-left: auto; box-shadow: 2px 2px 0px var(--azul-escuro);">VALIDADOR ATIVO</span>`
                    : "";

                html += `
                    <div class="db-inspector-card">
                        <div style="display: flex; align-items: center; margin-bottom: 12px; border-bottom: 2px solid var(--azul-escuro); padding-bottom: 6px;">
                            <h3 style="color: var(--azul-escuro); font-size: 1.05rem; font-weight: bold;">📁 Coleção: ${col.colecao}</h3>
                            ${validadorStatus}
                        </div>
                        <p style="font-size: 0.9rem; margin-bottom: 6px; color: #333;">Documentos Ativos: <strong>${col.documentos}</strong></p>
                        <p style="font-size: 0.9rem; margin-bottom: 12px; color: #333;">Alocação Física: <strong>${col.tamanho_kb} KB</strong></p>

                        <div style="border-top: 1.5px dashed var(--azul-escuro); padding-top: 8px; margin-top: 10px;">
                            <p style="font-size: 0.75rem; font-weight: 800; color: var(--azul-escuro); margin-bottom: 6px; letter-spacing: 0.5px;">ESTRUTURAS DE ÍNDICES:</p>
                            <div style="display: flex; flex-wrap: gap: 4px;">${indexBadges}</div>
                        </div>
                    </div>
                `;
            });
        }

        html += `
                </div>
            </div>
        `;

        container.innerHTML = html;
    } catch (erro) {
        console.error("Erro ao inspecionar banco:", erro);
        container.innerHTML = `<p class="carregando" style="color: red;">Não foi possível ler os metadados de infraestrutura: ${erro.message}</p>`;
    }
}