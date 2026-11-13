"""
C4 — Raw Data Collection Module (Box Office, Scores, Budget Backup).
Implements Section 10 of project requirements:
- C4b: Box Office Mojo opening collection by territory/scope.
- C4c: Rotten Tomatoes critic/audience score collection.
- C4d: The Numbers budget backup collection.
Maintains raw grain: film_key x market_scope x territory_code.
Does NOT calculate analytical fields (no Y, no _prev, no sequel_number).
"""
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

from src.config import RAW_DATA_DIR, CACHE_HTML_DIR, HTTP_HEADERS
from src.film_key_utils import normalize_slug


def parse_dollar_amount(val_str: str) -> float:
    """Parses strings like '$90,294,621' or '90294621' into float."""
    if not val_str or val_str.strip() in ["-", "–", "—", "N/A", ""]:
        return None
    cleaned = re.sub(r"[^\d.]", "", val_str)
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def fetch_bom_data(imdb_id: str, film_key: str) -> list:
    """
    Fetches Box Office Mojo data for a given movie using its IMDb ID.
    Extracts:
      1. Domestic opening weekend gross, theaters, days
      2. International / territory opening gross from release group if available
    Returns list of dicts formatted for box_office_raw.
    """
    records = []
    retrieval_date = datetime.now().strftime("%Y-%m-%d")
    source_url = f"https://www.boxofficemojo.com/title/{imdb_id}/"

    cache_file = CACHE_HTML_DIR / f"bom_{imdb_id}.html"
    html_content = ""
    if cache_file.exists():
        html_content = cache_file.read_text(encoding="utf-8", errors="ignore")
    else:
        try:
            r = requests.get(source_url, headers=HTTP_HEADERS, timeout=12)
            if r.status_code == 200:
                html_content = r.text
                cache_file.write_text(html_content, encoding="utf-8", errors="ignore")
                time.sleep(0.3)
        except Exception as e:
            print(f"Error fetching BOM {imdb_id}: {e}")

    if not html_content:
        # Record missing domestic row
        records.append({
            "film_key": film_key,
            "market_scope": "domestic",
            "territory_code": "Domestic",
            "local_release_date": "",
            "opening_gross": None,
            "opening_days_count": None,
            "opening_theater_count": None,
            "local_currency_gross": None,
            "missing_flag": True,
            "source": source_url,
            "retrieval_date": retrieval_date
        })
        return records

    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Domestic Opening extraction from title page
    domestic_opening = None
    domestic_theaters = None
    earliest_date = ""

    for div in soup.find_all("div", class_="a-section"):
        text = div.get_text(" ", strip=True)
        if "Domestic Opening" in text:
            m = re.search(r"Domestic Opening\s*(\$[\d,]+)", text)
            if m:
                domestic_opening = parse_dollar_amount(m.group(1))
        if "Earliest Release Date" in text:
            m = re.search(r"Earliest Release Date\s*([A-Za-z]+\s+\d+,\s+\d{4})", text)
            if m:
                earliest_date = m.group(1)

    # Check weekend link for theaters count and exact days
    weekend_link = soup.find("a", href=re.compile(r"/release/rl\d+/weekend"))
    opening_days = 3  # Standard Fri-Sun baseline unless holiday noted

    if weekend_link:
        rl_match = re.search(r"/release/(rl\d+)/weekend", weekend_link["href"])
        if rl_match:
            rl_id = rl_match.group(1)
            rl_cache = CACHE_HTML_DIR / f"bom_{rl_id}_weekend.html"
            rl_html = ""
            if rl_cache.exists():
                rl_html = rl_cache.read_text(encoding="utf-8", errors="ignore")
            else:
                try:
                    r_rl = requests.get(f"https://www.boxofficemojo.com/release/{rl_id}/weekend/", headers=HTTP_HEADERS, timeout=10)
                    if r_rl.status_code == 200:
                        rl_html = r_rl.text
                        rl_cache.write_text(rl_html, encoding="utf-8", errors="ignore")
                        time.sleep(0.2)
                except Exception:
                    pass

            if rl_html:
                soup_wk = BeautifulSoup(rl_html, "html.parser")
                wk_table = soup_wk.find("table")
                if wk_table:
                    rows = wk_table.find_all("tr")
                    if len(rows) > 1:
                        cols = [td.get_text(strip=True) for td in rows[1].find_all(["td", "th"])]
                        # Format: Date, Rank, Weekend, %, Theaters, Change, Avg, To Date
                        if len(cols) >= 5:
                            date_desc = cols[0]
                            if "4-Day" in date_desc:
                                opening_days = 4
                            elif "5-Day" in date_desc:
                                opening_days = 5
                            th_val = parse_dollar_amount(cols[4])
                            if th_val:
                                domestic_theaters = int(th_val)

    records.append({
        "film_key": film_key,
        "market_scope": "domestic",
        "territory_code": "Domestic",
        "local_release_date": earliest_date,
        "opening_gross": domestic_opening,
        "opening_days_count": opening_days if domestic_opening else None,
        "opening_theater_count": domestic_theaters,
        "local_currency_gross": None,
        "missing_flag": (domestic_opening is None),
        "source": source_url,
        "retrieval_date": retrieval_date
    })

    # 2. International Release Group Check
    # Look for original release group (e.g. /releasegroup/gr.../)
    rg_link = soup.find("a", href=re.compile(r"/releasegroup/gr\d+/"))
    if rg_link:
        rg_url = "https://www.boxofficemojo.com" + rg_link["href"]
        m_gr = re.search(r"/releasegroup/(gr\d+)/", rg_link["href"])
        if m_gr:
            gr_id = m_gr.group(1)
            gr_cache = CACHE_HTML_DIR / f"bom_{gr_id}.html"
            gr_html = ""
            if gr_cache.exists():
                gr_html = gr_cache.read_text(encoding="utf-8", errors="ignore")
            else:
                try:
                    r_gr = requests.get(rg_url, headers=HTTP_HEADERS, timeout=10)
                    if r_gr.status_code == 200:
                        gr_html = r_gr.text
                        gr_cache.write_text(gr_html, encoding="utf-8", errors="ignore")
                        time.sleep(0.2)
                except Exception:
                    pass

            if gr_html:
                soup_gr = BeautifulSoup(gr_html, "html.parser")
                # Parse territory tables
                for t in soup_gr.find_all("table"):
                    headers = [th.get_text(strip=True) for th in t.find_all("th")]
                    if "Opening" in headers and "Market" in headers:
                        market_idx = headers.index("Market")
                        date_idx = headers.index("Release Date") if "Release Date" in headers else 1
                        open_idx = headers.index("Opening")

                        for tr in t.find_all("tr")[1:]:
                            tds = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                            if len(tds) > open_idx:
                                mkt = tds[market_idx]
                                if mkt == "Domestic" or not mkt:
                                    continue
                                local_d = tds[date_idx] if len(tds) > date_idx else ""
                                open_val = parse_dollar_amount(tds[open_idx])
                                records.append({
                                    "film_key": film_key,
                                    "market_scope": "territory",
                                    "territory_code": mkt,
                                    "local_release_date": local_d,
                                    "opening_gross": open_val,
                                    "opening_days_count": None,  # unrecorded in BOM releasegroup summary
                                    "opening_theater_count": None,
                                    "local_currency_gross": None,
                                    "missing_flag": (open_val is None),
                                    "source": rg_url,
                                    "retrieval_date": retrieval_date
                                })

    return records


