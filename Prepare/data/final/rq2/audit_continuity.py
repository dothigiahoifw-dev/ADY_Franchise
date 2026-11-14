"""
AUDIT: Production Continuity (cast retention, director change) cho gói RQ2.

KHÔNG sửa file gốc. Chỉ đọc Master + credits, ghi kết quả vào --out.
KHÔNG chạy mô hình hồi quy (chỉ đếm, mô tả, tính lại biến để đối chiếu).

Chạy:
  python audit_continuity.py \
      --master analysis_master_transitions.csv \
      --credits analysis_credits_detail.csv \
      [--pkg thu_muc_giai_nen/rq2]     # tuỳ chọn: đối chiếu ID mẫu với gói RQ2
      [--out audit_output]

Python >= 3.10; pandas, numpy.

Lưu ý phạm vi: tính lại từ credits chỉ chứng minh TÍNH NHẤT QUÁN NỘI BỘ giữa
Master và credits_detail. Không xác minh credits TMDB đầy đủ/đúng ngoài thực tế.
"""
import argparse, hashlib, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
K = 5                       # top-k diễn viên
OPEN_MIN = 1_000_000        # ngưỡng opening của mẫu RQ2 (analysis_config.json)

ap = argparse.ArgumentParser()
ap.add_argument("--master", required=True)
ap.add_argument("--credits", required=True)
ap.add_argument("--pkg", default=None)
ap.add_argument("--out", default="audit_output")
a = ap.parse_args()
OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
log = {}

def save(df, name, index=False):
    df.to_csv(OUT / name, index=index, encoding="utf-8-sig")

# ------------------------------------------------------------------ load
M = pd.read_csv(a.master, low_memory=False)
C = pd.read_csv(a.credits, low_memory=False)
log["master_sha256"] = hashlib.sha256(open(a.master, "rb").read()).hexdigest()
log["master_shape"] = list(M.shape)
log["credits_shape"] = list(C.shape)

# ---------------------------------------------------- 1. integrity: Master
integ = {
    "transition_id_duplicates": int(M.transition_id.duplicated().sum()),
    "pair(film_prev,film_curr)_duplicates": int(M.duplicated(["film_key_prev", "film_key_curr"]).sum()),
    "film_key_curr_appearing_in_>1_transition": int(M.film_key_curr.duplicated().sum()),
}
# ---------------------------------------------------- 2. integrity: credits
cast = C[C.role == "cast"]
dire = C[C.role == "director"]
integ.update({
    "credits_rows": len(C),
    "credits_roles": C.role.value_counts().to_dict(),
    "credits_dup_(film,person,role)": int(C.duplicated(["film_key", "person_id", "role"]).sum()),
    "credits_dup_groups_all_cast_with_different_billing_order": True,
    "cast_billing_order_null": int(cast.billing_order.isna().sum()),
    "director_rows_with_billing_order": int(dire.billing_order.notna().sum()),
    "cast_dup_billing_order_within_film": int(cast.duplicated(["film_key", "billing_order"]).sum()),
    "films_with_cast_rows": int(cast.film_key.nunique()),
    "films_with_<5_cast_rows": int((cast.groupby("film_key").size() < K).sum()),
    "films_with_director_rows": int(dire.film_key.nunique()),
    "films_with_>1_director": int((dire.groupby("film_key").size() > 1).sum()),
    "credits_sources": C.source.value_counts().to_dict(),
    "credits_retrieval_dates": C.retrieval_date.value_counts().to_dict(),
})
dd = cast[cast.duplicated(["film_key", "person_id"], keep=False)]
integ["credits_dup_groups_all_cast_with_different_billing_order"] = bool(
    (dd.groupby(["film_key", "person_id"]).billing_order.nunique() > 1).all()) if len(dd) else None
log["integrity"] = integ

# ---------------------------------------------------- 3. cast retention recompute
# top-5 theo billing_order tăng dần; mỗi person_id chỉ giữ billing_order nhỏ nhất
cs = cast.sort_values(["film_key", "billing_order", "person_id"])
cs_dedup = cs.drop_duplicates(["film_key", "person_id"], keep="first")
top5 = cs_dedup.groupby("film_key").head(K).groupby("film_key").person_id.apply(frozenset)
n_cast = cs_dedup.groupby("film_key").size()

