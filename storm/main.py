from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from wind_engine import WindEngine

app = FastAPI(title="Risk Network Storm API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = WindEngine()

class WindRequest(BaseModel):
    latitude: float
    longitude: float
    date: str

@app.post("/api/wind/plot")
async def plot_wind(request: WindRequest):
    """
    Recebe lat, lon e date, recorta a janela no modelo de ventos
    e retorna o JSON para renderização pelo leaflet-velocity.
    """
    try:
        data = engine.get_wind_data(
            lat=request.latitude,
            lon=request.longitude,
            date_str=request.date,
            radius_km=500.0
        )
        return data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
