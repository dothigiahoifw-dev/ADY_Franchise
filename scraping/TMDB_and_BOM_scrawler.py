import csv, json, os, re, sys, time, datetime as dt
from pathlib import Path
from urllib import robotparser
import requests
from bs4 import BeautifulSoup

OUT = Path(os.environ.get("ADY_OUT", "ady_pilot_out"))
CACHE = OUT / "cache"
TODAY = dt.date.today().isoformat()
KEY = os.environ.get("TMDB_API_KEY")
UA = f"ADY_PRJ-university-research/0.1 ({os.environ.get('ADY_CONTACT', 'set ADY_CONTACT')})"
TMDB = "https://api.themoviedb.org/3"
TOP_CAST = 20  # superset only; fixed k is an OPEN decision, NOT made here

for d in (OUT, CACHE / "tmdb"):
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
    return f"FK{int(tmdb_id):08d}"


def need_key():
    if not KEY:
        sys.exit("TMDB_API_KEY not set")


# ---------- C0 source audit ----------
def c0():
    audit = {"retrieval_date": TODAY, "sources": {}}
    for name, base in [("TMDB", "https://www.themoviedb.org"), ("RT", "https://www.rottentomatoes.com"),
                       ("TheNumbers", "https://www.the-numbers.com"), ("OpusData", "https://www.opusdata.com")]:
        info = {}
        try:
            r = requests.get(base + "/robots.txt", headers={"User-Agent": UA}, timeout=10)
            rp = robotparser.RobotFileParser()
            rp.parse(r.text.splitlines())
            info["robots_fetch_ok"] = True
            info["robots_allows_root"] = rp.can_fetch(UA, base + "/")
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


