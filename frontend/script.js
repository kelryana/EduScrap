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

        const fotoPerfil = usuarioAtual.foto_perfil || '';
        let avatarHTML = `<i class="ph-bold ph-student"></i>`;
        if (fotoPerfil) {
            if (fotoPerfil.startsWith('preset:')) {
                const presetIcone = fotoPerfil.replace('preset:', '');
                avatarHTML = `<i class="ph-bold ${presetIcone}"></i>`;
            } else {
                avatarHTML = `<img src="${fotoPerfil}" alt="Avatar" class="nav-avatar-img">`;
            }
        }

        navAuth.innerHTML = `
            <div class="nav-user-box" onclick="carregarPortalUsuario()" title="Acessar Portal do Estudante" style="cursor: pointer;">
                <span class="nav-user-tag" style="display: inline-flex; align-items: center; gap: 8px;">
                    <span class="nav-avatar-mini">${avatarHTML}</span>
                    <span>Olá, <strong id="user-name-display">${primeiroNome}</strong></span>
                </span>
                <button class="btn-nav-mini btn-nav-logout" onclick="event.stopPropagation(); fazerLogout();" title="Sair da Conta">
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
    // Se o usuário clicar em "Salvos" quando já estiver na tela de favoritos,
    // atua como toggle e retorna para a aba padrão 'estagios'
    if (tipoAtual === 'favoritos') {
        carregarDados('estagios', 1);
        return;
    }

    tipoAtual = 'favoritos';
    alternarExibicaoFiltroVigentes(true);
    const container = document.getElementById('container-vagas');
    const antigo = document.getElementById('bloco-paginacao');
    if (antigo) antigo.remove();

    destacarBotaoAtivo('btn-favoritos');

    if (!usuarioAtual) {
        container.style.display = 'block';
        container.innerHTML = `
            <div class="status-box" style="border-color: var(--color-orange);">
                <div class="status-box-decor"></div>
                <h3 class="status-box-titulo"><i class="ph-bold ph-lock-key"></i> Faça Login para Ver Seus Salvos</h3>
                <p class="status-box-texto">Você precisa estar conectado para acessar as oportunidades que favoritou e acompanhar prazos.</p>
                <div style="margin-top: 15px; display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                    <button class="btn-hero-primary" onclick="abrirModalAuth('login')">
                        <i class="ph ph-sign-in"></i> Entrar na Minha Conta
                    </button>
                    <button class="btn-hero-secondary" onclick="carregarDados('estagios', 1)">
                        <i class="ph ph-arrow-left"></i> Voltar aos Editais
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
        let lista = data.data || [];

        if (filtroVigentesAtivo) {
            const agora = new Date();
            lista = lista.filter(item => {
                if (!item.data_vencimento) return true;
                const dv = new Date(item.data_vencimento);
                return isNaN(dv.getTime()) || dv >= agora;
            });
        }

        if (lista.length === 0) {
            container.style.display = 'block';
            container.innerHTML = `
                <div class="status-box">
                    <div class="status-box-decor"></div>
                    <h3 class="status-box-titulo"><i class="ph-bold ph-star"></i> Nenhum Edital Favoritado Ainda</h3>
                    <p class="status-box-texto">Clique na estrelinha dos editais e vagas para salvá-los e acompanhar os prazos aqui!</p>
                    <div style="margin-top: 15px; display: flex; justify-content: center;">
                        <button class="btn-hero-primary" onclick="carregarDados('estagios', 1)">
                            <i class="ph ph-magnifying-glass"></i> Explorar Oportunidades
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        renderizarCards(lista);

    } catch (err) {
        container.style.display = 'block';
        container.innerHTML = `
            <div class="status-box" style="border-color: var(--color-red);">
                <h3 class="status-box-titulo" style="color: var(--color-red);"><i class="ph-bold ph-warning-circle"></i> Falha ao Carregar Favoritos</h3>
                <p class="status-box-texto">${err.message}. Verifique a conexão com o servidor.</p>
                <div style="margin-top: 15px; display: flex; justify-content: center;">
                    <button class="btn-hero-secondary" onclick="carregarDados('estagios', 1)">
                        <i class="ph ph-arrow-left"></i> Voltar aos Editais
                    </button>
                </div>
            </div>
        `;
    }
}

async function carregarFeedPersonalizado() {
    tipoAtual = 'personalizado';
    alternarExibicaoFiltroVigentes(true);
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
        let lista = data.data || [];

        if (filtroVigentesAtivo) {
            const agora = new Date();
            lista = lista.filter(item => {
                if (!item.data_vencimento) return true;
                const dv = new Date(item.data_vencimento);
                return isNaN(dv.getTime()) || dv >= agora;
            });
        }

        renderizarCards(lista);

    } catch (err) {
        container.innerHTML = `<p class="carregando" style="color: red;">Erro ao gerar feed personalizado: ${err.message}</p>`;
    }
}

function destacarBotaoAtivo(idBotao) {
    document.querySelectorAll('.tab-origem-btn, .btn-filtro-aluno').forEach(btn => btn.classList.remove('ativo'));
    const btn = document.getElementById(idBotao);
    if (btn) btn.classList.add('ativo');

    if (idBotao === 'btn-analises' || idBotao === 'btn-portal-usuario' || idBotao === 'btn-abrir-sidebar-filtros') {
        alternarExibicaoFiltroVigentes(false);
    }
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

function alternarExibicaoFiltroVigentes(visivel) {
    const elId = document.getElementById('toolbar-filtro-vigentes');
    const right = document.querySelector('.student-toolbar-right');
    const toggle = document.querySelector('.toggle-vigentes-container');

    [elId, right, toggle].forEach(el => {
        if (!el) return;
        if (visivel) {
            el.classList.remove('escondido');
            el.style.removeProperty('display');
        } else {
            el.classList.add('escondido');
            el.style.setProperty('display', 'none', 'important');
        }
    });

    if (visivel) {
        document.body.classList.remove('filtro-vigentes-oculto');
    } else {
        document.body.classList.add('filtro-vigentes-oculto');
    }
}

function toggleFiltroVigentes() {
    const checkbox = document.getElementById('filtroVigentes');
    if (!checkbox) return;
    filtroVigentesAtivo = checkbox.checked;

    // Não executa requisições de editais se estiver no perfil ou indicadores (evita 404)
    if (tipoAtual === 'perfil' || tipoAtual === 'indicadores' || tipoAtual === 'analises') {
        return;
    }

    if (tipoAtual === 'favoritos') {
        carregarFavoritos();
    } else if (tipoAtual === 'personalizado') {
        carregarFeedPersonalizado();
    } else if (tipoAtual) {
        carregarDados(tipoAtual, 1);
    } else {
        carregarDados('estagios', 1);
    }
}

async function carregarDados(tipo, novaPagina = 1) {
    tipoAtual = tipo;
    paginaAtual = novaPagina;

    alternarExibicaoFiltroVigentes(true);
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

    alternarExibicaoFiltroVigentes(true);

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

// Sanitização de títulos de editais e extração de órgãos
function sanitizarItemEdital(titulo) {
    if (!titulo) return { tag: 'GERAL', tituloLimpo: 'Edital de Oportunidade' };
    let t = String(titulo).trim();
    let tag = 'GERAL';

    if (/\[MPRN\]|MPRN/i.test(t)) { tag = 'MPRN'; t = t.replace(/\[MPRN\]/gi, '').trim(); }
    else if (/UFERSA/i.test(t)) { tag = 'UFERSA'; t = t.replace(/\[UFERSA\]/gi, '').trim(); }
    else if (/UERN/i.test(t)) { tag = 'UERN'; t = t.replace(/\[UERN\]/gi, '').trim(); }
    else if (/IFRN/i.test(t)) { tag = 'IFRN'; t = t.replace(/\[IFRN\]/gi, '').trim(); }
    else if (/CIEE/i.test(t)) { tag = 'CIEE'; t = t.replace(/\[CIEE\]/gi, '').trim(); }
    else if (/IEL/i.test(t)) { tag = 'IEL'; t = t.replace(/\[IEL\]/gi, '').trim(); }
    else if (/DOM|Prefeitura de Mossoró/i.test(t)) { tag = 'DOM'; t = t.replace(/\[DOM\/Mossoró\]/gi, '').trim(); }
    else if (/PRAE/i.test(t)) { tag = 'PRAE'; }
    else if (/PROEX/i.test(t)) { tag = 'PROEX'; }

    // Limpeza de ruídos de scraping/OCR
    t = t.replace(/–\s*PRAETORNA\s*PÚBLICO/gi, '– PRAE Torna Público');
    t = t.replace(/–\s*TTORNA\s*PÚBLICO/gi, '– Torna Público');
    t = t.replace(/–\s*TORNA\s*PÚBLICO/gi, '– Torna Público');
    t = t.replace(/PRAETORNA/gi, 'PRAE Torna');

    return { tag, tituloLimpo: t };
}

function alternarAbaPrazos(aba, btn) {
    if (!btn) {
        btn = document.querySelector(`[data-purpose="tab-filters"] button[data-aba="${aba}"]`);
    }
    const todosBotoes = document.querySelectorAll('[data-purpose="tab-filters"] button');
    todosBotoes.forEach(b => {
        b.className = 'px-4 sm:px-5 py-2.5 bg-white text-slate-800 rounded-xl text-xs sm:text-sm md:text-base font-extrabold flex items-center space-x-2 border-2 border-slate-900 hover:bg-slate-50 transition cursor-pointer';
        const svg = b.querySelector('svg');
        if (svg) {
            svg.classList.remove('text-white');
            svg.classList.add('text-slate-700');
        }
    });
    if (btn) {
        btn.className = 'px-4 sm:px-5 py-2.5 bg-slate-900 text-white rounded-xl text-xs sm:text-sm md:text-base font-extrabold flex items-center space-x-2 border-2 border-slate-900 shadow-sm transition hover:bg-slate-800 cursor-pointer ativo';
        const svg = btn.querySelector('svg');
        if (svg) {
            svg.classList.remove('text-slate-700');
            svg.classList.add('text-white');
        }
    }

    const colProximos = document.getElementById('col-prazos-proximos');
    const colEncerrados = document.getElementById('col-prazos-encerrados');
    const grid = document.getElementById('dash-prazos-listas-grid');
    const tituloColAbertos = document.getElementById('dash-titulo-col-abertos');
    const msgSemRetaFinal = document.getElementById('dash-msg-sem-reta-final');
    if (!colProximos || !colEncerrados) return;

    const cardsAbertos = colProximos.querySelectorAll('[data-edital-tipo="aberto"]');

    if (aba === 'proximos') {
        colProximos.style.display = 'block';
        colEncerrados.style.display = 'none';
        if (grid) {
            grid.classList.remove('md:grid-cols-2');
            grid.classList.add('grid-cols-1');
        }
        let visiveis = 0;
        cardsAbertos.forEach(c => {
            if (c.dataset.retaFinal === 'true') {
                c.style.display = 'flex';
                visiveis++;
            } else {
                c.style.display = 'none';
            }
        });
        if (tituloColAbertos) {
            tituloColAbertos.innerHTML = `Vencendo em Breve <span class="font-normal text-slate-500">(${visiveis})</span>`;
        }
        if (msgSemRetaFinal) {
            msgSemRetaFinal.style.display = visiveis === 0 ? 'block' : 'none';
        }
    } else if (aba === 'encerrados') {
        colProximos.style.display = 'none';
        colEncerrados.style.display = 'block';
        if (grid) {
            grid.classList.remove('md:grid-cols-2');
            grid.classList.add('grid-cols-1');
        }
    } else {
        // 'todos' ou 'abertos'
        colProximos.style.display = 'block';
        if (aba === 'abertos') {
            colEncerrados.style.display = 'none';
            if (grid) {
                grid.classList.remove('md:grid-cols-2');
                grid.classList.add('grid-cols-1');
            }
        } else {
            colEncerrados.style.display = 'block';
            if (grid) {
                grid.classList.remove('grid-cols-1');
                grid.classList.add('md:grid-cols-2');
            }
        }
        cardsAbertos.forEach(c => {
            c.style.display = 'flex';
        });
        if (tituloColAbertos) {
            tituloColAbertos.innerHTML = `Editais Abertos <span class="font-normal text-slate-500">(${cardsAbertos.length})</span>`;
        }
        if (msgSemRetaFinal) {
            msgSemRetaFinal.style.display = 'none';
        }
    }
}

function alternarListaEncerrados(btn) {
    const extras = document.getElementById('lista-encerrados-extras');
    if (!extras) return;
    const estaAberto = extras.style.display === 'block';
    extras.style.display = estaAberto ? 'none' : 'block';
    if (btn) {
        const svgIcon = estaAberto
            ? `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M19.5 8.25l-7.5 7.5-7.5-7.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>`
            : `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M4.5 15.75l7.5-7.5 7.5 7.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>`;
        const texto = estaAberto ? (btn.dataset.textoExpandir || 'Mostrar mais editais encerrados') : 'Recolher histórico de editais';
        btn.innerHTML = `${svgIcon}<span>${texto}</span>`;
    }
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
    tipoAtual = 'indicadores';
    alternarExibicaoFiltroVigentes(false);

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
        const editaisAbertos = dados.editais_abertos || dados.proximos_a_vencer || [];
        const proximos = dados.proximos_a_vencer || [];
        const vencidosLista = dados.vencidos_recentes || [];
        // Configuração dos 8 KPIs de topo do dashboard com ícones e acentos idênticos ao layout solicitado
        const kpis = [
            {
                rotulo: 'TOTAL NO HUB',
                numero: totalGeral,
                accent: 'bg-amber-500',
                boxBg: 'bg-amber-50 border-amber-300 text-amber-600',
                svg: `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M3.75 6.75l8.25-4.5 8.25 4.5m-16.5 0l8.25 4.5 8.25-4.5m-16.5 6l8.25 4.5 8.25-4.5m-16.5 6l8.25 4.5 8.25-4.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>`,
                acao: "carregarDados('estagios')"
            },
            {
                rotulo: 'ESTÁGIOS (PRAE / CIEE / MPRN / IEL)',
                numero: totalEstagios,
                accent: 'bg-orange-500',
                boxBg: 'bg-orange-50 border-orange-300 text-orange-600',
                svg: `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M4.26 10.147L12 5.25l7.74 4.897M4.26 10.147l7.74 4.897 7.74-4.897M4.26 10.147v4.603a7.5 7.5 0 0015.48 0v-4.603" stroke-linecap="round" stroke-linejoin="round"></path></svg>`,
                acao: "carregarDados('estagios')"
            },
            {
                rotulo: 'BOLSAS (PROEX)',
                numero: totalBolsas,
                accent: 'bg-cyan-500',
                boxBg: 'bg-cyan-50 border-cyan-300 text-cyan-600',
                svg: `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" stroke-linecap="round" stroke-linejoin="round"></path></svg>`,
                acao: "carregarDados('bolsas')"
            },
            {
                rotulo: 'EDITAIS UFERSA',
                numero: totalUfersa,
                accent: 'bg-purple-600',
                boxBg: 'bg-purple-50 border-purple-300 text-purple-600',
                svg: `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.5m-15 10.5V10.5M3 21h18" stroke-linecap="round" stroke-linejoin="round"></path></svg>`,
                acao: "carregarDados('ufersa')"
            },
            {
                rotulo: 'CURSOS & BOLSAS',
                numero: totalCursosBolsas,
                accent: 'bg-teal-500',
                boxBg: 'bg-teal-50 border-teal-300 text-teal-600',
                svg: `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" stroke-linecap="round" stroke-linejoin="round"></path></svg>`,
                acao: "carregarDados('cursos-bolsas')"
            },
            {
                rotulo: 'NOTÍCIAS (TECH, EDU, SAÚDE...)',
                numero: totalTech,
                accent: 'bg-emerald-500',
                boxBg: 'bg-emerald-50 border-emerald-300 text-emerald-600',
                svg: `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" stroke-linecap="round" stroke-linejoin="round"></path></svg>`,
                acao: "carregarDados('noticias')"
            },
            {
                rotulo: 'PORTAL UERN (MINERADO)',
                numero: totalUern,
                accent: 'bg-blue-600',
                boxBg: 'bg-blue-50 border-blue-300 text-blue-700',
                svg: `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" stroke-linecap="round" stroke-linejoin="round"></path></svg>`,
                acao: "carregarDados('portal_uern')"
            },
            {
                rotulo: 'DOM MOSSORÓ',
                numero: totalDom,
                accent: 'bg-pink-500',
                boxBg: 'bg-pink-50 border-pink-300 text-pink-600',
                svg: `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" stroke-linecap="round" stroke-linejoin="round"></path></svg>`,
                acao: "carregarDados('dom')"
            }
        ];

        // 7 Categorias do Gráfico de Barras Vertical
        const categoriasBarras = [
            {
                id: 'estagios',
                rotulo: 'Estágios',
                total: totalEstagios,
                corClass: 'bg-[#f97316]',
                svg: `<svg class="w-3.5 h-3.5 text-slate-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292" stroke-linecap="round" stroke-linejoin="round"></path></svg>`
            },
            {
                id: 'bolsas',
                rotulo: 'Bolsas',
                total: totalBolsas,
                corClass: 'bg-[#38bdf8]',
                svg: `<svg class="w-3.5 h-3.5 text-slate-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" stroke-linecap="round" stroke-linejoin="round"></path></svg>`
            },
            {
                id: 'ufersa',
                rotulo: 'UFERSA',
                total: totalUfersa,
                corClass: 'bg-[#a855f7]',
                svg: `<svg class="w-3.5 h-3.5 text-slate-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" stroke-linecap="round" stroke-linejoin="round"></path></svg>`
            },
            {
                id: 'cursos-bolsas',
                rotulo: 'Cursos',
                total: totalCursosBolsas,
                corClass: 'bg-[#facc15]',
                svg: `<svg class="w-3.5 h-3.5 text-slate-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" stroke-linecap="round" stroke-linejoin="round"></path></svg>`
            },
            {
                id: 'noticias',
                rotulo: 'Notícias',
                total: totalTech,
                corClass: 'bg-[#10b981]',
                svg: `<svg class="w-3.5 h-3.5 text-slate-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" stroke-linecap="round" stroke-linejoin="round"></path></svg>`
            },
            {
                id: 'portal_uern',
                rotulo: 'UERN',
                total: totalUern,
                corClass: 'bg-[#3b82f6]',
                svg: `<svg class="w-3.5 h-3.5 text-slate-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke-linecap="round" stroke-linejoin="round"></path></svg>`
            },
            {
                id: 'dom',
                rotulo: 'DOM',
                total: totalDom,
                corClass: 'bg-[#f43f5e]',
                svg: `<svg class="w-3.5 h-3.5 text-slate-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke-linecap="round" stroke-linejoin="round"></path></svg>`
            }
        ];
        const maxBarraValor = Math.max(...categoriasBarras.map(c => c.total), 1);

        // Gráfico Donut em SVG: cálculo preciso do comprimento dos arcos (r = 46, Circunferência = 289)
        const totalPrazosCalculo = Math.max(vigentes + vencidos, 1);
        const circ = 289;
        let lenAbertosTotal = (vigentes / totalPrazosCalculo) * circ;
        if (vigentes > 0 && lenAbertosTotal < 16) lenAbertosTotal = 16;
        let lenAbertosNormais = (Math.max(vigentes - retaFinal, 0) / totalPrazosCalculo) * circ;
        if (vigentes > retaFinal && lenAbertosNormais < 10) lenAbertosNormais = 10;
        if (vigentes === retaFinal) lenAbertosNormais = 0;

        const dashOffsetVencendo = Math.max(0, Math.min(289, Math.round(circ - lenAbertosTotal)));
        const dashOffsetAberto = Math.max(0, Math.min(289, Math.round(circ - lenAbertosNormais)));

        let html = `
            <div class="w-full max-w-[1380px] 2xl:max-w-[1440px] bg-white rounded-3xl border-2 border-slate-900 shadow-xl overflow-hidden p-4 sm:p-6 md:p-8 space-y-6 mx-auto" data-purpose="dashboard-wrapper">
                
                <!-- BEGIN: HeaderSection -->
                <header class="text-center pt-1 pb-2" data-purpose="header">
                    <h1 class="text-xl sm:text-2xl md:text-[28px] font-black uppercase tracking-tight text-slate-900">
                        DASHBOARD DE OPORTUNIDADES - HUB
                    </h1>
                </header>
                <!-- END: HeaderSection -->

                <!-- BEGIN: TopMetricCardsGrid -->
                <section class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 sm:gap-3.5" data-purpose="metric-cards">
                    ${kpis.map(k => `
                    <div onclick="${k.acao}" class="relative bg-white border-2 border-slate-900 rounded-2xl pt-4 pb-3.5 px-2.5 flex flex-col items-center justify-between text-center shadow-[0_2px_0_0_rgba(15,23,42,0.9)] hover:shadow-md transition-all cursor-pointer group">
                        <span class="absolute top-0 inset-x-3 h-1.5 ${k.accent} rounded-b-md"></span>
                        <div class="w-9 h-9 sm:w-10 sm:h-10 rounded-xl ${k.boxBg} border-2 flex items-center justify-center mb-2 shadow-sm group-hover:scale-105 transition-transform">
                            ${k.svg}
                        </div>
                        <div class="text-[11px] sm:text-xs font-black tracking-tight text-slate-700 uppercase min-h-[38px] flex items-center justify-center text-center leading-snug px-1">${k.rotulo}</div>
                        <div class="text-2xl sm:text-3xl md:text-4xl font-black text-slate-900 mt-1" data-alvo="${k.numero}">0</div>
                    </div>`).join('')}
                </section>
                <!-- END: TopMetricCardsGrid -->

                <!-- BEGIN: MiddleChartsSection -->
                <section class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch" data-purpose="charts-row">
                    <!-- Left Chart: Donut and Status breakdown (Separado com respiro confortável) -->
                    <div class="lg:col-span-5 flex flex-col sm:flex-row items-center justify-between p-5 sm:p-6 md:p-7 bg-white border-2 border-slate-900 rounded-2xl gap-8 sm:gap-10 md:gap-12 shadow-sm">
                        <!-- Donut Chart representation -->
                        <div class="relative w-44 h-44 sm:w-48 sm:h-48 md:w-52 md:h-52 flex items-center justify-center shrink-0">
                            <svg class="w-44 h-44 sm:w-48 sm:h-48 md:w-52 md:h-52 transform -rotate-90" viewBox="0 0 120 120">
                                <!-- Background base circle (Edital Vencido - Red) -->
                                <circle cx="60" cy="60" fill="transparent" r="46" stroke="#ef4444" stroke-width="18"></circle>
                                <!-- Vencem em breve - Orange arc -->
                                <circle cx="60" cy="60" fill="transparent" r="46" stroke="#f97316" stroke-dasharray="289" stroke-dashoffset="${dashOffsetVencendo}" stroke-width="18"></circle>
                                <!-- Abertos para Inscrição - Emerald Green arc -->
                                <circle cx="60" cy="60" fill="transparent" r="46" stroke="#10b981" stroke-dasharray="289" stroke-dashoffset="${dashOffsetAberto}" stroke-linecap="round" stroke-width="18"></circle>
                                <!-- Inner dark circle ring for border definition -->
                                <circle cx="60" cy="60" fill="none" r="37" stroke="#0f172a" stroke-width="2.5"></circle>
                                <circle cx="60" cy="60" fill="none" r="55" stroke="#0f172a" stroke-width="2.5"></circle>
                            </svg>
                            <!-- Inner Pulse Badge -->
                            <div class="absolute inset-0 m-auto w-16 h-16 sm:w-18 sm:h-18 md:w-20 md:h-20 bg-white rounded-full flex items-center justify-center border-2 sm:border-3 border-slate-900 shadow-md">
                                <svg class="w-7 h-7 sm:w-8 sm:h-8 md:w-9 md:h-9 text-slate-900" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                                    <path d="M3 12h4.5l3-7 4.5 14 3-7H21" stroke-linecap="round" stroke-linejoin="round"></path>
                                </svg>
                            </div>
                        </div>
                        <!-- Donut Legend & Values -->
                        <div class="flex-1 w-full space-y-4 sm:space-y-5 sm:pl-2">
                            <div class="flex items-center justify-between cursor-pointer group" onclick="alternarAbaPrazos('abertos')" title="Ver todos os editais com inscrições abertas">
                                <div class="flex items-center space-x-3">
                                    <span class="w-4 h-4 sm:w-5 sm:h-5 rounded-full bg-[#10b981] border-2 border-slate-900 shrink-0"></span>
                                    <span class="font-black text-slate-800 text-sm sm:text-base md:text-[17px] group-hover:text-emerald-700 transition-colors leading-snug">Abertos para inscrição</span>
                                </div>
                                <span class="text-2xl sm:text-3xl font-black text-slate-900 ml-4 shrink-0" data-alvo="${vigentes}">0</span>
                            </div>
                            <div class="flex items-center justify-between cursor-pointer group" onclick="alternarAbaPrazos('proximos')" title="Ver editais que vencem em até 7 dias">
                                <div class="flex items-center space-x-3">
                                    <span class="w-4 h-4 sm:w-5 sm:h-5 rounded-full bg-[#f97316] border-2 border-slate-900 shrink-0"></span>
                                    <span class="font-black text-slate-800 text-sm sm:text-base md:text-[17px] group-hover:text-orange-700 transition-colors leading-snug">Vencem em até 7 dias</span>
                                </div>
                                <span class="text-2xl sm:text-3xl font-black text-slate-900 ml-4 shrink-0" data-alvo="${retaFinal}">0</span>
                            </div>
                            <div class="flex items-center justify-between cursor-pointer group" onclick="alternarAbaPrazos('encerrados')" title="Ver editais encerrados">
                                <div class="flex items-center space-x-3">
                                    <span class="w-4 h-4 sm:w-5 sm:h-5 rounded-full bg-[#ef4444] border-2 border-slate-900 shrink-0"></span>
                                    <span class="font-black text-slate-800 text-sm sm:text-base md:text-[17px] group-hover:text-red-700 transition-colors leading-snug">Editais vencidos</span>
                                </div>
                                <span class="text-2xl sm:text-3xl font-black text-slate-900 ml-4 shrink-0" data-alvo="${vencidos}">0</span>
                            </div>
                        </div>
                    </div>

                    <!-- Right Chart: Category Bar Distribution (Ampliado nos eixos X e Y) -->
                    <div class="lg:col-span-7 bg-white border-2 border-slate-900 rounded-2xl p-5 sm:p-6 md:p-7 flex flex-col justify-between" data-purpose="bar-chart-card">
                        <!-- Header of Bar Chart -->
                        <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
                            <div>
                                <div class="flex items-center space-x-2.5">
                                    <svg class="w-6 h-6 sm:w-7 sm:h-7 text-amber-500" fill="currentColor" viewBox="0 0 20 20"><path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path></svg>
                                    <h2 class="font-black text-slate-900 text-xl sm:text-2xl tracking-tight">Oportunidades por Categoria</h2>
                                </div>
                                <p class="text-xs sm:text-sm md:text-base text-slate-600 font-semibold mt-0.5">Distribuição de vagas e editais no acervo</p>
                            </div>
                            <span class="text-xs sm:text-sm md:text-base font-black border-2 border-slate-900 rounded-full px-4 py-1.5 bg-white text-slate-900 shadow-[2px_2px_0px_0px_rgba(15,23,42,0.9)]">
                                ${totalGeral} Coletadas
                            </span>
                        </div>
                        <!-- Vertical Bars Area: Deslocado mais à direita e distribuído sem corte -->
                        <div class="h-64 sm:h-72 md:h-80 w-full flex items-end justify-between sm:justify-around pl-6 sm:pl-10 md:pl-12 pr-4 sm:pr-8 md:pr-10 pt-6 pb-2 gap-2 sm:gap-3 md:gap-4">
                            ${categoriasBarras.map(cat => {
                                let hPx = 0;
                                if (cat.total > 0) {
                                    hPx = Math.round(36 + (cat.total / maxBarraValor) * 174);
                                } else {
                                    hPx = 18;
                                }
                                return `
                                <div class="flex-1 max-w-[95px] flex flex-col items-center group cursor-pointer" onclick="carregarDados('${cat.id}')" title="${cat.rotulo}: ${cat.total} oportunidades (Clique para abrir)">
                                    <span class="text-sm sm:text-base md:text-lg font-black text-slate-900 mb-2 tracking-tight group-hover:scale-110 transition-transform">${cat.total}</span>
                                    <div class="w-7 sm:w-8 md:w-8.5 ${cat.corClass} rounded-full border-2 border-slate-900 shadow-[2px_2px_0px_0px_rgba(15,23,42,0.9)] transition-all duration-200 group-hover:scale-105 group-hover:shadow-[3px_3px_0px_0px_rgba(15,23,42,1)]" style="height: ${hPx}px;"></div>
                                    <div class="w-7 h-7 sm:w-8 sm:h-8 rounded-full border-2 border-slate-900 flex items-center justify-center bg-white mt-2.5 shadow-[1px_1px_0px_0px_rgba(15,23,42,0.8)] group-hover:bg-slate-50 transition-colors">
                                        ${cat.svg}
                                    </div>
                                    <span class="text-xs sm:text-sm font-black text-slate-800 mt-2 text-center truncate max-w-full leading-tight">${cat.rotulo}</span>
                                </div>`;
                            }).join('')}
                        </div>
                    </div>
                </section>
                <!-- END: MiddleChartsSection -->

                <!-- BEGIN: FilterTabs -->
                <nav class="flex flex-wrap items-center gap-2.5 pt-1" data-purpose="tab-filters">
                    <button class="px-4 sm:px-5 py-2.5 bg-slate-900 text-white rounded-xl text-xs sm:text-sm md:text-base font-extrabold flex items-center space-x-2 border-2 border-slate-900 shadow-sm transition hover:bg-slate-800 cursor-pointer ativo" type="button" data-aba="todos" onclick="alternarAbaPrazos('todos', this)">
                        <svg class="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M9 4.5v15m6-15v15m-10.5 0h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                        <span>Visão Lado a Lado</span>
                    </button>
                    <button class="px-4 sm:px-5 py-2.5 bg-white text-slate-800 rounded-xl text-xs sm:text-sm md:text-base font-extrabold flex items-center space-x-2 border-2 border-slate-900 hover:bg-slate-50 transition cursor-pointer" type="button" data-aba="abertos" onclick="alternarAbaPrazos('abertos', this)">
                        <svg class="w-4 h-4 sm:w-5 sm:h-5 text-slate-700" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M4.5 12.75l6 6 9-13.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                        <span>Todos Abertos (${editaisAbertos.length})</span>
                    </button>
                    <button class="px-4 sm:px-5 py-2.5 bg-white text-slate-800 rounded-xl text-xs sm:text-sm md:text-base font-extrabold flex items-center space-x-2 border-2 border-slate-900 hover:bg-slate-50 transition cursor-pointer" type="button" data-aba="proximos" onclick="alternarAbaPrazos('proximos', this)">
                        <svg class="w-4 h-4 sm:w-5 sm:h-5 text-slate-700" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                        <span>Vencendo em Breve (${retaFinal || proximos.length})</span>
                    </button>
                    <button class="px-4 sm:px-5 py-2.5 bg-white text-slate-800 rounded-xl text-xs sm:text-sm md:text-base font-extrabold flex items-center space-x-2 border-2 border-slate-900 hover:bg-slate-50 transition cursor-pointer" type="button" data-aba="encerrados" onclick="alternarAbaPrazos('encerrados', this)">
                        <svg class="w-4 h-4 sm:w-5 sm:h-5 text-slate-700" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0l-3-3m3 3l3-3M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                        <span>Encerrados (${vencidosLista.length})</span>
                    </button>
                </nav>
                <!-- END: FilterTabs -->

                <!-- Horizontal divider line -->
                <div class="border-t border-slate-200 -mx-4 sm:-mx-6 md:-mx-8"></div>

                <!-- BEGIN: SideBySideNoticeColumns -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-8 pt-1" data-purpose="columns-container" id="dash-prazos-listas-grid">
                    <!-- COLUMN 1: Editais Abertos -->
                    <section class="space-y-4" data-purpose="open-notices-column" id="col-prazos-proximos">
                        <div class="flex items-center space-x-2.5 pb-1.5 border-b border-slate-200">
                            <span class="w-3 h-3 rounded-full bg-emerald-500 ring-4 ring-emerald-200"></span>
                            <h3 class="font-black text-base sm:text-lg md:text-xl text-slate-900 tracking-tight" id="dash-titulo-col-abertos">Editais Abertos <span class="font-bold text-slate-500 text-sm sm:text-base">(${editaisAbertos.length})</span></h3>
                        </div>
                        <div class="space-y-4" id="dash-lista-abertos-container">
                            ${editaisAbertos.length ? editaisAbertos.map(e => {
                                const info = sanitizarItemEdital(e.titulo);
                                const diasRestantes = calcularDiasAteData(e.data);
                                const isRetaFinal = diasRestantes !== null && diasRestantes >= 0 && diasRestantes <= 7;
                                const isEstagio = /estágio|ciee|prae|bolsa/i.test(e.titulo || '');
                                const badgeCor = isRetaFinal ? 'bg-red-500' : (isEstagio ? 'bg-teal-600' : 'bg-emerald-500');
                                const svgIcone = isRetaFinal
                                    ? `<svg class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" stroke-linecap="round" stroke-linejoin="round"></path></svg>`
                                    : (isEstagio
                                        ? `<svg class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M4.26 10.147L12 5.25l7.74 4.897M4.26 10.147l7.74 4.897 7.74-4.897M4.26 10.147v4.603a7.5 7.5 0 0015.48 0v-4.603" stroke-linecap="round" stroke-linejoin="round"></path></svg>`
                                        : `<svg class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"></path></svg>`);
                                let badgeRetaFinal = '';
                                if (isRetaFinal) {
                                    const txtBadge = diasRestantes === 0 ? 'Vence HOJE!' : (diasRestantes === 1 ? 'Vence amanhã!' : `Vence em ${diasRestantes} dias`);
                                    badgeRetaFinal = `
                                        <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded text-xs font-black bg-amber-500 text-white tracking-tight border border-amber-600 shadow-sm ml-2">
                                            <svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                                            <span>${txtBadge}</span>
                                        </span>`;
                                }
                                return `
                                <article class="flex items-start space-x-3.5 group cursor-pointer" data-edital-tipo="aberto" data-reta-final="${isRetaFinal ? 'true' : 'false'}" onclick="irParaEdital('${escaparHTML(e.link || '')}', '${escaparHTML(e.id || '')}')" title="${escaparHTML(info.tituloLimpo)}">
                                    <div class="w-9 h-9 sm:w-10 sm:h-10 rounded-full ${badgeCor} text-white flex items-center justify-center shrink-0 border-2 border-slate-900 shadow-sm mt-0.5 group-hover:scale-105 transition-transform">
                                        ${svgIcone}
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <h4 class="text-sm sm:text-[15px] md:text-base font-black text-slate-900 leading-snug group-hover:text-blue-600 transition truncate">
                                            ${escaparHTML(info.tituloLimpo)}
                                        </h4>
                                        <div class="flex items-center space-x-2 mt-1">
                                            <span class="text-xs sm:text-sm font-semibold text-slate-500">Até ${escaparHTML(e.data)}</span>
                                            ${badgeRetaFinal}
                                        </div>
                                    </div>
                                </article>`;
                            }).join('') : `
                                <div class="p-5 rounded-xl border-2 border-dashed border-slate-300 text-center">
                                    <p class="text-sm font-bold text-slate-600">Nenhum edital com inscrição aberta no momento.</p>
                                </div>
                            `}
                            <div id="dash-msg-sem-reta-final" style="display: none;" class="p-5 rounded-xl border-2 border-dashed border-slate-300 text-center">
                                <p class="text-sm font-bold text-slate-600">Nenhum edital vencendo nos próximos 7 dias.</p>
                            </div>
                        </div>
                    </section>

                    <!-- COLUMN 2: Editais Vencidos -->
                    <section class="space-y-4" data-purpose="closed-notices-column" id="col-prazos-encerrados">
                        <div class="flex items-center space-x-2.5 pb-1.5 border-b border-slate-200">
                            <span class="w-3 h-3 rounded-full bg-red-500 ring-4 ring-red-200"></span>
                            <h3 class="font-black text-base sm:text-lg md:text-xl text-slate-900 tracking-tight">Editais Vencidos <span class="font-bold text-slate-500 text-sm sm:text-base">(${vencidosLista.length})</span></h3>
                        </div>
                        ${vencidosLista.length ? `
                        <div class="space-y-4">
                            ${vencidosLista.slice(0, 4).map(e => {
                                const info = sanitizarItemEdital(e.titulo);
                                return `
                                <article class="flex items-start space-x-3.5 group cursor-pointer" onclick="irParaEdital('${escaparHTML(e.link || '')}', '${escaparHTML(e.id || '')}')" title="${escaparHTML(info.tituloLimpo)}">
                                    <div class="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-red-600 text-white flex items-center justify-center shrink-0 border-2 border-slate-900 shadow-sm mt-0.5 group-hover:scale-105 transition-transform">
                                        <svg class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <h4 class="text-sm sm:text-[15px] md:text-base font-black text-slate-900 leading-snug group-hover:text-red-700 transition truncate">
                                            ${escaparHTML(info.tituloLimpo)}
                                        </h4>
                                        <div class="text-xs sm:text-sm font-semibold text-slate-500 mt-1">
                                            Encerrado em ${escaparHTML(e.data)}
                                        </div>
                                    </div>
                                </article>`;
                            }).join('')}

                            ${vencidosLista.length > 4 ? `
                            <div id="lista-encerrados-extras" style="display: none;" class="space-y-4 pt-1">
                                ${vencidosLista.slice(4).map(e => {
                                    const info = sanitizarItemEdital(e.titulo);
                                    return `
                                    <article class="flex items-start space-x-3.5 group cursor-pointer" onclick="irParaEdital('${escaparHTML(e.link || '')}', '${escaparHTML(e.id || '')}')" title="${escaparHTML(info.tituloLimpo)}">
                                        <div class="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-red-600 text-white flex items-center justify-center shrink-0 border-2 border-slate-900 shadow-sm mt-0.5 group-hover:scale-105 transition-transform">
                                            <svg class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                                        </div>
                                        <div class="flex-1 min-w-0">
                                            <h4 class="text-sm sm:text-[15px] md:text-base font-black text-slate-900 leading-snug group-hover:text-red-700 transition truncate">
                                                ${escaparHTML(info.tituloLimpo)}
                                            </h4>
                                            <div class="text-xs sm:text-sm font-semibold text-slate-500 mt-1">
                                                Encerrado em ${escaparHTML(e.data)}
                                            </div>
                                        </div>
                                    </article>`;
                                }).join('')}
                            </div>
                            <div class="pt-2">
                                <button class="w-full py-3 px-4 rounded-xl border-2 border-dashed border-slate-400 hover:border-slate-800 text-xs sm:text-sm md:text-base font-black text-slate-800 hover:text-slate-950 flex items-center justify-center space-x-2 transition bg-slate-50 hover:bg-slate-100 cursor-pointer" type="button" data-texto-expandir="Mostrar mais ${vencidosLista.length - 4} editais encerrados" onclick="alternarListaEncerrados(this)">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M19.5 8.25l-7.5 7.5-7.5-7.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                                    <span>Mostrar mais ${vencidosLista.length - 4} editais encerrados</span>
                                </button>
                            </div>` : ''}
                        </div>` : `
                            <p class="text-sm font-bold text-slate-500 py-3">Nenhum edital encerrado recentemente.</p>
                        `}
                    </section>
                </div>
                <!-- END: SideBySideNoticeColumns -->

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

