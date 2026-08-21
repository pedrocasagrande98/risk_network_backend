from abc import ABC, abstractmethod
import time
import requests
from .models import GeoEvent

class BaseEventProcessor(ABC):
    def __init__(self, event: GeoEvent):
        self.event = event

    @abstractmethod
    def process(self):
        """Processes the event and updates its status/data"""
        pass

class FloodEventProcessor(BaseEventProcessor):
    WTH_URL = "http://127.0.0.1:8001/api/v1/flood"
    OSMNX_URL = "http://127.0.0.1:8002/api/v1/streets"

    def process(self):
        event_id = self.event.id
        event = self.event
        print(f"[FloodEventProcessor] Iniciando evento {event_id} na coord ({event.latitude}, {event.longitude})")
        
        # Define a cota com base na severidade
        cota_map = {
            'Baixa': 0.5,
            'Media': 1.0,
            'Critica': 2.0
        }
        cota_value = cota_map.get(event.severity, 1.0)
        
        print(f"[FloodEventProcessor] Severidade: {event.severity} -> Cota definida: {cota_value}m")
        
        # 1. Chamar WTH Motor
        resp_wth = requests.post(f"{self.WTH_URL}/calculate", json={
            "lat": event.latitude,
            "lon": event.longitude,
            "cota": cota_value
        })
        if resp_wth.status_code != 200:
            raise Exception("Falha ao comunicar com WTH Motor")
            
        wth_task_id = resp_wth.json()["task_id"]
        
        # Polling WTH Motor
        flood_geojson = None
        while True:
            time.sleep(2)
            status_resp = requests.get(f"{self.WTH_URL}/status/{wth_task_id}")
            data = status_resp.json()
            if data["status"] == "Concluído":
                if "error" in data.get("result", {}):
                    print(f"[FloodEventProcessor] Evento {event_id}: Sem mancha - {data['result']['error']}")
                    event.status = 'COMPLETED'
                    event.save(update_fields=['status'])
                    return "No flood risk found"
                flood_geojson = data["result"]["flood_polygon"]
                break
            elif data["status"] == "Falha":
                raise Exception(f"WTH Falhou: {data.get('error')}")
                
        # Salva mancha provisória
        event.flood_geojson = flood_geojson
        event.save(update_fields=['flood_geojson'])
        print(f"[FloodEventProcessor] Mancha do evento {event_id} recebida com sucesso!")

        # 2. Chamar OSMNX
        resp_osmnx = requests.post(f"{self.OSMNX_URL}/extract", json=flood_geojson)
        if resp_osmnx.status_code != 200:
            raise Exception("Falha ao comunicar com OSMNX API")
            
        osmnx_task_id = resp_osmnx.json()["task_id"]
        
        # Polling OSMNX
        streets_geojson = None
        start_time = time.time()
        while True:
            time.sleep(2)
            # Simula TimeOut-vias se demorar mais que 5 minutos
            if time.time() - start_time > 300:
                print(f"[FloodEventProcessor] TimeOut-vias atingido para evento {event_id}")
                event.status = 'COMPLETED_PARTIAL' # Salva só a mancha
                event.save(update_fields=['status'])
                return "Timeout vias"

            status_resp = requests.get(f"{self.OSMNX_URL}/status/{osmnx_task_id}")
            data = status_resp.json()
            if data["status"] == "Concluído":
                streets_geojson = data["result"]["impacted_streets"]
                break
            elif data["status"] == "Falha":
                raise Exception(f"OSMNX Falhou: {data.get('error')}")

        event.streets_geojson = streets_geojson
        event.status = 'COMPLETED'
        event.save(update_fields=['streets_geojson', 'status'])
        
        print(f"[FloodEventProcessor] Evento {event_id} processado 100% com sucesso!")
        return f"Processed event {event_id}"

class DefaultEventProcessor(BaseEventProcessor):
    def process(self):
        # Para eventos que não são Inundação, apenas completamos sem IA
        print(f"[DefaultEventProcessor] Processando evento simples (Sem IA) do tipo '{self.event.type}' para o ID {self.event.id}")
        self.event.status = 'COMPLETED'
        self.event.save(update_fields=['status'])
        return f"Processed simple event {self.event.id}"

class EventProcessorFactory:
    @staticmethod
    def get_processor(event: GeoEvent) -> BaseEventProcessor:
        if event.type == 'Inundacao':
            return FloodEventProcessor(event)
        else:
            return DefaultEventProcessor(event)
