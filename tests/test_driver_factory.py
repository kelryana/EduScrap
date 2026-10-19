# tests/test_driver_factory.py

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from driver_factory import (
    determinar_ordem_navegadores,
    localizar_executavel,
    obter_driver,
    CHROME_USER_AGENT,
    FIREFOX_USER_AGENT,
)


class TestDriverFactory:

    def test_determinar_ordem_linux_padrao(self):
        with patch("sys.platform", "linux"):
            ordem = determinar_ordem_navegadores("auto")
            assert ordem[0] == "firefox"
            assert "chrome" in ordem
            assert "edge" in ordem

    def test_determinar_ordem_windows_padrao(self):
        with patch("sys.platform", "win32"):
            ordem = determinar_ordem_navegadores("auto")
            assert ordem[0] == "chrome"
            assert ordem[1] == "edge"
            assert "firefox" in ordem

    def test_determinar_ordem_preferencia_explicita(self):
        ordem_chrome = determinar_ordem_navegadores("chrome")
        assert ordem_chrome[0] == "chrome"

        ordem_edge = determinar_ordem_navegadores("edge")
        assert ordem_edge[0] == "edge"

        ordem_firefox = determinar_ordem_navegadores("firefox")
        assert ordem_firefox[0] == "firefox"

        ordem_brave = determinar_ordem_navegadores("brave")
        assert ordem_brave[0] == "brave"

    def test_localizar_executavel_env_var(self, monkeypatch, tmp_path):
        fake_bin = tmp_path / "custom_chrome.exe"
        fake_bin.write_text("fake")
        monkeypatch.setenv("CHROME_BINARY_PATH", str(fake_bin))

        encontrado = localizar_executavel("chrome")
        assert encontrado == str(fake_bin)

    def test_localizar_executavel_shutil_which(self):
        with patch("shutil.which", return_value="/mock/bin/firefox"):
            encontrado = localizar_executavel("firefox")
            assert encontrado == "/mock/bin/firefox"

    @patch("driver_factory.criar_driver_chrome")
    def test_obter_driver_sucesso_primeira_tentativa(self, mock_chrome):
        mock_instance = MagicMock()
        mock_instance.name = "chrome"
        mock_chrome.return_value = mock_instance

        driver = obter_driver(preferencia="chrome", fallback=False)
        assert driver == mock_instance
        mock_instance.set_page_load_timeout.assert_called_with(30)
        mock_instance.implicitly_wait.assert_called_with(10)

    @patch("driver_factory.criar_driver_chrome", side_effect=Exception("Chrome não instalado"))
    @patch("driver_factory.criar_driver_edge")
    def test_obter_driver_fallback_para_edge(self, mock_edge, mock_chrome):
        mock_edge_instance = MagicMock()
        mock_edge_instance.name = "msedge"
        mock_edge.return_value = mock_edge_instance

        driver = obter_driver(preferencia="chrome", fallback=True)
        assert driver == mock_edge_instance
        mock_chrome.assert_called_once()
        mock_edge.assert_called_once()

    @patch("driver_factory.criar_driver_chrome", side_effect=Exception("Erro Chrome"))
    @patch("driver_factory.criar_driver_edge", side_effect=Exception("Erro Edge"))
    @patch("driver_factory.criar_driver_brave", side_effect=Exception("Erro Brave"))
    @patch("driver_factory.criar_driver_firefox", side_effect=Exception("Erro Firefox"))
    def test_obter_driver_todos_falham_lanca_runtime_error(
        self, mock_firefox, mock_brave, mock_edge, mock_chrome
    ):
        with pytest.raises(RuntimeError) as exc_info:
            obter_driver(preferencia="auto", fallback=True)

        assert "Não foi possível inicializar nenhum navegador Selenium" in str(exc_info.value)
        assert "Windows" in str(exc_info.value) or "Linux" in str(exc_info.value)

    @patch("scraper_ciee.obter_driver")
    def test_scraper_ciee_configurar_driver_sucesso(self, mock_obter):
        from scraper_ciee import ScraperCIEEHibrido
        mock_driver = MagicMock()
        mock_driver.name = "chrome"
        mock_obter.return_value = mock_driver

        scraper = ScraperCIEEHibrido(cidade="Mossoró")
        sucesso = scraper.configurar_driver()
        assert sucesso is True
        assert scraper.driver == mock_driver

    @patch("scraper_ciee.obter_driver", side_effect=RuntimeError("Nenhum navegador encontrado"))
    def test_scraper_ciee_configurar_driver_falha(self, mock_obter):
        from scraper_ciee import ScraperCIEEHibrido
        scraper = ScraperCIEEHibrido(cidade="Mossoró")
        sucesso = scraper.configurar_driver()
        assert sucesso is False
        assert scraper.driver is None

    @patch("driver_factory.obter_driver")
    def test_scraper_portal_uern_criar_navegador(self, mock_obter):
        from scraper_portal_uern import criar_navegador_headless
        mock_driver = MagicMock()
        mock_obter.return_value = mock_driver

        driver = criar_navegador_headless()
        assert driver == mock_driver
        mock_obter.assert_called_once()

