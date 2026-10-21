const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Carrega o script.js simulando o ambiente do browser (DOM / window)
function criarContextoFrontend() {
    const scriptPath = path.resolve(__dirname, '../frontend/script.js');
    const codigo = fs.readFileSync(scriptPath, 'utf8');

    const domMock = {
        elementos: {},
        innerHTMLMap: {},
        addEventListener: () => {},
        getElementById(id) {
            if (!this.elementos[id]) {
                this.elementos[id] = {
                    id,
                    innerHTML: '',
                    style: { removeProperty: () => {}, setProperty: () => {} },
                    hidden: false,
                    classList: { add: () => {}, remove: () => {}, contains: () => false },
                    appendChild: () => {},
                    querySelector: () => null,
                    querySelectorAll: () => []
                };
            }
            return this.elementos[id];
        },
        querySelector: () => null,
        querySelectorAll: () => [],
        createElement: (tag) => ({
            tagName: tag,
            dataset: {},
            classList: { add: () => {}, remove: () => {} },
            setAttribute: () => {},
            style: { removeProperty: () => {}, setProperty: () => {} }
        }),
        addEventListener: () => {}
    };

    const sandbox = {
        console,
        window: {
            addEventListener: () => {},
            localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} }
        },
        document: domMock,
        localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
        setInterval: () => 1,
        setTimeout: () => 1,
        fetch: async () => ({ ok: true, json: async () => ({}) })
    };

    vm.createContext(sandbox);
    vm.runInContext(codigo, sandbox);
    return sandbox;
}

test('1. sintetizarTituloEdital: não deve quebrar nem duplicar "Convocação" nem deixar "Ção dos(as)" solto', () => {
    const ctx = criarContextoFrontend();
    const sintetizar = ctx.sintetizarTituloEdital;

    const caso1 = "Edital Nº 080/2026 - Convocação dos Beneficiários do Auxílio Inclusão Digital";
    const res1 = sintetizar(caso1);
    assert.equal(res1.numeroEdital, "Edital Nº 080/2026");
    assert.doesNotMatch(res1.tituloLimpo, /ção\s+dos/i, 'Não pode conter fragmento "ção dos"');
    assert.match(res1.tituloLimpo, /^Convocação:/i);

    const caso2 = "CONVOCAÇÃO DOS BENEFICIÁRIOS PARAPRESTAÇÃO DE CONTAS";
    const res2 = sintetizar(caso2);
    assert.doesNotMatch(res2.tituloLimpo, /ção\s+dos/i);
    assert.match(res2.tituloLimpo, /para\s+prestação/i, 'Deve separar "paraprestação"');

    const caso3 = "Edital Nº 077/2026 - Processo seletivo para preenchimento de vagas remanescentes do Programa de apoio à permanência estudantil da uern";
    const res3 = sintetizar(caso3);
    assert.equal(res3.numeroEdital, "Edital Nº 077/2026");
    assert.match(res3.tituloLimpo, /Vagas Remanescentes/);
    assert.match(res3.tituloLimpo, /Permanência Estudantil/);
});

test('2. Lembrete: NÃO deve aparecer para editais com status "vencido" (encerrados)', () => {
    const ctx = criarContextoFrontend();
    const container = ctx.document.getElementById('container-vagas');

    const vagaVencida = {
        _id: "vaga_1",
        titulo: "Processo Seletivo Residência Jurídica",
        status_prazo: "vencido",
        data_vencimento_formatada: "01/10/2026",
        data_vencimento: "2026-10-01",
        tipo: "estagio",
        categoria: "Estágios MPRN",
        fonte: "MPRN"
    };

    ctx.renderizarCards([vagaVencida]);
    const htmlGerado = container.innerHTML;

    assert.match(htmlGerado, /badge-status-encerrado/, 'Deve exibir badge de encerrado');
    assert.doesNotMatch(htmlGerado, /btn-calendario-card/, 'NÃO pode exibir botão de Lembrete para edital vencido');
    assert.doesNotMatch(htmlGerado, /adicionarLembrete|lembrete-menu/, 'NÃO deve conter menu de lembrete');
});

