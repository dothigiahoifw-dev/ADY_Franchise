#!/usr/bin/env python3
"""ADY_PRJ RQ1 Task 2 - kiem tra du lieu, dung mau/split/registry, tai lap baseline.
Khong huan luyen model ung vien, khong cham test.
Dung:  python verify_task2.py --project DIR_chua_pairs_audit_va_master --split DIR_chua_split_va_baseline --out OUT_DIR
"""
import argparse, hashlib, json, os
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--project', default='/mnt/project')
ap.add_argument('--split', default='/home/claude/z')
ap.add_argument('--out', default='/mnt/user-data/outputs/task2_rq1/data')
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
V = {}                       # cac kiem tra VERIFIED (ten -> gia tri)

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for c in iter(lambda: fh.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

# ---------- 1. manifest ----------
expected = {
 'pairs_audit.csv': a.project, 'analysis_master_films.csv': a.project,
 'rq1_split_v2.csv': a.split, 'rq1_baseline_dev_preds_v2.csv': a.split,
 'analysis_master_transitions.csv': None, 'transitions_model_rq1.csv': None,
 'rq1_feature_policy.csv': None, 'feature_registry_transitions.csv': None,
 'ADY_DP_v3_3_relationship_and_attribute_report.md': None}
rows = []
for fn, d in expected.items():
    p = os.path.join(d, fn) if d else None
    if p and os.path.exists(p):
        df = pd.read_csv(p, encoding='utf-8-sig', low_memory=False)
        rows.append(dict(file=fn, received=True, sha256=sha(p), n_rows=len(df), n_cols=df.shape[1], bytes=os.path.getsize(p)))
    else:
        rows.append(dict(file=fn, received=False, sha256='', n_rows='', n_cols='', bytes=''))
MANIFEST_ROWS = rows

p = pd.read_csv(f'{a.project}/pairs_audit.csv', encoding='utf-8-sig', low_memory=False)
f = pd.read_csv(f'{a.project}/analysis_master_films.csv', encoding='utf-8-sig', low_memory=False)
s = pd.read_csv(f'{a.split}/rq1_split_v2.csv')
b = pd.read_csv(f'{a.split}/rq1_baseline_dev_preds_v2.csv')


# ================= CONG KIEM TRA (FAIL -> DUNG, khong ghi output khac) =================
EXPECT = dict(n=918, dev=725, test=193, folds={0: 193, 1: 178, 2: 185, 3: 176, 4: 186}, flagged_dev=6)
TOL = 1e-9
CH = []
def chk(cid, desc, ok, detail=''):
    CH.append(dict(id=cid, description=desc, status='PASS' if bool(ok) else 'FAIL', critical=True, detail=str(detail)))
for fn in ['pairs_audit.csv', 'analysis_master_films.csv', 'rq1_split_v2.csv', 'rq1_baseline_dev_preds_v2.csv']:
    chk('G00_' + fn, f'file nguon ton tai: {fn}', next(r['received'] for r in rows if r['file'] == fn))
_e = p[p.y_eligible]
_g = f.set_index('film_key')
chk('G01', 'transition_id trong split duy nhat', s.transition_id.is_unique)
chk('G02', 'tap ID split == tap y_eligible cua pairs_audit', set(s.transition_id) == set(_e.transition_id), f'split={len(s)} eligible={len(_e)}')
chk('G03', 'so dong mau/dev/test dung thiet ke (918/725/193)', (len(s), int((s.role == 'dev').sum()), int((s.role != 'dev').sum())) == (EXPECT['n'], EXPECT['dev'], EXPECT['test']), (len(s), s.role.value_counts().to_dict()))
chk('G04', 'so dong theo fold dung thiet ke', {int(k): int(v) for k, v in s.fold.value_counts().items()} == EXPECT['folds'], s.fold.value_counts().sort_index().to_dict())
chk('G05', 'dev = fold 1-4, test = fold 0', bool((s[s.role == 'dev'].fold.between(1, 4)).all() and (s[s.role != 'dev'].fold == 0).all()))
chk('G06', 'moi franchise dung 1 vai tro va 1 fold', s.groupby('franchise_id').role.nunique().max() == 1 and s.groupby('franchise_id').fold.nunique().max() == 1)
chk('G07', 'khong franchise chong lan dev/test', len(set(s[s.role == 'dev'].franchise_id) & set(s[s.role != 'dev'].franchise_id)) == 0)
_m = s.merge(_e[['transition_id', 'franchise_id', 'open_prev', 'open_curr', 'Y', 'gap_years', 'chain_pos_prev', 'chain_pos_curr', 'release_date_prev', 'release_date_curr', 'film_key_prev', 'film_key_curr']], on='transition_id', suffixes=('', '_p'))
chk('G08', 'franchise_id split == pairs_audit', bool((_m.franchise_id == _m.franchise_id_p).all()))
chk('G09', 'opening N-1 va N duong, huu han', bool((_m.open_prev > 0).all() and (_m.open_curr > 0).all() and np.isfinite(_m.Y).all()))
chk('G10', 'Y == ln(open_curr) - ln(open_prev) (tol 1e-12)', np.abs(_m.Y - (np.log(_m.open_curr) - np.log(_m.open_prev))).max() < 1e-12, np.abs(_m.Y - (np.log(_m.open_curr) - np.log(_m.open_prev))).max())
chk('G11', 'transition_id == film_key_prev__film_key_curr', bool((_m.transition_id == _m.film_key_prev + '__' + _m.film_key_curr).all()))
chk('G12', 'cap lien tiep: chain_pos_curr - chain_pos_prev == 1', bool(((_m.chain_pos_curr - _m.chain_pos_prev) == 1).all()))
_dd = (pd.to_datetime(_m.release_date_curr) - pd.to_datetime(_m.release_date_prev)).dt.days
chk('G13', 'ngay chieu N sau N-1 va gap_years = ngay/365.25 (tol 1e-12)', bool((_dd > 0).all()) and np.abs(_m.gap_years - _dd / 365.25).max() < 1e-12)
chk('G14', 'mau_chinh == (open_prev >= 1,000,000)', bool((_m.mau_chinh == (_m.open_prev >= 1e6)).all()))
chk('G15', 'opening trong pairs_audit khop analysis_master_films', bool(np.allclose(_g.loc[_m.film_key_prev, 'raw_box_office_detailed__opening_weekend_gross'].values, _m.open_prev.values) and np.allclose(_g.loc[_m.film_key_curr, 'raw_box_office_detailed__opening_weekend_gross'].values, _m.open_curr.values)))
_core_ok = _m[['open_prev', 'gap_years', 'chain_pos_curr', 'release_date_curr']].notna().all().all()
chk('G16', '5 feature loi khong thieu (open_prev, gap, vi tri, ngay chieu)', _core_ok)
_dev_ids = set(s[s.role == 'dev'].transition_id)
chk('G17', 'baseline file: dung 3 model x 725 dong dev, khong trung, khong co dong test',
    set(b.transition_id) == _dev_ids and b.groupby('model').size().eq(EXPECT['dev']).all() and not b.duplicated(['model', 'transition_id']).any() and b.model.nunique() == 3,
    b.groupby('model').size().to_dict())
_bm = b.merge(_m[['transition_id', 'Y', 'fold', 'mau_chinh']], on='transition_id', suffixes=('', '_s'))
chk('G18', 'baseline: Y, fold, mau_chinh khop split/pairs_audit', bool(np.allclose(_bm.Y, _bm.Y_s) and (_bm.fold == _bm.fold_s).all() and (_bm.mau_chinh == _bm.mau_chinh_s).all()))
chk('G19', 'baseline: ae_log == |Y - pred|', bool(np.allclose(b.ae_log, np.abs(b.Y - b.pred), atol=1e-9)))
_d = _m[_m.role == 'dev'].copy(); _d['x'] = np.log(_d.open_prev)
_bb = b.set_index(['model', 'transition_id'])
_mx = {}
for _n in ['Hồi quy log_open_prev', 'Median train', 'Y=0']:
    _w = 0.0
    for _k in (1, 2, 3, 4):
        _tr = _d[_d.fold != _k]; _te = _d[_d.fold == _k]
        _pr = np.zeros(len(_te)) if _n == 'Y=0' else (np.full(len(_te), _tr.Y.median()) if _n == 'Median train' else np.polyval(np.polyfit(_tr.x, _tr.Y, 1), _te.x))
        _w = max(_w, float(np.abs(_pr - _bb.loc[_n].loc[_te.transition_id, 'pred'].values).max()))
    _mx[_n] = _w
chk('G20', f'baseline v2 tai lap duoc khi fit tren moi dong dev cua fold con lai (sai lech < {TOL})', max(_mx.values()) < TOL, _mx)
_fl = _e[_e[['opening_low_warning_prev', 'opening_low_warning_curr', 'opening_inconsistent']].any(axis=1)].transition_id
chk('G21', 'so dong dev co co chat luong = 6 (S1)', len(set(_fl) & _dev_ids) == EXPECT['flagged_dev'], len(set(_fl) & _dev_ids))
_tbl = pd.DataFrame(CH)
print(_tbl[['id', 'status', 'description', 'detail']].to_string(index=False))
if (_tbl.status == 'FAIL').any():
    os.makedirs(a.out, exist_ok=True); _tbl.to_csv(f'{a.out}/checks_source.csv', index=False)
    print('\n*** FAIL: %d kiem tra quan trong khong dat. DUNG, khong ghi output nao khac. ***' % int((_tbl.status == 'FAIL').sum()))
    raise SystemExit(1)
_tbl.to_csv(f'{a.out}/checks_source.csv', index=False)
pd.DataFrame(MANIFEST_ROWS).to_csv(f'{a.out}/manifest_sources.csv', index=False)
print('\nTAT CA %d KIEM TRA QUAN TRONG: PASS' % len(_tbl))
# ================= HET CONG =================

# ---------- 2. funnel + loai tru ----------
V['pairs_audit_rows'] = len(p)
V['pairs_valid_ids_unique'] = bool(p.transition_id.dropna().is_unique)
V['films_master_key_unique'] = bool(f.film_key.is_unique)
tv = p[p.technically_valid]
el = p[p.y_eligible]
def fr(x): return int(x.franchise_id.nunique())
fun = [
 ('S0 cap phim ung vien trong pairs_audit', len(p), fr(p), ''),
 ('S1 technically_valid (cung collection, ke tiep, co ngay hop le, khong trung ngay, chua phat hanh)', len(tv), fr(tv), 'bo 4170 cap'),
 ('S2 co opening ca N-1 va N (y_eligible)', len(el), fr(el), 'bo 25025 cap thieu opening'),
 ('S3 co trong rq1_split_v2.csv', len(s), int(s.franchise_id.nunique()), ''),
]
pd.DataFrame(fun, columns=['stage','n_transitions','n_franchises','note']).to_csv(f'{a.out}/sample_funnel.csv', index=False)
ex = p[~p.y_eligible].copy()
ex['stage'] = np.where(ex.technically_valid, 'S2_opening_missing', 'S1_not_technically_valid')
ex['reason'] = np.where(ex.technically_valid, ex.y_ineligible_reason, ex.exclusion_reason)
ex[['film_key_prev','film_key_curr','transition_id','franchise_id','stage','reason']].to_csv(f'{a.out}/exclusions.csv', index=False)
V['exclusion_reasons_S1'] = ex[ex.stage=='S1_not_technically_valid'].reason.value_counts().to_dict()
V['exclusion_reasons_S2'] = ex[ex.stage=='S2_opening_missing'].reason.value_counts().to_dict()

# ---------- 3. kiem tra mau ----------
e = el.copy()
V['sample_ids_equal_split'] = set(e.transition_id) == set(s.transition_id)
V['transition_id_equals_prev__curr'] = bool((e.transition_id == e.film_key_prev + '__' + e.film_key_curr).all())
V['Y_recompute_max_abs_diff'] = float(np.abs(e.Y - (np.log(e.open_curr) - np.log(e.open_prev))).max())
V['openings_positive_finite'] = bool((e.open_prev > 0).all() and (e.open_curr > 0).all() and np.isfinite(e.Y).all())
V['chain_pos_diff_all_1'] = bool(((e.chain_pos_curr - e.chain_pos_prev) == 1).all())
dd = (pd.to_datetime(e.release_date_curr) - pd.to_datetime(e.release_date_prev)).dt.days
V['release_order_ok'] = bool((dd > 0).all())
V['gap_years_recompute_days_over_365.25_max_diff'] = float(np.abs(e.gap_years - dd / 365.25).max())
V['gap_min_days'] = int(dd.min())
V['film_reuse_as_curr_dup'] = int(e.film_key_curr.duplicated().sum())
V['franchise_prev_curr_same'] = bool((e.franchise_id == e.franchise_id_prev).all() and (e.franchise_id == e.franchise_id_curr).all())
g = f.set_index('film_key')
V['open_prev_equals_master'] = bool(np.allclose(g.loc[e.film_key_prev, 'raw_box_office_detailed__opening_weekend_gross'].values, e.open_prev.values))
V['open_curr_equals_master'] = bool(np.allclose(g.loc[e.film_key_curr, 'raw_box_office_detailed__opening_weekend_gross'].values, e.open_curr.values))
V['release_date_curr_equals_master'] = bool((pd.to_datetime(g.loc[e.film_key_curr, 'raw_movies__release_date_ref'].values) == pd.to_datetime(e.release_date_curr.values)).all())
fc = f[f.raw_movies__tmdb_collection_id.notna()].copy()
fc['rd'] = pd.to_datetime(fc.raw_movies__release_date_ref)
fc['rank'] = fc.groupby('raw_movies__tmdb_collection_id').rd.rank(method='min')
r = fc.set_index('film_key')['rank']
V['chain_pos_equals_independent_rank_by_date'] = bool((r.loc[e.film_key_curr].values == e.chain_pos_curr.values).all())
V['theater_count_nonmissing_prev_curr'] = [int(g.loc[e.film_key_prev, 'raw_box_office_detailed__theater_count'].notna().sum()),
                                          int(g.loc[e.film_key_curr, 'raw_box_office_detailed__theater_count'].notna().sum())]
flagcols = ['opening_low_warning_prev','opening_low_warning_curr','opening_inconsistent']
V['quality_flags_in_sample'] = {c: int(e[c].sum()) for c in flagcols}
V['comparability_status_values'] = e.comparability_status.value_counts().to_dict()
V['min_open_prev'] = float(e.open_prev.min()); V['min_open_curr'] = float(e.open_curr.min())
# co chat luong: khong loai, chi danh dau
e['qflag'] = e[flagcols].any(axis=1)

# ---------- 4. split ----------
sp = s.merge(e[['transition_id','film_key_prev','film_key_curr','open_prev','open_curr','Y','gap_years','chain_pos_curr',
                'release_date_prev','release_date_curr','qflag','opening_inconsistent','opening_low_warning_prev','opening_low_warning_curr']],
             on='transition_id', how='left')
V['split_rows'] = len(s); V['split_unique_ids'] = bool(s.transition_id.is_unique)
V['role_counts'] = s.role.value_counts().to_dict()
V['fold_counts'] = {int(k): int(v) for k, v in s.fold.value_counts().sort_index().items()}
V['one_role_per_franchise'] = int(s.groupby('franchise_id').role.nunique().max())
V['one_fold_per_franchise'] = int(s.groupby('franchise_id').fold.nunique().max())
V['dev_test_franchise_overlap'] = len(set(s[s.role=='dev'].franchise_id) & set(s[s.role!='dev'].franchise_id))
V['test_fold_is_0'] = bool((s[s.role!='dev'].fold == 0).all() and (s[s.role=='dev'].fold.between(1,4)).all())
V['mau_chinh_equals_open_prev_ge_1M'] = bool((s.mau_chinh == (sp.open_prev >= 1e6)).all())
tab = sp.groupby(['role','mau_chinh']).agg(n=('transition_id','size'), n_franchise=('franchise_id','nunique')).reset_index()
V['role_x_stratum'] = tab.to_dict('records')
V['dev_franchises'] = int(sp[sp.role=='dev'].franchise_id.nunique()); V['test_franchises'] = int(sp[sp.role!='dev'].franchise_id.nunique())
V['dev_stratum_overlap_franchises'] = len(set(sp[(sp.role=='dev')&sp.mau_chinh].franchise_id) & set(sp[(sp.role=='dev')&~sp.mau_chinh].franchise_id))
V['fold_x_stratum'] = sp[sp.role=='dev'].groupby(['fold','mau_chinh']).size().unstack().to_dict()
sizes = sp.groupby('franchise_id').size()
V['transitions_per_franchise_dev'] = sp[sp.role=='dev'].groupby('franchise_id').size().value_counts().sort_index().to_dict()

# ---------- 5. dac trung ung vien (cap transition) ----------
P, C = g.loc[e.film_key_prev].reset_index(drop=True), g.loc[e.film_key_curr].reset_index(drop=True)
def toset(x): return set(str(x).split('|')) if isinstance(x, str) and x != '' else None
def changed(a_, b_):
    A, B = toset(a_), toset(b_)
    return np.nan if A is None or B is None else float(A != B)
def jac(a_, b_):
    A, B = toset(a_), toset(b_)
    return np.nan if A is None or B is None or len(A | B) == 0 else len(A & B) / len(A | B)
F = pd.DataFrame({'transition_id': e.transition_id.values})
F['log_open_prev'] = np.log(e.open_prev.values)
F['gap_years'] = e.gap_years.values
F['franchise_position_n'] = e.chain_pos_curr.values
dt = pd.to_datetime(e.release_date_curr.values)
F['release_month_n'] = dt.month; F['release_year_n'] = dt.year
F['is_director_changed'] = [changed(x, y) for x, y in zip(P.raw_movies__director_ids, C.raw_movies__director_ids)]
F['studio_changed'] = [changed(x, y) for x, y in zip(P.raw_movies__production_company_ids, C.raw_movies__production_company_ids)]
F['genre_jaccard'] = [jac(x, y) for x, y in zip(P.raw_movies__genre_ids, C.raw_movies__genre_ids)]
F['production_budget_prev'] = P.raw_movies__production_budget.values
F['production_budget_curr'] = C.raw_movies__production_budget.values
F['critic_score_prev'] = P.raw_rt_scores__critic_score.values
F['audience_score_prev'] = P.raw_rt_scores__audience_score.values
F['vote_count_prev'] = P.raw_movies__vote_count.values; F['vote_count_curr'] = C.raw_movies__vote_count.values
def top5(x):
    return None if not isinstance(x, str) else x.split('|')[:5]
cr = []
for x, y in zip(P.credits__cast_person_ids, C.credits__cast_person_ids):
    A, B = top5(x), top5(y)
    cr.append(np.nan if A is None or B is None else len(set(A) & set(B)) / 5)
F['cast_retention_top5_diag'] = cr
F['theater_count_prev'] = P.raw_box_office_detailed__theater_count.values
F = F.merge(sp[['transition_id','role','mau_chinh']], on='transition_id')
dev = F.role == 'dev'
def cov(col, mask=None):
    x = F[col] if mask is None else F.loc[mask, col]
    return int(x.notna().sum()), len(x)
cov_rows = []
for c in [c for c in F.columns if c not in ('transition_id','role','mau_chinh')]:
    n_all, N = cov(c); n_dev, Nd = cov(c, dev)
    cov_rows.append(dict(column=c, nonmissing_918=n_all, nonmissing_dev=n_dev, n_dev=Nd,
                         miss_pct_918=round(100*(1-n_all/N),1), miss_pct_dev=round(100*(1-n_dev/Nd),1),
                         n_unique=int(F[c].nunique()), min=F[c].min(), max=F[c].max()))
pd.DataFrame(cov_rows).to_csv(f'{a.out}/feature_coverage_computed.csv', index=False)
V['feature_core_missing_918'] = {c: int(F[c].isna().sum()) for c in ['log_open_prev','gap_years','franchise_position_n','release_month_n','release_year_n']}
V['director_raw_equals_credits'] = bool((P.raw_movies__director_ids.fillna('') == P.credits__directors_person_ids.fillna('')).all())
V['snapshot_retrieval_dates'] = {'movies': f.raw_movies__retrieval_date.value_counts().to_dict(), 'rt': f.raw_rt_scores__retrieval_date.value_counts().to_dict(), 'credits': f.credits__retrieval_dates.dropna().value_counts().to_dict()}
V['max_release_date_curr'] = str(pd.to_datetime(e.release_date_curr).max().date())
V['core_pairwise_abs_corr_dev'] = None
core = F.loc[dev, ['log_open_prev','gap_years','franchise_position_n','release_month_n','release_year_n']].copy()
core['gap_years'] = np.log(core.gap_years); core['franchise_position_n'] = np.log(core.franchise_position_n)
cm = core.corr().abs().to_numpy(copy=True); np.fill_diagonal(cm, 0)
V['core_pairwise_abs_corr_dev'] = float(cm.max())

# ---------- 6. bang thanh vien mau + split ----------

sp['quality_flag_any'] = sp.qflag
sp['stratum_open_prev'] = np.where(sp.mau_chinh, 'open_prev>=1M', 'open_prev<1M')
sp['sample_role'] = 'MAIN_SAMPLE'
sp[['transition_id','franchise_id','film_key_prev','film_key_curr','role','fold','mau_chinh','stratum_open_prev','quality_flag_any','sample_role']].to_csv(f'{a.out}/sample_rq1_membership.csv', index=False)
sp[['transition_id','franchise_id','role','fold']].to_csv(f'{a.out}/split_assignment.csv', index=False)


# ---------- 6b. file dau vao tu du cho Task 3 (dev) va file test bi niem phong ----------
sp['quality_flag_any'] = sp.qflag
_cols_sp = ['transition_id','franchise_id','role','fold','mau_chinh','film_key_prev','film_key_curr','release_date_prev','release_date_curr',
            'open_prev','open_curr','Y','quality_flag_any','opening_low_warning_prev','opening_low_warning_curr','opening_inconsistent']
_cols_F = ['transition_id','log_open_prev','gap_years','franchise_position_n','release_month_n','release_year_n','is_director_changed','studio_changed','genre_jaccard']
INP = sp[_cols_sp].merge(F[_cols_F], on='transition_id').sort_values('transition_id').reset_index(drop=True)
INP[INP.role == 'dev'].to_csv(f'{a.out}/rq1_inputs_dev.csv', index=False)
INP[INP.role != 'dev'].to_csv(f'{a.out}/rq1_inputs_test_LOCKED.csv', index=False)
_w = b.pivot(index='transition_id', columns='model', values='pred').rename(columns={'Y=0': 'pred_Y0', 'Median train': 'pred_median_train', 'Hồi quy log_open_prev': 'pred_reg_log_open_prev'}).reset_index()
_w = _w.merge(b[b.model == 'Y=0'][['transition_id', 'fold', 'mau_chinh', 'Y']], on='transition_id')
_w = _w[['transition_id', 'fold', 'mau_chinh', 'Y', 'pred_Y0', 'pred_median_train', 'pred_reg_log_open_prev']].sort_values('transition_id')
_w.to_csv(f'{a.out}/baseline_v2_dev_preds_wide.csv', index=False)
# doi chieu file wide voi file dai goc
_back = pd.read_csv(f'{a.out}/baseline_v2_dev_preds_wide.csv').melt(id_vars=['transition_id'], value_vars=['pred_Y0','pred_median_train','pred_reg_log_open_prev'], var_name='m', value_name='pred2')
_back['model'] = _back.m.map({'pred_Y0': 'Y=0', 'pred_median_train': 'Median train', 'pred_reg_log_open_prev': 'Hồi quy log_open_prev'})
_cmp = b.merge(_back, on=['transition_id', 'model'])
if len(_cmp) != len(b) or not np.allclose(_cmp.pred, _cmp.pred2):
    print('*** FAIL: file baseline wide khong khop file goc. DUNG. ***'); raise SystemExit(1)
_rd = pd.read_csv(f'{a.out}/rq1_inputs_dev.csv')
if len(_rd) != EXPECT['dev'] or (_rd.role != 'dev').any() or set(_rd.transition_id) != _dev_ids:
    print('*** FAIL: rq1_inputs_dev.csv sai tap dev. DUNG. ***'); raise SystemExit(1)
print('OK: rq1_inputs_dev.csv (%d), rq1_inputs_test_LOCKED.csv (%d), baseline_v2_dev_preds_wide.csv (%d)' % (len(_rd), len(INP) - len(_rd), len(_w)))

# ---------- 7. tai lap baseline (v2) ----------
d = sp[sp.role == 'dev'].copy(); d['x'] = np.log(d.open_prev)
bb = b.set_index(['model','transition_id'])
rep = {}
for name in ['Hồi quy log_open_prev','Median train','Y=0']:
    out = {}
    for fit_main in (False, True):
        mx = 0
        for k in (1,2,3,4):
            tr = d[(d.fold != k) & (d.mau_chinh if fit_main else True)]; te = d[d.fold == k]
            if name == 'Median train': pr = np.full(len(te), tr.Y.median())
            elif name == 'Y=0': pr = np.zeros(len(te))
            else: pr = np.polyval(np.polyfit(tr.x, tr.Y, 1), te.x)
            ref = bb.loc[name].loc[te.transition_id, 'pred'].values
            mx = max(mx, float(np.abs(pr - ref).max()))
        out['fit_on_train_rows_of_other_folds_all_strata' if not fit_main else 'fit_on_mau_chinh_only'] = mx
    rep[name] = out
V['baseline_reproduction_max_abs_pred_diff'] = rep
V['baseline_file_ae_equals_abs_Y_minus_pred'] = bool(np.allclose(b.ae_log, np.abs(b.Y - b.pred)))
V['baseline_Y_equals_pairs_audit_Y'] = bool(np.allclose(b.merge(sp[['transition_id','Y']], on='transition_id', suffixes=('','_p')).eval('Y-Y_p'), 0))
V['baseline_covers_dev_only'] = bool(set(b.transition_id) == set(sp[sp.role=='dev'].transition_id))
b2 = b.merge(sp[['transition_id','franchise_id']], on='transition_id')
rows = []
for m_, g_ in b2.groupby('model'):
    fold_mae = g_.groupby('fold').ae_log.mean()
    fr_mae = g_.groupby('franchise_id').ae_log.mean()
    rows.append(dict(model=m_, pooled_micro_mae=g_.ae_log.mean(), macro_fold_mean=fold_mae.mean(),
                     fold1=fold_mae[1], fold2=fold_mae[2], fold3=fold_mae[3], fold4=fold_mae[4],
                     franchise_mean_of_means=fr_mae.mean(),
                     mae_stratum_ge1M=g_[g_.mau_chinh].ae_log.mean(), mae_stratum_lt1M=g_[~g_.mau_chinh].ae_log.mean(),
                     rmse_pooled=float(np.sqrt((g_.ae_log**2).mean()))))
ref = pd.DataFrame(rows).round(4); ref.to_csv(f'{a.out}/baseline_v2_reference_metrics.csv', index=False)
pw = {}
names = ['Hồi quy log_open_prev','Median train','Y=0']
fm = {m_: b2[b2.model==m_].groupby('fold').ae_log.mean() for m_ in names}
for x_ in names:
    for y_ in names:
        if x_ != y_: pw[f'{x_} thap hon {y_} o so fold'] = int((fm[x_] < fm[y_]).sum())
V['baseline_pairwise_fold_wins_of_4'] = pw
V['baseline_reference'] = ref.to_dict('records')

# ---------- 8. xac nhan cac so Task 1 ----------
Y = sp.Y; Yd = sp[sp.role=='dev'].Y; Ym = sp[(sp.role=='dev') & sp.mau_chinh].Y
V['Y_all_918'] = dict(mean=float(Y.mean()), median=float(Y.median()), sd=float(Y.std()), min=float(Y.min()), max=float(Y.max()), skew=float(Y.skew()))
V['Y_dev_725'] = dict(mean=float(Yd.mean()), median=float(Yd.median()), sd=float(Yd.std()), min=float(Yd.min()), max=float(Yd.max()))
V['Y_dev_main_576'] = dict(share_neg=float((Ym<0).mean()), q01=float(Ym.quantile(.01)), q50=float(Ym.median()), q99=float(Ym.quantile(.99)), n_abs_gt3=int((Ym.abs()>3).sum()))
V['dev_main_open_curr_lt_1M'] = int((sp[(sp.role=='dev') & sp.mau_chinh].open_curr < 1e6).sum())
V['quality_flag_rows_by_role'] = sp.groupby('role').quality_flag_any.sum().to_dict()
V['quality_flag_dev_ids'] = sp[(sp.role=='dev') & sp.quality_flag_any].transition_id.tolist()

def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.bool_,)): return bool(o)
    return o
json.dump(clean(V), open(f'{a.out}/verified_numbers.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(clean(V), ensure_ascii=False, indent=1))
