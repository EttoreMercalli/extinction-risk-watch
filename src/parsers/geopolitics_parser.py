"""
Parser per Guerra Nucleare e Rischio Geopolitico (Geopolitical Risk Index - Caldara & Iacoviello).
Estrae:
- Formato Tabella: serie storica del GPRD (Geopolitical Risk Daily), sub-indice minacce (GPRD_THREAT) e atti (GPRD_ACT)
- Formato Testo: livello di allerta di escalation bellica / nucleare
"""

from datetime import datetime, timedelta
from typing import List
import requests
import xlrd

from src.parsers.models import CategoryPayload, IndicatorSummary, TimeSeriesRecord, NewsItem

GPR_XLS_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls"

def fetch_and_parse_geopolitics(timeout_sec: float = 20.0) -> CategoryPayload:
    """Scarica e converte i dati dell'indice GPR giornaliero di Caldara & Iacoviello."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(GPR_XLS_URL, headers=headers, timeout=timeout_sec)
    response.raise_for_status()

    wb = xlrd.open_workbook(file_contents=response.content)
    sheet = wb.sheet_by_index(0)

    # Identifica le colonne: DAY, GPRD, GPRD_ACT, GPRD_THREAT, GPRD_MA30, event
    col_map = {}
    for col_idx in range(sheet.ncols):
        col_name = str(sheet.cell_value(0, col_idx)).strip().upper()
        col_map[col_name] = col_idx

    day_idx = col_map.get("DAY", 0)
    gprd_idx = col_map.get("GPRD", 2)
    threat_idx = col_map.get("GPRD_THREAT", 4)
    act_idx = col_map.get("GPRD_ACT", 3)
    event_idx = col_map.get("EVENT", 8)

    all_records: List[TimeSeriesRecord] = []
    values_5y: List[float] = []
    recent_events: List[str] = []

    cutoff_5y = (datetime.now() - timedelta(days=5 * 365)).strftime("%Y-%m-%d")

    for r in range(1, sheet.nrows):
        raw_day = str(sheet.cell_value(r, day_idx)).strip()
        # raw_day può essere '19850101' o numero float '19850101.0'
        if "." in raw_day:
            raw_day = raw_day.split(".")[0]
        if len(raw_day) != 8:
            continue

        try:
            iso_date = f"{raw_day[:4]}-{raw_day[4:6]}-{raw_day[6:]}"
            val = float(sheet.cell_value(r, gprd_idx))
            all_records.append(TimeSeriesRecord(date=iso_date, value=val))

            if iso_date >= cutoff_5y:
                values_5y.append(val)

            evt_text = str(sheet.cell_value(r, event_idx)).strip()
            if evt_text and iso_date >= cutoff_5y:
                recent_events.append(f"{iso_date}: {evt_text}")
        except (ValueError, TypeError):
            continue

    if not all_records:
        raise ValueError("Nessun record valido estratto dal file GPR.")

    curr_record = all_records[-1]
    curr_val = curr_record.value
    curr_date = curr_record.date

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

    indicator = IndicatorSummary(
        metric_id="gprd_index",
        name="Geopolitical Risk Index (GPR Daily)",
        unit="indice",
        current_value=curr_val,
        current_date=curr_date,
        total_records=len(all_records),
        min_value=min_v,
        max_value=max_v,
        mean_value=mean_v,
        percentile_5y=percentile_5y,
        sparkline=[r.value for r in all_records[-30:]]
    )

    # Generazione elemento testuale per la UI
    if curr_val >= 300.0:
        severity = 5
        status_txt = "ALLERTA ROSSA GEOPOLITICA: picco storico di minacce e tensioni belliche tra superpotenze. Rischio di escalation nucleare ai massimi."
    elif curr_val >= 200.0:
        severity = 4
        status_txt = "TENSIONE GEOPOLITICA ACUTA: frequenza anomala di minacce militari e crisi internazionali nei media globali."
    elif curr_val >= 120.0:
        severity = 3
        status_txt = "RISCHIO GEOPOLITICO ELEVATO: attriti diplomatici e conflitti regionali attivi."
    else:
        severity = 1
        status_txt = "RISCHIO GEOPOLITICO NELLA NORMA: livello ordinario di conflittualita internazionale."

    last_event_note = f" Ultimi eventi tracciati: {recent_events[-1]}" if recent_events else ""

    news = [
        NewsItem(
            title=f"Indice di Rischio Geopolitico GPR a quota {curr_val:.1f} ({status_txt.split(':')[0]})",
            date=curr_date,
            source="Federal Reserve Board / Matteo Iacoviello",
            url="https://www.matteoiacoviello.com/gpr.htm",
            summary=status_txt + last_event_note,
            category="Guerra Nucleare e Geopolitica",
            severity=severity,
            tags=["Geopolitica", "Guerra", "GPR", "Nucleare", "Escalation"]
        )
    ]

    return CategoryPayload(
        category_id="geopolitics_nuclear",
        category_name="Guerra Nucleare e Geopolitica",
        indicators={"gpr": indicator},
        time_series={"gpr_daily_chart": all_records[-365:]},
        news_items=news
    )
