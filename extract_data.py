#!/usr/bin/env python3
"""
CLI Tool per l'estrazione, conversione e ispezione dei dati:
1. Formato Tabella (Serie storiche e valori numerici per grafici e algoritmo)
2. Formato Testo (Ultime notizie e allerte per il feed tematico della UI)
"""

import sys
import json
from pathlib import Path

# Assicura compatibilità UTF-8 sulla console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.parsers import fetch_all_categories

def main():
    print("-> Avvio estrazione e conversione dati da tutte le fonti target...")
    categories_data = fetch_all_categories()

    print("\n" + "=" * 95)
    print("      EXTINCTION RISK WATCH - RISULTATI ESTRAZIONE DATI (TABELLE & TESTO)")
    print("=" * 95)

    all_exported = {}

    for cat_id, payload in categories_data.items():
        print(f"\n📁 CATEGORIA: [{payload.category_name.upper()}] (ID: {cat_id})")
        print("-" * 95)

        # 1. FORMATO TABELLA / INDICATORI
        print("  📊 FORMATO TABELLA (Indicatori Quantitativi & Percentili per l'Algoritmo):")
        for m_id, ind in payload.indicators.items():
            pct_str = f"{ind.percentile_5y * 100:.1f}%"
            print(f"     • {ind.name:<42} : {ind.current_value:>8.2f} {ind.unit:<12} (Data: {ind.current_date} | Storico: {ind.total_records} gg | Percentile: {pct_str})")

        # 2. SERIE GRAFICI
        print("\n  📈 SERIE TEMPORALI PER GRAFICI WEB:")
        for s_name, pts in payload.time_series.items():
            first_pt = pts[0].date if pts else "--"
            last_pt = pts[-1].date if pts else "--"
            print(f"     • Grafico '{s_name}': {len(pts)} punti giornalieri (Da: {first_pt} A: {last_pt})")

        # 3. FORMATO TESTUALE / NOTIZIE
        print("\n  📰 FORMATO TESTUALE (Ultime Notizie per la UI):")
        for news in payload.news_items:
            sev_badge = "🔴 ALLERTA" if news.severity >= 4 else ("🟡 ATTENZIONE" if news.severity >= 3 else "⚪ NOTIZIA")
            print(f"     [{sev_badge}] ({news.source} - {news.date})")
            print(f"       Titolo: {news.title}")
            print(f"       Sommario: {news.summary[:110]}...")

        all_exported[cat_id] = payload.to_dict()

    # Salva il dump JSON estratto
    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "extracted_sample.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_exported, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 95)
    print(f"✅ Estrazione completata con successo!")
    print(f"   Dati convertiti e salvati in: {output_file.resolve()}")
    print("=" * 95 + "\n")

if __name__ == "__main__":
    main()
