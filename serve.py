#!/usr/bin/env python3
"""
Server web locale leggero per visualizzare l'anteprima del sito Extinction Risk Watch.
Utilizzo:
    python serve.py
    (poi apri il browser su http://localhost:8080)
"""

import sys
import os
import http.server
import socketserver
import webbrowser
from pathlib import Path

# Compatibilità encoding UTF-8 console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PORT = 8080
PUBLIC_DIR = Path(__file__).resolve().parent / "public"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def end_headers(self):
        # Disabilita la cache locale per sviluppo in tempo reale
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

def main():
    if not (PUBLIC_DIR / "data" / "index.json").exists():
        print("-> File public/data/index.json non trovato. Eseguo la pipeline di compilazione...")
        from build_site_data import build_production_site_data
        build_production_site_data()

    with socketserver.TCPServer(("127.0.0.1", PORT), CustomHandler) as httpd:
        url = f"http://127.0.0.1:{PORT}"
        print("\n" + "=" * 70)
        print("   EXTINCTION RISK WATCH - ANTEPRIMA LOCALE ATTIVA")
        print("=" * 70)
        print(f"   Indirizzo: {url}")
        print("   Premi CTRL+C per arrestare il server.")
        print("=" * 70 + "\n")

        # Apri il browser automaticamente
        try:
            webbrowser.open(url)
        except Exception:
            pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer arrestato.")

if __name__ == "__main__":
    main()
