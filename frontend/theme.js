// frontend/theme.js - Gerenciador de Tema (Modo Escuro / Claro) do EduScrap

(function() {
    // Executa imediatamente para evitar "flash" de tema claro (anti-FOUC)
    try {
        const temaSalvo = localStorage.getItem('eduscrap_theme');
        const prefereEscuro = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (temaSalvo === 'dark' || (!temaSalvo && prefereEscuro)) {
            document.documentElement.classList.add('dark');
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            document.documentElement.setAttribute('data-theme', 'light');
        }
    } catch (e) {
        console.warn('Erro ao inicializar tema no head:', e);
    }
})();

function obterTemaAtual() {
    return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
}

function aplicarTema(tema, salvar = true) {
    const isDark = (tema === 'dark');
    const root = document.documentElement;

    if (isDark) {
        root.classList.add('dark');
        root.setAttribute('data-theme', 'dark');
    } else {
        root.classList.remove('dark');
        root.setAttribute('data-theme', 'light');
    }

    if (salvar) {
        try {
            localStorage.setItem('eduscrap_theme', tema);
        } catch (e) {
            console.warn('Não foi possível salvar tema no localStorage:', e);
        }
    }

    atualizarBotoesTema(isDark);

    // Dispara evento para quaisquer ouvintes adicionais
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: tema, isDark } }));
}

function toggleTheme() {
    const temaAtual = obterTemaAtual();
    const novoTema = (temaAtual === 'dark') ? 'light' : 'dark';
    aplicarTema(novoTema, true);

    if (typeof mostrarToast === 'function') {
        mostrarToast(
            novoTema === 'dark' ? 'Modo Escuro ativado' : 'Modo Claro ativado',
            'info'
        );
    }
}

function atualizarBotoesTema(isDark) {
    const botoes = document.querySelectorAll('.btn-theme-toggle, #btn-theme-toggle');
    const icones = document.querySelectorAll('.theme-toggle-icon, #theme-toggle-icon');
    const textos = document.querySelectorAll('.theme-toggle-text, #theme-toggle-text');

    icones.forEach(icone => {
        if (isDark) {
            icone.className = 'ph-bold ph-sun theme-toggle-icon';
            icone.style.color = '#FACC15';
        } else {
            icone.className = 'ph-bold ph-moon theme-toggle-icon';
            icone.style.color = '';
        }
    });

    textos.forEach(texto => {
        texto.textContent = isDark ? 'Claro' : 'Escuro';
    });

    botoes.forEach(btn => {
        btn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
        btn.setAttribute('aria-label', isDark ? 'Mudar para Modo Claro' : 'Mudar para Modo Escuro');
        btn.setAttribute('title', isDark ? 'Mudar para Modo Claro' : 'Mudar para Modo Escuro');
    });
}

// Sincroniza os botões assim que o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    const isDark = obterTemaAtual() === 'dark';
    atualizarBotoesTema(isDark);

    // Se o usuário não tiver preferência explícita salva, responde às mudanças do sistema operacional
    try {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            const temaSalvo = localStorage.getItem('eduscrap_theme');
            if (!temaSalvo) {
                aplicarTema(e.matches ? 'dark' : 'light', false);
            }
        });
    } catch (e) {}
});
