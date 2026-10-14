#!/usr/bin/env python3
"""
CLI Tool e Simulatore per il Calcolo Veritiero del Rischio di Estinzione Umana.
Contrasta:
- Aspettativa Biologica Naturale della Specie (~200.000 anni / 73 milioni di giorni)
- Compressione Antropogenica ed Ecologica attuale (~209.000 giorni / ~575 anni)
- Probabilità percentuali su 1, 5, 10, 50 e 100 anni
"""

import sys
import json
import argparse
from pathlib import Path

# Compatibilità encoding UTF-8 console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.parsers import fetch_all_categories
from src.parsers.models import CategoryPayload, IndicatorSummary
from src.engine import DoomsdayCalculator, ExtinctionLifespanResult

def print_lifespan_report(result: ExtinctionLifespanResult, title: str = "CALCOLO QUANTITATIVO DEL RISCHIO DI ESTINZIONE"):
    print("\n" + "=" * 94)
    print(f"                 {title}")
    print("=" * 94)

    ls = result.lifespan

    # 1. Hero Metric: Il Contrasto Biologico vs Antropogenico
    bio_days_str = f"{ls.biological_baseline_days:,}".replace(",", ".")
    bio_yrs_str = f"{int(ls.biological_baseline_years):,}".replace(",", ".")
    eff_days_str = f"{ls.effective_expected_days:,}".replace(",", ".")
    eff_yrs_str = f"{ls.effective_expected_years:.1f}"

    delta_d = ls.daily_delta_days_vs_norm
    delta_sign = "+" if delta_d >= 0 else ""
    delta_str = f"{delta_sign}{delta_d:,}".replace(",", ".")

    print(f"\n   🧬 DATA DI SCADENZA BIOLOGICA NATURALE (Genetica & Evoluzione):")
    print(f"      • Aspettativa naturale della specie Homo sapiens: ~{bio_yrs_str} ANNI  (~{bio_days_str} GIORNI)")
    print(f"        (Fonte: Genetica delle popolazioni, Science 2023 & Principio Copernicano J. R. Gott)")

    print(f"\n   ⚠️ COMPRESSIONE ANTROPOGENICA ATTUALE (Guerra, Clima, IA, Biosicurezza):")
    print(f"      • Aspettativa residua effettiva al rischio odierno: >>> [ {eff_days_str} GIORNI ] <<< (~{eff_yrs_str} ANNI)")
    print(f"      • Futuro potenziale naturale eroso dalle minacce umane: {ls.future_potential_lost_pct:.1f}%")
    print(f"      • Fluttuazione contingente di oggi: {delta_str} giorni rispetto alla norma del secolo")
    print(f"      • Moltiplicatore di Fragilità Sistemica (VIX a 15.27): x{result.systemic_fragility_multiplier:.3f}")

    # 2. I 5 Orizzonti Temporali
    print("\n" + "-" * 94)
    print("   PROBABILITÀ PERCENTUALE DI ESTINZIONE SUI 5 ORIZZONTI TEMPORALI:")
    print("-" * 94)
    h_header = f"   {'ORIZZONTE':<15} | {'PROBABILITÀ (%)':<16} | {'QUOTA (ODDS)':<18} | {'DELTA BASELINE':<16} | {'LIVELLO':<10}"
    print(h_header)
    print("   " + "-" * 88)

    order = ["1_year", "5_years", "10_years", "50_years", "100_years"]
    labels = {
        "1_year": "1 Anno",
        "5_years": "5 Anni",
        "10_years": "10 Anni",
        "50_years": "50 Anni",
        "100_years": "100 Anni"
    }

    for k in order:
        h = result.horizons[k]
        lbl = labels[k]
        dsign = "+" if h.delta_vs_baseline >= 0 else ""
        dstr = f"{dsign}{h.delta_vs_baseline * 100:.3f}%"
        print(f"   {lbl:<15} | {h.percentage_str:<16} | {h.odds_str:<18} | {dstr:<16} | [{h.risk_tier}]")

    # 3. Scomposizione per Categoria
    print("\n" + "-" * 94)
    print("   SCOMPOSIZIONE DEL RISCHIO PER MACROCATEGORIA:")
    print("-" * 94)
    c_header = f"   {'CATEGORIA':<36} | {'MODULATORE':<11} | {'1 ANNO':<10} | {'10 ANNI':<10} | {'100 ANNI':<10} | {'STATO':<12}"
    print(c_header)
    print("   " + "-" * 92)

    for cat_id, c in result.categories.items():
        p1 = f"{c.prob_1y * 100:.3f}%"
        p10 = f"{c.prob_10y * 100:.2f}%"
        p100 = f"{c.prob_100y * 100:.2f}%"
        mod_str = f"x{c.modulator:.2f} ({c.percentile_driver*100:.0f}°)"
        print(f"   {c.category_name:<36} | {mod_str:<11} | {p1:<10} | {p10:<10} | {p100:<10} | {c.status_label}")

    # 4. Fonti Scientifiche Citate
    print("\n" + "-" * 94)
    print("   FONTI E CITAZIONI SCIENTIFICHE DELLA METODOLOGIA:")
    print("-" * 94)
    for s in result.scientific_sources:
        print(f"   • [{s.scope}]")
        print(f"     {s.title} ({s.authors}, {s.year} - {s.institution})")
        print(f"     URL: {s.url}")

    print("=" * 94 + "\n")

