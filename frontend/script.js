// frontend/script.js - EduScrap Portal Universitário

const API_URL = "http://localhost:8000/api";

const TODOS_CURSOS = [
    "Ciência da Computação", "Sistemas de Informação", "Medicina",
    "Enfermagem", "Direito", "Administração", "Ciências Contábeis",
    "Educação Física", "Letras", "História", "Pedagogia",
    "Ciências Biológicas", "Serviço Social", "Geografia", "Filosofia"
];

const TODAS_AREAS = [
    "Tecnologia", "Saúde", "Humanas", "Exatas",
    "Extensão", "Pesquisa", "Inovação"
];

let paginaAtual = 1;
let tipoAtual = 'estagios';
let filtroVigentesAtivo = false;
let usuarioAtual = null;

window.addEventListener('DOMContentLoaded', () => {
    inicializarAutenticacao();
    configurarChipsClick();
    carregarDados('estagios');
    verificarNovoUsuarioOnboarding();
});

function verificarNovoUsuarioOnboarding() {
    if (localStorage.getItem('eduscrap_novo_usuario') === 'true') {
        localStorage.removeItem('eduscrap_novo_usuario');
        setTimeout(() => {
            if (typeof abrirSidebarPerfil === 'function' && usuarioAtual) {
                abrirSidebarPerfil();
            }
        }, 600);
    }
}

function getAuthToken() {
    return localStorage.getItem('eduscrap_token') || null;
}

function getAuthHeaders() {
    const token = getAuthToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

function inicializarAutenticacao() {
    const userJson = localStorage.getItem('eduscrap_user');
    if (userJson) {
        try {
            usuarioAtual = JSON.parse(userJson);
        } catch (e) {
            usuarioAtual = null;
        }
    }
    atualizarInterfaceUsuario();
    if (getAuthToken()) {
        sincronizarPerfilRemoto();
    }
}

function setAuthSession(token, user) {
    localStorage.setItem('eduscrap_token', token);
    localStorage.setItem('eduscrap_user', JSON.stringify(user));
    usuarioAtual = user;
    atualizarInterfaceUsuario();
}

function limparSessao() {
    localStorage.removeItem('eduscrap_token');
    localStorage.removeItem('eduscrap_user');
    usuarioAtual = null;
    atualizarInterfaceUsuario();
}

async function sincronizarPerfilRemoto() {
    try {
        const resp = await fetch(`${API_URL}/auth/me`, {
            headers: getAuthHeaders()
        });
        if (resp.ok) {
            const data = await resp.json();
            if (data.user) {
                usuarioAtual = data.user;
                localStorage.setItem('eduscrap_user', JSON.stringify(data.user));
                atualizarInterfaceUsuario();
            }
        } else if (resp.status === 401) {
            limparSessao();
        }
    } catch (err) {
        console.warn("Não foi possível sincronizar o perfil com a API:", err);
    }
}

function atualizarInterfaceUsuario() {
    const navAuth = document.getElementById('nav-auth-area');
    const bannerUsuario = document.getElementById('banner-usuario');
    const bannerTexto = document.getElementById('banner-usuario-texto');
    const contadorFav = document.getElementById('contador-favoritos');

    const totalFavs = (usuarioAtual && usuarioAtual.favoritos) ? usuarioAtual.favoritos.length : 0;
    if (contadorFav) contadorFav.innerText = totalFavs;

    if (!navAuth) return;

    if (usuarioAtual) {
        const primeiroNome = usuarioAtual.nome ? usuarioAtual.nome.split(' ')[0] : 'Estudante';
        const userDisplay = document.getElementById('user-name-display');
        if (userDisplay) {
            userDisplay.textContent = primeiroNome;
        }
        navAuth.innerHTML = `
            <div class="nav-user-box">
                <span class="nav-user-tag">
                    <i class="ph-bold ph-student"></i> Olá, <strong id="user-name-display">${primeiroNome}</strong>
                </span>
                <button class="btn-nav-mini btn-nav-logout" onclick="fazerLogout()" title="Sair da Conta">
                    <i class="ph-bold ph-sign-out"></i>
                </button>
            </div>
        `;

        // Sincroniza dados na sidebar de perfil se ela estiver presente
        const sidebarNome = document.getElementById('perfil-nome-display-sidebar');
        if (sidebarNome) sidebarNome.innerText = usuarioAtual.nome || 'Estudante';
        const sidebarEmail = document.getElementById('perfil-email-display-sidebar');
        if (sidebarEmail) sidebarEmail.innerText = usuarioAtual.email || '';

        // Sincroniza dados no modal de perfil
        const modalNome = document.getElementById('perfil-nome-display');
        if (modalNome) modalNome.innerText = usuarioAtual.nome || 'Estudante';
        const modalEmail = document.getElementById('perfil-email-display');
        if (modalEmail) modalEmail.innerText = usuarioAtual.email || '';

        if (bannerUsuario && bannerTexto) {
            bannerUsuario.style.display = 'flex';
            const cursosCount = (usuarioAtual.preferencias && usuarioAtual.preferencias.cursos) ? usuarioAtual.preferencias.cursos.length : 0;
            const areasCount = (usuarioAtual.preferencias && usuarioAtual.preferencias.areas) ? usuarioAtual.preferencias.areas.length : 0;
            bannerTexto.innerHTML = `<i class="ph-bold ph-sparkle"></i> <strong>Feed Personalizado Ativo:</strong> ${cursosCount} curso(s) e ${areasCount} área(s) configurados.`;
        }
    } else {
        navAuth.innerHTML = `
            <a href="login.html" class="btn-nav-auth" style="text-decoration: none;">
                <i class="ph ph-user"></i> <span>Entrar / Cadastrar</span>
            </a>
        `;
        if (bannerUsuario) bannerUsuario.style.display = 'none';
    }
}

function fazerLogout() {
    limparSessao();
    fecharModalPerfil();
    fecharSidebarPerfil(); // Close sidebar if open
    mostrarToast("Você saiu da sua conta.", "info");
    carregarDados('estagios');
}

function abrirModalAuth(aba = 'login') {
    window.location.href = `login.html?aba=${aba}`;
}



function abrirSidebarPerfil() {
    if (!usuarioAtual) {
        abrirModalAuth('login');
        return;
    }

    const sidebar = document.getElementById('sidebar-perfil');

    // Update sidebar content with user data
    document.getElementById('perfil-nome-display-sidebar').innerText = usuarioAtual.nome || 'Estudante';
    document.getElementById('perfil-email-display-sidebar').innerText = usuarioAtual.email || '';

    const pref = usuarioAtual.preferencias || {};
    const cursosSalvos = pref.cursos || [];
    const areasSalvas = pref.areas || [];
    const emailNotif = pref.receber_emails !== false;

    // Renderiza chips no sidebar
    const containerCursos = document.getElementById('perfil-chips-cursos-sidebar');
    containerCursos.innerHTML = '';
    TODOS_CURSOS.forEach(curso => {
        const sel = cursosSalvos.includes(curso) ? 'chip-selecionado' : '';
        containerCursos.innerHTML += `<button type="button" class="chip-opcao ${sel}" data-valor="${curso}"><span class="chip-check"><i class="ph-bold ph-check"></i></span> ${curso}</button>`;
    });

    const containerAreas = document.getElementById('perfil-chips-areas-sidebar');
    containerAreas.innerHTML = '';
    TODAS_AREAS.forEach(area => {
        const sel = areasSalvas.includes(area) ? 'chip-selecionado' : '';
        containerAreas.innerHTML += `<button type="button" class="chip-opcao ${sel}" data-valor="${area}"><span class="chip-check"><i class="ph-bold ph-check"></i></span> ${area}</button>`;
    });

    document.getElementById('perfil-receber-emails-sidebar').checked = emailNotif;

    // Configure chip clicks
    configurarChipsClickSidebar();

    sidebar.classList.add('aberto');

    // Feedback visual de que a gaveta está aberta + rolagem suave em telas estreitas
    const gatilho = document.getElementById('btn-abrir-sidebar-filtros');
    if (gatilho) gatilho.classList.add('ativo');
    if (window.innerWidth < 1024) {
        sidebar.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function fecharSidebarPerfil() {
    const sidebar = document.getElementById('sidebar-perfil');
    if (!sidebar) return;

    sidebar.classList.remove('aberto');

    const gatilho = document.getElementById('btn-abrir-sidebar-filtros');
    if (gatilho) gatilho.classList.remove('ativo');
}

// Toggle simples para abrir/fechar sem afetar o resto da página
function alternarSidebarPerfil() {
    if (!usuarioAtual) {
        abrirModalAuth('login');
        return;
    }
    const sidebar = document.getElementById('sidebar-perfil');
    if (!sidebar) return;
    if (sidebar.classList.contains('aberto')) {
        fecharSidebarPerfil();
    } else {
        abrirSidebarPerfil();
    }
}

function configurarChipsClickSidebar() {
    document.querySelectorAll('#perfil-chips-cursos-sidebar .chip-opcao, #perfil-chips-areas-sidebar .chip-opcao').forEach(btn => {
        btn.onclick = function() {
            this.classList.toggle('chip-selecionado');
            // Trigger real-time update of feed when chips are toggled
            if (tipoAtual === 'personalizado') {
                carregarFeedPersonalizado();
            }
        };
    });
}


function configurarChipsClick() {
    document.querySelectorAll('.chip-opcao').forEach(btn => {
        btn.onclick = function() {
            this.classList.toggle('chip-selecionado');
        };
    });
}

function obterChipsSelecionados(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];
    const selecionados = [];
    container.querySelectorAll('.chip-opcao.chip-selecionado').forEach(btn => {
        selecionados.push(btn.getAttribute('data-valor'));
    });
    return selecionados;
}

async function executarLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const senha = document.getElementById('login-senha').value;
    const erroDiv = document.getElementById('login-erro');

    erroDiv.style.display = 'none';

    try {
        const resp = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, senha })
        });

        const data = await resp.json();
        if (!resp.ok || !data.success) {
            throw new Error(data.error || data.detail || 'Email ou senha inválidos.');
        }

        setAuthSession(data.token, data.user);
        fecharModalAuth();
        mostrarToast(`Bem-vindo de volta, ${data.user.nome.split(' ')[0]}!`, 'sucesso');
        carregarFeedPersonalizado();

    } catch (err) {
        erroDiv.innerText = err.message;
        erroDiv.style.display = 'block';
    }
}

