"""
C2 & C4a — Movie Metadata and Credits Collection Module (Optimized Multi-threaded).
Implements Section 8, Section 10 (C4a), and Schema B1/B2 of project requirements.
Collects TMDB metadata, directors, cast with billing order, production companies, and budget.
Maintains raw fidelity and full provenance.
"""
import csv
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

from src.config import RAW_DATA_DIR, CACHE_HTML_DIR, HTTP_HEADERS, TMDB_API_KEY


def parse_currency_str(val_str: str) -> float:
    """Parses '$125,000,000' or similar into float."""
    if not val_str:
        return None
    cleaned = re.sub(r"[^\d.]", "", val_str)
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def fetch_movie_page(tmdb_id: int) -> tuple:
    """
    Fetches the main movie page and cast page from TMDB.
    Returns: (main_html, cast_html)
    """
    main_cache = CACHE_HTML_DIR / f"movie_{tmdb_id}.html"
    cast_cache = CACHE_HTML_DIR / f"movie_{tmdb_id}_cast.html"

    main_html = ""
    cast_html = ""

    if main_cache.exists():
        main_html = main_cache.read_text(encoding="utf-8", errors="ignore")
    else:
        url = f"https://www.themoviedb.org/movie/{tmdb_id}"
        try:
            r = requests.get(url, headers=HTTP_HEADERS, timeout=12)
            if r.status_code == 200:
                main_html = r.text
                main_cache.write_text(main_html, encoding="utf-8", errors="ignore")
                time.sleep(0.05)
        except Exception as e:
            pass

    if cast_cache.exists():
        cast_html = cast_cache.read_text(encoding="utf-8", errors="ignore")
    else:
        url = f"https://www.themoviedb.org/movie/{tmdb_id}/cast"
        try:
            r = requests.get(url, headers=HTTP_HEADERS, timeout=12)
            if r.status_code == 200:
                cast_html = r.text
                cast_cache.write_text(cast_html, encoding="utf-8", errors="ignore")
                time.sleep(0.05)
        except Exception as e:
            pass

    return main_html, cast_html


def parse_movie_details(tmdb_id: int, main_html: str, cast_html: str) -> dict:
    """
    Parses metadata, directors, cast, and budget from TMDB HTML.
    """
    details = {
        "budget": None,
        "director_ids": [],
        "lead_cast_ids": [],
        "production_company_ids": [],
        "credits": []
    }

    # 1. Parse Budget & Companies from Main HTML
    if main_html:
        soup_main = BeautifulSoup(main_html, "html.parser")
        for p in soup_main.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text.startswith("Budget") or "Budget" in text:
                m = re.search(r"Budget\s*(\$[\d,]+)", text)
                if m:
                    details["budget"] = parse_currency_str(m.group(1))
                    break

        for a in soup_main.find_all("a", href=re.compile(r"^/company/(\d+)")):
            m = re.match(r"^/company/(\d+)", a["href"])
            if m:
                cid = int(m.group(1))
                if cid not in details["production_company_ids"]:
                    details["production_company_ids"].append(cid)

    # 2. Parse Directors and Cast from Cast HTML
    if cast_html:
        soup_cast = BeautifulSoup(cast_html, "html.parser")

        # Directors
        for h4 in soup_cast.find_all("h4"):
            if "Directing" in h4.get_text():
                ol = h4.find_next_sibling("ol")
                if ol:
                    b_order = 0
                    for li in ol.find_all("li"):
                        text = li.get_text(" ", strip=True)
                        if "Director" in text and "Assistant" not in text and "Second Unit" not in text:
                            a = li.find("a", href=re.compile(r"^/person/(\d+)"))
                            if a:
                                m = re.match(r"^/person/(\d+)", a["href"])
                                pid = int(m.group(1))
                                pname = a.get_text(strip=True)
                                if pid not in details["director_ids"]:
                                    details["director_ids"].append(pid)
                                    details["credits"].append({
                                        "person_id": pid,
                                        "person_name": pname,
                                        "role": "director",
                                        "billing_order": b_order
                                    })
                                    b_order += 1

        # Cast
        cast_ol = soup_cast.find("ol", class_="people")
        if cast_ol:
            for b_order, li in enumerate(cast_ol.find_all("li")):
                a = li.find("a", href=re.compile(r"^/person/(\d+)"))
                if a:
                    m = re.match(r"^/person/(\d+)", a["href"])
                    pid = int(m.group(1))
                    p_texts = [p.get_text(strip=True) for p in li.find_all("p") if p.get_text(strip=True)]
                    pname = p_texts[0] if p_texts else a.get_text(strip=True)
                    details["lead_cast_ids"].append(pid)
                    details["credits"].append({
                        "person_id": pid,
                        "person_name": pname,
                        "role": "cast",
                        "billing_order": b_order
                    })

    return details


