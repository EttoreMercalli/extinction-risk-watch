#!/usr/bin/env python3
"""
CLI Tool per la verifica automatica della disponibilità e integrità delle sorgenti dati target.
Utilizzo:
    python verify_sources.py                 # Verifica tutte le sorgenti di livello A (gratuite e libere)
    python verify_sources.py --all           # Verifica tutte le sorgenti nel catalogo (A, B, C)
    python verify_sources.py --category AI   # Verifica solo le sorgenti di una specifica categoria
    python verify_sources.py --id cboe_vix_history # Verifica una singola sorgente
"""

import sys
import argparse
from pathlib import Path

from src.config import load_sources, filter_sources
from src.verifier import SourceVerifier
from src.reporter import VerificationReporter

def main():
    parser = argparse.ArgumentParser(
        description="Strumento di verifica e testing per le sorgenti dati del Doomsday Index."
    )
    parser.add_argument(
        "--level",
        type=str,
        default="A",
        help="Filtra per livello di accesso: 'A' (libere), 'B' (registrazione/chiave), 'C' (strutturali/annuali), 'ALL'. Default: 'A'."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scorciatoia per testare tutte le sorgenti (equivale a --level ALL)."
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filtra le sorgenti per categoria (es. 'Clima', 'Pandemie', 'Cosmici', 'IA', 'Mercati')."
    )
    parser.add_argument(
        "--id",
        type=str,
        default=None,
        help="Verifica una singola sorgente specificandone l'ID (es. 'nasa_sentry')."
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=25.0,
        help="Timeout per ciascuna richiesta HTTP in secondi (default: 25.0)."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Numero di thread concorrenti per il download parallelo (default: 5)."
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Disabilita la scrittura dei report su file JSON e Markdown."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Cartella di destinazione per i report generati (default: 'reports')."
    )

    args = parser.parse_args()

    # Determina il livello
    target_level = "ALL" if args.all else args.level

    # Carica la configurazione
    try:
        all_sources = load_sources()
    except Exception as e:
        print(f"[ERRORE] Impossibile caricare il catalogo sources.json: {e}", file=sys.stderr)
        sys.exit(1)

    # Applica i filtri
    sources_to_check = filter_sources(
        sources=all_sources,
        level=target_level,
        category=args.category,
        source_id=args.id
    )

    if not sources_to_check:
        print(f"[AVVISO] Nessuna sorgente corrisponde ai criteri specificati (Livello: {target_level}, Categoria: {args.category}, ID: {args.id})")
        sys.exit(0)

    print(f"-> Avvio verifica per {len(sources_to_check)} sorgente/i target...")
    print(f"   (Filtri: Livello={target_level}, Categoria={args.category or 'Tutte'}, Timeout={args.timeout}s, Workers={args.workers})")

    # Inizializza motore di verifica
    verifier = SourceVerifier(timeout_sec=args.timeout)
    results = verifier.verify_all(sources=sources_to_check, max_workers=args.workers)

    # Inizializza reporter
    reporter = VerificationReporter(output_dir=Path(args.output_dir))
    reporter.print_terminal_summary(results)

    # Esporta report se richiesto
    if not args.no_export:
        json_path = reporter.export_json(results)
        md_path = reporter.export_markdown(results)
        print(f"Report JSON salvato in:     {json_path}")
        print(f"Report Markdown salvato in: {md_path}\n")

    # Exit code basato su fallimenti
    failures = sum(1 for r in results if r.status == "FAIL")
    if failures > 0:
        sys.exit(2)
    sys.exit(0)

if __name__ == "__main__":
    main()
