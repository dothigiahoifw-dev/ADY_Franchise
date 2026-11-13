"""Engine bootstrap theo franchise (vector hoa) - cung phuong phap voi rq3_stats_helpers.py:
 - rut len(franchise) cum CO HOAN LAI tu TOAN BO franchise cua 'universe' (rng.integers, seed co dinh);
 - cum duoc chon m lan dong gop DU m ban sao (trong so = so lan chon);
 - trong so franchise 1/k_f tinh theo TUNG BAN SAO (k_f la so transition cua franchise trong nhom dang xet, khong bi gop khi duoc chon nhieu lan)
   => moi ban sao co tong trong so 1; transition cua franchise duoc chon m lan co trong so m/k_f;
 - phan vi theo quy tac nghich dao CDF cua helper (wquantile), trung binh tai diem hoa;
 - o rong trong mot lan lap -> NaN, bi bo khoi percentile cua o do va dem lai.
Kiem chung tung lan lap voi helper: xem code/00_validate_engine.py"""
import numpy as np


class Boot:
    def __init__(self, franchise_ids, B=10000, seed=20260101):
        self.fr = np.array(sorted(set(franchise_ids)))          # thu tu sort giong groupby(sort=True) cua helper
        self.F = len(self.fr)
        self.B = B
        rng = np.random.default_rng(seed)
        C = np.empty((B, self.F), dtype=np.int32)
        for b in range(B):
            C[b] = np.bincount(rng.integers(0, self.F, size=self.F), minlength=self.F)   # == cluster_bootstrap_indices cua helper
        self.C = C
        self.pos = {f: i for i, f in enumerate(self.fr)}


class Def:
    """Mot thong ke tren mot tap dong: kind in {'wq','lt0','gt0','eq0'}; weight in {'eq','fr'}."""
    def __init__(self, y, fid, kind, q=0.5, weight='eq'):
        self.y = np.asarray(y, float)
        self.fid = np.asarray(fid)
        self.kind, self.q, self.weight = kind, q, weight
        if weight == 'fr':
            s = {}
            for f in self.fid:
                s[f] = s.get(f, 0) + 1
            self.base = np.array([1.0 / s[f] for f in self.fid])
        else:
            self.base = np.ones(len(self.y))


def _wq_matrix(y, W, q):
    o = np.argsort(y, kind='mergesort')
    ys, Ws = y[o], W[:, o]
    cs = np.cumsum(Ws, axis=1)
    tot = cs[:, -1]
    out = np.full(W.shape[0], np.nan)
    ok = tot > 0
    Fm = np.where(ok[:, None], cs / np.where(ok, tot, 1)[:, None], 0)
    i = np.minimum((Fm >= q - 1e-12).argmax(axis=1), len(ys) - 1)
    out[ok] = ys[i[ok]]
    ar = np.arange(W.shape[0])
    tie = ok & (np.abs(Fm[ar, i] - q) <= 1e-12)
    for b in np.nonzero(tie)[0]:
        rest = Ws[b, i[b] + 1:] > 0
        if rest.any():
            j = i[b] + 1 + int(rest.argmax())
            out[b] = 0.5 * (ys[i[b]] + ys[j])
    return out


def stat_matrix(d, boot, C=None):
    """Tra ve vector (so hang cua C) gia tri thong ke cua Def d. C=None -> bootstrap day du; C=ones -> diem uoc luong."""
    if C is None:
        C = boot.C
    fi = np.array([boot.pos[f] for f in d.fid])
    W = C[:, fi].astype(float) * d.base[None, :]
    if d.kind == 'wq':
        return _wq_matrix(d.y, W, d.q)
    tot = W.sum(axis=1)
    mask = {'lt0': d.y < 0, 'gt0': d.y > 0, 'eq0': d.y == 0}[d.kind]
    return np.where(tot > 0, (W * mask[None, :]).sum(axis=1) / np.where(tot > 0, tot, 1), np.nan)


def point(d, boot):
    return float(stat_matrix(d, boot, C=np.ones((1, boot.F), dtype=np.int32))[0])


def run(defs, boot):
    """defs: dict name->Def. Tra ve (points dict, reps dict name->array(B))."""
    reps = {k: stat_matrix(d, boot) for k, d in defs.items()}
    pts = {k: point(d, boot) for k, d in defs.items()}
    return pts, reps


def ci(x, alpha=0.05):
    v = x[~np.isnan(x)]
    if len(v) == 0:
        return np.nan, np.nan, int(np.isnan(x).sum())
    return float(np.percentile(v, 100 * alpha / 2)), float(np.percentile(v, 100 * (1 - alpha / 2))), int(np.isnan(x).sum())
