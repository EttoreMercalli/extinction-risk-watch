#!/usr/bin/env python3
"""
Pipeline di Aggregazione Automatica (Fase 4 della Roadmap).
Esegue:
1. Estrazione dati dai connettori (Serie storiche e News)
2. Calcolo dell'algoritmo quantitativo (Aspettativa naturale vs compressa, 5 orizzonti)
3. Generazione del file statico unificato `public/data/index.json` pronto per il frontend
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Compatibilità encoding UTF-8 console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.parsers import fetch_all_categories
from src.parsers.models import CategoryPayload
from src.engine import DoomsdayCalculator, ExtinctionLifespanResult

def build_production_site_data(use_cache: bool = True) -> Path:
    print("-> Avvio pipeline di aggregazione dati per il sito web...")

    cache_file = Path("data/extracted_sample.json")
    categories_data = {}

    if use_cache and cache_file.exists():
        print(f"   Caricamento cache estrattore da {cache_file}...")
        with open(cache_file, "r", encoding="utf-8") as f:
            raw_cache = json.load(f)
        for cat_id, cat_dict in raw_cache.items():
            from src.parsers.models import IndicatorSummary, TimeSeriesRecord, NewsItem
            inds = {
                k: IndicatorSummary(**v) for k, v in cat_dict.get("indicators", {}).items()
            }
            ts = {
                k: [TimeSeriesRecord(**pt) for pt in pts]
                for k, pts in cat_dict.get("time_series", {}).items()
            }
            news = [NewsItem(**n) for n in cat_dict.get("news_items", [])]
            categories_data[cat_id] = CategoryPayload(
                category_id=cat_dict["category_id"],
                category_name=cat_dict["category_name"],
                indicators=inds,
                time_series=ts,
                news_items=news
            )
    else:
        print("   Esecuzione connettori live verso tutti i siti target...")
        categories_data = fetch_all_categories()

    # Esegui calcolo matematico
    print("   Esecuzione calcolo probabilistico (5 orizzonti & aspettativa di vita)...")
    calculator = DoomsdayCalculator()
    result = calculator.compute_index(categories_data)

    # Prepara il payload strutturato per il frontend web
    site_payload = {
        "metadata": {
            "title": "Extinction Risk Watch",
            "subtitle": "Quantificazione del Rischio di Estinzione Umana e Monitoraggio in Tempo Reale",
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "LIVE"
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
            "vix_percentile": categories_data.get("systemic_fragility", CategoryPayload("","")).indicators.get("vix", type("",(),{"percentile_5y":0.5})()).percentile_5y
        },
        "categories_breakdown": {
            k: v.to_dict() for k, v in result.categories.items()
        },
        "charts": {
            cat_id: {
                ts_name: [pt.to_dict() for pt in pts]
                for ts_name, pts in payload.time_series.items()
            }
            for cat_id, payload in categories_data.items()
            if payload.time_series
        },
        "news_feed": {
            cat_id: [n.to_dict() for n in payload.news_items]
            for cat_id, payload in categories_data.items()
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

    # Destinazione: public/data/index.json
    out_dir = Path("public/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(site_payload, f, indent=2, ensure_ascii=False)

    print(f"✅ Pipeline completata! File statico generato con successo:")
    print(f"   -> {out_file.resolve()} ({out_file.stat().st_size / 1024:.1f} KB)\n")
    return out_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline di compilazione dati per il frontend.")
    parser.add_argument("--live", action="store_true", help="Forza la riscarica dai connettori web live.")
    args = parser.parse_args()

    build_production_site_data(use_cache=not args.live)