async function carregarPortalUsuario() {
    tipoAtual = 'perfil';
    alternarExibicaoFiltroVigentes(false);
    // Fecha a sidebar lateral de filtros para evitar sobreposição e redundância visual
    if (typeof fecharSidebarPerfil === 'function') {
        fecharSidebarPerfil();
    }

    const container = document.getElementById('container-vagas');
    const antigo = document.getElementById('bloco-paginacao');
    if (antigo) antigo.remove();

    destacarBotaoAtivo('btn-portal-usuario');

    if (!usuarioAtual) {
        container.style.display = 'block';
        container.innerHTML = `
            <div class="status-box" style="border-color: var(--color-orange); max-width: 600px; margin: 40px auto;">
                <div class="status-box-decor"></div>
                <h3 class="status-box-titulo"><i class="ph-bold ph-user-circle"></i> Portal do Estudante</h3>
                <p class="status-box-texto">Faça login ou crie sua conta para personalizar sua foto de perfil, curso de graduação, matrícula e notificações de editais.</p>
                <div style="margin-top: 20px; display: flex; gap: 14px; justify-content: center; flex-wrap: wrap;">
                    <button class="btn-hero-primary" onclick="abrirModalAuth('login')">
                        <i class="ph ph-sign-in"></i> Entrar na Minha Conta
                    </button>
                    <button class="btn-hero-secondary" onclick="abrirModalAuth('register')">
                        <i class="ph ph-user-plus"></i> Criar Conta Gratuita
                    </button>
                </div>
            </div>
        `;
        return;
    }

    container.style.display = 'block';

    const pref = usuarioAtual.preferencias || {};
    const cursosSalvos = pref.cursos || [];
    const areasSalvas = pref.areas || [];
    const emailNotif = pref.receber_emails !== false;
    const foto = usuarioAtual.foto_perfil || '';
    const cursoAtual = usuarioAtual.curso_principal || (cursosSalvos[0] || '');
    const campusAtual = usuarioAtual.campus || 'Campus Central (Mossoró)';
    const matriculaAtual = usuarioAtual.matricula || '';
    const bioAtual = usuarioAtual.bio || '';

    let avatarHTML = `<div class="portal-avatar-placeholder" id="portal-avatar-placeholder-preview"><i class="ph-bold ph-student"></i></div>`;
    if (foto) {
        if (foto.startsWith('preset:')) {
            const presetIcone = foto.replace('preset:', '');
            avatarHTML = `<div class="portal-avatar-placeholder" id="portal-avatar-placeholder-preview"><i class="ph-bold ${presetIcone}"></i></div>`;
        } else {
            avatarHTML = `<img src="${foto}" class="portal-avatar-img" id="portal-avatar-img-preview" alt="Foto de perfil">`;
        }
    }

    container.innerHTML = `
        <div class="portal-usuario-wrapper">
            <!-- CABEÇALHO DO PERFIL COM DADOS AMPLIADOS -->
            <div class="portal-header-card">
                <div class="portal-header-left" style="width: 100%;">
                    <div class="portal-avatar-tools">
                        <div class="portal-avatar-box" id="portal-avatar-preview-container" data-foto-data-url="${foto}">
                            ${avatarHTML}
                        </div>
                        <input type="file" id="portal-foto-input" accept="image/*" onchange="processarUploadFotoPortal(event)" style="display: none;">
                        <button type="button" class="btn-filtro-aluno" style="padding: 7px 16px; font-size: 0.9rem;" onclick="document.getElementById('portal-foto-input').click()" title="Escolha uma imagem do seu computador">
                            <i class="ph-bold ph-camera"></i> <span>Trocar Foto</span>
                        </button>
                        <div class="portal-avatar-presets-row" title="Ou escolha um avatar vetorial temático">
                            <button type="button" class="btn-avatar-preset ${foto === 'preset:ph-graduation-cap' ? 'ativo' : ''}" data-preset="ph-graduation-cap" onclick="selecionarAvatarPreset('ph-graduation-cap')" title="Estudante">
                                <i class="ph-bold ph-graduation-cap"></i>
                            </button>
                            <button type="button" class="btn-avatar-preset ${foto === 'preset:ph-laptop' ? 'ativo' : ''}" data-preset="ph-laptop" onclick="selecionarAvatarPreset('ph-laptop')" title="Tecnologia">
                                <i class="ph-bold ph-laptop"></i>
                            </button>
                            <button type="button" class="btn-avatar-preset ${foto === 'preset:ph-flask' ? 'ativo' : ''}" data-preset="ph-flask" onclick="selecionarAvatarPreset('ph-flask')" title="Pesquisa">
                                <i class="ph-bold ph-flask"></i>
                            </button>
                            <button type="button" class="btn-avatar-preset ${foto === 'preset:ph-scales' ? 'ativo' : ''}" data-preset="ph-scales" onclick="selecionarAvatarPreset('ph-scales')" title="Direito">
                                <i class="ph-bold ph-scales"></i>
                            </button>
                            <button type="button" class="btn-avatar-preset ${foto === 'preset:ph-heartbeat' ? 'ativo' : ''}" data-preset="ph-heartbeat" onclick="selecionarAvatarPreset('ph-heartbeat')" title="Saúde">
                                <i class="ph-bold ph-heartbeat"></i>
                            </button>
                            <button type="button" class="btn-avatar-preset ${foto === 'preset:ph-lightning' ? 'ativo' : ''}" data-preset="ph-lightning" onclick="selecionarAvatarPreset('ph-lightning')" title="Inovação">
                                <i class="ph-bold ph-lightning"></i>
                            </button>
                        </div>
                    </div>

                    <div class="portal-info-box">
                        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                            <h2 class="portal-user-nome">${escaparHTML(usuarioAtual.nome || 'Estudante')}</h2>
                            <span class="portal-user-tag-badge"><i class="ph-bold ph-shield-check"></i> Aluno EduScrap</span>
                        </div>
                        <div class="portal-user-meta">
                            <span class="portal-meta-item"><i class="ph-bold ph-envelope"></i> ${escaparHTML(usuarioAtual.email || '')}</span>
                            ${matriculaAtual ? `<span class="portal-meta-item"><i class="ph-bold ph-identification-card"></i> Matrícula: ${escaparHTML(matriculaAtual)}</span>` : ''}
                            ${cursoAtual ? `<span class="portal-meta-item"><i class="ph-bold ph-graduation-cap"></i> ${escaparHTML(cursoAtual)}</span>` : ''}
                            ${campusAtual ? `<span class="portal-meta-item"><i class="ph-bold ph-map-pin"></i> ${escaparHTML(campusAtual)}</span>` : ''}
                        </div>
                    </div>
                </div>
            </div>

            <!-- FORMULÁRIO DE DADOS E PREFERÊNCIAS -->
            <form id="form-portal-usuario" onsubmit="salvarPortalUsuario(event)" class="portal-corpo-card">
                <div>
                    <h3 class="portal-secao-titulo"><i class="ph-bold ph-identification-badge"></i> Dados Pessoais & Acadêmicos</h3>
                    <div class="portal-grid-duas-colunas">
                        <div class="form-group-memphis">
                            <label class="label-memphis" for="portal-input-nome">Nome Completo:</label>
                            <input type="text" id="portal-input-nome" class="input-memphis" value="${escaparHTML(usuarioAtual.nome || '')}" required>
                        </div>

                        <div class="form-group-memphis">
                            <label class="label-memphis" for="portal-input-matricula">Matrícula / Registro Acadêmico:</label>
                            <input type="text" id="portal-input-matricula" class="input-memphis" placeholder="Ex: 2024012345" value="${escaparHTML(matriculaAtual)}">
                        </div>

                        <div class="form-group-memphis">
                            <label class="label-memphis" for="portal-select-curso">Curso Principal de Graduação:</label>
                            <select id="portal-select-curso" class="input-memphis" style="cursor: pointer;">
                                <option value="">Selecione seu curso...</option>
                                ${TODOS_CURSOS.map(c => `<option value="${c}" ${c === cursoAtual ? 'selected' : ''}>${c}</option>`).join('')}
                            </select>
                        </div>

                        <div class="form-group-memphis">
                            <label class="label-memphis" for="portal-select-campus">Campus Universitário:</label>
                            <select id="portal-select-campus" class="input-memphis" style="cursor: pointer;">
                                <option value="Campus Central (Mossoró)" ${campusAtual === 'Campus Central (Mossoró)' ? 'selected' : ''}>Campus Central (Mossoró - UERN / UFERSA)</option>
                                <option value="Campus Pau dos Ferros" ${campusAtual === 'Campus Pau dos Ferros' ? 'selected' : ''}>Campus Pau dos Ferros</option>
                                <option value="Campus Assú" ${campusAtual === 'Campus Assú' ? 'selected' : ''}>Campus Assú</option>
                                <option value="Campus Patu" ${campusAtual === 'Campus Patu' ? 'selected' : ''}>Campus Patu</option>
                                <option value="Campus Caicó" ${campusAtual === 'Campus Caicó' ? 'selected' : ''}>Campus Caicó</option>
                                <option value="Campus Natal" ${campusAtual === 'Campus Natal' ? 'selected' : ''}>Campus Natal</option>
                                <option value="Outro" ${campusAtual === 'Outro' ? 'selected' : ''}>Outro Polo Universitário</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-group-memphis" style="margin-top: 16px;">
                        <label class="label-memphis" for="portal-input-bio">Apresentação / Interesses Acadêmicos (Bio):</label>
                        <textarea id="portal-input-bio" class="input-memphis" rows="2" placeholder="Conte brevemente sobre seus objetivos (ex: buscando primeiro estágio em desenvolvimento web ou bolsa de pesquisa)...">${escaparHTML(bioAtual)}</textarea>
                    </div>
                </div>

                <!-- PREFERÊNCIAS DE CURSOS PARA O FEED -->
                <div>
                    <h3 class="portal-secao-titulo"><i class="ph-bold ph-sparkle"></i> Cursos de Interesse para o Feed 'Para Você'</h3>
                    <p style="color: #64748B; font-size: 0.95rem; margin-top: -8px; margin-bottom: 14px;">Selecione os cursos abaixo para personalizar suas recomendações diárias de editais:</p>
                    <div class="chips-container" id="portal-chips-cursos">
                        ${TODOS_CURSOS.map(curso => {
                            const sel = cursosSalvos.includes(curso) ? 'chip-selecionado' : '';
                            return `<button type="button" class="chip-opcao ${sel}" data-valor="${curso}"><span class="chip-check"><i class="ph-bold ph-check"></i></span> ${curso}</button>`;
                        }).join('')}
                    </div>
                </div>

                <!-- ÁREAS DE INTERESSE -->
                <div>
                    <h3 class="portal-secao-titulo"><i class="ph-bold ph-bookmarks"></i> Áreas Temáticas</h3>
                    <div class="chips-container" id="portal-chips-areas">
                        ${TODAS_AREAS.map(area => {
                            const sel = areasSalvas.includes(area) ? 'chip-selecionado' : '';
                            return `<button type="button" class="chip-opcao ${sel}" data-valor="${area}"><span class="chip-check"><i class="ph-bold ph-check"></i></span> ${area}</button>`;
                        }).join('')}
                    </div>
                </div>

                <!-- NOTIFICAÇÕES -->
                <div>
                    <label class="checkbox-memphis-container">
                        <input type="checkbox" id="portal-receber-emails" ${emailNotif ? 'checked' : ''}>
                        <span class="custom-checkbox"></span>
                        <span class="label-texto">Receber alertas de editais críticos e prazos de encerramento por e-mail</span>
                    </label>
                </div>

                <div id="portal-feedback-msg" class="msg-sucesso-memphis" style="display: none;"></div>

                <div style="display: flex; gap: 14px; flex-wrap: wrap; align-items: center; justify-content: space-between; border-top: 2px dashed #CBD5E1; padding-top: 20px;">
                    <button type="submit" id="btn-salvar-portal" class="btn-submit-memphis btn-submit-primary" style="padding: 14px 28px; font-size: 1rem;">
                        <i class="ph-bold ph-floppy-disk"></i> Salvar Alterações
                    </button>

                    <button type="button" class="btn-submit-memphis btn-submit-danger" onclick="fazerLogout()">
                        <i class="ph-bold ph-sign-out"></i> Sair da Conta
                    </button>
                </div>
            </form>
        </div>
    `;

    // Ativa cliques dos chips do portal
    configurarChipsClickPortal();
}

