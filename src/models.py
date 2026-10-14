"""
Modelli dati per la configurazione delle sorgenti e i risultati dei test di verifica.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class ValidationRule:
    expected_status: List[int] = field(default_factory=lambda: [200])
    min_bytes: int = 100
    parse_test: str = "text"
    required_keys: Optional[List[str]] = None
    min_lines: Optional[int] = None

@dataclass
class SourceConfig:
    id: str
    name: str
    category: str
    level: str  # "A", "B", "C"
    enabled: bool
    endpoint: str
    method: str
    format: str  # "json", "csv", "text", "rss_xml", "xls", "html"
    frequency: str
    target_metric: str
    description: str
    validation: ValidationRule
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceConfig":
        val_data = data.get("validation", {})
        val_rule = ValidationRule(
            expected_status=val_data.get("expected_status", [200]),
            min_bytes=val_data.get("min_bytes", 100),
            parse_test=val_data.get("parse_test", "text"),
            required_keys=val_data.get("required_keys"),
            min_lines=val_data.get("min_lines")
        )
        return cls(
            id=data["id"],
            name=data["name"],
            category=data.get("category", "Uncategorized"),
            level=data.get("level", "A"),
            enabled=data.get("enabled", True),
            endpoint=data["endpoint"],
            method=data.get("method", "GET"),
            format=data.get("format", "json"),
            frequency=data.get("frequency", "daily"),
            target_metric=data.get("target_metric", ""),
            description=data.get("description", ""),
            validation=val_rule,
            notes=data.get("notes", "")
        )

@dataclass
class CheckResult:
    source_id: str
    source_name: str
    category: str
    level: str
    endpoint: str
    status: str  # "PASS", "WARN", "FAIL", "SKIPPED"
    status_code: Optional[int] = None
    latency_ms: float = 0.0
    size_bytes: int = 0
    content_type: str = ""
    parse_valid: bool = False
    details: str = ""
    sample_preview: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "category": self.category,
            "level": self.level,
            "endpoint": self.endpoint,
            "status": self.status,
            "status_code": self.status_code,
            "latency_ms": round(self.latency_ms, 2),
            "size_bytes": self.size_bytes,
            "content_type": self.content_type,
            "parse_valid": self.parse_valid,
            "details": self.details,
            "sample_preview": self.sample_preview,
            "error": self.error
        }
