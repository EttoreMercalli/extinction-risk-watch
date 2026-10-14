"""
Parser per Clima e Biosfera (NOAA Mauna Loa CO2 & NSIDC Ghiacci Artici).
Estrae:
- Formato Tabella: serie storica di concentrazione CO2 (ppm) ed estensione ghiaccio artico (milioni di km²)
- Formato Testo: bollettini climatici e superamento soglie critiche (Tipping Points)
"""

import csv
import io
from datetime import datetime
from typing import List, Tuple
import requests

from src.parsers.models import CategoryPayload, IndicatorSummary, TimeSeriesRecord, NewsItem

NOAA_CO2_URL = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_daily_mlo.txt"
NSIDC_ICE_URL = "https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v4.0.csv"

def fetch_and_parse_climate(timeout_sec: float = 20.0) -> CategoryPayload:
    """Scarica e converte i dati di CO2 e ghiacci artici."""
    headers = {"User-Agent": "Mozilla/5.0"}

    # 1. Parsing NOAA Mauna Loa CO2
    co2_resp = requests.get(NOAA_CO2_URL, headers=headers, timeout=timeout_sec)
    co2_resp.raise_for_status()

    co2_series: List[TimeSeriesRecord] = []
    for line in co2_resp.text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 5:
            try:
                year, month, day, _, ppm = parts[0], parts[1], parts[2], parts[3], parts[4]
                ppm_val = float(ppm)
                if ppm_val <= 0:  # Giorni senza misurazione valida
                    continue
                iso_date = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
                co2_series.append(TimeSeriesRecord(date=iso_date, value=ppm_val))
            except (ValueError, IndexError):
                continue

    if not co2_series:
        raise ValueError("Nessun dato valido estratto da NOAA CO2.")

    curr_co2 = co2_series[-1]
    co2_vals = [r.value for r in co2_series]
    min_co2 = min(co2_vals)
    max_co2 = max(co2_vals)
    # Calcolo percentile storico complessivo per CO2 (siamo sui massimi storici dell'Olocene)
    pct_co2 = sum(1 for v in co2_vals if v <= curr_co2.value) / len(co2_vals)

    co2_indicator = IndicatorSummary(
        metric_id="co2_mauna_loa",
        name="Concentrazione Atmosferica CO2 (Mauna Loa)",
        unit="ppm",
        current_value=curr_co2.value,
        current_date=curr_co2.date,
        total_records=len(co2_series),
        min_value=min_co2,
        max_value=max_co2,
        mean_value=sum(co2_vals) / len(co2_vals),
        percentile_5y=pct_co2,
        sparkline=[r.value for r in co2_series[-30:]]
    )

    # 2. Parsing NSIDC Ghiacci Artici
    ice_resp = requests.get(NSIDC_ICE_URL, headers=headers, timeout=timeout_sec)
    ice_resp.raise_for_status()

    ice_reader = csv.reader(io.StringIO(ice_resp.text))
    # Salta le prime 2 righe di intestazione
    next(ice_reader, None)
    next(ice_reader, None)

    ice_series: List[TimeSeriesRecord] = []
    for row in ice_reader:
        if len(row) < 4:
            continue
        try:
            year, month, day, extent_str = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
            extent_val = float(extent_str)
            if extent_val <= 0:
                continue
            iso_date = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
            ice_series.append(TimeSeriesRecord(date=iso_date, value=extent_val))
        except (ValueError, IndexError):
            continue

    if not ice_series:
        raise ValueError("Nessun dato valido estratto da NSIDC Sea Ice.")

    curr_ice = ice_series[-1]
    ice_vals = [r.value for r in ice_series]
    min_ice = min(ice_vals)
    max_ice = max(ice_vals)

    # Per il ghiaccio artico, meno ghiaccio c'è più alto è il rischio:
    # Quindi percentile di rischio = frazione di giorni storici con PIÙ ghiaccio rispetto a oggi
    risk_pct_ice = sum(1 for v in ice_vals if v >= curr_ice.value) / len(ice_vals)

    ice_indicator = IndicatorSummary(
        metric_id="arctic_sea_ice",
        name="Estensione Calotta Glaciale Artica",
        unit="milioni kmq",
        current_value=curr_ice.value,
        current_date=curr_ice.date,
        total_records=len(ice_series),
        min_value=min_ice,
        max_value=max_ice,
        mean_value=sum(ice_vals) / len(ice_vals),
        percentile_5y=risk_pct_ice,
        sparkline=[r.value for r in ice_series[-30:]]
    )

    # Notizie / Aggiornamenti testuali per la UI
    news_items = [
        NewsItem(
            title=f"Concentrazione CO2 a quota {curr_co2.value:.1f} ppm a Mauna Loa",
            date=curr_co2.date,
            source="NOAA Global Monitoring Laboratory",
            url="https://gml.noaa.gov/ccgg/trends/",
            summary=f"L'osservatorio di Mauna Loa registra {curr_co2.value:.2f} ppm. La concentrazione di anidride carbonica atmosferica resta vicina ai massimi storici dell'era umana, esercitando una costante pressione climatica globale.",
            category="Clima e Ambiente",
            severity=3 if curr_co2.value > 420 else 2,
            tags=["CO2", "Clima", "Effetto Serra", "Keeling Curve"]
        ),
        NewsItem(
            title=f"Estensione ghiaccio marino artico: {curr_ice.value:.2f} milioni di kmq",
            date=curr_ice.date,
            source="National Snow and Ice Data Center (NSIDC)",
            url="https://nsidc.org/arcticseaicenews/",
            summary=f"La copertura glaciale nell'emisfero settentrionale si attesta a {curr_ice.value:.2f} milioni di kmq. Il monitoraggio satellitare traccia i minimi stagionali e l'avanzamento verso il tipping point dell'Artico privo di ghiacci estivi.",
            category="Clima e Ambiente",
            severity=3 if curr_ice.value < 5.0 else 2,
            tags=["Ghiacci", "Artico", "Tipping Point", "Criosfera"]
        )
    ]

    return CategoryPayload(
        category_id="climate_biosphere",
        category_name="Clima e Ambiente",
        indicators={
            "co2": co2_indicator,
            "sea_ice": ice_indicator
        },
        time_series={
            "co2_chart": co2_series[-365:],        # Ultimo anno di dati giornalieri CO2
            "sea_ice_chart": ice_series[-365:]     # Ultimo anno di dati giornalieri ghiaccio
        },
        news_items=news_items
    )
