#tests/test_regex.py 

import pytest
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from normalizer.regex_engine import RegexEngine
from normalizer.validator import DataValidator

class TestRegexEngine:
    @pytest.fixture
    def engine(self):
        return RegexEngine()

    def test_extract_edital_number(self, engine):
        texto = "Publicado no Diário Oficial: Edital n° 025/2026"
        result = engine.extract_edital_number(texto)
        assert result is not None
        assert "025/2026" in result

    def test_extract_date_br_numeric(self, engine):
        texto = "Prazo final: 30/09/2026"
        dates = engine.extract_dates(texto)
        assert len(dates) > 0
        assert "30/09/2026" in dates or "30" in str(dates)

    def test_extract_date_br_full(self, engine):
        texto = "Inscrições até 15 de dezembro de 2026"
        dates = engine.extract_dates(texto)
        assert len(dates) > 0

    def test_detect_status_open(self, engine):
        texto = "Inscrições abertas para bolsa de pesquisa"
        status = engine.detect_status(texto)
        assert status == "Aberto"

    def test_detect_status_closed(self, engine):
        texto = "Processo encerrado, vagas preenchidas"
        status = engine.detect_status(texto)
        assert status == "Encerrado"

    def test_extract_currency(self, engine):
        texto = "Valor da bolsa: R$ 700,00 mensais"
        values = engine.extract_currency_values(texto)
        assert len(values) > 0
        assert "R$" in values[0]


class TestDataValidator:
    """Testes unitários para DataValidator"""

    @pytest.fixture
    def validator(self):
        return DataValidator()

    def test_parse_date_numeric(self, validator):
        result = validator.parse_date_string("25/12/2024")
        assert result is not None
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25

    def test_parse_date_full(self, validator):
        result = validator.parse_date_string("15 de março de 2026")
        assert result is not None
        assert result.year == 2026
        assert result.month == 3

    def test_validate_deadline_future(self, validator):
        # Data no futuro
        result = validator.validate_deadline("30/12/2026")
        assert result['status'] in ['Aberto', 'Urgente']
        assert result['valido'] == True

    def test_validate_deadline_past(self, validator):
        # Data no passado
        result = validator.validate_deadline("01/01/2020")
        assert result['status'] == 'Encerrado'
        assert result['valido'] == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
