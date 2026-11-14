#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADY_PRJ - build_ady_tables.py  (schema MVS v3)

WHAT THIS SCRIPT DOES
  1. Reads the 5 raw CSVs from  <base>/data/raw/  (never modifies them).
  2. Writes processed tables (typed, 1:1 with raw, values unchanged)  -> data/processed/
  3. Writes TEMPLATES for the manual work (franchise_film.csv, pair.csv) -> data/curated/
     - existing curated files are NEVER overwritten (your manual work is safe).
  4. Builds data/analytical/pair_analysis.csv from CONFIRMED pairs only.
  5. Writes metadata: source_manifest.csv, feature_registry.csv, validation_report.csv.

WHAT THIS SCRIPT DOES NOT DO
  - It does not confirm any franchise, installment order or pair.
  - It does not mark any opening as comparable (default is 'pending').
  - It does not compute Y for any pair that is not (confirmed AND opening comparable AND both openings > 0).
  - It does not claim a check passed unless that check actually ran and returned PASS.

RUN:  python build_ady_tables.py            (base dir = folder containing this file)
      python build_ady_tables.py --base-dir "D:/ADY"
"""
import argparse
import hashlib
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# 1. CONFIGURATION (edit here, nowhere else)
# ----------------------------------------------------------------------------
TOP_K_CAST = 5                 # decided: top-5 cast
SEED_MIN_OPENING_FILMS = 2     # seed candidate rows only for TMDB collections with >= this many films that HAVE an opening value
                               # (a REVIEW-PRIORITY list, not a decision; every film of the collection is listed so chains are complete)

# Expected raw columns (from the audited files)
RAW_SPEC = {
    "movies_raw": ("movies_raw.csv", ["film_key", "tmdb_id", "imdb_id", "title", "release_date_ref",
                                       "tmdb_collection_id", "director_ids", "lead_cast_ids_superset",
                                       "production_company_ids", "genre_ids", "production_budget",
                                       "budget_missing_flag", "release_month", "vote_count",
                                       "source", "retrieval_date"]),
    "credits_raw": ("credits_raw.csv", ["film_key", "person_id", "role", "billing_order", "source", "retrieval_date"]),
    "box_office_raw": ("box_office_raw.csv", ["film_key", "market_scope", "global_gross", "missing_flag",
                                               "source", "retrieval_date"]),
    "box_office_detailed": ("box_office_detailed.csv", ["film_key", "imdb_id", "domestic_gross",
                                                         "international_gross", "opening_weekend_gross",
                                                         "theater_count"]),
    "rt_scores": ("rt_scores.csv", ["film_key", "critic_score", "audience_score", "rt_url", "rt_status",
                                     "source", "retrieval_date"]),
}

# Allowed values for the hand-edited tables
REL_TYPES = ["mainline", "prequel", "spinoff", "reboot", "remake", "other", "unresolved"]
VERIF_STATUS = ["candidate", "verified", "rejected", "uncertain"]
PAIR_STATUS = ["confirmed", "excluded", "pending"]
OPENING_STATUS = ["pending", "comparable", "not_comparable", "missing", "nonpositive"]
EXCLUSION_REASONS = ["ORDER_UNVERIFIED", "RELATIONSHIP_INELIGIBLE", "ORDER_GAP", "DATE_INVALID", "SOURCE_CONFLICT"]

FF_COLS = ["franchise_id", "film_key", "relationship_type", "installment_number", "verification_status",
           "evidence_note", "evidence_url", "reviewer", "reviewed_at"]
FF_HELPERS = ["_title", "_release_date", "_has_opening", "_collection_size"]   # read-only helper columns
PAIR_COLS = ["franchise_id", "film_key_prev", "film_key_curr", "pair_status", "exclusion_reason",
             "opening_status", "opening_note"]

ENC = "utf-8-sig"   # BOM so Excel opens Unicode titles correctly


# ----------------------------------------------------------------------------
# 2. SMALL HELPERS
# ----------------------------------------------------------------------------
def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv_str(path):
    """Read everything as text. Only EMPTY cells become NA (so 'NA'/'null' text is not silently changed)."""
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""], encoding=ENC)


def to_int(series):
    """Text -> nullable Int64. Returns (series, n_unparseable). Non-integral numbers keep float and are counted."""
    num = pd.to_numeric(series, errors="coerce")
    bad = int((series.notna() & num.isna()).sum())
    if int(((num.dropna() % 1) != 0).sum()) == 0:   # all non-null values are whole numbers
        num = num.round().astype("Int64")
    return num, bad


def to_date(series):
    d = pd.to_datetime(series, errors="coerce", format="%Y-%m-%d")
    bad = int((series.notna() & d.isna()).sum())
    return d, bad


def to_bool(series):
    m = {"True": True, "False": False, "true": True, "false": False, "1": True, "0": False}
    out = series.map(m).astype("boolean")
    bad = int((series.notna() & out.isna()).sum())
    return out, bad


def positive_int(series):
    """Text -> nullable Int64 holding ONLY positive whole numbers. 0, negatives, 1.5, inf/nan, text, blank -> NA.
    (Same rule as franchise_mapping.parse_order, so both scripts agree on what a valid installment number is.)"""
    num = pd.to_numeric(series, errors="coerce").astype("float64")
    ok = np.isfinite(num) & (num >= 1) & (num < 1e9) & (num == np.floor(num))
    return num.where(ok).astype("Int64")


def mapping_conflicts(ff):
    """{franchise_id: reason} for franchises whose franchise_film rows contradict each other.
    Mirrors franchise_mapping.franchise_conflicts: pairs of such a franchise must never reach pair_analysis."""
    out = {}
    ok = ff[ff["franchise_id"].notna() & ff["film_key"].notna()]
    live = ok[ok["verification_status"] != "rejected"]
    nfr = live.groupby("film_key")["franchise_id"].nunique()
    multi = set(nfr[nfr >= 2].index)
    for fr, fk in live.loc[live["film_key"].isin(multi), ["franchise_id", "film_key"]].drop_duplicates().itertuples(index=False):
        out.setdefault(fr, f"film {fk} has non-rejected rows in more than one franchise_id")
    for fr, fk in ok.loc[ok.duplicated(["franchise_id", "film_key"], keep=False), ["franchise_id", "film_key"]].drop_duplicates().itertuples(index=False):
        out.setdefault(fr, f"duplicate franchise_film rows for film {fk}")
    vm = ok[(ok["verification_status"] == "verified") & (ok["relationship_type"] == "mainline")].copy()
    vm["_o"] = positive_int(vm["installment_number"])
    vm = vm[vm["_o"].notna()]
    for fr, o in vm.loc[vm.duplicated(["franchise_id", "_o"], keep=False), ["franchise_id", "_o"]].drop_duplicates().itertuples(index=False):
        out.setdefault(fr, f"duplicate installment_number {int(o)}")
    return out


def write_csv(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding=ENC)


class Report:
    """Collects validation results. A check that raises is recorded as ERROR (never silently skipped)."""
    def __init__(self):
        self.rows = []
        self.ts = now_utc()

    def add(self, check_id, category, table, description, status, observed="", expected="", detail=""):
        self.rows.append(dict(check_id=check_id, category=category, table=table, description=description,
                              status=status, observed=observed, expected=expected, detail=detail,
                              run_timestamp_utc=self.ts))

    def run(self, check_id, category, table, description, fn):
        """fn returns (status, observed, expected, detail). status in PASS/FAIL/WARN/INFO/SKIPPED."""
        try:
            status, observed, expected, detail = fn()
        except Exception as exc:  # record the failure instead of crashing the whole run
            status, observed, expected = "ERROR", "", ""
            detail = f"{type(exc).__name__}: {exc} | {traceback.format_exc(limit=2).strip().splitlines()[-1]}"
        self.add(check_id, category, table, description, status, observed, expected, detail)

    def frame(self):
        return pd.DataFrame(self.rows)

    def has_failures(self):
        return any(r["status"] in ("FAIL", "ERROR") for r in self.rows)


def pf(ok, observed, expected, detail=""):
    """PASS/FAIL helper."""
    return ("PASS" if ok else "FAIL", observed, expected, detail)


# ----------------------------------------------------------------------------
# 3. BUILD PROCESSED TABLES (typing only - no value is repaired, filled or dropped)
# ----------------------------------------------------------------------------
def explode_ids(df, col, out_col):
    """'1|2|3' -> one row per (film_key, id). Returns (frame, n_bad_tokens, n_duplicates_removed)."""
    s = df[["film_key", col]].dropna()
    s = s.assign(**{out_col: s[col].str.split("|")}).explode(out_col)
    s[out_col] = s[out_col].str.strip()
    ok = s[out_col].str.fullmatch(r"\d+").fillna(False)
    n_bad = int((~ok).sum())
    s = s[ok][["film_key", out_col]]
    s[out_col] = s[out_col].astype("int64")
    n_before = len(s)
    s = s.drop_duplicates()
    return s.reset_index(drop=True), n_bad, n_before - len(s)


def build_processed(raw):
    """raw: dict of text DataFrames. Returns (tables dict, parse_info dict)."""
    info = {}
    m, c, b, d, r = (raw[k] for k in ("movies_raw", "credits_raw", "box_office_raw",
                                      "box_office_detailed", "rt_scores"))

    # --- film (1 row / film). Dropped: director_ids & lead_cast (use credit), genre_ids, release_month,
    #     budget_missing_flag (= null), source/retrieval_date (constants -> manifest).
    rd, bad_rd = to_date(m["release_date_ref"])
    tid, bad1 = to_int(m["tmdb_id"])
    coll, bad2 = to_int(m["tmdb_collection_id"])
    bud, bad3 = to_int(m["production_budget"])
    vc, bad4 = to_int(m["vote_count"])
    film = pd.DataFrame({
        "film_key": m["film_key"], "tmdb_id": tid, "imdb_id": m["imdb_id"], "title": m["title"],
        "release_date": rd.dt.strftime("%Y-%m-%d"), "tmdb_collection_id": coll,
        "production_budget": bud, "vote_count": vc})
    info["film_numeric_bad"] = bad1 + bad2 + bad3 + bad4
    info["film_date_bad"] = bad_rd

    # --- film_company bridge (needed for studio_changed; avoids list-in-cell)
    fc, bad_tok, dup_tok = explode_ids(m, "production_company_ids", "company_id")
    info["company_bad_tokens"], info["company_dups_removed"] = bad_tok, dup_tok

    # --- credit (1 row / raw credit line; technical key because (film,person,role) is NOT unique)
    pid, bad5 = to_int(c["person_id"])
    bo, bad6 = to_int(c["billing_order"])
    credit = pd.DataFrame({"credit_row_id": np.arange(1, len(c) + 1), "film_key": c["film_key"],
                           "person_id": pid, "role": c["role"], "billing_order": bo})
    info["credit_numeric_bad"] = bad5 + bad6

    # --- box_office_global (TMDB lifetime gross - descriptive only, NOT opening)
    gg, bad7 = to_int(b["global_gross"])
    bog = pd.DataFrame({"film_key": b["film_key"], "global_gross": gg})
    info["bog_numeric_bad"] = bad7
    info["market_scope_values"] = sorted(b["market_scope"].dropna().unique().tolist())
    mf, bad_mf = to_bool(b["missing_flag"])
    info["missing_flag_bad"] = bad_mf
    info["missing_flag_vs_null_mismatch"] = int((mf.fillna(False) != gg.isna()).sum())

    # --- box_office_detail (opening scope/currency/window NOT documented in source -> see manifest)
    dg, e1 = to_int(d["domestic_gross"])
    ig, e2 = to_int(d["international_gross"])
    og, e3 = to_int(d["opening_weekend_gross"])
    bod = pd.DataFrame({"film_key": d["film_key"], "domestic_gross": dg, "international_gross": ig,
                        "opening_weekend_gross": og})
    info["bod_numeric_bad"] = e1 + e2 + e3
    info["theater_count_nonnull"] = int(d["theater_count"].notna().sum())

    # --- rt_lookup (snapshot scraped in 2026; shared-URL matches unverified)
    cs, f1 = to_int(r["critic_score"])
    au, f2 = to_int(r["audience_score"])
    rt = pd.DataFrame({"film_key": r["film_key"], "critic_score": cs, "audience_score": au,
                       "rt_url": r["rt_url"], "rt_status": r["rt_status"]})
    info["rt_numeric_bad"] = f1 + f2

    return {"film": film, "film_company": fc, "credit": credit, "box_office_global": bog,
            "box_office_detail": bod, "rt_lookup": rt}, info


# ----------------------------------------------------------------------------
# 4. CREDIT-DERIVED SETS (aggregate FIRST, join later -> no row multiplication)
# ----------------------------------------------------------------------------
def director_sets(credit):
    d = credit[(credit["role"] == "director") & credit["person_id"].notna()]
    return d.groupby("film_key")["person_id"].agg(lambda x: frozenset(int(v) for v in x))


def top_cast(credit, k=TOP_K_CAST):
    """Per film: dedupe by person (keep smallest billing_order), sort by (billing_order, person_id), keep top-k.
    Returns DataFrame indexed by film_key with columns top (tuple of ids) and n_cast (distinct people)."""
    c = credit[(credit["role"] == "cast") & credit["person_id"].notna()][["film_key", "person_id", "billing_order"]].copy()
    c["person_id"] = c["person_id"].astype("int64")
    c["bo"] = c["billing_order"].astype("float64").fillna(np.inf)       # null billing order sorts last
    c = c.sort_values(["film_key", "person_id", "bo"]).drop_duplicates(["film_key", "person_id"], keep="first")
    n_cast = c.groupby("film_key").size().rename("n_cast")
    c = c.sort_values(["film_key", "bo", "person_id"])                   # tie-break by person_id
    top = c.groupby("film_key").head(k).groupby("film_key")["person_id"].agg(tuple).rename("top")
    return pd.concat([top, n_cast], axis=1)


# ----------------------------------------------------------------------------
# 5. CURATED TEMPLATES (manual work) - never overwrite existing files
# ----------------------------------------------------------------------------
def make_franchise_film_seed(film, bod):
    """Candidate rows for review. verification_status='candidate', relationship_type='unresolved'.
    franchise_id = 'CAND_<tmdb_collection_id>' is a PROVISIONAL grouping label, not a verified franchise."""
    f = film.merge(bod[["film_key", "opening_weekend_gross"]], on="film_key", how="left")
    f["_has_opening"] = f["opening_weekend_gross"].notna()
    f = f[f["tmdb_collection_id"].notna()]
    g = f.groupby("tmdb_collection_id").agg(n=("film_key", "size"), k=("_has_opening", "sum"))
    keep = g[g["k"] >= SEED_MIN_OPENING_FILMS]
    f = f[f["tmdb_collection_id"].isin(keep.index)].copy()
    f["_collection_size"] = f["tmdb_collection_id"].map(keep["n"])
    f = f.sort_values(["tmdb_collection_id", "release_date", "film_key"], na_position="last")
    out = pd.DataFrame({
        "franchise_id": "CAND_" + f["tmdb_collection_id"].astype(str),
        "film_key": f["film_key"], "relationship_type": "unresolved", "installment_number": "",
        "verification_status": "candidate", "evidence_note": "", "evidence_url": "", "reviewer": "",
        "reviewed_at": "", "_title": f["title"], "_release_date": f["release_date"],
        "_has_opening": f["_has_opening"], "_collection_size": f["_collection_size"]})
    return out.reset_index(drop=True), len(keep)


def load_curated(path, cols):
    """Load a hand-edited table; strip whitespace; drop helper columns."""
    df = read_csv_str(path)
    for col in cols:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[cols].copy()
    for col in df.columns:
        df[col] = df[col].astype("string").str.strip().replace("", pd.NA)
    return df


# ----------------------------------------------------------------------------
# 6. PAIR ANALYSIS (derived; CONFIRMED pairs only; Y only if fully eligible)
# ----------------------------------------------------------------------------
def build_pair_analysis(tables, ff, pair, credit_dir, credit_cast, build_ts):
    """Returns (mart DataFrame, issues list[str]). Pairs failing integrity are excluded from the mart and listed."""
    film, bod, rt = tables["film"], tables["box_office_detail"], tables["rt_lookup"]
    comp = tables["film_company"].groupby("film_key")["company_id"].agg(lambda x: frozenset(int(v) for v in x))
    issues = []
    cols = ["franchise_id", "film_key_prev", "film_key_curr", "installment_prev", "installment_curr",
            "pair_status", "opening_status", "open_prev", "open_curr", "log_open_prev", "Y", "y_status",
            "gap_years", "is_director_changed", "cast_retention_top5", "cast_n_prev", "cast_n_curr",
            "studio_changed", "budget_prev", "budget_curr", "critic_score_prev", "audience_score_prev",
            "build_timestamp_utc"]
    conf = pair[pair["pair_status"] == "confirmed"].copy()
    if conf.empty:
        return pd.DataFrame(columns=cols), issues

    # verified mainline membership with integer order
    ffv = ff[(ff["verification_status"] == "verified") & (ff["relationship_type"] == "mainline")].copy()
    ffv["installment_number"] = positive_int(ffv["installment_number"])          # positive whole numbers only
    ffv = ffv[ffv["installment_number"].notna()].drop_duplicates(["franchise_id", "film_key"])
    conflicts = mapping_conflicts(ff)                                              # contradictory franchises never enter the mart
    key = ffv[["franchise_id", "film_key", "installment_number"]]
    p = conf.merge(key.rename(columns={"film_key": "film_key_prev", "installment_number": "installment_prev"}),
                   on=["franchise_id", "film_key_prev"], how="left")
    p = p.merge(key.rename(columns={"film_key": "film_key_curr", "installment_number": "installment_curr"}),
                on=["franchise_id", "film_key_curr"], how="left")
    assert len(p) == len(conf), "row count changed while attaching installment order"

    bad = (p["installment_prev"].isna() | p["installment_curr"].isna() |
           ((p["installment_curr"] - p["installment_prev"]) != 1) |
           p["franchise_id"].isin(list(conflicts))).fillna(True).astype(bool)
    for _, row in p[bad].iterrows():
        why = ("franchise_film conflict: " + conflicts[row["franchise_id"]]) if row["franchise_id"] in conflicts \
            else "order/verification integrity"
        issues.append(f"confirmed pair excluded from mart ({why}): "
                      f"{row['franchise_id']} {row['film_key_prev']}->{row['film_key_curr']}")
    p = p[~bad].copy()
    if p.empty:
        return pd.DataFrame(columns=cols), issues

    # attach film-level facts with explicit 1:1 / 1:0..1 joins and row-count assertions
    fk = film.set_index("film_key")
    bd = bod.set_index("film_key")
    rr = rt.set_index("film_key")
    n0 = len(p)
    for side in ("prev", "curr"):
        k = p[f"film_key_{side}"]
        p[f"date_{side}"] = pd.to_datetime(k.map(fk["release_date"]), errors="coerce")
        p[f"budget_{side}"] = k.map(fk["production_budget"])
        p[f"open_{side}"] = k.map(bd["opening_weekend_gross"])
    kp = p["film_key_prev"]
    p["critic_score_prev"] = kp.map(rr["critic_score"])
    p["audience_score_prev"] = kp.map(rr["audience_score"])
    assert len(p) == n0, "row count changed after film-level lookups"

    # target: ONLY when opening_status == 'comparable' and both openings are positive
    op = p["open_prev"].astype("float64")
    oc = p["open_curr"].astype("float64")
    eligible = (p["opening_status"] == "comparable") & (op > 0) & (oc > 0)
    p["log_open_prev"] = np.where(eligible, np.log(op.where(eligible)), np.nan)
    p["Y"] = np.where(eligible, np.log(oc.where(eligible)) - np.log(op.where(eligible)), np.nan)

    def why(row):
        if row["opening_status"] != "comparable":
            return f"not_computed:opening_status={row['opening_status']}"
        if pd.isna(row["open_prev"]) or pd.isna(row["open_curr"]):
            return "not_computed:opening_missing"
        return "not_computed:opening_nonpositive"
    p["y_status"] = np.where(eligible, "computed", p.apply(why, axis=1))

    # features (null whenever an input is missing - never 0)
    p["gap_years"] = (p["date_curr"] - p["date_prev"]).dt.days / 365.25
    dprev, dcurr = p["film_key_prev"].map(credit_dir), p["film_key_curr"].map(credit_dir)
    p["is_director_changed"] = [pd.NA if (isinstance(a, float) or isinstance(b, float)) else (a != b)
                                for a, b in zip(dprev, dcurr)]
    p["is_director_changed"] = p["is_director_changed"].astype("boolean")
    ctop_prev, ctop_curr = p["film_key_prev"].map(credit_cast["top"]), p["film_key_curr"].map(credit_cast["top"])
    p["cast_n_prev"] = p["film_key_prev"].map(credit_cast["n_cast"])
    p["cast_n_curr"] = p["film_key_curr"].map(credit_cast["n_cast"])
    ret = []
    for a, b, na, nb in zip(ctop_prev, ctop_curr, p["cast_n_prev"], p["cast_n_curr"]):
        # rule: need >= TOP_K_CAST distinct cast in BOTH films, otherwise null (documented default)
        if isinstance(a, tuple) and isinstance(b, tuple) and na >= TOP_K_CAST and nb >= TOP_K_CAST:
            ret.append(len(set(a) & set(b)) / TOP_K_CAST)
        else:
            ret.append(np.nan)
    p["cast_retention_top5"] = ret
    cprev, ccurr = p["film_key_prev"].map(comp), p["film_key_curr"].map(comp)
    p["studio_changed"] = [pd.NA if (isinstance(a, float) or isinstance(b, float)) else (a != b)
                           for a, b in zip(cprev, ccurr)]
    p["studio_changed"] = p["studio_changed"].astype("boolean")
    p["build_timestamp_utc"] = build_ts
    return p[cols].reset_index(drop=True), issues


# ----------------------------------------------------------------------------
# 7. FEATURE REGISTRY (leakage control). 'pending' = not allowed in RQ1 until evidence is added
# ----------------------------------------------------------------------------
def build_feature_registry():
    R = []
    def add(name, role, src, time_basis, rq1, rq2, evidence, note):
        R.append(dict(feature_name=name, role=role, source=src, time_basis=time_basis,
                      rq1_allowed=rq1, rq2_allowed=rq2, evidence_status=evidence, note=note))
    add("Y", "target", "ln(open_curr)-ln(open_prev)", "outcome", "target", "target", "decided",
        "Only computed when pair confirmed AND opening_status=comparable AND both openings > 0.")
    add("open_prev", "target_input", "box_office_detail.opening_weekend_gross (N-1)", "known_before_N", "target_input", "target_input", "pending",
        "Scope/currency/window of opening NOT documented in source file -> comparability stays pending.")
    add("open_curr", "target_input", "box_office_detail.opening_weekend_gross (N)", "outcome", "target_input", "target_input", "pending", "Part of Y; never a predictor.")
    add("log_open_prev", "feature", "ln(open_prev)", "known_before_N", "pending", "yes", "pending",
        "Depends on opening comparability rule (pending).")
    add("gap_years", "feature", "film.release_date (N) - (N-1)", "pre_release_known", "yes", "yes", "assumption",
        "Assumes the scheduled release date of N is known at prediction time. Team must state the prediction time point.")
    add("is_director_changed", "feature", "credit(role=director) sets", "pre_release_known", "yes", "yes", "assumption",
        "Credits are a 2026 TMDB snapshot; directors are normally announced pre-release (assumption).")
    add("cast_retention_top5", "feature", "credit(role=cast) top-5 by billing_order", "pre_release_known", "pending", "yes", "assumption",
        "Final billing order is from a 2026 snapshot; pre-release billing may differ -> pending for RQ1. Null if < 5 distinct cast in either film.")
    add("studio_changed", "feature", "film_company sets", "pre_release_known", "yes", "yes", "assumption",
        "Production-company lists are a 2026 snapshot (assumed stable).")
    add("budget_prev", "feature", "film.production_budget (N-1)", "known_before_N", "yes", "yes", "assumption", "~89% null in raw; null is kept, never 0.")
    add("budget_curr", "feature", "film.production_budget (N)", "unknown", "pending", "yes", "pending",
        "Budget of N is often reported after release -> pending for RQ1.")
    add("critic_score_prev", "feature", "rt_lookup.critic_score (N-1)", "snapshot_2026", "pending", "pending", "unverified",
        "Scraped 2026-10; not the score visible when N was released. Shared RT URLs unverified.")
    add("audience_score_prev", "feature", "rt_lookup.audience_score (N-1)", "snapshot_2026", "pending", "pending", "unverified",
        "Same limitation as critic_score_prev.")
    add("vote_count", "excluded", "film.vote_count", "snapshot_2026", "no", "pending", "unverified",
        "2026 snapshot; kept in film table but NOT placed in pair_analysis.")
    return pd.DataFrame(R)


# ----------------------------------------------------------------------------
# 8. MAIN
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Build ADY processed tables, templates and validation report.")
    ap.add_argument("--base-dir", default=str(Path(__file__).resolve().parent),
                    help="project folder containing data/raw (default: folder of this script)")
    ap.add_argument("--force-templates", action="store_true",
                    help="DANGEROUS: overwrite franchise_film.csv / pair.csv (destroys manual work)")
    args = ap.parse_args()

    base = Path(args.base_dir)
    raw_dir, proc_dir = base / "data" / "raw", base / "data" / "processed"
    cur_dir, ana_dir, meta_dir = base / "data" / "curated", base / "data" / "analytical", base / "metadata"
    for dpath in (raw_dir, proc_dir, cur_dir, ana_dir, meta_dir):
        dpath.mkdir(parents=True, exist_ok=True)

    rep = Report()
    run_ts = rep.ts

    # ---- R01: raw files exist -------------------------------------------------
    missing = [fn for fn, _ in RAW_SPEC.values() if not (raw_dir / fn).exists()]
    if missing:
        rep.add("R01", "raw", "-", "All 5 raw files present", "FAIL", f"missing={missing}", "none missing",
                f"Put the files in {raw_dir}")
        write_csv(rep.frame(), meta_dir / "validation_report.csv")
        print(f"[ERROR] Missing raw files in {raw_dir}: {missing}")
        sys.exit(1)
    rep.add("R01", "raw", "-", "All 5 raw files present", "PASS", "5/5", "5/5")

    # ---- hash BEFORE, load raw ------------------------------------------------
    hash_before = {k: sha256_of(raw_dir / fn) for k, (fn, _) in RAW_SPEC.items()}
    raw = {k: read_csv_str(raw_dir / fn) for k, (fn, _) in RAW_SPEC.items()}

    bad_cols = []
    for k, (fn, cols) in RAW_SPEC.items():
        miss = [c for c in cols if c not in raw[k].columns]
        extra = [c for c in raw[k].columns if c not in cols]
        if miss:
            bad_cols.append(f"{fn}: missing {miss}")
        if extra:
            rep.add("R02x", "raw", k, "Unexpected extra columns (ignored by this script)", "WARN", str(extra), "none")
    if bad_cols:
        rep.add("R02", "raw", "-", "Required columns present", "FAIL", "; ".join(bad_cols), "all present")
        write_csv(rep.frame(), meta_dir / "validation_report.csv")
        print("[ERROR] Column mismatch:", bad_cols)
        sys.exit(1)
    rep.add("R02", "raw", "-", "Required columns present in all 5 files", "PASS", "all present", "all present")

    # ---- processed tables -----------------------------------------------------
    tables, info = build_processed(raw)
    for name, df in tables.items():
        write_csv(df, proc_dir / f"{name}.csv")
    film, credit, bog, bod, rt, fcomp = (tables[k] for k in
                                         ("film", "credit", "box_office_global", "box_office_detail",
                                          "rt_lookup", "film_company"))

    # ---- curated templates (never overwrite) ----------------------------------
    ff_path, pair_path = cur_dir / "franchise_film.csv", cur_dir / "pair.csv"
    if args.force_templates or not ff_path.exists():
        seed, n_coll = make_franchise_film_seed(film, bod)
        write_csv(seed, ff_path)
        rep.add("T00a", "template", "franchise_film", "Seed file written (all rows 'candidate'/'unresolved')", "INFO",
                f"rows={len(seed)}, collections={n_coll}", "",
                f"Review-priority list: collections with >= {SEED_MIN_OPENING_FILMS} films that have an opening value. "
                "Not a decision. Complete the chain (incl. films without opening) before marking verified.")
    else:
        rep.add("T00a", "template", "franchise_film", "Existing file kept (not overwritten)", "INFO", str(ff_path), "")
    if args.force_templates or not pair_path.exists():
        write_csv(pd.DataFrame(columns=PAIR_COLS), pair_path)
        rep.add("T00b", "template", "pair", "Empty template written (header only; no pairs created)", "INFO", "rows=0", "")
    else:
        rep.add("T00b", "template", "pair", "Existing file kept (not overwritten)", "INFO", str(pair_path), "")

    ff = load_curated(ff_path, FF_COLS)
    pair = load_curated(pair_path, PAIR_COLS)

    # ---- pair_analysis --------------------------------------------------------
    cdir, ccast = director_sets(credit), top_cast(credit)
    mart, mart_issues = build_pair_analysis(tables, ff, pair, cdir, ccast, run_ts)
    write_csv(mart, ana_dir / "pair_analysis.csv")

    # ---- feature registry + funnel -------------------------------------------
    registry = build_feature_registry()
    write_csv(registry, meta_dir / "feature_registry.csv")
    if len(pair):
        funnel = (pair.fillna({"exclusion_reason": "(none)"})
                  .groupby(["pair_status", "exclusion_reason", "opening_status"], dropna=False)
                  .size().reset_index(name="n_pairs"))
    else:
        funnel = pd.DataFrame(columns=["pair_status", "exclusion_reason", "opening_status", "n_pairs"])
    write_csv(funnel, meta_dir / "pair_funnel.csv")

    # =========================================================================
    # VALIDATION CHECKS (every row below was executed in this run)
    # =========================================================================
    # --- keys
    rep.run("K01", "key", "film", "film_key non-null and unique", lambda: pf(
        film["film_key"].notna().all() and film["film_key"].is_unique,
        f"nulls={int(film['film_key'].isna().sum())}, dups={int(film['film_key'].duplicated().sum())}", "0 / 0"))
    rep.run("K02", "key", "film", "tmdb_id non-null and unique", lambda: pf(
        film["tmdb_id"].notna().all() and film["tmdb_id"].is_unique,
        f"nulls={int(film['tmdb_id'].isna().sum())}, dups={int(film['tmdb_id'].duplicated().sum())}", "0 / 0"))
    rep.run("K03", "key", "film", "film_key == 'FK' + 8-digit tmdb_id (re-encoding of tmdb_id)", lambda: (
        lambda mm: ("PASS" if mm == 0 else "WARN", f"mismatches={mm}", "0",
                    "film_key is only a re-encoding of tmdb_id; it adds no independent identity")
    )(int((film["film_key"] != "FK" + film["tmdb_id"].astype("string").str.zfill(8)).sum())))
    for name, df in (("box_office_global", bog), ("box_office_detail", bod), ("rt_lookup", rt)):
        rep.run(f"F-{name}", "fk", name, "film_key unique and subset of film", lambda df=df: pf(
            df["film_key"].is_unique and df["film_key"].isin(film["film_key"]).all(),
            f"dups={int(df['film_key'].duplicated().sum())}, orphans={int((~df['film_key'].isin(film['film_key'])).sum())}", "0 / 0"))
    rep.run("F-credit", "fk", "credit", "film_key subset of film (orphans)", lambda: pf(
        credit["film_key"].isin(film["film_key"]).all(),
        f"orphans={int((~credit['film_key'].isin(film['film_key'])).sum())}", "0"))
    rep.run("F-film_company", "fk", "film_company", "film_key subset of film (orphans)", lambda: pf(
        fcomp["film_key"].isin(film["film_key"]).all(), f"orphans={int((~fcomp['film_key'].isin(film['film_key'])).sum())}", "0"))

    # --- row counts raw vs processed
    rep.run("C01", "rowcount", "all", "Processed row counts equal raw row counts (film_company excluded: exploded)", lambda: pf(
        all([len(film) == len(raw["movies_raw"]), len(credit) == len(raw["credits_raw"]),
             len(bog) == len(raw["box_office_raw"]), len(bod) == len(raw["box_office_detailed"]),
             len(rt) == len(raw["rt_scores"])]),
        f"film={len(film)}/{len(raw['movies_raw'])}, credit={len(credit)}/{len(raw['credits_raw'])}, "
        f"global={len(bog)}/{len(raw['box_office_raw'])}, detail={len(bod)}/{len(raw['box_office_detailed'])}, "
        f"rt={len(rt)}/{len(raw['rt_scores'])}", "equal"))

    # --- parsing
    rep.run("P01", "parse", "all", "Non-empty numeric cells that failed to parse", lambda: pf(
        sum(info[k] for k in ("film_numeric_bad", "credit_numeric_bad", "bog_numeric_bad", "bod_numeric_bad", "rt_numeric_bad")) == 0,
        str({k: info[k] for k in ("film_numeric_bad", "credit_numeric_bad", "bog_numeric_bad", "bod_numeric_bad", "rt_numeric_bad")}), "all 0"))
    rep.run("P02", "parse", "film", "release_date cells that failed to parse (YYYY-MM-DD)", lambda: pf(
        info["film_date_bad"] == 0, str(info["film_date_bad"]), "0"))
    rep.run("P03", "parse", "film_company", "production_company_ids tokens not numeric / duplicates removed", lambda: (
        "PASS" if info["company_bad_tokens"] == 0 else "WARN",
        f"bad_tokens={info['company_bad_tokens']}, dup_pairs_removed={info['company_dups_removed']}", "bad=0", ""))
    rep.run("P04", "parse", "box_office_global", "missing_flag parses as boolean", lambda: pf(
        info["missing_flag_bad"] == 0, str(info["missing_flag_bad"]), "0"))

    # --- values
    def nonpos():
        out = {}
        for t, col, df in (("detail", "opening_weekend_gross", bod), ("detail", "domestic_gross", bod),
                           ("detail", "international_gross", bod), ("global", "global_gross", bog),
                           ("film", "production_budget", film)):
            s = df[col]
            out[f"{t}.{col}"] = int((s.dropna() <= 0).sum())
        return ("PASS" if sum(out.values()) == 0 else "WARN", str(out), "all 0", "Zero/negative values would break ln(); null is not counted")
    rep.run("V01", "value", "money", "Non-null money values <= 0", nonpos)
    rep.run("V02", "value", "box_office_global", "missing_flag consistent with global_gross null", lambda: pf(
        info["missing_flag_vs_null_mismatch"] == 0, str(info["missing_flag_vs_null_mismatch"]), "0"))
    rep.run("V03", "value", "box_office_global", "market_scope values in raw", lambda: (
        "INFO", str(info["market_scope_values"]), "", "Constant column; gross is TMDB lifetime figure, NOT opening"))
    rep.run("V04", "value", "credit", "role values", lambda: pf(
        set(credit["role"].dropna().unique()) <= {"cast", "director"} and credit["role"].notna().all(),
        str(sorted(credit["role"].dropna().unique())), "{cast, director}"))
    rep.run("V05", "value", "credit", "credit_row_id unique", lambda: pf(credit["credit_row_id"].is_unique, "", "unique"))
    rep.run("V06", "value", "credit", "(film_key, person_id, role) duplicate rows (known; kept, handled by dedupe in features)", lambda: (
        "INFO", f"rows_in_dup_groups={int(credit.duplicated(['film_key','person_id','role'], keep=False).sum())}", "",
        "Not an error classification - rows are kept; cast features dedupe by person"))
    rep.run("V07", "value", "credit vs movies_raw", "director set in movies_raw.director_ids equals credit directors", lambda: (
        lambda cmp: ("PASS" if cmp == 0 else "WARN", f"films_with_difference={cmp}", "0",
                     "movies_raw.director_ids is not used by the pipeline; credit is the single source")
    )(sum(
        1 for fk_, ids in raw["movies_raw"].set_index("film_key")["director_ids"].dropna().items()
        if frozenset(int(x) for x in ids.split("|") if x.strip().isdigit()) != cdir.get(fk_, frozenset())
    )))
    rep.run("V08", "value", "box_office_detail", "theater_count non-empty cells", lambda: (
        "INFO", str(info["theater_count_nonnull"]), "", "Column dropped from processed table if 0 (empty in source)"))
    rep.run("V09", "value", "rt_lookup", "UNMATCHED rows must have no scores; shared rt_url count", lambda: (
        lambda um, sh: ("PASS" if um == 0 else "FAIL", f"unmatched_with_score={um}; urls_shared_by_multiple_films={sh}", "0",
                        "Shared URLs = RT matching unverified (info only)")
    )(int((rt["rt_status"].eq("UNMATCHED") & (rt["critic_score"].notna() | rt["audience_score"].notna())).sum()),
      int((rt["rt_url"].dropna().value_counts() > 1).sum())))
    rep.run("V10", "value", "film", "release_date: null / Jan-01 / after raw retrieval date", lambda: (
        lambda d_, mx: ("INFO", f"null={int(d_.isna().sum())}, jan01={int(((d_.dt.month==1)&(d_.dt.day==1)).sum())}, "
                        f"after_{mx.date()}={int((d_>mx).sum())}", "",
                        "Flags only; dates are not repaired. Date order alone never proves installment order")
    )(pd.to_datetime(film["release_date"], errors="coerce"),
      pd.to_datetime(raw["movies_raw"]["retrieval_date"], errors="coerce").max()))
    rep.run("V11", "coverage", "box_office_detail", "Films with opening_weekend_gross (selection concern)", lambda: (
        "INFO", f"{int(bod['opening_weekend_gross'].notna().sum())} of {len(film)} films "
                f"({bod['opening_weekend_gross'].notna().sum()/len(film):.2%})", "",
        "Coverage depends strongly on popularity; opening scope/currency/window undocumented -> comparability stays 'pending'"))

    # --- join safety (executed)
    def join_chain():
        x = film.merge(bog, on="film_key", how="left", validate="1:1")
        x = x.merge(bod, on="film_key", how="left", validate="1:1")
        x = x.merge(rt, on="film_key", how="left", validate="1:1")
        return pf(len(x) == len(film), f"{len(x)} rows", f"{len(film)} rows")
    rep.run("J01", "join", "film+global+detail+rt", "LEFT JOIN chain keeps film grain (validate=1:1)", join_chain)

    def join_credit_agg():
        summ = pd.DataFrame({"n_director": cdir.map(len)}).join(ccast["n_cast"], how="outer")
        x = film.merge(summ, left_on="film_key", right_index=True, how="left", validate="1:1")
        return pf(len(x) == len(film), f"{len(x)} rows; films_without_credits={int(x[['n_director','n_cast']].isna().all(axis=1).sum())}",
                  f"{len(film)} rows", "Credits aggregated to 1 row/film BEFORE joining; films without credits stay null")
    rep.run("J02", "join", "film+credit(aggregated)", "Aggregated credits join keeps film grain", join_credit_agg)

    # --- curated tables (only meaningful when someone has edited them)
    def check_ff():
        if ff["film_key"].isna().all() and len(ff) == 0:
            return ("SKIPPED", "empty", "", "")
        probs = []
        probs.append(f"unknown film_key={int((~ff['film_key'].isin(film['film_key'])).sum())}")
        probs.append(f"dup(franchise_id,film_key)={int(ff.duplicated(['franchise_id','film_key']).sum())}")
        probs.append(f"bad relationship_type={int((~ff['relationship_type'].isin(REL_TYPES)).sum())}")
        probs.append(f"bad verification_status={int((~ff['verification_status'].isin(VERIF_STATUS)).sum())}")
        ver = ff[ff["verification_status"] == "verified"]
        n_ver = len(ver)
        if n_ver == 0:
            return ("SKIPPED", f"rows={len(ff)}, verified=0", "", "No verified rows yet; structure checks: " + "; ".join(probs))
        vm = ver[ver["relationship_type"] == "mainline"]
        order = positive_int(vm["installment_number"])
        probs.append(f"verified mainline without positive integer order={int(order.isna().sum())}")
        probs.append(f"verified: film in >1 franchise={int(ver['film_key'].duplicated().sum())}")
        probs.append(f"dup (franchise_id, installment_number)={int(vm.assign(o=order).dropna(subset=['o']).duplicated(['franchise_id','o']).sum())}")
        probs.append(f"verified without evidence_note/url={int((ver['evidence_note'].isna() & ver['evidence_url'].isna()).sum())}")
        ok = all(p.endswith("=0") for p in probs)
        return ("PASS" if ok else "FAIL", "; ".join(probs), "all 0", "")
    rep.run("T01", "curated", "franchise_film", "Enum values, FK, uniqueness, order, evidence", check_ff)

    def check_pair():
        if len(pair) == 0:
            return ("SKIPPED", "pair.csv has 0 rows", "", "No pairs created (by design)")
        probs = [f"dup pair key={int(pair.duplicated(['film_key_prev','film_key_curr']).sum())}",
                 f"unknown film_key={int((~pair['film_key_prev'].isin(film['film_key']) | ~pair['film_key_curr'].isin(film['film_key'])).sum())}",
                 f"prev==curr={int((pair['film_key_prev'] == pair['film_key_curr']).sum())}",
                 f"bad pair_status={int((~pair['pair_status'].isin(PAIR_STATUS)).sum())}",
                 f"bad opening_status={int((~pair['opening_status'].isin(OPENING_STATUS)).sum())}",
                 f"excluded without valid reason={int(((pair['pair_status']=='excluded') & ~pair['exclusion_reason'].isin(EXCLUSION_REASONS)).sum())}",
                 f"confirmed failing order integrity={len(mart_issues)}"]
        d_ = pd.to_datetime(pair["film_key_prev"].map(film.set_index('film_key')["release_date"]), errors="coerce")
        e_ = pd.to_datetime(pair["film_key_curr"].map(film.set_index('film_key')["release_date"]), errors="coerce")
        warn = int(((pair["pair_status"] == "confirmed") & (e_ < d_)).sum())
        ok = all(p.endswith("=0") for p in probs)
        return ("PASS" if ok and warn == 0 else ("FAIL" if not ok else "WARN"),
                "; ".join(probs) + f"; confirmed with date_curr<date_prev={warn}", "all 0", "; ".join(mart_issues[:5]))
    rep.run("T02", "curated", "pair", "Pair integrity (franchise, adjacency, enums, reasons, dates)", check_pair)

    def check_mart():
        if len(mart) == 0:
            return ("SKIPPED", "pair_analysis has 0 rows", "", "No confirmed pairs yet")
        y = mart["Y"].astype("float64")
        recompute = np.log(mart["open_curr"].astype("float64")) - np.log(mart["open_prev"].astype("float64"))
        has_y = y.notna()
        probs = [f"rows!=confirmed valid pairs={int(len(mart) != int((pair['pair_status']=='confirmed').sum()) - len(mart_issues))}",
                 f"Y present while opening_status!=comparable={int((has_y & (mart['opening_status'] != 'comparable')).sum())}",
                 f"Y differs from independent recompute={int(((y[has_y] - recompute[has_y]).abs() > 1e-9).sum())}",
                 f"dup pair key={int(mart.duplicated(['film_key_prev','film_key_curr']).sum())}"]
        return ("PASS" if all(p.endswith("=0") for p in probs) else "FAIL", "; ".join(probs), "all 0", "")
    rep.run("M01", "mart", "pair_analysis", "One row per confirmed pair; Y only when eligible; Y recomputed independently", check_mart)

    meta_cols = {"franchise_id", "film_key_prev", "film_key_curr", "installment_prev", "installment_curr", "pair_status",
                 "opening_status", "y_status", "build_timestamp_utc", "cast_n_prev", "cast_n_curr"}
    rep.run("L01", "leakage", "pair_analysis", "Every mart column is registered in feature_registry", lambda: (
        lambda unreg: pf(len(unreg) == 0, f"unregistered={unreg}", "[]")
    )(sorted(set(mart.columns) - meta_cols - set(registry["feature_name"]))))
    rep.run("L02", "leakage", "feature_registry", "No snapshot_2026 feature is marked rq1_allowed='yes'", lambda: (
        lambda bad: pf(len(bad) == 0, f"violations={bad}", "[]")
    )(registry[(registry["time_basis"] == "snapshot_2026") & (registry["rq1_allowed"] == "yes")]["feature_name"].tolist()))

    # --- raw unchanged + manifest
    hash_after = {k: sha256_of(raw_dir / fn) for k, (fn, _) in RAW_SPEC.items()}
    rep.run("R03", "raw", "all", "Raw files byte-identical after run (sha256 before == after)", lambda: pf(
        hash_before == hash_after, "identical" if hash_before == hash_after else "CHANGED", "identical"))

    notes = {
        "movies_raw": "TMDB. tmdb_collection_id present for ~all films: candidate signal only, not franchise evidence.",
        "credits_raw": "TMDB. (film_key, person_id, role) not unique; director rows have no billing_order.",
        "box_office_raw": "TMDB lifetime 'global' gross (constant market_scope). NOT an opening figure.",
        "box_office_detailed": "NO source/date/market/currency/window columns. Opening scope UNVERIFIED -> all openings 'pending'. theater_count empty.",
        "rt_scores": "Rotten Tomatoes lookup scraped 2026; rt_url shared by multiple films (matching unverified).",
    }
    man = []
    for k, (fn, cols) in RAW_SPEC.items():
        df = raw[k]
        man.append(dict(table=k, file=fn, sha256=hash_before[k], bytes=(raw_dir / fn).stat().st_size,
                        rows=len(df), columns=len(df.columns),
                        source_values="|".join(sorted(df["source"].dropna().unique())) if "source" in df.columns else "(no source column)",
                        retrieval_dates="|".join(sorted(df["retrieval_date"].dropna().unique())) if "retrieval_date" in df.columns else "(no retrieval_date column)",
                        unchanged_after_run=(hash_before[k] == hash_after[k]), definition_notes=notes[k], manifest_built_utc=run_ts))
    write_csv(pd.DataFrame(man), meta_dir / "source_manifest.csv")

    out = rep.frame()
    write_csv(out, meta_dir / "validation_report.csv")

    # ---- console summary ------------------------------------------------------
    print("\n=== ADY build finished ===")
    print(out["status"].value_counts().to_string())
    for _, r_ in out[out["status"].isin(["FAIL", "ERROR", "WARN"])].iterrows():
        print(f"  [{r_['status']}] {r_['check_id']} {r_['table']}: {r_['observed']} {r_['detail']}")
    print(f"\nOutputs under: {base}")
    sys.exit(1 if rep.has_failures() else 0)


if __name__ == "__main__":
    main()
