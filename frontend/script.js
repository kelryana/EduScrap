// URL base da sua API FastAPI
const API_URL = "http://localhost:8000/api";

// Controle de estado global da paginação
let paginaAtual = 1;
let tipoAtual = 'estagios';

// Quando a página carregar, puxa os estágios por padrão
window.onload = () => {
    carregarDados('estagios');
};

// --- FUNÇÕES DE BUSCA E NAVEGAÇÃO ---

async function carregarDados(tipo, novaPagina = 1) {
    tipoAtual = tipo;
    paginaAtual = novaPagina;
    
    const container = document.getElementById('container-vagas');
    container.style.display = 'grid'; // Garante o layout grid
    container.innerHTML = '<p class="carregando">Buscando dados no banco...</p>';

    // Remove a classe ativa de todos os botões
    document.querySelectorAll('.controles button').forEach(botao => {
        botao.classList.remove('ativo');
    });
    
    const botaoAtivo = document.getElementById(`btn-${tipo}`);
    if(botaoAtivo) botaoAtivo.classList.add('ativo');

    try {
        // Envia os parâmetros de paginação via URL Query String para o MongoDB
        const resposta = await fetch(`${API_URL}/${tipo}?pagina=${paginaAtual}&limite=6`);
        const objetoPaginado = await resposta.json();
        
        // Envia apenas o array '.dados' para renderizar os cards
        renderizarCards(objetoPaginado.dados);
        
        // Injeta os controles visuais de paginação logo após os cards
        renderizarControlesPaginacao(objetoPaginado.pagina_atual, objetoPaginado.total_documentos, objetoPaginado.limite_por_pagina);
        
    } catch (erro) {
        console.error("Erro ao buscar dados paginados:", erro);
        container.innerHTML = '<p class="carregando" style="color: red;">Erro ao conectar com a API. O FastAPI está rodando?</p>';
    }
}

// Renderiza os botões de Anterior e Próximo mantendo o seu estilo original robusto
function renderizarControlesPaginacao(atual, total, limite) {
    const antigo = document.getElementById('bloco-paginacao');
    if(antigo) antigo.remove();
    
    const totalPaginas = Math.ceil(total / limite);
    if(totalPaginas <= 1) return; 

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
        const resposta = await fetch(`${API_URL}/pesquisar?termo=${termo}`);
        const dados = await resposta.json();
        renderizarCards(dados);
        document.querySelectorAll('.controles button').forEach(b => b.classList.remove('ativo'));
    } catch (e) {
        container.innerHTML = '<p class="carregando" style="color: red;">Erro na pesquisa.</p>';
    }
}

