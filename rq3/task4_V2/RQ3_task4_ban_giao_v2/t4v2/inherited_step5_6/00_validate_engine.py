"""Doi chieu engine vector hoa voi helper v4 (rq3_stats_helpers) TUNG LAN LAP, cung seed, tren du lieu that A1b."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import rq3_stats_helpers as H, rq3_engine as E
R = sys.argv[1] if len(sys.argv) > 1 else '.'
T = pd.read_csv(os.path.join(R, 'input_tables', 'T1_transitions_A0_with_sample_flags.csv'))
d = T[T.in_A1b].reset_index(drop=True); NB = 300; SEED = 20260101
boot = E.Boot(d.franchise_id.unique(), B=NB, seed=SEED)
blocks = [g.index.values for _, g in d.groupby('franchise_id', sort=True)]
rng = np.random.default_rng(SEED)
res = {k: [] for k in ['2|med', '>=6|med', '>=6|lt0', '>=6|med_w', '>=6|lt0_w', '3|lt0', '>=6|q25_w']}
for b in range(NB):
    idx, pick = H.cluster_bootstrap_indices(blocks, rng)
    x = H.resampled(d, blocks, pick)
    for g in ['2', '>=6', '3']:
        s = x[x.pos_bin == g]
        if g == '2': res['2|med'].append(H.wquantile(s.Y, np.ones(len(s)), .5) if len(s) else np.nan)
        if g == '3': res['3|lt0'].append((s.Y < 0).mean() if len(s) else np.nan)
        if g == '>=6':
            w = H.franchise_weights(s, 'boot_cluster').values
            res['>=6|med'].append(H.wquantile(s.Y, np.ones(len(s)), .5)); res['>=6|lt0'].append((s.Y < 0).mean())
            res['>=6|med_w'].append(H.wquantile(s.Y, w, .5)); res['>=6|lt0_w'].append((w * (s.Y < 0)).sum() / w.sum())
            res['>=6|q25_w'].append(H.wquantile(s.Y, w, .25))
defs = {'2|med': E.Def(d[d.pos_bin == '2'].Y, d[d.pos_bin == '2'].franchise_id, 'wq'),
        '3|lt0': E.Def(d[d.pos_bin == '3'].Y, d[d.pos_bin == '3'].franchise_id, 'lt0')}
s6 = d[d.pos_bin == '>=6']
defs.update({'>=6|med': E.Def(s6.Y, s6.franchise_id, 'wq'), '>=6|lt0': E.Def(s6.Y, s6.franchise_id, 'lt0'),
             '>=6|med_w': E.Def(s6.Y, s6.franchise_id, 'wq', weight='fr'), '>=6|lt0_w': E.Def(s6.Y, s6.franchise_id, 'lt0', weight='fr'),
             '>=6|q25_w': E.Def(s6.Y, s6.franchise_id, 'wq', q=.25, weight='fr')})
pts, reps = E.run(defs, boot)
ok = True
for k in res:
    a = np.array(res[k], float); b = reps[k]; same = np.allclose(a, b, equal_nan=True, atol=1e-10)
    print(f'{k:12s} {NB} lan lap: khop helper = {same}; max|diff| = {np.nanmax(np.abs(a-b)):.2e}'); ok &= same
# diem uoc luong: helper
s2 = d[d.pos_bin == '2']; print('diem 2|med', H.wquantile(s2.Y, np.ones(len(s2)), .5), pts['2|med'])
assert abs(H.wquantile(s2.Y, np.ones(len(s2)), .5) - pts['2|med']) < 1e-12
w = H.franchise_weights(s6).values; assert abs(H.wquantile(s6.Y, w, .5) - pts['>=6|med_w']) < 1e-12
assert ok, 'engine KHONG khop helper'
msg = 'VALIDATE OK: engine khop helper v4 tung lan lap (B=300, seed 20260101, A1b); diem uoc luong khop.'
print(msg); open(os.path.join(R, 'logs', '00_validate_engine_log.txt'), 'w').write(msg + '\n')