# ---------- C1 candidate discovery (KHÔNG ĐỌC FILE ĐẦU VÀO) ----------
def c1():
    
    # print("Đang tự động cào danh sách Franchise từ TMDB API...")
    # cands = []
    # new_choices = []
    # seen_cids = set()
    # franchise_idx = 1
    # page = 1
    # max_pages = 500  # Quét tối đa để tìm collection

    # sort_options = [
    #     "revenue.desc",
    #     "popularity.desc",
    #     "vote_count.desc",
    #     "primary_release_date.desc",
    #     "vote_average.desc"
    # ]
    # for sort_by in sort_options:
    #     if franchise_idx > 7000:
    #         break
    #     print(f" -> Đang quét với tiêu chí sort_by = {sort_by}")
    #     page = 1

    #     while franchise_idx <= 7000 and page <= max_pages:
    #         j, s = tmdb("/discover/movie", sort_by=sort_by, page=page)
    #         time.sleep(0.05)
    #         if not j or "results" not in j or not j["results"]:
    #             print(f" -> [DEBUG] Lỗi gọi API TMDB! Mã HTTP: {s}")
    #             break

    #         for m in j["results"]:
    #             if franchise_idx > 7000:
    #                 break
                
    #             det, ds = tmdb(f"/movie/{m['id']}")
    #             time.sleep(0.05)

    #             if det and isinstance(det, dict) and det.get("belongs_to_collection"):
    #                 col = det["belongs_to_collection"]
    #                 cid = str(col["id"])
                    
    #                 if cid not in seen_cids:
    #                     seen_cids.add(cid)
    #                     cname = col["name"]
    #                     cands.append(dict(franchise_no=str(franchise_idx), franchise=cname, tmdb_collection_id=cid, collection_name=cname))
    #                     new_choices.append(dict(franchise_no=str(franchise_idx), franchise=cname, tmdb_collection_ids=cid))
    #                     franchise_idx += 1
    #         page += 1
    # if not new_choices:
    #     sys.exit("Lỗi: Không tìm thấy bất kỳ collection nào qua API.")

    # write_csv("collection_candidates.csv", cands, ["franchise_no", "franchise", "tmdb_collection_id", "collection_name"])
    # write_csv("collection_choice.csv", new_choices, ["franchise_no", "franchise", "tmdb_collection_ids"])

    # choice = {r["franchise_no"]: r for r in new_choices}
    # seed, reg = [], {}
    # for no, c in choice.items():
    #     ids = [x for x in str(c["tmdb_collection_ids"]).split("|") if x.strip()]
    #     for cid in ids:
    #         j, s = tmdb(f"/collection/{cid}")
    #         time.sleep(0.05)
    #         if not j:
    #             LOG.add("TMDB", f"{c['franchise']}/{cid}", "collection", f"HTTP {s}")
    #             continue
    #         if len(j.get("parts", [])) < 2:
    #             LOG.add("TMDB", f"{c['franchise']}/{cid}", "collection", "<2 films", "kept, flagged", "", "OPEN")
    #         for p in j.get("parts", []):
    #             seed.append(dict(franchise_no=no, franchise=c["franchise"], tmdb_collection_id=cid, tmdb_id=p["id"],
    #                              title=p.get("title"), release_date=p.get("release_date") or "",
    #           
    need_key()
    
    print("Đang đọc danh sách Collection ID từ file JSON và gọi TMDB API...")
    cands, new_choices, seed, clean = [], [], [], []
    reg = {}
    seen_tmdb_ids = set()
    franchise_idx = 1
    
    # Đọc danh sách ID từ file JSON đã có
    json_file_path = "collection_ids_10_22_2026.json"
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            collection_ids = [json.loads(line)["id"] for line in f if line.strip()]
    except FileNotFoundError:
        sys.exit(f"Lỗi: Không tìm thấy file {json_file_path}. Vui lòng kiểm tra lại đường dẫn.")

    print(f"Đã tải {len(collection_ids)} Collection ID. Bắt đầu xử lý...")

    for cid in collection_ids:
        # Gọi trực tiếp thông tin collection bằng ID đã lấy từ file JSON
        j, s = tmdb(f"/collection/{cid}")
        time.sleep(0.05) # Tránh bị chặn do gọi API quá nhanh
        
        # Nếu HTTP status không phải 200 (thường là 404 do ID không tồn tại), bỏ qua luôn
        if s != 200 or not j:
            continue
            
        parts = j.get("parts", [])
        
        # Bắt buộc: Loại bỏ hoàn toàn những collection có dưới 2 phim
        if len(parts) < 2:
            continue
            
        # Lưu thông tin Collection hợp lệ
        cname = j.get("name", f"Collection {cid}")
        cands.append(dict(franchise_no=str(franchise_idx), franchise=cname, tmdb_collection_id=str(cid), collection_name=cname))
        new_choices.append(dict(franchise_no=str(franchise_idx), franchise=cname, tmdb_collection_ids=str(cid)))
        
        # Xử lý ngay lập tức các phim (parts) bên trong Collection này
        for p in parts:
            tmdb_id = p["id"]
            if tmdb_id in seen_tmdb_ids:
                LOG.add("TMDB", str(tmdb_id), "tmdb_id", "duplicate across collections", "kept first", "", "OPEN")
                continue
                
            seen_tmdb_ids.add(tmdb_id)
            
            # Đẩy vào danh sách seed_films
            seed.append(dict(
                franchise_no=str(franchise_idx), 
                franchise=cname, 
                tmdb_collection_id=str(cid), 
                tmdb_id=tmdb_id,
                title=p.get("title"), 
                release_date=p.get("release_date") or "",
                source="TMDB", 
                retrieval_date=TODAY
            ))
            
            # Đẩy vào film registry
            reg[str(tmdb_id)] = dict(
                tmdb_id=tmdb_id, 
                film_key=film_key(tmdb_id), 
                key_rule="PROVISIONAL"
            )
            
        franchise_idx += 1
        
        # Cứ tìm được 50 collection thì in ra màn hình để theo dõi tiến độ
        if franchise_idx % 50 == 0:
            print(f" -> Đã thu thập {franchise_idx} collections hợp lệ (đang quét ở ID: {cid})...")


    if not cands:
        sys.exit("Lỗi: Không tìm thấy bất kỳ collection nào hợp lệ.")

    if seed:
        write_csv("seed_films.csv", seed, list(seed[0].keys()))
    if reg:
        write_csv("film_registry.csv", list(reg.values()), ["tmdb_id", "film_key", "key_rule"])

    LOG.save()
    print(f"\n--- TỔNG KẾT BƯỚC C1 ---")
    print(f"Số Collection hợp lệ thu được: {len(cands)}")
    print(f"Tổng số lượng phim (seed films): {len(seed)}")
    # seen, clean = set(), []
    # for r in seed:
    #     if r["tmdb_id"] in seen:
    #         LOG.add("TMDB", str(r["tmdb_id"]), "tmdb_id", "duplicate across collections", "kept first", "", "OPEN")
    #         continue
    #     seen.add(r["tmdb_id"])
    #     clean.append(r)
    #     reg[str(r["tmdb_id"])] = dict(tmdb_id=r["tmdb_id"], film_key=film_key(r["tmdb_id"]), key_rule="PROVISIONAL")
    
    # if clean:
    #     write_csv("seed_films.csv", clean, list(clean[0].keys()))
    # if reg:
    #     write_csv("film_registry.csv", list(reg.values()), ["tmdb_id", "film_key", "key_rule"])

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
        vote_cnt = j.get("vote_count")
        genres = j.get("genres", [])  # [ĐÃ SỬA]: Lấy danh sách genres từ TMDB API
        
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
            genre_ids="|".join(str(g["id"]) for g in genres),  # [ĐÃ SỬA]: Thêm cột genre_ids (chuỗi các ID thể loại ngăn cách bằng dấu |)
            production_budget=bud if bud else "",
            budget_missing_flag=not bool(bud),
            release_month=rd[5:7] if len(rd) >= 7 else "",
            vote_count=vote_cnt if vote_cnt is not None else "",
            source="TMDB", retrieval_date=TODAY))
            
        for c in crew:
            credits.append(dict(film_key=fk, person_id=c["id"], role="director", billing_order="", source="TMDB", retrieval_date=TODAY))
        for c in cast:
            credits.append(dict(film_key=fk, person_id=c["id"], role="cast", billing_order=c.get("order", ""), source="TMDB", retrieval_date=TODAY))
        if not cast:
            LOG.add("TMDB", fk, "cast", "empty cast list")
        if not crew:
            LOG.add("TMDB", fk, "director_ids", "no director in crew")
            
    if movies:
        write_csv("movies_raw.csv", movies, list(movies[0].keys()))
    if credits:
        write_csv("credits_raw.csv", credits, ["film_key", "person_id", "role", "billing_order", "source", "retrieval_date"])
    LOG.save()
    print(f"movies_raw: {len(movies)}, credits_raw rows: {len(credits)}")