// 2. RECURSO ANALÍTICO VISUAL: Dashboard Acadêmico com Barras de Gráfico CSS
async function carregarEstatisticas() {
    const antigo = document.getElementById('bloco-paginacao');
    if(antigo) antigo.remove();

    const container = document.getElementById('container-vagas');
    container.style.display = 'block'; 
    container.innerHTML = '<p class="carregando">Gerando painel visual...</p>';

    document.querySelectorAll('.controles button').forEach(botao => {
        botao.classList.remove('ativo');
    });
    document.getElementById('btn-analises').classList.add('ativo');

    try {
        const resposta = await fetch(`${API_URL}/estatisticas`);
        const dados = await resposta.json();

        let html = `
            <div class="dashboard-container">
                <div class="dashboard-header">
                    <h2 class="dashboard-titulo">Dashboard Acadêmico <span>(Live)</span></h2>
                    <p class="dashboard-subtitulo">Visão consolidada da volumetria e distribuição de oportunidades.</p>
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
                </div>

                <div class="dash-secao-grafico">
                    <h3 class="grafico-titulo">📂 Distribuição Física por Categoria (PRAE Estágios)</h3>
                    <p class="grafico-metadado">Pipeline: MongoDB Aggregation <b>$group</b> + <b>$sort</b></p>
                    
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
                            <span class="legenda-valor">${item.total} edital(is)</span>
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
        container.innerHTML = '<p class="carregando" style="color: red;">Falha ao gerar o painel visual das estatísticas.</p>';
    }
}

// 3. MongoDB Inspector COMPLETO E CORRIGIDO PARA JAVASCRIPT
async function carregarInspector() {
    const antigo = document.getElementById('bloco-paginacao');
    if(antigo) antigo.remove();

    const container = document.getElementById('container-vagas');
    container.style.display = 'block';
    container.innerHTML = '<p class="carregando">Lendo metadados físicos e regras do JSON Schema...</p>';

    document.querySelectorAll('.controles button').forEach(b => b.classList.remove('ativo'));

    try {
        const res = await fetch(`${API_URL}/db-status`);
        const info = await res.json();

        let html = `
            <div style="background: white; border: 3px solid var(--azul-escuro); border-radius: 12px; padding: 2.5rem; box-shadow: 6px 6px 0px var(--azul-claro); margin-bottom: 2rem; animation: surgimento 0.4s ease-out;">
                <h2 style="color: var(--azul-escuro); margin-bottom: 0.5rem; border-bottom: 4px solid var(--azul-escuro); padding-bottom: 8px; font-weight: 800;">
                    🛡️ MongoDB Physical Inspector
                </h2>
                <p style="color: #555; margin-bottom: 2rem; font-size: 0.95rem;">
                    Monitoramento em tempo real de armazenamento, índices invertidos em disco e integridade NoSQL.
                </p>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
        `;

        // CORREÇÃO EFETIVA: Usando sintaxe nativa JS para varrer o array do objeto info
        if (info && info.colecoes) {
            info.colecoes.forEach(col => {
                const indexBadges = col.indices.map(idx => `<span class="badge-index">${idx}</span>`).join(' ');
                const validadorStatus = col.has_validator 
                    ? `<span style="background: #E8F5E9; color: #1B5E20; font-size: 0.7rem; padding: 3px 8px; border-radius: 4px; border: 2px solid var(--azul-escuro); font-weight: bold; margin-left: auto; box-shadow: 2px 2px 0px var(--azul-escuro);">VALIDADOR ATIVO</span>` 
                    : "";

                html += `
                    <div class="db-inspector-card">
                        <div style="display: flex; align-items: center; margin-bottom: 12px; border-bottom: 2px solid var(--azul-escuro); padding-bottom: 6px;">
                            <h3 style="color: var(--azul-escuro); font-size: 1.05rem; font-weight: bold;">📁 col: ${col.colecao}</h3>
                            ${validadorStatus}
                        </div>
                        <p style="font-size: 0.9rem; margin-bottom: 6px; color: #333;">Documentos Ativos: <strong>${col.documentos}</strong></p>
                        <p style="font-size: 0.9rem; margin-bottom: 12px; color: #333;">Alocação Física: <strong>${col.tamanho_kb} KB</strong></p>
                        
                        <div style="border-top: 1.5px dashed var(--azul-escuro); padding-top: 8px; margin-top: 10px;">
                            <p style="font-size: 0.75rem; font-weight: 800; color: var(--azul-escuro); margin-bottom: 6px; letter-spacing: 0.5px;">ESTRUTURAS DE ÍNDICE:</p>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px;">${indexBadges}</div>
                        </div>
                    </div>
                `;
            });
        }

        html += `
                </div>
                <div style="margin-top: 30px; padding: 15px; border: 2px dashed var(--azul-escuro); border-radius: 8px; background: #FFFDE7; text-align: left;">
                    <p style="color: var(--azul-escuro); font-weight: bold; font-size: 0.95rem; margin-bottom: 4px;">💡 Insight para a Apresentação Técnica:</p>
                    <p style="font-size: 0.85rem; color: #333; line-height: 1.4;">A coleção <b>historico_varreduras</b> funciona de forma assíncrona gravando metadados de governança a cada varredura dos robôs, persistindo o tempo de resposta do script externo e logs estruturados em caso de falha operaria.</p>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    } catch (erro) {
        console.error("Erro ao inspecionar banco:", erro);
        container.innerHTML = '<p class="carregando" style="color: red;">Não foi possível ler os metadados físicos do MongoDB.</p>';
    }
}

// --- RENDERIZAÇÃO ---

function renderizarCards(listaDeVagas) {
    const container = document.getElementById('container-vagas');
    container.innerHTML = ''; 

    if (!listaDeVagas || listaDeVagas.length === 0) {
        container.innerHTML = '<p class="carregando">Nenhuma oportunidade encontrada no banco.</p>';
        return;
    }

    listaDeVagas.forEach(vaga => {
        const temaVerde = vaga.categoria === "Notícia Tech" ? "card-verde" : "";
        const cardHTML = `
            <div class="card ${temaVerde}">
                <div>
                    <span class="card-categoria">${vaga.categoria || 'Geral'}</span>
                    <h3 class="card-titulo">${vaga.nome}</h3>
                    <p class="card-fonte">Fonte: ${vaga.fonte}</p>
                </div>
                <a href="${vaga.link}" target="_blank" class="card-link">Acessar</a>
            </div>
        `;
        container.innerHTML += cardHTML;
    });
}

// Função que aciona o Botão Vermelho (Raspagem Global + Geração de Logs)
async function acionarTodosOsRobos() {
    const container = document.getElementById('container-vagas');
    const btn = document.getElementById('btn-buscar-tudo');
    
    const antigo = document.getElementById('bloco-paginacao');
    if(antigo) antigo.remove();

    btn.innerText = "⏳ Raspando...";
    btn.disabled = true;
    
    container.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <h2 style="color: #DC143C; margin-bottom: 15px; font-size: 1.8rem;">Iniciando Protocolo de Varredura...</h2>
            <p style="font-size: 1.1rem; color: var(--azul-escuro);">Os scrapers assíncronos foram disparados. Limpando instâncias antigas e populando coleções...</p>
        </div>
    `;
    
    try {
        await fetch(`${API_URL}/buscar-tudo`);
        btn.innerText = "Buscar 🤖";
        btn.disabled = false;
        carregarDados('estagios');
    } catch (erro) {
        container.innerHTML = '<p class="carregando" style="color: red;">Erro crítico na execução dos robôs externos.</p>';
        btn.innerText = "Erro!";
        btn.disabled = false;
    }
}