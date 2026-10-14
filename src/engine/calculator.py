"""
Motore Matematico di Calcolo Quantitativo del Rischio di Estinzione Umana.
Contrasta:
1. Aspettativa di vita naturale biologica della specie (~200.000 anni / ~73 milioni di giorni)
2. Compressione antropogenica ed ecologica dovuta a tecnologia e guerre nel XXI secolo
3. Probabilità percentuali su 1, 5, 10, 50 e 100 anni
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List

from src.engine.models import (
    ExtinctionLifespanResult,
    HorizonProbability,
    CategoryRiskBreakdown,
    SpeciesLifespanMetrics,
    ScientificSourceRef
)
from src.parsers.models import CategoryPayload

# -----------------------------------------------------------------------------------------
# 1. BASELINE STRUTTURALI A 100 ANNI (Fonte: Toby Ord, The Precipice, 2020 - Oxford Univ.)
# -----------------------------------------------------------------------------------------
BASELINE_100Y = {
    "ai_unaligned": 0.1000,          # 1 su 10 (10.0%)
    "engineered_pandemics": 0.0333,  # 1 su 30 (~3.33%)
    "nuclear_war": 0.0010,           # 1 su 1.000 (0.10%)
    "climate_collapse": 0.0010,      # 1 su 1.000 (0.10%)
    "cosmic_hazards": 0.0001,        # 1 su 10.000 (0.01%)
    "natural_pandemics": 0.0001,     # 1 su 10.000 (0.01%)
    "other_anthropogenic": 0.0333    # 1 su 30 (~3.33%)
}

# -----------------------------------------------------------------------------------------
# 2. PROIEZIONE TEMPORALE SUI 5 ORIZZONTI (1, 5, 10, 50, 100 ANNI)
# -----------------------------------------------------------------------------------------
TEMPORAL_FACTORS = {
    "ai_unaligned": {
        "1y": 0.015, "5y": 0.120, "10y": 0.350, "50y": 0.850, "100y": 1.000
    },
    "engineered_pandemics": {
        "1y": 0.020, "5y": 0.100, "10y": 0.300, "50y": 0.800, "100y": 1.000
    },
    "nuclear_war": {
        "1y": 0.030, "5y": 0.100, "10y": 0.200, "50y": 0.650, "100y": 1.000
    },
    "climate_collapse": {
        "1y": 0.002, "5y": 0.025, "10y": 0.080, "50y": 0.600, "100y": 1.000
    },
    "cosmic_hazards": {
        "1y": 0.010, "5y": 0.050, "10y": 0.100, "50y": 0.500, "100y": 1.000
    },
    "natural_pandemics": {
        "1y": 0.010, "5y": 0.050, "10y": 0.100, "50y": 0.500, "100y": 1.000
    },
    "other_anthropogenic": {
        "1y": 0.010, "5y": 0.060, "10y": 0.150, "50y": 0.650, "100y": 1.000
    }
}

# -----------------------------------------------------------------------------------------
# 3. FONTI SCIENTIFICHE PER IL CONFRONTO BIOLOGICO VS ANTROPOGENICO
# -----------------------------------------------------------------------------------------
SCIENTIFIC_SOURCES: List[ScientificSourceRef] = [
    ScientificSourceRef(
        title="Genomic inference of a severe human bottleneck during the Early to Middle Pleistocene transition",
        authors="Hu, Hao, Du, et al.",
        year=2023,
        institution="Science / Sapienza Universita di Roma / ECNU",
        scope="Biologico / Decadimento Genetico & Longevita Naturale della Specie",
        url="https://www.science.org/doi/10.1126/science.abq7487"
    ),
    ScientificSourceRef(
        title="Implications of the Copernican Principle on our Future Prospects",
        authors="J. Richard Gott III",
        year=1993,
        institution="Nature / Princeton University",
        scope="Biologico / Statistica di Longevita della Specie (~200.000 anni)",
        url="https://www.nature.com/articles/363315a0"
    ),
    ScientificSourceRef(
        title="The Precipice: Existential Risk and the Future of Humanity",
        authors="Toby Ord",
        year=2020,
        institution="Future of Humanity Institute / Oxford University",
        scope="Rischio Antropogenico & Accelerazione Tecnologica nel XXI Secolo",
        url="https://theprecipice.com/"
    )
]

class DoomsdayCalculator:
    """Calcola le probabilità di estinzione (1, 5, 10, 50, 100 anni) e l'erosione dell'aspettativa di vita naturale."""

    def compute_index(self, categories_data: Dict[str, CategoryPayload]) -> ExtinctionLifespanResult:
        """Esegue il calcolo quantitativo integrando i modulatori in tempo reale."""

        # 1. Moltiplicatore di Fragilità Sistemica (VIX)
        sys_pct = 0.50
        if "systemic_fragility" in categories_data:
            ind = categories_data["systemic_fragility"].indicators.get("vix")
            if ind:
                sys_pct = ind.percentile_5y

        # S varia in [0.85, 1.15]
        systemic_multiplier = 1.0 + 0.30 * (sys_pct - 0.50)

        # 2. Modulatori e scomposizione per categoria
        category_breakdowns: Dict[str, CategoryRiskBreakdown] = {}

        # --- A. Guerra Nucleare & Geopolitica ---
        gpr_pct = 0.50
        if "geopolitics_nuclear" in categories_data:
            ind = categories_data["geopolitics_nuclear"].indicators.get("gpr")
            if ind:
                gpr_pct = ind.percentile_5y
        mod_nuclear = max(0.5, min(1.6, 1.0 + 0.80 * (gpr_pct - 0.50)))
        b_nuc = BASELINE_100Y["nuclear_war"]
        p100_nuc = b_nuc * mod_nuclear * systemic_multiplier
        tf_nuc = TEMPORAL_FACTORS["nuclear_war"]
        p50_nuc = p100_nuc * tf_nuc["50y"]
        p10_nuc = p100_nuc * tf_nuc["10y"]
        p5_nuc = p100_nuc * tf_nuc["5y"] * (1.0 + 0.5 * (gpr_pct - 0.50))
        p1_nuc = p100_nuc * tf_nuc["1y"] * (1.0 + 1.0 * (gpr_pct - 0.50))

        category_breakdowns["nuclear_war"] = CategoryRiskBreakdown(
            category_id="nuclear_war",
            category_name="Guerra Nucleare & Conflitti",
            baseline_100y=b_nuc,
            modulator=mod_nuclear,
            prob_1y=p1_nuc,
            prob_5y=p5_nuc,
            prob_10y=p10_nuc,
            prob_50y=p50_nuc,
            prob_100y=p100_nuc,
            percentile_driver=gpr_pct,
            status_label="ALLERTA MASSIMA" if gpr_pct > 0.9 else ("TENSIONE" if gpr_pct > 0.7 else "NORMALE")
        )

        # --- B. Pandemie (Ingegnerizzate & Naturali) ---
        bio_pct = 0.50
        if "pandemics_biosecurity" in categories_data:
            ind = categories_data["pandemics_biosecurity"].indicators.get("outbreak_alerts")
            if ind:
                bio_pct = ind.percentile_5y
        mod_bio = max(0.6, min(1.5, 1.0 + 0.50 * (bio_pct - 0.50)))
        b_bio = BASELINE_100Y["engineered_pandemics"] + BASELINE_100Y["natural_pandemics"]
        p100_bio = b_bio * mod_bio * systemic_multiplier
        tf_bio = TEMPORAL_FACTORS["engineered_pandemics"]
        p50_bio = p100_bio * tf_bio["50y"]
        p10_bio = p100_bio * tf_bio["10y"]
        p5_bio = p100_bio * tf_bio["5y"]
        p1_bio = p100_bio * tf_bio["1y"]

        category_breakdowns["pandemics"] = CategoryRiskBreakdown(
            category_id="pandemics",
            category_name="Pandemie (Ingegnerizzate & Naturali)",
            baseline_100y=b_bio,
            modulator=mod_bio,
            prob_1y=p1_bio,
            prob_5y=p5_bio,
            prob_10y=p10_bio,
            prob_50y=p50_bio,
            prob_100y=p100_bio,
            percentile_driver=bio_pct,
            status_label="ELEVATA" if bio_pct > 0.75 else "NORMALE"
        )

        # --- C. Collasso Climatico ed Ecosistemico ---
        clim_pct = 0.50
        if "climate_biosphere" in categories_data:
            ind_co2 = categories_data["climate_biosphere"].indicators.get("co2")
            ind_ice = categories_data["climate_biosphere"].indicators.get("sea_ice")
            p_co2 = ind_co2.percentile_5y if ind_co2 else 0.5
            p_ice = ind_ice.percentile_5y if ind_ice else 0.5
            clim_pct = 0.5 * p_co2 + 0.5 * p_ice

        mod_clim = max(0.7, min(1.4, 1.0 + 0.40 * (clim_pct - 0.50)))
        b_clim = BASELINE_100Y["climate_collapse"]
        p100_clim = b_clim * mod_clim * systemic_multiplier
        tf_clim = TEMPORAL_FACTORS["climate_collapse"]
        p50_clim = p100_clim * tf_clim["50y"]
        p10_clim = p100_clim * tf_clim["10y"]
        p5_clim = p100_clim * tf_clim["5y"]
        p1_clim = p100_clim * tf_clim["1y"]

        category_breakdowns["climate"] = CategoryRiskBreakdown(
            category_id="climate",
            category_name="Collasso Climatico ed Ecosistemico",
            baseline_100y=b_clim,
            modulator=mod_clim,
            prob_1y=p1_clim,
            prob_5y=p5_clim,
            prob_10y=p10_clim,
            prob_50y=p50_clim,
            prob_100y=p100_clim,
            percentile_driver=clim_pct,
            status_label="PRESSIONE COSTANTE" if clim_pct > 0.8 else "NORMALE"
        )

        # --- D. Rischi Naturali e Cosmici ---
        cosm_pct = 0.50
        if "cosmic_natural_hazards" in categories_data:
            ind = categories_data["cosmic_natural_hazards"].indicators.get("solar_kp")
            if ind:
                cosm_pct = ind.percentile_5y
        mod_cosm = max(0.8, min(1.3, 1.0 + 0.30 * (cosm_pct - 0.50)))
        b_cosm = BASELINE_100Y["cosmic_hazards"]
        p100_cosm = b_cosm * mod_cosm
        tf_cosm = TEMPORAL_FACTORS["cosmic_hazards"]
        p50_cosm = p100_cosm * tf_cosm["50y"]
        p10_cosm = p100_cosm * tf_cosm["10y"]
        p5_cosm = p100_cosm * tf_cosm["5y"]
        p1_cosm = p100_cosm * tf_cosm["1y"]

        category_breakdowns["cosmic"] = CategoryRiskBreakdown(
            category_id="cosmic",
            category_name="Rischi Naturali e Cosmici",
            baseline_100y=b_cosm,
            modulator=mod_cosm,
            prob_1y=p1_cosm,
            prob_5y=p5_cosm,
            prob_10y=p10_cosm,
            prob_50y=p50_cosm,
            prob_100y=p100_cosm,
            percentile_driver=cosm_pct,
            status_label="MODERATO" if cosm_pct > 0.7 else "BASSO"
        )

        # --- E. Intelligenza Artificiale non Allineata (AGI) ---
        ai_pct = 0.70  # Finestra di transizione AGI
        mod_ai = 1.0 + 0.30 * (ai_pct - 0.50)
        b_ai = BASELINE_100Y["ai_unaligned"]
        p100_ai = b_ai * mod_ai * systemic_multiplier
        tf_ai = TEMPORAL_FACTORS["ai_unaligned"]
        p50_ai = p100_ai * tf_ai["50y"]
        p10_ai = p100_ai * tf_ai["10y"]
        p5_ai = p100_ai * tf_ai["5y"]
        p1_ai = p100_ai * tf_ai["1y"]

        category_breakdowns["ai_risk"] = CategoryRiskBreakdown(
            category_id="ai_risk",
            category_name="Intelligenza Artificiale non Allineata",
            baseline_100y=b_ai,
            modulator=mod_ai,
            prob_1y=p1_ai,
            prob_5y=p5_ai,
            prob_10y=p10_ai,
            prob_50y=p50_ai,
            prob_100y=p100_ai,
            percentile_driver=ai_pct,
            status_label="ACCELERAZIONE"
        )

        # --- F. Altri Rischi Antropogenici Latenti ---
        b_oth = BASELINE_100Y["other_anthropogenic"]
        p100_oth = b_oth * systemic_multiplier
        tf_oth = TEMPORAL_FACTORS["other_anthropogenic"]
        p50_oth = p100_oth * tf_oth["50y"]
        p10_oth = p100_oth * tf_oth["10y"]
        p5_oth = p100_oth * tf_oth["5y"]
        p1_oth = p100_oth * tf_oth["1y"]

        category_breakdowns["other_anthropogenic"] = CategoryRiskBreakdown(
            category_id="other_anthropogenic",
            category_name="Altri Rischi Antropogenici Non Previsti",
            baseline_100y=b_oth,
            modulator=1.0,
            prob_1y=p1_oth,
            prob_5y=p5_oth,
            prob_10y=p10_oth,
            prob_50y=p50_oth,
            prob_100y=p100_oth,
            percentile_driver=0.50,
            status_label="COSTANTE"
        )

        # 3. Combinazione Complessiva delle Probabilità: P_tot(t) = 1 - Prod(1 - P_i(t))
        def combine_probs(key_prob: str) -> float:
            prod_survive = 1.0
            for cb in category_breakdowns.values():
                val = getattr(cb, key_prob)
                prod_survive *= (1.0 - val)
            return max(0.000001, min(0.999, 1.0 - prod_survive))

        p_tot_1y = combine_probs("prob_1y")
        p_tot_5y = combine_probs("prob_5y")
        p_tot_10y = combine_probs("prob_10y")
        p_tot_50y = combine_probs("prob_50y")
        p_tot_100y = combine_probs("prob_100y")

        # 4. Calcolo delle Baseline di Riferimento Accademiche (Toby Ord)
        def combine_baseline(horizon_key: str) -> float:
            prod_surv = 1.0
            for cat_k, b_val in BASELINE_100Y.items():
                if cat_k == "natural_pandemics":
                    continue
                tf = TEMPORAL_FACTORS[cat_k][horizon_key]
                p_cat = b_val * tf
                prod_surv *= (1.0 - p_cat)
            return 1.0 - prod_surv

        base_1y = combine_baseline("1y")
        base_5y = combine_baseline("5y")
        base_10y = combine_baseline("10y")
        base_50y = combine_baseline("50y")
        base_100y = combine_baseline("100y")

        # 5. METRICHE DI LONGEVITA: Aspettativa Biologica Naturale vs Compressa
        s1 = 1.0 - p_tot_1y
        s5 = 1.0 - p_tot_5y
        s10 = 1.0 - p_tot_10y
        s50 = 1.0 - p_tot_50y
        s100 = 1.0 - p_tot_100y

        area_0_1 = (1.0 + s1) / 2.0 * 1.0
        area_1_5 = (s1 + s5) / 2.0 * 4.0
        area_5_10 = (s5 + s10) / 2.0 * 5.0
        area_10_50 = (s10 + s50) / 2.0 * 40.0
        area_50_100 = (s50 + s100) / 2.0 * 50.0

        lambda_tail = max(0.0005, -math.log(s100) / 100.0)
        tail_area = s100 / lambda_tail

        eff_years = area_0_1 + area_1_5 + area_5_10 + area_10_50 + area_50_100 + tail_area
        eff_days = int(round(eff_years * 365.25))

        # Baseline per delta giorni contingente
        bs1, bs5, bs10, bs50, bs100 = 1.0 - base_1y, 1.0 - base_5y, 1.0 - base_10y, 1.0 - base_50y, 1.0 - base_100y
        b_area = ((1.0 + bs1)/2.0 * 1.0 + (bs1 + bs5)/2.0 * 4.0 + (bs5 + bs10)/2.0 * 5.0 +
                  (bs10 + bs50)/2.0 * 40.0 + (bs50 + bs100)/2.0 * 50.0)
        b_tail = bs100 / max(0.0005, -math.log(bs100) / 100.0)
        b_eff_days = int(round((b_area + b_tail) * 365.25))
        delta_daily_days = eff_days - b_eff_days

        bio_years = 200000.0
        bio_days = int(round(bio_years * 365.25))
        lost_potential_pct = (1.0 - (eff_years / bio_years)) * 100.0

        lifespan_metrics = SpeciesLifespanMetrics(
            biological_baseline_years=bio_years,
            biological_baseline_days=bio_days,
            effective_expected_years=eff_years,
            effective_expected_days=eff_days,
            future_potential_lost_pct=lost_potential_pct,
            daily_delta_days_vs_norm=delta_daily_days
        )

        # Helper quote (odds) e livelli
        def format_odds(p: float) -> str:
            if p <= 0: return "> 1 su 1.000.000"
            one_in = int(round(1.0 / p))
            return f"1 su {one_in:,}".replace(",", ".")

        def get_tier(p: float, horizon: int) -> str:
            if horizon == 100:
                return "CRITICO" if p >= 0.22 else ("ELEVATO" if p >= 0.15 else ("MODERATO" if p >= 0.08 else "BASSO"))
            elif horizon == 50:
                return "CRITICO" if p >= 0.18 else ("ELEVATO" if p >= 0.11 else ("MODERATO" if p >= 0.05 else "BASSO"))
            elif horizon == 10:
                return "CRITICO" if p >= 0.08 else ("ELEVATO" if p >= 0.04 else ("MODERATO" if p >= 0.015 else "BASSO"))
            elif horizon == 5:
                return "CRITICO" if p >= 0.03 else ("ELEVATO" if p >= 0.015 else ("MODERATO" if p >= 0.006 else "BASSO"))
            else: # 1 anno
                return "CRITICO" if p >= 0.005 else ("ELEVATO" if p >= 0.002 else ("MODERATO" if p >= 0.0008 else "BASSO"))

        horizons = {
            "1_year": HorizonProbability(
                horizon_years=1,
                probability=p_tot_1y,
                percentage_str=f"{p_tot_1y * 100:.3f}%",
                odds_str=format_odds(p_tot_1y),
                delta_vs_baseline=p_tot_1y - base_1y,
                risk_tier=get_tier(p_tot_1y, 1)
            ),
            "5_years": HorizonProbability(
                horizon_years=5,
                probability=p_tot_5y,
                percentage_str=f"{p_tot_5y * 100:.2f}%",
                odds_str=format_odds(p_tot_5y),
                delta_vs_baseline=p_tot_5y - base_5y,
                risk_tier=get_tier(p_tot_5y, 5)
            ),
            "10_years": HorizonProbability(
                horizon_years=10,
                probability=p_tot_10y,
                percentage_str=f"{p_tot_10y * 100:.2f}%",
                odds_str=format_odds(p_tot_10y),
                delta_vs_baseline=p_tot_10y - base_10y,
                risk_tier=get_tier(p_tot_10y, 10)
            ),
            "50_years": HorizonProbability(
                horizon_years=50,
                probability=p_tot_50y,
                percentage_str=f"{p_tot_50y * 100:.2f}%",
                odds_str=format_odds(p_tot_50y),
                delta_vs_baseline=p_tot_50y - base_50y,
                risk_tier=get_tier(p_tot_50y, 50)
            ),
            "100_years": HorizonProbability(
                horizon_years=100,
                probability=p_tot_100y,
                percentage_str=f"{p_tot_100y * 100:.2f}%",
                odds_str=format_odds(p_tot_100y),
                delta_vs_baseline=p_tot_100y - base_100y,
                risk_tier=get_tier(p_tot_100y, 100)
            )
        }

        sign = "+" if delta_daily_days >= 0 else ""
        verdict = (
            f"Aspettativa biologica naturale della specie: ~{int(bio_years):,} anni (~{bio_days:,} giorni). "
            f"Al tasso di rischio antropogenico attuale, l'aspettativa di vita residua e compressa a ~{eff_days:,} giorni (~{eff_years:.0f} anni), "
            f"con un'erosione del {lost_potential_pct:.1f}% del futuro potenziale naturale della specie umana. "
            f"Probabilita di estinzione sui 5 orizzonti: 1y: {horizons['1_year'].percentage_str}, "
            f"5y: {horizons['5_years'].percentage_str}, 10y: {horizons['10_years'].percentage_str}, "
            f"50y: {horizons['50_years'].percentage_str}, 100y: {horizons['100_years'].percentage_str}."
        ).replace(",", ".")

        return ExtinctionLifespanResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            lifespan=lifespan_metrics,
            systemic_fragility_multiplier=systemic_multiplier,
            horizons=horizons,
            categories=category_breakdowns,
            scientific_sources=SCIENTIFIC_SOURCES,
            summary_verdict=verdict
        )