function configurarChipsClickPortal() {
    document.querySelectorAll('#portal-chips-cursos .chip-opcao, #portal-chips-areas .chip-opcao').forEach(btn => {
        btn.onclick = function() {
            this.classList.toggle('chip-selecionado');
        };
    });
}

function processarUploadFotoPortal(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
        mostrarToast("Por favor selecione um arquivo de imagem válido.", "erro");
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            const canvas = document.createElement('canvas');
            const maxDim = 256;
            let w = img.width;
            let h = img.height;
            if (w > h) {
                if (w > maxDim) {
                    h = Math.round(h * (maxDim / w));
                    w = maxDim;
                }
            } else {
                if (h > maxDim) {
                    w = Math.round(w * (maxDim / h));
                    h = maxDim;
                }
            }
            canvas.width = w;
            canvas.height = h;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, w, h);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.85);

            const previewEl = document.getElementById('portal-avatar-preview-container');
            if (previewEl) {
                previewEl.innerHTML = `<img src="${dataUrl}" class="portal-avatar-img" id="portal-avatar-img-preview" alt="Foto de perfil">`;
                previewEl.dataset.fotoDataUrl = dataUrl;
            }
            document.querySelectorAll('.btn-avatar-preset').forEach(b => b.classList.remove('ativo'));
            mostrarToast("Foto carregada! Clique em 'Salvar Alterações' para salvar.", "sucesso");
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function selecionarAvatarPreset(iconeNome) {
    const previewContainer = document.getElementById('portal-avatar-preview-container');
    if (!previewContainer) return;

    previewContainer.innerHTML = `<div class="portal-avatar-placeholder" id="portal-avatar-placeholder-preview"><i class="ph-bold ${iconeNome}"></i></div>`;
    previewContainer.dataset.fotoDataUrl = `preset:${iconeNome}`;

    document.querySelectorAll('.btn-avatar-preset').forEach(b => b.classList.remove('ativo'));
    const btnClicado = document.querySelector(`.btn-avatar-preset[data-preset="${iconeNome}"]`);
    if (btnClicado) btnClicado.classList.add('ativo');

    mostrarToast("Avatar selecionado! Clique em 'Salvar Alterações' para confirmar.", "sucesso");
}

