import csv, json, os, re, sys, time, datetime as dt
from pathlib import Path
from urllib import robotparser
import requests
from bs4 import BeautifulSoup
import os

OUT = Path(os.environ.get("ADY_OUT", "ady_pilot_out"))
CACHE = OUT / "cache"
TODAY = dt.date.today().isoformat()
KEY = os.environ.get("TMDB_API_KEY")
UA = f"ADY_PRJ-university-research/0.1 ({os.environ.get('ADY_CONTACT', 'set ADY_CONTACT')})"
BOM = "https://www.boxofficemojo.com"
TMDB = "https://api.themoviedb.org/3"
TOP_CAST = 20  # superset only; fixed k is an OPEN decision, NOT made here
for d in (OUT, CACHE / "tmdb", CACHE / "bom"):
    d.mkdir(parents=True, exist_ok=True)


# ---------- helpers ----------
def write_csv(name, rows, fields):
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
        write_csv("issue_log.csv", self.rows, self.FIELDS)


LOG = IssueLog()
_last = {}


def get(url, source, params=None, cache_file=None, delay=1.0, binary=False):
    """GET with cache + polite delay + retry. Returns (status, text). Raw response always cached first."""
    if source == "BOM":
        raise RuntimeError("BOM blocked: robots.txt disallows automated access")

    if cache_file and cache_file.exists():
        return 200, cache_file.read_text(encoding="utf-8")
    wait = delay - (time.time() - _last.get(source, 0))
    if wait > 0:
        time.sleep(wait)
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=30)
            _last[source] = time.time()
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            if cache_file and r.status_code == 200:
                cache_file.write_text(r.text, encoding="utf-8")
            return r.status_code, r.text
        except requests.RequestException as e:
            LOG.add(source, url, "http", f"request error: {e}", "retry", f"attempt {attempt+1}")
            time.sleep(3)
    return 0, ""


def tmdb(path, **params):
    params["api_key"] = KEY
    safe = re.sub(r"\W+", "_", path + json.dumps({k: v for k, v in params.items() if k != "api_key"}, sort_keys=True))
    s, t = get(f"{TMDB}{path}", "TMDB", params, CACHE / "tmdb" / f"{safe}.json", delay=0.3)
    return (json.loads(t) if s == 200 else None), s


def film_key(tmdb_id):
    # PROVISIONAL: deterministic from tmdb_id. Replace with the rule in the project's Film_key tab.
    return f"FK{int(tmdb_id):08d}"


def need_key():
    if not KEY:
        sys.exit("TMDB_API_KEY not set")