async function executarCadastro(e) {
    e.preventDefault();
    const nome = document.getElementById('reg-nome').value.trim();
    const matricula = document.getElementById('reg-matricula').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const senha = document.getElementById('reg-senha').value;
    const cursos = obterChipsSelecionados('reg-chips-cursos');
    const areas = obterChipsSelecionados('reg-chips-areas');
    const receber_emails = document.getElementById('reg-receber-emails').checked;
    const erroDiv = document.getElementById('register-erro');

    erroDiv.style.display = 'none';

    try {
        const resp = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nome, matricula, email, senha,
                cursos, areas, receber_emails
            })
        });

        const data = await resp.json();
        if (!resp.ok || !data.success) {
            throw new Error(data.error || data.detail || 'Falha ao cadastrar estudante.');
        }

        setAuthSession(data.token, data.user);
        fecharModalAuth();
        mostrarToast(`Conta criada com sucesso! Perfil configurado.`, 'sucesso');
        carregarFeedPersonalizado();

    } catch (err) {
        erroDiv.innerText = err.message;
        erroDiv.style.display = 'block';
    }
}

async function salvarPreferenciasPerfil(e) {
    e.preventDefault();
    const sidebarEl = document.getElementById('sidebar-perfil');
    const isSidebar = sidebarEl && sidebarEl.classList.contains('aberto');
    const cursos = isSidebar ?
        obterChipsSelecionados('perfil-chips-cursos-sidebar') :
        obterChipsSelecionados('perfil-chips-cursos');
    const areas = isSidebar ?
        obterChipsSelecionados('perfil-chips-areas-sidebar') :
        obterChipsSelecionados('perfil-chips-areas');
    const emailSidebarInput = document.getElementById('perfil-receber-emails-sidebar');
    const emailModalInput = document.getElementById('perfil-receber-emails');
    const receber_emails = isSidebar ?
        (emailSidebarInput ? emailSidebarInput.checked : true) :
        (emailModalInput ? emailModalInput.checked : true);

    const feedback = isSidebar ?
        document.getElementById('perfil-feedback-sidebar') :
        document.getElementById('perfil-feedback');

    try {
        const resp = await fetch(`${API_URL}/auth/preferencias`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({ cursos, areas, receber_emails })
        });

        const data = await resp.json();
        if (!resp.ok || !data.success) {
            throw new Error(data.error || data.detail || 'Erro ao salvar preferências.');
        }

        usuarioAtual = data.user;
        localStorage.setItem('eduscrap_user', JSON.stringify(data.user));
        atualizarInterfaceUsuario();

        if (feedback) {
            feedback.innerHTML = '<i class="ph-bold ph-check-circle"></i> Preferências atualizadas com sucesso!';
            feedback.style.display = 'block';
            feedback.style.backgroundColor = '#D1FAE5';
            feedback.style.color = '#065F46';
        }

        setTimeout(() => {
            if (isSidebar) {
                fecharSidebarPerfil();
            } else {
                fecharModalPerfil();
            }
            mostrarToast("Feed adaptado com suas novas preferências!", "sucesso");
            carregarFeedPersonalizado();
        }, 800);

    } catch (err) {
        if (feedback) {
            feedback.innerText = err.message;
            feedback.style.display = 'block';
            feedback.style.backgroundColor = '#FFD2D2';
            feedback.style.color = '#7F1D1D';
        } else {
            mostrarToast(err.message, 'erro');
        }
    }
}