def fetch_rt_scores(film_key: str, title: str, release_date: str) -> tuple:
    """
    Fetches Rotten Tomatoes critic score and audience score.
    Returns: (critic_score, audience_score, source_url)
    """
    retrieval_date = datetime.now().strftime("%Y-%m-%d")
    slug = normalize_slug(title).replace("-", "_")
    
    # Try slug variations: title_year, title
    year = release_date.split("-")[0] if release_date else ""
    urls_to_try = [
        f"https://www.rottentomatoes.com/m/{slug}_{year}" if year else "",
        f"https://www.rottentomatoes.com/m/{slug}"
    ]
    urls_to_try = [u for u in urls_to_try if u]

    for url in urls_to_try:
        cache_file = CACHE_HTML_DIR / f"rt_{url.split('/')[-1]}.html"
        html_content = ""
        if cache_file.exists():
            html_content = cache_file.read_text(encoding="utf-8", errors="ignore")
        else:
            try:
                r = requests.get(url, headers=HTTP_HEADERS, timeout=8)
                if r.status_code == 200:
                    html_content = r.text
                    cache_file.write_text(html_content, encoding="utf-8", errors="ignore")
                    time.sleep(0.2)
            except Exception:
                continue

        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            critic = None
            audience = None

            # New RT layout with <rt-text slot="critics-score">
            crit_elem = soup.find("rt-text", attrs={"slot": "critics-score"})
            if crit_elem:
                m = re.search(r"(\d+)%", crit_elem.get_text())
                if m:
                    critic = float(m.group(1))

            aud_elem = soup.find("rt-text", attrs={"slot": "audience-score"})
            if aud_elem:
                m = re.search(r"(\d+)%", aud_elem.get_text())
                if m:
                    audience = float(m.group(1))

            # Old layout fallback
            if critic is None or audience is None:
                sb = soup.find("score-board")
                if sb:
                    if critic is None and sb.get("tomatometerscore"):
                        try:
                            critic = float(sb.get("tomatometerscore"))
                        except ValueError:
                            pass
                    if audience is None and sb.get("audiencescore"):
                        try:
                            audience = float(sb.get("audiencescore"))
                        except ValueError:
                            pass

            if critic is not None or audience is not None:
                return critic, audience, url

    return None, None, ""


def fetch_the_numbers_budget(title: str, release_date: str) -> float:
    """
    Queries The Numbers for production budget backup.
    Returns: production_budget (float) or None
    """
    clean_title = re.sub(r"[^\w\s]", "", title).strip()
    words = clean_title.split()
    if not words:
        return None

    # Common URL patterns on The Numbers: Title-The, Title, Title-Year
    slug = "-".join(words)
    url = f"https://www.the-numbers.com/movie/{slug}"

    cache_file = CACHE_HTML_DIR / f"numbers_{slug}.html"
    html_content = ""
    if cache_file.exists():
        html_content = cache_file.read_text(encoding="utf-8", errors="ignore")
    else:
        try:
            r = requests.get(url, headers=HTTP_HEADERS, timeout=8)
            if r.status_code == 200:
                html_content = r.text
                cache_file.write_text(html_content, encoding="utf-8", errors="ignore")
                time.sleep(0.2)
        except Exception:
            return None

    if html_content:
        for line in html_content.splitlines():
            if "Production" in line and "Budget" in line and "$" in line:
                m = re.search(r"Production\s*Budget:\s*(\$[\d,]+)", line)
                if m:
                    return parse_dollar_amount(m.group(1))
    return None
