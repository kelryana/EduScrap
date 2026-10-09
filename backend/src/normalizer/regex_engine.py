#src/normalizer/regex_engine.py 

import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegexEngine:
    def __init__(self, patterns_path: Optional[str] = None):
       
        self.patterns = self._load_default_patterns()

        if patterns_path:
            custom_patterns = self._load_custom_patterns(patterns_path)
            self.patterns.update(custom_patterns)

        # Compila os padrões para melhor performance
        self._compiled_patterns = {}
        self._compile_all()

    def _load_default_patterns(self) -> Dict:
        """Carrega padrões padrão do sistema"""
        return {
            'dates': {
                'br_full': r'\d{1,2}\s+de\s+(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d{4}',
                'br_numeric': r'\d{1,2}/\d{1,2}/\d{4}',
                'iso': r'\d{4}-\d{2}-\d{2}'
            },
            'edital': {
                'number': r'Edital\s+n[ºo]?\s+\d+/\d+',
                'title_captured': r'"([^"]*)"',
                'title_single_quotes': r"'([^']*)'"
            },
            'values': {
                'currency': r'R\$\s*[\d,.]+',
                'number': r'\d+[.,]\d+'
            },
            'status': {
                'open_keywords': ['inscrições abertas', 'período de inscrição', 'prazo', 'vagas abertas'],
                'closed_keywords': ['encerrado', 'prazo encerrado', 'inscrições encerradas', 'vagas preenchidas']
            }
        }

    def _load_custom_patterns(self, path: str) -> Dict:
        """Carrega padrões personalizados de arquivo JSON"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
            logger.info(f"Padrões personalizados carregados de {path}")
            return patterns
        except Exception as e:
            logger.error(f"Erro ao carregar padrões de {path}: {str(e)}")
            return {}

    def _compile_all(self) -> None:
        """Compila todos os padrões regex para performance"""
        self._compiled_patterns = {}

        for category, patterns in self.patterns.items():
            self._compiled_patterns[category] = {}
            for name, pattern in patterns.items():
                if isinstance(pattern, str):
                    try:
                        self._compiled_patterns[category][name] = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    except re.error as e:
                        logger.error(f"Erro ao compilar padrão {category}.{name}: {str(e)}")

    def extract_dates(self, text: str) -> List[str]:

        dates = []
        date_patterns = self._compiled_patterns.get('dates', {})

        for name, pattern in date_patterns.items():
            matches = pattern.findall(text)
            if matches:  # Check if matches is not empty before accessing first element
                if isinstance(matches[0], str):
                    dates.extend(matches)
                else:
                    # Handle tuple results (groups)
                    dates.extend([match[0] if isinstance(match, tuple) else match for match in matches])

        logger.info(f"{len(dates)} datas extraídas")
        return list(set(dates))  # Remove duplicatas

    def extract_edital_number(self, text: str) -> Optional[str]:
     
        pattern = self._compiled_patterns.get('edital', {}).get('number')
        if pattern:
            match = pattern.search(text)
            if match:
                result = match.group(0)
                logger.info(f"Edital extraído: {result}")
                return result
        return None

    def extract_title(self, text: str) -> Optional[str]:
      
        edital_patterns = self._compiled_patterns.get('edital', {})

        # Tenta primeiro aspas duplas
        pattern = edital_patterns.get('title_captured')
        if pattern:
            match = pattern.search(text)
            if match:
                result = match.group(1)  # Grupo capturado
                logger.info(f"Título extraído: {result}")
                return result

        # Tenta aspas simples
        pattern = edital_patterns.get('title_single_quotes')
        if pattern:
            match = pattern.search(text)
            if match:
                result = match.group(1)  # Grupo capturado
                logger.info(f"Título extraído: {result}")
                return result

        return None

    def extract_currency_values(self, text: str) -> List[str]:
      
        pattern = self._compiled_patterns.get('values', {}).get('currency')
        if pattern:
            matches = pattern.findall(text)
            logger.info(f"{len(matches)} valores monetários extraídos")
            return matches
        return []

    def detect_status(self, text: str) -> str:
      
        text_lower = text.lower()
        
        # Verifica palavras-chave para status aberto
        open_keywords = self.patterns.get('status', {}).get('open_keywords', [])
        for keyword in open_keywords:
            if keyword.lower() in text_lower:
                logger.info(f"Status detectado: Aberto (encontrado '{keyword}')")
                return "Aberto"

        # Verifica palavras-chave para status fechado
        closed_keywords = self.patterns.get('status', {}).get('closed_keywords', [])
        for keyword in closed_keywords:
            if keyword.lower() in text_lower:
                logger.info(f"Status detectado: Encerrado (encontrado '{keyword}')")
                return "Encerrado"

        # Padrões dinâmicos (mais flexíveis)
        open_patterns = [
            r'(inscrições?|candidaturas?)\s+(abertas?|disponívei[sl])',
            r'(processo|seleção)\s+em\s+(andamento|aberto)',
            r'vagas?\s+disponívei[sl]',
            r'prazo\s+(em\s+aberto|disponível)'
        ]
        
        for pattern in open_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return "Aberto"

        closed_patterns = [
            r'(inscrições?|candidaturas?)\s+(encerradas?|finalizadas?|concluídas?)',
            r'prazo\s+(encerrado|finalizado|concluído)',
            r'vagas?\s+(preenchidas?|fechadas?)',
            r'(processo|seleção)\s+(encerrad[oa]|finalizad[oa]|concluíd[oa])'
        ]
        
        for pattern in closed_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return "Encerrado"

        logger.info("Status detectado: Indefinido")
        return "Indefinido"

    def extract_numbers(self, text: str) -> List[str]:
      
        pattern = self._compiled_patterns.get('values', {}).get('number')
        if pattern:
            matches = pattern.findall(text)
            logger.info(f"{len(matches)} números extraídos")
            return matches
        return []

    def extract_by_pattern(self, text: str, category: str, pattern_name: str) -> List[str]:
      
        pattern = self._compiled_patterns.get(category, {}).get(pattern_name)
        if pattern:
            matches = pattern.findall(text)
            return matches if matches else []
        return []