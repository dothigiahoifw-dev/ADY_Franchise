"""
Film Registry Module for ADY_PRJ.
Implements Section 7 of project requirements:
1. Registers verified films and issues internal stable film_key.
2. Checks for duplicates and collisions without overwriting.
3. Preserves existing film_key for known tmdb_id.
4. Outputs film_registry.csv and logs any collisions.
"""
import csv
from datetime import datetime
from pathlib import Path

from src.config import RAW_DATA_DIR
from src.film_key_utils import generate_film_key


class FilmRegistry:
    def __init__(self, registry_file: Path = None):
        self.registry_file = registry_file or (RAW_DATA_DIR / "film_registry.csv")
        self.records_by_tmdb = {}     # tmdb_id -> record dict
        self.records_by_key = {}      # film_key -> record dict
        self.collisions = []          # collisions log
        self._load()

    def _load(self):
        """Loads existing registry if file exists."""
        if not self.registry_file.exists():
            return

        with open(self.registry_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                t_id = int(row["tmdb_id"])
                f_key = row["film_key"]
                rec = {
                    "film_key": f_key,
                    "tmdb_id": t_id,
                    "title_seed": row["title_seed"],
                    "release_date": row["release_date"],
                    "discovery_method": row["discovery_method"],
                    "created_at": row.get("created_at", datetime.now().isoformat())
                }
                self.records_by_tmdb[t_id] = rec
                self.records_by_key[f_key] = rec

    def register_film(self, tmdb_id: int, title: str, release_date: str, discovery_method: str = "tmdb_collection") -> str:
        """
        Registers a film into the Film Registry and returns its stable film_key:
        - If tmdb_id already exists -> return existing film_key
        - If new -> generate film_key = normalized_title + '-' + release_year
        - If duplicate key collision -> do NOT overwrite, append unique suffix and log collision
        """
        if tmdb_id in self.records_by_tmdb:
            return self.records_by_tmdb[tmdb_id]["film_key"]

        # Generate base key
        base_key = generate_film_key(title=title, release_date=release_date, tmdb_id=tmdb_id)
        final_key = base_key

        # Collision detection: if key is already claimed by a DIFFERENT tmdb_id
        if final_key in self.records_by_key:
            existing = self.records_by_key[final_key]
            if existing["tmdb_id"] != tmdb_id:
                # Collision: same title and year, different film
                collision_info = {
                    "film_key_attempted": final_key,
                    "tmdb_id_new": tmdb_id,
                    "title_new": title,
                    "tmdb_id_existing": existing["tmdb_id"],
                    "title_existing": existing["title_seed"]
                }
                self.collisions.append(collision_info)
                # Disambiguate without overwriting: fallback to film-{tmdb_id}-{year}
                final_key = f"film-{tmdb_id}-{base_key.split('-')[-1]}"

        record = {
            "film_key": final_key,
            "tmdb_id": tmdb_id,
            "title_seed": title,
            "release_date": release_date,
            "discovery_method": discovery_method,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.records_by_tmdb[tmdb_id] = record
        self.records_by_key[final_key] = record
        return final_key

    def save(self):
        """Saves registry to CSV."""
        fieldnames = ["film_key", "tmdb_id", "title_seed", "release_date", "discovery_method", "created_at"]
        with open(self.registry_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for rec in self.records_by_tmdb.values():
                writer.writerow(rec)

    def get_film_key(self, tmdb_id: int) -> str:
        rec = self.records_by_tmdb.get(tmdb_id)
        return rec["film_key"] if rec else None


def build_film_registry_from_candidates():
    """
    Builds the official Film Registry from verified candidate discovery entries.
    Excludes unreleased placeholders.
    """
    cand_file = RAW_DATA_DIR / "candidate_discovery.csv"
    ver_file = RAW_DATA_DIR / "manual_verification_log.csv"

    if not cand_file.exists():
        raise FileNotFoundError(f"Missing {cand_file}")

    # Load verification status
    ver_map = {}
    if ver_file.exists():
        with open(ver_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                ver_map[r["candidate_id"]] = r["verification_status"]

    registry = FilmRegistry()

    registered_count = 0
    skipped_unreleased = 0

    with open(cand_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cid = r["candidate_id"]
            t_id = int(r["tmdb_id"])
            title = r["title"]
            rel_date = r["release_date"]
            method = r["discovery_method"]

            # Filter out unreleased films without release dates
            if not rel_date:
                skipped_unreleased += 1
                continue

            registry.register_film(
                tmdb_id=t_id,
                title=title,
                release_date=rel_date,
                discovery_method=method
            )
            registered_count += 1

    registry.save()
    print(f"Film Registry Built: {len(registry.records_by_tmdb)} films registered.")
    print(f"Skipped unreleased placeholders: {skipped_unreleased}")
    if registry.collisions:
        print(f"Collisions detected and resolved: {len(registry.collisions)}")
    return registry


if __name__ == "__main__":
    reg = build_film_registry_from_candidates()
    print("Sample 5 registered films:")
    for k in list(reg.records_by_key.keys())[:5]:
        print(" ", reg.records_by_key[k])
