"""
Configuration and constants for ADY_PRJ Pilot Collection.
All settings strictly adhere to ADY_CONTENT .docx data requirements.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CACHE_DIR = DATA_DIR / "cache"
CACHE_HTML_DIR = CACHE_DIR / "html"
CACHE_JSON_DIR = CACHE_DIR / "json"
DATABASE_DIR = DATA_DIR / "database"
DB_PATH = DATABASE_DIR / "ady_pilot.db"

# Create directories if they don't exist
for d in [RAW_DATA_DIR, CACHE_HTML_DIR, CACHE_JSON_DIR, DATABASE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Exactly 40 Franchises from ADY_CONTENT .docx
FRANCHISE_SEEDS = [
    {"id": 1, "name": "James Bond", "notes": "Franchise dài, thay đổi diễn viên/đạo diễn", "search_term": "James Bond"},
    {"id": 2, "name": "Star Wars", "notes": "Franchise dài, nhiều thế hệ", "search_term": "Star Wars"},
    {"id": 3, "name": "Fast & Furious", "notes": "Franchise dài, cast thay đổi", "search_term": "Fast and the Furious"},
    {"id": 4, "name": "Mission: Impossible", "notes": "Franchise dài, diễn viên chính ổn định", "search_term": "Mission: Impossible"},
    {"id": 5, "name": "Harry Potter", "notes": "Franchise dài, cast trẻ em trưởng thành", "search_term": "Harry Potter"},
    {"id": 6, "name": "Jurassic Park / Jurassic World", "notes": "Sequel + reboot/thế hệ mới", "search_term": "Jurassic Park"},
    {"id": 7, "name": "Transformers", "notes": "Franchise dài, cast/director thay đổi", "search_term": "Transformers"},
    {"id": 8, "name": "X-Men", "notes": "Ensemble cast, nhiều thế hệ", "search_term": "X-Men"},
    {"id": 9, "name": "Planet of the Apes", "notes": "Reboot + nhiều thế hệ", "search_term": "Planet of the Apes"},
    {"id": 10, "name": "Rocky / Creed", "notes": "Franchise nối tiếp + spin-off", "search_term": "Rocky"},
    {"id": 11, "name": "Alien", "notes": "Franchise dài, sequel/reboot", "search_term": "Alien"},
    {"id": 12, "name": "Terminator", "notes": "Sequel + reboot, cast thay đổi", "search_term": "The Terminator"},
    {"id": 13, "name": "Predator", "notes": "Franchise dài, cast thay đổi", "search_term": "Predator"},
    {"id": 14, "name": "Scream", "notes": "Horror sequel, cast thay đổi", "search_term": "Scream"},
    {"id": 15, "name": "Halloween", "notes": "Horror + reboot nhiều lần", "search_term": "Halloween"},
    {"id": 16, "name": "Saw", "notes": "Horror sequel liên tục", "search_term": "Saw"},
    {"id": 17, "name": "Final Destination", "notes": "Horror anthology/sequel", "search_term": "Final Destination"},
    {"id": 18, "name": "Resident Evil", "notes": "Franchise dài, cast/director thay đổi", "search_term": "Resident Evil"},
    {"id": 19, "name": "The Bourne", "notes": "Franchise dài, lead actor thay đổi", "search_term": "The Bourne"},
    {"id": 20, "name": "Die Hard", "notes": "Franchise dài, khoảng cách giữa phim lớn", "search_term": "Die Hard"},
    {"id": 21, "name": "Indiana Jones", "notes": "Franchise dài, gap năm lớn", "search_term": "Indiana Jones"},
    {"id": 22, "name": "The Matrix", "notes": "Trilogy + sequel/revival", "search_term": "The Matrix"},
    {"id": 23, "name": "Mad Max", "notes": "Franchise dài, reboot", "search_term": "Mad Max"},
    {"id": 24, "name": "Pirates of the Caribbean", "notes": "Franchise dài, cast thay đổi", "search_term": "Pirates of the Caribbean"},
    {"id": 25, "name": "John Wick", "notes": "Franchise hiện đại, sequel liên tiếp", "search_term": "John Wick"},
    {"id": 26, "name": "The Hunger Games", "notes": "Franchise dài, cùng thế hệ nhân vật", "search_term": "The Hunger Games"},
    {"id": 27, "name": "Twilight", "notes": "Franchise dài, cast ổn định", "search_term": "The Twilight"},
    {"id": 28, "name": "Avatar", "notes": "Gap năm lớn, công nghệ/đạo diễn", "search_term": "Avatar"},
    {"id": 29, "name": "Toy Story", "notes": "Animation, cast lồng tiếng ổn định", "search_term": "Toy Story"},
    {"id": 30, "name": "Shrek", "notes": "Animation, franchise dài", "search_term": "Shrek"},
    {"id": 31, "name": "Ice Age", "notes": "Animation, franchise dài", "search_term": "Ice Age"},
    {"id": 32, "name": "Despicable Me", "notes": "Animation, sequel + spin-off", "search_term": "Despicable Me"},
    {"id": 33, "name": "Kung Fu Panda", "notes": "Animation, sequel", "search_term": "Kung Fu Panda"},
    {"id": 34, "name": "How to Train Your Dragon", "notes": "Animation + live-action remake", "search_term": "How to Train Your Dragon"},
    {"id": 35, "name": "Cars", "notes": "Animation, franchise dài", "search_term": "Cars"},
    {"id": 36, "name": "Hotel Transylvania", "notes": "Animation, sequel liên tiếp", "search_term": "Hotel Transylvania"},
    {"id": 37, "name": "Back to the Future", "notes": "Trilogy, khoảng cách ngắn", "search_term": "Back to the Future"},
    {"id": 38, "name": "The Godfather", "notes": "Trilogy, gap giữa phim", "search_term": "The Godfather"},
    {"id": 39, "name": "The Lord of the Rings", "notes": "Trilogy, cùng đạo diễn/cast", "search_term": "The Lord of the Rings"},
    {"id": 40, "name": "The Hobbit", "notes": "Trilogy, cùng đạo diễn/cast", "search_term": "The Hobbit"}
]

# Request headers for web scraping
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Optional TMDB API key from environment
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "").strip()
