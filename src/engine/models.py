"""
Modelli dati per l'Algoritmo di Calcolo Quantitativo del Rischio di Estinzione Umana.
Modello basato sul contrasto tra:
1. Aspettativa Biologica Naturale della Specie (~200.000 anni / ~73 milioni di giorni)
2. Compressione Antropogenica ed Ecologica del Rischio (1, 5, 10, 50, 100 anni)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

@dataclass
class ScientificSourceRef:
    """Riferimento accademico/scientifico citabile nella UI."""
    title: str
    authors: str
    year: int
    institution: str
    scope: str  # "Biologico / Decadimento Genetico" oppure "Rischio Antropogenico / Tecnologico"
    url: str

@dataclass
class HorizonProbability:
    """Probabilità stimata per un dato orizzonte temporale (1, 5, 10, 50 o 100 anni)."""
    horizon_years: int
    probability: float          # Valore decimale (es. 0.0494)
    percentage_str: str         # Formattato in percentuale (es. "4.94%")
    odds_str: str               # Formattato in probabilità frazionaria (es. "1 su 20")
    delta_vs_baseline: float    # Differenza rispetto alla baseline accademica (+/- float)
    risk_tier: str              # Livello: BASSO, MODERATO, ELEVATO, CRITICO, ESTREMO

@dataclass
class CategoryRiskBreakdown:
    """Scomposizione del rischio per singola macrocategoria sui diversi orizzonti."""
    category_id: str
    category_name: str
    baseline_100y: float
    modulator: float            # Modulatore dinamico attuale (es. 1.39 = +39%)
    prob_1y: float
    prob_5y: float
    prob_10y: float
    prob_50y: float
    prob_100y: float
    percentile_driver: float    # Percentile medio degli indicatori reali della categoria
    status_label: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_id": self.category_id,
            "category_name": self.category_name,
            "baseline_100y": round(self.baseline_100y, 5),
            "modulator": round(self.modulator, 3),
            "prob_1y": round(self.prob_1y, 6),
            "prob_5y": round(self.prob_5y, 5),
            "prob_10y": round(self.prob_10y, 5),
            "prob_50y": round(self.prob_50y, 4),
            "prob_100y": round(self.prob_100y, 4),
            "percentile_driver": round(self.percentile_driver, 3),
            "status_label": self.status_label
        }

@dataclass
class SpeciesLifespanMetrics:
    """Metriche dell'aspettativa di vita naturale vs compressa dall'uomo."""
    biological_baseline_years: float = 200000.0     # ~200.000 anni (longevità genetica naturale stimata)
    biological_baseline_days: int = 73050000        # ~73.050.000 giorni
    effective_expected_years: float = 574.6         # Anni effettivi attesi al tasso di rischio attuale
    effective_expected_days: int = 209877           # Giorni effettivi attesi al tasso di rischio attuale
    future_potential_lost_pct: float = 99.71        # Percentuale di futuro potenziale eroso da rischi antropogenici
    daily_delta_days_vs_norm: int = 2415            # Giorni guadagnati/persi oggi rispetto alla norma per fluttuazioni contingenti

    def to_dict(self) -> Dict[str, Any]:
        return {
            "biological_baseline_years": self.biological_baseline_years,
            "biological_baseline_days": self.biological_baseline_days,
            "effective_expected_years": round(self.effective_expected_years, 1),
            "effective_expected_days": self.effective_expected_days,
            "future_potential_lost_pct": round(self.future_potential_lost_pct, 2),
            "daily_delta_days_vs_norm": self.daily_delta_days_vs_norm
        }

@dataclass
class ExtinctionLifespanResult:
    """Risultato complessivo della stima probabilistica dell'aspettativa di vita della specie umana."""
    timestamp: str
    lifespan: SpeciesLifespanMetrics
    systemic_fragility_multiplier: float
    horizons: Dict[str, HorizonProbability]  # 1_year, 5_years, 10_years, 50_years, 100_years
    categories: Dict[str, CategoryRiskBreakdown]
    scientific_sources: List[ScientificSourceRef]
    summary_verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "lifespan": self.lifespan.to_dict(),
            "systemic_fragility_multiplier": round(self.systemic_fragility_multiplier, 3),
            "horizons": {
                k: {
                    "horizon_years": v.horizon_years,
                    "probability": round(v.probability, 6),
                    "percentage_str": v.percentage_str,
                    "odds_str": v.odds_str,
                    "delta_vs_baseline": round(v.delta_vs_baseline, 6),
                    "risk_tier": v.risk_tier
                }
                for k, v in self.horizons.items()
            },
            "categories": {k: v.to_dict() for k, v in self.categories.items()},
            "scientific_sources": [asdict(s) for s in self.scientific_sources],
            "summary_verdict": self.summary_verdict
        }
