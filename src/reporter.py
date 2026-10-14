"""
Modulo di reporting: genera report formattati per terminale, file JSON e file Markdown.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from src.models import CheckResult

class VerificationReporter:
    """Formatta ed esporta i risultati dei test di verifica."""

    def __init__(self, output_dir: Path = Path("reports")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def print_terminal_summary(self, results: List[CheckResult]):
        """Stampa una tabella riepilogativa chiara a terminale."""
        print("\n" + "=" * 90)
        print("          EXTINCTION RISK WATCH - REPORT DISPONIBILITA' SORGENTI DATI")
        print("=" * 90)

        header = f"{'STATO':<7} | {'ID SORGENTE':<23} | {'CATEGORIA':<25} | {'LATENZA':<8} | {'DIMENSIONE':<10}"
        print(header)
        print("-" * 90)

        for r in results:
            status_tag = f"[{r.status}]"
            latency = f"{r.latency_ms:.0f}ms" if r.latency_ms > 0 else "--"
            size_kb = f"{r.size_bytes / 1024:.1f} KB" if r.size_bytes > 0 else "--"
            print(f"{status_tag:<7} | {r.source_id:<23} | {r.category[:25]:<25} | {latency:<8} | {size_kb:<10}")

        print("-" * 90)
        summary = self._compute_summary(results)
        print(f"TOTALE: {summary['total']} | PASSATI: {summary['pass']} | WARN: {summary['warn']} | FALLITI: {summary['fail']} | SKIPPED: {summary['skipped']}")
        print(f"Tasso di Successo Operativo: {summary['health_score']:.1f}%")
        print("=" * 90 + "\n")

    def export_json(self, results: List[CheckResult], filename: str = "verification_report.json") -> Path:
        """Esporta il report completo in formato JSON."""
        summary = self._compute_summary(results)
        report_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "results": [r.to_dict() for r in results]
        }
        dest = self.output_dir / filename
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        return dest

    def export_markdown(self, results: List[CheckResult], filename: str = "verification_report.md") -> Path:
        """Esporta un report descrittivo in formato Markdown."""
        summary = self._compute_summary(results)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = []
        md.append("# Report di Verifica Automatizzabilità delle Fonti Dati\n")
        md.append(f"> Generato il: **{now_str}**  \n")
        md.append(f"> **Tasso di Successo Operativo:** **`{summary['health_score']:.1f}%`**\n")
        md.append("\n## Riepilogo Globale\n")
        md.append(f"- **Sorgenti Verificate:** `{summary['total']}`")
        md.append(f"- **Disponibili e Valide (`PASS`):** `{summary['pass']}`")
        md.append(f"- **Con Avvisi (`WARN`):** `{summary['warn']}`")
        md.append(f"- **Non Raggiungibili / Errore (`FAIL`):** `{summary['fail']}`")
        md.append(f"- **In Attesa di Credenziali (`SKIPPED`):** `{summary['skipped']}`")
        md.append(f"- **Latenza Media:** `{summary['avg_latency_ms']:.1f} ms`\n")

        md.append("## Dettaglio per Sorgente\n")
        md.append("| Stato | ID Sorgente | Nome | Categoria | Latenza | Dimensione | Validazione | Note / Dettagli |")
        md.append("| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :--- |")

        for r in results:
            badge = "✅ PASS" if r.status == "PASS" else ("⚠️ WARN" if r.status == "WARN" else ("⏭️ SKIP" if r.status == "SKIPPED" else "❌ FAIL"))
            latency = f"{r.latency_ms:.0f} ms" if r.latency_ms > 0 else "--"
            size = f"{r.size_bytes / 1024:.1f} KB" if r.size_bytes > 0 else "--"
            valid = "Sì" if r.parse_valid else "No"
            details = r.details.replace("|", "/")
            md.append(f"| {badge} | `{r.source_id}` | {r.source_name} | {r.category} | {latency} | {size} | {valid} | {details} |")

        dest = self.output_dir / filename
        with open(dest, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
        return dest

    def _compute_summary(self, results: List[CheckResult]) -> Dict[str, Any]:
        total = len(results)
        passed = sum(1 for r in results if r.status == "PASS")
        warn = sum(1 for r in results if r.status == "WARN")
        fail = sum(1 for r in results if r.status == "FAIL")
        skipped = sum(1 for r in results if r.status == "SKIPPED")

        active_count = total - skipped
        health = ((passed + warn) / active_count * 100.0) if active_count > 0 else 0.0

        latencies = [r.latency_ms for r in results if r.latency_ms > 0]
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

        return {
            "total": total,
            "pass": passed,
            "warn": warn,
            "fail": fail,
            "skipped": skipped,
            "health_score": round(health, 1),
            "avg_latency_ms": round(avg_lat, 1)
        }
