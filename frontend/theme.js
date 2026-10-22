// frontend/theme.js - Controle de tema claro/escuro do EduScrap
// Carregado no <head> de index.html e login.html para aplicar o tema
// salvo antes da primeira pintura (evita "flash" de tema errado).

(function () {
    'use strict';

    const THEME_KEY = 'eduscrap_theme'; // 'dark' | 'light'

    function getPreferredTheme() {
        const salvo = localStorage.getItem(THEME_KEY);
        if (salvo === 'dark' || salvo === 'light') return salvo;
        // Sem preferência salva: segue o sistema operacional do usuário.
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    function isDark() {
        return document.documentElement.classList.contains('dark');
    }

    // Aplica a classe 'dark' no <html> (necessária para as regras
    // "html.dark" do style.css e para o darkMode:'class' do Tailwind).
    function applyTheme(theme, persist) {
        const root = document.documentElement;
        if (theme === 'dark') {
            root.classList.add('dark');
        } else {
            root.classList.remove('dark');
        }
        if (persist !== false) {
            localStorage.setItem(THEME_KEY, theme);
        }
        updateToggleUI();
        updateLogo(theme);
        // Avisa o dashboard (script.js) para recolorir elementos inline.
        window.dispatchEvent(new Event('themechange'));
    }

    function toggleTheme() {
        applyTheme(isDark() ? 'light' : 'dark');
    }

    // Troca a imagem da logo conforme o tema: logos com os atributos
    // data-logo-light / data-logo-dark usam assets/logo_temaescuro.png
    // no tema escuro, mantendo exatamente o mesmo tamanho/CSS da logo.
    function updateLogo(theme) {
        const dark = theme === 'dark';
        document.querySelectorAll('img[data-logo-dark]').forEach(function (img) {
            const srcDark = img.getAttribute('data-logo-dark');
            const srcLight = img.getAttribute('data-logo-light') || 'assets/logo.png';
            const alvo = dark ? srcDark : srcLight;
            if (img.getAttribute('src') !== alvo) img.setAttribute('src', alvo);
        });
    }

    // Atualiza ícone e texto do botão (lua/sol + "Escuro"/"Claro").
    function updateToggleUI() {
        const dark = isDark();
        document.querySelectorAll('.theme-toggle-icon, #theme-toggle-icon').forEach(function (icon) {
            icon.classList.toggle('ph-moon', !dark);
            icon.classList.toggle('ph-sun', dark);
        });
        document.querySelectorAll('.theme-toggle-text, #theme-toggle-text').forEach(function (text) {
            text.textContent = dark ? 'Claro' : 'Escuro';
        });
        document.querySelectorAll('.btn-theme-toggle, #btn-theme-toggle').forEach(function (btn) {
            btn.setAttribute('aria-pressed', dark ? 'true' : 'false');
        });
    }

    // Aplica imediatamente (o script roda no <head>, antes do body existir;
    // por isso updateToggleUI/updateLogo também são chamados no DOMContentLoaded).
    applyTheme(getPreferredTheme(), false);

    document.addEventListener('DOMContentLoaded', function () {
        updateToggleUI();
        updateLogo(isDark() ? 'dark' : 'light');
    });

    // Expõe para o onclick="toggleTheme()" e alternarTema() dos botões.
    window.toggleTheme = toggleTheme;
    window.alternarTema = toggleTheme;
    window.getTheme = function () { return isDark() ? 'dark' : 'light'; };
})();