# kiểm tra: top-5 có bị ảnh hưởng bởi trùng person / đồng hạng billing ở ranh giới?
raw5 = cs.groupby("film_key").head(K)
dup_in_top5 = int(raw5.duplicated(["film_key", "person_id"]).groupby(raw5.film_key).any().sum())
tie_rows = cs_dedup.copy()
tie_rows["rank"] = tie_rows.groupby("film_key").cumcount()
b5 = tie_rows[tie_rows["rank"].isin([K - 1, K])].pivot(index="film_key", columns="rank", values="billing_order")
tie_at_boundary = int((b5[K - 1] == b5[K]).sum()) if K in b5.columns else 0
integ["films_where_top5_rows_contain_repeated_person"] = dup_in_top5
integ["films_with_billing_tie_exactly_at_5th/6th_boundary"] = tie_at_boundary

X = M[["transition_id", "franchise_id", "film_key_prev", "film_key_curr", "title_prev", "title_curr",
       "cast_retention_top5", "is_director_changed", "director_jaccard_snapshot",
       "director_overlap_count_snapshot", "Y"]].copy()
X["s_prev"] = X.film_key_prev.map(top5); X["s_curr"] = X.film_key_curr.map(top5)
X["ncast_prev"] = X.film_key_prev.map(n_cast); X["ncast_curr"] = X.film_key_curr.map(n_cast)
ok = (X.ncast_prev >= K) & (X.ncast_curr >= K)
X["my_cast_ret"] = np.nan
X.loc[ok, "my_cast_ret"] = [len(p & c) / K for p, c in zip(X.s_prev[ok], X.s_curr[ok])]
mm = X.cast_retention_top5.notna()
cast_cmp = {
    "formula_verified": "|top5_prev ∩ top5_curr| / 5, chỉ tính khi CẢ HAI phim có >=5 diễn viên (person_id), top5 theo billing_order tăng dần",
    "master_nonmissing": int(mm.sum()),
    "my_nonmissing": int(X.my_cast_ret.notna().sum()),
    "availability_agree": bool((mm == X.my_cast_ret.notna()).all()),
    "value_match_on_master_nonmissing": float((abs(X.cast_retention_top5 - X.my_cast_ret)[mm] < 1e-9).mean()),
    "master_missing_because_<5_cast_either_side": int((~mm & (X.ncast_prev.notna() & X.ncast_curr.notna() & ~ok)).sum()),
    "master_missing_because_no_cast_rows_at_all": int((~mm & (X.ncast_prev.isna() | X.ncast_curr.isna())).sum()),
    "retention_zero_total": int((X.cast_retention_top5 == 0).sum()),
    "retention_zero_with_missing_cast_sets(should_be_0)": int(((X.cast_retention_top5 == 0) & ~ok).sum()),
}
# đối chiếu thứ tự với danh sách top trong movies_raw (superset, tối đa 20 người)
sup = pd.read_csv(a.master, usecols=["film_key_prev", "raw_movies__lead_cast_ids_superset_prev"], low_memory=False).dropna()
sup["t5_sup"] = sup.raw_movies__lead_cast_ids_superset_prev.map(lambda s: frozenset(int(v) for v in s.split("|")[:K]))
sup["t5_cr"] = sup.film_key_prev.map(top5)
sup = sup.dropna(subset=["t5_cr"]); sup = sup[sup.t5_sup.map(len) >= K]
cast_cmp["top5_from_movies_raw_superset_equals_top5_from_credits"] = float((sup.t5_sup == sup.t5_cr).mean())
log["cast_retention_recompute"] = cast_cmp

