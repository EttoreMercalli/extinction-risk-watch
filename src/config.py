"""
Gestione e caricamento del file di configurazione sources.json.
"""

import json
from pathlib import Path
from typing import List, Optional
from src.models import SourceConfig

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "sources.json"

def load_sources(config_path: Optional[Path] = None) -> List[SourceConfig]:
    """Carica tutte le sorgenti configurate in sources.json."""
    path = config_path or DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Configurazione non trovata al percorso: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_sources = data.get("sources", [])
    return [SourceConfig.from_dict(item) for item in raw_sources]

def filter_sources(
    sources: List[SourceConfig],
    level: Optional[str] = None,
    category: Optional[str] = None,
    source_id: Optional[str] = None,
    only_enabled: bool = False
) -> List[SourceConfig]:
    """Filtra le sorgenti per livello (A/B/C), categoria o identificativo."""
    filtered = sources

    if only_enabled:
        filtered = [s for s in filtered if s.enabled]

    if level and level.upper() != "ALL":
        filtered = [s for s in filtered if s.level.upper() == level.upper()]

    if category:
        filtered = [s for s in filtered if category.lower() in s.category.lower()]

    if source_id:
        filtered = [s for s in filtered if s.id.lower() == source_id.lower()]

    return filtered
