"""RQ3 Buoc 6 - chay PT1, PT3, PT4, do nhay. Doc input_tables/ (tao boi 01_prepare.py). Bootstrap theo franchise, B/seed tu config.json.
Chay: python code/02_analyze.py --root ."""
import argparse, json, os, sys, time
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import rq3_engine as E
import rq3_stats_helpers as H

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--B', type=int, default=None, help='CHI de thu nhanh; mac dinh lay tu config.json (10000)')
a = ap.parse_args()
R = a.root
cfg = json.load(open(os.path.join(R, 'config.json')))
B = a.B or cfg['bootstrap']['B']
SEED = cfg['bootstrap']['seed']
IN = os.path.join(R, 'input_tables')
OUT = os.path.join(R, 'results')
os.makedirs(OUT, exist_ok=True)
POS = cfg['position_bins']
SAMPLES = ['A0', 'A1b', 'A1', 'A2']
log = []
t0 = time.time()


def say(*x):
    s = ' '.join(str(i) for i in x)
    print(s, flush=True)
    log.append(s)


T = pd.read_csv(os.path.join(IN, 'T1_transitions_A0_with_sample_flags.csv'))
Dt = pd.read_csv(os.path.join(IN, 'T2_D_table_franchises_with_Y2_and_Y3.csv'))
CHT = pd.read_csv(os.path.join(IN, 'T3_chain_CH_transitions.csv'))
say(f'B = {B}, seed = {SEED}')
pct = lambda q: 100 * (np.exp(q) - 1)
GROUPS = POS + ['ALL']


def rows(d, g):
    return d if g == 'ALL' else d[d.pos_bin == g]


# ============ mo ta (khong bootstrap): n, F, trung vi, Q1-Q3 (type 7), ty le ============
def describe(d, g):
    s = rows(d, g)
    y = s.Y.values
    q1, med, q3 = np.percentile(y, [25, 50, 75])
    return dict(group=g, n_transition=len(s), n_franchise=s.franchise_id.nunique(), median_Y=med, q1_Y=q1, q3_Y=q3,
                median_pct=pct(med), q1_pct=pct(q1), q3_pct=pct(q3), share_lt0=(y < 0).mean(), share_eq0=(y == 0).mean(), share_gt0=(y > 0).mean(),
                n_lt0=int((y < 0).sum()), n_eq0=int((y == 0).sum()), n_gt0=int((y > 0).sum()))


def wilson(k, n, z=1.959964):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def pt1_defs(d):
    defs = {}
    for g in GROUPS:
        s = rows(d, g)
        defs[f'{g}|med'] = E.Def(s.Y, s.franchise_id, 'wq')
        for k in ('lt0', 'gt0', 'eq0'):
            defs[f'{g}|{k}'] = E.Def(s.Y, s.franchise_id, k)
    s6 = rows(d, '>=6')
    defs['>=6|med_w'] = E.Def(s6.Y, s6.franchise_id, 'wq', weight='fr')
    defs['>=6|lt0_w'] = E.Def(s6.Y, s6.franchise_id, 'lt0', weight='fr')
    defs['>=6|gt0_w'] = E.Def(s6.Y, s6.franchise_id, 'gt0', weight='fr')
    return defs


