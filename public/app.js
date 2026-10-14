/**
 * EXTINCTION RISK WATCH - JAVASCRIPT FRONTEND CONTROLLER
 * Consuma public/data/index.json e gestisce:
 * 1. Visualizzazione giorni rimanenti e contrasto biologico vs antropogenico
 * 2. Visualizzazione 5 orizzonti temporali (1, 5, 10, 50, 100 anni)
 * 3. Grafici interattivi Chart.js (VIX, CO2, Ghiacci, GPR, Kp)
 * 4. Feed notizie filtrabile per categoria
 */

let siteData = null;
let currentChartInstance = null;
let activeChartType = 'vix';
let activeNewsFilter = 'all';
let pollingTimer = null;
let countdownSeconds = 30;

document.addEventListener('DOMContentLoaded', () => {
  initApp();
  setupPolling();
});

async function initApp(isSilent = false) {
  const icon = document.querySelector('.refresh-icon');
  if (icon && !isSilent) icon.classList.add('rotating');

  try {
    // Cache-busting con timestamp per garantire dati freschi
    const response = await fetch(`data/index.json?_t=${Date.now()}`);
    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }
    const newData = await response.json();

    const isChanged = !siteData || siteData.metadata?.generated_at !== newData.metadata?.generated_at;
    siteData = newData;

    if (isChanged || !isSilent) {
      renderHero();
      renderHorizons();
      renderCategories();
      renderActiveChart();
      renderNewsCards();
    }

    countdownSeconds = 30;
    updatePillDisplay();

  } catch (error) {
    console.error("Errore nel caricamento di data/index.json:", error);
    if (!siteData) {
      document.getElementById('hero-days').innerText = "ERRORE";
      document.getElementById('last-updated-pill').innerText = "Errore connessione dati";
    }
  } finally {
    if (icon) setTimeout(() => icon.classList.remove('rotating'), 600);
  }
}

function setupPolling() {
  // Pulsante Aggiorna Ora manuale
  const refreshBtn = document.getElementById('btn-refresh-now');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      initApp(false);
    });
  }

  // Timer di countdown e polling automatico ogni 30 secondi
  if (pollingTimer) clearInterval(pollingTimer);
  pollingTimer = setInterval(() => {
    countdownSeconds--;
    if (countdownSeconds <= 0) {
      initApp(true);
    } else {
      updatePillDisplay();
    }
  }, 1000);
}

function updatePillDisplay() {
  const pill = document.getElementById('last-updated-pill');
  if (!siteData || !pill) return;
  const genDate = new Date(siteData.metadata.generated_at);
  const timeStr = genDate.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  pill.innerHTML = `<span>Live: ${timeStr}</span> &bull; <span style="color:var(--accent-cyan);">check in ${countdownSeconds}s</span>`;
}

// -----------------------------------------------------------------------------
// 1. Render Hero Section (Contrasto Biologico vs Antropogenico)
// -----------------------------------------------------------------------------
function renderHero() {
  const ls = siteData.hero_lifespan;
  const sys = siteData.systemic_fragility;

  // Giorni & Anni effettivi attesi
  document.getElementById('hero-days').innerText = ls.effective_expected_days.toLocaleString('it-IT');
  document.getElementById('hero-years').innerText = Math.round(ls.effective_expected_years);

  // Legende barra
  document.getElementById('leg-eff').innerText = `~${ls.effective_expected_days.toLocaleString('it-IT')} giorni`;
  document.getElementById('leg-bio').innerText = `~${ls.biological_baseline_days.toLocaleString('it-IT')} giorni`;

  // Barra di avanzamento proporzionale
  const pct = Math.max(0.2, (ls.effective_expected_years / ls.biological_baseline_years) * 100);
  document.getElementById('comparison-fill').style.width = `${pct.toFixed(2)}%`;

  // Chips
  const deltaDays = ls.daily_delta_days_vs_norm;
  const deltaSign = deltaDays >= 0 ? "+" : "";
  const deltaEl = document.getElementById('hero-delta-days');
  deltaEl.innerText = `${deltaSign}${deltaDays.toLocaleString('it-IT')} giorni`;
  if (deltaDays < 0) {
    deltaEl.classList.remove('chip-positive');
    deltaEl.style.color = 'var(--accent-crimson)';
  }

  // Moltiplicatore VIX
  document.getElementById('hero-vix-mult').innerText = `x${sys.multiplier} (VIX ${Math.round(sys.vix_percentile * 100)}° pct)`;

  // Timestamp
  const genDate = new Date(siteData.metadata.generated_at);
  const dateStr = genDate.toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  document.getElementById('last-updated-pill').innerText = `Aggiornato: ${dateStr}`;
}

