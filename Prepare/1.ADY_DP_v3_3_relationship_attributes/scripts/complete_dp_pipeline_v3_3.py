#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADY_PRJ - complete_dp_pipeline_v3_3.py (Tasks 3-5 + diagnostic extension)   v3: built ON TOP OF build_ady_tables.py

REUSED FROM build_ady_tables.py (imported, file unchanged):
    RAW_SPEC, read_csv_str, build_processed, director_sets, top_cast, TOP_K_CAST,
    build_feature_registry, Report, pf, write_csv, sha256_of, ENC
REPLACES candidate_pairs.py's dependency on franchise_mapping.py (not required by this script):
    FM.audit_collections / FM.norm / FM.load_text are NOT used. Only the pair logic that candidate_pairs.py
    documents is re-implemented (same ordering: collection, release_date, film_key; undated last; adjacent
    films; blocks for undated member / same-date ambiguity; n-1 pairs per collection).
    Collection tiers/flags/signals from FM are not reproduced (not needed for technical validation).
OPTIONAL: --candidate-pairs reports/candidate_pairs_full.csv (produced by YOUR run of candidate_pairs.py)
    -> that file's pairs are used as the candidate population and RE-VALIDATED here; differences vs the
    in-script generated population are reported.

Never written: data/curated/*, data/raw/*, data/analytical/pair_analysis.csv (hash-checked).

Project assumptions (explicit, NOT verified):
  A1 TMDB collection membership = franchise membership (no mainline / formal-order requirement).
  A2 box_office_detailed.opening_weekend_gross is an operationally comparable opening measure
     (no market/currency/window/theater metadata in source). This overrides build_ady_tables' default
     opening_status='pending' by explicit project decision.

RUN (project folder containing data/raw/*.csv, build_ady_tables.py, this file):
    python complete_dp_pipeline_v3_3.py
    python complete_dp_pipeline_v3_3.py --base-dir "D:/ADY" --candidate-pairs reports/candidate_pairs_full.csv
"""
import argparse
import re
import unicodedata
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import build_ady_tables as B
except ImportError as e:  # pragma: no cover
    sys.exit(f"[ERROR] build_ady_tables.py must sit next to this script: {e}")

CONFIG = {
    "undated_policy": "exclude",       # exclude: any pair in a collection that has an undated film is excluded
    "min_opening": 0.0,                # opening must be > this
    "exclude_inconsistent_opening": False,
    "low_opening_warn": 1000.0,
    "season_map": {12: "holiday", 11: "holiday", 6: "summer", 7: "summer", 8: "summer", 5: "early_summer",
                   3: "spring", 4: "spring", 1: "winter", 2: "winter", 9: "fall", 10: "fall"},
}
COMPARABILITY_STATUS = "ASSUMED_NOT_VERIFIED"
COMPARABILITY_NOTE = ("opening_weekend_gross adopted as operationally comparable (assumption A2). Source lacks "
                      "market scope, currency, opening-window length and theater count; NOT independently verified.")
log = logging.getLogger("ady")


# ------------------------------------------------------------------------------------------------
# TASK 3
# ------------------------------------------------------------------------------------------------
def prepare_films(film, as_of):
    f = film.copy()
    f["release_date"] = pd.to_datetime(f["release_date"], errors="coerce")
    f["franchise_id"] = np.where(f["tmdb_collection_id"].notna(),
                                 "TMDBC" + f["tmdb_collection_id"].astype("string"), None)
    f = f.sort_values(["franchise_id", "release_date", "film_key"], na_position="last", kind="mergesort")
    has_fr = f["franchise_id"].notna()
    f["chain_pos"] = pd.Series(np.nan, index=f.index)
    f.loc[has_fr, "chain_pos"] = f[has_fr].groupby("franchise_id").cumcount() + 1
    dated = f["release_date"].notna() & has_fr
    f["tied_date"] = False
    f.loc[dated, "tied_date"] = f[dated].duplicated(["franchise_id", "release_date"], keep=False)
    und = f[has_fr].groupby("franchise_id")["release_date"].apply(lambda s: int(s.isna().sum()))
    n = f[has_fr].groupby("franchise_id").size()
    f["collection_n_undated"] = f["franchise_id"].map(und)
    f["collection_n_films"] = f["franchise_id"].map(n)
    f["is_unreleased"] = f["release_date"] > as_of
    return f.set_index("film_key", drop=False)


def generate_candidates(films):
    """Adjacent films per TMDB collection in (release_date, film_key) order, undated last (as candidate_pairs.py)."""
    ch = films[films["franchise_id"].notna()].sort_values(["franchise_id", "chain_pos"], kind="mergesort")
    nxt = ch.groupby("franchise_id")["film_key"].shift(-1)
    c = pd.DataFrame({"film_key_prev": ch["film_key"].values, "film_key_curr": nxt.values}).dropna()
    return c.reset_index(drop=True)


def task3_pairs(film, as_of, ext_path=None):
    films = prepare_films(film, as_of)
    gen = generate_candidates(films)
    ext_diff = None
    cand = gen
    src = "generated_in_script_from_tmdb_collection_id (franchise_mapping.py not used)"
    if ext_path:
        e = B.read_csv_str(Path(ext_path))
        miss = [c for c in ("film_key_prev", "film_key_curr") if c not in e.columns]
        if miss:
            raise ValueError(f"{ext_path} missing columns {miss}")
        extra = [c for c in ("candidate_class", "block_reason", "tmdb_collection_id") if c in e.columns]
        cand = e[["film_key_prev", "film_key_curr"] + extra].rename(
            columns={"candidate_class": "cp_candidate_class", "block_reason": "cp_block_reason",
                     "tmdb_collection_id": "cp_tmdb_collection_id"}).reset_index(drop=True)
        gk = set(zip(gen.film_key_prev, gen.film_key_curr))
        ek = set(zip(cand.film_key_prev, cand.film_key_curr))
        ext_diff = {"in_file_not_generated": len(ek - gk), "generated_not_in_file": len(gk - ek)}
        src = f"file:{ext_path}"
    # Required for unique film lookups and reliable chronological chains.
    if not films.index.is_unique:
        raise ValueError("film_key is not unique in film table; cannot construct valid pairs")
    cand["duplicate_pair"] = cand.duplicated(["film_key_prev", "film_key_curr"], keep="first")

    for side in ("prev", "curr"):
        k = cand[f"film_key_{side}"]
        cand[f"known_{side}"] = k.isin(films.index)
        for c in ("tmdb_id", "title", "release_date", "franchise_id", "chain_pos", "tied_date", "is_unreleased"):
            cand[f"{c}_{side}"] = k.map(films[c])
    cand["franchise_id"] = cand["franchise_id_curr"].where(cand["franchise_id_curr"].notna(), cand["franchise_id_prev"])

    f = pd.DataFrame(index=cand.index)
    f["invalid_film_id"] = ~(cand["known_prev"] & cand["known_curr"]) | cand["tmdb_id_prev"].isna() | cand["tmdb_id_curr"].isna()
    f["self_pair"] = cand["film_key_prev"] == cand["film_key_curr"]
    f["duplicate_pair"] = cand["duplicate_pair"]
    f["collection_missing"] = cand["franchise_id_prev"].isna() | cand["franchise_id_curr"].isna()
    f["different_collection"] = ~f["collection_missing"] & (cand["franchise_id_prev"] != cand["franchise_id_curr"])
    f["missing_release_date"] = cand["release_date_prev"].isna() | cand["release_date_curr"].isna()
    f["tied_release_date"] = cand["tied_date_prev"].fillna(False).astype(bool) | cand["tied_date_curr"].fillna(False).astype(bool)
    f["not_chronological"] = ~f["missing_release_date"] & ~f["tied_release_date"] & (cand["release_date_curr"] < cand["release_date_prev"])
    gap = cand["chain_pos_curr"] - cand["chain_pos_prev"]
    f["not_adjacent"] = ~f["different_collection"] & ~f["collection_missing"] & (gap != 1)
    if CONFIG["undated_policy"] == "exclude":
        u = cand["film_key_curr"].map(films["collection_n_undated"]).fillna(0)
        f["collection_has_undated_film"] = u > 0
    else:
        f["collection_has_undated_film"] = False
    f["unreleased_film"] = cand["is_unreleased_prev"].fillna(False).astype(bool) | cand["is_unreleased_curr"].fillna(False).astype(bool)
    flag_cols = list(f.columns)
    cand = pd.concat([cand.drop(columns=["duplicate_pair"]), f], axis=1)
    cand["exclusion_reason"] = f.apply(lambda r: ";".join(c for c in flag_cols if bool(r[c])), axis=1)
    cand["technically_valid"] = cand["exclusion_reason"] == ""
    cand["gap_years"] = ((cand["release_date_curr"] - cand["release_date_prev"]).dt.days / 365.25).where(~f["missing_release_date"])
    cand["transition_id"] = np.where(cand["technically_valid"], cand["film_key_prev"] + "__" + cand["film_key_curr"], None)
    cand["candidate_source"] = src
    cand["franchise_definition"] = "TMDB_collection_membership (project assumption A1, not verified)"
    cand = cand.sort_values(["franchise_id", "chain_pos_prev", "film_key_prev"], na_position="last", kind="mergesort").reset_index(drop=True)

    st = {"candidate_source": src, "external_vs_generated_diff": ext_diff,
          "n_films": int(len(film)), "n_collections_ge2_films": int((films.groupby("franchise_id").size() >= 2).sum()),
          "n_candidate_pairs": int(len(cand)), "n_pairs_technically_valid": int(cand["technically_valid"].sum()),
          "n_pairs_excluded": int((~cand["technically_valid"]).sum()),
          "exclusion_flag_counts_(pairs_may_have_several)": {c: int(cand[c].sum()) for c in flag_cols},
          "undated_policy": CONFIG["undated_policy"]}
    log.info("Task3: candidates=%d valid=%d excluded=%d", len(cand), st["n_pairs_technically_valid"], st["n_pairs_excluded"])
    return cand, films, st


# ------------------------------------------------------------------------------------------------
# TASK 4
# ------------------------------------------------------------------------------------------------
def task4_openings(pairs, bod, raw):
    det = bod.drop_duplicates("film_key").set_index("film_key")
    rm = raw["movies_raw"].drop_duplicates("film_key").set_index("film_key")["imdb_id"]
    rd = raw["box_office_detailed"].drop_duplicates("film_key").set_index("film_key")["imdb_id"]
    p = pairs.copy()
    for s in ("prev", "curr"):
        k = p[f"film_key_{s}"]
        o = pd.to_numeric(k.map(det["opening_weekend_gross"]).astype("float64"), errors="coerce")
        p[f"open_{s}"] = o
        dom = pd.to_numeric(k.map(det["domestic_gross"]).astype("float64"), errors="coerce")
        p[f"opening_status_{s}"] = np.select([o.isna(), ~np.isfinite(o.fillna(0)), o <= CONFIG["min_opening"]],
                                             ["missing", "invalid_nonfinite", "nonpositive"], default="ok")
        mi, di = k.map(rm), k.map(rd)
        p[f"_flag_{s}"] = (o.notna() & dom.notna() & (o > dom)) | (mi.notna() & di.notna() & (mi != di))
        p[f"opening_low_warning_{s}"] = (o > CONFIG["min_opening"]) & (o < CONFIG["low_opening_warn"])
    p["opening_inconsistent"] = p["_flag_prev"] | p["_flag_curr"]
    p = p.drop(columns=["_flag_prev", "_flag_curr"])
    ok = (p["opening_status_prev"] == "ok") & (p["opening_status_curr"] == "ok")
    elig = p["technically_valid"] & ok
    if CONFIG["exclude_inconsistent_opening"]:
        elig &= ~p["opening_inconsistent"]
    p["y_eligible"] = elig

    def why(r):
        if not r["technically_valid"]:
            return "pair_not_technically_valid"
        rs = [f"opening_{r['opening_status_' + s]}_{lab}" for s, lab in (("prev", "N-1"), ("curr", "N"))
              if r["opening_status_" + s] != "ok"]
        if CONFIG["exclude_inconsistent_opening"] and r["opening_inconsistent"]:
            rs.append("opening_inconsistent")
        return ";".join(rs)
    p["y_ineligible_reason"] = p.apply(why, axis=1) if len(p) else pd.Series(dtype=str)
    with np.errstate(divide="ignore", invalid="ignore"):
        p["Y"] = np.log(p["open_curr"].where(elig)) - np.log(p["open_prev"].where(elig))
    p["comparability_status"] = COMPARABILITY_STATUS
    p["comparability_note"] = COMPARABILITY_NOTE
    v = p["technically_valid"]
    st = {"pairs_technically_valid": int(v.sum()), "pairs_Y_eligible": int(elig.sum()),
          "pairs_Y_ineligible_among_valid": int((v & ~elig).sum()),
          "valid_pairs_opening_status_prev": p.loc[v, "opening_status_prev"].value_counts().to_dict(),
          "valid_pairs_opening_status_curr": p.loc[v, "opening_status_curr"].value_counts().to_dict(),
          "valid_pairs_opening_inconsistent_flag": int((v & p["opening_inconsistent"]).sum()),
          "Y_eligible_with_inconsistent_flag": int((elig & p["opening_inconsistent"]).sum()),
          "opening_non_null_in_source": int(bod["opening_weekend_gross"].notna().sum()),
          "theater_count_non_null_in_source": int(raw["box_office_detailed"]["theater_count"].notna().sum()),
          "comparability_status": COMPARABILITY_STATUS, "comparability_note": COMPARABILITY_NOTE}
    log.info("Task4: valid=%d Y-eligible=%d", st["pairs_technically_valid"], st["pairs_Y_eligible"])
    return p, st


# ------------------------------------------------------------------------------------------------
# TASK 5
# ------------------------------------------------------------------------------------------------
def new_registry_rows():
    R = []
    def add(n, t, rq1, rq2, note):
        R.append(dict(feature_name=n, role="feature", source="complete_dp_pipeline", time_basis=t, rq1_allowed=rq1,
                      rq2_allowed=rq2, evidence_status="assumption", note=note))
    add("franchise_position_n", "pre_release_known", "yes", "yes",
        "Rank of N among TMDB-collection films by release date (NOT a formal installment number). Collection list is a 2026 snapshot.")
    add("release_month_n", "pre_release_known", "yes", "yes", "From release_date of N.")
    add("season_n", "pre_release_known", "yes", "yes", "Month->season map in CONFIG.")
    add("season_change", "pre_release_known", "yes", "yes", "season(N-1) != season(N).")
    add("release_year_n", "pre_release_known", "yes", "yes", "Era proxy; collinear with other time effects.")
    add("budget_log_ratio", "unknown", "pending", "yes", "ln(budget_N/budget_N-1); budget of N often reported post-release; ~90% null.")
    return pd.DataFrame(R)


def task5_features(pairs, film, credit, fcomp):
    k = B.TOP_K_CAST
    t = pairs[pairs["technically_valid"]].copy().reset_index(drop=True)
    fi = film.set_index("film_key")
    t["franchise_position_n"] = t["chain_pos_curr"].astype("Int64")
    cdir, ccast = B.director_sets(credit), B.top_cast(credit, k)
    comp = fcomp.groupby("film_key")["company_id"].agg(lambda x: frozenset(int(v) for v in x))

    def changed(m):
        a, b = t["film_key_prev"].map(m), t["film_key_curr"].map(m)
        return pd.array([pd.NA if (isinstance(x, float) or isinstance(y, float)) else bool(x != y)
                         for x, y in zip(a, b)], dtype="boolean")
    t["is_director_changed"] = changed(cdir)
    t["studio_changed"] = changed(comp)
    tp, tc = t["film_key_prev"].map(ccast["top"]), t["film_key_curr"].map(ccast["top"])
    np_, nc = t["film_key_prev"].map(ccast["n_cast"]), t["film_key_curr"].map(ccast["n_cast"])
    t["cast_retention_top5"] = [len(set(a) & set(b)) / k if isinstance(a, tuple) and isinstance(b, tuple)
                                and x >= k and y >= k else np.nan for a, b, x, y in zip(tp, tc, np_, nc)]
    bp = pd.to_numeric(t["film_key_prev"].map(fi["production_budget"]), errors="coerce").astype("float64")
    bc = pd.to_numeric(t["film_key_curr"].map(fi["production_budget"]), errors="coerce").astype("float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        t["budget_log_ratio"] = (np.log(bc) - np.log(bp)).where((bp > 0) & (bc > 0))
    t["release_month_prev"] = t["release_date_prev"].dt.month
    t["release_month_n"] = t["release_date_curr"].dt.month
    t["release_year_n"] = t["release_date_curr"].dt.year
    sm = CONFIG["season_map"]
    t["season_prev"], t["season_n"] = t["release_month_prev"].map(sm), t["release_month_n"].map(sm)
    t["season_change"] = pd.array([pd.NA if (pd.isna(a) or pd.isna(b)) else bool(a != b)
                                   for a, b in zip(t["season_prev"], t["season_n"])], dtype="boolean")
    with np.errstate(divide="ignore", invalid="ignore"):
        t["log_open_prev"] = np.log(t["open_prev"].where(t["opening_status_prev"] == "ok"))
    t["modeling_eligible"] = t["y_eligible"]
    # Prediction time: before release of N, after the release plan/cast has been announced.
    # Conservative core predictors: avoid snapshots/metadata whose historical availability is uncertain.
    # Availability of release dates for a planned release remains an explicit assumption.
    # Do not confuse the existence of a feature column with its approval for prediction.

    ids = ["transition_id", "franchise_id", "film_key_prev", "film_key_curr", "title_prev", "title_curr",
           "release_date_prev", "release_date_curr"]
    tgt = ["Y", "modeling_eligible", "y_ineligible_reason", "comparability_status"]
    feats = ["log_open_prev", "gap_years", "franchise_position_n", "is_director_changed", "cast_retention_top5",
             "studio_changed", "budget_log_ratio", "release_month_n", "season_n", "season_change", "release_year_n"]
    aud = ["open_prev", "open_curr", "opening_status_prev", "opening_status_curr", "opening_inconsistent",
           "opening_low_warning_prev", "opening_low_warning_curr", "release_month_prev", "season_prev",
           "candidate_source", "franchise_definition", "comparability_note"]
    t = t[ids + tgt + feats + aud]
    elig = t["modeling_eligible"]
    nn = lambda m: {c: (round(float(t.loc[m, c].notna().mean()), 4) if m.any() else None) for c in feats}
    st = {"feature_columns": feats, "feature_non_null_all_valid": nn(pd.Series(True, index=t.index)),
          "feature_non_null_Y_eligible": nn(elig),
          "not_used_as_features": {
              "open_curr / Y": "target side", "critic_score, audience_score": "2026 snapshot; post-release for N",
              "vote_count": "accumulates after release", "global/domestic/international gross": "lifetime totals",
              "collection_n_films": "uses later releases (future information)"}}
    log.info("Task5: transitions=%d model_rows=%d", len(t), int(elig.sum()))
    return t, st



# ------------------------------------------------------------------------------------------------
# DIAGNOSTIC EXTENSION — NOT NEW OPENING TARGETS, NOT RQ1 PREDICTORS
# ------------------------------------------------------------------------------------------------
DIAG_GROSS_SOURCES = {
    "global": ("box_office_raw", "global_gross"),
    "domestic": ("box_office_detailed", "domestic_gross"),
    "international": ("box_office_detailed", "international_gross"),
}


def _num_lookup(df, value_col):
    if df["film_key"].isna().any() or df["film_key"].duplicated().any():
        raise ValueError(f"Source of {value_col} has invalid/duplicate film_key")
    return pd.to_numeric(df.set_index("film_key")[value_col], errors="coerce")


def _id_set(value):
    if pd.isna(value) or str(value).strip() == "":
        return None  # missing != empty set
    return frozenset(s.strip() for s in str(value).split("|") if s.strip())


def _set_comparison(a, b):
    if a is None or b is None:
        return (np.nan, pd.NA, np.nan)
    union = a | b
    return (len(a & b) / len(union) if union else np.nan,
            a != b, len(a & b))


def task_diagnostic_extension(trans, raw):
    """Descriptive/diagnostic post-release snapshots. Keep away from RQ1 X columns."""
    d = trans.copy()
    for region, (source, col) in DIAG_GROSS_SOURCES.items():
        lookup = _num_lookup(raw[source], col)
        for side in ("prev", "curr"):
            d[f"lifetime_{region}_{side}"] = d[f"film_key_{side}"].map(lookup).astype(float)
        prev, curr = d[f"lifetime_{region}_prev"], d[f"lifetime_{region}_curr"]
        both = prev.gt(0) & curr.gt(0) & np.isfinite(prev) & np.isfinite(curr)
        with np.errstate(divide="ignore", invalid="ignore"):
            d[f"Y_lifetime_{region}"] = (np.log(curr.where(both)) - np.log(prev.where(both)))
        d[f"lifetime_{region}_pair_usable"] = both

    movies = raw["movies_raw"]
    for attr in ("production_budget", "vote_count", "release_month", "budget_missing_flag"):
        values = movies.set_index("film_key")[attr]
        for side in ("prev", "curr"):
            d[f"{attr}_{side}"] = d[f"film_key_{side}"].map(values).to_numpy()
    for name in ("genre_ids", "production_company_ids"):
        sets = movies.set_index("film_key")[name].map(_id_set)
        prev, curr = d["film_key_prev"].map(sets), d["film_key_curr"].map(sets)
        pairs = [_set_comparison(a, b) for a, b in zip(prev, curr)]
        stem = name.replace("_ids", "")
        d[f"{stem}_jaccard"] = [p[0] for p in pairs]
        d[f"{stem}_changed"] = pd.array([p[1] for p in pairs], dtype="boolean")
        d[f"{stem}_overlap_count"] = [p[2] for p in pairs]
        d[f"{stem}_n_prev"] = [len(v) if v is not None else np.nan for v in prev]
        d[f"{stem}_n_curr"] = [len(v) if v is not None else np.nan for v in curr]

    rt = raw["rt_scores"]
    if rt["film_key"].isna().any() or rt["film_key"].duplicated().any():
        raise ValueError("rt_scores has invalid/duplicate film_key")
    rtidx = rt.set_index("film_key")
    for score in ("critic_score", "audience_score"):
        lookup = pd.to_numeric(rtidx[score], errors="coerce")
        for side in ("prev", "curr"):
            d[f"{score}_{side}"] = d[f"film_key_{side}"].map(lookup).astype(float)
        d[f"delta_{score}_snapshot"] = d[f"{score}_curr"] - d[f"{score}_prev"]
    for side in ("prev", "curr"):
        d[f"rt_status_{side}"] = d[f"film_key_{side}"].map(rtidx["rt_status"])
    d["diagnostic_snapshot_status"] = "POST_RELEASE_SNAPSHOT_NOT_RQ1_PREDICTORS"
    d["lifetime_scope_note"] = "LIFETIME grosses, NOT opening-weekend revenue; global source differs from domestic/international source"

    outcome_cols = ["Y"] + [f"Y_lifetime_{x}" for x in DIAG_GROSS_SOURCES]
    coverage = []
    for c in outcome_cols:
        valid = d[c].notna() & np.isfinite(pd.to_numeric(d[c], errors="coerce"))
        with_primary = valid & d["Y"].notna()
        coverage.append({"outcome": c, "measurement": "opening_log_change_assumed_comparable" if c == "Y" else "lifetime_log_gross_change_NOT_opening",
                         "source": "box_office_detailed.opening_weekend_gross" if c == "Y" else ".".join(DIAG_GROSS_SOURCES[c.removeprefix("Y_lifetime_")]),
                         "valid_pairs": int(valid.sum()), "distinct_franchises": int(d.loc[valid, "franchise_id"].nunique()),
                         "pairs_also_have_opening_Y": int(with_primary.sum()),
                         "coverage_of_technical_pairs": round(float(valid.mean()), 6) if len(d) else 0})
    for c in ("critic_score_curr", "audience_score_curr", "genre_jaccard", "production_company_jaccard", "budget_log_ratio"):
        valid = d[c].notna()
        coverage.append({"outcome": c, "measurement": "diagnostic_attribute_NOT_opening_target", "source": "raw_snapshot",
                         "valid_pairs": int(valid.sum()), "distinct_franchises": int(d.loc[valid, "franchise_id"].nunique()),
                         "pairs_also_have_opening_Y": int((valid & d["Y"].notna()).sum()),
                         "coverage_of_technical_pairs": round(float(valid.mean()), 6) if len(d) else 0})
    return d, pd.DataFrame(coverage)



# ------------------------------------------------------------------------------------------------
# TITLE-BASED RELATIONSHIP SIGNALS (NOT VERIFIED FILM-TYPE CLASSIFICATIONS)
# ------------------------------------------------------------------------------------------------
# Important: The five supplied CSVs contain no authoritative sequel/prequel/spin-off/reboot/remake label.
# This deliberately favors an "unknown" label over fabricating a film relationship.
EXPLICIT_RELATION_PATTERN = re.compile(r"(?i)\b(spin[\s-]?off|prequel|reboot|remake|sequel)\b")
PART_NUMBER_PATTERN = re.compile(
    r"(?i)\b(?P<kind>part|chapter|volume|vol\.?|episode)\s*[#:]?\s*"
    r"(?P<number>\d{1,2}|X|IX|VIII|VII|VI|V|IV|III|II|I)\b"
)
TRAILING_NUMBER_PATTERN = re.compile(
    r"(?i)^(?P<root>.+?)\s+(?P<number>\d{1,2}|X|IX|VIII|VII|VI|V|IV|III|II)"
    r"(?:\s*[:\-–]\s*.+)?$"
)
ROMAN_NUMBERS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
                 "VII": 7, "VIII": 8, "IX": 9, "X": 10}


def _normalize_title(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text).casefold()
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _title_number_clue(title):
    """Return (marker_kind, number, normalized_root) or (None, None, '')."""
    if not isinstance(title, str):
        return None, None, ""
    m = PART_NUMBER_PATTERN.search(title)
    if m:
        val = m.group("number").upper()
        num = int(val) if val.isdigit() else ROMAN_NUMBERS.get(val)
        root = _normalize_title(title[:m.start()].rstrip(" :–-"))
        return m.group("kind").lower().strip('.'), num, root
    m = TRAILING_NUMBER_PATTERN.match(title)
    if m:
        val = m.group("number").upper()
        num = int(val) if val.isdigit() else ROMAN_NUMBERS.get(val)
        if num and 2 <= num <= 20:
            return "suffix", num, _normalize_title(m.group("root"))
    return None, None, ""


def _title_root_link(root, older_title):
    """Restricted title prefix match as a clue only, never proof of a direct sequel."""
    old = _normalize_title(older_title)
    if not root or not old or len(root) < 3:
        return False
    return old == root or old.startswith(root + " ") or root.startswith(old + " ")


def infer_relationship_labels(movies):
    """One candidate label per film using ONLY film titles + dated collection-order signals.

    No source in supplied raws establishes definitive relationship_type. Labels are explicitly
    'candidate' / 'unclassified' and should NOT be interpreted as verified narrative types.
    """
    required = ["film_key", "title", "tmdb_collection_id", "release_date_ref"]
    if movies["film_key"].isna().any() or movies["film_key"].duplicated().any():
        raise ValueError("movies_raw film_key must be unique and non-null for relationship annotation")
    x = movies[required].copy()
    x["release_date"] = pd.to_datetime(x["release_date_ref"], errors="coerce")
    x = x.sort_values(["tmdb_collection_id", "release_date", "film_key"], na_position="last", kind="mergesort")
    x["release_position_observed"] = x.groupby("tmdb_collection_id").cumcount() + 1
    x["same_date_ambiguity"] = x["release_date"].notna() & x.duplicated(
        ["tmdb_collection_id", "release_date"], keep=False)
    # Prior title context is restricted to earlier releases in the same collection, not all corpus titles.
    rows = []
    for _, group in x.groupby("tmdb_collection_id", sort=False, dropna=False):
        earlier_titles = []
        for film_key, title, dt, pos, ambiguous in zip(group["film_key"], group["title"],
                                                        group["release_date"], group["release_position_observed"],
                                                        group["same_date_ambiguity"]):
            t = "" if pd.isna(title) else str(title)
            explicit = EXPLICIT_RELATION_PATTERN.search(t)
            kind, number, root = _title_number_clue(t)
            if pd.isna(dt) or bool(ambiguous) or pd.isna(group["tmdb_collection_id"].iloc[0]):
                label, evidence, strength = "unclassified", "undated/tied/collection-missing; no reliable order", "none"
            elif explicit:
                hit = explicit.group(1).lower().replace(" ", "").replace("-", "")
                subtype = {"spinoff": "spinoff_candidate", "prequel": "prequel_candidate",
                           "reboot": "reboot_candidate", "remake": "remake_candidate",
                           "sequel": "sequel_candidate"}[hit]
                label, evidence, strength = subtype, "explicit_title_keyword:" + explicit.group(0), "explicit_title_clue"
            elif pos == 1:
                label, evidence, strength = "first_observed_in_collection", "first dated collection film, NOT proven original", "chronology_only"
            elif kind and number and number >= 2:
                # An 'episode' number may reflect STORY order rather than release order (Star Wars prequels).
                match = any(_title_root_link(root, older) for older in earlier_titles)
                if kind == "episode":
                    label = "numbered_installment_unknown_type"
                elif match:
                    label = "sequel_candidate"
                else:
                    label = "numbered_installment_unknown_type"
                evidence = f"title_number:{kind}:{number};earlier_title_root_match={match}"
                strength = "inferred_title_pattern" if match and kind != "episode" else "weak_title_clue"
            elif _normalize_title(t) and any(_normalize_title(t) == _normalize_title(old) for old in earlier_titles):
                label, evidence, strength = "repeated_title_unknown_type", "exact_normalized_title_reused; remake/reboot NOT established", "weak_title_clue"
            else:
                label, evidence, strength = "unclassified", "no reliable type indicator in supplied fields", "none"
            rows.append((film_key, label, evidence, strength, kind, number, root))
            if pd.notna(dt) and not bool(ambiguous):
                earlier_titles.append(t)
    annotations = pd.DataFrame(rows, columns=["film_key", "relationship_type_candidate",
        "relationship_evidence", "relationship_signal_strength", "title_number_kind",
        "title_number_value", "title_number_root"])
    annotations["relationship_verification_status"] = "UNVERIFIED_HEURISTIC"
    return movies[["film_key", "tmdb_collection_id", "title", "release_date_ref"]].merge(
        annotations, on="film_key", how="left", validate="one_to_one")


def extend_diagnostics_v33(diagnostic, raw):
    """Add relationship-title signals and a few useful unused raw attributes without altering RQ1 X/Y."""
    d = diagnostic.copy()
    rel = infer_relationship_labels(raw["movies_raw"])
    lookup = rel.set_index("film_key")
    for side in ("prev", "curr"):
        for col in ("relationship_type_candidate", "relationship_evidence",
                    "relationship_signal_strength", "relationship_verification_status"):
            d[f"{col}_{side}"] = d[f"film_key_{side}"].map(lookup[col])
    # Keep a familiar name for downstream diagnostics; values remain explicitly *candidate* labels.
    d["relationship_type_n"] = d["relationship_type_candidate_curr"]
    d["relationship_type_n_status"] = "UNVERIFIED_TITLE_HEURISTIC"
    types_with_clues = {"sequel_candidate", "prequel_candidate", "spinoff_candidate", "reboot_candidate", "remake_candidate"}
    cmp_eligible = d["relationship_type_candidate_prev"].isin(types_with_clues) & d["relationship_type_candidate_curr"].isin(types_with_clues)
    d["relationship_type_changed_candidate"] = (
        d["relationship_type_candidate_prev"].ne(d["relationship_type_candidate_curr"]).where(cmp_eligible).astype("boolean"))
    for source_col in ("director_ids", "lead_cast_ids_superset"):
        idx = raw["movies_raw"].set_index("film_key")[source_col].map(_id_set)
        a, b = d["film_key_prev"].map(idx), d["film_key_curr"].map(idx)
        vals = [_set_comparison(x, y) for x, y in zip(a, b)]
        stem = source_col.removesuffix("_ids")
        d[f"{stem}_jaccard_snapshot"] = [v[0] for v in vals]
        d[f"{stem}_changed_snapshot"] = pd.array([v[1] for v in vals], dtype="boolean")
        d[f"{stem}_overlap_count_snapshot"] = [v[2] for v in vals]
    # Data-quality attributes: retain missingness flags and source identity checks rather than
    # treating flags, retrieval metadata or IDs as predictive numeric features.
    b = raw["box_office_raw"].set_index("film_key")
    d["global_source_missing_flag_prev"] = d["film_key_prev"].map(b["missing_flag"])
    d["global_source_missing_flag_curr"] = d["film_key_curr"].map(b["missing_flag"])
    r = raw["rt_scores"].set_index("film_key")
    for side in ("prev", "curr"):
        d[f"rt_url_present_{side}"] = d[f"film_key_{side}"].map(r["rt_url"]).notna()
    raw_month = pd.to_numeric(raw["movies_raw"].set_index("film_key")["release_month"], errors="coerce")
    d["release_month_raw_matches_date_n"] = (
        d["film_key_curr"].map(raw_month).eq(pd.to_datetime(d["release_date_curr"]).dt.month)).astype("boolean")
    return d, rel


def summarize_relationships(diagnostic):
    r = diagnostic.groupby("relationship_type_n", dropna=False).agg(
        valid_transitions=("transition_id", "size"),
        pairs_with_opening_Y=("Y", "count"),
        distinct_franchises=("franchise_id", "nunique")
    ).reset_index().sort_values("valid_transitions", ascending=False)
    r["label_status"] = "UNVERIFIED_TITLE_HEURISTIC; NOT independently verified film type"
    return r


ATTRIBUTE_ROLES = {
    "movies_raw": {
        "film_key": "join_id", "tmdb_id": "audit_id", "imdb_id": "join_validation", "title": "pair_label",
        "release_date_ref": "core_pair_chronology", "tmdb_collection_id": "core_franchise_assumption",
        "director_ids": "diagnostic_director_ids_overlap", "lead_cast_ids_superset": "diagnostic_lead_cast_superset_overlap",
        "production_company_ids": "diagnostic_company_overlap", "genre_ids": "diagnostic_genre_overlap",
        "production_budget": "diagnostic_budget", "budget_missing_flag": "diagnostic_missingness",
        "release_month": "core_date_cross_check", "vote_count": "diagnostic_snapshot_only",
        "source": "provenance", "retrieval_date": "snapshot_time"},
    "credits_raw": {"film_key": "join_id", "person_id": "core_cast_director", "role": "core_cast_director",
                    "billing_order": "core_cast_order", "source": "provenance", "retrieval_date": "snapshot_time"},
    "box_office_raw": {"film_key": "join_id", "market_scope": "scope_audit_global_only",
                       "global_gross": "diagnostic_lifetime_global", "missing_flag": "diagnostic_source_missingness_flags",
                       "source": "provenance", "retrieval_date": "snapshot_time"},
    "box_office_detailed": {"film_key": "join_id", "imdb_id": "join_validation", "domestic_gross": "diagnostic_lifetime_domestic",
                            "international_gross": "diagnostic_lifetime_international",
                            "opening_weekend_gross": "PRIMARY_TARGET_SOURCE", "theater_count": "unusable_all_missing"},
    "rt_scores": {"film_key": "join_id", "critic_score": "diagnostic_snapshot_only",
                  "audience_score": "diagnostic_snapshot_only", "rt_url": "diagnostic_rt_url_presence",
                  "rt_status": "diagnostic_match_status", "source": "provenance", "retrieval_date": "snapshot_time"},
}


def audit_raw_attributes(raw):
    rows = []
    for table, df in raw.items():
        roles = ATTRIBUTE_ROLES.get(table, {})
        if set(df.columns) != set(roles):
            raise ValueError(f"Unaccounted source attributes in {table}: {sorted(set(df.columns)^set(roles))}")
        for name in df.columns:
            nonnull = int(df[name].notna().sum())
            rows.append({"source_table": table, "attribute": name, "non_null_rows": nonnull,
                         "source_rows": len(df), "non_null_rate": round(nonnull/len(df), 6) if len(df) else None,
                         "treatment": roles[name],
                         "rq1_predictor": "no" if roles[name] not in {"core_date_cross_check", "core_pair_chronology"} else "derived_only_with_timing_assumption",
                         "note": "Tracked/used selectively; not all attributes are valid predictors. 2026 snapshots may leak future observations."})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------
# validation + main
# ------------------------------------------------------------------------------------------------
def run_checks(rep, pairs, trans, model, films, feats, ext_diff):
    pf = B.pf
    rep.run("X01", "pairs", "pairs_audit", "Every candidate pair preserved in audit output", lambda: pf(
        len(pairs) >= len(trans), f"{len(pairs)} audit rows >= {len(trans)} transitions", ">="))
    rep.run("X02", "pairs", "transitions", "transition_id unique; no duplicate/self pairs", lambda: pf(
        trans["transition_id"].is_unique and not trans.duplicated(["film_key_prev", "film_key_curr"]).any()
        and (trans["film_key_prev"] != trans["film_key_curr"]).all(), "", ""))
    rep.run("X03", "pairs", "transitions", "Same collection, strictly increasing dates, gap_years > 0", lambda: pf(
        (trans["film_key_prev"].map(films["franchise_id"]) == trans["film_key_curr"].map(films["franchise_id"])).all()
        and (trans["release_date_curr"] > trans["release_date_prev"]).all() and (trans["gap_years"] > 0).all(), "", ""))
    rep.run("X04", "pairs", "transitions", "Adjacent in collection chain (position diff == 1)", lambda: pf(
        ((trans["film_key_curr"].map(films["chain_pos"]) - trans["film_key_prev"].map(films["chain_pos"])) == 1).all(), "", ""))

    def skipped():
        by = films[films["release_date"].notna() & films["franchise_id"].notna()].groupby("franchise_id")["release_date"].apply(list)
        bad = sum(1 for fr, a, b in zip(trans["franchise_id"], trans["release_date_prev"], trans["release_date_curr"])
                  for d in by[fr] if a < d < b)
        return pf(bad == 0, f"violations={bad}", "0", "No collection film lies strictly between N-1 and N")
    rep.run("X05", "pairs", "transitions", "No skipped intermediate release", skipped)
    rep.run("X06", "pairs", "transitions", "Undated-collection policy respected", lambda: pf(
        CONFIG["undated_policy"] != "exclude" or int((trans["franchise_id"].map(
            films.groupby("franchise_id")["collection_n_undated"].first()) > 0).sum()) == 0, "", ""))
    rep.run("X07", "target", "transitions_model", "Y finite; openings > 0; Y == ln(open_curr)-ln(open_prev) recomputed", lambda: pf(
        len(model) == 0 or (np.isfinite(model["Y"]).all() and (model["open_prev"] > 0).all() and (model["open_curr"] > 0).all()
                            and np.allclose(np.log(model["open_curr"]) - np.log(model["open_prev"]), model["Y"])),
        f"{len(model)} rows", ""))
    rep.run("X08", "target", "transitions", "Y missing for every non-eligible pair", lambda: pf(
        trans.loc[~trans["modeling_eligible"], "Y"].isna().all(), "", ""))
    rep.run("X09", "leakage", "features", "No leaky column in feature list", lambda: (lambda l: pf(
        not l, f"leaked={l}", "[]"))(sorted({"open_curr", "Y", "critic_score", "audience_score", "vote_count",
                                             "global_gross", "domestic_gross", "international_gross", "collection_n_films"} & set(feats))))
    rep.run("X10", "grouping", "transitions", "franchise_id present on all rows (grouped CV)", lambda: pf(
        trans["franchise_id"].notna().all(), "", ""))
    rep.run("X11", "pairs", "candidates", "External candidate file vs in-script generated set", lambda: (
        ("INFO", str(ext_diff), "", "differences are re-validated, not trusted") if ext_diff is not None
        else ("INFO", "no external file", "", "run candidate_pairs.py yourself and pass --candidate-pairs to compare")))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-dir", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--candidate-pairs", default=None)
    ap.add_argument("--undated-policy", choices=["exclude", "ignore"], default="exclude",
                    help="exclude (default) ensures no unplaced film can sit between a pair; ignore is a sensitivity scenario")
    ap.add_argument("--exclude-inconsistent-opening", action="store_true")
    ap.add_argument("--as-of-date", default=None)
    a = ap.parse_args(argv)
    CONFIG["undated_policy"], CONFIG["exclude_inconsistent_opening"] = a.undated_policy, a.exclude_inconsistent_opening

    base = Path(a.base_dir).resolve()
    if a.candidate_pairs:
        candidate_path = Path(a.candidate_pairs)
        if not candidate_path.is_absolute():
            candidate_path = base / candidate_path
        if not candidate_path.is_file():
            log.error("Candidate file missing: %s", candidate_path)
            return 1
    else:
        candidate_path = None
    raw_dir, ana, rdir, cur = base / "data/raw", base / "data/analytical", base / "reports", base / "data/curated"
    for d in (ana, rdir):
        d.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(rdir / "pipeline_run.log", mode="w")])
    miss = [fn for fn, _ in B.RAW_SPEC.values() if not (raw_dir / fn).exists()]
    if miss:
        log.error("missing raw files in %s: %s", raw_dir, miss)
        return 1
    h0 = {k: B.sha256_of(raw_dir / fn) for k, (fn, _) in B.RAW_SPEC.items()}
    cur_files = [cur / "franchise_film.csv", cur / "pair.csv", ana / "pair_analysis.csv"]
    c0 = [B.sha256_of(p) if p.exists() else None for p in cur_files]
    raw = {k: B.read_csv_str(raw_dir / fn) for k, (fn, _) in B.RAW_SPEC.items()}
    for k, (fn, cols) in B.RAW_SPEC.items():
        bad = [c for c in cols if c not in raw[k].columns]
        if bad:
            log.error("%s missing columns %s", fn, bad)
            return 1
    # Fail clearly on duplicate lookup keys; do not silently resolve them with keep='first'.
    for table in ("movies_raw", "box_office_detailed"):
        if raw[table]["film_key"].isna().any() or raw[table]["film_key"].duplicated().any():
            log.error("%s has null or duplicate film_key, cannot safely perform one-to-one lookups", table)
            return 1
    T, info = B.build_processed(raw)
    film, credit, bod, fcomp = T["film"], T["credit"], T["box_office_detail"], T["film_company"]
    as_of = pd.Timestamp(a.as_of_date) if a.as_of_date else pd.to_datetime(raw["movies_raw"]["retrieval_date"], errors="coerce").max()
    log.info("as_of=%s config=%s", as_of.date(), {k: v for k, v in CONFIG.items() if k != "season_map"})

    pairs, films, s3 = task3_pairs(film, as_of, candidate_path)
    pairs, s4 = task4_openings(pairs, bod, raw)
    trans, s5 = task5_features(pairs, film, credit, fcomp)
    model = trans[trans["modeling_eligible"]].reset_index(drop=True)

    B.write_csv(pairs, rdir / "pairs_audit.csv")
    B.write_csv(trans, ana / "transitions.csv")
    B.write_csv(model, ana / "transitions_model.csv")
    diagnostic, coverage = task_diagnostic_extension(trans, raw)
    diagnostic, relationship_films = extend_diagnostics_v33(diagnostic, raw)
    relationship_summary = summarize_relationships(diagnostic)
    B.write_csv(relationship_films, rdir / "film_relationship_labels.csv")
    B.write_csv(relationship_summary, rdir / "relationship_type_summary.csv")
    diagnostic_features = {
        "relationship_type_n": "RQ2_EXPLORATORY_TITLE_HEURISTIC",
        "director_jaccard_snapshot": "RQ2_DIAGNOSTIC_SNAPSHOT",
        "lead_cast_ids_superset_jaccard_snapshot": "RQ2_DIAGNOSTIC_SNAPSHOT",
        "genre_jaccard": "RQ2_DIAGNOSTIC_SNAPSHOT",
        "production_company_jaccard": "RQ2_DIAGNOSTIC_SNAPSHOT",
        "budget_log_ratio": "RQ2_DIAGNOSTIC_TIMING_UNVERIFIED",
        "cast_retention_top5": "RQ2_DIAGNOSTIC_TIMING_UNVERIFIED",
        "is_director_changed": "RQ2_DIAGNOSTIC_TIMING_UNVERIFIED",
        "studio_changed": "RQ2_DIAGNOSTIC_TIMING_UNVERIFIED",
        "critic_score_curr": "RQ2_POST_RELEASE",
        "audience_score_curr": "RQ2_POST_RELEASE",
        "vote_count_curr": "RQ2_POST_RELEASE",
        "Y_lifetime_global": "SECONDARY_LIFETIME_OUTCOME",
        "Y_lifetime_domestic": "SECONDARY_LIFETIME_OUTCOME",
        "Y_lifetime_international": "SECONDARY_LIFETIME_OUTCOME",
    }
    coverage_rows = []
    for c, role in diagnostic_features.items():
        if c not in diagnostic:
            raise ValueError(f"Expected diagnostic column not found: {c}")
        valid = diagnostic[c].notna()
        subset = diagnostic["Y"].notna()
        coverage_rows.append({"attribute": c, "analytical_role": role,
            "nonmissing_pairs_all": int(valid.sum()), "nonmissing_pairs_with_Y": int((valid & subset).sum()),
            "total_valid_pairs": len(diagnostic), "pairs_with_opening_Y": int(subset.sum()),
            "rq1_baseline_predictor": "no"})
    feature_coverage = pd.DataFrame(coverage_rows)
    B.write_csv(feature_coverage, rdir / "diagnostic_feature_coverage.csv")
    B.write_csv(diagnostic, ana / "transitions_diagnostic.csv")
    three_gross_outcomes = [f"Y_lifetime_{g}" for g in DIAG_GROSS_SOURCES]
    lifetime_complete = diagnostic.loc[diagnostic[three_gross_outcomes].notna().all(axis=1)].copy()
    B.write_csv(lifetime_complete, ana / "diagnostic_complete_lifetime_3scopes.csv")
    B.write_csv(coverage, rdir / "diagnostic_coverage.csv")
    attribute_inventory = audit_raw_attributes(raw)
    B.write_csv(attribute_inventory, rdir / "raw_attribute_inventory.csv")
    # Only these predictors are tentatively approved for RQ1 at the defined prediction time.
    rq1_features = ["log_open_prev", "gap_years", "franchise_position_n", "release_month_n", "release_year_n"]
    rq1_ids = ["transition_id", "franchise_id", "film_key_prev", "film_key_curr"]
    B.write_csv(model[rq1_ids + rq1_features + ["Y"]], ana / "transitions_model_rq1.csv")
    # OPTIONAL experiment only: compare the baseline with an UNVERIFIED title-derived category.
    # Rare categories cannot support individual effects; the official RQ1 baseline stays unchanged.
    relationship_model_exploratory = model[rq1_ids + rq1_features + ["Y"]].merge(
        diagnostic[["transition_id", "relationship_type_n", "relationship_type_n_status",
                    "relationship_signal_strength_curr"]],
        on="transition_id", how="left", validate="one_to_one")
    B.write_csv(relationship_model_exploratory, ana / "transitions_model_rq1_relationship_EXPLORATORY.csv")
    policy = pd.DataFrame([
        ("log_open_prev", "RQ1_CORE", "Previous opening is observed before the planned release of N"),
        ("gap_years", "RQ1_CORE", "Assume scheduled release date of N known at prediction time"),
        ("franchise_position_n", "RQ1_CORE", "Past release count and upcoming position assumed known; historical collection snapshot needs caution"),
        ("release_month_n", "RQ1_CORE", "Assume announced release month known at prediction time"),
        ("release_year_n", "RQ1_CORE", "Assume announced release year known at prediction time"),
        ("season_n", "RQ1_REDUNDANT", "Derived deterministically from release_month_n"),
        ("season_change", "RQ1_REDUNDANT", "Related to release_month_n; prefer simpler temporal feature"),
        ("is_director_changed", "RQ2_ONLY_PENDING", "2026 credit snapshot; verify pre-release availability before RQ1"),
        ("cast_retention_top5", "RQ2_ONLY_PENDING", "Final billing order may be known only after release"),
        ("studio_changed", "RQ2_ONLY_PENDING", "Current company snapshot may not equal pre-release announced status"),
        ("budget_log_ratio", "RQ2_ONLY_PENDING", "Budget of N historically unavailable/mostly missing"),
    ], columns=["feature_name", "usage", "reason"])
    B.write_csv(policy, rdir / "rq1_feature_policy.csv")
    feature_missing = pd.DataFrame({
        "feature_name": rq1_features,
        "missing_count": [int(model[f].isna().sum()) for f in rq1_features],
        "missing_rate": [float(model[f].isna().mean()) if len(model) else None for f in rq1_features],
    })
    B.write_csv(feature_missing, rdir / "rq1_feature_missingness.csv")
    reg = pd.concat([B.build_feature_registry(), new_registry_rows()], ignore_index=True)
    # Align registry with the actual approved RQ1 modeling allowlist.
    # Earlier registry was inconsistent: some time-uncertain features remained "yes"
    # while log_open_prev was marked "pending" even though present in the RQ1 export.
    reg["rq1_allowed"] = reg["feature_name"].isin(rq1_features).map({True: "yes", False: "no"})
    reg.loc[reg["feature_name"].eq("Y"), "rq1_allowed"] = "target"
    reg.loc[reg["feature_name"].eq("open_prev") | reg["feature_name"].eq("open_curr"), "rq1_allowed"] = "target_input"
    reg.loc[reg["feature_name"].isin(rq1_features), "evidence_status"] = "prediction_time_assumption"
    B.write_csv(reg, rdir / "feature_registry_transitions.csv")

    rep = B.Report()
    run_checks(rep, pairs, trans, model, films, s5["feature_columns"], s3["external_vs_generated_diff"])
    h1 = {k: B.sha256_of(raw_dir / fn) for k, (fn, _) in B.RAW_SPEC.items()}
    c1 = [B.sha256_of(p) if p.exists() else None for p in cur_files]
    rep.run("X12", "raw", "data/raw", "Raw files byte-identical", lambda: B.pf(h0 == h1, "", ""))
    rep.run("X13", "raw", "curated/pair_analysis", "franchise_film.csv, pair.csv, pair_analysis.csv untouched", lambda: B.pf(c0 == c1, "", ""))
    rep.run("X14", "modeling", "transitions_model_rq1", "RQ1 feature allowlist excludes outcomes and uncertain-timing predictors", lambda: B.pf(
        not (set(rq1_features) & {"open_curr", "Y", "budget_log_ratio", "cast_retention_top5", "studio_changed", "is_director_changed", "critic_score", "audience_score"}),
        ",".join(rq1_features), "approved core predictors"))
    rep.run("X15", "modeling", "transitions_model_rq1", "Modeling subset equals valid-Y set", lambda: B.pf(
        len(model) == int(trans["modeling_eligible"].sum()), str(len(model)), str(int(trans["modeling_eligible"].sum()))))
    rep.run("X16", "modeling", "feature_registry_transitions", "RQ1 registry allowlist agrees with RQ1 export", lambda: B.pf(
        set(reg.loc[reg["rq1_allowed"].eq("yes"), "feature_name"]) == set(rq1_features),
        ",".join(reg.loc[reg["rq1_allowed"].eq("yes"), "feature_name"]), ",".join(rq1_features)))
    # Diagnostic additions must not modify fixed primary Y or RQ1 model rows.
    rep.run("X17", "diagnostic", "transitions_diagnostic", "Diagnostic one-to-one with core valid transitions", lambda: B.pf(
        len(diagnostic) == len(trans) and diagnostic["transition_id"].equals(trans["transition_id"]),
        str(len(diagnostic)), str(len(trans))))
    rep.run("X18", "diagnostic", "transitions_diagnostic", "Primary Y unchanged by extra outcomes", lambda: B.pf(
        np.allclose(diagnostic["Y"], trans["Y"], equal_nan=True), "Y preserved", "identical"))
    rep.run("X19", "diagnostic", "transitions_diagnostic", "Lifetime target derivation independently checked", lambda: B.pf(
        all(np.allclose(diagnostic[f"Y_lifetime_{g}"],
            np.log(diagnostic[f"lifetime_{g}_curr"].where(diagnostic[f"lifetime_{g}_pair_usable"])) -
            np.log(diagnostic[f"lifetime_{g}_prev"].where(diagnostic[f"lifetime_{g}_pair_usable"])),
            equal_nan=True) for g in DIAG_GROSS_SOURCES), "3 log differences", "3"))
    rep.run("X20", "leakage", "transitions_model_rq1", "No diagnostic/post-release outcomes in RQ1 export", lambda: B.pf(
        not set(model[rq1_ids + rq1_features + ["Y"]].columns).intersection(
            set(diagnostic.columns) - set(trans.columns)), "RQ1 export unchanged", "no new diagnostic columns"))
    rep.run("X21", "inventory", "raw_attribute_inventory", "Every raw attribute accounted for", lambda: B.pf(
        len(attribute_inventory) == sum(len(df.columns) for df in raw.values()),
        str(len(attribute_inventory)), str(sum(len(df.columns) for df in raw.values()))))
    rep.run("X22", "diagnostic", "diagnostic_complete_lifetime_3scopes", "Three gross scopes complete on common pairs", lambda: B.pf(
        lifetime_complete[three_gross_outcomes].notna().all(axis=1).all(),
        str(len(lifetime_complete)), "no missing lifetime changes"))
    rep.run("X23", "relationship", "film_relationship_labels", "Every source film annotated once; no duplicates", lambda: B.pf(
        len(relationship_films) == len(raw["movies_raw"]) and relationship_films["film_key"].is_unique,
        str(len(relationship_films)), str(len(raw["movies_raw"]))))
    rep.run("X24", "relationship", "transitions_diagnostic", "Candidate relation labels map to current film", lambda: B.pf(
        diagnostic["relationship_type_n"].equals(diagnostic["film_key_curr"].map(
            relationship_films.set_index("film_key")["relationship_type_candidate"])),
        "film_key_curr join", "exact"))
    rep.run("X25", "leakage", "transitions_model_rq1", "Relation and post-release features excluded from RQ1 baseline", lambda: B.pf(
        not any("relationship" in c or "lifetime" in c or "snapshot" in c for c in model[rq1_ids + rq1_features + ["Y"]].columns),
        "none", "no new predictors"))
    rep.run("X26", "diagnostic", "transitions_diagnostic", "No diagnostic expansion or primary-Y modification", lambda: B.pf(
        len(diagnostic) == len(trans) and np.allclose(diagnostic["Y"], trans["Y"], equal_nan=True),
        str(len(diagnostic)), str(len(trans))))
    rep.run("X27", "diagnostic", "diagnostic_feature_coverage", "All diagnostic feature coverage counted against real paired rows", lambda: B.pf(
        len(feature_coverage) == len(diagnostic_features) and
        (feature_coverage["nonmissing_pairs_with_Y"] <= feature_coverage["nonmissing_pairs_all"]).all() and
        (feature_coverage["nonmissing_pairs_with_Y"] <= len(model)).all(),
        str(len(feature_coverage)), str(len(diagnostic_features))))
    rep.run("X28", "modeling", "transitions_model_rq1_relationship_EXPLORATORY", "Optional label experiment keeps same Y and number of RQ1 rows", lambda: B.pf(
        len(relationship_model_exploratory) == len(model) and
        relationship_model_exploratory["Y"].equals(model["Y"]) and
        relationship_model_exploratory["relationship_type_n_status"].eq("UNVERIFIED_TITLE_HEURISTIC").all(),
        str(len(relationship_model_exploratory)), str(len(model))))
    B.write_csv(rep.frame(), rdir / "pipeline_validation.csv")

    nfr = int(model["franchise_id"].nunique()) if len(model) else 0
    summary = {"assumptions": ["A1 TMDB collection = franchise (unverified)", "A2 " + COMPARABILITY_NOTE],
               "task3": s3, "task4": s4, "task5": s5,
               "final": {"transitions_total": int(len(trans)), "transitions_model_Y_available": int(len(model)),
                         "franchises_in_model_subset": nfr,
                         "Y_summary": model["Y"].describe().round(4).to_dict() if len(model) else {}},
               "diagnostic": {"outcome_coverage": coverage.to_dict(orient="records"),
                              "three_lifetime_scopes_complete_pairs": len(lifetime_complete),
                              "three_lifetime_scopes_plus_opening_Y_complete_pairs": int(lifetime_complete["Y"].notna().sum()),
                              "raw_attribute_count": len(attribute_inventory),
                              "raw_attribute_usage_note": "All accounted for, not all valid as RQ1 predictors"},
               "relationship_annotation": {
                   "source": "movie title + TMDB collection chronological context only",
                   "status": "UNVERIFIED_HEURISTIC, NOT film type ground truth",
                   "film_label_counts": relationship_films["relationship_type_candidate"].value_counts(dropna=False).to_dict(),
                   "transition_summary": relationship_summary.to_dict(orient="records")},
               "all_checks_passed": not rep.has_failures(),
               "feature_registry_rq1_allowed_yes": reg.loc[reg["rq1_allowed"] == "yes", "feature_name"].tolist(),
               "limitations": [
                   "Franchise = TMDB collection; may include non-theatrical items, unrelated items, re-releases.",
                   "Opening market/currency/window/theater metadata absent; comparability assumed, not verified.",
                   "opening_weekend_gross is sparse and popularity-selected; Y-eligible sample is a small, biased subset.",
                   "Nominal (not inflation-adjusted) openings across decades; early-era openings may reflect first-run limits.",
                   "Missing-opening films are never bridged; adjacent pairs touching them have missing Y.",
                   "Pairs in collections with undated films excluded by default.",
                   "Rows clustered by franchise_id: use grouped CV / cluster-robust inference.",
                   "Lifetime global, domestic, and international gross changes are secondary diagnostic outcomes only, NOT opening changes.",
                   "The lifetime gross sources differ (TMDB global vs detailed gross), and represent snapshots, not consistent opening windows.",
                   "RT scores and vote_count are 2026 snapshots; current-film scores are prohibited as RQ1 predictors.",
                   "franchise_mapping.py not used: candidate_pairs.py collection tiers/flags/signals not reproduced.",
                   "Relationship types are TITLE-HEURISTIC CANDIDATES only. Sequel/prequel/spin-off/reboot/remake are not established by five raw datasets; majority legitimately unclassified."]}
    (rdir / "pipeline_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(rep.frame()[["check_id", "status", "description", "observed"]].to_string(index=False))
    log.info("DONE valid=%d model=%d franchises=%d all_checks=%s", len(trans), len(model), nfr, summary["all_checks_passed"])
    return 1 if rep.has_failures() else 0


if __name__ == "__main__":
    sys.exit(main())
