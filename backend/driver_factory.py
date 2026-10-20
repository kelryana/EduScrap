## backend/driver_factory.py
"""
Fábrica unificada de WebDrivers para Selenium no projeto EduScrap.
Permite que os scrapers rodem de forma transparente em:
- Linux / macOS / Windows / Docker (containers)
- Google Chrome / Chromium / Microsoft Edge / Brave / Firefox
Com auto-detecção do sistema operacional e fallback inteligente.
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
try:
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
except ImportError:
    EdgeChromiumDriverManager = None

logger = logging.getLogger(__name__)

# User-Agents padrão para evitar bloqueios
CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
FIREFOX_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
)

# Caminhos padrão conhecidos no Windows
WINDOWS_COMMON_PATHS = {
    "chrome": [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ],
    "edge": [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ],
    "brave": [
        os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ],
    "firefox": [
        os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe"),
    ],
}


def _rodando_em_container() -> bool:
    """Detecta se o código está sendo executado dentro de um container Docker/Podman."""
    return (
        Path("/.dockerenv").exists()
        or Path("/run/.containerenv").exists()
        or (Path("/proc/1/cgroup").exists() and "docker" in Path("/proc/1/cgroup").read_text(errors="ignore"))
    )


def localizar_executavel(navegador: str) -> Optional[str]:
    navegador = navegador.lower().strip()

    # 1. Variáveis de ambiente explícitas (suporta convenções comuns como CHROME_BIN)
    env_vars = {
        "chrome": ["CHROME_BINARY_PATH", "CHROME_BIN", "CHROMIUM_PATH"],
        "brave": ["BRAVE_PATH", "BRAVE_BIN"],
        "edge": ["EDGE_BINARY_PATH", "EDGE_BIN"],
        "firefox": ["FIREFOX_BINARY_PATH", "FIREFOX_BIN"],
    }
    for var_name in env_vars.get(navegador, []):
        valor = os.getenv(var_name)
        if valor and Path(valor).exists():
            return str(Path(valor).resolve())

    # 2. Busca no PATH via shutil.which
    comandos_busca = {
        "chrome": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"],
        "edge": ["msedge", "microsoft-edge", "edge"],
        "brave": ["brave-browser", "brave"],
        "firefox": ["firefox", "firefox-esr"],
    }
    for cmd in comandos_busca.get(navegador, [navegador]):
        encontrado = shutil.which(cmd)
        if encontrado:
            return encontrado

    # 3. Caminhos padrão no Windows
    if sys.platform == "win32" and navegador in WINDOWS_COMMON_PATHS:
        for caminho_str in WINDOWS_COMMON_PATHS[navegador]:
            if os.path.exists(caminho_str):
                return caminho_str

    # 4. Caminhos padrão no Linux / macOS
    unix_paths = {
        "chrome": [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ],
        "brave": [
            "/usr/bin/brave-browser",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ],
        "edge": [
            "/usr/bin/microsoft-edge",
            "/usr/bin/msedge",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ],
        "firefox": [
            "/usr/bin/firefox",
            "/usr/bin/firefox-esr",
            "/snap/bin/firefox",
            "/Applications/Firefox.app/Contents/MacOS/firefox",
        ],
    }
    for caminho_str in unix_paths.get(navegador, []):
        if os.path.exists(caminho_str):
            return caminho_str

    return None


def _aplicar_stealth_cdp(driver):
    """Aplica propriedades stealth anti-automação via Chrome DevTools Protocol."""
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['pt-BR', 'pt', 'en']
                    });
                """
            },
        )
    except Exception as e:
        logger.debug(f"Aviso ao aplicar stealth CDP: {e}")


