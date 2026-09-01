import json
from datetime import datetime, timezone
import numpy as np
import rioxarray
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

class WindEngine:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir

    def _get_tiff_path_for_date(self, date_str: str) -> str:
        """
        Dada uma data (YYYY-MM-DD), extrai o ano e o mês e monta o caminho 
        do arquivo COG esperado, ex: vento_brasil_2025-05.tif
        Faz fallback para o arquivo mais recente ou um padrão se não existir.
        """
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            year = dt.strftime("%Y")
            month = dt.strftime("%m")
        except ValueError:
            # Fallback seguro se vier em outro formato
            year = "2025"
            month = "01"

        filename = f"vento_brasil_{year}-{month}.tif"
        filepath = os.path.join(self.data_dir, filename)

        if not os.path.exists(filepath):
            # Fallback para um arquivo que sabemos que existe ou levanta erro 404
            fallback = os.path.join(self.data_dir, "vento_brasil_2025-10.tif")
            if os.path.exists(fallback):
                print(f"[Aviso] Arquivo {filename} não encontrado. Usando fallback {fallback}.")
                return fallback
            raise FileNotFoundError(f"Arquivo de vento para o mês {month}/{year} não foi encontrado.")

        return filepath

    def get_wind_data(self, lat: float, lon: float, date_str: str, radius_km: float = 500.0):
        """
        Identifica o COG do mês, recorta a janela e retorna o JSON Leaflet.
        """
        tiff_path = self._get_tiff_path_for_date(date_str)

        # Conversão aproximada de km para graus
        deg_radius = radius_km / 111.0
        min_lon = lon - deg_radius
        max_lon = lon + deg_radius
        min_lat = lat - deg_radius
        max_lat = lat + deg_radius

        print(f"Buscando dados no arquivo: {tiff_path}")
        rds = rioxarray.open_rasterio(tiff_path)

        if rds.y[0] > rds.y[-1]:
            y_slice = slice(max_lat, min_lat)
        else:
            y_slice = slice(min_lat, max_lat)

        rds_subset = rds.sel(x=slice(min_lon, max_lon), y=y_slice)

        u_da = rds_subset.sel(band=1).squeeze(drop=True)
        v_da = rds_subset.sel(band=2).squeeze(drop=True)

        lons = u_da.x.values
        lats = u_da.y.values

        if len(lons) == 0 or len(lats) == 0:
            raise ValueError("As coordenadas fornecidas estão fora da cobertura do arquivo TIFF.")

        nx = int(lons.size)
        ny = int(lats.size)

        lo1 = float(lons.min())
        lo2 = float(lons.max())
        la1 = float(lats.max())
        la2 = float(lats.min())

        dx = float(abs(lons[1] - lons[0])) if nx > 1 else 0.25
        dy = float(abs(lats[1] - lats[0])) if ny > 1 else 0.25

        u_vals = u_da.values
        v_vals = v_da.values

        # Garante top-bottom para o Y
        if lats[0] < lats[-1]:
            u_vals = u_vals[::-1, :]
            v_vals = v_vals[::-1, :]

        def build_band(values, param_number, param_name):
            clean = np.nan_to_num(values, nan=0.0)
            return {
                "header": {
                    "parameterUnit": "m.s-1",
                    "parameterNumber": param_number,
                    "parameterNumberName": param_name,
                    "parameterCategory": 2,
                    "la1": la1,
                    "la2": la2,
                    "lo1": lo1,
                    "lo2": lo2,
                    "nx": nx,
                    "ny": ny,
                    "dx": dx,
                    "dy": dy,
                    "refTime": f"{date_str} 00:00:00",
                    "forecastTime": 0,
                },
                "data": clean.astype(float).flatten().tolist(),
            }

        wind_json = [
            build_band(u_vals, 2, "U-component_of_wind"),
            build_band(v_vals, 3, "V-component_of_wind"),
        ]

        return wind_json
