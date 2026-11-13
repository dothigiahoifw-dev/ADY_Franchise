import csv, hashlib, json, os, re, sys, time, datetime as dt
from pathlib import Path
from urllib.parse import quote
import requests

OUT = Path(os.environ.get("ADY_OUT", "ady_pilot_out"))
CACHE = OUT / "cache"
TODAY = dt.date.today().isoformat()
RT_BASE = "https://www.rottentomatoes.com"
RT_SEARCH_URL = f"{RT_BASE}/search"

for d in (OUT, CACHE / "rt"):
    d.mkdir(parents=True, exist_ok=True)

# SỬA CHỖ 1: Thay thế UA cơ bản bằng BROWSER_HEADERS để giả lập Chrome thật
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": RT_BASE + "/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

SESSION = requests.Session()
SESSION.headers.update(BROWSER_HEADERS)

# ---------- HELPERS (Giữ nguyên) ----------
def write_csv(name, rows, fields):
    if not rows: return
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def read_csv(name):
    p = OUT / name
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))

class IssueLog:
    FIELDS = ["issue_id", "source", "film_key_or_record", "field", "problem", "action", "result", "status"]
    def __init__(self):
        self.rows = read_csv("issue_log.csv")
    def add(self, source, record, field, problem, action="logged", result="", status="OPEN"):
        self.rows.append(dict(issue_id=f"I-{len(self.rows)+1:04d}", source=source, film_key_or_record=record,
                              field=field, problem=problem, action=action, result=result, status=status))
    def save(self):
        try:
            write_csv("issue_log.csv", self.rows, self.FIELDS)
        except PermissionError:
            # Excel/LibreOffice thường khóa CSV. Không để lỗi này làm hỏng C6/C7.
            fallback = OUT / "issue_log_pending.csv"
            with open(fallback, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=self.FIELDS, extrasaction="ignore")
                w.writeheader()
                w.writerows(self.rows)
            print(
                f"\n[WARNING] Không thể ghi {OUT / 'issue_log.csv'} "
                f"(file có thể đang mở). Đã ghi tạm vào {fallback}."
            )

LOG = IssueLog()
_last = {}

def get(url, source, params=None, cache_file=None, delay=1.0):
    if cache_file and cache_file.exists():
        return 200, cache_file.read_text(encoding="utf-8")

    wait = delay - (time.time() - _last.get(source, 0))
    if wait > 0:
        time.sleep(wait)

    for attempt in range(3):
        try:
            r = SESSION.get(
                url,
                params=params,
                timeout=30,
                allow_redirects=True,
            )
            _last[source] = time.time()

            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue

            if r.status_code in (403, 502, 503, 504):
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue

            if cache_file and r.status_code == 200:
                cache_file.write_text(r.text, encoding="utf-8")

            return r.status_code, r.text

        except requests.RequestException as e:
            LOG.add(
                source, url, "http",
                f"request error: {e}",
                "retry",
                f"attempt {attempt + 1}",
            )
            time.sleep(3)

    return 0, ""


# ---------- C6: ROTTEN TOMATOES SCRAPER ----------

# SỬA CHỖ 2: Thêm hàm tìm kiếm phim trên RT thay vì tự đoán tên đường link
def _norm_text(value):
    """
    Normalize title text for reliable movie-title matching.
    Giữ apostrophe trong từ, ví dụ Marvel's -> marvels.
    """
    if value is None:
        return ""

    value = str(value)

    # Xóa HTML
    value = re.sub(r"<[^>]+>", " ", value)

    # Decode một số HTML entities cơ bản
    value = re.sub(
        r"&(?:amp|apos|quot|#39|#x27|#x2F|#47);",
        "",
        value,
        flags=re.IGNORECASE,
    )

    # Đổi apostrophe thành nothing:
    # Marvel's the Avengers -> Marvels the Avengers
    value = value.replace("’", "").replace("'", "")

    # Các dấu khác -> space
    value = re.sub(r"[^\w\s]+", " ", value, flags=re.UNICODE)

    value = re.sub(r"\s+", " ", value).strip().lower()

    return value

