"""
Modelli dati per la rappresentazione standardizzata di:
1. Formato Tabella (Serie temporali e indicatori quantitativi per grafici e algoritmi)
2. Formato Testuale (Notizie, allerte ed eventi per il feed della UI)
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

@dataclass
class TimeSeriesRecord:
    """Singolo punto di una serie storica temporale per grafici."""
    date: str       # Formato ISO YYYY-MM-DD
    value: float    # Valore numerico normalizzato

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class IndicatorSummary:
    """Riepilogo statistico di un indicatore chiave per l'algoritmo e le card della UI."""
    metric_id: str
    name: str
    unit: str
    current_value: float
    current_date: str
    total_records: int
    min_value: float
    max_value: float
    mean_value: float
    percentile_5y: float   # Percentile rispetto agli ultimi 5 anni (0.0 -> 1.0)
    sparkline: List[float] = field(default_factory=list) # Ultimi 30 valori per grafici compatti

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "unit": self.unit,
            "current_value": round(self.current_value, 2),
            "current_date": self.current_date,
            "total_records": self.total_records,
            "min_value": round(self.min_value, 2),
            "max_value": round(self.max_value, 2),
            "mean_value": round(self.mean_value, 2),
            "percentile_5y": round(self.percentile_5y, 3),
            "sparkline": [round(v, 2) for v in self.sparkline]
        }

@dataclass
class NewsItem:
    """Articolo o notifica per il feed delle notizie tematiche della UI."""
    title: str
    date: str
    source: str
    url: str
    summary: str
    category: str
    severity: int = 1  # Scala 1-5 (1: Notizia informativa, 5: Crisi critica globale)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CategoryPayload:
    """Contenitore per una macrocategoria comprendente dati tabella (numeri) e testo (notizie)."""
    category_id: str
    category_name: str
    indicators: Dict[str, IndicatorSummary] = field(default_factory=dict)
    time_series: Dict[str, List[TimeSeriesRecord]] = field(default_factory=dict)
    news_items: List[NewsItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_id": self.category_id,
            "category_name": self.category_name,
            "indicators": {k: v.to_dict() for k, v in self.indicators.items()},
            "time_series": {
                k: [pt.to_dict() for pt in v] for k, v in self.time_series.items()
            },
            "news_items": [n.to_dict() for n in self.news_items]
        }
