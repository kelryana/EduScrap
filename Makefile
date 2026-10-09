.PHONY: run test scrape setup help

help:
	@echo "Comandos disponíveis para o EduScrap:"
	@echo "  make run     - Inicia todo o projeto (Backend, Frontend e MongoDB) com um comando"
	@echo "  make test    - Executa os testes automatizados com pytest"
	@echo "  make scrape  - Executa o web scraping de notícias e editais"
	@echo "  make setup   - Configura índices e coleções no MongoDB"

run:
	./start.sh

test:
	./venv/bin/pytest tests/

scrape:
	./venv/bin/python run_scrapers.py $(fontes)

setup:
	./venv/bin/python backend/database_setup.py

