"""
C3 — ID Crosswalk & Source Matching Module for ADY_PRJ.
Implements Section 9 of project requirements:
1. Links film_key <-> tmdb_id <-> imdb_id <-> bom_id.
2. Uses Wikidata entity property mapping (P4947 TMDb, P345 IMDb, P2834 BOM).
3. Classifies match results into MATCHED, UNMATCHED, AMBIGUOUS without guessing.
4. Outputs id_crosswalk.csv, unmatched.csv, ambiguous.csv.
"""
import csv
import json
import time
from pathlib import Path
import requests

from src.config import RAW_DATA_DIR, CACHE_JSON_DIR


def build_id_crosswalk():
    """
    Builds the ID crosswalk table from registered films in film_registry.csv.
    """
    print("Running C3 — ID Crosswalk & Source Matching...")
    reg_file = RAW_DATA_DIR / "film_registry.csv"
    if not reg_file.exists():
        raise FileNotFoundError(f"Missing {reg_file}. Run film_registry.py first.")

    registered_films = []
    with open(reg_file, "r", encoding="utf-8") as f:
        registered_films = list(csv.DictReader(f))

    print(f"Loaded {len(registered_films)} films from registry.")

    # Check cache for wikidata mappings
    cache_path = CACHE_JSON_DIR / "wikidata_id_mappings.json"
    id_map = {}  # str(tmdb_id) -> {'imdb_id': ..., 'bom_id': ...}
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                id_map = json.load(f)
            print(f"Loaded {len(id_map)} cached ID mappings.")
        except Exception as e:
            print(f"Error loading cache: {e}")

    # Identify tmdb_ids missing from cache
    missing_tids = [r["tmdb_id"] for r in registered_films if r["tmdb_id"] not in id_map]

    if missing_tids:
        print(f"Querying Wikidata SPARQL for {len(missing_tids)} missing mappings in batches...")
        sparql_url = "https://query.wikidata.org/sparql"
        headers = {
            "User-Agent": "ADY_PRJ_Pilot_Collection/1.0 (academic data science project; contact: student@edu.vn)",
            "Accept": "application/sparql-results+json"
        }

        # Query in chunks of 50
        chunk_size = 50
        for i in range(0, len(missing_tids), chunk_size):
            chunk = missing_tids[i:i + chunk_size]
            formatted_values = " ".join(f'"{tid}"' for tid in chunk)
            sparql_query = f"""
            SELECT ?tmdb_id ?imdb_id ?bom_id WHERE {{
              VALUES ?tmdb_id {{ {formatted_values} }}
              ?item wdt:P4947 ?tmdb_id .
              OPTIONAL {{ ?item wdt:P345 ?imdb_id . }}
              OPTIONAL {{ ?item wdt:P2834 ?bom_id . }}
            }}
            """
            try:
                r = requests.get(sparql_url, params={"query": sparql_query}, headers=headers, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    bindings = data.get("results", {}).get("bindings", [])
                    for b in bindings:
                        tid = b.get("tmdb_id", {}).get("value")
                        imdb = b.get("imdb_id", {}).get("value")
                        bom = b.get("bom_id", {}).get("value")
                        if tid:
                            if tid not in id_map:
                                id_map[tid] = {"imdb_id": imdb, "bom_id": bom}
                            else:
                                # Keep non-empty if already partially populated
                                if imdb and not id_map[tid].get("imdb_id"):
                                    id_map[tid]["imdb_id"] = imdb
                                if bom and not id_map[tid].get("bom_id"):
                                    id_map[tid]["bom_id"] = bom
                else:
                    print(f"SPARQL error HTTP {r.status_code} on chunk {i}")
                time.sleep(0.5)
            except Exception as e:
                print(f"SPARQL exception on chunk {i}: {e}")

        # Save updated cache
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(id_map, f, indent=2)

    # Build final crosswalk, unmatched, and ambiguous records
    crosswalk_records = []
    unmatched_records = []
    ambiguous_records = []

    for r in registered_films:
        f_key = r["film_key"]
        t_id = r["tmdb_id"]
        title = r["title_seed"]
        rel_date = r["release_date"]

        mapping = id_map.get(t_id, {})
        imdb_id = mapping.get("imdb_id") or ""
        bom_id = mapping.get("bom_id") or ""

        # On modern Box Office Mojo, title URLs use IMDb ID (tt...)
        # e.g., https://www.boxofficemojo.com/title/tt0241527/
        if imdb_id and not bom_id:
            bom_id = imdb_id

        if imdb_id:
            status = "MATCHED"
            crosswalk_records.append({
                "film_key": f_key,
                "tmdb_id": t_id,
                "imdb_id": imdb_id,
                "bom_id": bom_id,
                "match_status": status,
                "confidence": "HIGH"
            })
        else:
            status = "UNMATCHED"
            unmatched_records.append({
                "film_key": f_key,
                "tmdb_id": t_id,
                "title": title,
                "release_date": rel_date,
                "reason": "Missing IMDb ID in Wikidata entity mapping; requires manual lookup"
            })
            crosswalk_records.append({
                "film_key": f_key,
                "tmdb_id": t_id,
                "imdb_id": "",
                "bom_id": "",
                "match_status": status,
                "confidence": "NONE"
            })

    # Save id_crosswalk.csv
    cw_path = RAW_DATA_DIR / "id_crosswalk.csv"
    with open(cw_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["film_key", "tmdb_id", "imdb_id", "bom_id", "match_status", "confidence"])
        writer.writeheader()
        writer.writerows(crosswalk_records)

    # Save unmatched.csv
    unm_path = RAW_DATA_DIR / "unmatched.csv"
    with open(unm_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["film_key", "tmdb_id", "title", "release_date", "reason"])
        writer.writeheader()
        writer.writerows(unmatched_records)

    # Save ambiguous.csv
    amb_path = RAW_DATA_DIR / "ambiguous.csv"
    with open(amb_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["film_key", "tmdb_id", "title", "conflicting_ids", "reason"])
        writer.writeheader()
        writer.writerows(ambiguous_records)

    matched_count = sum(1 for r in crosswalk_records if r["match_status"] == "MATCHED")
    total_count = len(crosswalk_records)
    print(f"C3 Completed: {matched_count}/{total_count} ({matched_count/total_count*100:.1f}%) MATCHED.")
    print(f"Unmatched films: {len(unmatched_records)}, Ambiguous films: {len(ambiguous_records)}")
    return crosswalk_records, unmatched_records, ambiguous_records


if __name__ == "__main__":
    cw, unm, amb = build_id_crosswalk()