def run_simulation():
    """Esegue scenari ipotetici di stress-test."""
    calc = DoomsdayCalculator()

    print("\n" + "#" * 94)
    print("                      SIMULAZIONE SCENARI DI STRESS-TEST")
    print("#" * 94)

    # Scenario A: Crisi Acuta
    print("\n>>> SCENARIO A: CRISI NUCLEARE TOTALE & PANICO DEI MERCATI")
    print("    (GPR al 100° percentile, VIX al 100° percentile)")
    sim_a = {
        "geopolitics_nuclear": CategoryPayload(
            category_id="geopolitics_nuclear",
            category_name="Guerra Nucleare & Conflitti",
            indicators={"gpr": IndicatorSummary("gpr", "GPR", "idx", 600.0, "2026-10-14", 100, 50, 600, 200, 1.0)}
        ),
        "systemic_fragility": CategoryPayload(
            category_id="systemic_fragility",
            category_name="Fragilità",
            indicators={"vix": IndicatorSummary("vix", "VIX", "pts", 80.0, "2026-10-14", 100, 10, 80, 25, 1.0)}
        )
    }
    res_a = calc.compute_index(sim_a)
    days_a = f"{res_a.lifespan.effective_expected_days:,}".replace(",", ".")
    print(f"    -> Giorni Residui Effettivi:  {days_a} giorni (~{res_a.lifespan.effective_expected_years:.0f} anni)")
    print(f"    -> Rischio a 1 Anno:    {res_a.horizons['1_year'].percentage_str} ({res_a.horizons['1_year'].odds_str})")
    print(f"    -> Rischio a 5 Anni:    {res_a.horizons['5_years'].percentage_str} ({res_a.horizons['5_years'].odds_str})")
    print(f"    -> Rischio a 10 Anni:   {res_a.horizons['10_years'].percentage_str} ({res_a.horizons['10_years'].odds_str})")
    print(f"    -> Rischio a 50 Anni:   {res_a.horizons['50_years'].percentage_str} ({res_a.horizons['50_years'].odds_str})")
    print(f"    -> Rischio a 100 Anni:  {res_a.horizons['100_years'].percentage_str} ({res_a.horizons['100_years'].odds_str})")

    # Scenario B: Distensione e Transizione Ecologica
    print("\n>>> SCENARIO B: DISTENSIONE GEOPOLITICA & TRANSIZIONE ECOLOGICA")
    print("    (GPR al 10° percentile, VIX al 10° percentile, CO2 stabilizzata)")
    sim_b = {
        "geopolitics_nuclear": CategoryPayload(
            category_id="geopolitics_nuclear",
            category_name="Guerra Nucleare & Conflitti",
            indicators={"gpr": IndicatorSummary("gpr", "GPR", "idx", 40.0, "2026-10-14", 100, 40, 400, 120, 0.10)}
        ),
        "systemic_fragility": CategoryPayload(
            category_id="systemic_fragility",
            category_name="Fragilità",
            indicators={"vix": IndicatorSummary("vix", "VIX", "pts", 11.0, "2026-10-14", 100, 10, 80, 20, 0.10)}
        ),
        "climate_biosphere": CategoryPayload(
            category_id="climate_biosphere",
            category_name="Clima",
            indicators={
                "co2": IndicatorSummary("co2", "CO2", "ppm", 350.0, "2026-10-14", 100, 300, 430, 380, 0.20),
                "sea_ice": IndicatorSummary("sea_ice", "Ice", "mln kmq", 12.0, "2026-10-14", 100, 4, 15, 10, 0.20)
            }
        )
    }
    res_b = calc.compute_index(sim_b)
    days_b = f"{res_b.lifespan.effective_expected_days:,}".replace(",", ".")
    print(f"    -> Giorni Residui Effettivi:  {days_b} giorni (~{res_b.lifespan.effective_expected_years:.0f} anni)")
    print(f"    -> Rischio a 1 Anno:    {res_b.horizons['1_year'].percentage_str} ({res_b.horizons['1_year'].odds_str})")
    print(f"    -> Rischio a 5 Anni:    {res_b.horizons['5_years'].percentage_str} ({res_b.horizons['5_years'].odds_str})")
    print(f"    -> Rischio a 10 Anni:   {res_b.horizons['10_years'].percentage_str} ({res_b.horizons['10_years'].odds_str})")
    print(f"    -> Rischio a 50 Anni:   {res_b.horizons['50_years'].percentage_str} ({res_b.horizons['50_years'].odds_str})")
    print(f"    -> Rischio a 100 Anni:  {res_b.horizons['100_years'].percentage_str} ({res_b.horizons['100_years'].odds_str})")
    print("#" * 94 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Calcolo Veritiero del Rischio di Estinzione Umana.")
    parser.add_argument("--simulate", action="store_true", help="Esegue anche le simulazioni di scenari estremi.")
    parser.add_argument("--live", action="store_true", help="Forza il re-download live dai siti target.")
    args = parser.parse_args()

    extracted_sample_file = Path("data/extracted_sample.json")
    categories_data = {}

    if not args.live and extracted_sample_file.exists():
        print("-> Caricamento dati estratti da data/extracted_sample.json...")
        with open(extracted_sample_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        for cat_id, cat_dict in raw_data.items():
            inds = {}
            for m_id, ind_dict in cat_dict.get("indicators", {}).items():
                inds[m_id] = IndicatorSummary(
                    metric_id=ind_dict["metric_id"],
                    name=ind_dict["name"],
                    unit=ind_dict["unit"],
                    current_value=ind_dict["current_value"],
                    current_date=ind_dict["current_date"],
                    total_records=ind_dict.get("total_records", 0),
                    min_value=ind_dict.get("min_value", 0.0),
                    max_value=ind_dict.get("max_value", 0.0),
                    mean_value=ind_dict.get("mean_value", 0.0),
                    percentile_5y=ind_dict.get("percentile_5y", 0.5),
                    sparkline=ind_dict.get("sparkline", [])
                )
            categories_data[cat_id] = CategoryPayload(
                category_id=cat_dict["category_id"],
                category_name=cat_dict["category_name"],
                indicators=inds
            )
    else:
        print("-> Esecuzione parser live per estrarre i dati correnti...")
        categories_data = fetch_all_categories()

    calculator = DoomsdayCalculator()
    result = calculator.compute_index(categories_data)

    print_lifespan_report(result)

    if args.simulate:
        run_simulation()

    out_dir = Path("data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "extinction_lifespan_output.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    print(f"Risultato salvato in: {out_file.resolve()}\n")

if __name__ == "__main__":
    main()
