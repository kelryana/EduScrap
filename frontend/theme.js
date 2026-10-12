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
        // Avisa o dashboard (script.js) para recolorir elementos inline.
        window.dispatchEvent(new Event('themechange'));
    }

    function toggleTheme() {
        applyTheme(isDark() ? 'light' : 'dark');
    }

    // Atualiza ícone e texto do botão (lua/sol + "Escuro"/"Claro").
    function updateToggleUI() {
        const icon = document.getElementById('theme-toggle-icon');
        const text = document.getElementById('theme-toggle-text');
        const btn = document.getElementById('btn-theme-toggle');
        const dark = isDark();
        if (icon) {
            icon.classList.toggle('ph-moon', !dark);
            icon.classList.toggle('ph-sun', dark);
        }
        if (text) text.textContent = dark ? 'Claro' : 'Escuro';
        if (btn) btn.setAttribute('aria-pressed', dark ? 'true' : 'false');
    }

    // Aplica imediatamente (o script roda no <head>, antes do body existir;
    // por isso updateToggleUI também é chamado no DOMContentLoaded).
    applyTheme(getPreferredTheme(), false);

    document.addEventListener('DOMContentLoaded', updateToggleUI);

    // Expõe para o onclick="toggleTheme()" dos botões.
    window.toggleTheme = toggleTheme;
    window.getTheme = function () { return isDark() ? 'dark' : 'light'; };
})();
