/**
 * EXTINCTION RISK WATCH - JAVASCRIPT FRONTEND CONTROLLER
 * Consumes public/data/index.json and handles:
 * 1. Display of remaining days and biological vs anthropogenic contrast
 * 2. Display of 5 time horizons (1, 5, 10, 50, 100 years)
 * 3. Interactive Chart.js charts (VIX, CO2, Sea Ice, GPR, Kp)
 * 4. Category-filterable news feed
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
    // Cache-busting with timestamp to ensure fresh data
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
    console.error("Error loading data/index.json:", error);
    if (!siteData) {
      document.getElementById('hero-days').innerText = "ERROR";
      document.getElementById('last-updated-pill').innerText = "Data connection error";
    }
  } finally {
    if (icon) setTimeout(() => icon.classList.remove('rotating'), 600);
  }
}

function setupPolling() {
  // Manual refresh button
  const refreshBtn = document.getElementById('btn-refresh-now');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      initApp(false);
    });
  }

  // Countdown timer and automatic polling every 30 seconds
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
  const timeStr = genDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  pill.innerHTML = `<span>Live: ${timeStr}</span> &bull; <span style="color:var(--accent-cyan);">check in ${countdownSeconds}s</span>`;
}

// -----------------------------------------------------------------------------
// 1. Render Hero Section (Biological vs Anthropogenic Contrast)
// -----------------------------------------------------------------------------
function renderHero() {
  const ls = siteData.hero_lifespan;
  const sys = siteData.systemic_fragility;

  // Effective expected days & years
  document.getElementById('hero-days').innerText = ls.effective_expected_days.toLocaleString('en-US');
  document.getElementById('hero-years').innerText = Math.round(ls.effective_expected_years);

  // Bar legend
  document.getElementById('leg-eff').innerText = `~${ls.effective_expected_days.toLocaleString('en-US')} days`;
  document.getElementById('leg-bio').innerText = `~${ls.biological_baseline_days.toLocaleString('en-US')} days`;

  // Proportional progress bar
  const pct = Math.max(0.2, (ls.effective_expected_years / ls.biological_baseline_years) * 100);
  document.getElementById('comparison-fill').style.width = `${pct.toFixed(2)}%`;

  // Chips
  const deltaDays = ls.daily_delta_days_vs_norm;
  const deltaSign = deltaDays >= 0 ? "+" : "";
  const deltaEl = document.getElementById('hero-delta-days');
  deltaEl.innerText = `${deltaSign}${deltaDays.toLocaleString('en-US')} days`;
  if (deltaDays < 0) {
    deltaEl.classList.remove('chip-positive');
    deltaEl.style.color = 'var(--accent-crimson)';
  }

  // VIX multiplier
  document.getElementById('hero-vix-mult').innerText = `x${sys.multiplier} (VIX ${Math.round(sys.vix_percentile * 100)}th pct)`;

  // Timestamp
  const genDate = new Date(siteData.metadata.generated_at);
  const dateStr = genDate.toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  document.getElementById('last-updated-pill').innerText = `Updated: ${dateStr}`;
}

// -----------------------------------------------------------------------------
// 2. Render 5 Time Horizons (1, 5, 10, 50, 100 Years)
// -----------------------------------------------------------------------------
function renderHorizons() {
  const container = document.getElementById('horizons-cards-container');
  container.innerHTML = '';

  const order = ["1_year", "5_years", "10_years", "50_years", "100_years"];
  const names = {
    "1_year": "1 Year",
    "5_years": "5 Years",
    "10_years": "10 Years",
    "50_years": "50 Years",
    "100_years": "100 Years"
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
// 3. Render Risk Macro-Categories
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
    if (c.status_label.includes('ALERT') || c.status_label.includes('ALLERTA')) statusClass = 'tier-critico';
    else if (c.status_label.includes('HIGH') || c.status_label.includes('ELEVATA') || c.status_label.includes('ACCELERAZIONE')) statusClass = 'tier-elevato';

    card.innerHTML = `
      <div class="cat-top">
        <div class="cat-title">${c.category_name}</div>
        <span class="cat-status ${statusClass}">${c.status_label}</span>
      </div>
      <div class="cat-modulator">
        Today's modulator: <span class="cat-mod-val">x${c.modulator.toFixed(2)}</span> (${Math.round(c.percentile_driver * 100)}th percentile)
      </div>
      <div class="cat-probs-row">
        <div class="prob-cell">
          <div class="prob-cell-lbl">1 Year</div>
          <div class="prob-cell-val">${(c.prob_1y * 100).toFixed(3)}%</div>
        </div>
        <div class="prob-cell">
          <div class="prob-cell-lbl">10 Years</div>
          <div class="prob-cell-val">${(c.prob_10y * 100).toFixed(2)}%</div>
        </div>
        <div class="prob-cell">
          <div class="prob-cell-lbl">100 Years</div>
          <div class="prob-cell-val">${(c.prob_100y * 100).toFixed(2)}%</div>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// -----------------------------------------------------------------------------
// 4. Interactive Charts (Chart.js)
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
    title = "CBOE Volatility Index (VIX) – 365-Day Historical";
    meta = "Daily series | Source: CBOE Global Markets";
    labelText = "VIX Index";
    unitText = "pts";
    chartColor = "#ffb703";
    const pts = chartsData?.systemic_fragility?.vix_daily_chart || [];
    labels = pts.map(p => p.date);
    dataPoints = pts.map(p => p.value);
    stat = `Current value: ${dataPoints[dataPoints.length - 1] || '--'} pts`;
  }
  else if (activeChartType === 'co2') {
    title = "Atmospheric CO₂ Concentration (Mauna Loa Keeling Curve)";
    meta = "Daily ppm readings | Source: NOAA GML";
    labelText = "CO₂ (ppm)";
    unitText = "ppm";
    chartColor = "#ff3366";
    const pts = chartsData?.climate_biosphere?.co2_chart || [];
    labels = pts.map(p => p.date);
    dataPoints = pts.map(p => p.value);
    stat = `Current value: ${dataPoints[dataPoints.length - 1] || '--'} ppm`;
  }
  else if (activeChartType === 'ice') {
    title = "Arctic Sea Ice Extent (NSIDC v4.0)";
    meta = "Daily surface area in million km² | Source: NOAA / NSIDC";
    labelText = "Ice Extent";
    unitText = "mln km²";
    chartColor = "#00f0ff";
    const pts = chartsData?.climate_biosphere?.sea_ice_chart || [];
    labels = pts.map(p => p.date);
    dataPoints = pts.map(p => p.value);
    stat = `Current value: ${dataPoints[dataPoints.length - 1] || '--'} mln km²`;
  }
  else if (activeChartType === 'gpr') {
    title = "Geopolitical Risk Index (GPR Daily) – Caldara & Iacoviello";
    meta = "Threats and military acts index | Source: Federal Reserve Board";
    labelText = "GPR Index";
    unitText = "index";
    chartColor = "#ff3366";
    const pts = chartsData?.geopolitics_nuclear?.gpr_daily_chart || [];
    labels = pts.map(p => p.date);
    dataPoints = pts.map(p => p.value);
    stat = `Current value: ${dataPoints[dataPoints.length - 1] || '--'}`;
  }
  else if (activeChartType === 'kp') {
    title = "Planetary Geomagnetic Index Kp (Solar Storms)";
    meta = "Hourly space weather monitoring | Source: NOAA SWPC";
    labelText = "Kp Index (0–9)";
    unitText = "Kp";
    chartColor = "#00e676";
    const pts = chartsData?.cosmic_natural_hazards?.kp_hourly_chart || [];
    labels = pts.map(p => p.date.substring(5)); // MM-DD HH:MM
    dataPoints = pts.map(p => p.value);
    stat = `Latest Kp: ${dataPoints[dataPoints.length - 1] || '--'}`;
  }

  document.getElementById('current-chart-title').innerText = title;
  document.getElementById('current-chart-meta').innerText = meta;
  document.getElementById('current-chart-stat').innerText = stat;

  // Gradient fill under the line
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
// 5. Filterable News Feed (Text Format)
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

  // Sort by date descending
  newsList.sort((a, b) => (b.date || "").localeCompare(a.date || ""));

  if (newsList.length === 0) {
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-dim); padding: 40px;">No news available for this filter.</div>`;
    return;
  }

  newsList.forEach(news => {
    const card = document.createElement('div');
    card.className = 'news-card';

    let badgeClass = 'news-badge-info';
    let badgeText = 'NEWS';
    if (news.severity >= 4) {
      badgeClass = 'news-badge-red';
      badgeText = '🔴 ALERT';
    } else if (news.severity >= 3) {
      badgeClass = 'news-badge-yellow';
      badgeText = '🟡 WARNING';
    }

    card.innerHTML = `
      <div class="news-card-header">
        <span class="news-badge ${badgeClass}">${badgeText}</span>
        <span class="news-date">${news.date || 'Recent'}</span>
      </div>
      <h4 class="news-title">${news.title}</h4>
      <p class="news-summary">${news.summary}</p>
      <div class="news-footer">
        <span class="news-source">${news.source}</span>
        <a href="${news.url}" target="_blank" rel="noopener noreferrer" class="news-link">Official Source &rarr;</a>
      </div>
    `;
    container.appendChild(card);
  });
}