# ---------- C0 source audit ----------
def c0():
    audit = {"retrieval_date": TODAY, "sources": {}}
    for name, base in [("TMDB", "https://www.themoviedb.org"), ("BOM", BOM), ("RT", "https://www.rottentomatoes.com"),
                       ("TheNumbers", "https://www.the-numbers.com"), ("OpusData", "https://www.opusdata.com")]:
        info = {}
        try:
            r = requests.get(base + "/robots.txt", headers={"User-Agent": UA}, timeout=10)
            rp = robotparser.RobotFileParser()
            rp.parse(r.text.splitlines())
            info["robots_fetch_ok"] = True
            info["robots_allows_root"] = rp.can_fetch(UA, base + "/")
            if name == "BOM":
                info["robots_allows_title_page"] = rp.can_fetch(UA, BOM + "/title/tt0120347/")
        except Exception as e:
            info["robots_fetch_ok"] = False
            info["error"] = str(e)
        audit["sources"][name] = info

    if KEY:
        j, s = tmdb("/configuration")
        audit["sources"]["TMDB"]["api_status"] = s
    else:
        audit["sources"]["TMDB"]["api_status"] = "no key"
        LOG.add("TMDB", "-", "api key", "TMDB_API_KEY missing", status="OPEN")

    (OUT / "source_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    LOG.save()
    print(json.dumps(audit, indent=2))


# ---------- C1 candidate discovery ----------
def c1():
    need_key()
    franchises = list(csv.DictReader(open(Path(__file__).with_name("pilot_franchises.csv"), encoding="utf-8")))
    choice = {r["franchise_no"]: r for r in read_csv("collection_choice.csv")}
    cands = []
    for fr in franchises:
        j, s = tmdb("/search/collection", query=fr["tmdb_search_query"])
        if not j:
            LOG.add("TMDB", fr["franchise"], "search/collection", f"HTTP {s}")
            continue
        for r in j.get("results", []):
            cands.append(dict(franchise_no=fr["franchise_no"], franchise=fr["franchise"],
                              tmdb_collection_id=r["id"], collection_name=r["name"]))
    write_csv("collection_candidates.csv", cands, ["franchise_no", "franchise", "tmdb_collection_id", "collection_name"])
    if not choice:
        # template for the human: fill tmdb_collection_ids (pipe-separated, e.g. 1234|5678). Nothing is auto-picked.
        write_csv("collection_choice.csv",
                  [dict(franchise_no=f["franchise_no"], franchise=f["franchise"], tmdb_collection_ids="") for f in franchises],
                  ["franchise_no", "franchise", "tmdb_collection_ids"])
        LOG.save()
        sys.exit("Review collection_candidates.csv, fill collection_choice.csv, then re-run c1.")
    seed, reg = [], {r["tmdb_id"]: r for r in read_csv("film_registry.csv")}
    for no, c in choice.items():
        ids = [x for x in c["tmdb_collection_ids"].split("|") if x.strip()]
        if not ids:
            LOG.add("TMDB", c["franchise"], "collection", "no collection chosen", "skipped", "franchise excluded at C1", "OPEN")
            continue
        for cid in ids:
            j, s = tmdb(f"/collection/{cid}")
            if not j:
                LOG.add("TMDB", f"{c['franchise']}/{cid}", "collection", f"HTTP {s}")
                continue
            if len(j.get("parts", [])) < 2:
                LOG.add("TMDB", f"{c['franchise']}/{cid}", "collection", "<2 films", "kept, flagged", "", "OPEN")
            for p in j.get("parts", []):
                seed.append(dict(franchise_no=no, franchise=c["franchise"], tmdb_collection_id=cid, tmdb_id=p["id"],
                                 title=p.get("title"), release_date=p.get("release_date") or "",
                                 source="TMDB", retrieval_date=TODAY))
    seen, clean = set(), []
    for r in seed:
        if r["tmdb_id"] in seen:
            LOG.add("TMDB", str(r["tmdb_id"]), "tmdb_id", "duplicate across collections", "kept first", "", "OPEN")
            continue
        seen.add(r["tmdb_id"])
        clean.append(r)
        reg[str(r["tmdb_id"])] = dict(tmdb_id=r["tmdb_id"], film_key=film_key(r["tmdb_id"]), key_rule="PROVISIONAL")
    write_csv("seed_films.csv", clean, list(clean[0].keys()) if clean else ["tmdb_id"])
    write_csv("film_registry.csv", list(reg.values()), ["tmdb_id", "film_key", "key_rule"])
    LOG.save()
    print(f"seed films: {len(clean)}")


# ---------- C2 movies_raw / credits_raw ----------
def c2():
    need_key()
    movies, credits = [], []
    for r in read_csv("seed_films.csv"):
        j, s = tmdb(f"/movie/{r['tmdb_id']}", append_to_response="credits,external_ids")
        fk = film_key(r["tmdb_id"])
        if not j:
            LOG.add("TMDB", fk, "movie", f"HTTP {s}", "skipped")
            continue
        crew = [c for c in j.get("credits", {}).get("crew", []) if c.get("job") == "Director"]
        cast = sorted(j.get("credits", {}).get("cast", []), key=lambda c: c.get("order", 9999))
        bud = j.get("budget")
        rd = j.get("release_date") or ""
        if not rd:
            LOG.add("TMDB", fk, "release_date_ref", "missing")
        if not (j.get("external_ids") or {}).get("imdb_id"):
            LOG.add("TMDB", fk, "imdb_id", "missing")
        movies.append(dict(
            film_key=fk, tmdb_id=j["id"], imdb_id=(j.get("external_ids") or {}).get("imdb_id") or "",
            title=j.get("title"), release_date_ref=rd,
            tmdb_collection_id=(j.get("belongs_to_collection") or {}).get("id", ""),
            director_ids="|".join(str(c["id"]) for c in crew),
            lead_cast_ids_superset=("|".join(str(c["id"]) for c in cast[:TOP_CAST])),
            production_company_ids="|".join(str(c["id"]) for c in j.get("production_companies", [])),
            production_budget=bud if bud else "",          # 0 on TMDB treated as MISSING, never as zero
            budget_missing_flag=not bool(bud),
            release_month=rd[5:7] if len(rd) >= 7 else "",
            critic_score="", audience_score="",             # RT not collected by this script
            source="TMDB", retrieval_date=TODAY))
        for c in crew:
            credits.append(dict(film_key=fk, person_id=c["id"], role="director", billing_order="", source="TMDB", retrieval_date=TODAY))
        for c in cast:
            credits.append(dict(film_key=fk, person_id=c["id"], role="cast", billing_order=c.get("order", ""), source="TMDB", retrieval_date=TODAY))
        if not cast:
            LOG.add("TMDB", fk, "cast", "empty cast list")
        if not crew:
            LOG.add("TMDB", fk, "director_ids", "no director in crew")
    write_csv("movies_raw.csv", movies, list(movies[0].keys()) if movies else ["film_key"])
    write_csv("credits_raw.csv", credits, ["film_key", "person_id", "role", "billing_order", "source", "retrieval_date"])
    LOG.save()
    print(f"movies_raw: {len(movies)}, credits_raw rows: {len(credits)}")


# ---------- C3 crosswalk TMDB -> BOM (verified) ----------
def norm(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def parse_bom_title(html):
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    text = soup.get_text(" ", strip=True)
    m = re.search(r"^(.*?)\s*\((\d{4})\)", h1.get_text(" ", strip=True)) if h1 else None
    return (m.group(1), int(m.group(2))) if m else (None, None), text


def c3():
    rows = []
    for m in read_csv("movies_raw.csv"):
        base = dict(film_key=m["film_key"], tmdb_id=m["tmdb_id"], imdb_id=m["imdb_id"], bom_id="", bom_status="",
                    source="BOM", retrieval_date=TODAY, note="")
        if not m["imdb_id"]:
            base.update(bom_status="UNMATCHED", note="no imdb_id from TMDB")
            LOG.add("BOM", m["film_key"], "bom_id", "no imdb_id to try", "not guessed", "UNMATCHED", "OPEN")
            rows.append(base)
            continue
        s, html = get(f"{BOM}/title/{m['imdb_id']}/", "BOM", cache_file=CACHE / "bom" / f"title_{m['imdb_id']}.html")
        if s != 200:
            base.update(bom_status="UNMATCHED", note=f"HTTP {s}")
            LOG.add("BOM", m["film_key"], "bom_id", f"title page HTTP {s}", "not guessed", "UNMATCHED", "OPEN")
        else:
            (t, y), _ = parse_bom_title(html)
            ty = int(m["release_date_ref"][:4]) if m["release_date_ref"][:4].isdigit() else None
            if t and norm(t) == norm(m["title"]) and ty and y and abs(y - ty) <= 1:
                base.update(bom_id=m["imdb_id"], bom_status="MATCHED", note=f"BOM title='{t}' ({y})")
            else:
                base.update(bom_id=m["imdb_id"], bom_status="AMBIGUOUS", note=f"BOM title='{t}' ({y}) vs TMDB '{m['title']}' ({ty})")
                LOG.add("BOM", m["film_key"], "bom_id", base["note"], "not resolved", "AMBIGUOUS", "NEEDS MANUAL")
        rows.append(base)
    write_csv("id_crosswalk.csv", rows, list(rows[0].keys()) if rows else ["film_key"])
    write_csv("unmatched.csv", [r for r in rows if r["bom_status"] == "UNMATCHED"], list(rows[0].keys()) if rows else ["film_key"])
    write_csv("ambiguous.csv", [r for r in rows if r["bom_status"] == "AMBIGUOUS"], list(rows[0].keys()) if rows else ["film_key"])
    LOG.save()


# ---------- C4b BOM domestic opening ----------
def parse_domestic(text):
    o = re.search(r"Domestic Opening\s*\$([\d,]+)", text)
    d = re.search(r"Earliest Release Date\s*([A-Z][a-z]+ \d{1,2}, \d{4})", text)
    return (int(o.group(1).replace(",", "")) if o else None, d.group(1) if d else None)


def c4b():
    rows = []
    for x in read_csv("id_crosswalk.csv"):
        if x["bom_status"] != "MATCHED":
            continue  # AMBIGUOUS / UNMATCHED are never collected on a guess
        html = (CACHE / "bom" / f"title_{x['bom_id']}.html").read_text(encoding="utf-8")
        gross, rel = parse_domestic(BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
        rows.append(dict(film_key=x["film_key"], market_scope="domestic", territory_code="",  # BOM 'domestic' = US+Canada; code not asserted
                         local_release_date=rel or "", opening_gross=gross if gross is not None else "",
                         opening_days_count="", opening_theater_count="", local_currency_gross="",
                         missing_flag=gross is None, source="BOM title page", retrieval_date=TODAY))
        if gross is None:
            LOG.add("BOM", x["film_key"], "opening_gross", "Domestic Opening not found on page", "left missing (not 0)")
    # days_count / theaters / territory / global: NOT parsed -> SOURCE TO VERIFY. Inspect cached HTML + release-group pages manually.
    LOG.add("BOM", "all", "opening_days_count/theaters/territory/global",
            "not collected by this script: structure of release-group/territory pages unverified", "cached title pages only", "", "OPEN")
    write_csv("box_office_raw.csv", rows, ["film_key", "market_scope", "territory_code", "local_release_date", "opening_gross",
                                           "opening_days_count", "opening_theater_count", "local_currency_gross",
                                           "missing_flag", "source", "retrieval_date"])
    LOG.save()
    print(f"box_office_raw rows: {len(rows)}")


# ---------- C5 coverage + attrition ----------
def c5():
    mv, cw, bo = read_csv("movies_raw.csv"), read_csv("id_crosswalk.csv"), read_csv("box_office_raw.csv")
    seed = read_csv("seed_films.csv")
    lines = ["# Coverage report", f"retrieval/report date: {TODAY}", ""]
    lines.append(f"seed films: {len(seed)} | movies_raw: {len(mv)}")
    for f in ["imdb_id", "release_date_ref", "tmdb_collection_id", "director_ids", "lead_cast_ids_superset",
              "production_company_ids", "production_budget"]:
        n = sum(1 for r in mv if r[f] != "")
        lines.append(f"- {f}: {n}/{len(mv)} non-missing")
    st = {}
    for r in cw:
        st[r["bom_status"]] = st.get(r["bom_status"], 0) + 1
    lines += ["", f"BOM match: {st}", "", "box_office_raw (domestic):"]
    for f in ["opening_gross", "local_release_date", "opening_days_count", "opening_theater_count"]:
        lines.append(f"- {f}: {sum(1 for r in bo if r[f] != '')}/{len(bo)} non-missing")
    att = [("seed films", len(seed)), ("movies_raw retrieved", len(mv)),
           ("BOM MATCHED", st.get("MATCHED", 0)), ("domestic opening_gross present", sum(1 for r in bo if r["opening_gross"] != ""))]
    write_csv("attrition.csv", [dict(stage=a, count=b) for a, b in att], ["stage", "count"])
    (OUT / "coverage_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    # --- 1. TỰ ĐỘNG CẤP API KEY VÀ EMAIL LIÊN HỆ ---
    os.environ["TMDB_API_KEY"] = "763f28df21fc59bd3da4152438647847"
    os.environ["ADY_CONTACT"] = "nhatlam23122007@gmail.com"
    KEY = os.environ.get("TMDB_API_KEY")  # Cập nhật lại biến KEY toàn cục

    # --- 2. DANH SÁCH 6 BƯỚC CẦN CHẠY TỰ ĐỘNG NỐI TIẾP ---
    ALL_STEPS = ["c0", "c1", "c2", "c3", "c4b", "c5"]
    STEPS_MAP = {"c0": c0, "c1": c1, "c2": c2, "c3": c3, "c4b": c4b, "c5": c5}

    # Nếu truyền tham số từ dòng lệnh (ví dụ: c1) thì chỉ chạy bước đó,
    # Nếu chỉ bấm nút RUN thì sẽ chạy toàn bộ các bước trong ALL_STEPS.
    steps_to_run = [sys.argv[1]] if len(sys.argv) > 1 else ALL_STEPS

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
        except SystemExit as e:
            # Bắt lỗi sys.exit() từ bước c1 (khi cần human review) hoặc missing key
            print(f"--> [DỪNG TIẾN TRÌNH] Bước {step} yêu cầu chú ý: {e}")
            break
        except Exception as e:
            print(f"--> [LỖI BAN ĐẦU] Bước {step} gặp lỗi: {e}")
            break

    print("\n=== ĐÃ HOÀN THÀNH CHUỖI TIẾN TRÌNH ===")