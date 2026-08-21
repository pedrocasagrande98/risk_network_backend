from celery import shared_task
from .models import GeoEvent
from .processors import EventProcessorFactory

@shared_task
def process_new_geoevent(event_id):
    """
    Task Orquestradora que seleciona a estratégia correta baseada no tipo de evento.
    """
    try:
        event = GeoEvent.objects.get(id=event_id)
        print(f"[Orquestrador] Iniciando processamento do evento {event_id} ({event.type}) na coord ({event.latitude}, {event.longitude})")
        
        processor = EventProcessorFactory.get_processor(event)
        return processor.process()

    except Exception as e:
        print(f"[Orquestrador] ERRO fatal no evento {event_id}: {str(e)}")
        GeoEvent.objects.filter(id=event_id).update(status='ERROR')
        return str(e)