def _extract_attr(tag_or_row, *names):
    for name in names:
        m = re.search(
            rf'\b{re.escape(name)}=["\']([^"\']*)["\']',
            tag_or_row,
            flags=re.IGNORECASE,
        )
        if m:
            return m.group(1).strip()
    return ""


def _extract_result_title(row):
    """Extract visible title text from one RT search result row."""
    # Common title attributes used by RT/custom components.
    for names in (
        ("title", "name", "displaytitle", "display-title"),
    ):
        value = _extract_attr(row, *names)
        if value:
            return value

    # Prefer explicit heading/title nodes when present.
    for pattern in (
        r'<(?:a|span|div|h[1-6])\b[^>]*(?:title|name)=["\']([^"\']+)["\'][^>]*>.*?</(?:a|span|div|h[1-6])>',
        r'<a\b[^>]*href=["\'][^"\']*/m/[^"\']+["\'][^>]*>(.*?)</a>',
    ):
        m = re.search(pattern, row, flags=re.IGNORECASE | re.DOTALL)
        if m:
            candidate = re.sub(r"<[^>]+>", " ", m.group(1))
            candidate = re.sub(r"\s+", " ", candidate).strip()
            if candidate:
                return candidate

    # Last resort: strip tags and use the remaining text.
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", row, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def search_rt_movie(title, year):
    """
    Find the correct Rotten Tomatoes movie page.

    Matching priority:
        1. EXACT RELEASE YEAR
        2. EXACT TITLE
        3. TITLE CONTAINS
        4. SLUG SIMILARITY

    Nếu có year và RT trả về ít nhất một candidate đúng year,
    thì loại bỏ toàn bộ candidate khác year.

    Điều này ngăn lỗi:
        The Avengers (2012) -> The Avengers (1998)
    """

    params = {"search": title}

    s, html = get(
        RT_SEARCH_URL,
        "RT_SEARCH",
        params=params,
        delay=1.0,
    )

    if s != 200 or not html:
        LOG.add(
            "RT_SEARCH",
            title,
            "search",
            f"HTTP {s} khi tìm '{title}'",
            "retry/manual check",
            "SEARCH_FAILED",
            "OPEN",
        )
        return None

    q_title = _norm_text(title)
    q_year = str(year).strip() if year else ""

    candidates = []

    # ============================================================
    # PARSE FULL SEARCH RESULT ROW
    # ============================================================

    rows = re.findall(
        r"<search-page-media-row\b[^>]*>[\s\S]*?</search-page-media-row\s*>",
        html,
        flags=re.IGNORECASE,
    )

    for row in rows:

        # --------------------------------------------------------
        # URL
        # --------------------------------------------------------

        href_m = re.search(
            r'href=["\']([^"\']*?/m/[^"\']+)["\']',
            row,
            flags=re.IGNORECASE,
        )

        if not href_m:
            continue

        href = href_m.group(1)

        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = RT_BASE + href

        href = href.split("?", 1)[0]

        if "/m/" not in href.lower():
            continue

        # --------------------------------------------------------
        # TITLE
        # --------------------------------------------------------

        result_title = _extract_result_title(row)

        normalized_result = _norm_text(result_title)

        # --------------------------------------------------------
        # YEAR
        # --------------------------------------------------------

        result_year = _extract_attr(
            row,
            "release-year",
            "releaseyear",
            "year",
        )

        result_year = str(result_year).strip()

        # Nếu attribute không có thì thử tìm năm trong row
        if not result_year:
            years = re.findall(
                r"\b((?:19|20)\d{2})\b",
                row,
            )

            if years:
                # Ưu tiên year mà đúng query
                if q_year and q_year in years:
                    result_year = q_year
                else:
                    result_year = years[0]

        # --------------------------------------------------------
        # SCORES TRÊN SEARCH RESULT
        # --------------------------------------------------------

        critic = _extract_attr(
            row,
            "tomatometerscore",
            "tomatometer-score",
            "tomatometer",
        )

        audience = _extract_attr(
            row,
            "audiencescore",
            "audience-score",
            "popcornmeter",
        )

        # --------------------------------------------------------
        # TITLE MATCH
        # --------------------------------------------------------

        exact_title = (
            normalized_result == q_title
        )

        title_contains = bool(
            q_title
            and normalized_result
            and (
                q_title in normalized_result
                or normalized_result in q_title
            )
        )

        # Marvel's the Avengers -> the avengers
        result_without_marvels = re.sub(
            r"^marvels\s+",
            "",
            normalized_result,
        )

        q_without_marvels = re.sub(
            r"^marvels\s+",
            "",
            q_title,
        )

        alias_exact = (
            result_without_marvels == q_without_marvels
        )

        # --------------------------------------------------------
        # YEAR MATCH
        # --------------------------------------------------------

        year_match = bool(
            q_year
            and result_year
            and result_year == q_year
        )

        # --------------------------------------------------------
        # SCORING
        # --------------------------------------------------------

        score = 0

        # YEAR PHẢI CỰC KỲ QUAN TRỌNG
        if year_match:
            score += 10000

        if exact_title:
            score += 2000

        if alias_exact:
            score += 1800

        elif title_contains:
            score += 1000

        candidates.append({
            "url": href,
            "title": result_title,
            "year": result_year,
            "critic": critic,
            "audience": audience,
            "_rank": score,
        })

    # ============================================================
    # FALLBACK: PARSE /m/ LINKS
    # ============================================================

    if not candidates:

        hrefs = re.findall(
            r'href=["\']([^"\']*?/m/[^"\']+)["\']',
            html,
            flags=re.IGNORECASE,
        )

        seen = set()

        for href in hrefs:

            href = href.split("?", 1)[0]

            if href.startswith("/"):
                href = RT_BASE + href

            if href in seen:
                continue

            seen.add(href)

            slug = href.rsplit("/m/", 1)[-1]

            slug_text = _norm_text(
                slug.replace("_", " ")
            )

            score = 0

            if q_title and q_title in slug_text:
                score += 1000

            candidates.append({
                "url": href,
                "title": "",
                "year": "",
                "critic": "",
                "audience": "",
                "_rank": score,
            })

    if not candidates:

        LOG.add(
            "RT_SEARCH",
            title,
            "search",
            "Không tìm thấy movie result /m/",
            "manual check",
            "NO_MOVIE_RESULT",
            "OPEN",
        )

        return None

    # ============================================================
    # CRITICAL FIX:
    # NẾU CÓ CANDIDATE ĐÚNG YEAR -> LOẠI BỎ HẾT CANDIDATE KHÁC
    # ============================================================

    if q_year:

        year_candidates = [
            c for c in candidates
            if c.get("year") == q_year
        ]

        if year_candidates:
            candidates = year_candidates

    # ============================================================
    # SORT
    # ============================================================

    candidates.sort(
        key=lambda c: c["_rank"],
        reverse=True,
    )

    selected = candidates[0]

    # ============================================================
    # DEBUG
    # ============================================================

    print(
        f"\n    [RT SEARCH] "
        f"'{title}' ({q_year})"
    )

    print(
        f"    -> Selected: "
        f"{selected.get('title') or 'N/A'} "
        f"({selected.get('year') or 'N/A'})"
    )

    print(
        f"    -> URL: {selected['url']}"
    )

    print(
        f"    -> Rank: {selected['_rank']}"
    )

    # ============================================================
    # SAFETY CHECK
    # ============================================================

    if q_year and selected.get("year"):
        if selected["year"] != q_year:

            LOG.add(
                "RT_SEARCH",
                title,
                "year",
                (
                    f"Expected year {q_year}, "
                    f"got {selected.get('year')} "
                    f"URL={selected['url']}"
                ),
                "reject",
                "YEAR_MISMATCH",
                "OPEN",
            )

            return None

    return selected


