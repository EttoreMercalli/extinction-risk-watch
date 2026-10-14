"""
Parser per Fragilità Finanziaria e Sistemica (CBOE VIX & Yahoo Finance).
Estrae:
- Formato Tabella: serie storica completa del VIX, valore spot, percentile a 5 anni per l'algoritmo
- Formato Testo: interpretazione dello stato di stress sistemico e alert di mercato
"""

import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional
import requests

from src.parsers.models import CategoryPayload, IndicatorSummary, TimeSeriesRecord, NewsItem

CBOE_VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"

def fetch_and_parse_finance(timeout_sec: float = 15.0) -> CategoryPayload:
    """Scarica e converte i dati dell'indice VIX CBOE in serie temporale e indicatori."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(CBOE_VIX_URL, headers=headers, timeout=timeout_sec)
    response.raise_for_status()

    reader = csv.reader(io.StringIO(response.text))
    header = next(reader, None)

    # Indici colonne: DATE, OPEN, HIGH, LOW, CLOSE
    all_records: List[TimeSeriesRecord] = []
    values_5y: List[float] = []

    cutoff_5y = (datetime.now() - timedelta(days=5 * 365)).strftime("%Y-%m-%d")

    for row in reader:
        if len(row) < 5:
            continue
        raw_date, _, _, _, raw_close = row[0].strip(), row[1], row[2], row[3], row[4].strip()
        try:
            close_val = float(raw_close)
            # Converte MM/DD/YYYY in YYYY-MM-DD
            dt = datetime.strptime(raw_date, "%m/%d/%Y")
            iso_date = dt.strftime("%Y-%m-%d")
            all_records.append(TimeSeriesRecord(date=iso_date, value=close_val))

            if iso_date >= cutoff_5y:
                values_5y.append(close_val)
        except ValueError:
            continue

    if not all_records:
        raise ValueError("Nessun record valido estratto dal feed CBOE VIX.")

    current_record = all_records[-1]
    curr_val = current_record.value
    curr_date = current_record.date

    # Calcolo percentile su 5 anni
    if values_5y:
        below_count = sum(1 for v in values_5y if v <= curr_val)
        percentile_5y = below_count / len(values_5y)
        min_v = min(values_5y)
        max_v = max(values_5y)
        mean_v = sum(values_5y) / len(values_5y)
    else:
        percentile_5y = 0.5
        min_v = curr_val
        max_v = curr_val
        mean_v = curr_val

    sparkline = [r.value for r in all_records[-30:]]

    # Serie per il grafico web: ultimi 365 giorni di trading (~1.5 anni di calendario)
    chart_series = all_records[-365:]

    indicator = IndicatorSummary(
        metric_id="vix_index",
        name="CBOE Volatility Index (VIX)",
        unit="punti",
        current_value=curr_val,
        current_date=curr_date,
        total_records=len(all_records),
        min_value=min_v,
        max_value=max_v,
        mean_value=mean_v,
        percentile_5y=percentile_5y,
        sparkline=sparkline
    )

    # Generazione elemento testuale per la UI
    if curr_val >= 40.0:
        severity = 5
        sentiment = "PANICO SISTEMICO ESTREMO: mercati finanziari globali sotto shock severo. Capacità di resilienza istituzionale drasticamente compromessa."
    elif curr_val >= 30.0:
        severity = 4
        sentiment = "ELEVATA TURBOLENZA GLOBALE: volatilità implicita sui massimi plurimensili. Segnali di stress sistemico acuto."
    elif curr_val >= 20.0:
        severity = 3
        sentiment = "TENSIONE MODERATA: mercati in allerta per rischi macroeconomici e geopolitici latenti."
    else:
        severity = 1
        sentiment = "STABILITÀ FINANZIARIA: volatilità contenuta, assenza di shock sistemici immediati sulla liquidità globale."

    news = [
        NewsItem(
            title=f"Indice VIX a quota {curr_val:.2f} ({sentiment.split(':')[0]})",
            date=curr_date,
            source="CBOE Global Markets",
            url="https://www.cboe.com/tradable_products/vix/",
            summary=sentiment,
            category="Fragilità Finanziaria e Sistemica",
            severity=severity,
            tags=["VIX", "Mercati", "Fragilità", "Volatilità"]
        )
    ]

    return CategoryPayload(
        category_id="systemic_fragility",
        category_name="Fragilità Finanziaria e Sistemica",
        indicators={"vix": indicator},
        time_series={"vix_daily_chart": chart_series},
        news_items=news
    )
