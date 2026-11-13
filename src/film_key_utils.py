"""
Utility functions for generating and validating stable film_key values.
Strictly adheres to Section 3 and Section 1966-2000 of the project document.
"""
import re
import unicodedata


def normalize_slug(title: str) -> str:
    """
    Normalizes a movie title into a clean URL-friendly slug:
    1. Strip diacritics/accents (é -> e, ç -> c, ü -> u, etc.)
    2. Lowercase
    3. Replace non-alphanumeric characters with '-'
    4. Collapse consecutive '-'
    5. Strip leading/trailing '-'
    """
    if not title:
        return ""

    # Special character replacements
    text = title.replace("&", " and ")
    
    # Decompose unicode characters into base character + accent, then drop accents
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Lowercase
    text = text.lower()

    # Replace any character other than a-z, 0-9 with '-'
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # Collapse consecutive '-'
    text = re.sub(r"-+", "-", text)

    # Strip leading/trailing '-'
    text = text.strip("-")

    return text


def generate_film_key(title: str, release_date: str, tmdb_id: int = None) -> str:
    """
    Generates internal stable film_key:
    Standard format: {slug}-{release_year}
    Fallback format: film-{tmdb_id}-{release_year}
    Fallback triggers:
      - Title is non-Latin or slug is empty
      - Slug is purely numeric (e.g. '2046', '2.0' to prevent Excel auto-format bugs)
    """
    year = ""
    if release_date:
        match = re.search(r"\b(19\d\d|20\d\d)\b", str(release_date))
        if match:
            year = match.group(1)

    slug = normalize_slug(title)

    # Condition a & b: slug empty or non-Latin
    if not slug:
        if tmdb_id and year:
            return f"film-{tmdb_id}-{year}"
        elif tmdb_id:
            return f"film-{tmdb_id}-unknown"
        return f"film-unknown-{year or 'unknown'}"

    # Condition c: slug is purely numeric (e.g. '2046')
    if slug.isdigit():
        if tmdb_id:
            return f"film-{tmdb_id}-{year or slug}"
        return f"film-{slug}-{year or 'unknown'}"

    if year:
        return f"{slug}-{year}"
    return f"{slug}-unknown"
