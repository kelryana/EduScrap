// URL base da sua API FastAPI
const API_URL = "http://localhost:8000/api";

// Função principal que busca os dados
async function carregarDados(tipo) {
    const container = document.getElementById('container-vagas');
    container.innerHTML = '<p class="carregando">Buscando dados no banco...</p>';

    // JEITO NOVO E ESCALÁVEL: Remove a classe 'ativo' de TODOS os botões de uma vez
    document.querySelectorAll('.controles button').forEach(botao => {
        botao.classList.remove('ativo');
    });
    // Adiciona a classe 'ativo' só no botão que foi clicado
    document.getElementById(`btn-${tipo}`).classList.add('ativo');

    try {
        // ... (o resto do código fetch continua igualzinho!)
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
    container.innerHTML = ''; 

    if (listaDeVagas.length === 0) {
        container.innerHTML = '<p class="carregando">Nenhuma oportunidade encontrada no banco.</p>';
        return;
    }

    listaDeVagas.forEach(vaga => {
        // Verifica se é notícia para aplicar o tema verde
        const temaVerde = vaga.categoria === "Notícia Tech" ? "card-verde" : "";

        // Adicionamos a variável temaVerde na classe principal do card
        const cardHTML = `
            <div class="card ${temaVerde}">
                <div>
                    <span class="card-categoria">${vaga.categoria}</span>
                    <h3 class="card-titulo">${vaga.nome}</h3>
                    <p class="card-fonte">Fonte: ${vaga.fonte}</p>
                </div>
                <a href="${vaga.link}" target="_blank" class="card-link">Acessar</a>
            </div>
        `;
        
        container.innerHTML += cardHTML;
    });
}

// Quando a página carregar, puxa os estágios por padrão
window.onload = () => {
    carregarDados('estagios');
};