# ============ PT1 tren moi mau (universe = franchise cua chinh mau do) ============
pt1_rows, wrows, ov = [], [], []
PT1_REPS = {}
for k in SAMPLES:
    d = T[T['in_' + k]].reset_index(drop=True)
    boot = E.Boot(d.franchise_id.unique(), B=B, seed=SEED)
    pts, reps = E.run(pt1_defs(d), boot)
    if k == 'A1b':
        PT1_REPS = reps
    for g in GROUPS:
        r = describe(d, g)
        r.update(sample=k, boot_universe_franchises=boot.F)
        for nm, key in (('median_Y', f'{g}|med'), ('share_lt0', f'{g}|lt0'), ('share_gt0', f'{g}|gt0'), ('share_eq0', f'{g}|eq0')):
            lo, hi, nn = E.ci(reps[key])
            r[nm + '_ci_lo'], r[nm + '_ci_hi'], r[nm + '_boot_nan'] = lo, hi, nn
            assert abs(pts[key] - r[nm]) < 1e-9 if nm in r else True
        r['median_pct_ci_lo'], r['median_pct_ci_hi'] = pct(r['median_Y_ci_lo']), pct(r['median_Y_ci_hi'])
        if g in POS[:4]:
            r['share_lt0_wilson_lo'], r['share_lt0_wilson_hi'] = wilson(r['n_lt0'], r['n_transition'])
        pt1_rows.append(r)
    # trong so ">=6": cung quy tac phan vi
    s6 = d[d.pos_bin == '>=6']
    w = H.franchise_weights(s6).values
    for scheme, ww in (('transition_equal', np.ones(len(s6))), ('franchise_equal_1_over_kf', w)):
        sfx = '' if scheme == 'transition_equal' else '_w'
        medk, ltk, gtk = f'>=6|med{sfx}', f'>=6|lt0{sfx}', f'>=6|gt0{sfx}'
        lo, hi, nn = E.ci(reps[medk])
        l2, h2, n2 = E.ci(reps[ltk])
        wrows.append(dict(sample=k, scheme=scheme, n_transition=len(s6), n_franchise=s6.franchise_id.nunique(),
                          max_weight_share_single_franchise=float((pd.Series(ww, index=s6.index).groupby(s6.franchise_id).sum() / ww.sum()).max()),
                          q1_Y=H.wquantile(s6.Y, ww, .25), median_Y=H.wquantile(s6.Y, ww, .5), q3_Y=H.wquantile(s6.Y, ww, .75),
                          median_pct=pct(H.wquantile(s6.Y, ww, .5)), median_Y_ci_lo=lo, median_Y_ci_hi=hi, median_pct_ci_lo=pct(lo), median_pct_ci_hi=pct(hi),
                          share_lt0=float((ww * (s6.Y < 0)).sum() / ww.sum()), share_lt0_ci_lo=l2, share_lt0_ci_hi=h2,
                          share_gt0=float((ww * (s6.Y > 0)).sum() / ww.sum()), share_eq0=float((ww * (s6.Y == 0)).sum() / ww.sum()),
                          quantile_rule='inverse CDF (helper wquantile), cung quy tac cho ca hai phuong an'))
    say(f'PT1 {k} xong ({time.time()-t0:.0f}s)')
PT1 = pd.DataFrame(pt1_rows)
cols_first = ['sample', 'group', 'n_transition', 'n_franchise', 'median_Y', 'median_Y_ci_lo', 'median_Y_ci_hi', 'median_pct', 'median_pct_ci_lo', 'median_pct_ci_hi',
              'q1_Y', 'q3_Y', 'q1_pct', 'q3_pct', 'n_lt0', 'n_eq0', 'n_gt0', 'share_lt0', 'share_lt0_ci_lo', 'share_lt0_ci_hi', 'share_lt0_wilson_lo', 'share_lt0_wilson_hi',
              'share_eq0', 'share_gt0', 'share_gt0_ci_lo', 'share_gt0_ci_hi']
PT1 = PT1[cols_first + [c for c in PT1.columns if c not in cols_first]]
PT1.to_csv(os.path.join(OUT, 'R2_PT1_by_position_all_samples.csv'), index=False)
PT1[PT1['sample'] == 'A1b'].to_csv(os.path.join(OUT, 'R2_PT1_by_position_A1b_MAIN.csv'), index=False)
PT1[(PT1['sample'] == 'A1b') & (PT1.group == 'ALL')].to_csv(os.path.join(OUT, 'R1_overview_A1b.csv'), index=False)
pd.DataFrame(wrows).to_csv(os.path.join(OUT, 'R6_weighting_ge6_transition_vs_franchise.csv'), index=False)
np.savez_compressed(os.path.join(OUT, 'bootstrap_reps_PT1_A1b.npz'), **{k.replace('|', '__'): v for k, v in PT1_REPS.items()})

# ============ So sanh theo cap: universe chung = A0, cung cum rut cho moi mau ============
boot0 = E.Boot(T.franchise_id.unique(), B=B, seed=SEED)
defs0 = {}
for k in SAMPLES:
    d = T[T['in_' + k]]
    for g in GROUPS:
        s = rows(d, g)
        defs0[f'{k}|{g}|med'] = E.Def(s.Y, s.franchise_id, 'wq')
        defs0[f'{k}|{g}|lt0'] = E.Def(s.Y, s.franchise_id, 'lt0')
        defs0[f'{k}|{g}|gt0'] = E.Def(s.Y, s.franchise_id, 'gt0')
    s6 = rows(d, '>=6')
    defs0[f'{k}|>=6|med_w'] = E.Def(s6.Y, s6.franchise_id, 'wq', weight='fr')
    defs0[f'{k}|>=6|lt0_w'] = E.Def(s6.Y, s6.franchise_id, 'lt0', weight='fr')