# def extract_rt_scores(html):
#     """
#     Extract Tomatometer + Popcornmeter from Rotten Tomatoes.

#     Priority:
#       1. media-scorecard-json -> scorePercent
#       2. media-scorecard-json -> score
#       3. score-board/custom attributes
#       4. JSON-LD aggregateRating (critic only)
#       5. visible HTML fallback

#     Returns:
#         (critic_score, audience_score)
#     """

#     critic = ""
#     audience = ""
#     # ============================================================
#     # UPCOMING MOVIE SAFETY CHECK
#     # ============================================================
#     #
#     # Nếu RT xác nhận phim chưa có review/rating,
#     # tuyệt đối không lấy các con số khác trong HTML làm score.
#     #

#     upcoming_no_scores = (
#         re.search(
#             r"Tomatometer\s+0\s+Reviews",
#             html,
#             flags=re.IGNORECASE,
#         )
#         and
#         (
#             re.search(
#                 r"Popcornmeter\s+0\s+Verified\s+Ratings",
#                 html,
#                 flags=re.IGNORECASE,
#             )
#             or
#             re.search(
#                 r"Popcornmeter\s+0",
#                 html,
#                 flags=re.IGNORECASE,
#             )
#         )
#     )

#     if upcoming_no_scores:
#         return "", ""
#     def clean_percent(value):
#         """
#         Chỉ chấp nhận giá trị điểm 0-100.
#         Ưu tiên số đứng trước dấu %.
#         Không lấy bừa một con số trong chuỗi dài.
#         """
#         if value is None:
#             return ""

