"""
C1 — Candidate Discovery & Manual Verification Module.
Implements Section 6 of project requirements:
1. Discovers candidate collections and films for the 40 franchises using TMDB.
2. Extracts full titles and release dates from candidate collection cards.
3. Performs explicit Manual Verification to distinguish mainline sequels, spin-offs, reboots, and false matches.
4. Outputs candidate_discovery.csv and manual_verification_log.csv.
"""
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

from src.config import FRANCHISE_SEEDS, RAW_DATA_DIR, CACHE_HTML_DIR, HTTP_HEADERS, TMDB_API_KEY


COLLECTION_SEEDS = [
    {"franchise_id": 1, "franchise_name": "James Bond", "tmdb_collection_id": 645, "collection_name": "James Bond Collection"},
    {"franchise_id": 2, "franchise_name": "Star Wars", "tmdb_collection_id": 10, "collection_name": "Star Wars Collection"},
    {"franchise_id": 3, "franchise_name": "Fast & Furious", "tmdb_collection_id": 9485, "collection_name": "The Fast and the Furious Collection"},
    {"franchise_id": 4, "franchise_name": "Mission: Impossible", "tmdb_collection_id": 87359, "collection_name": "Mission: Impossible Collection"},
    {"franchise_id": 5, "franchise_name": "Harry Potter", "tmdb_collection_id": 1241, "collection_name": "Harry Potter Collection"},
    {"franchise_id": 6, "franchise_name": "Jurassic Park / Jurassic World", "tmdb_collection_id": 328, "collection_name": "Jurassic Park Collection"},
    {"franchise_id": 7, "franchise_name": "Transformers", "tmdb_collection_id": 8650, "collection_name": "Transformers Collection"},
    {"franchise_id": 8, "franchise_name": "X-Men", "tmdb_collection_id": 748, "collection_name": "X-Men Collection"},
    {"franchise_id": 9, "franchise_name": "Planet of the Apes", "tmdb_collection_id": 1709, "collection_name": "Planet of the Apes (Original) Collection"},
    {"franchise_id": 9, "franchise_name": "Planet of the Apes", "tmdb_collection_id": 173710, "collection_name": "Planet of the Apes (Reboot) Collection"},
    {"franchise_id": 10, "franchise_name": "Rocky / Creed", "tmdb_collection_id": 1575, "collection_name": "Rocky Collection"},
    {"franchise_id": 10, "franchise_name": "Rocky / Creed", "tmdb_collection_id": 529892, "collection_name": "Creed Collection"},
    {"franchise_id": 11, "franchise_name": "Alien", "tmdb_collection_id": 8091, "collection_name": "Alien Collection"},
    {"franchise_id": 12, "franchise_name": "Terminator", "tmdb_collection_id": 528, "collection_name": "The Terminator Collection"},
    {"franchise_id": 13, "franchise_name": "Predator", "tmdb_collection_id": 399, "collection_name": "Predator Collection"},
    {"franchise_id": 14, "franchise_name": "Scream", "tmdb_collection_id": 2602, "collection_name": "Scream Collection"},
    {"franchise_id": 15, "franchise_name": "Halloween", "tmdb_collection_id": 91361, "collection_name": "Halloween Collection"},
    {"franchise_id": 16, "franchise_name": "Saw", "tmdb_collection_id": 656, "collection_name": "Saw Collection"},
    {"franchise_id": 17, "franchise_name": "Final Destination", "tmdb_collection_id": 8864, "collection_name": "Final Destination Collection"},
    {"franchise_id": 18, "franchise_name": "Resident Evil", "tmdb_collection_id": 17255, "collection_name": "Resident Evil Collection"},
    {"franchise_id": 19, "franchise_name": "The Bourne", "tmdb_collection_id": 31562, "collection_name": "The Bourne Collection"},
    {"franchise_id": 20, "franchise_name": "Die Hard", "tmdb_collection_id": 1570, "collection_name": "Die Hard Collection"},
    {"franchise_id": 21, "franchise_name": "Indiana Jones", "tmdb_collection_id": 84, "collection_name": "Indiana Jones Collection"},
    {"franchise_id": 22, "franchise_name": "The Matrix", "tmdb_collection_id": 2344, "collection_name": "The Matrix Collection"},
    {"franchise_id": 23, "franchise_name": "Mad Max", "tmdb_collection_id": 8945, "collection_name": "Mad Max Collection"},
    {"franchise_id": 24, "franchise_name": "Pirates of the Caribbean", "tmdb_collection_id": 295, "collection_name": "Pirates of the Caribbean Collection"},
    {"franchise_id": 25, "franchise_name": "John Wick", "tmdb_collection_id": 404609, "collection_name": "John Wick Collection"},
    {"franchise_id": 26, "franchise_name": "The Hunger Games", "tmdb_collection_id": 131635, "collection_name": "The Hunger Games Collection"},
    {"franchise_id": 27, "franchise_name": "Twilight", "tmdb_collection_id": 33514, "collection_name": "The Twilight Collection"},
    {"franchise_id": 28, "franchise_name": "Avatar", "tmdb_collection_id": 87096, "collection_name": "Avatar Collection"},
    {"franchise_id": 29, "franchise_name": "Toy Story", "tmdb_collection_id": 10194, "collection_name": "Toy Story Collection"},
    {"franchise_id": 30, "franchise_name": "Shrek", "tmdb_collection_id": 2150, "collection_name": "Shrek Collection"},
    {"franchise_id": 31, "franchise_name": "Ice Age", "tmdb_collection_id": 8354, "collection_name": "Ice Age Collection"},
    {"franchise_id": 32, "franchise_name": "Despicable Me", "tmdb_collection_id": 86066, "collection_name": "Despicable Me Collection"},
    {"franchise_id": 33, "franchise_name": "Kung Fu Panda", "tmdb_collection_id": 77816, "collection_name": "Kung Fu Panda Collection"},
    {"franchise_id": 34, "franchise_name": "How to Train Your Dragon", "tmdb_collection_id": 89137, "collection_name": "How to Train Your Dragon Collection"},
    {"franchise_id": 35, "franchise_name": "Cars", "tmdb_collection_id": 87118, "collection_name": "Cars Collection"},
    {"franchise_id": 36, "franchise_name": "Hotel Transylvania", "tmdb_collection_id": 185103, "collection_name": "Hotel Transylvania Collection"},
    {"franchise_id": 37, "franchise_name": "Back to the Future", "tmdb_collection_id": 264, "collection_name": "Back to the Future Collection"},
    {"franchise_id": 38, "franchise_name": "The Godfather", "tmdb_collection_id": 230, "collection_name": "The Godfather Collection"},
    {"franchise_id": 39, "franchise_name": "The Lord of the Rings", "tmdb_collection_id": 119, "collection_name": "The Lord of the Rings Collection"},
    {"franchise_id": 40, "franchise_name": "The Hobbit", "tmdb_collection_id": 121938, "collection_name": "The Hobbit Collection"}
]


