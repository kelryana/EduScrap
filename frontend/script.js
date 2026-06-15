// URL base da sua API FastAPI
const API_URL = "http://localhost:8000/api";

// Quando a página carregar, puxa os estágios por padrão
window.onload = () => {
    carregarDados('estagios');
};

// --- FUNÇÕES DE BUSCA E NAVEGAÇÃO ---

async function carregarDados(tipo) {
    const container = document.getElementById('container-vagas');
    container.style.display = 'grid'; // Garante o layout grid
    container.innerHTML = '<p class="carregando">Buscando dados no banco...</p>';

    document.querySelectorAll('.controles button').forEach(botao => {
        botao.classList.remove('ativo');
    });
    
    const botaoAtivo = document.getElementById(`btn-${tipo}`);
    if(botaoAtivo) botaoAtivo.classList.add('ativo');

    try {
        const resposta = await fetch(`${API_URL}/${tipo}`);
        const dados = await resposta.json();
        renderizarCards(dados);
    } catch (erro) {
        console.error("Erro ao buscar dados:", erro);
        container.innerHTML = '<p class="carregando" style="color: red;">Erro ao conectar com a API. O FastAPI está rodando?</p>';
    }
}

// 1. NOVA FUNÇÃO: Pesquisa Textual via MongoDB
async function realizarPesquisa() {
    const termo = document.getElementById('input-busca').value;
    if (!termo) return;

    const container = document.getElementById('container-vagas');
    container.innerHTML = '<p class="carregando">Consultando índices no MongoDB...</p>';
    
    try {
        const resposta = await fetch(`${API_URL}/pesquisar?termo=${termo}`);
        const dados = await resposta.json();
        renderizarCards(dados);
    } catch (e) {
        container.innerHTML = '<p class="carregando" style="color: red;">Erro na pesquisa.</p>';
    }
}

// 2. NOVA FUNÇÃO: Painel Analítico (Gráficos)
// 2. RECURSO ANALÍTICO VISUAL: Dashboard Acadêmico com Barras de Gráfico CSS
async function carregarEstatisticas() {
    const container = document.getElementById('container-vagas');
    // Reinicia o layout para bloco único de dashboard, removendo o grid de cards
    container.style.display = 'block'; 
    container.innerHTML = '<p class="carregando">Gerando painel visual...</p>';

    // Atualiza o estado visual das abas
    document.querySelectorAll('.controles button').forEach(botao => {
        botao.classList.remove('ativo');
    });
    document.getElementById('btn-analises').classList.add('ativo');

    try {
        // Busca as agregações do MongoDB no backend
        const resposta = await fetch(`${API_URL}/estatisticas`);
        const dados = await resposta.json();

        // 1. Constrói o HTML do Dashboard Visual
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
                    
                    <div class="grafico-barras-container">
        `;

        if (dados.prae_categorias.length === 0) {
            html += `<p style="text-align: center; color: gray; font-style: italic; padding: 2rem;">Não existem dados analíticos disponíveis.</p>`;
        } else {
            // Calcula o maior valor para definir a escala 100% das barras
            const maxVal = Math.max(...dados.prae_categorias.map(i => i.total));

            // Mapeia os dados do MongoDB para barras visuais
            dados.prae_categorias.forEach(item => {
                // Define o percentual da barra baseado no maior valor
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
        
        // Injeta o HTML final no container
        container.innerHTML = html;
        
    } catch (erro) {
        console.error("Erro no Dashboard:", erro);
        container.innerHTML = '<p class="carregando" style="color: red;">Falha ao gerar o painel visual das estatísticas.</p>';
    }
}

// 3. NOVA FUNÇÃO: MongoDB Inspector
async function carregarInspector() {
    const container = document.getElementById('container-vagas');
    container.style.display = 'block';
    container.innerHTML = '<p class="carregando">Lendo metadados físicos...</p>';

    document.querySelectorAll('.controles button').forEach(b => b.classList.remove('ativo'));
    document.getElementById('btn-inspector').classList.add('ativo');

    const res = await fetch(`${API_URL}/db-status`);
    const info = await res.json();

    container.innerHTML = `
        <div class="card" style="grid-column: 1/-1;">
            <h3>🛡️ MongoDB Inspector</h3>
            <pre>${JSON.stringify(info, null, 2)}</pre>
        </div>
    `;
}

function renderizarCards(listaDeVagas) {
    const container = document.getElementById('container-vagas');
    container.innerHTML = ''; 

    if (listaDeVagas.length === 0) {
        container.innerHTML = '<p class="carregando">Nenhuma oportunidade encontrada.</p>';
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

// Função que aciona o Botão Vermelho
async function acionarTodosOsRobos() {
    const container = document.getElementById('container-vagas');
    const btn = document.getElementById('btn-buscar-tudo');
    
    btn.innerText = "⏳ Raspando...";
    btn.disabled = true;
    
    container.innerHTML = '<div style="text-align: center; padding: 40px;"><h2>Protocolo Iniciado...</h2></div>';
    
    try {
        await fetch(`${API_URL}/buscar-tudo`);
        btn.innerText = "Buscar 🤖";
        btn.disabled = false;
        carregarDados('estagios');
    } catch (erro) {
        container.innerHTML = '<p class="carregando" style="color: red;">Erro ao rodar robôs.</p>';
        btn.innerText = "Erro!";
        btn.disabled = false;
    }
}