#         s = str(value).strip()

#         # Ví dụ: "91%"
#         m = re.fullmatch(r"\s*(\d{1,3})\s*%\s*", s)
#         if m:
#             n = int(m.group(1))
#             return str(n) if 0 <= n <= 100 else ""

#         # Ví dụ: "91"
#         m = re.fullmatch(r"\s*(\d{1,3})\s*", s)
#         if m:
#             n = int(m.group(1))
#             return str(n) if 0 <= n <= 100 else ""

#         return ""

#     # ============================================================
#     # 1. MEDIA-SCORECARD-JSON
#     # ============================================================

#     scorecard_matches = re.findall(
#         r'<script\b[^>]*id=["\']media-scorecard-json["\'][^>]*>'
#         r'(.*?)'
#         r'</script\s*>',
#         html,
#         flags=re.IGNORECASE | re.DOTALL,
#     )

#     for raw in scorecard_matches:
#         try:
#             data = json.loads(raw.strip())
#         except (json.JSONDecodeError, TypeError, ValueError):
#             continue

#         if not isinstance(data, dict):
#             continue

#         # -------------------------
#         # Critics / Tomatometer
#         # -------------------------
#         critics = data.get("criticsScore")

#         if isinstance(critics, dict):

#             # Ưu tiên scorePercent
#             if not critic:
#                 critic = clean_percent(
#                     critics.get("scorePercent")
#                 )

#             # fallback score
#             if not critic:
#                 critic = clean_percent(
#                     critics.get("score")
#                 )

#         # -------------------------
#         # Audience / Popcornmeter
#         # -------------------------
#         aud = data.get("audienceScore")

#         if isinstance(aud, dict):

#             # Ưu tiên scorePercent
#             if not audience:
#                 audience = clean_percent(
#                     aud.get("scorePercent")
#                 )

#             # fallback score
#             if not audience:
#                 audience = clean_percent(
#                     aud.get("score")
#                 )

#         if critic or audience:
#             return critic, audience

#     # ============================================================
#     # 2. SCORE-BOARD
#     # ============================================================

#     scoreboards = re.findall(
#         r'<score-board\b[^>]*>',
#         html,
#         flags=re.IGNORECASE | re.DOTALL,
#     )

