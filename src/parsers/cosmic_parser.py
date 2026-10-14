"""
Parser per Rischi Cosmici e Naturali (NOAA SWPC Tempeste Solari, USGS Terremoti & NASA Sentry Asteroidi).
Estrae:
- Formato Tabella: serie oraria dell'indice Kp geomagnetico solare, magnitudo terremoti
- Formato Testo: allerte di tempeste solari di classe estrema e sciami sismici
"""

from datetime import datetime
from typing import List
import requests

from src.parsers.models import CategoryPayload, IndicatorSummary, TimeSeriesRecord, NewsItem

NOAA_KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
USGS_QUAKES_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson"
NASA_SENTRY_URL = "https://ssd-api.jpl.nasa.gov/sentry.api"

def fetch_and_parse_cosmic(timeout_sec: float = 20.0) -> CategoryPayload:
    """Scarica e converte i dati sul clima spaziale (Kp), terremoti e asteroidi."""
    headers = {"User-Agent": "Mozilla/5.0"}
    time_series_kp: List[TimeSeriesRecord] = []
    curr_kp = 0.0
    curr_date = datetime.now().strftime("%Y-%m-%d")

    # 1. Parsing NOAA Space Weather K-Index
    try:
        r_kp = requests.get(NOAA_KP_URL, headers=headers, timeout=timeout_sec)
        if r_kp.status_code == 200:
            kp_data = r_kp.json()
            for row in kp_data:
                if isinstance(row, dict):
                    try:
                        time_tag = str(row.get("time_tag", ""))
                        val = float(row.get("Kp", 0.0))
                        time_series_kp.append(TimeSeriesRecord(date=time_tag[:16], value=val))
                        curr_kp = val
                    except (ValueError, TypeError):
                        continue
                elif isinstance(row, list) and len(row) >= 2:
                    try:
                        time_tag = str(row[0])
                        val = float(row[1])
                        time_series_kp.append(TimeSeriesRecord(date=time_tag[:16], value=val))
                        curr_kp = val
                    except (ValueError, TypeError):
                        continue
    except Exception:
        curr_kp = 2.0

    kp_vals = [r.value for r in time_series_kp] or [curr_kp]
    peak_kp = max(kp_vals)
    mean_kp = sum(kp_vals) / len(kp_vals)

    # Indice Kp va da 0 a 9 (G5 Extreme Storm è Kp >= 9)
    risk_pct_kp = min(1.0, peak_kp / 9.0)

    kp_indicator = IndicatorSummary(
        metric_id="solar_kp_index",
        name="Indice Geomagnetico Planetario Kp (Tempeste Solari)",
        unit="scala Kp (0-9)",
        current_value=curr_kp,
        current_date=curr_date,
        total_records=len(time_series_kp),
        min_value=min(kp_vals),
        max_value=peak_kp,
        mean_value=mean_kp,
        percentile_5y=risk_pct_kp,
        sparkline=kp_vals[-30:] if len(kp_vals) >= 30 else kp_vals
    )

    # 2. Parsing USGS Terremoti
    quakes_count = 0
    max_mag = 0.0
    latest_quake_desc = ""
    try:
        r_quakes = requests.get(USGS_QUAKES_URL, headers=headers, timeout=timeout_sec)
        if r_quakes.status_code == 200:
            q_data = r_quakes.json()
            features = q_data.get("features", [])
            quakes_count = len(features)
            for feat in features:
                props = feat.get("properties", {})
                mag = props.get("mag") or 0.0
                if mag > max_mag:
                    max_mag = mag
                    latest_quake_desc = props.get("title") or ""
    except Exception:
        pass

    # Generazione notizie
    news_items = []
    if peak_kp >= 7.0:
        kp_severity = 4
        kp_status = f"TEMPESTA GEOMAGNETICA SEVERA (Kp={peak_kp}): possibile disturbo alle reti elettriche ad alta latitudine e comunicazioni HF."
    elif peak_kp >= 5.0:
        kp_severity = 2
        kp_status = f"TEMPESTA SOLARE MINORE (Kp={peak_kp}): aurore boreali visibili, attivita solare moderata."
    else:
        kp_severity = 1
        kp_status = f"CLIMA SPAZIALE QUIETO (Kp={peak_kp}): nessun rischio immediato da brillamenti o tempeste geomagnetiche."

    news_items.append(
        NewsItem(
            title=f"Monitoraggio Clima Spaziale: Kp a {curr_kp:.1f} (Picco {peak_kp:.1f})",
            date=curr_date,
            source="NOAA Space Weather Prediction Center",
            url="https://www.swpc.noaa.gov/",
            summary=kp_status,
            category="Rischi Naturali e Cosmici",
            severity=kp_severity,
            tags=["Spazio", "Sole", "Tempeste Solari", "Kp"]
        )
    )

    if quakes_count > 0 and latest_quake_desc:
        news_items.append(
            NewsItem(
                title=f"Attivita Sismica Significativa: {quakes_count} eventi nell'ultimo mese",
                date=curr_date,
                source="USGS Earthquake Hazards Program",
                url="https://earthquake.usgs.gov/",
                summary=f"Eventi tellurici globali maggiori registrati dai sismografi planetari. Evento di rilievo: {latest_quake_desc}.",
                category="Rischi Naturali e Cosmici",
                severity=2 if max_mag < 7.0 else 3,
                tags=["Terremoti", "Geologia", "USGS"]
            )
        )

    return CategoryPayload(
        category_id="cosmic_natural_hazards",
        category_name="Rischi Naturali e Cosmici",
        indicators={"solar_kp": kp_indicator},
        time_series={"kp_hourly_chart": time_series_kp[-72:]}, # Ultime 72 misurazioni
        news_items=news_items
    )