test('3. Lembrete: NÃO deve aparecer para notícias, mesmo se tiverem data', () => {
    const ctx = criarContextoFrontend();
    const container = ctx.document.getElementById('container-vagas');

    const noticiaComData = {
        _id: "noticia_1",
        titulo: "Professora e pesquisadora da Uern participam de atividades em Moçambique",
        tipo: "noticia",
        categoria: "Notícia UERN",
        data_vencimento_formatada: "10/10/2026",
        data_vencimento: "2026-10-10",
        status_prazo: "vigente",
        fonte: "Portal UERN"
    };

    ctx.renderizarCards([noticiaComData]);
    const htmlGerado = container.innerHTML;

    assert.doesNotMatch(htmlGerado, /btn-calendario-card/, 'Notícia NÃO deve ter botão de Lembrete');
    assert.match(htmlGerado, /Ler Notícia/, 'Deve mostrar texto de ação adequado para notícias');
});

test('4. Lembrete e Contador: DEVEM aparecer para editais VIGENTES', () => {
    const ctx = criarContextoFrontend();
    const container = ctx.document.getElementById('container-vagas');

    // Data no futuro
    const futuro = new Date(Date.now() + 5 * 86400000);
    const dia = String(futuro.getDate()).padStart(2, '0');
    const mes = String(futuro.getMonth() + 1).padStart(2, '0');
    const ano = futuro.getFullYear();
    const dataFmt = `${dia}/${mes}/${ano}`;

    const vagaVigente = {
        _id: "vaga_vigente",
        titulo: "Edital Nº 01/2026 - Seleção de Bolsistas",
        status_prazo: "vigente",
        dias_restantes: 5,
        data_vencimento_formatada: dataFmt,
        data_vencimento: futuro.toISOString(),
        tipo: "estagio",
        categoria: "Bolsas (PROEX)",
        fonte: "PROEX/UERN"
    };

    ctx.renderizarCards([vagaVigente]);
    const htmlGerado = container.innerHTML;

    assert.match(htmlGerado, /btn-calendario-card/, 'Edital vigente DEVE exibir botão de Lembrete');
    assert.match(htmlGerado, /contador-prazo/, 'Edital vigente DEVE ter o elemento com contador');
    assert.match(htmlGerado, /data-limite=/, 'Contador deve ter data-limite atribuída');
    assert.match(htmlGerado, /Encerra em/, 'Contador deve formatar tempo restante');
});

test('5. formatarContagemRegressiva: cálculo de tempo regressivo', () => {
    const ctx = criarContextoFrontend();
    const formatar = ctx.formatarContagemRegressiva;

    // Data 2 dias e 3 horas no futuro
    const agora = Date.now();
    const limiteFuturo = new Date(agora + (2 * 24 * 3600 * 1000) + (3 * 3600 * 1000) + (15 * 60 * 1000)).toISOString();
    const texto = formatar(limiteFuturo);
    assert.match(texto, /^Encerra em 2d 3h/);

    // Data já passada
    const limitePassado = new Date(agora - 10000).toISOString();
    assert.equal(formatar(limitePassado), 'Encerrado');
});

test('6. CIEE: cards devem exibir título detalhado e metadados ao invés de apenas "Vaga CIEE"', () => {
    const ctx = criarContextoFrontend();
    const container = ctx.document.getElementById('container-vagas');

    const vagaCieeComNomeCompleto = {
        _id: "ciee_1",
        titulo: "Vaga CIEE",
        nome_completo: "[6148015] Estágio - Seguridade Social Obrigatória (R$ 1.508,42 / Mês)",
        codigo: "6148015",
        categoria: "Estágio/Jovem Aprendiz",
        salario: "R$ 1.508,42 / Mês",
        area: "Seguridade Social Obrigatória",
        endereco: "Centro - Mossoró - RN",
        fonte: "CIEE"
    };

    ctx.renderizarCards([vagaCieeComNomeCompleto]);
    const htmlGerado = container.innerHTML;

    assert.doesNotMatch(htmlGerado, /<h3 class="card-titulo"[^>]*>Vaga CIEE<\/h3>/, 'NÃO pode exibir apenas "Vaga CIEE" como título');
    assert.match(htmlGerado, /6148015/, 'Deve conter o código da vaga');
    assert.match(htmlGerado, /Seguridade Social Obrigatória/, 'Deve conter a área da vaga');
    assert.match(htmlGerado, /Remuneração:/, 'Deve conter linha de remuneração');
    assert.match(htmlGerado, /Local:/, 'Deve conter linha de localidade');
    assert.match(htmlGerado, /href="https:\/\/portal\.ciee\.org\.br\/quero-uma-vaga\/\?codigoVaga=6148015"/, 'Link deve apontar diretamente para a vaga no CIEE');
    assert.match(htmlGerado, /Ver Vaga no CIEE/, 'Texto da ação deve ser Ver Vaga no CIEE');
});