# ---------------------------------------------------- 4. director change recompute
D = dire.groupby("film_key").person_id.apply(frozenset)
X["d_prev"] = X.film_key_prev.map(D); X["d_curr"] = X.film_key_curr.map(D)
okd = X.d_prev.notna() & X.d_curr.notna()
X["my_dir_changed"] = np.nan
X.loc[okd, "my_dir_changed"] = [float(p != c) for p, c in zip(X.d_prev[okd], X.d_curr[okd])]
X["my_dir_overlap"] = np.nan
X.loc[okd, "my_dir_overlap"] = [len(p & c) for p, c in zip(X.d_prev[okd], X.d_curr[okd])]
X["my_dir_jaccard"] = np.nan
X.loc[okd, "my_dir_jaccard"] = [len(p & c) / len(p | c) for p, c in zip(X.d_prev[okd], X.d_curr[okd])]
X["dir_chg"] = X.is_director_changed.map({True: 1.0, False: 0.0, "True": 1.0, "False": 0.0})
mmd = X.dir_chg.notna()
dir_cmp = {
    "formula_verified": "is_director_changed = (tập person_id đạo diễn N-1) != (tập N); thiếu nếu một phim không có dòng director",
    "master_nonmissing": int(mmd.sum()), "my_nonmissing": int(okd.sum()),
    "availability_agree": bool((mmd == okd).all()),
    "changed_match": float((X.dir_chg[mmd] == X.my_dir_changed[mmd]).mean()),
    "jaccard_match": float((abs(X.director_jaccard_snapshot - X.my_dir_jaccard)[mmd] < 1e-9).mean()),
    "overlap_count_match": float((X.director_overlap_count_snapshot == X.my_dir_overlap)[mmd].mean()),
    "missing_director_rows_prev": int(X.d_prev.isna().sum()),
    "missing_director_rows_curr": int(X.d_curr.isna().sum()),
    "missing_director_not_converted_to_FALSE": bool(X.dir_chg[~okd].isna().all()),
    "columns_is_director_changed_equals_director_changed_snapshot":
        bool((M.is_director_changed.astype(str) == M.director_changed_snapshot.astype(str)).all()),
    "partial_overlap_pairs_master(0<jaccard<1)": int(((X.my_dir_jaccard > 0) & (X.my_dir_jaccard < 1)).sum()),
    "partial_overlap_pairs_flagged_changed": int((X.dir_chg[(X.my_dir_jaccard > 0) & (X.my_dir_jaccard < 1)] == 1).sum()),
}
log["director_recompute"] = dir_cmp

# ---------------------------------------------------- 5. aggregate columns vs credits file
cnt_all = C.groupby("film_key").size()
agg = {}
for s in ("prev", "curr"):
    r = M[f"credits__rows_{s}"]; fk = M[f"film_key_{s}"]
    have = r.notna()
    agg[f"credits__rows_{s}_equals_count_in_credits_file"] = float((r[have] == fk[have].map(cnt_all)[have]).mean())
log["aggregate_consistency"] = agg

# ---------------------------------------------------- 6. samples (quy tắc lấy từ RQ2_Duyen_buoc3/common.py)
for c_ in ["Y", "open_prev", "open_curr", "audience_score_prev", "critic_score_prev", "gap_years",
           "franchise_position_n", "release_year_n", "budget_log_ratio", "cast_retention_top5"]:
    M[c_] = pd.to_numeric(M[c_], errors="coerce")
M["A10"] = M.audience_score_prev / 10
M["dir_chg"] = X.dir_chg.values
M["part"] = np.select([M.franchise_position_n.eq(2), M.franchise_position_n.eq(3)], ["2", "3"], default="4+")
valid = (np.isfinite(M.Y) & M.modeling_eligible.astype(str).str.lower().eq("true")
         & M.franchise_id.notna() & M.transition_id.notna())
ctx = ["gap_years", "franchise_position_n", "release_year_n"]
base = M.loc[valid & M.open_prev.ge(OPEN_MIN) & M.open_curr.ge(OPEN_MIN)].copy()
principal = base.dropna(subset=["A10"] + ctx).copy()
budget = principal.dropna(subset=["budget_log_ratio"]).copy()
wide = M.loc[valid & M.open_prev.gt(0) & M.open_curr.gt(0)].dropna(subset=["A10"] + ctx)
wide = wide.loc[~wide.opening_inconsistent].copy()
samples = {"Master (tất cả transition)": M, "Master có Y": M[np.isfinite(M.Y)], "base (open>=1M, có Y)": base,
           "principal (base + điểm KG + bối cảnh)": principal, "budget (principal + ngân sách)": budget,
           "wide (open>0, loại 4 cờ; nhánh độ vững)": wide}
if a.pkg:
    pk = Path(a.pkg) / "RQ2_Duyen_buoc6" / "results"
    chk = {}
    for nm, df in {"M0": principal, "M2": budget}.items():
        f = pk / f"{nm}_sample.csv"
        if f.exists():
            ids = set(pd.read_csv(f).transition_id)
            chk[f"{nm}_sample_ids_equal_pkg"] = ids == set(df.transition_id)
    log["package_sample_id_check"] = chk

rows = []
for nm, d in samples.items():
    n = len(d); c = d.cast_retention_top5.notna(); r = d.dir_chg.notna(); b = d.budget_log_ratio.notna()
    au = d.audience_score_prev.notna()
    row = {"sample": nm, "n": n, "franchises": d.franchise_id.nunique()}
    for lab, m in [("Y&cast", c), ("Y&director", r), ("Y&cast&director", c & r),
                   ("cast&director&audience_prev", c & r & au),
                   ("cast&director&audience_prev&budget", c & r & au & b)]:
        row[lab + "_n"] = int(m.sum()); row[lab + "_franchises"] = int(d.loc[m, "franchise_id"].nunique())
        row[lab + "_pct_of_sample"] = round(100 * m.mean(), 1)
    rows.append(row)