async function salvarPortalUsuario(e) {
    if (e && e.preventDefault) e.preventDefault();
    if (!usuarioAtual) return;

    const nome = document.getElementById('portal-input-nome')?.value.trim();
    const matricula = document.getElementById('portal-input-matricula')?.value.trim();
    const curso_principal = document.getElementById('portal-select-curso')?.value.trim();
    const campus = document.getElementById('portal-select-campus')?.value.trim();
    const bio = document.getElementById('portal-input-bio')?.value.trim();
    const receber_emails = document.getElementById('portal-receber-emails')?.checked;

    const cursos = obterChipsSelecionados('portal-chips-cursos');
    const areas = obterChipsSelecionados('portal-chips-areas');

    const previewContainer = document.getElementById('portal-avatar-preview-container');
    const foto_perfil = (previewContainer && previewContainer.dataset.fotoDataUrl)
        ? previewContainer.dataset.fotoDataUrl
        : (usuarioAtual.foto_perfil || '');

    const btnSubmit = document.getElementById('btn-salvar-portal');
    if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = `<i class="ph-bold ph-spinner animate-spin"></i> Salvando...`;
    }

    try {
        const resp = await fetch(`${API_URL}/auth/perfil`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                nome,
                matricula,
                curso_principal,
                campus,
                bio,
                foto_perfil,
                cursos,
                areas,
                receber_emails
            })
        });

        if (!resp.ok) {
            const errData = await resp.json().catch(() => ({}));
            throw new Error(errData.detail || "Erro ao salvar perfil");
        }

        const data = await resp.json();
        usuarioAtual = data.user;
        localStorage.setItem('eduscrap_user', JSON.stringify(data.user));
        atualizarInterfaceUsuario();

        mostrarToast("Perfil atualizado com sucesso! 🎉", "sucesso");

        const feedback = document.getElementById('portal-feedback-msg');
        if (feedback) {
            feedback.innerHTML = `<strong>Sucesso!</strong> Todas as alterações foram salvas.`;
            feedback.style.display = 'block';
            setTimeout(() => { feedback.style.display = 'none'; }, 4000);
        }

        // Recarrega o portal com os dados atualizados
        carregarPortalUsuario();

    } catch (err) {
        mostrarToast(`Erro: ${err.message}`, "erro");
    } finally {
        if (btnSubmit) {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = `<i class="ph-bold ph-floppy-disk"></i> Salvar Alterações`;
        }
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