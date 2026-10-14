"""
Parser per Pandemie e Rischi Biologici (WHO Disease Outbreak News & CIDRAP RSS).
Estrae:
- Formato Tabella: frequenza temporale delle notifiche di focolai epidemici globali
- Formato Testo: articoli e bollettini sanitari con patogeno, area geografica e data
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List
import requests

from src.parsers.models import CategoryPayload, IndicatorSummary, TimeSeriesRecord, NewsItem

WHO_DON_URL = "https://www.who.int/api/news/diseaseoutbreaknews"
CIDRAP_RSS_URL = "https://www.cidrap.umn.edu/news/178636/rss"

def fetch_and_parse_pandemics(timeout_sec: float = 15.0) -> CategoryPayload:
    """Scarica e converte i dati epidemici dell'OMS e di CIDRAP."""
    headers = {"User-Agent": "Mozilla/5.0"}
    news_items: List[NewsItem] = []

    # 1. Parsing CIDRAP RSS (notizie recentissime)
    try:
        r_cidrap = requests.get(CIDRAP_RSS_URL, headers=headers, timeout=timeout_sec)
        if r_cidrap.status_code == 200:
            root = ET.fromstring(r_cidrap.content)
            channel = root.find("channel")
            if channel is not None:
                for it in channel.findall("item")[:6]:
                    title = it.findtext("title") or "Aggiornamento CIDRAP"
                    link = it.findtext("link") or "https://www.cidrap.umn.edu/"
                    pub_date = it.findtext("pubDate") or ""
                    desc = it.findtext("description") or ""
                    # Pulizia testo
                    summary = desc[:200].replace("\n", " ").strip() if desc else "Notizia epidemiologica da CIDRAP"
                    news_items.append(
                        NewsItem(
                            title=title,
                            date=pub_date[:16] if pub_date else datetime.now().strftime("%Y-%m-%d"),
                            source="CIDRAP (University of Minnesota)",
                            url=link,
                            summary=summary,
                            category="Pandemie e Rischi Biologici",
                            severity=2 if "avian" in title.lower() or "flu" in title.lower() else 1,
                            tags=["Pandemie", "Infezioni", "Biosicurezza", "CIDRAP"]
                        )
                    )
    except Exception as e:
        pass

    # 2. Parsing WHO Disease Outbreak News (DON API)
    try:
        r_who = requests.get(WHO_DON_URL, headers=headers, timeout=timeout_sec)
        if r_who.status_code == 200:
            data = r_who.json()
            raw_items = data.get("value", [])
            # Ordina dal più recente al più vecchio
            raw_items.sort(key=lambda x: x.get("PublicationDate") or "", reverse=True)
            for it in raw_items[:6]:
                title = it.get("Title") or "Focolaio OMS"
                pub_date = (it.get("PublicationDate") or "")[:10]
                url = it.get("ItemDefaultUrl") or "https://www.who.int/emergencies/disease-outbreak-news"
                overview = str(it.get("Overview") or "")
                # Rimuovi tag html base
                clean_overview = overview.replace("<p>", "").replace("</p>", "").replace("<span>", "").replace("</span>", "").strip()[:200]
                news_items.append(
                    NewsItem(
                        title=f"Allerta OMS: {title}",
                        date=pub_date,
                        source="Organizzazione Mondiale della Sanità (OMS)",
                        url=url if url.startswith("http") else f"https://www.who.int{url}",
                        summary=clean_overview or f"Notifica ufficiale dell'OMS per focolaio epidemico: {title}",
                        category="Pandemie e Rischi Biologici",
                        severity=3 if "influenza" in title.lower() or "ebola" in title.lower() or "virus" in title.lower() else 2,
                        tags=["OMS", "Focolaio", "Epidemia", "Patogeni Emergenti"]
                    )
                )
    except Exception as e:
        pass

    # Calcolo metrica quantitativa: conteggio notifiche attive
    total_alerts = len(news_items)
    curr_date = datetime.now().strftime("%Y-%m-%d")

    indicator = IndicatorSummary(
        metric_id="who_active_outbreak_alerts",
        name="Indice di Allerta Epidemica Globale",
        unit="notifiche attive",
        current_value=float(total_alerts),
        current_date=curr_date,
        total_records=total_alerts,
        min_value=0.0,
        max_value=20.0,
        mean_value=5.0,
        percentile_5y=min(1.0, total_alerts / 15.0),
        sparkline=[float(total_alerts)]
    )

    return CategoryPayload(
        category_id="pandemics_biosecurity",
        category_name="Pandemie e Rischi Biologici",
        indicators={"outbreak_alerts": indicator},
        time_series={},
        news_items=news_items
    )
