# Catalogo delle Fonti Dati Target – Progetto Extinction Risk Watch

Questo documento descrive in modo dettagliato le fonti dati individuate per alimentare l'algoritmo di stima del rischio di estinzione della specie umana sui tre orizzonti temporali (**1 anno**, **10 anni**, **100 anni**).

---

## 1. Classificazione per Livello di Accesso

| Livello | Descrizione | Autenticazione | Strategia di Acquisizione |
| :--- | :--- | :--- | :--- |
| **Livello A** | **Automatiche e Libere** | Nessuna API key / Aperte al pubblico | Chiamate HTTP `GET` dirette schedulate (cron giornaliero/orario). |
| **Livello B** | **Automatiche con Registrazione** | Richiede API key gratuita o form di accesso | Chiamata con Header di autorizzazione (`Authorization: Bearer <token>`). |
| **Livello C** | **Strutturali / Annuali** | Dati da report periodici o letteratura accademica | File di configurazione locale (`baseline_*.json`) aggiornato 1 volta l'anno. |

---

## 2. Dettaglio delle Fonti per Macrocategoria

### 2.1 Rischi Naturali e Cosmici
*Questi rischi hanno una probabilità annua infinitesimale, ma dispongono di dati scientifici in tempo reale di massima precisione, ideali per dimostrare la reattività del sistema.*

1. **NASA CNEOS Sentry** *(Livello A)*
   * **Endpoint:** `https://ssd-api.jpl.nasa.gov/sentry.api`
   * **Formato:** JSON (REST API)
   * **Frequenza:** Giornaliera
   * **Cosa misura:** Calcolo automatico di impatto asteroidale cumulativo per tutti i Near-Earth Objects (NEO) noti nei prossimi 100 anni, con punteggio su Palermo Technical Scale e Torino Scale.
   * **Metrica target:** Probabilità di impatto massima e numero di oggetti con scala Palermo > -2.

2. **NOAA SWPC – Planetary K-Index** *(Livello A)*
   * **Endpoint:** `https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json`
   * **Formato:** JSON
   * **Frequenza:** Oraria / Realtime
   * **Cosa misura:** Indice geomagnetico globale $K_p$ su scala $0-9$. Monitora tempeste geomagnetiche solari estreme capaci di distruggere l'infrastruttura elettrica e di telecomunicazione globale (evento stile Carrington).
   * **Metrica target:** Valore picco $K_p$ nelle ultime 24-72 ore.

3. **USGS Significant Earthquakes** *(Livello A)*
   * **Endpoint:** `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson`
   * **Formato:** GeoJSON
   * **Frequenza:** Realtime
   * **Cosa misura:** Terremoti globali di magnitudo rilevante ($M > 6.0$ o con impatto catastrofico potenziale).
   * **Metrica target:** Conteggio ed energia rilasciata da eventi sismici planetari.

---

### 2.2 Clima, Ambiente e Biosfera
*Misurano l'avvicinamento ai tipping points ecologici irreversibili.*

4. **NOAA Mauna Loa CO₂ Daily** *(Livello A)*
   * **Endpoint:** `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_daily_mlo.txt`
   * **Formato:** Testo tabellare a colonne fisse
   * **Frequenza:** Giornaliera
   * **Cosa misura:** La Curva di Keeling aggiornata giorno per giorno.
   * **Metrica target:** Concentrazione di $CO_2$ in ppm rispetto alla media mobile storica e variazione anno su anno.

5. **NSIDC Arctic Sea Ice Extent (v4.0)** *(Livello A)*
   * **Endpoint:** `https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v4.0.csv`
   * **Formato:** CSV
   * **Frequenza:** Giornaliera
   * **Cosa misura:** Estensione della calotta artica in milioni di chilometri quadrati.
   * **Metrica target:** Anomalia rispetto alla climatologia trentennale di riferimento (1981-2010).

---

### 2.3 Guerra Nucleare e Tensioni Geopolitiche
*La minaccia nucleare è il rischio catastrofico a breve termine con il più alto potenziale distruttivo immediato.*

6. **Geopolitical Risk (GPR) Index – Caldara & Iacoviello** *(Livello A)*
   * **Endpoint:** `https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls`
   * **Formato:** Foglio di calcolo (.xls)
   * **Frequenza:** Aggiornato ogni lunedì
   * **Cosa misura:** Indice accademico (American Economic Review) basato sull'analisi della frequenza di articoli riguardanti minacce nucleari, mobilitazione bellica, atti di guerra e terrorismo su 10 testate mondiali.
   * **Metrica target:** Serie giornaliera del sub-indice $GPRT$ (minacce geopolitiche e nucleari).

7. **GDELT Project (Global Event Data)** *(Livello A)*
   * **Endpoint:** `http://data.gdeltproject.org/gdeltv2/lastupdate.txt`
   * **Formato:** Testo / Dump CSV ogni 15 minuti
   * **Frequenza:** Ogni 15 minuti / Oraria
   * **Cosa misura:** Monitoraggio mondiale di notizie ed eventi geopolitici in oltre 100 lingue.
   * **Strategia:** Scaricare l'export compresso dei soli eventi codificati con Cameo Code nucleare/militare, evitando i limiti di rate-limiting delle API di ricerca testo.

8. **SIPRI Yearbook & FAS Nuclear Notebook** *(Livello C)*
   * **Origine:** Rapporti annuali SIPRI / FAS
   * **Formato:** Configurazione statica
   * **Cosa misura:** Numero totale di testate nucleari nel mondo (~12.500), numero di testate dispiegate in stato di allerta elevata e stato dei trattati di non proliferazione.