async function toggleFavorito(idOportunidade, event) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }

    if (!usuarioAtual) {
        mostrarToast("Faça login para salvar oportunidades e receber avisos!", "info");
        abrirModalAuth('login');
        return;
    }

    const estaFavoritado = usuarioAtual.favoritos && usuarioAtual.favoritos.includes(String(idOportunidade));
    const metodo = estaFavoritado ? 'DELETE' : 'POST';

    // Atualização otimista local
    if (estaFavoritado) {
        usuarioAtual.favoritos = usuarioAtual.favoritos.filter(f => f !== String(idOportunidade));
    } else {
        usuarioAtual.favoritos = usuarioAtual.favoritos || [];
        usuarioAtual.favoritos.push(String(idOportunidade));
    }
    localStorage.setItem('eduscrap_user', JSON.stringify(usuarioAtual));
    atualizarInterfaceUsuario();

    // Atualiza botão no card diretamente
    const btnCard = document.getElementById(`fav-btn-${idOportunidade}`);
    if (btnCard) {
        if (!estaFavoritado) {
            btnCard.classList.add('favoritado');
            btnCard.innerHTML = `<i class="ph-fill ph-star"></i> <span>Salvo</span>`;
        } else {
            btnCard.classList.remove('favoritado');
            btnCard.innerHTML = `<i class="ph ph-star"></i> <span>Salvar</span>`;
        }
    }

    try {
        const resp = await fetch(`${API_URL}/favoritos/${idOportunidade}`, {
            method: metodo,
            headers: getAuthHeaders()
        });

        if (!resp.ok) {
            throw new Error("Falha ao sincronizar favorito");
        }

        mostrarToast(!estaFavoritado ? "Oportunidade salva nos seus favoritos!" : "Removido dos favoritos.", "sucesso");

        // Se estiver visualizando a tela de favoritos e desfavoritou, recarrega a lista
        if (tipoAtual === 'favoritos' && estaFavoritado) {
            carregarFavoritos();
        }

    } catch (err) {
        console.error("Erro ao favoritar:", err);
        mostrarToast("Erro ao sincronizar com o servidor.", "erro");
        sincronizarPerfilRemoto();
    }
}

async function carregarFavoritos() {
    tipoAtual = 'favoritos';
    const container = document.getElementById('container-vagas');
    const antigo = document.getElementById('bloco-paginacao');
    if (antigo) antigo.remove();

    destacarBotaoAtivo('btn-favoritos');
    liberarExibicaoCards();

    if (!usuarioAtual) {
        container.style.display = 'block';
        container.innerHTML = `
            <div class="status-box" style="border-color: var(--color-orange);">
                <div class="status-box-decor"></div>
                <h3 class="status-box-titulo">Faça Login para Ver Seus Salvos</h3>
                <p class="status-box-texto">Você precisa estar conectado para acessar as oportunidades que favoritou.</p>
                <div style="margin-top: 15px;">
                    <button class="btn-hero-primary" onclick="abrirModalAuth('login')">
                        <i class="ph ph-sign-in"></i> Entrar na Minha Conta
                    </button>
                </div>
            </div>
        `;
        return;
    }

    container.style.display = 'grid';
    container.innerHTML = '<p class="carregando">Carregando suas oportunidades salvas...</p>';

    try {
        const resp = await fetch(`${API_URL}/favoritos`, {
            headers: getAuthHeaders()
        });

        if (!resp.ok) throw new Error("Erro ao carregar favoritos");

        const data = await resp.json();
        const lista = data.data || [];

        if (lista.length === 0) {
            container.innerHTML = `
                <div class="status-box">
                    <div class="status-box-decor"></div>
                    <h3 class="status-box-titulo"><i class="ph-bold ph-star"></i> Nenhum Edital Favoritado Ainda</h3>
                    <p class="status-box-texto">Clique na estrelinha dos editais e vagas para salvá-los e acompanhar os prazos aqui!</p>
                </div>
            `;
            return;
        }

        renderizarCards(lista);

    } catch (err) {
        container.innerHTML = `<p class="carregando" style="color: red;">Erro ao consultar favoritos: ${err.message}</p>`;
    }
}

async function carregarFeedPersonalizado() {
    tipoAtual = 'personalizado';
    const container = document.getElementById('container-vagas');
    const antigo = document.getElementById('bloco-paginacao');
    if (antigo) antigo.remove();

    destacarBotaoAtivo('btn-personalizado');

    if (!usuarioAtual) {
        container.style.display = 'block';
        container.innerHTML = `
            <div class="status-box" style="border-color: var(--color-yellow);">
                <div class="status-box-decor"></div>
                <h3 class="status-box-titulo"><i class="ph-bold ph-sparkle"></i> Personalize seu Feed Universitário</h3>
                <p class="status-box-texto">Cadastre-se para filtrar automaticamente oportunidades que combinam exatamente com o seu curso de graduação.</p>
                <div style="margin-top: 15px;">
                    <button class="btn-hero-primary" onclick="abrirModalAuth('register')">
                        <i class="ph ph-sparkle"></i> Criar Perfil e Personalizar
                    </button>
                </div>
            </div>
        `;
        return;
    }

    container.style.display = 'grid';
    container.innerHTML = '<p class="carregando">Cruzando seus cursos e áreas com editais vigentes...</p>';

    try {
        const resp = await fetch(`${API_URL}/feed/personalizado`, {
            headers: getAuthHeaders()
        });

        if (!resp.ok) throw new Error("Erro ao buscar recomendações");

        const data = await resp.json();
        const lista = data.data || [];

        renderizarCards(lista);

    } catch (err) {
        container.innerHTML = `<p class="carregando" style="color: red;">Erro ao gerar feed personalizado: ${err.message}</p>`;
    }
}

function destacarBotaoAtivo(idBotao) {
    document.querySelectorAll('.tab-origem-btn, .btn-filtro-aluno').forEach(btn => btn.classList.remove('ativo'));
    const btn = document.getElementById(idBotao);
    if (btn) btn.classList.add('ativo');
}

