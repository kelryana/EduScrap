##backend/config.py

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


load_dotenv(BASE_DIR / ".env")


class Settings:
   
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "hub_estudantes")

   
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    FLASK_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_ENV: str = os.getenv("FLASK_ENV", "production")


    API_KEY: str = os.getenv("API_KEY", "")

    CHROMEDRIVER_PATH: str = os.getenv("CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver")
    GECKODRIVER_PATH: str = os.getenv("GECKODRIVER_PATH", "")  
    CIEE_CIDADE: str = os.getenv("CIEE_CIDADE", "Mossoro")
    CIEE_URL: str = os.getenv("CIEE_URL", "https://portal.ciee.org.br/")

    PATTERNS_PATH: str = os.getenv("PATTERNS_PATH", str(BASE_DIR / "config" / "patterns.json"))
    COURSE_MAPPING_PATH: str = os.getenv(
        "COURSE_MAPPING_PATH", str(BASE_DIR / "config" / "course_mapping.json")
    )
    LOG_DIR: str = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