cov = pd.DataFrame(rows)
save(cov, "feasibility_counts.csv")

# ---------------------------------------------------- 7. distributions in principal
P = principal[principal.cast_retention_top5.notna() & principal.dir_chg.notna()].copy()
dist_cast = P.cast_retention_top5.round(1).value_counts().sort_index().rename_axis("cast_retention_top5").reset_index(name="n")
dist_cast["pct"] = (100 * dist_cast.n / len(P)).round(1)
save(dist_cast, "cast_retention_distribution_principal.csv")
ct = pd.crosstab(P.cast_retention_top5.round(1), P.dir_chg.map({0.0: "dir_same", 1.0: "dir_changed"}), margins=True)
save(ct.reset_index(), "cast_by_director_crosstab_principal.csv")
dir_dist = P.dir_chg.map({0.0: "director_same", 1.0: "director_changed"}).value_counts().rename_axis("director").reset_index(name="n")
save(dir_dist, "director_distribution_principal.csv")

# ---------------------------------------------------- 8. concentration / dependence
vc = P.franchise_id.value_counts()
within = P.groupby("franchise_id").agg(n=("Y", "size"), dir_mean=("dir_chg", "mean"), cast_sd=("cast_retention_top5", "std"))
multi = within[within.n >= 2]
conc = {
    "n": len(P), "franchises": int(vc.size),
    "singleton_franchises": int((vc == 1).sum()),
    "largest_franchise_n": int(vc.iloc[0]), "largest_franchise_share_pct": round(100 * vc.iloc[0] / len(P), 1),
    "top5_franchises_share_pct": round(100 * vc.head(5).sum() / len(P), 1),
    "franchises_with_>=2_transitions": int(len(multi)),
    "of_which_director_varies_within_franchise": int(((multi.dir_mean > 0) & (multi.dir_mean < 1)).sum()),
    "of_which_cast_retention_varies_within_franchise": int((multi.cast_sd > 0).sum()),
    "transitions_in_franchises_with_>=2": int(multi.n.sum()),
}
log["concentration_principal"] = conc
save(vc.head(15).rename_axis("franchise_id").reset_index(name="transitions"), "top_franchises_principal.csv")

# ---------------------------------------------------- 9. descriptive association (KHÔNG phải mô hình)
desc = {
    "NOTE": "mô tả đơn biến/cặp biến trên mẫu principal; không điều chỉnh biến bối cảnh; không suy ra nhân quả",
    "spearman_cast_vs_Y": round(P[["cast_retention_top5", "Y"]].corr("spearman").iloc[0, 1], 3),
    "spearman_dirchanged_vs_Y": round(P[["dir_chg", "Y"]].corr("spearman").iloc[0, 1], 3),
    "spearman_cast_vs_dirchanged": round(P[["cast_retention_top5", "dir_chg"]].corr("spearman").iloc[0, 1], 3),
    "spearman_cast_vs_gap_years": round(P[["cast_retention_top5", "gap_years"]].corr("spearman").iloc[0, 1], 3),
    "spearman_dirchanged_vs_gap_years": round(P[["dir_chg", "gap_years"]].corr("spearman").iloc[0, 1], 3),
    "spearman_cast_vs_audience_prev": round(P[["cast_retention_top5", "A10"]].corr("spearman").iloc[0, 1], 3),
    "spearman_dirchanged_vs_audience_prev": round(P[["dir_chg", "A10"]].corr("spearman").iloc[0, 1], 3),
    "Y_mean_by_director": P.groupby("dir_chg").Y.mean().round(3).to_dict(),
    "Y_median_by_director": P.groupby("dir_chg").Y.median().round(3).to_dict(),
    "cast_retention_mean_by_director": P.groupby("dir_chg").cast_retention_top5.mean().round(3).to_dict(),
}
log["descriptive_principal"] = desc

# ---------------------------------------------------- 10. spot-check pairs (từ dữ liệu thật)
def pick(df, mask, k, label, seed=7):
    d = df[mask]
    d = d.sample(min(k, len(d)), random_state=seed) if len(d) else d
    return d.assign(case=label)

