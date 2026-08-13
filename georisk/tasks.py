from celery import shared_task
import time

@shared_task
def process_new_geoevent(event_id):
    """
    Task de exemplo simulando o processamento assíncrono de um novo evento de risco.
    Na vida real, isso poderia enviar um email, gerar um relatório, etc.
    """
    print(f"[Worker] Iniciando processamento do evento de risco {event_id}...")
    
    # Simula um trabalho pesado que demoraria 5 segundos (travando a requisição web se fosse síncrono)
    time.sleep(5)
    
    print(f"[Worker] Evento {event_id} processado com sucesso! Notificações enviadas.")
    
    return f"Processed event {event_id}"
