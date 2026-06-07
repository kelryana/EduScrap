// URL base da sua API FastAPI
const API_URL = "http://localhost:8000/api";

// Função principal que busca os dados
async function carregarDados(tipo) {
    const container = document.getElementById('container-vagas');
    container.innerHTML = '<p class="carregando">Buscando dados no banco...</p>';

    // Atualiza o visual dos botões
    document.getElementById('btn-estagios').classList.remove('ativo');
    document.getElementById('btn-bolsas').classList.remove('ativo');
    document.getElementById(`btn-${tipo}`).classList.add('ativo');

    try {
        // Faz a requisição para o FastAPI (ex: /api/estagios ou /api/bolsas)
        const resposta = await fetch(`${API_URL}/${tipo}`);
        const dados = await resposta.json();

        renderizarCards(dados);
    } catch (erro) {
        console.error("Erro ao buscar dados:", erro);
        container.innerHTML = '<p class="carregando" style="color: red;">Erro ao conectar com a API. O FastAPI está rodando?</p>';
    }
}

// Função que desenha o HTML na tela baseado nos dados
function renderizarCards(listaDeVagas) {
    const container = document.getElementById('container-vagas');
    container.innerHTML = ''; // Limpa o container

    if (listaDeVagas.length === 0) {
        container.innerHTML = '<p class="carregando">Nenhuma oportunidade encontrada no banco.</p>';
        return;
    }

    // Para cada item da lista, cria um HTML
    listaDeVagas.forEach(vaga => {
        const cardHTML = `
            <div class="card">
                <div>
                    <span class="card-categoria">${vaga.categoria}</span>
                    <h3 class="card-titulo">${vaga.nome}</h3>
                    <p class="card-fonte">Fonte: ${vaga.fonte}</p>
                </div>
                <a href="${vaga.link}" target="_blank" class="card-link">Acessar Edital</a>
            </div>
        `;
        
        // Adiciona o card dentro do container
        container.innerHTML += cardHTML;
    });
}

// Quando a página carregar, puxa os estágios por padrão
window.onload = () => {
    carregarDados('estagios');
};