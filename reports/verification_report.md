# Report di Verifica Automatizzabilità delle Fonti Dati

> Generato il: **2026-10-14 11:25:23**  

> **Tasso di Successo Operativo:** **`100.0%`**


## Riepilogo Globale

- **Sorgenti Verificate:** `20`
- **Disponibili e Valide (`PASS`):** `18`
- **Con Avvisi (`WARN`):** `0`
- **Non Raggiungibili / Errore (`FAIL`):** `0`
- **In Attesa di Credenziali (`SKIPPED`):** `2`
- **Latenza Media:** `690.8 ms`

## Dettaglio per Sorgente

| Stato | ID Sorgente | Nome | Categoria | Latenza | Dimensione | Validazione | Note / Dettagli |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| ✅ PASS | `doomsday_clock_bulletin` | Bulletin of the Atomic Scientists (Doomsday Clock) | Baseline Strutturale | 0 ms | 0.1 KB | Sì | Baseline strutturale locale registrata e pronta all'uso |
| ✅ PASS | `toby_ord_precipice_baseline` | The Precipice - Baseline Probabilities (Toby Ord, 2020) | Baseline Strutturale | 0 ms | 0.2 KB | Sì | Baseline strutturale locale registrata e pronta all'uso |
| ✅ PASS | `noaa_co2_mlo` | NOAA Mauna Loa Daily Atmospheric CO2 Trend | Clima e Ambiente | 1098 ms | 563.9 KB | Sì | Feed di testo valido (16035 righe) |
| ✅ PASS | `nsidc_arctic_ice` | NSIDC Sea Ice Index (Daily Arctic Extent v4.0) | Clima e Ambiente | 1781 ms | 1860.4 KB | Sì | CSV valido (15870 righe). Colonne: [Year,  Month,  Day,      Extent...] |
| ✅ PASS | `cboe_vix_history` | CBOE Official VIX Volatility Index Daily History | Fragilità Finanziaria e Sistemica | 612 ms | 462.6 KB | Sì | CSV valido (9294 righe). Colonne: [DATE, OPEN, HIGH, LOW...] |
| ⏭️ SKIP | `fred_stlouis_api` | Federal Reserve FRED API (Financial Stress Indices) | Fragilità Finanziaria e Sistemica | -- | -- | No | Sorgente disabilitata (richiede configurazione chiavi/accesso) |
| ✅ PASS | `yahoo_finance_vix` | Yahoo Finance Realtime VIX Chart API | Fragilità Finanziaria e Sistemica | 324 ms | 11.3 KB | Sì | JSON valido con 1 elementi di primo livello |
| ✅ PASS | `gdelt_15min_feed` | GDELT Project (15-min Global Events & Mentions) | Guerra Nucleare e Geopolitica | 486 ms | 0.3 KB | Sì | Feed di testo valido (3 righe) |
| ✅ PASS | `gpr_iacoviello_daily` | Geopolitical Risk Index (Caldara & Iacoviello) | Guerra Nucleare e Geopolitica | 640 ms | 3195.5 KB | Sì | File binario integro (3195.5 KB) |
| ✅ PASS | `sipri_nuclear_forces` | SIPRI Nuclear Forces Data & FAS Nuclear Notebook | Guerra Nucleare e Geopolitica | 0 ms | 0.1 KB | Sì | Baseline strutturale locale registrata e pronta all'uso |
| ✅ PASS | `ai_incident_db_portal` | AI Incident Database (Weekly Snapshots) | Intelligenza Artificiale | 601 ms | 376.9 KB | Sì | Pagina HTML / Snapshot disponibile (385949 bytes) |
| ✅ PASS | `epoch_ai_notable` | Epoch AI Notable AI Systems & Compute Database | Intelligenza Artificiale | 436 ms | 2208.9 KB | Sì | CSV valido (1079 righe). Colonne: [Model, Organization, Publication date, Domain...] |
| ✅ PASS | `manifold_markets_api` | Manifold Markets API (Probabilistic Forecasts) | Mercati di Previsione | 759 ms | 8.0 KB | Sì | JSON valido con 10 elementi di primo livello |
| ⏭️ SKIP | `metaculus_api` | Metaculus Aggregated Forecasts API | Mercati di Previsione | -- | -- | No | Sorgente disabilitata (richiede configurazione chiavi/accesso) |
| ✅ PASS | `polymarket_gamma` | Polymarket Gamma API (Prediction Markets) | Mercati di Previsione | 259 ms | 171.4 KB | Sì | JSON valido con 10 elementi di primo livello |
| ✅ PASS | `cidrap_news_rss` | CIDRAP News RSS (Center for Infectious Disease Research & Policy) | Pandemie e Rischi Biologici | 244 ms | 13.1 KB | Sì | XML/RSS valido (root tag: 'rss', nodi figli: 1) |
| ✅ PASS | `who_don_api` | WHO Disease Outbreak News (DON API) | Pandemie e Rischi Biologici | 279 ms | 265.4 KB | Sì | JSON valido con 3 elementi di primo livello |
| ✅ PASS | `nasa_sentry` | NASA CNEOS Sentry (Asteroid Impact Risk) | Rischi Naturali e Cosmici | 4408 ms | 568.1 KB | Sì | JSON valido con 3 elementi di primo livello |
| ✅ PASS | `noaa_swpc_kp` | NOAA Space Weather (Planetary K-Index - Tempeste Solari) | Rischi Naturali e Cosmici | 255 ms | 4.5 KB | Sì | JSON valido con 59 elementi di primo livello |
| ✅ PASS | `usgs_earthquakes` | USGS Earthquakes (Significant Monthly Events) | Rischi Naturali e Cosmici | 252 ms | 10.8 KB | Sì | JSON valido con 4 elementi di primo livello |