def criar_driver_chrome(
    headless: bool = True,
    binary_path: Optional[str] = None,
    driver_path: Optional[str] = None,
) -> webdriver.Chrome:
    """Cria e configura uma instância do Google Chrome ou Chromium."""
    if not binary_path:
        binary_path = localizar_executavel("chrome")

    # Se não houver executável instalado (em qualquer SO), falha imediatamente sem baixar driver à toa
    if not binary_path:
        raise FileNotFoundError(
            "Executável do Chrome/Chromium não foi encontrado no sistema."
        )

    options = ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--user-agent={CHROME_USER_AGENT}")
    options.add_argument("--lang=pt-BR")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if binary_path:
        options.binary_location = binary_path

    # Resolução do ChromeDriver (prioriza caminho local / apt no Linux antes de baixar)
    caminho_driver = driver_path or os.getenv("CHROMEDRIVER_PATH", "")
    if caminho_driver and Path(caminho_driver).exists():
        service = ChromeService(caminho_driver)
    else:
        driver_no_path = shutil.which("chromedriver") or shutil.which("chromium-driver")
        if driver_no_path:
            service = ChromeService(driver_no_path)
        else:
            try:
                service = ChromeService(ChromeDriverManager().install())
            except Exception as err:
                logger.debug(f"ChromeDriverManager falhou ({err}), tentando Selenium Manager nativo...")
                service = ChromeService()

    driver = webdriver.Chrome(service=service, options=options)
    _aplicar_stealth_cdp(driver)
    return driver


def criar_driver_edge(
    headless: bool = True,
    binary_path: Optional[str] = None,
    driver_path: Optional[str] = None,
) -> webdriver.Edge:
    """Cria e configura uma instância do Microsoft Edge (Chromium)."""
    if not binary_path:
        binary_path = localizar_executavel("edge")

    if not binary_path:
        raise FileNotFoundError(
            "Executável do Microsoft Edge não foi encontrado no sistema."
        )

    options = EdgeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--user-agent={CHROME_USER_AGENT}")
    options.add_argument("--lang=pt-BR")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if binary_path:
        options.binary_location = binary_path

    caminho_driver = driver_path or os.getenv("EDGEDRIVER_PATH", "")
    if caminho_driver and Path(caminho_driver).exists():
        service = EdgeService(caminho_driver)
    else:
        driver_no_path = shutil.which("msedgedriver")
        if driver_no_path:
            service = EdgeService(driver_no_path)
        elif EdgeChromiumDriverManager:
            try:
                service = EdgeService(EdgeChromiumDriverManager().install())
            except Exception as err:
                logger.debug(f"EdgeChromiumDriverManager falhou ({err}), usando Selenium Manager nativo...")
                service = EdgeService()
        else:
            service = EdgeService()

    driver = webdriver.Edge(service=service, options=options)
    _aplicar_stealth_cdp(driver)
    return driver


def criar_driver_brave(
    headless: bool = True,
    driver_path: Optional[str] = None,
) -> webdriver.Chrome:
    """Cria e configura uma instância do Brave Browser (via Chrome driver)."""
    brave_bin = localizar_executavel("brave")
    if not brave_bin:
        raise FileNotFoundError("Executável do Brave não foi encontrado no sistema.")
    return criar_driver_chrome(headless=headless, binary_path=brave_bin, driver_path=driver_path)


def criar_driver_firefox(
    headless: bool = True,
    binary_path: Optional[str] = None,
    driver_path: Optional[str] = None,
) -> webdriver.Firefox:
    """Cria e configura uma instância do Mozilla Firefox."""
    if not binary_path:
        binary_path = localizar_executavel("firefox")

    if not binary_path:
        raise FileNotFoundError(
            "Executável do Firefox não foi encontrado no sistema."
        )

    options = FirefoxOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Hardening de segurança e anti-detecção Firefox
    options.set_preference("general.useragent.override", FIREFOX_USER_AGENT)
    options.set_preference("permissions.default.image", 2)  # Não carregar imagens para otimizar velocidade
    options.set_preference("media.peerconnection.enabled", False)
    options.set_preference("dom.serviceWorkers.enabled", False)
    options.set_preference("network.http.redirection-limit", 5)
    options.set_preference("security.fileuri.strict_origin_policy", True)

    if binary_path:
        options.binary_location = binary_path

    caminho_driver = driver_path or os.getenv("GECKODRIVER_PATH", "")
    if caminho_driver and Path(caminho_driver).exists():
        service = FirefoxService(caminho_driver)
    else:
        driver_no_path = shutil.which("geckodriver")
        if driver_no_path:
            service = FirefoxService(driver_no_path)
        else:
            try:
                service = FirefoxService(GeckoDriverManager().install())
            except Exception as err:
                logger.debug(f"GeckoDriverManager falhou ({err}), usando Selenium Manager nativo...")
                service = FirefoxService()

    return webdriver.Firefox(service=service, options=options)