---

### 2.4 Pandemie e Rischi Biologici
*Copre sia pandemie naturali ad alta letalità (es. ceppi di influenza aviaria H5N1), sia patogeni ingegnerizzati da biologia sintetica.*

9. **WHO Disease Outbreak News (DON API)** *(Livello A)*
   * **Endpoint:** `https://www.who.int/api/news/diseaseoutbreaknews`
   * **Formato:** JSON (OData REST API)
   * **Frequenza:** Giornaliera
   * **Cosa misura:** Notifiche ufficiali dell'OMS su focolai emergenti nel mondo.
   * **Metrica target:** Numero di nuovi focolai e valutazione di severità (classificata tramite parser semantico/LLM).

10. **CIDRAP News RSS (University of Minnesota)** *(Livello A)*
    * **Endpoint:** `https://www.cidrap.umn.edu/news/178636/rss`
    * **Formato:** RSS / XML
    * **Frequenza:** Giornaliera
    * **Cosa misura:** Articoli e allerte epidemiologiche e di biosicurezza globale.

---

### 2.5 Intelligenza Artificiale e Rischi AGI
*Il rischio esistenziale con la crescita più rapida della probabilità di base nei modelli contemporanei (es. Toby Ord stima 1/10 nel secolo).*

11. **Epoch AI – Notable AI Systems Dataset** *(Livello A)*
    * **Endpoint:** `https://epoch.ai/data/notable_ai_models.csv`
    * **Formato:** CSV (~2.2 MB)
    * **Frequenza:** Settimanale
    * **Cosa misura:** Potenza di calcolo impiegata nell'addestramento dei modelli di frontiera (FLOPs), dimensione dei parametri e velocità di avanzamento algoritmico.
    * **Metrica target:** Flops massimi impiegati e accelerazione del tasso di raddoppio delle risorse computazionali.

12. **AI Incident Database** *(Livello A)*
    * **Endpoint:** `https://incidentdatabase.ai/research/snapshots/`
    * **Formato:** Snapshot scaricabili (JSON/CSV)
    * **Frequenza:** Settimanale
    * **Cosa misura:** Numero cumulativo di incidenti critici e violazioni di sicurezza causate da sistemi intelligenti.

---

### 2.6 Fragilità Sistemica e Finanziaria (Moltiplicatore)
*Gli indici finanziari non sono una causa di estinzione di per sé, ma agiscono come moltiplicatore: un mondo sotto estremo stress finanziario o istituzionale ha una capacità di risposta e resilienza drasticamente ridotta di fronte a una pandemia o una crisi nucleare.*

13. **CBOE VIX Volatility Index (Storico Completo)** *(Livello A)*
    * **Endpoint:** `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv`
    * **Formato:** CSV
    * **Frequenza:** Giornaliera
    * **Cosa misura:** Indice di volatilità implicita CBOE VIX (1990 - presente) direttamente dall'exchange.

14. **Yahoo Finance VIX Realtime** *(Livello A)*
    * **Endpoint:** `https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX`
    * **Formato:** JSON
    * **Frequenza:** Oraria / Realtime
    * **Cosa misura:** Livello spot intraday del VIX.
    * **Metrica target:** Percentile storico su 5 anni del VIX ($VIX > 40$ segnala panico sistemico globale).

---

### 2.7 Mercati di Previsione e Saggezza delle Folle
*I prediction market aggregano rapidamente le probabilità implicite assegnate da migliaia di scommettitori ed esperti internazionali su eventi catastrofici.*

15. **Polymarket Gamma API** *(Livello A)*
    * **Endpoint:** `https://gamma-api.polymarket.com/events?closed=false&limit=10`
    * **Formato:** JSON
    * **Frequenza:** Oraria
    * **Cosa misura:** Prezzo di liquidazione (probabilità $0\% - 100\%$) di contratti su test nucleari, pandemie, arrivo dell'AGI, crisi geopolitiche.

16. **Manifold Markets API** *(Livello A)*
    * **Endpoint:** `https://api.manifold.markets/v0/markets?limit=10`
    * **Formato:** JSON
    * **Frequenza:** Oraria
    * **Cosa misura:** Previsioni probabilistiche aperte con tag specifici su *Existential Risk*, *Biosecurity*, *AI Alignment*, *Nuclear War*.

17. **Metaculus API** *(Livello B)*
    * **Endpoint:** `https://www.metaculus.com/api2/questions/`
    * **Formato:** JSON
    * **Requisito:** Registrazione gratuita con richiesta token per l'accesso ai dati aggregati della community.

---

### 2.8 Baseline Accademiche Strutturali
18. **Toby Ord – The Precipice (Oxford Future of Humanity Institute)** *(Livello C)*
    * Baseline di rischio a 100 anni:
      * Rischio artificiale/tecnologico totale: $\approx 1/6 \ (\sim 16.6\%)$
      * Intelligenza Artificiale non allineata: $1/10 \ (10\%)$
      * Pandemie ingegnerizzate: $1/30 \ (\sim 3.3\%)$
      * Guerra nucleare totale: $1/1000 \ (0.1\%)$
      * Clima e catastrofe ecologica: $1/1000 \ (0.1\%)$
      * Rischi naturali cosmici (asteroidi, supervulcani): $1/10000 \ (0.01\%)$
