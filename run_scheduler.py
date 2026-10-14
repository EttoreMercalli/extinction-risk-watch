#!/usr/bin/env python3
"""
Daemon / Servizio di Aggiornamento Continuo (Extinction Risk Watch).
Esegue il refresh delle fonti veloci e ricalcola le probabilità di estinzione
ogni 10 minuti (o intervallo specificato), aggiornando atomicamente public/data/index.json.

Utilizzo:
    python run_scheduler.py                     # Avvia il daemon (default: ogni 10 minuti)
    python run_scheduler.py --interval 5        # Aggiorna ogni 5 minuti
    python run_scheduler.py --once              # Esegue un singolo ciclo immediato ed esce
"""

import sys
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

# Compatibilità encoding UTF-8 console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.scheduler import TieredDataUpdater

# Configurazione logging su console e su file
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "scheduler.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ExtinctionScheduler")

def main():
    parser = argparse.ArgumentParser(description="Daemon di aggiornamento continuo per Extinction Risk Watch.")
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Intervallo di aggiornamento in minuti (default: 10)."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Esegue un solo ciclo di aggiornamento ed esce immediatamente."
    )
    args = parser.parse_args()

    interval_sec = args.interval * 60

    print("\n" + "=" * 80)
    print("      EXTINCTION RISK WATCH - SERVIZIO DI AGGIORNAMENTO CONTINUO")
    print("=" * 80)
    print(f"   • Cadenza ciclo:       ogni {args.interval} minuti ({interval_sec} secondi)")
    print(f"   • File di output:      public/data/index.json (scrittura atomica)")
    print(f"   • Registro log:        {log_file.resolve()}")
    print("=" * 80 + "\n")

    updater = TieredDataUpdater()
    updater.load_initial_cache()

    cycle_count = 0

    try:
        while True:
            cycle_count += 1
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"--- [CICLO #{cycle_count}] Inizio aggiornamento alle {now_str} ---")

            t_start = time.time()
            try:
                result = updater.run_update_cycle()
                elapsed = time.time() - t_start

                days_str = f"{result.lifespan.effective_expected_days:,}".replace(",", ".")
                p1 = result.horizons['1_year'].percentage_str
                p10 = result.horizons['10_years'].percentage_str
                p100 = result.horizons['100_years'].percentage_str

                logger.info(
                    f"Ciclo #{cycle_count} completato in {elapsed:.2f}s | "
                    f"Giorni rimasti: {days_str} | 1y: {p1} | 10y: {p10} | 100y: {p100}"
                )
            except Exception as e:
                logger.error(f"Errore durante il ciclo #{cycle_count}: {e}", exc_info=True)

            if args.once:
                logger.info("Modalità --once completata. Uscita.")
                break

            next_run = datetime.fromtimestamp(time.time() + interval_sec).strftime("%H:%M:%S")
            logger.info(f"In attesa del prossimo ciclo alle {next_run} ({args.interval} min)... Premi CTRL+C per arrestare.\n")
            time.sleep(interval_sec)

    except KeyboardInterrupt:
        logger.info("Servizio di aggiornamento interrotto manualmente dall'utente.")

if __name__ == "__main__":
    main()