def determinar_ordem_navegadores(preferencia: str = "auto") -> List[str]:
    """
    Retorna a lista ordenada de navegadores a tentar conforme SO e preferência.
    """
    preferencia = (preferencia or "auto").lower().strip()

    if sys.platform == "win32":
        # No Windows: Edge é nativo, Chrome e Brave são os mais comuns, Firefox secundário
        padrao = ["chrome", "edge", "brave", "firefox"]
    else:
        # No Linux / macOS: Firefox ou Chrome
        padrao = ["firefox", "chrome", "edge", "brave"]

    if preferencia in ("chrome", "google-chrome", "chromium"):
        return ["chrome", "edge", "brave", "firefox"]
    elif preferencia in ("firefox", "gecko"):
        return ["firefox", "chrome", "edge", "brave"]
    elif preferencia in ("edge", "msedge"):
        return ["edge", "chrome", "brave", "firefox"]
    elif preferencia == "brave":
        return ["brave", "chrome", "edge", "firefox"]
    else:
        return padrao


def obter_driver(
    preferencia: Optional[str] = None,
    headless: bool = True,
    timeout_pagina: int = 30,
    timeout_implicito: int = 10,
    fallback: bool = True,
) -> webdriver.Remote:
    """
    Inicializa e retorna um WebDriver com fallback automático.
    Se o navegador preferencial não estiver disponível, tenta os demais.
    """
    if not preferencia:
        preferencia = os.getenv("SELENIUM_BROWSER", "auto")

    ordem = determinar_ordem_navegadores(preferencia)
    erros = []

    construtores = {
        "chrome": lambda: criar_driver_chrome(headless=headless),
        "edge": lambda: criar_driver_edge(headless=headless),
        "brave": lambda: criar_driver_brave(headless=headless),
        "firefox": lambda: criar_driver_firefox(headless=headless),
    }

    # Se fallback for False, tenta apenas o primeiro da lista
    alvos = ordem if fallback else ordem[:1]

    for nav in alvos:
        construtor = construtores.get(nav)
        if not construtor:
            continue

        try:
            logger.info(f"Tentando inicializar navegador: '{nav}' (headless={headless})...")
            driver = construtor()
            driver.set_page_load_timeout(timeout_pagina)
            driver.implicitly_wait(timeout_implicito)
            logger.info(f"✅ Navegador '{nav}' inicializado com sucesso!")
            return driver
        except Exception as e:
            msg_erro = f"Falha ao iniciar {nav}: {e}"
            logger.warning(f"⚠️ {msg_erro}")
            erros.append((nav, str(e)))

    # Se chegou aqui, nenhum navegador pôde ser inicializado
    detalhes = "\n".join([f" - {n}: {err}" for n, err in erros])
    if _rodando_em_container():
        mensagem = (
            f"❌ Erro no Docker: O container atual não possui o Chromium instalado (imagem antiga em cache).\n"
            f"Navegadores testados: {', '.join([n for n, _ in erros])}.\n"
            f"Detalhes dos erros:\n{detalhes}\n\n"
            f"👉 Como resolver:\n"
            f"   Execute na sua máquina host (fora do container):\n"
            f"   docker compose build --no-cache backend scraper-runner\n"
            f"   docker compose up -d"
        )
    else:
        mensagem = (
            f"❌ Não foi possível inicializar nenhum navegador Selenium.\n"
            f"Navegadores testados: {', '.join([n for n, _ in erros])}.\n"
            f"Detalhes dos erros:\n{detalhes}\n\n"
            f"Dica de solução:\n"
            f"- Se estiver no Windows: Instale o Google Chrome ou certifique-se que o Microsoft Edge está habilitado.\n"
            f"- Se estiver no Linux nativo: Instale o Chromium (`sudo apt install chromium chromium-driver`) ou Firefox (`sudo apt install firefox`)."
        )
    raise RuntimeError(mensagem)