#     for board in scoreboards:

#         if not critic:
#             m = re.search(
#                 r'\btomatometerscore=["\']([^"\']+)["\']',
#                 board,
#                 flags=re.IGNORECASE,
#             )
#             if m:
#                 critic = clean_percent(m.group(1))

#         if not audience:
#             m = re.search(
#                 r'\baudiencescore=["\']([^"\']+)["\']',
#                 board,
#                 flags=re.IGNORECASE,
#             )
#             if m:
#                 audience = clean_percent(m.group(1))

#         if critic and audience:
#             return critic, audience

#     # ============================================================
#     # 3. CUSTOM ATTRIBUTES
#     # ============================================================

#     if not critic:
#         for pattern in [
#             r'\btomatometerscore=["\']([^"\']+)["\']',
#             r'\btomatometer-score=["\']([^"\']+)["\']',
#             r'\bscore-percent=["\']([^"\']+)["\']',
#         ]:
#             m = re.search(
#                 pattern,
#                 html,
#                 flags=re.IGNORECASE,
#             )
#             if m:
#                 candidate = clean_percent(m.group(1))
#                 if candidate:
#                     critic = candidate
#                     break

#     if not audience:
#         for pattern in [
#             r'\baudiencescore=["\']([^"\']+)["\']',
#             r'\baudience-score=["\']([^"\']+)["\']',
#             r'\bpopcornmeter-score=["\']([^"\']+)["\']',
#         ]:
#             m = re.search(
#                 pattern,
#                 html,
#                 flags=re.IGNORECASE,
#             )
#             if m:
#                 candidate = clean_percent(m.group(1))
#                 if candidate:
#                     audience = candidate
#                     break

#     # ============================================================
#     # 4. JSON-LD
#     # ============================================================

#     ld_matches = re.findall(
#         r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>'
#         r'(.*?)'
#         r'</script\s*>',
#         html,
#         flags=re.IGNORECASE | re.DOTALL,
#     )

#     for ld in ld_matches:
#         try:
#             data = json.loads(ld.strip())
#         except (json.JSONDecodeError, TypeError, ValueError):
#             continue

#         objects = data if isinstance(data, list) else [data]

#         for obj in objects:

#             if not isinstance(obj, dict):
#                 continue

#             aggregate = obj.get("aggregateRating")

#             if not isinstance(aggregate, dict):
#                 continue

#             # JSON-LD chỉ dùng làm fallback cho critic.
#             if not critic:
#                 rating = aggregate.get("ratingValue")

#                 # Ví dụ ratingValue = "91"
#                 candidate = clean_percent(rating)

#                 if candidate:
#                     critic = candidate

#             if critic and audience:
#                 return critic, audience

#     # ============================================================
#     # 5. VISIBLE HTML FALLBACK
#     # ============================================================

#     if not critic:
#         m = re.search(
#             r'(?:Tomatometer|Tomato-meter|Critics Score)'
#             r'.{0,200}?'
#             r'(\d{1,3})\s*%',
#             html,
#             flags=re.IGNORECASE | re.DOTALL,
#         )

#         if m:
#             candidate = int(m.group(1))
#             if 0 <= candidate <= 100:
#                 critic = str(candidate)

#     if not audience:
#         m = re.search(
#             r'(?:Popcornmeter|Audience Score|AudienceScore)'
#             r'.{0,200}?'
#             r'(\d{1,3})\s*%',
#             html,
#             flags=re.IGNORECASE | re.DOTALL,
#         )

#         if m:
#             candidate = int(m.group(1))
#             if 0 <= candidate <= 100:
#                 audience = str(candidate)

