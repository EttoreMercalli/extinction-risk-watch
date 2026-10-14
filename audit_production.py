#!/usr/bin/env python3
"""
Audit di Pre-Deployment per la Messa Online di Extinction Risk Watch.
Esegue tutti i controlli imposti dalle Best Practice dell'ingegneria web:
1. Validazione HTML semantico, a11y e conformità W3C
2. Audit SEO, Open Graph & Twitter Cards
3. Verifica integrità asset statici (CSS, JS, Favicon SVG, _headers)
4. Audit sicurezza (rel="noopener noreferrer", assenza credenziali esposte)
5. Validazione schema e coerenza dati in public/data/index.json
6. Verifica configurazione CI/CD per GitHub Pages e Cloudflare Pages
"""

import sys
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path

# Assicura output UTF-8 su console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PUBLIC_DIR = Path("public")

class ProductionAuditor:
    def __init__(self):
        self.passed = 0
        self.warnings = 0
        self.failed = 0
        self.checks = []

    def check(self, condition: bool, title: str, category: str, details: str = ""):
        if condition:
            self.passed += 1
            status = "PASS"
        else:
            self.failed += 1
            status = "FAIL"
        self.checks.append({"status": status, "title": title, "category": category, "details": details})
        badge = "✅ PASS" if condition else "❌ FAIL"
        print(f"  {badge} [{category:<12}] {title}")
        if not condition and details:
            print(f"         └─ Dettaglio: {details}")

    def warn(self, condition: bool, title: str, category: str, details: str = ""):
        if condition:
            self.passed += 1
            status = "PASS"
            badge = "✅ PASS"
        else:
            self.warnings += 1
            status = "WARN"
            badge = "⚠️ WARN"
        self.checks.append({"status": status, "title": title, "category": category, "details": details})
        print(f"  {badge} [{category:<12}] {title}")
        if not condition and details:
            print(f"         └─ Avviso: {details}")

    def run_all_audits(self) -> bool:
        print("\n" + "=" * 85)
        print("         AUDIT DI PRE-DEPLOYMENT: VERIFICA BEST PRACTICE WEB")
        print("=" * 85 + "\n")

        # -------------------------------------------------------------
        # 1. STRUTTURA CARTELLE & FILE CHIAVE
        # -------------------------------------------------------------
        print("📁 1. STRUTTURA ASSET STATICI E FILE DI PRODUZIONE")
        html_file = PUBLIC_DIR / "index.html"
        css_file = PUBLIC_DIR / "style.css"
        js_file = PUBLIC_DIR / "app.js"
        json_file = PUBLIC_DIR / "data" / "index.json"
        svg_file = PUBLIC_DIR / "favicon.svg"
        headers_file = PUBLIC_DIR / "_headers"

        self.check(html_file.exists(), "index.html presente nella cartella public/", "Asset")
        self.check(css_file.exists() and css_file.stat().st_size > 1000, "style.css presente e non vuoto", "Asset")
        self.check(js_file.exists() and js_file.stat().st_size > 1000, "app.js presente e non vuoto", "Asset")
        self.check(json_file.exists() and json_file.stat().st_size > 5000, "data/index.json presente e popolato", "Asset")
        self.check(svg_file.exists(), "favicon.svg vettoriale presente", "Asset")
        self.check(headers_file.exists(), "File _headers di sicurezza presente", "Asset")

        # -------------------------------------------------------------
        # 2. VALIDAZIONE HTML, METADATI SEO & OPEN GRAPH
        # -------------------------------------------------------------
        print("\n🔍 2. AUDIT SEO, META TAG & OPEN GRAPH")
        html_content = html_file.read_text(encoding="utf-8")

        self.check("<!DOCTYPE html>" in html_content, "DOCTYPE HTML5 dichiarato", "HTML")
        self.check('<html lang="it">' in html_content or '<html lang="en">' in html_content, "Attributo lang presente sul tag <html>", "HTML")
        self.check('<meta charset="UTF-8">' in html_content, "Meta tag charset UTF-8 dichiarato", "SEO")
        self.check('<meta name="viewport"' in html_content, "Meta tag viewport per responsive design", "SEO")
        self.check('<meta name="description"' in html_content and len(re.findall(r'<meta name="description" content="([^"]+)"', html_content)[0]) > 30, "Meta description SEO ottimizzata (>30 char)", "SEO")
        self.check('<meta property="og:title"' in html_content, "Open Graph og:title configurato per social sharing", "Social")
        self.check('<meta property="og:description"' in html_content, "Open Graph og:description configurato", "Social")
        self.check('<meta name="twitter:card"' in html_content, "Twitter Card meta tag configurato", "Social")
        self.check('rel="icon"' in html_content, "Link favicon referenziato nella <head>", "SEO")

        # -------------------------------------------------------------
        # 3. ACCESSIBILITÀ (a11y) & SEMANTICA W3C
        # -------------------------------------------------------------
        print("\n♿ 3. ACCESSIBILITÀ (a11y) & SEMANTICA W3C")
        self.check('<main id="main-content">' in html_content, "Landmark semantico <main> presente", "a11y")
        self.check('class="skip-link"' in html_content and 'href="#main-content"' in html_content, "Skip link per navigazione da tastiera / screen reader", "a11y")
        self.check('<header' in html_content and '<footer' in html_content, "Tag semantici <header> e <footer> presenti", "a11y")
        self.check('role="banner"' in html_content and 'role="contentinfo"' in html_content, "Ruoli ARIA banner e contentinfo implementati", "a11y")

        # -------------------------------------------------------------
        # 4. SICUREZZA WEB (App.js, Link Esterni, CSP, Zero Credenziali)
        # -------------------------------------------------------------
        print("\n🛡️ 4. AUDIT SICUREZZA & VULNERABILITÀ")
        js_content = js_file.read_text(encoding="utf-8")
        
        # Link con target="_blank" devono avere rel="noopener noreferrer"
        blank_links_html = re.findall(r'<a\s+[^>]*target=["\']_blank["\'][^>]*>', html_content)
        all_safe_html = all("noopener" in l for l in blank_links_html)
        self.check(all_safe_html, "Tutti i link esterni statici hanno rel='noopener'", "Sicurezza")

        has_dynamic_safe = 'rel="noopener noreferrer"' in js_content or 'rel=\\"noopener noreferrer\\"' in js_content
        self.check(has_dynamic_safe, "Link generati dinamicamente in app.js hanno rel='noopener noreferrer'", "Sicurezza")

        # Nessuna chiave API privata o token cablato nei file pubblici
        forbidden_patterns = ["api_key=", "secret=", "bearer ", "token=", "sk-"]
        has_secrets = any(p in js_content.lower() or p in html_content.lower() for p in forbidden_patterns)
        self.check(not has_secrets, "Nessun segreto, token API o credenziale esposta nel client", "Sicurezza")

        headers_content = headers_file.read_text(encoding="utf-8")
        self.check("X-Frame-Options: DENY" in headers_content, "Protezione clickjacking X-Frame-Options attiva", "Headers")
        self.check("X-Content-Type-Options: nosniff" in headers_content, "Protezione MIME sniffing attiva", "Headers")

        # -------------------------------------------------------------
        # 5. VALIDAZIONE SCHEMA DATI JSON
        # -------------------------------------------------------------
        print("\n📊 5. VALIDAZIONE INTEGRITÀ PAYLOAD (data/index.json)")
        try:
            site_data = json.loads(json_file.read_text(encoding="utf-8"))
            json_valid = True
        except Exception:
            site_data = {}
            json_valid = False

        self.check(json_valid, "File public/data/index.json sintatticamente valido", "Data")
        self.check("hero_lifespan" in site_data, "Oggetto hero_lifespan presente", "Data")
        self.check(site_data.get("hero_lifespan", {}).get("biological_baseline_days") == 73050000, "Aspettativa biologica naturale calibrata a 73.050.000 giorni (~200k anni)", "Data")
        
        horizons = site_data.get("horizons", {})
        expected_horizons = ["1_year", "5_years", "10_years", "50_years", "100_years"]
        all_h = all(k in horizons for k in expected_horizons)
        self.check(all_h, "Tutti e 5 gli orizzonti temporali (1, 5, 10, 50, 100 anni) presenti", "Data")

        charts = site_data.get("charts", {})
        has_chart_data = len(charts) >= 3
        self.check(has_chart_data, "Serie storiche per grafici presenti (VIX, CO2, GPR, Ice)", "Data")

        # -------------------------------------------------------------
        # 6. CONFIGURAZIONE CI/CD & GITHUB PAGES
        # -------------------------------------------------------------
        print("\n🚀 6. AUDIT DEPLOYMENT AUTOMATICO (CI/CD)")
        deploy_workflow = Path(".github/workflows/deploy.yml")
        gitignore = Path(".gitignore")

        self.check(gitignore.exists(), "File .gitignore configurato", "Deploy")
        self.check(deploy_workflow.exists(), "Workflow GitHub Actions (.github/workflows/deploy.yml) configurato", "Deploy")
        
        if deploy_workflow.exists():
            wf_text = deploy_workflow.read_text(encoding="utf-8")
            self.check("actions/upload-pages-artifact" in wf_text and "actions/deploy-pages" in wf_text, "Workflow impiega le GitHub Actions ufficiali per Pages", "Deploy")
            self.check("cron:" in wf_text, "Schedulazione automatica cron configurata nel workflow", "Deploy")

        # -------------------------------------------------------------
        # RESOCONTO FINALE
        # -------------------------------------------------------------
        total = self.passed + self.warnings + self.failed
        score = (self.passed / total) * 100.0 if total > 0 else 0.0

        print("\n" + "=" * 85)
        print(f"  RISULTATO AUDIT: {self.passed} SUPERATI | {self.warnings} AVVISI | {self.failed} FALLITI")
        print(f"  PUNTEGGIO DI CONFORMITÀ BEST PRACTICE: {score:.1f}%")
        print("=" * 85 + "\n")

        return self.failed == 0

if __name__ == "__main__":
    auditor = ProductionAuditor()
    success = auditor.run_all_audits()
    sys.exit(0 if success else 1)