# ---------- C4b TMDB global worldwide gross ----------
def c4b():
    need_key()
    rows = []
    for m in read_csv("movies_raw.csv"):
        fk = m["film_key"]
        tmdb_id = m["tmdb_id"]
        j, s = tmdb(f"/movie/{tmdb_id}")
        rev = j.get("revenue") if j else None
        
        rows.append(dict(
            film_key=fk,
            market_scope="global",
            global_gross=rev if rev else "",
            missing_flag=not bool(rev),
            source="TMDB API",
            retrieval_date=TODAY
        ))
        if not rev:
            LOG.add("TMDB", fk, "global_gross", "Worldwide revenue (revenue) not found from TMDB", "left missing (not 0)")
            
    LOG.add("TMDB", "all", "territory_code/opening_days_count/opening_theater_count/local_currency_gross",
            "attributes removed per user request", "omitted", "", "RESOLVED")
            
    write_csv("box_office_raw.csv", rows, ["film_key", "market_scope", "global_gross", "missing_flag", "source", "retrieval_date"])
    LOG.save()
    print(f"box_office_raw (global) rows: {len(rows)}")


# ---------- C5 coverage + attrition ----------
def c5():
    mv, bo = read_csv("movies_raw.csv"), read_csv("box_office_raw.csv")
    seed = read_csv("seed_films.csv")
    lines = ["# Coverage report", f"retrieval/report date: {TODAY}", ""]
    lines.append(f"seed films: {len(seed)} | movies_raw: {len(mv)}")
    
    # [ĐÃ SỬA]: Thêm genre_ids vào vòng lặp kiểm tra non-missing trong báo cáo coverage
    for f in ["imdb_id", "release_date_ref", "tmdb_collection_id", "director_ids", "lead_cast_ids_superset",
              "production_company_ids", "genre_ids", "production_budget", "vote_count"]:
        n = sum(1 for r in mv if r[f] != "")
        lines.append(f"- {f}: {n}/{len(mv)} non-missing")
        
    lines += ["", "box_office_raw (global):"]
    for f in ["global_gross", "missing_flag"]:
        lines.append(f"- {f}: {sum(1 for r in bo if r[f] != '')}/{len(bo)} non-missing")
        
    att = [("seed films", len(seed)), ("movies_raw retrieved", len(mv)),
           ("global gross present", sum(1 for r in bo if r["global_gross"] != ""))]
           
    write_csv("attrition.csv", [dict(stage=a, count=b) for a, b in att], ["stage", "count"])
    (OUT / "coverage_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    os.environ["TMDB_API_KEY"] = "763f28df21fc59bd3da4152438647847"
    os.environ["ADY_CONTACT"] = "nhatlam23122007@gmail.com"
    KEY = os.environ.get("TMDB_API_KEY")

    ALL_STEPS = ["c0", "c1", "c2", "c4b", "c5"]
    STEPS_MAP = {"c0": c0, "c1": c1, "c2": c2, "c4b": c4b, "c5": c5}

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
            print(f"--> [DỪNG TIẾN TRÌNH] Bước {step} yêu cầu chú ý: {e}")
            break
        except Exception as e:
            print(f"--> [LỖI BAN ĐẦU] Bước {step} gặp lỗi: {e}")
            break

    print("\n=== ĐÃ HOÀN THÀNH CHUỖI TIẾN TRÌNH ===")