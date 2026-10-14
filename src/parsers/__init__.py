"""
Package parsers: Moduli per l'estrazione e conversione dei dati numerici (tabelle) e testuali (notizie).
"""

from typing import Dict
from concurrent.futures import ThreadPoolExecutor

from src.parsers.models import CategoryPayload, IndicatorSummary, TimeSeriesRecord, NewsItem
from src.parsers.finance_parser import fetch_and_parse_finance
from src.parsers.climate_parser import fetch_and_parse_climate
from src.parsers.geopolitics_parser import fetch_and_parse_geopolitics
from src.parsers.pandemics_parser import fetch_and_parse_pandemics
from src.parsers.cosmic_parser import fetch_and_parse_cosmic

def fetch_all_categories(max_workers: int = 5) -> Dict[str, CategoryPayload]:
    """
    Esegue in parallelo tutti i parser di estrazione e conversione dei dati.
    Restituisce un dizionario contenente per ogni categoria:
    - Formato Tabella: serie storiche per grafici e indicatori normalizzati per l'algoritmo
    - Formato Testuale: feed di notizie e bollettini per la UI
    """
    parsers = {
        "systemic_fragility": fetch_and_parse_finance,
        "climate_biosphere": fetch_and_parse_climate,
        "geopolitics_nuclear": fetch_and_parse_geopolitics,
        "pandemics_biosecurity": fetch_and_parse_pandemics,
        "cosmic_natural_hazards": fetch_and_parse_cosmic
    }

    results: Dict[str, CategoryPayload] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_cat = {executor.submit(fn): cat for cat, fn in parsers.items()}
        for future in future_to_cat:
            cat = future_to_cat[future]
            try:
                payload = future.result()
                results[cat] = payload
            except Exception as e:
                print(f"[ERRORE PARSER] Categoria '{cat}' ha sollevato un'eccezione: {e}")

    return results

__all__ = [
    "CategoryPayload",
    "IndicatorSummary",
    "TimeSeriesRecord",
    "NewsItem",
    "fetch_and_parse_finance",
    "fetch_and_parse_climate",
    "fetch_and_parse_geopolitics",
    "fetch_and_parse_pandemics",
    "fetch_and_parse_cosmic",
    "fetch_all_categories"
]