test('7. Busca rápida: atualizarBotaoLimparBusca alterna visibilidade conforme texto digitado', () => {
    const ctx = criarContextoFrontend();
    const input = ctx.document.getElementById('input-busca');
    const btnLimpar = ctx.document.getElementById('btn-limpar-busca');

    input.value = '';
    ctx.atualizarBotaoLimparBusca();
    assert.equal(btnLimpar.hidden, true, 'Botão limpar deve ficar oculto quando input está vazio');

    input.value = 'computação';
    ctx.atualizarBotaoLimparBusca();
    assert.equal(btnLimpar.hidden, false, 'Botão limpar deve aparecer quando há termo digitado');
});

test('8. Seletor de Instituição: atualizarEstadoSeletorFonte usa Phosphor Icons sem emojis', () => {
    const ctx = criarContextoFrontend();
    const iconeEl = ctx.document.getElementById('seletor-fonte-icone');
    const textoEl = ctx.document.getElementById('seletor-fonte-texto');

    ctx.atualizarEstadoSeletorFonte('ciee');
    assert.match(iconeEl.className, /ph-briefcase/, 'Deve aplicar o ícone ph-briefcase para CIEE');
    assert.equal(textoEl.textContent, 'Vagas CIEE');

    ctx.atualizarEstadoSeletorFonte(null);
    assert.match(iconeEl.className, /ph-bank/, 'Deve voltar para o ícone padrão ph-bank');
    assert.equal(textoEl.textContent, 'Filtrar por Instituição / Órgão...');
});

test('9. Tags dinâmicas e sub-tags: filtrarPorTag atualiza input e dispara pesquisa', () => {
    const ctx = criarContextoFrontend();
    const input = ctx.document.getElementById('input-busca');
    let pesquisaDisparada = false;
    ctx.realizarPesquisa = () => { pesquisaDisparada = true; };

    ctx.filtrarPorTag('#Tecnologia');
    assert.equal(input.value, 'Tecnologia', 'Deve definir o termo de busca sem o caractere #');
    assert.equal(pesquisaDisparada, true, 'Deve disparar a rotina de pesquisa ao selecionar a tag');
});

test('10. Pinned Urgent Notices: renderizarCards exibe painel de prazos críticos para editais ≤ 3 dias', () => {
    const ctx = criarContextoFrontend();
    const painel = ctx.document.getElementById('painel-prazos-criticos');
    const grid = ctx.document.getElementById('prazos-criticos-grid');

    const editalCritico = {
        _id: 'edital-critico-1',
        titulo: 'Edital 001/2026 - PRAE Bolsa Urgente',
        fonte: 'PRAE/UERN',
        categoria: 'Bolsas (PROEX)',
        data_vencimento_formatada: '22/10/2026',
        dias_restantes: 2,
        status_prazo: 'vigente',
        link: 'https://prae.uern.br/edital-001'
    };

    ctx.renderizarCards([editalCritico]);
    assert.equal(painel.style.display, 'block', 'Painel de prazos críticos deve ficar visível');
    assert.match(grid.innerHTML, /Restam 2 dias|Encerra/, 'Card de prazo crítico deve conter contagem regressiva');
    assert.match(grid.innerHTML, /Bolsa Urgente/, 'Card de prazo crítico deve conter o título');
});