#     return critic, audience
def extract_rt_scores(html):
    """
    STRICT Rotten Tomatoes score extraction.

    Chỉ chấp nhận score từ nguồn có cấu trúc rõ ràng:
        1. media-scorecard-json
        2. score-board

    KHÔNG:
        - lấy số bất kỳ trong HTML
        - lấy JSON-LD
        - lấy số gần chữ "Audience"
        - lấy fallback visible text

    Returns:
        (critic_score, audience_score)
    """

    critic = ""
    audience = ""

    # ============================================================
    # 0. PHIM CHƯA CÓ REVIEW/RATING
    # ============================================================

    no_critic_reviews = bool(
        re.search(
            r"Tomatometer\s+0\s+Reviews",
            html,
            flags=re.IGNORECASE,
        )
    )

    no_audience_ratings = bool(
        re.search(
            r"Popcornmeter\s+0\s+Verified\s+Ratings",
            html,
            flags=re.IGNORECASE,
        )
    )

    # Nếu RT xác nhận cả hai đều bằng 0,
    # tuyệt đối không lấy bất kỳ con số khác nào.
    if no_critic_reviews and no_audience_ratings:
        return "", ""

    # ============================================================
    # HELPER
    # ============================================================

    def strict_score(value):
        """
        Chỉ chấp nhận:
            "91"
            "91%"
        
        Không chấp nhận:
            "91/100"
            "91 reviews"
            "5 fresh, 15 rotten"
            "56 something"
        """

        if value is None:
            return ""

        value = str(value).strip()

        m = re.fullmatch(
            r"(\d{1,3})\s*%?",
            value,
        )

        if not m:
            return ""

        n = int(m.group(1))

        if 0 <= n <= 100:
            return str(n)

        return ""

    # ============================================================
    # 1. MEDIA-SCORECARD-JSON
    # ============================================================

    scorecard_matches = re.findall(
        r'<script\b[^>]*'
        r'id=["\']media-scorecard-json["\']'
        r'[^>]*>'
        r'(.*?)'
        r'</script\s*>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    for raw in scorecard_matches:

        try:
            data = json.loads(raw.strip())
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

        if not isinstance(data, dict):
            continue

        # --------------------------------------------------------
        # TOMATOMETER
        # --------------------------------------------------------

        critics = data.get("criticsScore")

        if isinstance(critics, dict):

            # Ưu tiên scorePercent
            candidate = strict_score(
                critics.get("scorePercent")
            )

            if candidate:
                critic = candidate

            # fallback score
            if not critic:
                candidate = strict_score(
                    critics.get("score")
                )

                if candidate:
                    critic = candidate

        # --------------------------------------------------------
        # POPCORNMETER
        # --------------------------------------------------------

        audience_data = data.get("audienceScore")

        if isinstance(audience_data, dict):

            # Ưu tiên scorePercent
            candidate = strict_score(
                audience_data.get("scorePercent")
            )

            if candidate:
                audience = candidate

            # fallback score
            if not audience:
                candidate = strict_score(
                    audience_data.get("score")
                )

                if candidate:
                    audience = candidate

        if critic or audience:
            return critic, audience

    # ============================================================
    # 2. SCORE-BOARD
    # ============================================================

    scoreboards = re.findall(
        r"<score-board\b[^>]*>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    for board in scoreboards:

        # --------------------------------------------------------
        # TOMATOMETER
        # --------------------------------------------------------

        if not critic:

            m = re.search(
                r'\btomatometerscore=["\']([^"\']+)["\']',
                board,
                flags=re.IGNORECASE,
            )

            if m:
                candidate = strict_score(
                    m.group(1)
                )

                if candidate:
                    critic = candidate

        # --------------------------------------------------------
        # POPCORNMETER
        # --------------------------------------------------------

        if not audience:

            m = re.search(
                r'\baudiencescore=["\']([^"\']+)["\']',
                board,
                flags=re.IGNORECASE,
            )

            if m:
                candidate = strict_score(
                    m.group(1)
                )

                if candidate:
                    audience = candidate

        if critic or audience:
            return critic, audience

    # ============================================================
    # 3. KHÔNG CÒN FALLBACK
    # ============================================================

    # Cực kỳ quan trọng:
    #
    # Không được cố "đoán" điểm từ HTML.
    #
    # Nếu RT thay đổi markup -> N/A.
    #
    return critic, audience

def c6_rt():
    movies = read_csv("movies_raw.csv")

    if not movies:
        sys.exit("Không tìm thấy movies_raw.csv. Cần chạy bước C2 trước.")

    rt_rows = []

    print(
        f"Bắt đầu cào dữ liệu Rotten Tomatoes cho "
        f"{len(movies)} phim..."
    )

    for idx, m in enumerate(movies, 1):
        fk = m["film_key"]
        title = m["title"]
        year = (
            m["release_date_ref"][:4]
            if m.get("release_date_ref")
            else ""
        )

        print(
            f"[{idx}/{len(movies)}] Đang lấy: "
            f"{title} ({year})...",
            end=" ",
        )

        # ========================================================
        # STAGE 1: SEARCH
        # ========================================================
        search_result = search_rt_movie(title, year)

        rt_path = None
        search_critic = ""
        search_audience = ""

        if search_result:
            rt_path = search_result.get("url")
            search_critic = search_result.get("critic", "")
            search_audience = search_result.get("audience", "")

        matched_html = None
        final_url = ""
        status_code = 0

        # ========================================================
        # STAGE 2: DETAIL PAGE
        # ========================================================
        if rt_path:
            url = (
                f"{RT_BASE}{rt_path}"
                if rt_path.startswith("/")
                else rt_path
            )

            # Cache theo URL RT thực tế, không chỉ theo film_key.
            # Nhờ vậy nếu lần chạy trước match nhầm trang, cache cũ sẽ
            # không được tái sử dụng cho URL mới.
            url_cache_key = hashlib.sha1(
                url.encode("utf-8")
            ).hexdigest()[:12]
            c_file = CACHE / "rt" / f"{fk}_{url_cache_key}_details.html"

            s, html = get(
                url,
                "RT",
                cache_file=c_file,
                delay=1.0,
            )

            status_code = s

            if s == 200 and html:
                matched_html = html
                final_url = url

        # ========================================================
        # STAGE 3: FAILURE
        # ========================================================
        if not matched_html:
            LOG.add(
                "RT",
                fk,
                "rt_url",
                f"HTTP {status_code} - Không tải được trang phim",
                "skipped",
                "UNMATCHED",
                "OPEN",
            )

            rt_rows.append({
                "film_key": fk,
                "critic_score": search_critic,
                "audience_score": search_audience,
                "rt_url": final_url,
                "rt_status": "SEARCH_ONLY" if (
                    search_critic or search_audience
                ) else "UNMATCHED",
                "source": "RT",
                "retrieval_date": TODAY,
            })

            if search_critic or search_audience:
                print(
                    f"-> SEARCH ONLY "
                    f"(Critic: {search_critic or 'N/A'}, "
                    f"Audience: {search_audience or 'N/A'})"
                )
            else:
                print(f"-> THẤT BẠI (HTTP {status_code})")

            continue

        # ========================================================
        # STAGE 4: DETAIL PAGE EXTRACTION
        # ========================================================
        detail_critic, detail_audience = extract_rt_scores(
            matched_html
        )

        # Search result is a valid fallback.
        critic = detail_critic 
        audience = detail_audience 

        # ========================================================
        # STAGE 5: STATUS
        # ========================================================
        if critic or audience:
            rt_status = "MATCHED"
        else:
            rt_status = "MATCHED_NO_SCORES"

            LOG.add(
                "RT",
                fk,
                "scores",
                "Trang phim tồn tại nhưng không có "
                "Critic/Audience score hoặc markup đã thay đổi",
                "manual check",
                "NO_SCORES",
                "OPEN",
            )

        rt_rows.append({
            "film_key": fk,
            "critic_score": critic,
            "audience_score": audience,
            "rt_url": final_url,
            "rt_status": rt_status,
            "source": "RT",
            "retrieval_date": TODAY,
        })

        print(
            f"-> XONG "
            f"(Critic: {critic or 'N/A'}, "
            f"Audience: {audience or 'N/A'}, "
            f"Status: {rt_status})"
        )

    write_csv(
        "rt_scores.csv",
        rt_rows,
        [
            "film_key",
            "critic_score",
            "audience_score",
            "rt_url",
            "rt_status",
            "source",
            "retrieval_date",
        ],
    )

    critic_count = sum(
        1 for r in rt_rows if r["critic_score"]
    )
    audience_count = sum(
        1 for r in rt_rows if r["audience_score"]
    )

    print(
        f"Đã lưu {len(rt_rows)} bản ghi vào rt_scores.csv."
    )
    print(
        f"- Critic/Tomatometer: "
        f"{critic_count}/{len(rt_rows)}"
    )
    print(
        f"- Audience/Popcornmeter: "
        f"{audience_count}/{len(rt_rows)}"
    )


# ---------- C7: MERGE BOM & RT (Giữ nguyên) ----------
def c7_merge():
    movies = {r["film_key"]: r for r in read_csv("movies_raw.csv")}
    bo = {r["film_key"]: r for r in read_csv("box_office_raw.csv")}
    rt = {r["film_key"]: r for r in read_csv("rt_scores.csv")}
    
    if not movies:
        print("Lỗi: Thiếu movies_raw.csv để gộp.")
        return

    merged = []
    fields = [
        "film_key", "title", "market_scope", "territory_code",
        "critic_score", "audience_score", 
        "opening_gross", "opening_start_date", "opening_end_date",
        "opening_days_count", "opening_theater_count", "local_currency_gross"
    ]
    
    for fk, m in movies.items():
        b_data = bo.get(fk, {})
        r_data = rt.get(fk, {})
        
        merged.append(dict(
            film_key=fk,
            title=m.get("title", ""),
            market_scope=b_data.get("market_scope", "domestic"),
            territory_code="", 
            critic_score=r_data.get("critic_score", ""),
            audience_score=r_data.get("audience_score", ""),
            opening_gross=b_data.get("opening_gross", ""),
            opening_start_date=b_data.get("local_release_date", ""),
            opening_end_date="", 
            opening_days_count=b_data.get("opening_days_count", ""),
            opening_theater_count=b_data.get("opening_theater_count", ""),
            local_currency_gross="" 
        ))
        
    write_csv("merged_bom_rt.csv", merged, fields)
    
    rt_count = sum(1 for x in merged if x["critic_score"] != "" or x["audience_score"] != "")
    bo_count = sum(1 for x in merged if x["opening_gross"] != "")
    
    print(f"\n[BÁO CÁO GỘP] File: merged_bom_rt.csv")
    print(f"Tổng số phim: {len(merged)}")
    print(f"- Đã thu thập điểm RT (critic/audience): {rt_count}/{len(merged)}")
    print(f"- Đã thu thập doanh thu mở màn (opening_gross): {bo_count}/{len(merged)}")


if __name__ == "__main__":
    os.environ["ADY_CONTACT"] = "nhatlam23122007@gmail.com"
    
    STEPS_MAP = {"c6": c6_rt, "c7": c7_merge}
    steps_to_run = [sys.argv[1]] if len(sys.argv) > 1 else ["c6", "c7"]

    for step in steps_to_run:
        fn = STEPS_MAP.get(step)
        if not fn:
            print(f"Không tìm thấy bước: {step}")
            continue

        print(f"\n==========================================")
        print(f"  ĐANG THỰC HIỆN BƯỚC: {step.upper()}")
        print(f"==========================================")
        
        try:
            fn()
            LOG.save()
            print(f"--> HOÀN THÀNH BƯỚC {step.upper()} THÀNH CÔNG!")
        except Exception as e:
            print(f"--> [LỖI] Bước {step} gặp lỗi: {e}")
            break