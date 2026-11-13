"""ADY RQ3 Buoc 4 - ham dac ta (chua chay tren du lieu that). selftest() chi dung du lieu gia lap de kiem tra co hoc.
python rq3_stats_helpers.py  -> chay selftest."""
import numpy as np, pandas as pd

def wquantile(y, w, q):
    """Phan vi co trong so (quy tac nghich dao CDF, trung binh o diem hoa).
    Sap tang theo y; F_i = cumsum(w)/sum(w). Phan vi q = y_i dau tien co F_i >= q.
    Neu F_i == q (sai so 1e-12) thi lay trung binh (y_i, y_{i+1}).
    Voi trong so bang nhau, trung vi trung np.median; Q1/Q3 co the khac type 7 -> khi so sanh, tinh ca ban khong trong so bang CUNG quy tac nay."""
    y = np.asarray(y, float); w = np.asarray(w, float)
    assert len(y) == len(w) > 0 and (w > 0).all()
    o = np.argsort(y, kind='mergesort'); y, w = y[o], w[o]
    F = np.cumsum(w) / w.sum()
    i = int(np.searchsorted(F, q - 1e-12, side='left'))
    i = min(i, len(y) - 1)
    if abs(F[i] - q) <= 1e-12 and i + 1 < len(y): return 0.5 * (y[i] + y[i + 1])
    return y[i]

def franchise_weights(df, fid='franchise_id'):
    """Trong so 1/k_f; k_f = so transition cua franchise TRONG nhom dang xet (truyen vao df da loc nhom)."""
    return 1.0 / df.groupby(fid)[fid].transform('size')

def cluster_bootstrap_indices(blocks, rng):
    """blocks: list mang chi so dong cua tung franchise (toan mau). Rut len(blocks) cum CO HOAN LAI;
    cum duoc chon m lan thi xuat hien DU m ban sao (noi lai bang concatenate). Khong dung isin."""
    pick = rng.integers(0, len(blocks), size=len(blocks))
    return np.concatenate([blocks[j] for j in pick]), pick

def resampled(df, blocks, pick):
    """Mau lap: noi cac cum da rut (moi ban sao la mot cum rieng). Them cot 'boot_cluster' (id duy nhat moi ban sao).
    CANH BAO: trong so 1/k_f phai tinh theo 'boot_cluster' (hoac dung cot w tinh san truoc khi rut), KHONG groupby franchise_id
    vi ban sao cung franchise se bi gop va k_f tang gia."""
    parts = [df.loc[blocks[j]].assign(boot_cluster=c) for c, j in enumerate(pick)]
    return pd.concat(parts, ignore_index=True)

def bootstrap_ci(df, stat, B=10000, seed=20260101, fid='franchise_id', alpha=0.05):
    """df: mau dang phan tich (toan bo franchise). stat(df_boot)->float (vd trung vi Y cua mot nhom vi tri; co the tra NaN neu o rong).
    Moi lan lap: rut lai franchise tren TOAN mau roi tinh stat tren mau lap (nhom vi tri hinh thanh sau khi rut).
    Tra ve (point, lo, hi, so_lan_NaN)."""
    df = df.reset_index(drop=True)
    blocks = [g.index.values for _, g in df.groupby(fid, sort=True)]
    rng = np.random.default_rng(seed)
    out = np.empty(B)
    for b in range(B):
        idx, pick = cluster_bootstrap_indices(blocks, rng)
        out[b] = stat(df.loc[idx].assign(boot_cluster=np.repeat(np.arange(len(pick)), [len(blocks[j]) for j in pick])))
    ok = out[~np.isnan(out)]
    return stat(df.assign(boot_cluster=df[fid])), np.percentile(ok, 100 * alpha / 2), np.percentile(ok, 100 * (1 - alpha / 2)), int(np.isnan(out).sum())

def selftest():
    rng = np.random.default_rng(1)
    # 1) phan vi co trong so: trong so bang nhau -> trung vi == np.median
    for n in (4, 5, 8, 9):
        v = rng.normal(size=n); assert np.isclose(wquantile(v, np.ones(n), .5), np.median(v))
    # 2) trong so 1/k_f: tong trong so moi franchise = 1
    d = pd.DataFrame({'franchise_id': list('AAABBC'), 'Y': [1, 2, 3, 4, 5, 6.]}); w = franchise_weights(d)
    assert np.allclose(w.groupby(d.franchise_id).sum(), 1)
    # 3) bootstrap cum: franchise duoc chon m lan dong gop dung m ban sao
    blocks = [np.array([0, 1, 2]), np.array([3, 4]), np.array([5])]
    for s in range(200):
        idx, pick = cluster_bootstrap_indices(blocks, np.random.default_rng(s))
        for j, bl in enumerate(blocks):
            assert (np.isin(idx, bl)).sum() == len(bl) * (pick == j).sum()
    # 3b) trong so theo boot_cluster: moi ban sao tong trong so = 1 (khong bi gop khi franchise duoc chon nhieu lan)
    dd = pd.DataFrame({'franchise_id': ['A', 'A', 'B'], 'Y': [1., 2., 3.]}); bl = [np.array([0, 1]), np.array([2])]
    rs = resampled(dd, bl, np.array([0, 0, 1]))
    assert np.isclose(franchise_weights(rs, 'boot_cluster').sum(), 3) and len(rs) == 5
    # 4) CI chay duoc tren du lieu gia lap, seed co dinh -> lap lai duoc
    sim = pd.DataFrame({'franchise_id': np.repeat(np.arange(30), 2), 'Y': rng.normal(size=60)})
    r1 = bootstrap_ci(sim, lambda x: x.Y.median(), B=200); r2 = bootstrap_ci(sim, lambda x: x.Y.median(), B=200)
    assert r1 == r2
    print('selftest OK (du lieu gia lap)')
if __name__ == '__main__': selftest()
