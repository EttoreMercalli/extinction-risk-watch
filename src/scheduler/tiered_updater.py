"""
Motore di Aggiornamento a Scaglioni (Tiered Updater).
Gestisce l'aggiornamento continuo dei dati distinguendo tra:
- Fonti Veloci (Realtime / ogni 10 minuti): VIX spot, NOAA Kp, USGS sismi, news OMS/CIDRAP
- Fonti Lente (Giornaliere / Cache 12-24h): CO2 Mauna Loa, Ghiacci NSIDC, Indice GPR
Assicura scrittura atomica di `public/data/index.json` senza blocchi per i client web.
"""

import os
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

import requests

from src.parsers.models import (
    CategoryPayload,
    IndicatorSummary,
    TimeSeriesRecord,
    NewsItem
)
from src.parsers.finance_parser import fetch_and_parse_finance
from src.parsers.climate_parser import fetch_and_parse_climate
from src.parsers.geopolitics_parser import fetch_and_parse_geopolitics
from src.parsers.pandemics_parser import fetch_and_parse_pandemics
from src.parsers.cosmic_parser import fetch_and_parse_cosmic
from src.engine import DoomsdayCalculator, ExtinctionLifespanResult

logger = logging.getLogger("ExtinctionScheduler")

YAHOO_VIX_URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"