pts0, reps0 = E.run(defs0, boot0)
say(f'Universe chung A0 ({boot0.F} franchise) xong ({time.time()-t0:.0f}s)')


def diff_row(label, contrast, A, Bk, g, stat, key_a, key_b):
    """A - Bk (A la phuong an sau thay doi). Tra ve dict."""
    ra, rb = reps0[key_a], reps0[key_b]
    pa, pb = pts0[key_a], pts0[key_b]
    r = dict(contrast=contrast, group=g, statistic=stat, from_=Bk, to_=A)
    if stat == 'median':
        dl = ra - rb
        dp = pct(ra) - pct(rb)
        lo, hi, nn = E.ci(dl)
        plo, phi, _ = E.ci(dp)
        r.update(value_from=pb, value_to=pa, delta=pa - pb, delta_ci_lo=lo, delta_ci_hi=hi, delta_unit='log-Y',
                 pct_from=pct(pb), pct_to=pct(pa), delta_pct_points=pct(pa) - pct(pb), delta_pct_points_ci_lo=plo, delta_pct_points_ci_hi=phi, boot_nan=nn)
    else:
        dl = ra - rb
        lo, hi, nn = E.ci(dl)
        r.update(value_from=pb, value_to=pa, delta=pa - pb, delta_ci_lo=lo, delta_ci_hi=hi, delta_unit='share (0-1)', boot_nan=nn)
    return r


drows = []
for (frm, to) in (('A0', 'A1b'), ('A1b', 'A1'), ('A1', 'A2')):
    for g in GROUPS:
        for stat, sk in (('median', 'med'), ('share_lt0', 'lt0'), ('share_gt0', 'gt0')):
            drows.append(diff_row(f'{frm}->{to}', f'{frm}->{to}', to, frm, g, stat, f'{to}|{g}|{sk}', f'{frm}|{g}|{sk}'))
for k in SAMPLES:
    for stat, sk in (('median', 'med'), ('share_lt0', 'lt0')):
        drows.append(diff_row(f'{k}: franchise-weighted vs transition-weighted', 'weights', f'{k}(1/kf)', f'{k}(equal)', '>=6', stat,
                              f'{k}|>=6|{sk}_w', f'{k}|>=6|{sk}'))
SENS = pd.DataFrame(drows)
SENS['n_from'] = SENS.apply(lambda r: int(T[T['in_' + r.from_.split('(')[0]]].pipe(rows, r.group).shape[0]) if r.contrast != 'weights' else np.nan, axis=1)
SENS['n_to'] = SENS.apply(lambda r: int(T[T['in_' + r.to_.split('(')[0]]].pipe(rows, r.group).shape[0]), axis=1)
SENS['note'] = np.where(SENS.contrast == 'weights', 'cung mau, doi trong so; cung quy tac phan vi', 'CI cua chenh lech tu cum rut CHUNG tren universe A0 (bootstrap ghep cap)')
SENS.to_csv(os.path.join(OUT, 'R5_sensitivity_paired_differences.csv'), index=False)
say(f'Do nhay xong ({time.time()-t0:.0f}s)')