// -----------------------------------------------------------------------------
// 2. Render 5 Orizzonti Temporali (1, 5, 10, 50, 100 Anni)
// -----------------------------------------------------------------------------
function renderHorizons() {
  const container = document.getElementById('horizons-cards-container');
  container.innerHTML = '';

  const order = ["1_year", "5_years", "10_years", "50_years", "100_years"];
  const names = {
    "1_year": "1 Anno",
    "5_years": "5 Anni",
    "10_years": "10 Anni",
    "50_years": "50 Anni",
    "100_years": "100 Anni"
  };

  order.forEach(k => {
    const h = siteData.horizons[k];
    if (!h) return;

    const tierClass = `tier-${h.risk_tier.toLowerCase()}`;
    const fillWidth = Math.min(100, Math.max(4, h.probability * 350));

    const card = document.createElement('div');
    card.className = 'horizon-card';
    card.innerHTML = `
      <div class="horizon-header">
        <span class="horizon-name">${names[k]}</span>
        <span class="tier-badge ${tierClass}">${h.risk_tier}</span>
      </div>
      <div class="horizon-pct">${h.percentage_str}</div>
      <div class="horizon-odds">${h.odds_str}</div>
      <div class="horizon-bar-track">
        <div class="horizon-bar-fill" style="width: ${fillWidth}%;"></div>
      </div>
      <div class="horizon-delta">
        Delta vs Baseline: ${h.delta_vs_baseline >= 0 ? '+' : ''}${(h.delta_vs_baseline * 100).toFixed(3)}%
      </div>
    `;
    container.appendChild(card);
  });
}

// -----------------------------------------------------------------------------
// 3. Render Macrocategorie di Rischio
// -----------------------------------------------------------------------------
function renderCategories() {
  const container = document.getElementById('categories-container');
  container.innerHTML = '';

  const cats = siteData.categories_breakdown;
  Object.keys(cats).forEach(id => {
    const c = cats[id];
    const card = document.createElement('div');
    card.className = 'category-card';

    let statusClass = 'tier-moderato';
    if (c.status_label.includes('ALLERTA')) statusClass = 'tier-critico';
    else if (c.status_label.includes('ELEVATA') || c.status_label.includes('ACCELERAZIONE')) statusClass = 'tier-elevato';

    card.innerHTML = `
      <div class="cat-top">
        <div class="cat-title">${c.category_name}</div>
        <span class="cat-status ${statusClass}">${c.status_label}</span>
      </div>
      <div class="cat-modulator">
        Modulatore odierno: <span class="cat-mod-val">x${c.modulator.toFixed(2)}</span> (${Math.round(c.percentile_driver * 100)}° percentile dati)
      </div>
      <div class="cat-probs-row">
        <div class="prob-cell">
          <div class="prob-cell-lbl">1 Anno</div>
          <div class="prob-cell-val">${(c.prob_1y * 100).toFixed(3)}%</div>
        </div>
        <div class="prob-cell">
          <div class="prob-cell-lbl">10 Anni</div>
          <div class="prob-cell-val">${(c.prob_10y * 100).toFixed(2)}%</div>
        </div>
        <div class="prob-cell">
          <div class="prob-cell-lbl">100 Anni</div>
          <div class="prob-cell-val">${(c.prob_100y * 100).toFixed(2)}%</div>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// -----------------------------------------------------------------------------
// 4. Grafici Interattivi (Chart.js)
// -----------------------------------------------------------------------------
function setupCharts() {
  const tabs = document.querySelectorAll('.chart-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      tabs.forEach(t => t.classList.remove('active'));
      e.target.classList.add('active');
      activeChartType = e.target.getAttribute('data-chart');
      renderActiveChart();
    });
  });

  renderActiveChart();
}

function renderActiveChart() {
  const canvas = document.getElementById('mainChartCanvas');
  const ctx = canvas.getContext('2d');

  if (currentChartInstance) {
    currentChartInstance.destroy();
  }

  let labels = [];
  let dataPoints = [];
  let labelText = "";
  let unitText = "";
  let chartColor = "#00f0ff";
  let title = "";
  let meta = "";
  let stat = "";

  const chartsData = siteData.charts;

  if (activeChartType === 'vix') {
    title = "CBOE Volatility Index (VIX) – Storico 365 Giorni";
    meta = "Serie giornaliera | Fonte: CBOE Global Markets";
    labelText = "VIX Index";
    unitText = "punti";
    chartColor = "#ffb703";
    const pts = chartsData?.systemic_fragility?.vix_daily_chart || [];
    labels = pts.map(p => p.date);
    dataPoints = pts.map(p => p.value);
    stat = `Valore attuale: ${dataPoints[dataPoints.length - 1] || '--'} punti`;
  }
  else if (activeChartType === 'co2') {
    title = "Concentrazione Atmosferica CO₂ (Mauna Loa Keeling Curve)";
    meta = "Rilevazioni giornaliere ppm | Fonte: NOAA GML";
    labelText = "CO₂ (ppm)";
    unitText = "ppm";
    chartColor = "#ff3366";
    const pts = chartsData?.climate_biosphere?.co2_chart || [];
    labels = pts.map(p => p.date);
    dataPoints = pts.map(p => p.value);
    stat = `Valore attuale: ${dataPoints[dataPoints.length - 1] || '--'} ppm`;
  }
  else if (activeChartType === 'ice') {
    title = "Estensione Ghiaccio Marino Artico (NSIDC v4.0)";
    meta = "Superficie giornaliera in milioni di km² | Fonte: NOAA / NSIDC";
    labelText = "Estensione Ghiacci";
    unitText = "mln km²";
    chartColor = "#00f0ff";
    const pts = chartsData?.climate_biosphere?.sea_ice_chart || [];
    labels = pts.map(p => p.date);
    dataPoints = pts.map(p => p.value);
    stat = `Valore attuale: ${dataPoints[dataPoints.length - 1] || '--'} mln km²`;
  }
  else if (activeChartType === 'gpr') {
    title = "Geopolitical Risk Index (GPR Daily) – Caldara & Iacoviello";
    meta = "Indice delle minacce e atti bellici | Fonte: Federal Reserve Board";
    labelText = "Indice GPR";
    unitText = "indice";
    chartColor = "#ff3366";
    const pts = chartsData?.geopolitics_nuclear?.gpr_daily_chart || [];
    labels = pts.map(p => p.date);
    dataPoints = pts.map(p => p.value);
    stat = `Valore attuale: ${dataPoints[dataPoints.length - 1] || '--'}`;
  }
  else if (activeChartType === 'kp') {
    title = "Indice Geomagnetico Planetario Kp (Tempeste Solari)";
    meta = "Monitoraggio orario clima spaziale | Fonte: NOAA SWPC";
    labelText = "Indice Kp (0-9)";
    unitText = "Kp";
    chartColor = "#00e676";
    const pts = chartsData?.cosmic_natural_hazards?.kp_hourly_chart || [];
    labels = pts.map(p => p.date.substring(5)); // MM-DD HH:MM
    dataPoints = pts.map(p => p.value);
    stat = `Ultimo Kp: ${dataPoints[dataPoints.length - 1] || '--'}`;
  }

  document.getElementById('current-chart-title').innerText = title;
  document.getElementById('current-chart-meta').innerText = meta;
  document.getElementById('current-chart-stat').innerText = stat;

  // Gradient fill per l'area sotto la linea
  const gradient = ctx.createLinearGradient(0, 0, 0, 360);
  gradient.addColorStop(0, chartColor + '40'); // 25% opacity
  gradient.addColorStop(1, chartColor + '00'); // 0% opacity

  currentChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: labelText,
        data: dataPoints,
        borderColor: chartColor,
        borderWidth: 2,
        backgroundColor: gradient,
        fill: true,
        tension: 0.2,
        pointRadius: labels.length > 100 ? 0 : 2,
        pointHoverRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: '#0d121c',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          titleFont: { family: 'Inter', size: 12 },
          bodyFont: { family: 'JetBrains Mono', size: 13 },
          callbacks: {
            label: (item) => `${item.dataset.label}: ${item.parsed.y} ${unitText}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: {
            color: '#5c6b84',
            font: { family: 'JetBrains Mono', size: 11 },
            maxTicksLimit: 10
          }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: {
            color: '#5c6b84',
            font: { family: 'JetBrains Mono', size: 11 }
          }
        }
      }
    }
  });
}