class TieredDataUpdater:
    """Gestore intelligente dell'aggiornamento dati a intervalli frequenti (10 min)."""

    def __init__(
        self,
        data_cache_path: Path = Path("data/extracted_sample.json"),
        output_json_path: Path = Path("public/data/index.json"),
        slow_refresh_hours: float = 12.0
    ):
        self.data_cache_path = data_cache_path
        self.output_json_path = output_json_path
        self.slow_refresh_interval = timedelta(hours=slow_refresh_hours)
        self.last_slow_refresh: Optional[datetime] = None
        self.calculator = DoomsdayCalculator()
        self.categories_cache: Dict[str, CategoryPayload] = {}

    def load_initial_cache(self):
        """Carica la cache esistente o esegue il primo scarico completo."""
        if self.data_cache_path.exists():
            try:
                with open(self.data_cache_path, "r", encoding="utf-8") as f:
                    raw_cache = json.load(f)
                for cat_id, cat_dict in raw_cache.items():
                    inds = {k: IndicatorSummary(**v) for k, v in cat_dict.get("indicators", {}).items()}
                    ts = {k: [TimeSeriesRecord(**pt) for pt in pts] for k, pts in cat_dict.get("time_series", {}).items()}
                    news = [NewsItem(**n) for n in cat_dict.get("news_items", [])]
                    self.categories_cache[cat_id] = CategoryPayload(
                        category_id=cat_dict["category_id"],
                        category_name=cat_dict["category_name"],
                        indicators=inds,
                        time_series=ts,
                        news_items=news
                    )
                self.last_slow_refresh = datetime.now(timezone.utc) - timedelta(hours=2)
                logger.info(f"Cache caricata con successo ({len(self.categories_cache)} categorie).")
                return
            except Exception as e:
                logger.warning(f"Errore lettura cache: {e}. Eseguo scarico iniziale completo...")

        self.refresh_slow_sources()

    def refresh_fast_sources(self) -> Dict[str, Any]:
        """
        Aggiorna le fonti veloci (eseguito ogni 10 minuti):
        1. VIX spot in tempo reale da Yahoo Finance
        2. Indice geomagnetico solare Kp (NOAA) e sismi (USGS)
        3. Allerte e notizie sanitarie recentissime (OMS e CIDRAP)
        """
        updates_log = {}
        t0 = time.time()

        # 1. Aggiornamento VIX spot (latenza ~300ms)
        try:
            r = requests.get(YAHOO_VIX_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            if r.status_code == 200:
                y_data = r.json()
                meta = y_data.get("chart", {}).get("result", [{}])[0].get("meta", {})
                spot_price = meta.get("regularMarketPrice")
                if spot_price and "systemic_fragility" in self.categories_cache:
                    vix_ind = self.categories_cache["systemic_fragility"].indicators.get("vix")
                    if vix_ind:
                        old_v = vix_ind.current_value
                        vix_ind.current_value = float(spot_price)
                        vix_ind.current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                        # Ricalcola percentile su min/max stimati
                        vix_ind.percentile_5y = max(0.01, min(0.99, (spot_price - vix_ind.min_value) / max(1.0, (vix_ind.max_value - vix_ind.min_value))))
                        updates_log["vix_spot"] = {"old": old_v, "new": spot_price}
        except Exception as e:
            logger.warning(f"Errore aggiornamento rapido VIX spot: {e}")

        # 2. Aggiornamento Rischi Cosmici & Tempeste Solari (NOAA Kp / USGS)
        try:
            cosmic_payload = fetch_and_parse_cosmic(timeout_sec=10.0)
            self.categories_cache["cosmic_natural_hazards"] = cosmic_payload
            kp_val = cosmic_payload.indicators.get("solar_kp", type("",(),{"current_value":0})()).current_value
            updates_log["solar_kp"] = kp_val
        except Exception as e:
            logger.warning(f"Errore aggiornamento rapido clima spaziale: {e}")

        # 3. Aggiornamento Notizie Pandemie (OMS e CIDRAP)
        try:
            pandemic_payload = fetch_and_parse_pandemics(timeout_sec=10.0)
            self.categories_cache["pandemics_biosecurity"] = pandemic_payload
            updates_log["active_outbreaks"] = len(pandemic_payload.news_items)
        except Exception as e:
            logger.warning(f"Errore aggiornamento rapido feed pandemie: {e}")

        elapsed = round(time.time() - t0, 2)
        updates_log["elapsed_sec"] = elapsed
        return updates_log

    def refresh_slow_sources(self):
        """Aggiorna le fonti pesanti/giornaliere (CO2, Ghiacci, GPR, CBOE History)."""
        logger.info("-> Aggiornamento fonti giornaliere (CO2, Ghiacci, GPR)...")
        t0 = time.time()

        try:
            self.categories_cache["climate_biosphere"] = fetch_and_parse_climate()
        except Exception as e:
            logger.error(f"Errore refresh clima: {e}")

        try:
            self.categories_cache["geopolitics_nuclear"] = fetch_and_parse_geopolitics()
        except Exception as e:
            logger.error(f"Errore refresh geopolitica GPR: {e}")

        try:
            self.categories_cache["systemic_fragility"] = fetch_and_parse_finance()
        except Exception as e:
            logger.error(f"Errore refresh finanza CBOE: {e}")

        self.last_slow_refresh = datetime.now(timezone.utc)
        logger.info(f"Fonti giornaliere aggiornate in {time.time() - t0:.1f}s.")

    def run_update_cycle(self) -> ExtinctionLifespanResult:
        """Esegue un ciclo completo di aggiornamento (chiamato ogni 10 minuti)."""
        now = datetime.now(timezone.utc)

        # 1. Controlla se è necessario il refresh delle fonti lente
        if self.last_slow_refresh is None or (now - self.last_slow_refresh) >= self.slow_refresh_interval:
            self.refresh_slow_sources()

        # 2. Esegui il refresh delle fonti veloci
        fast_updates = self.refresh_fast_sources()

        # 3. Ricalcola l'algoritmo quantitativo
        result = self.calculator.compute_index(self.categories_cache)

        # 4. Scrittura atomica del file public/data/index.json
        self._atomic_write_index_json(result)

        # 5. Salva la cache aggiornata su disco
        self._save_cache_on_disk()

        return result

    def _atomic_write_index_json(self, result: ExtinctionLifespanResult):
        """Scrive il file index.json in modo atomico per evitare letture parziali da parte dei client."""
        site_payload = {
            "metadata": {
                "title": "Extinction Risk Watch",
                "subtitle": "Quantificazione del Rischio di Estinzione Umana e Monitoraggio in Tempo Reale",
                "version": "1.0.0",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "status": "LIVE_AUTO_REFRESH",
                "refresh_interval_minutes": 10
            },
            "hero_lifespan": result.lifespan.to_dict(),
            "horizons": {
                k: {
                    "horizon_years": v.horizon_years,
                    "probability": v.probability,
                    "percentage_str": v.percentage_str,
                    "odds_str": v.odds_str,
                    "delta_vs_baseline": v.delta_vs_baseline,
                    "risk_tier": v.risk_tier
                }
                for k, v in result.horizons.items()
            },
            "systemic_fragility": {
                "multiplier": round(result.systemic_fragility_multiplier, 3),
                "vix_percentile": self.categories_cache.get("systemic_fragility", CategoryPayload("","")).indicators.get("vix", type("",(),{"percentile_5y":0.5})()).percentile_5y
            },
            "categories_breakdown": {
                k: v.to_dict() for k, v in result.categories.items()
            },
            "charts": {
                cat_id: {
                    ts_name: [pt.to_dict() for pt in pts]
                    for ts_name, pts in payload.time_series.items()
                }
                for cat_id, payload in self.categories_cache.items()
                if payload.time_series
            },
            "news_feed": {
                cat_id: [n.to_dict() for n in payload.news_items]
                for cat_id, payload in self.categories_cache.items()
                if payload.news_items
            },
            "scientific_sources": [
                {
                    "title": s.title,
                    "authors": s.authors,
                    "year": s.year,
                    "institution": s.institution,
                    "scope": s.scope,
                    "url": s.url
                }
                for s in result.scientific_sources
            ],
            "verdict": result.summary_verdict
        }

        self.output_json_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.output_json_path.parent / f"{self.output_json_path.name}.tmp"

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(site_payload, f, indent=2, ensure_ascii=False)

        # Scambio atomico
        os.replace(temp_path, self.output_json_path)

    def _save_cache_on_disk(self):
        """Persiste la cache categorie su disco."""
        try:
            self.data_cache_path.parent.mkdir(parents=True, exist_ok=True)
            export_dict = {cat_id: payload.to_dict() for cat_id, payload in self.categories_cache.items()}
            with open(self.data_cache_path, "w", encoding="utf-8") as f:
                json.dump(export_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Impossibile salvare la cache su disco: {e}")
