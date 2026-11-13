#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Understanding / EDA cho 5 dataset phim (CHỈ ĐỌC - KHÔNG SỬA DỮ LIỆU GỐC).

Chạy:
    python data_understanding_eda.py --data-dir /đường/dẫn/tới/csv --out-dir ../

Đầu ra (trong --out-dir):
    reports/*.csv          các bảng thống kê
    reports/md/*.md        các bảng Markdown (dùng cho build_report.py)
    reports/metrics.json   toàn bộ số liệu đã tính
    plots/<chủ đề>/*.png   biểu đồ

Nguyên tắc: không dropna/fillna/drop_duplicates/replace lên dataset gốc; mọi phép
biến đổi (log, parse ngày, merge) chỉ thực hiện trên bản sao trong bộ nhớ.
"""
import argparse
import json
import sys
import warnings
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")

DATASETS = ["movies_raw", "box_office_raw", "box_office_detailed", "credits_raw", "rt_scores"]
KEY = "film_key"
PURPOSE = {
    "movies_raw": "Metadata phim (TMDB): tên, ngày phát hành, ngân sách, thể loại, đạo diễn, diễn viên, hãng SX, vote_count",
    "box_office_raw": "Doanh thu toàn cầu (global_gross) từ TMDB API",
    "box_office_detailed": "Doanh thu nội địa / quốc tế / tuần mở màn (theo imdb_id)",
    "credits_raw": "Đoàn làm phim: mỗi dòng = 1 người x 1 vai trò (cast/director) x 1 phim (quan hệ 1-N)",
    "rt_scores": "Điểm Rotten Tomatoes (critic/audience) + trạng thái khớp RT",
}
DS_COL = {"movies_raw": "#1f77b4", "box_office_raw": "#ff7f0e", "box_office_detailed": "#2ca02c",
          "credits_raw": "#9467bd", "rt_scores": "#d62728"}
C_MAIN, C_ALT, C_WARN = "#3b7dbc", "#e07b39", "#c0392b"
MONEY = ["production_budget", "global_gross", "domestic_gross", "international_gross", "opening_weekend_gross"]
SCORES = ["critic_score", "audience_score"]
RETRIEVAL_DATE = pd.Timestamp("2026-10-22")  # giá trị retrieval_date duy nhất trong dữ liệu
TMDB_GENRE = {28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 99: "Documentary",
              18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
              9648: "Mystery", 10749: "Romance", 878: "Science Fiction", 10770: "TV Movie", 53: "Thriller",
              10752: "War", 37: "Western"}  # tên theo bảng TMDB chuẩn (KHÔNG có trong dataset)

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 150, "axes.titlesize": 12, "axes.labelsize": 10,
                     "font.family": "DejaVu Sans"})

M = {"errors": []}  # metrics
OUT = None


# ----------------------------------------------------------------------------- helpers
def fmt(v):
    if isinstance(v, (bool, np.bool_)):
        return str(v)
    if isinstance(v, (int, np.integer)):
        return f"{v:,}"
    if isinstance(v, (float, np.floating)):
        if np.isnan(v):
            return ""
        if v != 0 and abs(v) < 0.01:
            return f"{v:.1e}"
        if abs(v) >= 1000:
            return f"{v:,.0f}"
        return f"{v:,.2f}"
    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.astype(object).iterrows():
        lines.append("| " + " | ".join(fmt(v) for v in r) + " |")
    return "\n".join(lines)


def save_table(df, name, md=True):
    df.to_csv(OUT / "reports" / f"{name}.csv", index=False, encoding="utf-8-sig")
    if md:
        (OUT / "reports" / "md" / f"{name}.md").write_text(md_table(df), encoding="utf-8")


def savefig(fig, sub, name):
    p = OUT / "plots" / sub / f"{name}.png"
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    M.setdefault("plots", []).append(f"plots/{sub}/{name}.png")


def safe(fn):
    def wrap(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as e:  # ghi nhận chứ không dừng toàn bộ
            M["errors"].append(f"{fn.__name__}: {type(e).__name__}: {e}")
            print("LỖI", fn.__name__, e, file=sys.stderr)
    return wrap


def pct(a, b):
    return round(100 * a / b, 2) if b else float("nan")


def cramers_v(x, y):
    ct = pd.crosstab(x, y)
    chi2 = stats.chi2_contingency(ct)[0]
    n = ct.values.sum()
    return float(np.sqrt(chi2 / (n * (min(ct.shape) - 1))))


def vif_table(df, cols):
    X = df[cols].values.astype(float)
    out = {}
    for i, c in enumerate(cols):
        y = X[:, i]
        Z = np.c_[np.ones(len(X)), np.delete(X, i, axis=1)]
        beta = np.linalg.lstsq(Z, y, rcond=None)[0]
        r2 = 1 - (y - Z @ beta).var() / y.var()
        out[c] = 1 / (1 - r2)
    return out


def upset(pat, labels, title, fname, sub, topn=12, color=C_MAIN, xlabel="Số phim"):
    """UpSet-style: cột = tổ hợp có mặt; pat là DataFrame bool."""
    vc = pat.value_counts().head(topn)
    n = len(vc)
    fig = plt.figure(figsize=(max(9, 0.85 * n + 3), 6.5))
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1.7], hspace=0.05)
    ax1, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1], sharex=None)
    xs = np.arange(n)
    ax1.bar(xs, vc.values, color=color)
    for x, v in zip(xs, vc.values):
        ax1.text(x, v, f"{v:,}\n({v / len(pat) * 100:.1f}%)", ha="center", va="bottom", fontsize=8)
    ax1.set_xticks([]); ax1.set_ylabel(xlabel); ax1.set_title(title)
    ax1.set_ylim(0, vc.max() * 1.18); ax1.set_xlim(-0.6, n - 0.4)
    for j, lab in enumerate(labels):
        ax2.text(-0.9, j, lab, ha="right", va="center", fontsize=9)
    for i, combo in enumerate(vc.index):
        on = [j for j, b in enumerate(combo) if b]
        ax2.scatter([i] * len(labels), range(len(labels)), s=60, color="#dddddd", zorder=2)
        ax2.scatter([i] * len(on), on, s=60, color="#222222", zorder=3)
        if len(on) > 1:
            ax2.plot([i, i], [min(on), max(on)], color="#222222", lw=2, zorder=2)
    ax2.set_ylim(-0.6, len(labels) - 0.4); ax2.set_xlim(-0.6, n - 0.4)
    ax2.invert_yaxis(); ax2.axis("off")
    savefig(fig, sub, fname)


# ----------------------------------------------------------------------------- load
def load(data_dir):
    D = {}
    for n in DATASETS:
        p = Path(data_dir) / f"{n}.csv"
        if not p.exists():
            M["errors"].append(f"Thiếu file {p}")
            continue
        D[n] = pd.read_csv(p, dtype={KEY: str})  # chỉ đọc
    return D


def build_master(D):
    """Bảng tạm trong bộ nhớ (1-1 theo film_key) phục vụ phân tích. KHÔNG ghi ra đĩa."""
    m, bo, bd, rt = D["movies_raw"], D["box_office_raw"], D["box_office_detailed"], D["rt_scores"]
    for name, d in [("movies_raw", m), ("box_office_raw", bo), ("box_office_detailed", bd), ("rt_scores", rt)]:
        assert d[KEY].is_unique, f"{name}.film_key không duy nhất -> merge 1-1 không an toàn"
    F = m[[KEY, "title", "release_date_ref", "release_month", "production_budget", "vote_count",
           "tmdb_collection_id", "genre_ids", "director_ids", "lead_cast_ids_superset",
           "production_company_ids", "imdb_id"]].copy()
    F = F.merge(bo[[KEY, "global_gross"]], on=KEY, how="left")
    F = F.merge(bd[[KEY, "domestic_gross", "international_gross", "opening_weekend_gross"]], on=KEY, how="left")
    F = F.merge(rt[[KEY, "critic_score", "audience_score", "rt_status", "rt_url"]], on=KEY, how="left")
    cr = D["credits_raw"]
    F["in_movies"] = True
    F["in_bo_raw"] = F[KEY].isin(bo[KEY])
    F["in_bo_det"] = F[KEY].isin(bd[KEY])
    F["in_credits"] = F[KEY].isin(cr[KEY])
    F["in_rt"] = F[KEY].isin(rt[KEY])
    dt = pd.to_datetime(F["release_date_ref"], errors="coerce")
    F["release_dt"], F["year"] = dt, dt.dt.year
    F["decade"] = (F["year"] // 10 * 10)
    F["vgroup"] = pd.cut(F["vote_count"], [-1, 0, 9, 99, 999, 10 ** 9], labels=["0", "1-9", "10-99", "100-999", "1000+"])
    F["has_det_val"] = F[["domestic_gross", "international_gross", "opening_weekend_gross"]].notna().any(axis=1)
    return F


# ----------------------------------------------------------------------------- 1. overview / schema / missing
def col_role(s, name):
    nn = s.dropna()
    if s.nunique() <= 1:
        return "hằng số / rỗng" if len(nn) else "rỗng 100%"
    if s.dtype == bool:
        return "cờ (bool)"
    if name == KEY or name.endswith("_id") and name in ("tmdb_id", "imdb_id", "person_id"):
        return "định danh"
    if "date" in name:
        return "ngày (text)"
    if s.dtype == object or str(s.dtype).startswith("str"):
        if nn.astype(str).str.contains(r"\|", regex=True).mean() > 0.01:
            return "đa trị ('|')"
        return "text / categorical"
    if name in ("release_month", "tmdb_collection_id"):
        return "định danh/rời rạc"
    return "số"


@safe
def overview(D):
    rows, crow = [], []
    for n, d in D.items():
        full_dup = int(d.duplicated().sum())
        rows.append({"Dataset": n, "Number of Rows": len(d), "Number of Columns": d.shape[1], "Key": KEY,
                     "Unique film_key": int(d[KEY].nunique()), "Full-row duplicates": full_dup,
                     "Missing cells %": round(d.isna().mean().mean() * 100, 2), "Main Purpose": PURPOSE[n]})
        for c in d.columns:
            s = d[c]
            crow.append({"Dataset": n, "Column": c, "Data Type": str(s.dtype), "Role (suy luận)": col_role(s, c),
                         "Unique Values": int(s.nunique()), "Missing Count": int(s.isna().sum()),
                         "Missing Percentage": round(s.isna().mean() * 100, 2)})
    ov, co = pd.DataFrame(rows), pd.DataFrame(crow)
    save_table(ov, "dataset_overview"); save_table(co, "column_overview")
    mv = co[co["Missing Count"] > 0].sort_values("Missing Percentage", ascending=False)
    save_table(mv, "missing_values")
    M["overview"] = ov.to_dict("records")
    M["miss_pct"] = {f"{r.Dataset}.{r.Column}": r["Missing Percentage"] for _, r in co.iterrows()}
    M["miss_cnt"] = {f"{r.Dataset}.{r.Column}": r["Missing Count"] for _, r in co.iterrows()}
    M["const_cols"] = co[co["Unique Values"] <= 1][["Dataset", "Column", "Unique Values"]].values.tolist()


# ----------------------------------------------------------------------------- 2. duplicates & key
@safe
def duplicates_and_keys(D, F):
    m, bo, bd, cr, rt = (D[n] for n in DATASETS)
    rows = []
    for n, d in D.items():
        rows.append({"Dataset": n, "Check": "Trùng toàn bộ dòng", "Count": int(d.duplicated().sum()), "Note": ""})
        rows.append({"Dataset": n, "Check": "film_key bị thiếu", "Count": int(d[KEY].isna().sum()), "Note": ""})
        rows.append({"Dataset": n, "Check": "Dòng có film_key lặp (keep=False)", "Count": int(d[KEY].duplicated(keep=False).sum()),
                     "Note": "quan hệ 1-N là bình thường" if n == "credits_raw" else "kỳ vọng 0 (quan hệ 1-1)"})
    # credits
    dup3 = cr.duplicated([KEY, "person_id", "role"], keep=False)
    M["cr_dup_fpr_rows_extra"] = int(cr.duplicated([KEY, "person_id", "role"]).sum())
    M["cr_dup_fpr_groups"] = int(cr[dup3].groupby([KEY, "person_id", "role"]).ngroups)
    M["cr_dup_fpr_roles"] = cr[cr.duplicated([KEY, "person_id", "role"])].role.value_counts().to_dict()
    M["cr_dup_fp_extra"] = int(cr.duplicated([KEY, "person_id"]).sum())
    cast = cr[cr.role == "cast"]
    M["cr_dup_billing_extra"] = int(cast.duplicated([KEY, "billing_order"]).sum())
    rows += [{"Dataset": "credits_raw", "Check": "Trùng (film_key, person_id, role) - dòng dư", "Count": M["cr_dup_fpr_rows_extra"],
              "Note": f"khác nhau ở billing_order; vai trò: {M['cr_dup_fpr_roles']}"},
             {"Dataset": "credits_raw", "Check": "Trùng (film_key, person_id) - dòng dư", "Count": M["cr_dup_fp_extra"],
              "Note": "gồm cả người vừa là đạo diễn vừa là diễn viên (hợp lệ)"},
             {"Dataset": "credits_raw", "Check": "Trùng (film_key, billing_order) trong cast", "Count": M["cr_dup_billing_extra"], "Note": ""}]
    # movies
    t = m["title"]
    M["title_dup_rows"] = int(t.duplicated(keep=False).sum()); M["title_unique"] = int(t.nunique())
    g = m[t.duplicated(keep=False)].groupby("title").agg(n=(KEY, "size"), nd=("release_date_ref", "nunique"),
                                                          nnull=("release_date_ref", lambda s: s.isna().sum()))
    M["title_samedate_groups"] = int(((g.n > 1) & (g.nd == 1) & (g.nnull == 0)).sum())
    M["imdb_dup_nonnull"] = int(m["imdb_id"].dropna().duplicated().sum())
    M["tmdb_dup"] = int(m["tmdb_id"].duplicated().sum())
    rows += [{"Dataset": "movies_raw", "Check": "Số dòng có title trùng (keep=False)", "Count": M["title_dup_rows"],
              "Note": f"{M['title_unique']:,} title khác nhau / {len(m):,} dòng; không phải lỗi"},
             {"Dataset": "movies_raw", "Check": "Nhóm title trùng + cùng release_date_ref", "Count": M["title_samedate_groups"],
              "Note": "ứng viên trùng phim, cần kiểm tra thủ công"},
             {"Dataset": "movies_raw", "Check": "imdb_id trùng (non-null)", "Count": M["imdb_dup_nonnull"], "Note": ""},
             {"Dataset": "movies_raw", "Check": "tmdb_id trùng", "Count": M["tmdb_dup"], "Note": ""}]
    save_table(pd.DataFrame(rows), "duplicate_report")

    # key consistency
    sm = set(m[KEY]); kr = []
    for n, d in D.items():
        ks = set(d[KEY])
        kr.append({"Dataset": n, "Rows": len(d), "Unique film_key": len(ks), "Missing film_key": int(d[KEY].isna().sum()),
                   "Rows per key (max)": int(d.groupby(KEY).size().max()),
                   "Keys in movies_raw": len(ks & sm), "Orphan keys (not in movies_raw)": len(ks - sm),
                   "Coverage of movies_raw %": round(len(ks & sm) / len(sm) * 100, 2)})
    save_table(pd.DataFrame(kr), "key_consistency")
    # format film_key
    M["fk_format_ok"] = bool((m[KEY] == "FK" + m["tmdb_id"].astype(str).str.zfill(8)).all())
    M["same_order"] = bool((m[KEY].values == D["box_office_raw"][KEY].values).all() and (m[KEY].values == D["rt_scores"][KEY].values).all())
    # imdb consistency movies vs detailed
    x = bd.merge(m[[KEY, "imdb_id"]], on=KEY, suffixes=("_bd", "_m"))
    M["imdb_eq"] = int((x.imdb_id_bd == x.imdb_id_m).sum()); M["imdb_neq"] = int((x.imdb_id_bd != x.imdb_id_m).sum())
    # presence patterns
    pat = F[["in_movies", "in_bo_raw", "in_bo_det", "in_credits", "in_rt"]]
    M["presence_patterns"] = {str(k): int(v) for k, v in pat.value_counts().items()}
    M["in_all5"] = int(pat.all(axis=1).sum())
    # naive join
    naive = m[[KEY, "production_budget"]].merge(cr, on=KEY, how="left")
    M["naive_rows"] = int(len(naive)); M["naive_factor"] = round(len(naive) / len(m), 2)
    true_sum = m["production_budget"].sum(); naive_sum = naive["production_budget"].sum()
    M["budget_sum_inflation"] = round(naive_sum / true_sum, 2)
    M["films_no_credits"] = int((~F["in_credits"]).sum())
    M["no_credits_vote_median"] = float(F.loc[~F["in_credits"], "vote_count"].median())
    M["credits_per_film"] = cr.groupby(KEY).size().describe().round(2).to_dict()
    M["credits_per_film_max"] = int(cr.groupby(KEY).size().max())


# ----------------------------------------------------------------------------- 3. numeric stats
def num_summary(s, name, ds):
    s = s.dropna().astype(float)
    q1, q3 = s.quantile(.25), s.quantile(.75)
    iqr = q3 - q1
    r = {"Dataset": ds, "Column": name, "Count": len(s), "Mean": s.mean(), "Median": s.median(), "Std": s.std(),
         "Min": s.min(), "Q1": q1, "Q3": q3, "Max": s.max(), "IQR": iqr, "P99": s.quantile(.99),
         "Skewness": s.skew(), "Kurtosis": s.kurt(), "Mean/Median": s.mean() / s.median() if s.median() else np.nan,
         "P99/Median": s.quantile(.99) / s.median() if s.median() else np.nan,
         "IQR outliers high": int((s > q3 + 1.5 * iqr).sum()), "IQR outliers low": int((s < q1 - 1.5 * iqr).sum()),
         "Extreme high (>3IQR)": int((s > q3 + 3 * iqr).sum())}
    r["IQR outliers high %"] = round(r["IQR outliers high"] / len(s) * 100, 2)
    if name in MONEY:
        ls = np.log10(s[s > 0])
        lq1, lq3 = ls.quantile(.25), ls.quantile(.75); li = lq3 - lq1
        r.update({"Skew(log10)": ls.skew(), "Log-IQR outliers high": int((ls > lq3 + 1.5 * li).sum()),
                  "Log-IQR outliers low": int((ls < lq1 - 1.5 * li).sum()),
                  "Values <1000": int((s < 1000).sum()), "Values <100": int((s < 100).sum()), "Values <=0": int((s <= 0).sum())})
    return r


@safe
def numeric_stats(D, F):
    rows = []
    src = {"production_budget": "movies_raw", "global_gross": "box_office_raw", "domestic_gross": "box_office_detailed",
           "international_gross": "box_office_detailed", "opening_weekend_gross": "box_office_detailed",
           "critic_score": "rt_scores", "audience_score": "rt_scores", "vote_count": "movies_raw", "release_month": "movies_raw",
           "billing_order": "credits_raw"}
    for c, ds in src.items():
        rows.append(num_summary(D[ds][c], c, ds))
    ns = pd.DataFrame(rows)
    save_table(ns, "numerical_statistics", md=False)
    M["num"] = {r["Column"]: {k: (float(v) if isinstance(v, (int, float, np.number)) else v) for k, v in r.items()} for r in rows}
    # bảng rút gọn cho báo cáo
    a = ns[["Column", "Count", "Mean", "Median", "Std", "Min", "Q1", "Q3", "Max", "Skewness", "Kurtosis", "Mean/Median", "P99/Median"]]
    (OUT / "reports" / "md" / "numerical_statistics.md").write_text(md_table(a), encoding="utf-8")
    b = ns[ns.Column.isin(MONEY + SCORES)][["Column", "Count", "Q1", "Q3", "IQR", "IQR outliers high", "IQR outliers high %",
                                           "Extreme high (>3IQR)"]]
    (OUT / "reports" / "md" / "iqr_outliers.md").write_text(md_table(b), encoding="utf-8")
    c = ns[ns.Column.isin(MONEY)][["Column", "Skewness", "Skew(log10)", "Log-IQR outliers high", "Log-IQR outliers low",
                                    "Values <1000", "Values <100", "Values <=0"]]
    (OUT / "reports" / "md" / "log_outliers.md").write_text(md_table(c), encoding="utf-8")

    # vùng giá trị thấp & heaping
    ph = {}
    for c in MONEY:
        s = F[c].dropna()
        ph[c] = {"n": len(s), "lt1000": int((s < 1000).sum()), "lt100": int((s < 100).sum()), "lt10": int((s < 10).sum()),
                 "mult_1e6": round(float((s % 1e6 == 0).mean() * 100), 1), "mult_1e5": round(float((s % 1e5 == 0).mean() * 100), 1),
                 "top_values": {int(k): int(v) for k, v in s.value_counts().head(5).items()}}
    M["placeholder"] = ph
    b = F[(F.production_budget < 1000)]
    bg = b.dropna(subset=["global_gross"])
    M["lowbud_with_gross"] = {"n_lowbud": len(b), "n_with_gross": len(bg), "median_gross": float(bg.global_gross.median()) if len(bg) else None,
                              "share_gross_ge_1e6": round(float((bg.global_gross >= 1e6).mean() * 100), 1) if len(bg) else None,
                              "median_vote": float(b.vote_count.median()), "n_ge_100_votes": int((b.vote_count >= 100).sum())}
    g = F[(F.global_gross < 1000)]
    gb = g.dropna(subset=["production_budget"])
    M["lowgross_with_budget"] = {"n_lowgross": len(g), "n_with_budget": len(gb), "median_budget": float(gb.production_budget.median()) if len(gb) else None,
                                 "median_vote": float(g.vote_count.median())}
    both = F.dropna(subset=["production_budget", "global_gross"])
    ratio = both.global_gross / both.production_budget
    M["ratio"] = {"n": len(both), "gross_lt_budget": int((ratio < 1).sum()), "gt100": int((ratio > 100).sum()),
                  "lt_0_001": int((ratio < 0.001).sum()), "median": float(ratio.median())}
    # scores
    for c in SCORES:
        s = F[c].dropna()
        M[f"{c}_edges"] = {"n": len(s), "zero": int((s == 0).sum()), "hundred": int((s == 100).sum()),
                           "hundred_pct": round(float((s == 100).mean() * 100), 2), "mult10_pct": round(float((s % 10 == 0).mean() * 100), 1),
                           "mult5_pct": round(float((s % 5 == 0).mean() * 100), 1)}
    ex = F[F.critic_score.isin([0, 100])]
    M["critic_edge_vote_median"] = float(ex.vote_count.median())
    M["critic_mid_vote_median"] = float(F[F.critic_score.between(1, 99)].vote_count.median())
    # financial values for films not yet released
    fut = F[F.release_dt > RETRIEVAL_DATE]
    M["future_with_fin"] = {"n_future": len(fut), "with_budget": int(fut.production_budget.notna().sum()),
                           "with_global": int(fut.global_gross.notna().sum()), "with_critic": int(fut.critic_score.notna().sum())}


# ----------------------------------------------------------------------------- 4. categorical
@safe
def categorical_stats(D, F):
    m, cr, rt = D["movies_raw"], D["credits_raw"], D["rt_scores"]
    rows = []
    for col in ["genre_ids", "director_ids", "lead_cast_ids_superset", "production_company_ids"]:
        s = m[col].dropna().astype(str)
        toks = s.str.split("|")
        cnt = Counter(t for l in toks for t in l)
        tot = sum(cnt.values())
        top = cnt.most_common(10)
        canon = toks.apply(lambda l: "|".join(sorted(l, key=lambda x: int(x))))
        sets = toks.apply(lambda l: frozenset(l))
        rows.append({"Column": col, "Non-null cells": len(s), "Tokens/cell mean": toks.str.len().mean(),
                     "Tokens/cell max": int(toks.str.len().max()), "Unique tokens": len(cnt),
                     "Unique cell strings": int(s.nunique()), "Unique as sets": int(sets.nunique()),
                     "Cells not numerically sorted %": round(float((toks.apply(lambda l: [int(x) for x in l]) != toks.apply(lambda l: sorted(int(x) for x in l))).mean() * 100), 1),
                     "Top-1 token share %": round(top[0][1] / tot * 100, 2), "Top-10 token share %": round(sum(v for _, v in top) / tot * 100, 2),
                     "Tokens appearing once": int(sum(1 for v in cnt.values() if v == 1)),
                     "Top token": top[0][0]})
        M[f"cnt_{col}"] = cnt
    cs = pd.DataFrame(rows)
    save_table(cs, "categorical_statistics")
    M["cat"] = cs.to_dict("records")
    # genre names
    gc = M["cnt_genre_ids"]
    M["genre_tokens"] = {k: v for k, v in gc.items()}
    M["genre_unknown"] = [k for k in gc if int(k) not in TMDB_GENRE]
    # collection
    cc = m["tmdb_collection_id"].value_counts()
    M["collection"] = {"n_groups": int(len(cc)), "singletons": int((cc == 1).sum()), "median": float(cc.median()),
                       "mean": round(float(cc.mean()), 2), "max": int(cc.max()), "films_with": int(m.tmdb_collection_id.notna().sum()),
                       "share_films_in_groups_ge2": round(float(cc[cc >= 2].sum() / cc.sum() * 100), 1),
                       "top5": {int(k): int(v) for k, v in cc.head(5).items()}}
    # small categorical
    M["rt_status"] = rt["rt_status"].value_counts().to_dict()
    M["role_counts"] = cr["role"].value_counts().to_dict()
    # credits per role
    dr = cr[cr.role == "director"].groupby(KEY).size(); cs_ = cr[cr.role == "cast"].groupby(KEY).size()
    M["credits_dir"] = {"films": int(len(dr)), "max": int(dr.max()), "mean": round(float(dr.mean()), 2)}
    M["credits_cast"] = {"films": int(len(cs_)), "max": int(cs_.max()), "median": float(cs_.median())}
    M["no_dir_films"] = int(cr[KEY].nunique() - len(dr)); M["no_cast_films"] = int(cr[KEY].nunique() - len(cs_))
    # consistency movies.director_ids <-> credits
    cd = cr[cr.role == "director"].groupby(KEY).person_id.apply(lambda s: set(s.astype(str)))
    md = m.dropna(subset=["director_ids"]).set_index(KEY).director_ids.str.split("|").apply(set)
    j = pd.concat([md.rename("m"), cd.rename("c")], axis=1)
    M["dir_consistency"] = {"movies_nonnull": int(j.m.notna().sum()), "credits_films": int(j.c.notna().sum()),
                            "both": int(j.dropna().shape[0]), "equal_sets": int(sum(a == b for a, b in zip(j.dropna().m, j.dropna().c))),
                            "movies_null_credits_has": int((j.m.isna() & j.c.notna()).sum()),
                            "movies_has_credits_none": int((j.m.notna() & j.c.isna()).sum())}
    lc = m.dropna(subset=["lead_cast_ids_superset"]).set_index(KEY).lead_cast_ids_superset.str.split("|").str.len()
    cc2 = cr[cr.role == "cast"].groupby(KEY).size()
    jj = pd.concat([lc.rename("lead"), cc2.rename("cast")], axis=1).dropna()
    M["lead_vs_cast"] = {"max_lead": int(lc.max()), "corr": round(float(jj.corr().iloc[0, 1]), 3),
                         "lead_gt_cast": int((jj.lead > jj.cast).sum())}
    # tên: ký tự phi-ASCII
    M["title_nonascii_pct"] = round(float(m.title.str.contains(r"[^\x00-\x7F]").mean() * 100), 2)
    # coverage theo thể loại
    gm = F[["genre_ids", "production_budget", "global_gross", "critic_score"]].dropna(subset=["genre_ids"]).copy()
    gm["g"] = gm.genre_ids.str.split("|")
    ex = gm.explode("g")
    ex["g"] = ex.g.astype(int)
    gcov = ex.groupby("g").agg(n=("g", "size"), budget=("production_budget", lambda s: s.notna().mean() * 100),
                               gross=("global_gross", lambda s: s.notna().mean() * 100), critic=("critic_score", lambda s: s.notna().mean() * 100))
    gcov["name"] = [TMDB_GENRE.get(i, str(i)) for i in gcov.index]
    M["genre_cov"] = gcov.round(1).reset_index().to_dict("records")
    return gcov


# ----------------------------------------------------------------------------- 5. dates
@safe
def date_stats(D, F):
    dt = F["release_dt"]
    ok = dt.notna()
    M["date"] = {"missing": int((~ok).sum()), "parse_fail": int((F.release_date_ref.notna() & ~ok).sum()),
                 "min": str(dt.min().date()), "max": str(dt.max().date()),
                 "after_retrieval": int((dt > RETRIEVAL_DATE).sum()), "year_ge_2027": int((F.year >= 2027).sum()),
                 "pre1980": int((F.year < 1980).sum()), "pre1980_pct_dated": round(float((F.year < 1980).sum() / ok.sum() * 100), 2),
                 "pre1980_pct_all": round(float((F.year < 1980).sum() / len(F) * 100), 2),
                 "jan1": int(((dt.dt.month == 1) & (dt.dt.day == 1)).sum()),
                 "jan1_pct_dated": round(float(((dt.dt.month == 1) & (dt.dt.day == 1)).sum() / ok.sum() * 100), 2),
                 "expected_pct": round(100 / 365, 2),
                 "month_mismatch": int((dt.dt.month != F.release_month)[ok].sum()),
                 "format_len": F.release_date_ref.dropna().str.len().value_counts().to_dict(),
                 "median_year": float(F.year.median()), "films_2025_2026": int(F.year.isin([2025, 2026]).sum())}
    by = F.groupby("decade").agg(n=(KEY, "size"), budget=("production_budget", lambda s: s.notna().mean() * 100),
                                 global_gross=("global_gross", lambda s: s.notna().mean() * 100),
                                 critic=("critic_score", lambda s: s.notna().mean() * 100),
                                 audience=("audience_score", lambda s: s.notna().mean() * 100),
                                 detail=("has_det_val", lambda s: s.mean() * 100)).round(1).reset_index()
    by["decade"] = by["decade"].astype(int)
    M["decade_cov"] = by.to_dict("records")
    (OUT / "reports" / "md" / "decade_coverage.md").write_text(md_table(by.assign(decade=by["decade"].astype(str) + "s")), encoding="utf-8")
    save_table(by, "decade_coverage", md=False)
    jan = F[(dt.dt.month == 1) & (dt.dt.day == 1)].groupby(F.year // 10 * 10).size()
    M["jan1_by_decade"] = {int(k): int(v) for k, v in jan.items()}


# ----------------------------------------------------------------------------- 6. missingness vs popularity
@safe
def missing_mechanism(F):
    out = {}
    vars_ = {"production_budget": "production_budget", "global_gross": "global_gross", "critic_score": "critic_score",
             "audience_score": "audience_score", "domestic_gross": "domestic_gross", "international_gross": "international_gross"}
    rows = []
    for v in vars_:
        has = F[v].notna()
        a, b = F.loc[has, "vote_count"], F.loc[~has, "vote_count"]
        u = stats.mannwhitneyu(a, b, alternative="two-sided")
        rbc = 2 * u.statistic / (len(a) * len(b)) - 1  # rank-biserial
        rows.append({"Variable": v, "n có dữ liệu": int(has.sum()), "Median vote (có)": a.median(), "Median vote (thiếu)": b.median(),
                     "Rank-biserial": round(float(rbc), 3), "Mann-Whitney p": float(u.pvalue),
                     "Cramér V (vote group x có/thiếu)": round(cramers_v(F["vgroup"], has), 3)})
    mm = pd.DataFrame(rows)
    save_table(mm, "missingness_vs_votes")
    M["missing_vs_votes"] = mm.to_dict("records")
    cov = F.groupby("vgroup", observed=True).agg(
        n=(KEY, "size"), **{v: (v, lambda s: s.notna().mean() * 100) for v in
                           ["production_budget", "global_gross", "domestic_gross", "international_gross", "opening_weekend_gross",
                            "critic_score", "audience_score"]}).round(1).reset_index()
    cov.insert(2, "share %", (cov.n / cov.n.sum() * 100).round(1))
    (OUT / "reports" / "md" / "coverage_by_vote.md").write_text(md_table(cov), encoding="utf-8")
    save_table(cov, "coverage_by_vote", md=False)
    M["coverage_by_vote"] = cov.to_dict("records")
    # độ đầy đủ
    core = MONEY + SCORES
    comp = F[core].notna().sum(axis=1)
    M["completeness"] = {int(k): int(v) for k, v in comp.value_counts().sort_index().items()}
    M["budget_and_gross"] = int((F.production_budget.notna() & F.global_gross.notna()).sum())
    M["all4"] = int(F[["production_budget", "global_gross", "critic_score", "audience_score"]].notna().all(axis=1).sum())
    M["budget_only"] = int((F.production_budget.notna() & F.global_gross.isna()).sum())
    M["gross_only"] = int((F.production_budget.isna() & F.global_gross.notna()).sum())
    # chi tiết bd
    bdv = F[F.in_bo_det]
    M["bd_empty"] = int((~bdv.has_det_val).sum()); M["bd_rows"] = int(len(bdv))
    pat = bdv[["domestic_gross", "international_gross", "opening_weekend_gross"]].notna()
    M["bd_patterns"] = {str(k): int(v) for k, v in pat.value_counts().items()}
    # raw vs detailed bổ sung cho nhau
    g = F.global_gross.notna(); d = F.has_det_val
    M["rev_overlap"] = {"both": int((g & d).sum()), "global_only": int((g & ~d).sum()), "detail_only": int((~g & d).sum()),
                        "neither": int((~g & ~d).sum()), "detail_only_in_bd_rows": int((~g & d).sum())}
    M["intl_only_no_dom"] = int((F.domestic_gross.isna() & F.international_gross.notna()).sum())
    # rt
    rt = F[["rt_status", "critic_score", "audience_score"]]
    ct = pd.crosstab(rt.rt_status, [rt.critic_score.notna().map({True: "critic", False: "-"}) + "+" + rt.audience_score.notna().map({True: "aud", False: "-"})])
    M["rt_cross"] = {str(i): {str(c): int(v) for c, v in r.items() if v} for i, r in ct.iterrows()}
    M["rt_url_missing_equals_unmatched_or_search"] = int(F.rt_url.isna().sum())
    # imdb_id thiếu theo vote
    M["imdb_missing_by_vote"] = F.groupby("vgroup", observed=True).imdb_id.apply(lambda s: round(s.isna().mean() * 100, 1)).to_dict()


# ----------------------------------------------------------------------------- 7. relationships
@safe
def relationships(F):
    pairs = [("production_budget", "global_gross"), ("production_budget", "domestic_gross"), ("production_budget", "international_gross"),
             ("production_budget", "opening_weekend_gross"), ("domestic_gross", "international_gross"),
             ("domestic_gross", "opening_weekend_gross"), ("opening_weekend_gross", "global_gross"),
             ("international_gross", "global_gross"), ("domestic_gross", "global_gross"), ("critic_score", "audience_score"),
             ("critic_score", "global_gross"), ("audience_score", "global_gross"), ("critic_score", "production_budget"),
             ("audience_score", "production_budget"), ("critic_score", "opening_weekend_gross"), ("vote_count", "global_gross"),
             ("vote_count", "production_budget"), ("vote_count", "critic_score")]
    rows = []
    for a, b in pairs:
        s = F[[a, b]].dropna()
        if len(s) < 30:
            continue
        la = np.log10(s[a].clip(lower=1)) if a in MONEY or a == "vote_count" else s[a]
        lb = np.log10(s[b].clip(lower=1)) if b in MONEY or b == "vote_count" else s[b]
        rows.append({"Var A": a, "Var B": b, "n": len(s), "Pearson": stats.pearsonr(s[a], s[b])[0],
                     "Spearman": stats.spearmanr(s[a], s[b])[0], "Pearson(log10)": stats.pearsonr(la, lb)[0]})
    cr_ = pd.DataFrame(rows)
    save_table(cr_, "correlations")
    M["corr"] = {f"{r['Var A']}|{r['Var B']}": {k: float(r[k]) for k in ["n", "Pearson", "Spearman", "Pearson(log10)"]} for _, r in cr_.iterrows()}
    # VIF
    cols = ["production_budget", "domestic_gross", "international_gross", "opening_weekend_gross", "critic_score", "audience_score"]
    s = F[cols].dropna().copy()
    for c in cols[:4]:
        s[c] = np.log10(s[c].clip(lower=1))
    v = vif_table(s, cols)
    M["vif"] = {k: round(x, 2) for k, x in v.items()}; M["vif_n"] = int(len(s))
    # tương quan theo thời kỳ (Simpson check) budget~global
    b = F.dropna(subset=["production_budget", "global_gross", "year"]).copy()
    b["era"] = pd.cut(b.year, [1800, 1979, 1999, 2009, 2019, 2100], labels=["<1980", "1980-99", "2000-09", "2010-19", "2020+"])
    era = b.groupby("era", observed=True).apply(lambda g: pd.Series({"n": len(g), "spearman": stats.spearmanr(g.production_budget, g.global_gross)[0]}))
    M["era_corr"] = era.round(2).reset_index().to_dict("records")
    # sau khi loại giá trị < 1000 (chỉ tính tạm, không sửa dữ liệu)
    c = b[(b.production_budget >= 1000) & (b.global_gross >= 1000)]
    M["corr_after_lowdrop"] = {"n": len(c), "pearson_log": float(stats.pearsonr(np.log10(c.production_budget), np.log10(c.global_gross))[0]),
                               "spearman": float(stats.spearmanr(c.production_budget, c.global_gross)[0])}
    # sau khi lọc vote>=100 (kiểm tra thiên lệch lựa chọn)
    c2 = b[b.vote_count >= 100]
    M["corr_votes_ge100"] = {"n": len(c2), "spearman": float(stats.spearmanr(c2.production_budget, c2.global_gross)[0])}
    # nhóm điểm vs doanh thu
    s = F.dropna(subset=["critic_score", "global_gross"]).copy()
    s["bin"] = pd.cut(s.critic_score, [-1, 20, 40, 60, 80, 100])
    M["critic_bin_median_gross"] = {str(k): float(v) for k, v in s.groupby("bin", observed=True).global_gross.median().items()}
    # consistency doanh thu
    x = F.dropna(subset=["global_gross", "international_gross"])
    y = F.dropna(subset=["global_gross", "domestic_gross"])
    z = F.dropna(subset=["global_gross", "international_gross", "domestic_gross"])
    dev = (z.domestic_gross + z.international_gross - z.global_gross) / z.global_gross
    w = F.dropna(subset=["domestic_gross", "opening_weekend_gross"])
    M["consistency"] = {"intl_gt_global_1pct": int((x.international_gross > x.global_gross * 1.01).sum()), "n_intl_global": len(x),
                        "dom_gt_global_1pct": int((y.domestic_gross > y.global_gross * 1.01).sum()), "n_dom_global": len(y),
                        "sum_dev_gt_1pct": int((dev.abs() > .01).sum()), "n_all3": len(z),
                        "sum_within_1pct": int((dev.abs() <= .01).sum()), "median_abs_dev": float(dev.abs().median()),
                        "sum_below_global_gt1pct": int((dev < -.01).sum()), "sum_above_global_gt1pct": int((dev > .01).sum()),
                        "open_gt_dom": int((w.opening_weekend_gross > w.domestic_gross).sum()), "n_open_dom": len(w),
                        "exact_equal": int((dev.abs() < 1e-9).sum())}
    save_table(pd.DataFrame([{"Check": k, "Value": v} for k, v in M["consistency"].items()]), "consistency_checks", md=False)


# ----------------------------------------------------------------------------- PLOTS
@safe
def plots_missing(D, F):
    sub = "missing_values"
    co = pd.read_csv(OUT / "reports" / "column_overview.csv")
    # 01 xếp hạng missing
    c = co[co["Missing Percentage"] > 0].sort_values("Missing Percentage")
    fig, ax = plt.subplots(figsize=(10, 0.36 * len(c) + 2))
    ax.barh(c["Dataset"] + " . " + c["Column"], c["Missing Percentage"], color=[DS_COL[d] for d in c["Dataset"]])
    for i, v in enumerate(c["Missing Percentage"]):
        ax.text(v + 0.8, i, f"{v:.1f}%", va="center", fontsize=8)
    ax.set_xlim(0, 112); ax.set_xlabel("% giá trị thiếu (trên số dòng của dataset)")
    ax.set_title("Xếp hạng % missing của mọi cột có thiếu dữ liệu (màu = dataset)")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=DS_COL[d]) for d in DATASETS], labels=DATASETS, loc="lower right", fontsize=8)
    savefig(fig, sub, "mv_01_missing_ranking_all_columns")

    # 02 heatmap present/missing ở mức phim
    cols = ["production_budget", "global_gross", "domestic_gross", "international_gross", "opening_weekend_gross",
            "critic_score", "audience_score", "genre_ids", "director_ids", "production_company_ids", "release_date_ref", "imdb_id"]
    pres = F[cols].notna().astype(int)
    pres["_k"] = pres[cols[:7]].sum(axis=1)
    samp = pres.sample(2500, random_state=42).sort_values(["_k"] + cols[:7], ascending=False)
    fig, ax = plt.subplots(figsize=(10, 7.5))
    ax.imshow(samp[cols].values, aspect="auto", cmap=matplotlib.colors.ListedColormap(["#f2f2f2", C_MAIN]), interpolation="nearest")
    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("2.500 phim lấy mẫu ngẫu nhiên (seed=42), sắp theo độ đầy đủ"); ax.set_yticks([])
    ax.axvline(6.5, color="k", lw=0.8)
    ax.set_title("Missingness heatmap ở mức phim (xanh = có dữ liệu, xám = thiếu)")
    savefig(fig, sub, "mv_02_missingness_heatmap_films")

    # 03 completeness
    comp = F[MONEY + SCORES].notna().sum(axis=1).value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(comp.index, comp.values, color=C_MAIN)
    for k, v in comp.items():
        ax.text(k, v, f"{v:,}\n{v / len(F) * 100:.1f}%", ha="center", va="bottom", fontsize=8)
    ax.set_xlabel("Số biến (trong 7 biến: 5 tiền + 2 điểm RT) có dữ liệu"); ax.set_ylabel("Số phim")
    ax.set_ylim(0, comp.max() * 1.15); ax.set_title("Mức độ đầy đủ của từng phim trên 7 biến tài chính + điểm")
    savefig(fig, sub, "mv_03_film_completeness")

    # 04 upset pattern
    pat = pd.DataFrame({"budget": F.production_budget.notna(), "global_gross": F.global_gross.notna(), "dom/intl/open": F.has_det_val,
                        "critic": F.critic_score.notna(), "audience": F.audience_score.notna()})
    upset(pat, list(pat.columns), "Tổ hợp biến CÓ dữ liệu (top 12 / 32 tổ hợp có thể)", "mv_04_upset_data_presence", sub)

    # 05 rt_status
    rt = F.copy()
    rt["sc"] = np.select([rt.critic_score.notna() & rt.audience_score.notna(), rt.critic_score.isna() & rt.audience_score.notna(),
                          rt.critic_score.notna() & rt.audience_score.isna()], ["critic + audience", "chỉ audience", "chỉ critic"], "không có điểm")
    ct = pd.crosstab(rt.rt_status, rt.sc)[["critic + audience", "chỉ audience", "chỉ critic", "không có điểm"]]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ct.plot(kind="barh", stacked=True, ax=ax, color=["#2e86c1", "#85c1e9", "#f5b041", "#cccccc"])
    for i, (idx, r) in enumerate(ct.iterrows()):
        ax.text(r.sum() * 1.01, i, f"{r.sum():,}", va="center", fontsize=9)
    ax.set_xlabel("Số phim"); ax.set_ylabel("rt_status"); ax.set_xlim(0, ct.sum(axis=1).max() * 1.12)
    ax.set_title("rt_status giải thích vì sao thiếu điểm: UNMATCHED / MATCHED_NO_SCORES / MATCHED")
    savefig(fig, sub, "mv_05_rt_status_vs_scores")

    # 06 coverage vs vote_count + vote dist
    cov = pd.DataFrame(M["coverage_by_vote"])
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.2))
    for v, col in zip(["production_budget", "global_gross", "critic_score", "audience_score"], ["#4c72b0", "#dd8452", "#55a868", "#c44e52"]):
        axs[0].plot(cov.vgroup, cov[v], marker="o", label=v, color=col)
    ax2 = axs[0].twinx(); ax2.bar(cov.vgroup, cov["share %"], alpha=0.15, color="k"); ax2.set_ylabel("% phim trong nhóm (cột xám)"); ax2.set_ylim(0, 100); ax2.grid(False)
    axs[0].set_xlabel("vote_count (nhóm)"); axs[0].set_ylabel("% phim CÓ dữ liệu"); axs[0].legend(); axs[0].set_title("Độ phủ dữ liệu tăng mạnh theo mức độ nổi tiếng (tính lại từ dữ liệu)")
    dfp = []
    for v in ["production_budget", "global_gross", "critic_score"]:
        t = F[["vote_count"]].copy(); t["Có dữ liệu"] = np.where(F[v].notna(), "có", "thiếu"); t["biến"] = v; dfp.append(t)
    dfp = pd.concat(dfp); dfp["log10(vote+1)"] = np.log10(dfp.vote_count + 1)
    sns.boxplot(data=dfp, x="biến", y="log10(vote+1)", hue="Có dữ liệu", ax=axs[1], palette=["#4c72b0", "#bbbbbb"], hue_order=["có", "thiếu"], fliersize=1)
    axs[1].set_title("Phân phối vote_count: phim có vs thiếu dữ liệu"); axs[1].set_xlabel("")
    savefig(fig, sub, "mv_06_missingness_vs_popularity")

    # 07 coverage theo thể loại
    g = pd.DataFrame(M["genre_cov"]).sort_values("budget")
    fig, ax = plt.subplots(figsize=(9, 6))
    y = np.arange(len(g)); h = 0.28
    ax.barh(y - h, g.budget, h, label="có production_budget", color="#4c72b0")
    ax.barh(y, g.gross, h, label="có global_gross", color="#dd8452")
    ax.barh(y + h, g.critic, h, label="có critic_score", color="#55a868")
    ax.set_yticks(y); ax.set_yticklabels([f"{r['name']} ({int(r['n']):,})" for _, r in g.iterrows()], fontsize=8)
    ax.set_xlabel("% phim có dữ liệu"); ax.legend(loc="lower right", fontsize=8)
    ax.set_title("Độ phủ dữ liệu theo thể loại (tên TMDB chuẩn; n = số phim có thể loại đó)")
    savefig(fig, sub, "mv_07_coverage_by_genre")


@safe
def plots_numeric(D, F):
    sub = "numerical_distributions"
    pal = dict(zip(MONEY, sns.color_palette("tab10", 5)))
    # 01 ECDF
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    for c in MONEY:
        s = np.sort(F[c].dropna().values); s = s[s > 0]
        ax.plot(s, np.arange(1, len(s) + 1) / len(s), label=f"{c} (n={len(s):,})", color=pal[c])
    ax.set_xscale("log"); ax.set_xlabel("USD (thang log10 - chỉ để vẽ)"); ax.set_ylabel("Phân vị tích lũy")
    ax.axvline(1000, color="grey", ls="--", lw=0.8); ax.text(1100, 0.02, "1.000 USD", fontsize=8, color="grey")
    ax.legend(fontsize=8); ax.set_title("ECDF của 5 biến tiền tệ: phần đuôi trái (< 1.000 USD) và dải giá trị rất rộng")
    savefig(fig, sub, "num_01_ecdf_money")
    # 02 mean/median + skew raw vs log
    ns = pd.DataFrame(M["num"]).T.loc[MONEY]
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
    axs[0].bar(range(5), ns["Mean/Median"].astype(float), color=C_MAIN)
    for i, (a, b) in enumerate(zip(ns["Mean/Median"].astype(float), ns["P99/Median"].astype(float))):
        axs[0].text(i, a, f"{a:.1f}x\n(P99/Med {b:.0f}x)", ha="center", va="bottom", fontsize=8)
    axs[0].set_xticks(range(5)); axs[0].set_xticklabels([c.replace("_", "\n") for c in MONEY], fontsize=8)
    axs[0].set_ylabel("Mean / Median"); axs[0].set_ylim(0, ns["Mean/Median"].astype(float).max() * 1.2); axs[0].set_title("Mean bị kéo bởi đuôi phải")
    w = 0.38
    axs[1].bar(np.arange(5) - w / 2, ns["Skewness"].astype(float), w, label="Skewness (thang gốc)", color=C_WARN)
    axs[1].bar(np.arange(5) + w / 2, ns["Skew(log10)"].astype(float), w, label="Skewness (log10)", color="#27ae60")
    axs[1].axhline(0, color="k", lw=0.8); axs[1].set_xticks(range(5)); axs[1].set_xticklabels([c.replace("_", "\n") for c in MONEY], fontsize=8)
    axs[1].legend(); axs[1].set_title("Độ lệch trước và sau log10 (tính tạm, không đổi dữ liệu)")
    savefig(fig, sub, "num_02_mean_median_skew")
    # 03 KDE log
    fig, ax = plt.subplots(figsize=(10, 5))
    for c in MONEY:
        s = np.log10(F[c].dropna().clip(lower=1))
        sns.kdeplot(s, ax=ax, label=f"{c} (median={10 ** s.median():,.0f})", color=pal[c], bw_adjust=0.8)
    ax.set_xlabel("log10(USD)"); ax.set_ylabel("Mật độ"); ax.legend(fontsize=8)
    ax.set_title("KDE trên thang log10: đỉnh chính + 'đuôi trái' của các giá trị rất nhỏ")
    savefig(fig, sub, "num_03_kde_log_money")
    # 04 score heaping
    fig, axs = plt.subplots(1, 3, figsize=(17, 4.8), gridspec_kw={"width_ratios": [1.2, 1.2, 0.8]})
    for ax, c, col in zip(axs[:2], SCORES, [C_WARN, "#6c5b9e"]):
        s = F[c].dropna().astype(int)
        vc = s.value_counts().reindex(range(101), fill_value=0)
        ax.bar(vc.index, vc.values, color=col, width=0.9)
        for v in (0, 100):
            ax.text(v, vc[v], f"{vc[v]:,}", ha="center", va="bottom", fontsize=8, fontweight="bold")
        ax.set_xlabel(f"{c} (bin = 1 điểm)"); ax.set_ylabel("Số phim"); ax.set_title(f"{c}: n={len(s):,} - tụ ở 0, 100 và số tròn")
    e = pd.DataFrame({"critic_score": [M["critic_score_edges"]["mult10_pct"], M["critic_score_edges"]["hundred_pct"]],
                      "audience_score": [M["audience_score_edges"]["mult10_pct"], M["audience_score_edges"]["hundred_pct"]]}, index=["bội số của 10", "đúng = 100"])
    e.plot(kind="bar", ax=axs[2], color=[C_WARN, "#6c5b9e"], rot=0)
    axs[2].axhline(10, color="grey", ls="--", lw=0.8); axs[2].text(0.55, 10.5, "kỳ vọng ~10% nếu đều", fontsize=8, color="grey")
    axs[2].set_ylabel("% phim có điểm"); axs[2].set_title("Dồn cụm (heaping)")
    savefig(fig, sub, "num_04_score_heaping")
    # 05 vote_count
    v = F.vote_count
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
    axs[0].hist(np.log10(v + 1), bins=60, color=C_MAIN)
    axs[0].set_xlabel("log10(vote_count + 1)"); axs[0].set_ylabel("Số phim")
    axs[0].set_title(f"vote_count: {(v == 0).mean() * 100:.1f}% phim có 0 vote (median={v.median():.0f}, mean={v.mean():.0f})")
    sv = np.sort(v.values)[::-1]; cs = np.cumsum(sv) / sv.sum()
    axs[1].plot(np.arange(1, len(sv) + 1) / len(sv) * 100, cs * 100, color=C_ALT)
    for p in (1, 5, 10):
        k = int(len(sv) * p / 100); axs[1].scatter([p], [cs[k - 1] * 100], color="k", zorder=3); axs[1].text(p + 1, cs[k - 1] * 100 - 5, f"top {p}% = {cs[k - 1] * 100:.0f}%", fontsize=8)
    axs[1].set_xlabel("% phim (xếp từ nhiều vote nhất)"); axs[1].set_ylabel("% tổng vote tích lũy"); axs[1].set_title("Mức độ tập trung vote_count")
    savefig(fig, sub, "num_05_vote_count_concentration")


@safe
def plots_outliers(D, F):
    sub = "outliers"
    # 01 low values
    ph = M["placeholder"]
    fig, axs = plt.subplots(1, 3, figsize=(17, 5))
    x = np.arange(5); w = 0.27
    for k, (key, lab, col) in enumerate([("lt1000", "< 1.000", "#f5b041"), ("lt100", "< 100", "#e67e22"), ("lt10", "< 10", C_WARN)]):
        axs[0].bar(x + (k - 1) * w, [ph[c][key] for c in MONEY], w, label=f"giá trị {lab} USD", color=col)
    axs[0].set_xticks(x); axs[0].set_xticklabels([c.replace("_", "\n") for c in MONEY], fontsize=8); axs[0].set_ylabel("Số phim")
    axs[0].legend(fontsize=8); axs[0].set_title("Giá trị nhỏ bất thường theo biến")
    b = F.dropna(subset=["production_budget", "global_gross"])
    low = b.production_budget < 1000
    axs[1].scatter(b.production_budget[~low], b.global_gross[~low], s=4, alpha=0.25, color="#999999", label="budget ≥ 1.000")
    axs[1].scatter(b.production_budget[low], b.global_gross[low], s=14, color=C_WARN, label=f"budget < 1.000 (n={low.sum()})")
    axs[1].set_xscale("log"); axs[1].set_yscale("log"); axs[1].set_xlabel("production_budget (USD, log)"); axs[1].set_ylabel("global_gross (USD, log)")
    axs[1].legend(fontsize=8); axs[1].set_title("Phim budget < 1.000 USD: global_gross cũng rất nhỏ (cùng thang) - không giống lỗi đơn vị triệu USD")
    hv = pd.DataFrame({"production_budget": [ph["production_budget"]["mult_1e6"], ph["production_budget"]["mult_1e5"]],
                       "global_gross": [ph["global_gross"]["mult_1e6"], ph["global_gross"]["mult_1e5"]]}, index=["bội số 1 triệu", "bội số 100 nghìn"])
    hv.plot(kind="bar", ax=axs[2], rot=0, color=[C_MAIN, C_ALT]); axs[2].set_ylabel("% giá trị non-null"); axs[2].set_title("Số tròn (làm tròn) trong ngân sách vs doanh thu")
    savefig(fig, sub, "out_01_low_values_and_rounding")
    # 02 ratio
    ratio = (b.global_gross / b.production_budget)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.hist(np.log10(ratio), bins=80, color=C_MAIN)
    ax.axvline(0, color=C_WARN, ls="--"); ax.text(0.05, ax.get_ylim()[1] * 0.9, f"gross = budget\n({M['ratio']['gross_lt_budget']:,}/{M['ratio']['n']:,} phim có gross < budget)", color=C_WARN, fontsize=9)
    ax.set_xlabel("log10(global_gross / production_budget)"); ax.set_ylabel("Số phim")
    ax.set_title(f"Tỷ lệ doanh thu/ngân sách (n={len(ratio):,}): đuôi cực đoan hai phía ({M['ratio']['gt100']} phim > 100x; {M['ratio']['lt_0_001']} phim < 0,001x)")
    savefig(fig, sub, "out_02_gross_budget_ratio")
    # 03 IQR raw vs log
    ns = pd.DataFrame(M["num"]).T.loc[MONEY]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    n = ns["Count"].astype(float)
    ax.bar(np.arange(5) - 0.2, ns["IQR outliers high"].astype(float) / n * 100, 0.4, label="Cao - quy tắc IQR trên thang gốc", color=C_WARN)
    ax.bar(np.arange(5) + 0.2, ns["Log-IQR outliers high"].astype(float) / n * 100, 0.4, label="Cao - IQR trên log10", color="#27ae60")
    ax.bar(np.arange(5) + 0.2, ns["Log-IQR outliers low"].astype(float) / n * 100, 0.4, bottom=ns["Log-IQR outliers high"].astype(float) / n * 100, label="Thấp - IQR trên log10", color="#f5b041")
    ax.set_xticks(range(5)); ax.set_xticklabels([c.replace("_", "\n") for c in MONEY], fontsize=8); ax.set_ylabel("% phim bị gắn cờ")
    ax.legend(fontsize=8); ax.set_title("Outlier theo IQR: thang gốc (bom tấn) khác thang log (giá trị quá nhỏ)")
    savefig(fig, sub, "out_03_iqr_outliers_raw_vs_log")
    # 04 top giá trị
    top = F[MONEY].apply(lambda s: s.dropna().sort_values(ascending=False).head(1).iloc[0])
    rows = []
    for c in MONEY:
        tt = F.loc[F[c].nlargest(3).index, ["title", c]]
        for _, r in tt.iterrows():
            rows.append({"Column": c, "Title": r["title"], "Value": r[c]})
    save_table(pd.DataFrame(rows), "top_values_check")
    # box score ngoài biên
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for c, col in zip(SCORES, [C_WARN, "#6c5b9e"]):
        t = F.groupby(pd.cut(F[c], [-1, 0, 20, 40, 60, 80, 99, 100])).vote_count.median()
        ax.plot(range(len(t)), t.values, marker="o", label=c, color=col)
    ax.set_xticks(range(7)); ax.set_xticklabels(["=0", "1-20", "21-40", "41-60", "61-80", "81-99", "=100"]); ax.set_yscale("log")
    ax.set_xlabel("Khoảng điểm"); ax.set_ylabel("Median vote_count (TMDB, log)"); ax.legend()
    ax.set_title("Điểm RT ở biên (0/100) gắn với phim ít vote hơn? (vote_count là của TMDB, không phải số review RT)")
    savefig(fig, sub, "out_04_score_extremes_vs_votes")


@safe
def plots_categorical(D, F):
    sub = "categorical"
    gc = M["cnt_genre_ids"]
    g = pd.Series({TMDB_GENRE.get(int(k), k): v for k, v in gc.items()}).sort_values()
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(g.index, g.values, color=C_MAIN)
    for i, v in enumerate(g.values):
        ax.text(v, i, f" {v:,} ({v / g.sum() * 100:.1f}%)", va="center", fontsize=8)
    ax.set_xlim(0, g.max() * 1.2); ax.set_xlabel("Số lần xuất hiện của thể loại"); ax.set_title("19 genre_id (tên theo TMDB chuẩn) - tần suất token (một phim có nhiều thể loại)")
    savefig(fig, sub, "cat_01_genre_frequency")
    # 02 tokens per cell
    m = D["movies_raw"]
    fig, axs = plt.subplots(1, 4, figsize=(18, 4))
    for ax, col, lab in zip(axs, ["genre_ids", "director_ids", "production_company_ids", "lead_cast_ids_superset"], ["thể loại", "đạo diễn", "hãng SX", "diễn viên chính"]):
        s = m[col].dropna().str.split("|").str.len()
        ax.hist(s, bins=np.arange(0.5, min(s.max(), 40) + 1.5), color=C_ALT)
        ax.set_title(f"{col}\nmedian={s.median():.0f}, max={s.max()}, thiếu={m[col].isna().mean() * 100:.1f}%", fontsize=10)
        ax.set_xlabel(f"Số {lab} / ô"); ax.set_ylabel("Số phim")
    savefig(fig, sub, "cat_02_multivalue_cells")
    # 03 tập trung
    fig, ax = plt.subplots(figsize=(10, 5.2))
    for col, lab, colr in [("director_ids", "đạo diễn", "#4c72b0"), ("production_company_ids", "hãng sản xuất", "#dd8452"), ("lead_cast_ids_superset", "diễn viên chính", "#55a868")]:
        cnt = np.sort(np.array(list(M[f"cnt_{col}"].values())))[::-1]
        cs = np.cumsum(cnt) / cnt.sum()
        ax.plot(np.arange(1, len(cnt) + 1) / len(cnt) * 100, cs * 100, label=f"{lab} ({len(cnt):,} id)", color=colr)
        k = max(1, int(len(cnt) * 0.01)); ax.scatter([1], [cs[k - 1] * 100], color=colr, zorder=3)
        ax.text(2, cs[k - 1] * 100 - 4, f"top 1% = {cs[k - 1] * 100:.0f}% lượt", fontsize=8, color=colr)
    ax.set_xlabel("% id (xếp từ phổ biến nhất)"); ax.set_ylabel("% lượt xuất hiện tích lũy"); ax.legend(); ax.set_title("Mức độ tập trung của các trường đa trị (đuôi dài)")
    savefig(fig, sub, "cat_03_concentration")
    # 04 collection
    cc = m["tmdb_collection_id"].value_counts()
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
    axs[0].hist(cc.values, bins=np.logspace(0, np.log10(cc.max()) + 0.05, 40), color=C_MAIN); axs[0].set_xscale("log"); axs[0].set_yscale("log")
    axs[0].set_xlabel("Số phim / tmdb_collection_id (log)"); axs[0].set_ylabel("Số nhóm (log)")
    axs[0].set_title(f"{len(cc):,} nhóm; median={cc.median():.0f}; {(cc == 1).sum()} nhóm 1 phim; max={cc.max()}")
    top = cc.head(10)
    axs[1].barh([str(int(i)) for i in top.index][::-1], top.values[::-1], color=C_ALT)
    axs[1].set_title("10 collection lớn nhất (theo id)"); axs[1].set_xlabel("Số phim")
    savefig(fig, sub, "cat_04_collection_sizes")
    # 05 combos + title dup
    s = m.genre_ids.dropna().apply(lambda x: "|".join(sorted(x.split("|"), key=int)))
    top = s.value_counts().head(15)
    names = [" + ".join(TMDB_GENRE.get(int(t), t) for t in c.split("|")) for c in top.index]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(names[::-1], top.values[::-1], color=C_MAIN)
    ax.set_xlabel("Số phim"); ax.set_title(f"Top 15 tổ hợp thể loại (chuẩn hóa thứ tự tạm thời): {s.nunique():,} tổ hợp khác nhau vs {m.genre_ids.nunique():,} chuỗi gốc")
    savefig(fig, sub, "cat_05_genre_combinations")
    # 06 credits
    cr = D["credits_raw"]
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.6))
    rc = cr.role.value_counts(); axs[0].bar(rc.index, rc.values, color=[C_MAIN, C_ALT])
    for i, v in enumerate(rc.values):
        axs[0].text(i, v, f"{v:,}", ha="center", va="bottom")
    axs[0].set_title("credits_raw: số dòng theo role"); axs[0].set_ylabel("Số dòng")
    d = cr[cr.role == "director"].groupby(KEY).size(); c = cr[cr.role == "cast"].groupby(KEY).size()
    axs[1].hist(c.clip(upper=80), bins=40, color=C_MAIN); axs[1].set_title(f"cast / phim (median={c.median():.0f}, max={c.max()})"); axs[1].set_xlabel("Số diễn viên (cắt ở 80)")
    vc = d.clip(upper=6).value_counts().sort_index(); axs[2].bar(vc.index.astype(str).str.replace("6", "≥6"), vc.values, color=C_ALT)
    axs[2].set_title(f"director / phim (max={d.max()}; {M['no_dir_films']:,} phim có credits nhưng không có đạo diễn)", fontsize=10); axs[2].set_xlabel("Số đạo diễn")
    savefig(fig, sub, "cat_06_credits_roles")


@safe
def plots_dates(D, F):
    sub = "dates"
    y = F.year.dropna().astype(int).value_counts().sort_index()
    y = y[y.index >= 1890]
    fig, ax = plt.subplots(figsize=(13, 4.8))
    ax.bar(y.index, y.values, color=[C_WARN if i > 2026 else C_MAIN for i in y.index], width=0.85)
    ax.axvline(2026.5, color="k", ls="--", lw=0.8); ax.text(2025.8, y.max() * 0.93, f"retrieval_date = 2026-10-22\n{M['date']['after_retrieval']} phim có ngày sau mốc này", ha="right", fontsize=9)
    ax.set_xlabel("Năm phát hành (release_date_ref)"); ax.set_ylabel("Số phim"); ax.set_title(f"Số phim theo năm phát hành (min {M['date']['min']}, max {M['date']['max']}; {M['date']['missing']} phim thiếu ngày)")
    savefig(fig, sub, "date_01_films_per_year")
    # 02 coverage by decade
    d = pd.DataFrame(M["decade_cov"]); d = d[(d.decade >= 1910) & (d.decade <= 2020)]
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.bar(d.decade, d.n, width=7, color="#cccccc"); ax.set_ylabel("Số phim (cột xám)"); ax.set_xlabel("Thập niên")
    ax2 = ax.twinx(); ax2.grid(False)
    for c, col in [("budget", "#4c72b0"), ("global_gross", "#dd8452"), ("critic", "#55a868"), ("audience", "#c44e52"), ("detail", "#8172b3")]:
        ax2.plot(d.decade, d[c], marker="o", label=f"% có {c}", color=col)
    ax2.set_ylabel("% phim có dữ liệu"); ax2.set_ylim(0, 60); ax2.legend(fontsize=8, loc="upper left")
    ax.set_title("Độ phủ dữ liệu theo thập niên (tính lại): không 'tăng vọt' sau 2000; thập niên 2020 giảm")
    savefig(fig, sub, "date_02_coverage_by_decade")
    # 03 jan 1
    dt = F.release_dt.dropna()
    j = pd.DataFrame({"year": dt.dt.year, "jan1": (dt.dt.month == 1) & (dt.dt.day == 1)})
    jj = j.groupby("year").agg(n=("jan1", "size"), r=("jan1", "mean")); jj = jj[(jj.n >= 30) & (jj.index >= 1900)]
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.8))
    axs[0].plot(jj.index, jj.r * 100, color=C_WARN, marker=".")
    axs[0].axhline(100 / 365, color="k", ls="--", lw=0.8); axs[0].text(jj.index.min(), 100 / 365 + 0.5, "kỳ vọng nếu đều: 0,27%", fontsize=8)
    axs[0].set_xlabel("Năm (n ≥ 30 phim)"); axs[0].set_ylabel("% phim có ngày = 01-01"); axs[0].set_title(f"Dồn cụm ngày 01-01: {M['date']['jan1']:,} phim ({M['date']['jan1_pct_dated']}% phim có ngày)")
    mo = F.release_month.dropna().astype(int).value_counts().sort_index()
    axs[1].bar(mo.index, mo.values, color=C_MAIN); axs[1].set_xticks(range(1, 13)); axs[1].set_xlabel("release_month"); axs[1].set_ylabel("Số phim"); axs[1].set_title("Phân bố theo tháng (tháng 1 bị thổi phồng bởi ngày 01-01)")
    savefig(fig, sub, "date_03_jan1_heaping_and_month")
    # 04 trend
    t = F.dropna(subset=["year"]).groupby("year").agg(n_b=("production_budget", "count"), b=("production_budget", "median"),
                                                      n_g=("global_gross", "count"), g=("global_gross", "median"))
    t = t[(t.index >= 1980) & (t.index <= 2026)]
    fig, ax = plt.subplots(figsize=(12, 5))
    tb, tg = t[t.n_b >= 20], t[t.n_g >= 20]
    ax.plot(tb.index, tb.b, marker="o", label="median production_budget (năm có ≥ 20 phim)", color="#4c72b0")
    ax.plot(tg.index, tg.g, marker="s", label="median global_gross (năm có ≥ 20 phim)", color="#dd8452")
    ax.set_yscale("log"); ax.set_xlabel("Năm phát hành"); ax.set_ylabel("USD danh nghĩa (log)"); ax.legend(); ax.set_title("Xu hướng median theo năm (danh nghĩa, chưa điều chỉnh lạm phát; mẫu có dữ liệu bị thiên lệch)")
    savefig(fig, sub, "date_04_nominal_median_trend")


@safe
def plots_corr(D, F):
    sub = "correlations"
    # 01 budget vs gross
    b = F.dropna(subset=["production_budget", "global_gross"])
    fig, ax = plt.subplots(figsize=(8.5, 7))
    hb = ax.hexbin(b.production_budget.clip(lower=1), b.global_gross.clip(lower=1), xscale="log", yscale="log", gridsize=45, mincnt=1, cmap="Blues", bins="log")
    lim = [1, 3e9]; ax.plot(lim, lim, color=C_WARN, ls="--", lw=1, label="gross = budget")
    ax.set_xlabel("production_budget (USD, log)"); ax.set_ylabel("global_gross (USD, log)"); plt.colorbar(hb, label="log10(số phim)")
    c = M["corr"]["production_budget|global_gross"]
    ax.set_title(f"Budget vs Global gross (n={len(b):,}): Spearman={c['Spearman']:.2f}, Pearson(log)={c['Pearson(log10)']:.2f}"); ax.legend()
    savefig(fig, sub, "cor_01_budget_vs_global_gross")
    # 02 opening vs domestic, intl vs global
    fig, axs = plt.subplots(1, 3, figsize=(18, 5.4))
    for ax, (a, bb, la, lb) in zip(axs, [("opening_weekend_gross", "domestic_gross", "opening_weekend_gross", "domestic_gross"),
                                         ("domestic_gross", "international_gross", "domestic_gross", "international_gross"),
                                         ("international_gross", "global_gross", "international_gross", "global_gross")]):
        s = F.dropna(subset=[a, bb]); ax.scatter(s[a], s[bb], s=5, alpha=0.3, color=C_MAIN)
        lim = [max(1, min(s[a].min(), s[bb].min())), max(s[a].max(), s[bb].max())]; ax.plot(lim, lim, color=C_WARN, ls="--", lw=1)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel(f"{la} (USD, log)"); ax.set_ylabel(f"{lb} (USD, log)")
        c = M["corr"].get(f"{a}|{bb}") or M["corr"][f"{bb}|{a}"]; ax.set_title(f"{a} vs {bb}\nn={len(s):,}, Spearman={c['Spearman']:.2f}, Pearson(log)={c['Pearson(log10)']:.2f}", fontsize=10)
    savefig(fig, sub, "cor_02_gross_family_scatter")
    # 03 critic vs audience
    s = F.dropna(subset=SCORES)
    fig, ax = plt.subplots(figsize=(7.5, 7))
    hb = ax.hexbin(s.critic_score, s.audience_score, gridsize=30, cmap="Purples", mincnt=1, bins="log"); plt.colorbar(hb, label="log10(số phim)")
    ax.plot([0, 100], [0, 100], color=C_WARN, ls="--", lw=1)
    c = M["corr"]["critic_score|audience_score"]
    ax.set_xlabel("critic_score"); ax.set_ylabel("audience_score"); ax.set_title(f"Critic vs Audience (n={len(s):,}): Pearson={c['Pearson']:.2f}, Spearman={c['Spearman']:.2f}")
    savefig(fig, sub, "cor_03_critic_vs_audience")
    # 04 điểm vs doanh thu (box theo bin)
    fig, axs = plt.subplots(1, 2, figsize=(14, 5))
    for ax, sc in zip(axs, SCORES):
        s = F.dropna(subset=[sc, "global_gross"]).copy()
        s["bin"] = pd.cut(s[sc], [-1, 20, 40, 60, 80, 100], labels=["0-20", "21-40", "41-60", "61-80", "81-100"])
        s["log_gross"] = np.log10(s.global_gross.clip(lower=1))
        sns.boxplot(data=s, x="bin", y="log_gross", ax=ax, color="#9ec5e8", fliersize=1.5)
        ax.set_xlabel(sc); ax.set_ylabel("log10(global_gross)")
        c = M["corr"][f"{sc}|global_gross"]; ax.set_title(f"{sc} vs global_gross (n={len(s):,}) - Spearman={c['Spearman']:.2f}")
    savefig(fig, sub, "cor_04_scores_vs_gross_binned")
    # 05 so sánh phương pháp
    cr = pd.read_csv(OUT / "reports" / "correlations.csv")
    cr = cr[cr["Var B"] != "critic_score"].copy(); cr["pair"] = cr["Var A"] + " ~ " + cr["Var B"]
    cr = cr.sort_values("Spearman")
    fig, ax = plt.subplots(figsize=(10, 0.45 * len(cr) + 2))
    y = np.arange(len(cr)); h = 0.27
    ax.barh(y - h, cr.Pearson, h, label="Pearson (gốc)", color="#4c72b0"); ax.barh(y, cr.Spearman, h, label="Spearman", color="#dd8452"); ax.barh(y + h, cr["Pearson(log10)"], h, label="Pearson (log10)", color="#55a868")
    ax.set_yticks(y); ax.set_yticklabels([f"{p} (n={int(n):,})" for p, n in zip(cr.pair, cr.n)], fontsize=8); ax.axvline(0, color="k", lw=0.8)
    ax.legend(fontsize=8); ax.set_xlabel("Hệ số tương quan (pairwise)"); ax.set_title("Pearson thang gốc vs Spearman vs Pearson(log10): thang đo ảnh hưởng kết luận")
    savefig(fig, sub, "cor_05_pearson_spearman_log")
    # 06 era + vote>=100
    b = F.dropna(subset=["production_budget", "global_gross", "year"]).copy()
    b["era"] = pd.cut(b.year, [1800, 1979, 1999, 2009, 2019, 2100], labels=["<1980", "1980-99", "2000-09", "2010-19", "2020+"])
    era = pd.DataFrame(M["era_corr"])
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
    axs[0].bar(era.era, era.spearman, color=C_MAIN)
    for i, (v, n) in enumerate(zip(era.spearman, era.n)):
        axs[0].text(i, v, f"{v:.2f}\n(n={int(n):,})", ha="center", va="bottom", fontsize=8)
    axs[0].set_ylim(0, 1); axs[0].set_ylabel("Spearman budget ~ global_gross"); axs[0].set_title("Tương quan ngân sách-doanh thu theo thời kỳ (kiểm tra tính ổn định)")
    v = pd.DataFrame(M["missing_vs_votes"])
    axs[1].bar(["≥ 100 vote", "toàn bộ mẫu", "sau khi bỏ giá trị < 1.000"], [M["corr_votes_ge100"]["spearman"], M["corr"]["production_budget|global_gross"]["Spearman"], M["corr_after_lowdrop"]["spearman"]], color=["#8172b3", C_MAIN, "#55a868"])
    axs[1].set_ylim(0, 1); axs[1].set_ylabel("Spearman budget ~ global_gross"); axs[1].set_title("Độ nhạy của tương quan với cách chọn mẫu (tính tạm, không sửa dữ liệu)")
    for i, v_ in enumerate([M["corr_votes_ge100"]["spearman"], M["corr"]["production_budget|global_gross"]["Spearman"], M["corr_after_lowdrop"]["spearman"]]):
        axs[1].text(i, v_, f"{v_:.2f}", ha="center", va="bottom")
    savefig(fig, sub, "cor_06_stability_checks")
    # 07 heatmap tương quan hạng (n pairs)
    cols = ["production_budget", "domestic_gross", "international_gross", "global_gross", "opening_weekend_gross", "critic_score", "audience_score", "vote_count"]
    sp = F[cols].corr(method="spearman", min_periods=30)
    npair = pd.DataFrame({a: {b_: int(F[[a, b_]].dropna().shape[0]) for b_ in cols} for a in cols})
    fig, ax = plt.subplots(figsize=(9.5, 7.5))
    ann = sp.round(2).astype(str) + "\n(n=" + npair.map(lambda x: f"{x:,}") + ")"
    sns.heatmap(sp, annot=ann, fmt="", cmap="coolwarm", vmin=-1, vmax=1, ax=ax, annot_kws={"fontsize": 7}, linewidths=0.5)
    ax.set_title("Ma trận Spearman (pairwise) kèm số cặp quan sát - n khác nhau giữa các ô")
    savefig(fig, sub, "cor_07_spearman_matrix_with_n")


@safe
def plots_cross(D, F):
    sub = "cross_dataset"
    ov = pd.DataFrame(M["overview"])
    fig, ax = plt.subplots(figsize=(10, 4.6))
    x = np.arange(len(ov)); ax.bar(x - 0.2, ov["Number of Rows"], 0.4, label="Số dòng", color="#999999"); ax.bar(x + 0.2, ov["Unique film_key"], 0.4, label="Số film_key duy nhất", color=C_MAIN)
    for i, (a, b) in enumerate(zip(ov["Number of Rows"], ov["Unique film_key"])):
        ax.text(i - 0.2, a, f"{a:,}", ha="center", va="bottom", fontsize=8); ax.text(i + 0.2, b, f"{b:,}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(ov.Dataset, fontsize=9); ax.set_yscale("log"); ax.set_ylabel("Số lượng (log)"); ax.legend()
    ax.set_title("Số dòng vs số film_key duy nhất: chỉ credits_raw là quan hệ 1-N")
    savefig(fig, sub, "xd_01_rows_vs_unique_keys")
    # 02 overlap ma trận 'có dữ liệu thực'
    sets = {"budget": F.production_budget.notna(), "global_gross": F.global_gross.notna(), "domestic": F.domestic_gross.notna(),
            "international": F.international_gross.notna(), "opening": F.opening_weekend_gross.notna(), "critic": F.critic_score.notna(),
            "audience": F.audience_score.notna(), "has credits": F.in_credits, "in detailed (row)": F.in_bo_det}
    keys = list(sets); mat = pd.DataFrame({a: {b: int((sets[a] & sets[b]).sum()) for b in keys} for a in keys})
    jac = pd.DataFrame({a: {b: (sets[a] & sets[b]).sum() / max(1, (sets[a] | sets[b]).sum()) for b in keys} for a in keys})
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(jac, annot=mat.map(lambda v: f"{v:,}"), fmt="", cmap="Blues", ax=ax, annot_kws={"fontsize": 8}, cbar_kws={"label": "Jaccard"})
    ax.set_title("Giao nhau giữa các tập phim 'có dữ liệu thực' (số = phim chung, màu = Jaccard)")
    savefig(fig, sub, "xd_02_informative_overlap_matrix")
    # 03 membership
    pat = F[["in_movies", "in_bo_raw", "in_bo_det", "in_credits", "in_rt"]].rename(columns={"in_movies": "movies_raw", "in_bo_raw": "box_office_raw", "in_bo_det": "box_office_detailed", "in_credits": "credits_raw", "in_rt": "rt_scores"})
    upset(pat, list(pat.columns), "Phim hiện diện (theo film_key) trong tổ hợp dataset nào", "xd_03_upset_key_membership", sub, topn=6)
    # 04 revenue overlap
    ro = M["rev_overlap"]
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    names = ["Cả global_gross\nvà dom/intl/open", "Chỉ global_gross", "Chỉ dom/intl/open\n(global thiếu)", "Không có gì"]
    vals = [ro["both"], ro["global_only"], ro["detail_only"], ro["neither"]]
    ax.bar(names, vals, color=["#27ae60", C_MAIN, C_ALT, "#cccccc"])
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:,}\n({v / len(F) * 100:.1f}%)", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, max(vals) * 1.15); ax.set_ylabel("Số phim"); ax.set_title("box_office_raw và box_office_detailed bổ sung cho nhau, không dư thừa")
    savefig(fig, sub, "xd_04_raw_vs_detailed_revenue")
    # 05 nhất quán
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.2))
    z = F.dropna(subset=["global_gross", "international_gross", "domestic_gross"])
    dev = ((z.domestic_gross + z.international_gross - z.global_gross) / z.global_gross)
    axs[0].hist(np.sign(dev) * np.log10(1 + dev.abs() * 100), bins=70, color=C_MAIN)
    axs[0].set_xlabel("sign(d)·log10(1 + 100·|d|),  d = (dom + intl − global) / global"); axs[0].set_ylabel("Số phim")
    c = M["consistency"]; axs[0].set_title(f"Độ lệch (dom+intl) so với global (n={c['n_all3']:,}): {c['sum_within_1pct']:,} trong ±1%; {c['sum_dev_gt_1pct']} lệch >1%", fontsize=10)
    s = F.dropna(subset=["global_gross", "international_gross"]); bad = s.international_gross > s.global_gross * 1.01
    axs[1].scatter(s.global_gross[~bad], s.international_gross[~bad], s=4, alpha=0.3, color="#999999")
    axs[1].scatter(s.global_gross[bad], s.international_gross[bad], s=10, color=C_WARN, label=f"international > global (n={bad.sum()})")
    lim = [10, 3e9]; axs[1].plot(lim, lim, color="k", ls="--", lw=0.8)
    axs[1].set_xscale("log"); axs[1].set_yscale("log"); axs[1].set_xlabel("global_gross (box_office_raw)"); axs[1].set_ylabel("international_gross (box_office_detailed)"); axs[1].legend(fontsize=8)
    axs[1].set_title("Mâu thuẫn logic giữa hai nguồn doanh thu")
    savefig(fig, sub, "xd_05_revenue_consistency")
    # 06 merge explosion
    steps = ["movies_raw", "+ box_office_raw", "+ box_office_detailed\n(left)", "+ rt_scores", "+ credits_raw\n(left, chưa gộp)", "credits gộp về\nmức phim (1 dòng/phim)"]
    vals = [len(F)] * 4 + [M["naive_rows"], len(F)]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.bar(steps, vals, color=[C_MAIN] * 4 + [C_WARN, "#27ae60"])
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, max(vals) * 1.15); ax.set_ylabel("Số dòng sau merge (mô phỏng trong bộ nhớ)")
    ax.set_title(f"Nguy cơ nhân dòng: join thẳng credits_raw → {M['naive_factor']}x dòng; tổng production_budget bị nhân {M['budget_sum_inflation']}x")
    savefig(fig, sub, "xd_06_merge_row_explosion")
    # 07 quan hệ bảng (sơ đồ)
    fig, ax = plt.subplots(figsize=(11, 5)); ax.axis("off")
    boxes = {"movies_raw\n39,871 | film_key (1)": (0.5, 0.5), "box_office_raw\n39,871 | 1-1": (0.12, 0.85), "rt_scores\n39,871 | 1-1": (0.88, 0.85),
             "box_office_detailed\n29,527 | 1-0..1": (0.12, 0.12), "credits_raw\n639,728 | 1-N (0..N)": (0.88, 0.12)}
    for t, (x, y) in boxes.items():
        ds = t.split("\n")[0]
        ax.text(x, y, t, ha="center", va="center", fontsize=10, bbox=dict(boxstyle="round,pad=0.5", fc=DS_COL.get(ds, "#cccccc"), alpha=0.25, ec=DS_COL.get(ds, "k")))
    for t in list(boxes)[1:]:
        (x, y) = boxes[t]; ax.annotate("", xy=(x + (0.5 - x) * 0.62, y + (0.5 - y) * 0.62), xytext=(x + (0.5 - x) * 0.30, y + (0.5 - y) * 0.30), arrowprops=dict(arrowstyle="<->", color="k"))
    ax.text(0.5, 0.02, f"{M['films_no_credits']:,} phim không có credits | {len(F) - int(F.in_bo_det.sum()):,} phim không có dòng chi tiết | 0 khóa mồ côi", ha="center", fontsize=9)
    ax.set_title("Quan hệ giữa 5 bảng qua film_key (1-1 ngoại trừ credits_raw)")
    savefig(fig, sub, "xd_07_table_relationship_diagram")
    # 08 upset informative
    pat2 = pd.DataFrame({"budget": F.production_budget.notna(), "global_gross": F.global_gross.notna(), "dom/intl/open": F.has_det_val,
                         "critic": F.critic_score.notna(), "audience": F.audience_score.notna(), "has credits": F.in_credits})
    upset(pat2, list(pat2.columns), "Mức độ phủ thông tin thực (non-null) giữa các nguồn - top 12 tổ hợp", "xd_08_upset_informative_sources", sub, color=C_ALT)


# ----------------------------------------------------------------------------- issue table
def issues_table():
    p, n = M["miss_pct"], M["num"]
    c, ph, d = M["consistency"], M["placeholder"], M["date"]
    mv = {r["Variable"]: r for r in M["missing_vs_votes"]}
    cov = {r["vgroup"]: r for r in M["coverage_by_vote"]}
    I = []
    A = I.append
    A(("DQ-01", "movies_raw, box_office_raw, box_office_detailed, rt_scores", "production_budget, global_gross, domestic_gross, international_gross, opening_weekend_gross, critic_score, audience_score",
       "Các biến tài chính và điểm RT thiếu rất nhiều (79,7%–91,9%; audience_score 71,5%)",
       f"budget {p['movies_raw.production_budget']}%; global {p['box_office_raw.global_gross']}%; domestic {p['box_office_detailed.domestic_gross']}%; intl {p['box_office_detailed.international_gross']}%; opening {p['box_office_detailed.opening_weekend_gross']}%; critic {p['rt_scores.critic_score']}%; audience {p['rt_scores.audience_score']}%. Chỉ {M['budget_and_gross']:,} phim có đồng thời budget+global ({M['budget_and_gross'] / 39871 * 100:.1f}%); {M['all4']:,} phim đủ 4 biến",
       "Mọi phân tích ROI/lợi nhuận chỉ áp dụng cho ~7% phim; không suy rộng được cho toàn catalog", "HIGH", "Chia 2 tập: Catalog (giữ 39.871 phim + cờ has_*) và Financial (complete-case). Không impute hàng loạt khi chưa quyết định nghiệp vụ", "Số phim mỗi tập khớp bảng theo dõi; mọi báo cáo ghi rõ n và tập mẫu", "Đã xác nhận"))
    A(("DQ-02", "tất cả (liên bảng)", "vote_count ~ missingness",
       "Missingness gắn chặt với mức độ nổi tiếng (vote_count): phim nhiều vote có dữ liệu hơn hẳn",
       f"Median vote phim CÓ budget={mv['production_budget']['Median vote (có)']:.0f} vs THIẾU={mv['production_budget']['Median vote (thiếu)']:.0f}; coverage budget từ {cov['0']['production_budget']}% (0 vote) lên {cov['1000+']['production_budget']}% (≥1000 vote); rank-biserial={mv['production_budget']['Rank-biserial']}",
       "Mẫu có dữ liệu là mẫu thiên lệch về phim phổ biến → kết luận không đại diện cho phim ít vote; loại trừ MCAR cho biến quan sát được nhưng chưa phân biệt được MAR vs MNAR", "HIGH", "Báo cáo kết quả theo phân tầng vote_count; kiểm tra độ nhạy; chỉ chọn mô hình impute sau khi thống nhất giả định", "So sánh phân phối vote_count/năm/thể loại giữa mẫu complete-case và catalog; ghi vào tài liệu giới hạn", "Đã xác nhận mối liên hệ; cơ chế chưa xác định"))
    A(("DQ-03", "box_office_detailed", "domestic_gross, international_gross, opening_weekend_gross",
       "Phần lớn dòng chỉ có film_key + imdb_id ('dòng vỏ rỗng')",
       f"{M['bd_empty']:,}/{M['bd_rows']:,} dòng ({M['bd_empty'] / M['bd_rows'] * 100:.2f}%) không có giá trị nào trong 3 cột doanh thu",
       "Đếm 'phim có doanh thu chi tiết' theo số dòng sẽ sai gấp ~4,5 lần; join làm tăng tưởng tượng về độ phủ", "MEDIUM", "Tạo cờ has_detail_values; đếm coverage theo giá trị non-null; giữ nguyên dòng ở nguồn", "Coverage báo cáo = 6.621 phim (29.527 − 22.906), không phải 29.527", "Đã xác nhận"))
    A(("DQ-04", "box_office_detailed", "theater_count", "Cột rỗng 100% (0 giá trị) - báo cáo cũ không ghi nhận (ghi 5 cột)",
       f"Missing {p['box_office_detailed.theater_count']}%; dtype float64; 0 giá trị duy nhất", "Không mang thông tin; làm sai tỷ lệ missing tổng của bảng (60,46% vs 52,55% khi bỏ cột này)", "LOW",
       "Đề xuất loại khỏi tập phân tích sau khi xác nhận với nguồn rằng không có dữ liệu", "Schema sau xử lý không còn cột rỗng; ghi lý do trong log", "Đã xác nhận"))
    A(("DQ-05", "movies_raw, box_office_raw, box_office_detailed", "production_budget, global_gross, international_gross",
       "Có nhiều giá trị tiền cực nhỏ (< 1.000 USD) khó phù hợp phim chiếu rạp thương mại; giả thuyết 'sai đơn vị' không được ủng hộ (gross cũng cực nhỏ), còn lại placeholder / phim vô danh - chưa chứng minh",
       f"budget <1000: {ph['production_budget']['lt1000']} (<100: {ph['production_budget']['lt100']}); global <1000: {ph['global_gross']['lt1000']}; intl <1000: {ph['international_gross']['lt1000']}; dom <1000: {ph['domestic_gross']['lt1000']}; opening <1000: {ph['opening_weekend_gross']['lt1000']}. Trong {M['lowbud_with_gross']['n_with_gross']} phim budget<1000 có global_gross, {M['lowbud_with_gross']['share_gross_ge_1e6']}% có global ≥ 1 triệu",
       "Làm sai ROI, log-transform (log10(1)=0), tạo đuôi trái nặng; tỷ lệ gross/budget có giá trị phi thực tế", "HIGH", "Gắn cờ (không xóa) → điều tra nguồn gốc (placeholder vs đơn vị) → quyết định sửa/loại/giữ theo từng nhóm", "Danh sách phim bị gắn cờ + kết luận từng nhóm; phân phối log10 không còn đuôi trái phi lý nếu có sửa", "Dấu hiệu bất thường - cần điều tra"))
    A(("DQ-06", "box_office_raw vs box_office_detailed", "global_gross vs international_gross/domestic_gross",
       "Hai nguồn doanh thu mâu thuẫn ở một số phim",
       f"intl > global (>1%): {c['intl_gt_global_1pct']}/{c['n_intl_global']:,}; domestic > global: {c['dom_gt_global_1pct']}/{c['n_dom_global']:,}; |dom+intl−global| > 1%: {c['sum_dev_gt_1pct']}/{c['n_all3']:,}; còn lại {c['sum_within_1pct']:,} khớp (median lệch {c['median_abs_dev']:.1e}); opening > domestic: {c['open_gt_dom']}",
       "Dùng nguồn nào cho 'doanh thu' sẽ thay đổi kết quả; tổng hợp dom+intl không thay thế được global ở mọi phim", "HIGH", "Chọn một nguồn chuẩn cho từng mục tiêu (cần quyết định nghiệp vụ); ghi cờ conflict_flag; không tự ghi đè", "Số phim conflict được liệt kê; quy tắc ưu tiên nguồn được phê duyệt bằng văn bản", "Đã xác nhận mâu thuẫn; nguyên nhân chưa xác định"))
    A(("DQ-07", "credits_raw ↔ movies_raw", "film_key", "Quan hệ 1-N: join trực tiếp làm nhân dòng và nhân bội các tổng",
       f"Left join movies→credits = {M['naive_rows']:,} dòng ({M['naive_factor']}x); tổng production_budget bị nhân {M['budget_sum_inflation']}x; {M['films_no_credits']:,} phim không có credits",
       "Sai tổng/trung bình, thiên lệch về phim có nhiều credits", "HIGH", "Gộp credits về mức phim (aggregate) TRƯỚC khi merge; kiểm tra rows_after == rows_before", "len(merged) == 39.871 và film_key duy nhất sau merge", "Rủi ro đã đo (mô phỏng)"))
    A(("DQ-08", "credits_raw", "(film_key, person_id, role), billing_order",
       "Cùng một người lặp trong cùng vai trò của cùng một phim (khác billing_order)",
       f"{M['cr_dup_fpr_rows_extra']:,} dòng dư ({M['cr_dup_fpr_roles']}); {M['cr_dup_billing_extra']} dòng trùng (film_key, billing_order) trong cast; billing_order thiếu 100% ở director (do thiết kế)",
       "Đếm cast_count bị thổi phồng; ảnh hưởng đặc trưng top-billed", "MEDIUM", "Điều tra mẫu → quy tắc giữ billing_order nhỏ nhất (cần xác nhận) trước khi khử trùng", "Không còn khóa (film_key, person_id, role) lặp; log dòng bị loại", "Đã xác nhận trùng; quy tắc xử lý cần quyết định"))
    A(("DQ-09", "movies_raw", "genre_ids, director_ids, lead_cast_ids_superset, production_company_ids",
       "Trường đa trị phân tách bằng '|' trong một ô; thứ tự không chuẩn hóa; chỉ có ID, không có tên",
       "; ".join(f"{r['Column']}: {r['Unique cell strings']:,} chuỗi/{r['Unique as sets']:,} tập, {r['Cells not numerically sorted %']}% ô không sắp thứ tự" for r in M["cat"]),
       "Group-by chuỗi ô sẽ tách cùng một tổ hợp thành nhiều nhóm; không thể đếm theo thể loại/đạo diễn nếu chưa explode", "MEDIUM", "Tách thành bảng quan hệ (movie-genre, movie-director, ...) trong bước chuẩn bị, không sửa cột gốc; cần bảng tra cứu tên", "Số token sau explode = tổng token đếm được; mọi id có trong bảng tra cứu", "Đã xác nhận"))
    A(("DQ-10", "movies_raw", "director_ids, lead_cast_ids_superset ↔ credits_raw",
       "director_ids là thông tin có thể suy ra từ credits_raw (trùng 100%); lead_cast_ids_superset là tập con ≤ 20 diễn viên",
       f"director_ids non-null={M['dir_consistency']['movies_nonnull']:,}; khớp tập hợp với credits: {M['dir_consistency']['equal_sets']:,}/{M['dir_consistency']['both']:,}; max lead cast={M['lead_vs_cast']['max_lead']}",
       "Nguy cơ dùng trùng hai nguồn cho cùng một thông tin; lead_cast bị cắt ≤ 20", "LOW", "Chọn credits_raw làm nguồn chuẩn cho đạo diễn/diễn viên (đề xuất); giữ movies_raw cho kiểm tra chéo", "Sau aggregate: số đạo diễn khớp giữa hai nguồn", "Đã xác nhận (đối chiếu)"))
    A(("DQ-11", "movies_raw", "release_date_ref, release_month",
       "Ngày thiếu, ngày ở tương lai so với thời điểm thu thập và dồn cụm ngày 01-01",
       f"Thiếu {d['missing']} ({p['movies_raw.release_date_ref']}%); {d['after_retrieval']} phim sau 2026-10-22 ({d['year_ge_2027']} phim từ năm 2027); 01-01: {d['jan1']:,} phim = {d['jan1_pct_dated']}% (kỳ vọng ~{d['expected_pct']}%); trong phim tương lai có budget={M['future_with_fin']['with_budget']}, global={M['future_with_fin']['with_global']}",
       "Phân tích theo năm/tháng sai; 01-01 có thể là ngày mặc định khi chỉ biết năm; phim chưa phát hành không nên có doanh thu", "MEDIUM", "Gắn cờ date_is_jan1, date_after_retrieval, date_missing; thống nhất cách xử lý theo mục tiêu phân tích", "Cờ khớp số đếm EDA; phân tích theo tháng loại 01-01 hoặc ghi chú", "Đã xác nhận (nguyên nhân 01-01 là giả thuyết)"))
    A(("DQ-12", "movies_raw + box_office + rt_scores", "release_date_ref, tiền tệ",
       "Thiên lệch thời gian và giá trị danh nghĩa (chưa điều chỉnh lạm phát)",
       f"{d['pre1980']:,} phim trước 1980 ({d['pre1980_pct_dated']}% phim có ngày) với coverage budget ≤ 9% ở các thập niên trước 1980; coverage không tăng vọt sau 2000 mà ổn định ~10–14% và giảm ở 2020s",
       "So sánh doanh thu giữa các thập niên theo USD danh nghĩa sai lệch", "MEDIUM", "Quyết định nghiệp vụ: có cần quy đổi theo CPI không (cần nguồn CPI ngoài dataset); lọc/phân tầng theo thập niên", "Tài liệu ghi rõ danh nghĩa/thực; phân tầng theo era", "Đã xác nhận quan sát; cần quyết định"))
    A(("DQ-13", "rt_scores", "critic_score, audience_score, rt_status, rt_url",
       "Thiếu điểm có nhiều ý nghĩa khác nhau (không tìm thấy trên RT / có trang nhưng không có điểm)",
       f"rt_status: {M['rt_status']}; rt_url thiếu = {M['rt_url_missing_equals_unmatched_or_search']:,} (UNMATCHED + SEARCH_ONLY)",
       "Gộp mọi NaN thành một loại sẽ lẫn 'chưa khớp' với 'khớp nhưng chưa có điểm'", "MEDIUM", "Giữ rt_status làm biến phân loại trạng thái; tách các nhóm missing khi báo cáo", "Mỗi NaN của điểm được gán một trong các nguyên nhân từ rt_status", "Đã xác nhận"))
    A(("DQ-14", "rt_scores", "critic_score",
       "Điểm dồn ở biên 0/100 (phim ít review - giả thuyết)",
       f"critic=0: {M['critic_score_edges']['zero']}; critic=100: {M['critic_score_edges']['hundred']} ({M['critic_score_edges']['hundred_pct']}%); bội số của 10: {M['critic_score_edges']['mult10_pct']}% (kỳ vọng ~10%); median vote_count (TMDB) ở biên {M['critic_edge_vote_median']:.0f} vs {M['critic_mid_vote_median']:.0f} ở giữa",
       "Điểm biên kém tin cậy; không có số review RT để kiểm chứng", "LOW", "Thu thập thêm số lượng review nếu có nguồn; trước mắt gắn cờ score_at_boundary", "Cờ khớp số đếm; ghi giới hạn trong báo cáo", "Dấu hiệu - cần dữ liệu bổ sung"))
    A(("DQ-15", "box_office_detailed", "domestic_gross, opening_weekend_gross",
       "Đa cộng tuyến rất cao giữa các biến doanh thu (đặc tính dữ liệu, không phải lỗi)",
       f"Spearman domestic~opening = {M['corr']['domestic_gross|opening_weekend_gross']['Spearman']:.2f}; VIF (log10, n={M['vif_n']:,}): domestic {M['vif']['domestic_gross']}, opening {M['vif']['opening_weekend_gross']}",
       "Hệ số hồi quy bất ổn nếu đưa cả hai vào mô hình tuyến tính", "MEDIUM", "Chọn một biến hoặc dùng chính quy hóa/PCA ở bước mô hình hóa (không xử lý ở bước làm sạch)", "VIF < 5 trên bộ biến cuối cùng", "Đã xác nhận (đặc tính)"))
    A(("DQ-16", "movies_raw", "tmdb_collection_id",
       "Gần như mọi phim đều có collection id; ý nghĩa của trường chưa rõ",
       f"{M['collection']['films_with']:,}/39.871 phim có giá trị; {M['collection']['n_groups']:,} nhóm; median {M['collection']['median']:.0f} phim/nhóm; {M['collection']['singletons']} nhóm 1 phim; max {M['collection']['max']}",
       "Nếu dùng làm nhóm nhượng quyền (franchise) mà ý nghĩa là khác → sai kết luận", "MEDIUM", "Xác minh định nghĩa trường với người thu thập dữ liệu; kiểm tra thủ công mẫu nhóm lớn nhất", "Biên bản xác nhận ý nghĩa; kiểm tra ngẫu nhiên 30 nhóm", "Cần điều tra"))
    A(("DQ-17", "movies_raw", "title", "Title trùng giữa các phim khác nhau; 1 nhóm trùng cả title lẫn ngày",
       f"{M['title_dup_rows']:,} dòng có title trùng; {M['title_samedate_groups']} nhóm cùng title + cùng ngày; {M['title_nonascii_pct']}% title có ký tự phi-ASCII",
       "Không được dùng title làm khóa; chuẩn hóa tên tùy tiện có thể gộp nhầm", "LOW", "Dùng film_key làm định danh; điều tra thủ công nhóm cùng title+ngày", "film_key vẫn duy nhất; danh sách nhóm nghi trùng được xem xét", "Đã xác nhận / nghi vấn nhỏ"))
    A(("DQ-18", "movies_raw, box_office_raw, credits_raw, rt_scores", "source, retrieval_date, market_scope, budget_missing_flag, missing_flag",
       "Cột hằng số hoặc cờ dư thừa so với null",
       f"Cột có ≤1 giá trị duy nhất: {M['const_cols']}; budget_missing_flag và missing_flag khớp 100% với trạng thái null của budget/global_gross",
       "Không thêm thông tin; rủi ro hiểu nhầm cờ là biến dự báo", "LOW", "Giữ làm metadata truy vết; loại khỏi tập đặc trưng khi mô hình hóa", "Không còn cột hằng số trong tập phân tích", "Đã xác nhận"))
    A(("DQ-19", "BAO_CAO cũ", "số liệu thống kê trong báo cáo phiên bản trước",
       "Một số số liệu của báo cáo cũ không khớp dữ liệu thật", "Xem bảng 'Đối chiếu báo cáo cũ' (reports/old_report_discrepancies.csv)",
       "Kết luận dựa trên số liệu sai có thể dẫn quyết định sai", "HIGH", "Chỉ dùng số liệu của phiên bản này; giữ nguyên file cũ để đối chiếu", "Mọi số liệu trong báo cáo mới truy được tới reports/*.csv", "Đã xác nhận"))
    df = pd.DataFrame(I, columns=["ID", "Dataset", "Column / Key", "Finding", "Evidence", "Potential Impact", "Priority", "Recommended Action", "Validation Criteria", "Status"])
    save_table(df, "data_quality_issues", md=False)
    short = df[["ID", "Dataset", "Column / Key", "Finding", "Priority", "Status"]]
    (OUT / "reports" / "md" / "issues_summary.md").write_text(md_table(short), encoding="utf-8")
    # bảng đầy đủ dạng markdown (ngắn gọn từng ô)
    (OUT / "reports" / "md" / "issues_full.md").write_text(md_table(df.drop(columns=["Status"]).assign(Status=df["Status"])), encoding="utf-8")


def old_report_diff():
    n = M["num"]
    old = [("production_budget", "Median", 5_000_000, n["production_budget"]["Median"]), ("production_budget", "Mean", 24_161_424, n["production_budget"]["Mean"]),
           ("global_gross", "Median", 2_578_414, n["global_gross"]["Median"]), ("global_gross", "Mean", 16_738_450, n["global_gross"]["Mean"]),
           ("critic_score", "Median", 67, n["critic_score"]["Median"]), ("critic_score", "Mean", 61.6, n["critic_score"]["Mean"]),
           ("audience_score", "Median", 61, n["audience_score"]["Median"]), ("audience_score", "Mean", 59.4, n["audience_score"]["Mean"]),
           ("box_office_detailed", "Số cột", 5, 6), ("box_office_detailed", "% ô trống", 52.55, 60.46),
           ("credits_raw", "Max dòng/phim", 451, M["credits_per_film_max"]),
           ("movies_raw", "% phim có vote 100-999 có budget", 51.2, [r for r in M["coverage_by_vote"] if r["vgroup"] == "100-999"][0]["production_budget"]),
           ("movies_raw", "% phim có vote 1-9 có budget", 3.2, [r for r in M["coverage_by_vote"] if r["vgroup"] == "1-9"][0]["production_budget"]),
           ("movies_raw", "% phim 10-99 vote có budget", 15.4, [r for r in M["coverage_by_vote"] if r["vgroup"] == "10-99"][0]["production_budget"]),
           ("movies_raw", "Tỷ lệ phim vote 1-9", 31.4, [r for r in M["coverage_by_vote"] if r["vgroup"] == "1-9"][0]["share %"]),
           ("movies_raw", "Tỷ lệ phim vote ≥1000", 3.8, [r for r in M["coverage_by_vote"] if r["vgroup"] == "1000+"][0]["share %"]),
           ("rt_scores", "% phim critic_score = 100", 11.4, M['critic_score_edges']['hundred_pct'])]
    rows = []
    for ds, met, o, new in old:
        if isinstance(o, int) and isinstance(new, (int, np.integer)):
            ok = o == new
        else:
            ok = abs(float(o) - float(new)) <= max(0.005 * abs(float(new)), 0.06)
        rows.append({"Dataset/Biến": ds, "Chỉ số": met, "Báo cáo cũ": fmt(o) if not isinstance(o, int) else f"{o:,}", "Tính lại": fmt(new) if not isinstance(new, (int, np.integer)) else f"{int(new):,}", "Khớp?": "Khớp" if ok else "KHÔNG KHỚP"})
    save_table(pd.DataFrame(rows), "old_report_discrepancies")


# ----------------------------------------------------------------------------- main
def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/mnt/project")
    ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parent.parent))
    a = ap.parse_args()
    OUT = Path(a.out_dir).resolve()
    if OUT == Path(a.data_dir).resolve():
        sys.exit("out-dir không được trùng data-dir (bảo vệ dữ liệu gốc)")
    (OUT / "reports" / "md").mkdir(parents=True, exist_ok=True)
    for s in ["missing_values", "numerical_distributions", "outliers", "categorical", "dates", "correlations", "cross_dataset"]:
        (OUT / "plots" / s).mkdir(parents=True, exist_ok=True)
    D = load(a.data_dir)
    if len(D) < len(DATASETS):
        sys.exit(f"Thiếu dataset: {set(DATASETS) - set(D)}")
    F = build_master(D)
    overview(D); duplicates_and_keys(D, F); numeric_stats(D, F); categorical_stats(D, F); date_stats(D, F)
    missing_mechanism(F); relationships(F)
    for fn in (plots_missing, plots_numeric, plots_outliers, plots_categorical, plots_dates, plots_corr, plots_cross):
        fn(D, F)
    issues_table(); old_report_diff()
    # lưu metrics
    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items() if not str(k).startswith("cnt_")}
        if isinstance(o, (list, tuple)):
            return [clean(x) for x in o]
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        return o
    (OUT / "reports" / "metrics.json").write_text(json.dumps(clean(M), ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("Hoàn tất. Biểu đồ:", len(M.get("plots", [])), "| Lỗi:", M["errors"])


if __name__ == "__main__":
    main()