// -----------------------------------------------------------------------------
// 5. Feed Notizie Filtrabile (Formato Testo)
// -----------------------------------------------------------------------------
function setupNewsFeed() {
  const filterBtns = document.querySelectorAll('.news-filter-btn');
  filterBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      filterBtns.forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      activeNewsFilter = e.target.getAttribute('data-filter');
      renderNewsCards();
    });
  });

  renderNewsCards();
}

function renderNewsCards() {
  const container = document.getElementById('news-grid-container');
  container.innerHTML = '';

  const allNewsObj = siteData.news_feed || {};
  let newsList = [];

  if (activeNewsFilter === 'all') {
    Object.keys(allNewsObj).forEach(cat => {
      newsList = newsList.concat(allNewsObj[cat] || []);
    });
  } else {
    newsList = allNewsObj[activeNewsFilter] || [];
  }

  // Ordina per data decrescente se possibile
  newsList.sort((a, b) => (b.date || "").localeCompare(a.date || ""));

  if (newsList.length === 0) {
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-dim); padding: 40px;">Nessuna notizia disponibile per questo filtro.</div>`;
    return;
  }

  newsList.forEach(news => {
    const card = document.createElement('div');
    card.className = 'news-card';

    let badgeClass = 'news-badge-info';
    let badgeText = 'NOTIZIA';
    if (news.severity >= 4) {
      badgeClass = 'news-badge-red';
      badgeText = '🔴 ALLERTA';
    } else if (news.severity >= 3) {
      badgeClass = 'news-badge-yellow';
      badgeText = '🟡 ATTENZIONE';
    }

    card.innerHTML = `
      <div class="news-card-header">
        <span class="news-badge ${badgeClass}">${badgeText}</span>
        <span class="news-date">${news.date || 'Recente'}</span>
      </div>
      <h4 class="news-title">${news.title}</h4>
      <p class="news-summary">${news.summary}</p>
      <div class="news-footer">
        <span class="news-source">${news.source}</span>
        <a href="${news.url}" target="_blank" rel="noopener noreferrer" class="news-link">Fonte Ufficiale &rarr;</a>
      </div>
    `;
    container.appendChild(card);
  });
}
