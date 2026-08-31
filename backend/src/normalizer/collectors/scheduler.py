#src/collectors/scheduler.py

import schedule
import time
import logging
from datetime import datetime
from typing import Callable, List
import os
from src.normalizer.database import MongoDBHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, interval_hours: int = 6, fixed_time: str = "03:00"):
     
        self.interval_hours = interval_hours
        self.fixed_time = fixed_time
        self.tasks: List[Callable] = []
        self.is_running = False
        self.db_handler = None

    def add_task(self, task: Callable, name: str = "") -> None:

        self.tasks.append(task)
        logger.info(f"Tarefa adicionada: {name or task.__name__}")

    def _run_tasks(self) -> None:
        """Executa todas as tarefas registradas e atualiza status no MongoDB"""
        logger.info(f"Iniciando execução das tarefas - {datetime.now()}")

        # Atualiza status dos editais no MongoDB antes de executar tarefas
        try:
            if self.db_handler is None:
                self.db_handler = MongoDBHandler()
            self.db_handler.update_status()
            logger.info("Status dos editais atualizado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {str(e)}")

        for i, task in enumerate(self.tasks, 1):
            try:
                logger.info(f"Executando tarefa {i}/{len(self.tasks)}: {task.__name__}")
                task()
                logger.info(f"Tarefa {task.__name__} concluída com sucesso")
            except Exception as e:
                logger.error(f"Erro na tarefa {task.__name__}: {str(e)}")

        logger.info(f"Todas as tarefas concluídas - {datetime.now()}")

    def setup_schedule(self) -> None:
        """Configura o agendamento baseado no intervalo e horário fixo"""
        # Limpa agendamentos anteriores
        schedule.clear()

        # Agenda execução a cada N horas
        schedule.every(self.interval_hours).hours.do(self._run_tasks)

        # Agenda também para horário fixo de baixa demanda (03:00 AM por padrão)
        schedule.every().day.at(self.fixed_time).do(self._run_tasks)

        logger.info(f"Agendamento configurado: intervalo de {self.interval_hours} horas + horário fixo {self.fixed_time}")

    def run_once(self) -> None:

        logger.info("Execução única iniciada")
        self._run_tasks()

    def run_continuous(self) -> None:

        logger.info("Iniciando scheduler em modo contínuo...")
        self.setup_schedule()
        self.is_running = True

        # Executa uma vez imediatamente
        self._run_tasks()

        # Loop principal
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto

    def stop(self) -> None:

        self.is_running = False
        schedule.clear()
        logger.info("Scheduler parado")

    @staticmethod
    def get_interval_from_env() -> int:

        return int(os.getenv('SCRAPER_INTERVAL_HOURS', '6'))

# Exemplo de uso
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    def exemplo_coleta():
        print("Executando coleta de dados...")
        # Aqui chamaria os scrapers

    # Obtém horário fixo do environment ou usa padrão 03:00
    fixed_time = os.getenv('SCHEDULER_FIXED_TIME', '03:00')
    interval_hours = Scheduler.get_interval_from_env()

    scheduler = Scheduler(interval_hours=interval_hours, fixed_time=fixed_time)
    scheduler.add_task(exemplo_coleta, "Coleta Geral")

    # Para teste único:
    # scheduler.run_once()

    # Para produção (loop contínuo):
    # scheduler.run_continuous()