function formatarTituloEdital(texto) {
    if (!texto || typeof texto !== 'string') return '';

    // Detecta proporção de letras maiúsculas
    const letras = texto.replace(/[^a-zA-ZáéíóúÁÉÍÓÚãõÃÕâêîôûÂÊÎÔÛçÇ]/g, '');
    if (letras.length === 0) return texto;
    const maiusculas = letras.replace(/[^A-ZÁÉÍÓÚÃÕÂÊÎÔÛÇ]/g, '').length;
    if (maiusculas / letras.length < 0.6) {
        return texto; // Texto já possui caixa mista natural
    }

    // Siglas oficiais e acrônimos que devem ser mantidos em maiúsculas
    const siglas = new Set([
        'UERN', 'UFERSA', 'PRAE', 'PROEX', 'PROEG', 'PROPESP', 'PROPLAN', 'PROGEP',
        'CIEE', 'TI', 'PIBIC', 'PIBEX', 'PIBID', 'FAPERN', 'CAPES', 'CNPQ', 'CNPQ',
        'SEI', 'EAD', 'DED', 'FACHS', 'FASSO', 'FE', 'FANAT', 'FAD', 'FAEN', 'FAME',
        'PCD', 'SUS', 'MEC', 'RN', 'BR', 'PDF', 'CLT', 'MEI', 'CPF', 'RG', 'HTML', 'CSS', 'JS', 'API'
    ]);

    const minusculas = new Set([
        'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'nos', 'nas',
        'a', 'o', 'as', 'os', 'e', 'ou', 'com', 'por', 'para', 'pelo', 'pela', 'ao', 'aos', 'à', 'às'
    ]);

    const tokens = texto.split(/(\s+|[-/.,;:()ºª°"'])/);
    let primeiroTokenValido = true;

    return tokens.map(token => {
        if (!token || /^\s+$/.test(token) || /^[-/.,;:()ºª°"']+$/.test(token)) {
            return token;
        }

        const upper = token.toUpperCase();
        if (siglas.has(upper)) {
            primeiroTokenValido = false;
            return upper;
        }
        if (upper === 'Nº' || upper === 'NO' || upper === 'N°') {
            primeiroTokenValido = false;
            return 'Nº';
        }

        const lower = token.toLowerCase();
        if (!primeiroTokenValido && minusculas.has(lower)) {
            return lower;
        }

        primeiroTokenValido = false;
        return lower.charAt(0).toUpperCase() + lower.slice(1);
    }).join('');
}

// Normaliza categorias gigantescas para tags compactas e legíveis
function normalizarCategoriaTag(categoria, tipoContexto, vaga) {
    const fonte = ((vaga && vaga.fonte) || '').toLowerCase();
    const titulo = ((vaga && (vaga.titulo || vaga.nome)) || '').toLowerCase();
    const cLower = (categoria || '').toLowerCase();

    // 1. Notícias temáticas explícitas (Notícia Saúde, Notícia Educação, Notícia Tech, Notícia Geral...)
    if (cLower.startsWith('notícia ') || cLower.startsWith('noticia ')) {
        if (cLower.includes('ufersa') || fonte.includes('ufersa') || tipoContexto === 'noticias-ufersa') {
            return 'Notícia UFERSA';
        }
        return formatarTituloEdital(categoria);
    }

    // 2. Prioridade por Fonte / Instituição Real
    if (fonte.includes('ifrn') || titulo.includes('[ifrn') || tipoContexto === 'ifrn') return 'Editais IFRN';
    if (fonte.includes('iel') || titulo.includes('[iel') || tipoContexto === 'iel') return 'Estágios IEL/RN';
    if (fonte.includes('mprn') || titulo.includes('[mprn') || tipoContexto === 'mprn' || cLower.includes('mprn')) return 'Estágios MPRN';
    if (fonte.includes('prefeitura de mossoró') || titulo.includes('[dom/mossoró') || tipoContexto === 'dom') return 'DOM Mossoró';

    // 3. Notícias Institucionais UFERSA (ASSECOM)
    if (tipoContexto === 'noticias-ufersa' || (fonte.includes('ufersa') && (vaga && vaga.tipo === 'noticia')) ||
        (fonte.includes('ufersa') && cLower.includes('comunicação'))) {
        return 'Notícia UFERSA';
    }

    if (fonte.includes('ufersa') || titulo.includes('[cpps') || tipoContexto === 'ufersa') return 'Editais UFERSA';
    if (fonte.includes('ciee') || tipoContexto === 'ciee') return 'Vagas CIEE';
    if (fonte.includes('estudar fora') || fonte.includes('fundação estudar')) return 'Bolsa de Estudos';
    if (fonte.includes('dio') || fonte.includes('microsoft') || fonte.includes('trabalho')) return 'Capacitação & Cursos';
    if (tipoContexto === 'cursos-bolsas') {
        if (cLower.includes('bolsa')) return 'Bolsa de Estudos';
        return 'Capacitação & Cursos';
    }

    // 4. Se a origem for o Portal UERN (Blog institucional/AGECOM)
    if (fonte.includes('portal uern') || tipoContexto === 'portal_uern' || (vaga && vaga.fonte_id === 'portal_uern_oficial')) {
        if (titulo.includes('solidariedade') || titulo.includes('nota de') || titulo.includes('luto') || titulo.includes('pesar')) {
            return 'Comunicado Oficial';
        }
        if (titulo.includes('conselho') || titulo.includes('consepe') || titulo.includes('consuni') || titulo.includes('vagas iniciais') || titulo.includes('sisu')) {
            return 'Acadêmico UERN';
        }
        if (titulo.includes('estágio') || titulo.includes('estagio')) {
            return 'Estágio UERN';
        }
        if (titulo.includes('bolsa') || titulo.includes('auxílio') || titulo.includes('auxilio')) {
            return 'Bolsas UERN';
        }
        if (titulo.includes('proficiência') || titulo.includes('mobilidade') || titulo.includes('abruem') || titulo.includes('curso')) {
            return 'Intercâmbio & Cursos';
        }
        return 'Notícia UERN';
    }

    // 5. Editais de Assistência e Extensão da UERN (vindos de coleções específicas da PRAE/PROEX)
    if (cLower.includes('inclusão digital') || cLower.includes('inclusao digital')) return 'Inclusão Digital';
    if (cLower.includes('moradia')) return 'Auxílio Moradia';
    if (cLower.includes('creche')) return 'Auxílio Creche';
    if (cLower.includes('transporte')) return 'Auxílio Transporte';
    if (cLower.includes('alimentação') || cLower.includes('alimentacao')) return 'Auxílio Alimentação';
    if (cLower.includes('permanência') || cLower.includes('permanencia')) return 'Permanência Estudantil';
    if (tipoContexto === 'estagios' || fonte.includes('prae')) return 'Estágios (PRAE)';
    if (tipoContexto === 'bolsas' || fonte.includes('proex')) return 'Bolsas (PROEX)';

    // 6. Demais notícias gerais
    if (cLower.includes('notícia tech') || cLower.includes('noticia tech') || fonte.includes('canaltech')) {
        return 'Notícia Tech';
    }
    if (tipoContexto === 'noticias') {
        if (fonte.includes('g1') && cLower.includes('saúde')) return 'Notícia Saúde';
        if (fonte.includes('g1') && cLower.includes('educação')) return 'Notícia Educação';
        return categoria ? formatarTituloEdital(categoria) : 'Notícia';
    }

    if (!categoria) {
        return 'Oportunidade';
    }

    if (categoria.length <= 26) {
        return formatarTituloEdital(categoria);
    }

    return formatarTituloEdital(categoria.substring(0, 24).trim()) + '...';
}

// Higieniza jargões burocráticos oficiais e extrai o número do edital e o objeto direto
function sintetizarTituloEdital(textoOriginal) {
    if (!textoOriginal || typeof textoOriginal !== 'string') {
        return { numeroEdital: null, tituloLimpo: '' };
    }

    let t = textoOriginal.trim();
    let numeroEdital = null;

    // 1. Extração do número do edital (ex: Edital Nº 077/2026)
    const matchNumero = t.match(/^(Edital\s+(?:N[º°o]\s*)?[\d\w\/\.-]+)\s*[-–—:]*\s*/i);
    if (matchNumero) {
        numeroEdital = formatarTituloEdital(matchNumero[1].trim());
        t = t.substring(matchNumero[0].length).trim();
    }

    // 2. Remove ruídos burocráticos e siglas repetitivas
    t = t.replace(/^[-\s–—]*(?:prae|proex|proeg|uern|ufersa)[-\s–—]+/i, '');
    t = t.replace(/^(?:praetorna|torna)\s+p[úu]blic[oa]\s+(?:o|a|os|as)?\s*/i, '');
    t = t.replace(/^o\s+(processo|resultado|edital)/i, '$1');

    // 3. Destaca o Tipo de Ação
    t = t.replace(/^resultado\s+final\s+d[oe]\s+/i, 'Resultado Final: ');
    t = t.replace(/^resultado\s+preliminar\s+d[oe]\s+/i, 'Resultado Preliminar: ');
    t = t.replace(/^resultado\s+parcial\s+d[oe]\s+/i, 'Resultado Parcial: ');
    t = t.replace(/^convoca\s*(?:os\s+estudantes|candidatos)?\s*/i, 'Convocação: ');
    t = t.replace(/^homologa\s*(?:os\s+estudantes|candidatos|inscrições)?\s*/i, 'Homologação: ');
    t = t.replace(/^retifica\s*(?:o\s+edital|a\s+publicação)?\s*/i, 'Retificação: ');

    // 4. Encurta fórmulas longas do objeto
    t = t.replace(/processo\s+seletivo\s+para\s+preenchimento\s+de\s+vagas\s+remanescentes\s+d[oe]\s+/gi, 'Vagas Remanescentes – ');
    t = t.replace(/processo\s+seletivo\s+para\s+preenchimento\s+de\s+vagas\s+d[oe]\s+/gi, 'Vagas – ');
    t = t.replace(/programa\s+de\s+apoio\s+[àa]\s+perman[êe]ncia\s+estudantil\s+da\s+uern/gi, 'Permanência Estudantil');
    t = t.replace(/programa\s+de\s+apoio\s+[àa]\s+perman[êe]ncia\s+estudantil/gi, 'Permanência Estudantil');
    t = t.replace(/exclusivamente\s+na\s+modalidade\s+/gi, '');
    t = t.replace(/\s*,\s*semestre\s+(\d{4}\.\d)/gi, ' ($1)');
    t = t.replace(/\s*\.\s*$/, '');
    t = t.replace(/\s{2,}/g, ' ').trim();

    const tituloFormatado = formatarTituloEdital(t);

    return {
        numeroEdital,
        tituloLimpo: tituloFormatado || formatarTituloEdital(textoOriginal)
    };
}

function toggleFiltroVigentes() {
    const checkbox = document.getElementById('filtroVigentes');
    filtroVigentesAtivo = checkbox.checked;
    if (tipoAtual === 'favoritos') {
        carregarFavoritos();
    } else if (tipoAtual === 'personalizado') {
        carregarFeedPersonalizado();
    } else {
        carregarDados(tipoAtual, 1);
    }
}

async function carregarDados(tipo, novaPagina = 1) {
    tipoAtual = tipo;
    paginaAtual = novaPagina;

    destacarBotaoAtivo(`btn-${tipo}`);

    const container = document.getElementById('container-vagas');
    container.style.display = 'grid';
    container.innerHTML = '<p class="carregando">Buscando oportunidades oficiais...</p>';

    try {
        let url = `${API_URL}/${tipo}?pagina=${paginaAtual}&limite=6`;
        if (filtroVigentesAtivo) {
            url += `&apenas_vigentes=true`;
        }

        const resposta = await fetch(url, {
            method: 'GET',
            headers: getAuthHeaders(),
            signal: AbortSignal.timeout(10000)
        });

        if (!resposta.ok) {
            throw new Error(`Erro na requisição: ${resposta.status}`);
        }

        const objetoPaginado = await resposta.json();
        renderizarCards(objetoPaginado.dados);
        renderizarControlesPaginacao(objetoPaginado.pagina_atual, objetoPaginado.total_documentos, objetoPaginado.limite_por_pagina);

    } catch (erro) {
        console.error("Erro ao buscar dados paginados:", erro);
        container.innerHTML = `<p class="carregando" style="color: red;">Erro ao conectar com a API: ${erro.message || 'Verifique se o backend está em execução.'}</p>`;
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
                <p class="status-box-texto">Não foram localizadas oportunidades para o filtro selecionado.</p>
            </div>
        `;
        return;
    }

    const corCategoriaMap = {
        "Estágios (PRAE)": "#112244",
        "Bolsas (PROEX)": "#FF7A00",
        "Editais UFERSA": "#6B21A8",
        "UFERSA": "#6B21A8",
        "Estágios MPRN": "#1E3A8A",
        "Editais IFRN": "#15803D",
        "Estágios IEL/RN": "#B45309",
        "DOM Mossoró": "#4338CA",
        "Vagas CIEE": "#0F4C81",
        "Portal UERN": "#C2410C",
        "Comunicado Oficial": "#475569",
        "Acadêmico UERN": "#0284C7",
        "Estágio UERN": "#1E3A8A",
        "Bolsas UERN": "#EA580C",
        "Intercâmbio & Cursos": "#0D9488",
        "Notícia UERN": "#047857",
        "Notícia Tech": "#1E7E34",
        "Notícia UFERSA": "#7C3AED",
        "Notícia Educação": "#0891B2",
        "Notícia Saúde": "#DB2777",
        "Notícia Economia": "#CA8A04",
        "Notícia Geral": "#2563EB",
        "Notícia": "#2563EB",
        "Bolsa de Estudos": "#0D9488",
        "Capacitação & Cursos": "#7C3AED"
    };

    const favSet = (usuarioAtual && usuarioAtual.favoritos) ? new Set(usuarioAtual.favoritos.map(String)) : new Set();

    listaDeVagas.forEach(vaga => {
        const idStr = String(vaga._id);
        const ehFavorito = vaga.favorito === true || favSet.has(idStr);
        const catLower = (vaga.categoria || "").toLowerCase();
        const ehNoticia = vaga.tipo === "noticia" || catLower.includes("notícia") || catLower.includes("noticia") || tipoAtual === "noticias" || tipoAtual === "noticias-ufersa";
        const categoriaFormatada = normalizarCategoriaTag(vaga.categoria, tipoAtual, vaga);
        const corTag = corCategoriaMap[vaga.categoria] || corCategoriaMap[categoriaFormatada] || "#112244";

        let badgeStatusHTML = "";
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
                badgeStatusHTML = `
                    <div class="badge-status badge-status-encerrado" title="Inscrições finalizadas em ${vaga.data_vencimento_formatada}">
                        <i class="ph-bold ph-clock"></i>
                        <span>Encerrado em ${vaga.data_vencimento_formatada}</span>
                    </div>
                `;
            } else {
                const complemento = dias === 0 ? " (último dia!)" : ` (${dias}d restantes)`;
                badgeStatusHTML = `
                    <div class="badge-status badge-status-vigente" title="Inscrições abertas até ${vaga.data_vencimento_formatada}">
                        <i class="ph-bold ph-check-circle"></i>
                        <span>Até ${vaga.data_vencimento_formatada}${complemento}</span>
                    </div>
                `;
            }
        }

        const classeVencido = status === "vencido" ? "card-vencido" : "";
        const tituloBruto = vaga.titulo || vaga.nome || vaga.nome_completo || 'Oportunidade';
        const infoEdital = sintetizarTituloEdital(tituloBruto);
        const tituloFinal = infoEdital.tituloLimpo || tituloBruto;

        const numeroEditalHTML = infoEdital.numeroEdital ? `
            <div class="card-edital-numero">
                <i class="ph-bold ph-file-text"></i>
                <span>${infoEdital.numeroEdital}</span>
            </div>
        ` : '';

        let linkFonteHTML = vaga.fonte || 'Universidade';
        if (vaga.meta_fonte && vaga.meta_fonte.nome_oficial) {
            const nomeCurto = vaga.meta_fonte.nome_oficial.split(" - ")[0];
            linkFonteHTML = `
                <a href="${vaga.meta_fonte.url_oficial}" target="_blank" rel="noopener noreferrer"
                   title="${vaga.meta_fonte.nome_oficial}"
                   class="meta-link-oficial">
                    ${nomeCurto} ↗
                </a>
            `;
        }

        const linkDestino = vaga.link || vaga.url || '#';
        let textoAcao = 'Ver Edital Oficial';
        if (ehNoticia) {
            textoAcao = 'Ler Notícia';
        } else if (tipoAtual === 'cursos-bolsas' || vaga.tipo === 'capacitacao') {
            textoAcao = 'Ver Curso / Inscrever-se';
        }

        const cardHTML = `
            <div class="card ${classeVencido}">
                <div class="card-topo">
                    <div class="card-tags-row">
                        <span class="card-categoria-tag" style="background-color: ${corTag};" title="${vaga.categoria || 'Geral'}">
                            ${categoriaFormatada}
                        </span>
                        ${badgeStatusHTML}
                    </div>

                    ${numeroEditalHTML}

                    <h3 class="card-titulo" title="${tituloBruto}">${tituloFinal}</h3>

                    <div class="card-meta-box">
                        <i class="ph-bold ph-buildings meta-icone"></i>
                        <span class="meta-texto"><strong>Origem:</strong> ${linkFonteHTML}</span>
                    </div>
                </div>

                <div class="card-acoes-row">
                    <a href="${linkDestino}" target="_blank" rel="noopener noreferrer" class="card-link-btn">
                        <span>${textoAcao}</span>
                        <i class="ph-bold ph-arrow-up-right"></i>
                    </a>

                    <button id="fav-btn-${idStr}"
                        class="btn-favoritar-card ${ehFavorito ? 'favoritado' : ''}"
                        onclick="toggleFavorito('${idStr}', event)"
                        title="${ehFavorito ? 'Remover dos favoritos' : 'Salvar oportunidade'}">
                        <i class="${ehFavorito ? 'ph-fill ph-star' : 'ph-bold ph-star'}"></i>
                        <span>${ehFavorito ? 'Salvo' : 'Salvar'}</span>
                    </button>
                </div>
            </div>
        `;
        container.innerHTML += cardHTML;
    });
}

function renderizarControlesPaginacao(atual, total, limite) {
    const antigo = document.getElementById('bloco-paginacao');
    if (antigo) antigo.remove();

    const totalPaginas = Math.max(1, Math.ceil((total || 0) / (limite || 6)));
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
        <button class="btn-paginacao-nav" ${atual === 1 ? 'disabled' : ''} onclick="carregarDados('${tipoAtual}', ${atual - 1})"
            style="opacity: ${atual === 1 ? '0.5' : '1'}; cursor: ${atual === 1 ? 'not-allowed' : 'pointer'};">
            ◀ Anterior
        </button>
        <span class="paginacao-texto-info">Página ${atual} de ${totalPaginas}</span>
        <button class="btn-paginacao-nav" ${atual >= totalPaginas ? 'disabled' : ''} onclick="carregarDados('${tipoAtual}', ${atual + 1})"
            style="opacity: ${atual >= totalPaginas ? '0.5' : '1'}; cursor: ${atual >= totalPaginas ? 'not-allowed' : 'pointer'};">
            Próximo ▶
        </button>
    `;
    mainContainer.appendChild(blocoPaginacao);
}

// 1. Pesquisa Textual
async function realizarPesquisa() {
    const termo = document.getElementById('input-busca').value;
    if (!termo) return;

    const container = document.getElementById('container-vagas');
    container.innerHTML = '<p class="carregando">Consultando índices no MongoDB...</p>';

    const antigo = document.getElementById('bloco-paginacao');
    if (antigo) antigo.remove();

    try {
        const resposta = await fetch(`${API_URL}/pesquisar?termo=${encodeURIComponent(termo)}`, {
            method: 'GET',
            headers: getAuthHeaders(),
            signal: AbortSignal.timeout(10000)
        });

        if (!resposta.ok) {
            throw new Error(`Erro na pesquisa: ${resposta.status}`);
        }

        const dados = await resposta.json();
        renderizarCards(dados);
        document.querySelectorAll('.tab-origem-btn, .btn-filtro-aluno').forEach(b => b.classList.remove('ativo'));
    } catch (e) {
        console.error("Erro na pesquisa:", e);
        container.innerHTML = `<div class="status-box" style="border-color: var(--color-red);"><h3 class="status-box-titulo" style="color: var(--color-red);">Erro na Pesquisa</h3><p class="status-box-texto">${e.message}</p></div>`;
    }
}

// 2. Indicadores e Métricas
function escaparHTML(texto) {
    const div = document.createElement('div');
    div.textContent = texto == null ? '' : String(texto);
    return div.innerHTML;
}

// "Data → dias restantes" para o widget de prazos (retorna null se inválida)
function calcularDiasAteData(dataStr) {
    if (!dataStr || !/^\d{2}\/\d{2}\/\d{4}$/.test(String(dataStr).trim())) return null;
    const [dia, mes, ano] = String(dataStr).trim().split('/').map(Number);
    const alvo = new Date(ano, mes - 1, dia, 23, 59, 59);
    if (isNaN(alvo.getTime())) return null;
    return Math.ceil((alvo - new Date()) / 86400000);
}

// Navegação a partir dos itens do painel de prazos: abre o edital original.
// Se o link direto não vier na API, cai no fallback: filtra o hub pelo título.
function irParaEdital(link, id) {
    if (link && /^https?:\/\//i.test(link)) {
        window.open(link, '_blank', 'noopener,noreferrer');
        return;
    }
    const campoBusca = document.getElementById('input-busca');
    const item = typeof event !== 'undefined' && event && event.currentTarget
        ? event.currentTarget.querySelector('.dash-prazo-item-titulo')
        : null;
    if (campoBusca && item) {
        campoBusca.value = item.textContent.trim();
        if (typeof realizarPesquisa === 'function') realizarPesquisa();
    }
}

// Regra do dashboard no tema ESCURO: tudo que é escuro no tema claro passa a
// ser CLARO. Cores inline (barras, pilares, anéis de progresso) são ajustadas
// aqui, pois o CSS não alcança valores definidos via style="".
const CORES_ESCURAS_TEMA_CLARO = new Set([
    '#0F172A', '#1E3A8A', '#1E293B', '#EA580C', '#0284C7', '#0D47A1', '#166534'
]);
const COR_ESCURA_PARA_CLARA = {
    '#0F172A': '#F8FAFC',
    '#1E3A8A': '#93C5FD',
    '#1E293B': '#CBD5E1',
    '#EA580C': '#FB923C',
    '#0284C7': '#7DD3FC',
    '#0D47A1': '#93C5FD',
    '#166534': '#6EE7B7'
};

function ajustarCoresDashboardParaTema() {
    const container = document.getElementById('container-vagas');
    if (!container || !container.querySelector('.dashboard-neo-wrapper')) return;

    const ehEscuro = document.documentElement.classList.contains('dark');

    // 1. Preenchimentos (barras de fluxo, ranking de fontes, categorias) e
    //    pílulas zero: cor clara quando o tema é escuro.
    const alvosCor = container.querySelectorAll(
        '.dash-barra-pilar, .dash-ranking-preenchimento, .dash-cat-preenchimento, .dash-pill-zero, .dash-donut-container, .dash-slider-progresso'
    );
    alvosCor.forEach(el => {
        const original = el.dataset.corOriginal || (el.style.background || '').trim().toUpperCase();
        if (!el.dataset.corOriginal) el.dataset.corOriginal = original;
        let corFinal = original;
        if (ehEscuro && CORES_ESCURAS_TEMA_CLARO.has(original)) {
            corFinal = COR_ESCURA_PARA_CLARA[original] || '#F8FAFC';
        }
        if (corFinal) el.style.background = corFinal;
        // Anéis donut usam variáveis CSS para o conic-gradient
        if (el.classList.contains('dash-donut-container') && corFinal) {
            el.style.setProperty('--cor-anel', corFinal);
        }
    });

    // 2. Pontos da legenda: contorno branco no tema escuro (fundo escuro).
    container.querySelectorAll('.dash-legenda-ponto').forEach(ponto => {
        ponto.style.borderColor = ehEscuro ? '#FFFFFF' : '';
    });

    // 3. Fundo dos cards KPI acompanha o tema (pastel no claro / grafite no escuro).
    container.querySelectorAll('.dash-kpi-card').forEach(card => {
        card.style.backgroundColor = ehEscuro ? '#1E293B' : '';
    });
}

window.addEventListener('themechange', () => {
    try { ajustarCoresDashboardParaTema(); } catch (e) {}
});

function animarNumero(el, alvo, duracao = 900) {
    const prefereMenosMovimento = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefereMenosMovimento || duracao <= 0) { el.textContent = alvo; return; }
    const inicio = performance.now();
    function passo(agora) {
        const progresso = Math.min((agora - inicio) / duracao, 1);
        const suavizado = 1 - Math.pow(1 - progresso, 3);
        el.textContent = Math.round(alvo * suavizado);
        if (progresso < 1) requestAnimationFrame(passo);
    }
    requestAnimationFrame(passo);
}

async function carregarEstatisticas() {
    const antigo = document.getElementById('bloco-paginacao');
    if (antigo) antigo.remove();

    const container = document.getElementById('container-vagas');
    container.style.display = 'block';
    container.innerHTML = '<p class="carregando">Gerando painel visual...</p>';

    destacarBotaoAtivo('btn-analises');

    try {
        const resposta = await fetch(`${API_URL}/estatisticas`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(15000)
        });

        if (!resposta.ok) throw new Error(`Erro: ${resposta.status}`);

        const dados = await resposta.json();
        const totais = dados.totais || {};
        const totalEstagios = (totais.estagios || 0) + (totais.mprn || 0) + (totais.iel || 0) + (totais.ciee || 0);
        const totalBolsas = totais.bolsas || 0;
        const totalTech = totais.noticias || 0;
        const totalCursosBolsas = totais.cursos_bolsas || 0;
        const totalUfersa = totais.ufersa || 0;
        const totalUern = totais.portal_uern || 0;
        const totalDom = totais.dom || 0;
        const totalGeral = dados.total_geral || (totalEstagios + totalBolsas + totalTech + totalUfersa + totalUern);
        const retaFinal = dados.reta_final_urgente || 0;
        const canais = dados.canais_monitorados || 0;
        const vigentes = dados.vigentes || 0;
        const vencidos = dados.vencidos || 0;
        const proximos = dados.proximos_a_vencer || [];
        const vencidosLista = dados.vencidos_recentes || [];
        const totalPrazos = vigentes + retaFinal + vencidos;

        // Paleta por KPI espelhando o design de referência (cor + fundo pastel da pílula)
        const PALETA_KPI = {
            laranja:  { cor: '#FF5C00', bg: '#FFF4ED' },
            coral:    { cor: '#EA580C', bg: '#FFF4ED' },
            ciano:    { cor: '#0284C7', bg: '#EFF9FE' },
            roxo:     { cor: '#8B5CF6', bg: '#F5F1FD' },
            verde:    { cor: '#10B981', bg: '#EEFDF5' },
            azul:     { cor: '#1E3A8A', bg: '#EEF2FE' },
            grafite:  { cor: '#1E293B', bg: '#EFF3F8' }
        };

        // No tema ESCURO, tudo que é escuro no tema CLARO vira CLARO
        // (regra global do dashboard): cores escuras são clareadas via CSS.
        window.dispatchEvent(new Event('themechange'));

        const kpis = [
            { rotulo: 'TOTAL NO HUB', numero: totalGeral, icone: 'ph-stack', cor: 'laranja', acao: "carregarDados('estagios')" },
            { rotulo: 'ESTÁGIOS (PRAE / CIEE / MPRN / IEL)', numero: totalEstagios, icone: 'ph-graduation-cap', cor: 'coral', acao: "carregarDados('estagios')" },
            { rotulo: 'BOLSAS (PROEX)', numero: totalBolsas, icone: 'ph-coins', cor: 'ciano', acao: "carregarDados('bolsas')" },
            { rotulo: 'EDITAIS UFERSA', numero: totalUfersa, icone: 'ph-bank', cor: 'roxo', acao: "carregarDados('ufersa')" },
            { rotulo: 'CURSOS & BOLSAS', numero: totalCursosBolsas, icone: 'ph-book-open', cor: 'ciano', acao: "carregarDados('cursos-bolsas')" },
            { rotulo: 'NOTÍCIAS (TECH, EDU, SAÚDE...)', numero: totalTech, icone: 'ph-lightning', cor: 'verde', acao: "carregarDados('noticias')" },
            { rotulo: 'PORTAL UERN (MINERADO)', numero: totalUern, icone: 'ph-magnifying-glass', cor: 'azul', acao: "carregarDados('portal_uern')" },
            { rotulo: 'DOM MOSSORÓ', numero: totalDom, icone: 'ph-newspaper-clipping', cor: 'grafite', acao: "carregarDados('dom')" }
        ];

        let html = `
            <div class="dashboard-neo-wrapper">
                <!-- LINHA SUPERIOR: INDICADORES GLOBAIS -->
                <div class="dash-bloco-superior">
                    <div class="dash-bloco-header">
                        <div class="dash-bloco-titulo-row">
                            <h2 class="dash-neo-titulo">Indicadores Globais</h2>
                            <span class="dash-tag-tempo-real">Tempo Real</span>
                        </div>
                        <p class="dash-neo-subtitulo">Panorama das oportunidades coletadas pelos robôs em ${canais} canais monitorados. Clique em um indicador para explorar os editais.</p>
                    </div>

                    <div class="dash-grid-top-cards">
                        ${kpis.map(k => {
                            const paleta = PALETA_KPI[k.cor] || PALETA_KPI.laranja;
                            return `
                        <button type="button" class="dash-kpi-card card-cor-${k.cor}" style="--kpi-cor: ${paleta.cor}; --kpi-bg: ${paleta.bg};" onclick="${k.acao}" title="Ver ${k.rotulo}">
                            <span class="dash-kpi-icone"><i class="ph-bold ${k.icone}"></i></span>
                            <span class="dash-kpi-badge-label">${k.rotulo}</span>
                            <div class="dash-kpi-numero" data-alvo="${k.numero}">0</div>
                        </button>`; }).join('')}
                    </div>
                </div>

                <!-- LINHA DO MEIO: PAINEL DE PRAZOS (ABERTOS x VENCIDOS) -->
                <div class="dash-grid-widgets-circulares">
                    <div class="dash-card-prazos">
                        <div class="dash-prazos-header">
                            <div class="dash-widget-titulo-row">
                                <span class="dash-icone-box bg-laranja"><i class="ph-bold ph-calendar-check"></i></span>
                                <h3 class="dash-widget-titulo">Editais: Abertos x Vencidos</h3>
                            </div>
                            <p class="dash-widget-desc">Acompanhe em tempo real quais editais ainda aceitam inscrições e quais já encerraram o prazo.</p>
                        </div>

                        <div class="dash-prazos-resumo">
                            <button type="button" class="dash-prazo-chip chip-aberto" onclick="carregarDados('estagios')" title="Ver oportunidades com inscrições abertas">
                                <span class="dash-prazo-chip-icone"><i class="ph-bold ph-check-circle"></i></span>
                                <div class="dash-prazo-chip-conteudo">
                                    <span class="dash-prazo-chip-numero" data-alvo="${vigentes}">0</span>
                                    <span class="dash-prazo-chip-rotulo">Abertos para inscrição</span>
                                </div>
                            </button>
                            <button type="button" class="dash-prazo-chip chip-vencendo" title="Editais que vencem nos próximos 7 dias">
                                <span class="dash-prazo-chip-icone"><i class="ph-bold ph-timer"></i></span>
                                <div class="dash-prazo-chip-conteudo">
                                    <span class="dash-prazo-chip-numero" data-alvo="${retaFinal}">0</span>
                                    <span class="dash-prazo-chip-rotulo">Vencem em até 7 dias</span>
                                </div>
                            </button>
                            <div class="dash-prazo-chip chip-vencido">
                                <span class="dash-prazo-chip-icone"><i class="ph-bold ph-prohibit"></i></span>
                                <div class="dash-prazo-chip-conteudo">
                                    <span class="dash-prazo-chip-numero" data-alvo="${vencidos}">0</span>
                                    <span class="dash-prazo-chip-rotulo">Editais vencidos</span>
                                </div>
                            </div>
                        </div>

                        <!-- Barra proporcional: leitura visual imediata da distribuição dos editais -->
                        <div class="dash-prazos-proporcao" role="img" aria-label="Distribuição entre abertos, vencendo em breve e vencidos">
                            <p class="dash-proporcao-titulo">Proporção do acervo monitorado</p>
                            <div class="dash-proporcao-track">
                                <span class="dash-proporcao-seg seg-aberto" style="width: ${totalPrazos ? (vigentes / totalPrazos * 100) : 0}%"></span>
                                <span class="dash-proporcao-seg seg-vencendo" style="width: ${totalPrazos ? (retaFinal / totalPrazos * 100) : 0}%"></span>
                                <span class="dash-proporcao-seg seg-vencido" style="width: ${totalPrazos ? (vencidos / totalPrazos * 100) : 0}%"></span>
                            </div>
                            <div class="dash-proporcao-legenda">
                                <span class="dash-proporcao-chave"><i class="chave-ponto ponto-aberto"></i> Abertos</span>
                                <span class="dash-proporcao-chave"><i class="chave-ponto ponto-vencendo"></i> Vencem em 7 dias</span>
                                <span class="dash-proporcao-chave"><i class="chave-ponto ponto-vencido"></i> Vencidos</span>
                            </div>
                        </div>

                        <div class="dash-prazos-listas">
                            <div class="dash-prazo-coluna">
                                <h4 class="dash-prazo-coluna-titulo titulo-aberto">
                                    <i class="ph-bold ph-flag-banner"></i> Próximos a vencer
                                </h4>
                                ${proximos.length ? proximos.map(e => {
                                    const diasRestantes = calcularDiasAteData(e.data);
                                    return `
                                <button type="button" class="dash-prazo-item item-aberto" onclick="irParaEdital('${escaparHTML(e.link || '')}', '${escaparHTML(e.id || '')}')" title="Abrir este edital">
                                    <span class="dash-prazo-item-seta"><i class="ph-bold ph-arrow-up-right"></i></span>
                                    <span class="dash-prazo-item-titulo">${escaparHTML(e.titulo)}</span>
                                    <span class="dash-prazo-item-badges">
                                        ${diasRestantes !== null && diasRestantes <= 3 ? '<span class="prazo-alerta-urgente"><i class="ph-bold ph-alarm"></i> Urgente</span>' : ''}
                                        <strong class="dash-prazo-item-data">${escaparHTML(e.data)}</strong>
                                    </span>
                                </button>`; }).join('') : `<p class="dash-legenda-texto">Nenhum edital vence nos próximos 7 dias. 🎉</p>`}
                            </div>
                            <div class="dash-prazo-coluna">
                                <h4 class="dash-prazo-coluna-titulo titulo-vencido">
                                    <i class="ph-bold ph-prohibit"></i> Encerrados recentemente
                                </h4>
                                ${vencidosLista.length ? vencidosLista.map(e => `
                                <button type="button" class="dash-prazo-item item-vencido" onclick="irParaEdital('${escaparHTML(e.link || '')}', '${escaparHTML(e.id || '')}')" title="Abrir este edital">
                                    <span class="dash-prazo-item-seta"><i class="ph-bold ph-arrow-up-right"></i></span>
                                    <span class="dash-prazo-item-titulo">${escaparHTML(e.titulo)}</span>
                                    <span class="dash-prazo-item-badges">
                                        <strong class="dash-prazo-item-data">${escaparHTML(e.data)}</strong>
                                    </span>
                                </button>`).join('') : `<p class="dash-legenda-texto">Nenhum edital encerrado recentemente.</p>`}
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        `;
        container.innerHTML = html;

        // Animação contada dos números (count-up)
        container.querySelectorAll('[data-alvo]').forEach((el, i) => {
            animarNumero(el, parseInt(el.dataset.alvo, 10) || 0, 700 + i * 40);
        });

        ajustarCoresDashboardParaTema();
    } catch (erro) {
        container.innerHTML = `
            <div class="status-box" style="border-color: var(--color-red);">
                <h3 class="status-box-titulo" style="color: var(--color-red);">Falha ao gerar painel</h3>
                <p class="status-box-texto">${erro.message}. Verifique se a API está rodando em localhost:8000.</p>
            </div>`;
    }
}

function mostrarToast(mensagem, tipo = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-item-memphis toast-${tipo}`;

    let icone = '<i class="ph-bold ph-bell"></i>';
    if (tipo === 'sucesso') icone = '<i class="ph-bold ph-check-circle"></i>';
    if (tipo === 'erro') icone = '<i class="ph-bold ph-x-circle"></i>';
    if (tipo === 'info') icone = '<i class="ph-bold ph-info"></i>';

    toast.innerHTML = `
        <span class="toast-icone">${icone}</span>
        <span class="toast-texto">${mensagem}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-saindo');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

// Add keyboard support for closing sidebar
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const sidebar = document.getElementById('sidebar-perfil');
        if (sidebar && sidebar.classList.contains('aberto')) {
            fecharSidebarPerfil();
        }
    }
});