# ============ PT3: D ============
d_rows, dd_rows = [], []
DREPS = {}
for k in SAMPLES:
    ds = Dt[Dt['in_' + k]].reset_index(drop=True)
    boot = E.Boot(ds.franchise_id.unique(), B=B, seed=SEED)
    defs = {'D|med': E.Def(ds.D, ds.franchise_id, 'wq'), 'D|lt0': E.Def(ds.D, ds.franchise_id, 'lt0'), 'D|gt0': E.Def(ds.D, ds.franchise_id, 'gt0'),
            'D|eq0': E.Def(ds.D, ds.franchise_id, 'eq0'), 'Y12|med': E.Def(ds.Y12, ds.franchise_id, 'wq'), 'Y23|med': E.Def(ds.Y23, ds.franchise_id, 'wq'),
            'Y12|lt0': E.Def(ds.Y12, ds.franchise_id, 'lt0'), 'Y23|lt0': E.Def(ds.Y23, ds.franchise_id, 'lt0')}
    pts, reps = E.run(defs, boot)
    if k == 'A1b':
        DREPS = reps
    q1, med, q3 = np.percentile(ds.D, [25, 50, 75])
    r = dict(sample=k, n_franchise=len(ds), median_D=med, q1_D=q1, q3_D=q3)
    for nm, key in (('median_D', 'D|med'), ('share_D_lt0', 'D|lt0'), ('share_D_gt0', 'D|gt0'), ('share_D_eq0', 'D|eq0'),
                    ('median_Y12', 'Y12|med'), ('median_Y23', 'Y23|med'), ('share_Y12_lt0', 'Y12|lt0'), ('share_Y23_lt0', 'Y23|lt0')):
        lo, hi, nn = E.ci(reps[key])
        r[nm] = pts[key]
        r[nm + '_ci_lo'], r[nm + '_ci_hi'] = lo, hi
    r['n_D_lt0'], r['n_D_eq0'], r['n_D_gt0'] = int((ds.D < 0).sum()), int((ds.D == 0).sum()), int((ds.D > 0).sum())
    r['boot_universe_franchises'] = boot.F
    r['spearman_Y12_Y23_descriptive'] = float(ds[['Y12', 'Y23']].corr(method='spearman').iloc[0, 1])
    d_rows.append(r)
    say(f'PT3 {k} xong ({time.time()-t0:.0f}s)')
PT3 = pd.DataFrame(d_rows)
PT3.to_csv(os.path.join(OUT, 'R3_PT3_D_all_samples.csv'), index=False)
PT3[PT3['sample'] == 'A1b'].to_csv(os.path.join(OUT, 'R3_PT3_D_A1b_MAIN.csv'), index=False)
# chenh lech D giua cac mau (cum chung: franchise cua A0)
bootD = E.Boot(Dt.franchise_id.unique(), B=B, seed=SEED)
defsD = {}
for k in SAMPLES:
    ds = Dt[Dt['in_' + k]]
    defsD[f'{k}|med'] = E.Def(ds.D, ds.franchise_id, 'wq')
    defsD[f'{k}|lt0'] = E.Def(ds.D, ds.franchise_id, 'lt0')
ptsD, repsD = E.run(defsD, bootD)
for (frm, to) in (('A0', 'A1b'), ('A1b', 'A1'), ('A1', 'A2')):
    for stat, sk in (('median_D', 'med'), ('share_D_lt0', 'lt0')):
        dl = repsD[f'{to}|{sk}'] - repsD[f'{frm}|{sk}']
        lo, hi, nn = E.ci(dl)
        dd_rows.append(dict(contrast=f'{frm}->{to}', statistic=stat, n_from=int(Dt['in_' + frm].sum()), n_to=int(Dt['in_' + to].sum()),
                            value_from=ptsD[f'{frm}|{sk}'], value_to=ptsD[f'{to}|{sk}'], delta=ptsD[f'{to}|{sk}'] - ptsD[f'{frm}|{sk}'],
                            delta_ci_lo=lo, delta_ci_hi=hi, boot_nan=nn, note='CI chenh lech tu cum rut chung tren 177 franchise cua A0'))
pd.DataFrame(dd_rows).to_csv(os.path.join(OUT, 'R3b_PT3_D_sensitivity_paired.csv'), index=False)
Dt.to_csv(os.path.join(OUT, 'R3c_D_values_per_franchise.csv'), index=False)

# ============ PT4: chuoi CH (mo ta) ============
ch = T[T.in_CH_A1b].sort_values(['franchise_id', 'franchise_position_n'])


def sgn(y):
    return '-' if y < 0 else ('0' if y == 0 else '+')


def chain_tbl(df, label):
    out = []
    for f, g in df.groupby('franchise_id'):
        y = g.Y.values
        s = ''.join(sgn(v) for v in y)
        rev = sum(1 for i in range(len(y) - 1) if (y[i] < 0 and y[i + 1] > 0) or (y[i] > 0 and y[i + 1] < 0))      # dao chieu TRUC TIEP; zero khong noi qua
        out.append(dict(chain_sample=label, franchise_id=f, n_transition=len(y), first_position=int(g.franchise_position_n.min()), last_position=int(g.franchise_position_n.max()),
                        sign_pattern=s, n_decrease=int((y < 0).sum()), n_zero=int((y == 0).sum()), n_increase=int((y > 0).sum()), n_direct_reversals=rev,
                        min_Y=float(y.min()), max_Y=float(y.max()), titles=' | '.join(g.title_curr.astype(str).head(1)) + ' ...'))
    return pd.DataFrame(out)