def process_single_film(r: dict, crosswalk: dict, collection_ids: dict, retrieval_date: str) -> tuple:
    f_key = r["film_key"]
    t_id = int(r["tmdb_id"])
    title = r["title_seed"]
    rel_date = r["release_date"]
    
    cw_rec = crosswalk.get(f_key, {})
    imdb_id = cw_rec.get("imdb_id", "")
    bom_id = cw_rec.get("bom_id", "")
    tmdb_cid = collection_ids.get(t_id, "")

    rel_month = None
    if rel_date:
        try:
            rel_month = int(rel_date.split("-")[1])
        except (IndexError, ValueError):
            pass

    main_html, cast_html = fetch_movie_page(t_id)
    details = parse_movie_details(t_id, main_html, cast_html)

    budget_val = details["budget"]
    budget_missing = (budget_val is None or budget_val <= 0)

    movie_record = {
        "film_key": f_key,
        "tmdb_id": t_id,
        "imdb_id": imdb_id,
        "bom_id": bom_id,
        "title": title,
        "release_date_ref": rel_date,
        "release_month": rel_month,
        "tmdb_collection_id": tmdb_cid,
        "director_ids": json.dumps(details["director_ids"]),
        "lead_cast_ids": json.dumps(details["lead_cast_ids"]),
        "production_company_ids": json.dumps(details["production_company_ids"]),
        "production_budget": budget_val,
        "budget_missing_flag": budget_missing,
        "critic_score": None,
        "audience_score": None,
        "source": f"https://www.themoviedb.org/movie/{t_id}",
        "retrieval_date": retrieval_date
    }

    credits_records = []
    for c in details["credits"]:
        credits_records.append({
            "film_key": f_key,
            "person_id": c["person_id"],
            "person_name": c["person_name"],
            "role": c["role"],
            "billing_order": c["billing_order"],
            "source": f"https://www.themoviedb.org/movie/{t_id}/cast",
            "retrieval_date": retrieval_date
        })

    return movie_record, credits_records


def collect_movie_metadata(max_workers: int = 8):
    """
    Executes C2 and C4a concurrently across registered films.
    """
    print(f"Running C2 & C4a — Movie Metadata & Credits Collection (workers={max_workers})...")
    
    reg_file = RAW_DATA_DIR / "film_registry.csv"
    cw_file = RAW_DATA_DIR / "id_crosswalk.csv"
    cand_file = RAW_DATA_DIR / "candidate_discovery.csv"

    if not reg_file.exists() or not cw_file.exists():
        raise FileNotFoundError("Missing prerequisite files.")

    crosswalk = {}
    with open(cw_file, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            crosswalk[r["film_key"]] = r

    collection_ids = {}
    with open(cand_file, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            collection_ids[int(r["tmdb_id"])] = r["tmdb_collection_id"]

    registered_films = []
    with open(reg_file, "r", encoding="utf-8") as f:
        registered_films = list(csv.DictReader(f))

    retrieval_date = datetime.now().strftime("%Y-%m-%d")
    movies_raw_records = []
    credits_raw_records = []

    print(f"Processing {len(registered_films)} films concurrently...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_film, r, crosswalk, collection_ids, retrieval_date): r["film_key"]
            for r in registered_films
        }
        completed = 0
        for future in as_completed(futures):
            m_rec, c_recs = future.result()
            movies_raw_records.append(m_rec)
            credits_raw_records.extend(c_recs)
            completed += 1
            if completed % 50 == 0 or completed == len(registered_films):
                print(f"  Processed {completed}/{len(registered_films)} films...")

    # Sort records by film_key for determinism
    movies_raw_records.sort(key=lambda x: x["film_key"])
    credits_raw_records.sort(key=lambda x: (x["film_key"], x["role"], x["billing_order"]))

    # Save movies_raw.csv
    m_path = RAW_DATA_DIR / "movies_raw.csv"
    with open(m_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "film_key", "tmdb_id", "imdb_id", "bom_id", "title",
            "release_date_ref", "release_month", "tmdb_collection_id",
            "director_ids", "lead_cast_ids", "production_company_ids",
            "production_budget", "budget_missing_flag", "critic_score",
            "audience_score", "source", "retrieval_date"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(movies_raw_records)

    # Save credits_raw.csv
    c_path = RAW_DATA_DIR / "credits_raw.csv"
    with open(c_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["film_key", "person_id", "person_name", "role", "billing_order", "source", "retrieval_date"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(credits_raw_records)

    print(f"C2 & C4a Completed: {len(movies_raw_records)} movies, {len(credits_raw_records)} credits recorded.")
    return movies_raw_records, credits_raw_records


if __name__ == "__main__":
    collect_movie_metadata()