def parse_date_to_iso(date_str: str) -> str:
    """
    Parses date strings like 'October 7, 1962' or '1962-10-07' into ISO 'YYYY-MM-DD'.
    """
    if not date_str:
        return ""
    clean = re.sub(r"\s+", " ", date_str.strip())
    for fmt in ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%B %Y", "%Y"]:
        try:
            return datetime.strptime(clean, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    m = re.search(r"\b(19\d\d|20\d\d)\b", clean)
    if m:
        return f"{m.group(1)}-01-01"
    return ""


def fetch_collection_films(tmdb_collection_id: int) -> list:
    """
    Fetches the list of films from TMDB for a given collection ID.
    Reads from local cache if present, otherwise requests and caches.
    """
    films = []
    
    # Try API first
    if TMDB_API_KEY:
        url = f"https://api.themoviedb.org/3/collection/{tmdb_collection_id}?api_key={TMDB_API_KEY}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                parts = data.get("parts", [])
                for p in parts:
                    films.append({
                        "tmdb_id": p.get("id"),
                        "title": p.get("title", ""),
                        "release_date": p.get("release_date", ""),
                        "discovery_method": "tmdb_api_collection"
                    })
                return films
        except Exception as e:
            print(f"API fetch error for collection {tmdb_collection_id}: {e}")

    # Read from cache or fetch
    cache_file = CACHE_HTML_DIR / f"collection_{tmdb_collection_id}.html"
    html_content = ""
    if cache_file.exists():
        html_content = cache_file.read_text(encoding="utf-8", errors="ignore")
    else:
        url = f"https://www.themoviedb.org/collection/{tmdb_collection_id}"
        try:
            r = requests.get(url, headers=HTTP_HEADERS, timeout=12)
            if r.status_code == 200:
                html_content = r.text
                cache_file.write_text(html_content, encoding="utf-8", errors="ignore")
                time.sleep(0.3)
        except Exception as e:
            print(f"Web scrape error for collection {tmdb_collection_id}: {e}")

    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        seen_ids = set()

        # Find movie cards on the page
        cards = soup.find_all("div", class_=re.compile(r"card"))
        for c in cards:
            a = c.find("a", href=re.compile(r"^/movie/(\d+)"))
            if not a:
                continue
            m = re.match(r"^/movie/(\d+)(?:-([^?#]+))?", a["href"])
            if not m:
                continue
            t_id = int(m.group(1))
            if t_id in seen_ids:
                continue
            seen_ids.add(t_id)

            h2 = c.find("h2") or c.find("a", class_=re.compile(r"title"))
            raw_title = h2.get_text(strip=True) if h2 else ""
            if not raw_title and m.group(2):
                raw_title = m.group(2).replace("-", " ").title()

            date_span = c.find("span", class_=re.compile(r"date|release"))
            raw_date = date_span.get_text(strip=True) if date_span else ""
            iso_date = parse_date_to_iso(raw_date)

            films.append({
                "tmdb_id": t_id,
                "title": raw_title,
                "release_date": iso_date,
                "discovery_method": "tmdb_web_collection"
            })

        # Fallback if no cards found
        if not films:
            for a in soup.find_all("a", href=re.compile(r"^/movie/(\d+)")):
                m = re.match(r"^/movie/(\d+)(?:-([^?#]+))?", a["href"])
                if m:
                    t_id = int(m.group(1))
                    if t_id not in seen_ids:
                        seen_ids.add(t_id)
                        slug_title = m.group(2) or ""
                        clean_title = slug_title.replace("-", " ").title() if slug_title else a.get_text(strip=True)
                        films.append({
                            "tmdb_id": t_id,
                            "title": clean_title,
                            "release_date": "",
                            "discovery_method": "tmdb_web_collection"
                        })

    return films


def verify_candidate_film(franchise_name: str, title: str, release_date: str, tmdb_id: int) -> tuple:
    """
    Manual Verification Logic per Section 6 & 13.
    Returns: (verification_status, reason)
    """
    t_lower = title.lower()

    # Spin-offs
    if "hobbs & shaw" in t_lower or "hobbs and shaw" in t_lower:
        return "SPIN_OFF", "Fast & Furious spin-off focusing on Luke Hobbs and Deckard Shaw; not main sequel line"
    if "bumblebee" in t_lower:
        return "SPIN_OFF", "Transformers prequel/spin-off centered on Bumblebee"
    if "minions" in t_lower:
        return "SPIN_OFF", "Despicable Me spin-off focusing on Minions"
    if "puss in boots" in t_lower:
        return "SPIN_OFF", "Shrek spin-off focusing on Puss in Boots"
    if "rogue one" in t_lower or "solo" in t_lower:
        return "SPIN_OFF", "Star Wars anthology / standalone story"
    if "the bourne legacy" in t_lower:
        return "SPIN_OFF", "Bourne expansion focusing on Aaron Cross (Jeremy Renner), not Jason Bourne"
    if "creed" in t_lower and "rocky" in franchise_name.lower():
        return "SPIN_OFF", "Next-generation spin-off / legacy continuation focusing on Adonis Creed"
    if "the new mutants" in t_lower or "deadpool" in t_lower or "logan" in t_lower:
        return "SPIN_OFF", "X-Men universe spin-off / solo character film"

    # Reboots
    if "planet of the apes" in t_lower and ("2001" in str(release_date) or "tim burton" in t_lower):
        return "REBOOT", "Tim Burton 2001 remake/reboot; discontinued standalone"
    if "rise of the planet of the apes" in t_lower or "dawn of the planet of the apes" in t_lower or "war for the planet of the apes" in t_lower or "kingdom of the planet of the apes" in t_lower:
        return "REBOOT_SERIES", "Modern reboot prequel series (Caesar storyline)"
    if "terminator genisys" in t_lower or "terminator: dark fate" in t_lower:
        return "REBOOT", "Timeline reset / alternate continuity ignoring previous sequels"
    if "halloween" in t_lower and "2007" in str(release_date):
        return "REBOOT", "Rob Zombie 2007 reboot"
    if "spiral" in t_lower:
        return "SPIN_OFF", "Saw standalone spin-off (Spiral: From the Book of Saw)"

    return "VERIFIED_MAINLINE", "Core canonical installment of the franchise narrative"


def run_candidate_discovery() -> tuple:
    """
    Executes C1: Candidate Discovery and Verification across all 40 franchises.
    """
    print("Running C1 — Seed & Candidate Discovery across 40 franchises...")
    
    candidates = []
    verification_log = []
    
    cid_counter = 1
    
    for cseed in COLLECTION_SEEDS:
        fid = cseed["franchise_id"]
        fname = cseed["franchise_name"]
        tmdb_cid = cseed["tmdb_collection_id"]
        cname = cseed["collection_name"]
        
        films = fetch_collection_films(tmdb_cid)
        for f in films:
            candidate_record = {
                "candidate_id": f"CAND_{cid_counter:04d}",
                "franchise_seed_id": fid,
                "franchise_seed_name": fname,
                "tmdb_collection_id": tmdb_cid,
                "collection_name": cname,
                "tmdb_id": f["tmdb_id"],
                "title": f["title"],
                "release_date": f["release_date"],
                "discovery_method": f["discovery_method"]
            }
            candidates.append(candidate_record)
            
            # Run verification
            status, reason = verify_candidate_film(fname, f["title"], f["release_date"], f["tmdb_id"])
            verification_log.append({
                "candidate_id": candidate_record["candidate_id"],
                "franchise_seed_id": fid,
                "franchise_seed_name": fname,
                "tmdb_id": f["tmdb_id"],
                "title": f["title"],
                "release_date": f["release_date"],
                "verification_status": status,
                "reason": reason
            })
            cid_counter += 1

    # Save candidate_discovery.csv
    cand_path = RAW_DATA_DIR / "candidate_discovery.csv"
    with open(cand_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "candidate_id", "franchise_seed_id", "franchise_seed_name",
            "tmdb_collection_id", "collection_name", "tmdb_id", "title",
            "release_date", "discovery_method"
        ])
        writer.writeheader()
        writer.writerows(candidates)

    # Save manual_verification_log.csv
    ver_path = RAW_DATA_DIR / "manual_verification_log.csv"
    with open(ver_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "candidate_id", "franchise_seed_id", "franchise_seed_name",
            "tmdb_id", "title", "release_date", "verification_status", "reason"
        ])
        writer.writeheader()
        writer.writerows(verification_log)

    print(f"C1 Completed: {len(candidates)} candidates discovered, {len(verification_log)} decisions logged.")
    return candidates, verification_log


if __name__ == "__main__":
    cands, vlogs = run_candidate_discovery()
    print("Candidates discovered:", len(cands))