Xi = X.set_index("transition_id")
rows = []
pr = principal.set_index("transition_id")
pr = pr.join(Xi[["s_prev", "s_curr", "d_prev", "d_curr", "my_cast_ret", "my_dir_changed", "my_dir_overlap"]], how="left")
pr = pr.reset_index()
rows += [pick(pr, pr.cast_retention_top5.eq(0), 2, "cast_ret = 0"),
         pick(pr, pr.cast_retention_top5.eq(1), 2, "cast_ret = 1"),
         pick(pr, pr.cast_retention_top5.round(1).eq(0.4), 2, "cast_ret = 0.4 (mức giữa)"),
         pick(pr, pr.cast_retention_top5.round(1).eq(0.6), 1, "cast_ret = 0.6 (mức giữa)"),
         pick(pr, pr.dir_chg.eq(0), 2, "director không đổi"),
         pick(pr, pr.dir_chg.eq(1) & pr.my_dir_overlap.eq(0), 2, "director đổi hoàn toàn (overlap 0)"),
         pick(pr, pr.dir_chg.eq(1) & pr.my_dir_overlap.gt(0), 3, "director đổi một phần (đa đạo diễn, overlap>0)")]
allx = X.set_index("transition_id")
miss_c = allx[(allx.cast_retention_top5.isna()) & allx.ncast_prev.notna() & allx.ncast_curr.notna()].reset_index()
miss_c = miss_c.sample(min(3, len(miss_c)), random_state=7).assign(case="cast_ret THIẾU (<5 diễn viên một bên) - không bị đổi thành 0")
miss_d = allx[allx.dir_chg.isna()].reset_index()
miss_d = miss_d.sample(min(3, len(miss_d)), random_state=7).assign(case="director THIẾU (không có dòng director) - không bị đổi thành FALSE")
sp = pd.concat(rows + [miss_c, miss_d], ignore_index=True)
fmt = lambda s: "|".join(map(str, sorted(s))) if isinstance(s, frozenset) else ""
sp_out = pd.DataFrame({
    "case": sp.case, "transition_id": sp.transition_id, "title_prev": sp.title_prev, "title_curr": sp.title_curr,
    "master_cast_ret": sp.cast_retention_top5, "recomputed_cast_ret": sp.my_cast_ret,
    "top5_prev_ids": sp.s_prev.map(fmt), "top5_curr_ids": sp.s_curr.map(fmt),
    "ncast_prev": sp.get("ncast_prev"), "ncast_curr": sp.get("ncast_curr"),
    "master_dir_changed": sp.get("is_director_changed", sp.get("dir_chg")),
    "recomputed_dir_changed": sp.my_dir_changed, "dir_overlap": sp.my_dir_overlap,
    "dir_prev_ids": sp.d_prev.map(fmt), "dir_curr_ids": sp.d_curr.map(fmt)})
save(sp_out, "spot_check_pairs.csv")

# ---------------------------------------------------- 11. variable audit table
va = pd.DataFrame([
    {"column": "cast_retention_top5", "formula": "|top5_prev ∩ top5_curr| / 5", "ordering_field": "credits.billing_order (tăng dần)",
     "id_based": "person_id (TMDB)", "fewer_than_5": "thiếu (NaN), không phải 0",
     "master_nonmissing": cast_cmp["master_nonmissing"], "recompute_match": cast_cmp["value_match_on_master_nonmissing"]},
    {"column": "is_director_changed", "formula": "set(person_id director N-1) != set(N)", "ordering_field": "không dùng (director không có billing_order)",
     "id_based": "person_id (TMDB)", "fewer_than_5": "n/a",
     "master_nonmissing": dir_cmp["master_nonmissing"], "recompute_match": dir_cmp["changed_match"]},
    {"column": "director_jaccard_snapshot", "formula": "|∩|/|∪| của hai tập đạo diễn", "ordering_field": "n/a",
     "id_based": "person_id (TMDB)", "fewer_than_5": "n/a",
     "master_nonmissing": dir_cmp["master_nonmissing"], "recompute_match": dir_cmp["jaccard_match"]},
])
save(va, "variable_audit.csv")

# ---------------------------------------------------- write log
def _clean(o):
    if isinstance(o, dict): return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, (np.bool_,)): return bool(o)
    return o
with open(OUT / "audit_log.json", "w", encoding="utf-8") as f:
    json.dump(_clean(log), f, ensure_ascii=False, indent=2)
print(json.dumps(_clean(log), ensure_ascii=False, indent=2))
print("\n", cov.T.to_string())
print("\n", dist_cast.to_string(index=False)); print(ct)
print("\nspot-check:", len(sp_out), "rows ->", OUT)
