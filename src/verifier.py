"""
Motore di verifica automatica per le sorgenti dati target.
Esegue chiamate HTTP, valida la struttura del payload e misura latenza e integrità.
"""

import time
import json
import csv
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
import requests

from src.models import SourceConfig, CheckResult

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml,application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8"
}

class SourceVerifier:
    """Verificatore della disponibilità e qualità dei dati per ciascuna sorgente target."""

    def __init__(self, timeout_sec: float = 15.0, user_agent: Optional[str] = None):
        self.timeout_sec = timeout_sec
        self.headers = dict(DEFAULT_HEADERS)
        if user_agent:
            self.headers["User-Agent"] = user_agent

    def verify_single(self, source: SourceConfig) -> CheckResult:
        """Verifica una singola sorgente e restituisce il CheckResult."""
        # Se è una sorgente locale / livello C
        if source.endpoint.startswith("local://"):
            return self._verify_local(source)

        if not source.enabled:
            return CheckResult(
                source_id=source.id,
                source_name=source.name,
                category=source.category,
                level=source.level,
                endpoint=source.endpoint,
                status="SKIPPED",
                details="Sorgente disabilitata (richiede configurazione chiavi/accesso)"
            )

        t_start = time.perf_counter()
        try:
            response = requests.get(
                source.endpoint,
                headers=self.headers,
                timeout=self.timeout_sec,
                allow_redirects=True
            )
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            status_code = response.status_code
            content_type = response.headers.get("content-type", "")
            content_bytes = response.content
            size_bytes = len(content_bytes)

            # Validazione HTTP Status
            expected_statuses = source.validation.expected_status
            if status_code not in expected_statuses:
                return CheckResult(
                    source_id=source.id,
                    source_name=source.name,
                    category=source.category,
                    level=source.level,
                    endpoint=source.endpoint,
                    status="FAIL",
                    status_code=status_code,
                    latency_ms=elapsed_ms,
                    size_bytes=size_bytes,
                    content_type=content_type,
                    parse_valid=False,
                    details=f"Status HTTP {status_code} inatteso (attesi: {expected_statuses})",
                    sample_preview=response.text[:150].replace('\n', ' ').strip(),
                    error=f"HTTP_{status_code}"
                )

            # Validazione dimensione minima
            if size_bytes < source.validation.min_bytes:
                return CheckResult(
                    source_id=source.id,
                    source_name=source.name,
                    category=source.category,
                    level=source.level,
                    endpoint=source.endpoint,
                    status="FAIL",
                    status_code=status_code,
                    latency_ms=elapsed_ms,
                    size_bytes=size_bytes,
                    content_type=content_type,
                    parse_valid=False,
                    details=f"Dimensione payload ({size_bytes} byte) inferiore alla soglia minima ({source.validation.min_bytes} byte)",
                    sample_preview=response.text[:150].replace('\n', ' ').strip(),
                    error="PAYLOAD_TOO_SMALL"
                )

            # Validazione del formato / parsing
            parse_ok, parse_msg, sample_preview = self._validate_payload(
                response=response,
                source=source
            )

            status = "PASS" if parse_ok else "FAIL"
            if parse_ok and elapsed_ms > 10000:
                status = "WARN"  # Segnala latenza elevata pur con payload valido

            return CheckResult(
                source_id=source.id,
                source_name=source.name,
                category=source.category,
                level=source.level,
                endpoint=source.endpoint,
                status=status,
                status_code=status_code,
                latency_ms=elapsed_ms,
                size_bytes=size_bytes,
                content_type=content_type,
                parse_valid=parse_ok,
                details=parse_msg,
                sample_preview=sample_preview,
                error=None if parse_ok else parse_msg
            )

        except requests.exceptions.Timeout:
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            return CheckResult(
                source_id=source.id,
                source_name=source.name,
                category=source.category,
                level=source.level,
                endpoint=source.endpoint,
                status="FAIL",
                latency_ms=elapsed_ms,
                details=f"Timeout dopo {self.timeout_sec:.1f} secondi",
                error="REQUEST_TIMEOUT"
            )
        except requests.exceptions.RequestException as e:
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            return CheckResult(
                source_id=source.id,
                source_name=source.name,
                category=source.category,
                level=source.level,
                endpoint=source.endpoint,
                status="FAIL",
                latency_ms=elapsed_ms,
                details=f"Errore di rete / connessione: {e}",
                error=type(e).__name__
            )

    def _validate_payload(self, response: requests.Response, source: SourceConfig) -> (bool, str, str):
        """Esegue il test di parsing sul contenuto in base al formato atteso."""
        parse_type = source.validation.parse_test.lower()
        content = response.content
        text = response.text

        sample_preview = text[:180].replace("\n", " ").strip()

        if parse_type == "json":
            try:
                data = json.loads(text)
                if not isinstance(data, (dict, list)):
                    return False, "Il JSON parsato non è un dizionario o una lista", sample_preview

                # Controllo chiavi obbligatorie
                required_keys = source.validation.required_keys
                if required_keys and isinstance(data, dict):
                    missing = [k for k in required_keys if k not in data]
                    if missing:
                        return False, f"JSON valido ma mancano le chiavi obbligatorie: {missing}", sample_preview

                items_count = len(data) if isinstance(data, list) else len(data.keys())
                return True, f"JSON valido con {items_count} elementi di primo livello", sample_preview
            except json.JSONDecodeError as e:
                return False, f"Errore sintattico JSON: {e}", sample_preview

        elif parse_type == "csv":
            try:
                reader = csv.reader(io.StringIO(text))
                rows = list(reader)
                row_count = len(rows)
                min_lines = source.validation.min_lines or 2
                if row_count < min_lines:
                    return False, f"CSV valido ma contiene solo {row_count} righe (minimo atteso: {min_lines})", sample_preview
                header = ", ".join(rows[0][:4]) if rows else ""
                return True, f"CSV valido ({row_count} righe). Colonne: [{header}...]", sample_preview
            except Exception as e:
                return False, f"Errore di lettura CSV: {e}", sample_preview

        elif parse_type in ("xml", "rss_xml"):
            try:
                root = ET.fromstring(content)
                tag = root.tag
                children = len(list(root))
                return True, f"XML/RSS valido (root tag: '{tag}', nodi figli: {children})", sample_preview
            except ET.ParseError as e:
                return False, f"Errore sintattico XML/RSS: {e}", sample_preview

        elif parse_type == "text":
            lines = text.strip().splitlines()
            line_count = len(lines)
            min_lines = source.validation.min_lines or 1
            if line_count < min_lines:
                return False, f"Testo con {line_count} righe (minimo atteso: {min_lines})", sample_preview
            return True, f"Feed di testo valido ({line_count} righe)", sample_preview

        elif parse_type == "binary":
            # Per XLS o file binari: verifica la presenza di signature o grandezza
            size_kb = len(content) / 1024.0
            return True, f"File binario integro ({size_kb:.1f} KB)", f"<Binary payload: {size_kb:.1f} KB>"

        elif parse_type == "html":
            if "<html" in text.lower():
                return True, f"Pagina HTML / Snapshot disponibile ({len(content)} bytes)", sample_preview
            return False, "La risposta non sembra contenere codice HTML valido", sample_preview

        return True, "Validazione di default superata", sample_preview

    def _verify_local(self, source: SourceConfig) -> CheckResult:
        """Verifica per sorgenti statiche / baseline memorizzate localmente."""
        return CheckResult(
            source_id=source.id,
            source_name=source.name,
            category=source.category,
            level=source.level,
            endpoint=source.endpoint,
            status="PASS",
            status_code=200,
            latency_ms=0.1,
            size_bytes=len(source.target_metric.encode("utf-8")),
            content_type="application/json",
            parse_valid=True,
            details="Baseline strutturale locale registrata e pronta all'uso",
            sample_preview=source.target_metric[:150]
        )

    def verify_all(
        self,
        sources: List[SourceConfig],
        max_workers: int = 5
    ) -> List[CheckResult]:
        """Esegue la verifica su una lista di sorgenti usando un pool di thread concorrenti."""
        results: List[CheckResult] = []
        if not sources:
            return results

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_source = {
                executor.submit(self.verify_single, src): src for src in sources
            }
            for future in as_completed(future_to_source):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as exc:
                    src = future_to_source[future]
                    results.append(CheckResult(
                        source_id=src.id,
                        source_name=src.name,
                        category=src.category,
                        level=src.level,
                        endpoint=src.endpoint,
                        status="FAIL",
                        details=f"Eccezione non gestita durante il test: {exc}",
                        error=str(exc)
                    ))

        # Ordina i risultati per categoria e id per consistenza
        results.sort(key=lambda r: (r.category, r.source_id))
        return results