CH_A = chain_tbl(ch, 'CH_A1b(=A0=A1)')
CH_B = chain_tbl(T[T.in_CH_A2].sort_values(['franchise_id', 'franchise_position_n']), 'CH_A2')
pd.concat([CH_A, CH_B]).to_csv(os.path.join(OUT, 'R4_PT4_chain_per_franchise.csv'), index=False)
pat, contrib, lenrows = [], [], []
for lab, tb, df in (('CH_A1b', CH_A, ch), ('CH_A2', CH_B, T[T.in_CH_A2])):
    nF, nT = len(tb), int(tb.n_transition.sum())
    for p, c in tb.sign_pattern.value_counts().items():
        pat.append(dict(chain_sample=lab, sign_pattern=p, length=len(p), n_franchise=int(c), share_of_franchises=c / nF))
    for L, c in tb.n_transition.value_counts().sort_index().items():
        lenrows.append(dict(chain_sample=lab, chain_length_transitions=int(L), n_franchise=int(c)))
    for pos, g in df.groupby('franchise_position_n'):
        contrib.append(dict(chain_sample=lab, position=int(pos), n_franchise_contributing=g.franchise_id.nunique(), n_transition=len(g), median_Y=g.Y.median(),
                            median_pct=pct(g.Y.median()), share_lt0=float((g.Y < 0).mean()), n_lt0=int((g.Y < 0).sum()), n_gt0=int((g.Y > 0).sum()), n_eq0=int((g.Y == 0).sum())))
    pat.append(dict(chain_sample=lab, sign_pattern='__SUMMARY__', length=np.nan, n_franchise=nF,
                    share_of_franchises=np.nan, n_transition_total=nT, n_all_decrease=int((tb.n_decrease == tb.n_transition).sum()),
                    n_all_increase=int((tb.n_increase == tb.n_transition).sum()), n_with_zero=int((tb.n_zero > 0).sum()),
                    n_with_ge1_reversal=int((tb.n_direct_reversals > 0).sum()), n_reversals_total=int(tb.n_direct_reversals.sum())))
pd.DataFrame(pat).to_csv(os.path.join(OUT, 'R4b_PT4_sign_patterns.csv'), index=False)
pd.DataFrame(contrib).to_csv(os.path.join(OUT, 'R4c_PT4_position_contribution_and_median.csv'), index=False)
pd.DataFrame(lenrows).to_csv(os.path.join(OUT, 'R4d_PT4_chain_length_distribution.csv'), index=False)
say(f'PT4 xong ({time.time()-t0:.0f}s)')

# ============ Tuy chon re: leave-one-franchise-out nhom >=6 (A1b), khong bootstrap ============
d6 = T[T.in_A1b & (T.pos_bin == '>=6')]
base_med = H.wquantile(d6.Y, np.ones(len(d6)), .5)
lo_rows = []
for f in sorted(d6.franchise_id.unique()):
    s = d6[d6.franchise_id != f]
    w = H.franchise_weights(s).values
    lo_rows.append(dict(dropped_franchise=f, dropped_n_transition=int((d6.franchise_id == f).sum()), n_remaining=len(s), n_franchise_remaining=s.franchise_id.nunique(),
                        median_Y_transition_w=H.wquantile(s.Y, np.ones(len(s)), .5), share_lt0_transition_w=float((s.Y < 0).mean()),
                        median_Y_franchise_w=H.wquantile(s.Y, w, .5), share_lt0_franchise_w=float((w * (s.Y < 0)).sum() / w.sum())))
LOFO = pd.DataFrame(lo_rows)
LOFO.to_csv(os.path.join(OUT, 'R7_LOFO_ge6_A1b_optional.csv'), index=False)
say('LOFO >=6: median Y (transition-weighted) range', LOFO.median_Y_transition_w.min(), LOFO.median_Y_transition_w.max(),
    '| share<0 range', LOFO.share_lt0_transition_w.min(), LOFO.share_lt0_transition_w.max())
say(f'XONG ({time.time()-t0:.0f}s)')
open(os.path.join(R, 'logs', '02_analyze_log.txt'), 'w', encoding='utf-8').write('\n'.join(log))
