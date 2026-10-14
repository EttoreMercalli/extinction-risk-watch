# Metodologia dell'Algoritmo – Extinction Risk Watch

Questo documento descrive il modello matematico, le basi scientifiche e la logica di calcolo quantitativo utilizzata per determinare:
1. La **probabilità percentuale di estinzione dell'umanità** sui 5 orizzonti temporali: **1 anno**, **5 anni**, **10 anni**, **50 anni** e **100 anni**.
2. I **giorni probabili stimati rimasti alla razza umana** (aspettativa matematica di sopravvivenza della specie).

---

## 1. Fondamenti Scientifici e Baseline Accademiche

L'algoritmo non adotta metafore simboliche (come i secondi alla mezzanotte del Doomsday Clock), ma un calcolo probabilistico rigoroso basato sulla letteratura accademica del Future of Humanity Institute dell'Università di Oxford:  
📖 **Toby Ord, *The Precipice: Existential Risk and the Future of Humanity* (2020)**.

### 1.1 Baseline di Rischio a 100 Anni ($P_{\text{base}, 100}$)

| Categoria di Rischio | Probabilità Base (Secolo) | Frazione Ord | Tipologia di Rischio |
| :--- | :---: | :---: | :--- |
| **Intelligenza Artificiale non allineata** | **$10.00\%$** | $1 / 10$ | Antropogenico / Tecnologico emergente |
| **Pandemie ingegnerizzate (Biologia sintetica)** | **$3.33\%$** | $1 / 30$ | Antropogenico / Biologico |
| **Guerra nucleare totale** | **$0.10\%$** | $1 / 1.000$ | Antropogenico / Geopolitico |
| **Collasso climatico ed ecologico** | **$0.10\%$** | $1 / 1.000$ | Antropogenico / Biosfera |
| **Pandemie naturali** | **$0.01\%$** | $1 / 10.000$ | Naturale |
| **Rischi cosmici (Asteroidi, Supervulcani, Sole)** | **$0.01\%$** | $1 / 10.000$ | Naturale / Cosmico |
| **Altri rischi antropogenici non previsti** | **$3.33\%$** | $1 / 30$ | Antropogenico latente |
| **RISCHIO ESISTENZIALE TOTALE CUMULATIVO** | **$\approx 16.67\%$** | **$1 / 6$** | **Combinato su 100 anni** |

---

## 2. Proiezione Non Lineare sui 5 Orizzonti Temporali

Ogni macrocategoria ha una dinamica temporale propria, modellata tramite i fattori di proiezione $f_i(t)$:

| Categoria | 1 Anno | 5 Anni | 10 Anni | 50 Anni | 100 Anni | Dinamica |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **IA non allineata** | $1.5\%$ | $12.0\%$ | $35.0\%$ | $85.0\%$ | $100\%$ | Concentrata nella finestra AGI (2026-2050) |
| **Pandemie ingegnerizzate** | $2.0\%$ | $10.0\%$ | $30.0\%$ | $80.0\%$ | $100\%$ | Scalabilità esponenziale della biologia sintetica |
| **Guerra nucleare** | $3.0\%$ | $10.0\%$ | $20.0\%$ | $65.0\%$ | $100\%$ | Rischio contingente amplificato da crisi acute |
| **Collasso climatico** | $0.2\%$ | $2.5\%$ | $8.0\%$ | $60.0\%$ | $100\%$ | Inerzia termica ed effetti a cascata su decenni |
| **Rischi cosmici / naturali** | $1.0\%$ | $5.0\%$ | $10.0\%$ | $50.0\%$ | $100\%$ | Tasso di arrivo stocastico costante (Poissoniano) |

---

## 3. Modulatori a Percentile Storico ($M_i$) e Fragilità Sistemica ($S$)

1. **Modulatori di Categoria ($M_i$)**:  
   I dati numerici estratti in tempo reale (GPR, $CO_2$, ghiacci, tempeste solari, allerte OMS) vengono convertiti nel rispettivo percentile storico a 5 anni $p_i \in [0.0, 1.0]$.
   $$M_i = 1.0 + \alpha_i \cdot (p_i - 0.50)$$
2. **Moltiplicatore di Fragilità Sistemica ($S$)**:  
   Guidato dal percentile del CBOE VIX ($p_{\text{vix}}$), quantifica la resilienza e la liquidità globale nel gestire le crisi:
   $$S = 1.0 + 0.30 \cdot (p_{\text{vix}} - 0.50) \quad \in [0.85, 1.15]$$

---

## 4. Calcolo delle Probabilità Complessive sui 5 Orizzonti

Per ogni orizzonte $t \in \{1, 5, 10, 50, 100\}$ anni:
$$P_i(t) = P_{\text{base}, i} \cdot f_i(t) \cdot M_i \cdot S$$

La probabilità totale che almeno una catastrofe irreversibile estingua la specie entro l'orizzonte $t$ è:
$$P_{\text{tot}}(t) = 1 - \prod_{i=1}^{N} \left(1 - P_i(t)\right)$$

---

## 5. Calcolo dei Giorni Probabili Rimasti alla Razza Umana

L'aspettativa di vita media della specie umana $E[T]$ (in anni) è calcolata tramite l'integrale dell'area sotto la curva di sopravvivenza $S(t) = 1 - P_{\text{tot}}(t)$:

$$E[T] = \int_{0}^{\infty} S(t) \, dt$$

L'integrale viene computato a tratti trapezoidali tra i 5 orizzonti noti ($0 \to 1 \to 5 \to 10 \to 50 \to 100$ anni), più la coda post-secolo integrando l'hazard residuo $\lambda_{\infty} = -\frac{\ln S(100)}{100}$:
$$\text{Tail Area} = \frac{S(100)}{\lambda_{\infty}}$$

La conversione nei **giorni probabili rimasti** è data da:
$$\text{Giorni Rimasti} = \text{round}\left(E[T] \times 365.25\right)$$
