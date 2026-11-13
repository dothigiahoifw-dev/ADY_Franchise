"""RQ1 Task 3 - ham dung chung: nap du lieu dev, bieu dien feature, OLS, CV ngoai fold theo franchise, metric.
KHONG doc file test. Khong ngau nhien (khong seed)."""
import hashlib, json, os, datetime
import numpy as np, pandas as pd

FORBIDDEN_IN_X = {'Y', 'open_curr', 'transition_id', 'franchise_id', 'film_key_prev', 'film_key_curr', 'role', 'fold', 'mau_chinh', 'quality_flag_any'}
FOLDS = [1, 2, 3, 4]
CORE_RAW = ['log_open_prev', 'gap_years', 'franchise_position_n', 'release_month_n', 'release_year_n']

def build_X(df, feats, rep=None):
    """feats: nhom feature trong {'lop','gap','pos','season','year'}. Bieu dien ban dau theo Task 2 muc 7.1."""
    rep = rep or {}
    cols, names = [], []
    for f in feats:
        if f == 'lop':
            cols.append(df['log_open_prev'].values); names.append('log_open_prev')
        elif f == 'gap':
            assert rep.get('gap', 'ln') == 'ln'
            cols.append(np.log(df['gap_years'].values)); names.append('ln_gap_years')
        elif f == 'pos':
            assert rep.get('pos', 'ln') == 'ln'
            cols.append(np.log(df['franchise_position_n'].values)); names.append('ln_franchise_position_n')
        elif f == 'season':
            m = df['release_month_n'].values
            cols += [np.sin(2 * np.pi * m / 12), np.cos(2 * np.pi * m / 12)]; names += ['sin_month', 'cos_month']
        elif f == 'year':
            cols.append((df['release_year_n'].values - 2000) / 10.0); names.append('year_c10')
        else:
            raise ValueError(f)
    X = np.column_stack(cols)
    assert not (set(names) & FORBIDDEN_IN_X), names
    assert np.isfinite(X).all(), 'X khong huu han'
    return X, names

CONFIGS = {'E0': ['lop'], 'E1': ['lop', 'gap'], 'E2': ['lop', 'pos'], 'E3': ['lop', 'season', 'year'], 'E4': ['lop', 'gap', 'pos', 'season', 'year']}
COMPLEXITY = {'E0': 0, 'E1': 1, 'E2': 1, 'E3': 2, 'E4': 3}

def ols_fit(X, y):
    A = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return beta
def ols_pred(beta, X): return beta[0] + X @ beta[1:]

def cv_predict(dev, feats, rep=None, train_mask=None):
    X, names = build_X(dev, feats, rep)
    y = dev['Y'].values
    pred = np.full(len(dev), np.nan); coefs = []
    for k in FOLDS:
        tr = (dev['fold'].values != k)
        if train_mask is not None: tr = tr & train_mask
        te = dev['fold'].values == k
        beta = ols_fit(X[tr], y[tr]); pred[te] = ols_pred(beta, X[te])
        coefs.append(dict(fold=k, n_train=int(tr.sum()), intercept=beta[0], **{n: b for n, b in zip(names, beta[1:])}))
    assert np.isfinite(pred).all()
    return pred, pd.DataFrame(coefs)

def baseline_predict(dev, which, train_mask=None):
    y = dev['Y'].values; pred = np.full(len(dev), np.nan)
    for k in FOLDS:
        tr = (dev['fold'].values != k)
        if train_mask is not None: tr = tr & train_mask
        te = dev['fold'].values == k
        pred[te] = 0.0 if which == 'Y0' else float(np.median(y[tr]))
    return pred

def pct(v): return 100.0 * (np.exp(v) - 1.0)

def metrics_row(name, d, pred, n_params=None):
    y = d['Y'].values; e = y - pred; ae = np.abs(e)
    py, pp = pct(y), pct(pred)
    assert np.isfinite(py).all() and np.isfinite(pp).all(), 'pp khong huu han'
    ape = np.abs(py - pp)
    fo = d['fold'].values
    foldm = {k: float(ae[fo == k].mean()) for k in FOLDS}
    fr = pd.Series(ae).groupby(d['franchise_id'].values).mean()
    r = dict(model=name, n=len(d), n_params=n_params, pooled_mae=float(ae.mean()), rmse=float(np.sqrt((e ** 2).mean())),
             mean_fold_mae=float(np.mean(list(foldm.values()))), sd_fold_mae=float(np.std(list(foldm.values()), ddof=1)),
             franchise_mean_mae=float(fr.mean()), pp_mae_mean=float(ape.mean()), pp_mae_median=float(np.median(ape)))
    for k in FOLDS: r[f'fold{k}_mae'] = foldm[k]
    for lab, mk in (('ge1M', d['mau_chinh'].values), ('lt1M', ~d['mau_chinh'].values)):
        r[f'mae_{lab}'] = float(ae[mk].mean()); r[f'n_{lab}'] = int(mk.sum())
    return r

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for c in iter(lambda: fh.read(1 << 20), b''): h.update(c)
    return h.hexdigest()
def now_utc(): return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

class Log:
    def __init__(self, path): self.path = path; self.rows = []
    def add(self, stage, event, detail=''):
        self.rows.append(dict(time_utc=now_utc(), stage=stage, event=event, detail=str(detail)))
    def save(self): pd.DataFrame(self.rows).to_csv(self.path, index=False)

def select_config(table):
    """Quy tac Task 2 muc 7.3 (thuc hanh, khong phai kiem dinh thong ke)."""
    steps = []
    e0 = table.loc[table.model == 'E0', 'pooled_mae'].iloc[0]
    cand = table[table.model.isin(['E1', 'E2', 'E3', 'E4'])].copy()
    cand['eligible'] = (cand.pooled_mae < e0) & (cand.folds_better_vs_E0 >= 3)
    ok = cand[cand.eligible]
    if ok.empty:
        steps.append('Khong cau hinh nao dat (MAE gop < E0 va thap hon E0 o >= 3/4 fold) -> giu E0'); return 'E0', steps, cand
    best = ok.sort_values('pooled_mae').iloc[0]
    steps.append(f"Nhom dat: {ok.model.tolist()}; MAE thap nhat: {best.model} ({best.pooled_mae:.4f})")
    cur = best.model
    while True:
        cur_mae = ok.loc[ok.model == cur, 'pooled_mae'].iloc[0]
        simpler = ok[(ok.model.map(COMPLEXITY) < COMPLEXITY[cur]) & (ok.pooled_mae - cur_mae < 0.005)]
        if simpler.empty: break
        pick = simpler.assign(c=simpler.model.map(COMPLEXITY)).sort_values(['c', 'pooled_mae']).iloc[0].model
        steps.append(f"{pick} don gian hon {cur} va chi kem {ok.loc[ok.model == pick, 'pooled_mae'].iloc[0] - cur_mae:.4f} (< 0.005) -> chon {pick}")
        cur = pick
    steps.append(f'Cau hinh duoc chon: {cur}')
    return cur, steps, cand
