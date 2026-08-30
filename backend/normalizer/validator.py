#src/normalizer/validator.py 

from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataValidator:
    def __init__(self):
        """Inicializa o validador"""
        self.today = datetime.now()

    def parse_date_string(self, date_str: str) -> Optional[datetime]:
     
        if not date_str:
            return None

        # Formatos brasileiros
        formats = [
            '%d/%m/%Y',           # 25/12/2024
            '%d-%m-%Y',           # 25-12-2024
            '%Y-%m-%d',           # 2024-12-25 (ISO)
            '%d de %B de %Y',     # 25 de dezembro de 2024
            '%d de %b de %Y',     # 25 de dez de 2024
        ]

        # Normaliza a string
        date_str = date_str.strip().lower()

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Tenta formato com mês por extenso em português
        meses = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
            'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
            'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
        }

        match = re.search(r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', date_str)
        if match:
            dia, mes_str, ano = match.groups()
            mes = meses.get(mes_str.lower())
            if mes:
                try:
                    return datetime(int(ano), mes, int(dia))
                except ValueError:
                    pass

        logger.warning(f"Não foi possível parsear a data: {date_str}")
        return None

    def validate_deadline(self, deadline_str: str) -> Dict[str, Any]:
     
        deadline = self.parse_date_string(deadline_str)

        if not deadline:
            return {
                'status': 'Indefinido',
                'dias_restantes': None,
                'data_limite': None,
                'valido': False
            }

        delta = deadline - self.today
        dias_restantes = delta.days

        if dias_restantes < 0:
            status = 'Encerrado'
            valido = False
        elif dias_restantes == 0:
            status = 'Encerra Hoje'
            valido = True
        elif dias_restantes <= 3:
            status = 'Urgente'
            valido = True
        else:
            status = 'Aberto'
            valido = True

        result = {
            'status': status,
            'dias_restantes': dias_restantes,
            'data_limite': deadline.strftime('%d/%m/%Y'),
            'valido': valido
        }

        logger.info(f"Validação de prazo: {status} ({dias_restantes} dias)")
        return result

    def validate_required_fields(self, data: Dict, required: List[str]) -> Dict[str, Any]:
       
        missing = []

        for field in required:
            if field not in data or not data[field]:
                missing.append(field)

        valido = len(missing) == 0

        result = {
            'valido': valido,
            'campos_faltantes': missing,
            'completo': f"{len(required) - len(missing)}/{len(required)}"
        }

        if missing:
            logger.warning(f"Campos faltantes: {missing}")
        else:
            logger.info("Todos os campos obrigatórios presentes")

        return result

    def validate_edital(self, edital_data: Dict) -> Dict[str, Any]:
      
        # Campos obrigatórios para editais
        required_fields = ['titulo', 'fonte', 'data_publicacao']

        # Valida campos obrigatórios
        fields_validation = self.validate_required_fields(
            edital_data,
            required_fields
        )

        # Valida prazo se houver data limite
        deadline_validation = {'status': 'N/A'}
        if edital_data.get('data_limite'):
            deadline_validation = self.validate_deadline(
                edital_data['data_limite']
            )

        # Validação geral
        is_valid = (
            fields_validation['valido'] and
            deadline_validation.get('valido', True)
        )

        return {
            'valido': is_valid,
            'campos': fields_validation,
            'prazo': deadline_validation,
            'timestamp': datetime.now().isoformat()
        }
