"""Task 4 / RQ3 - kiem tra thanh phan mau, chan doan CI zero, PT2-lite, kich ban |Y|>3, ty le dao chieu, tong hop do vung >=6.
Doc inherited_step5_6/input_tables va results (KHONG sua). Ghi results/ (phien ban Task 4).
Bootstrap: cung engine/seed/B nhu buoc 6 (config.json cua inherited_step5_6)."""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument('--root', default='.'); ap.add_argument('--B', type=int, default=None); a = ap.parse_args()
R = a.root; INH = os.path.join(R, 'inherited_step5_6'); OUT = os.path.join(R, 'results'); sys.path.insert(0, os.path.join(R, 'code'))
import rq3_engine as E
cfg = json.load(open(os.path.join(INH, 'config.json'))); B = a.B or cfg['bootstrap']['B']; SEED = cfg['bootstrap']['seed']
T = pd.read_csv(os.path.join(INH, 'input_tables', 'T1_transitions_A0_with_sample_flags.csv'))
Dt = pd.read_csv(os.path.join(INH, 'input_tables', 'T2_D_table_franchises_with_Y2_and_Y3.csv'))
RS = os.path.join(INH, 'results')
POS = ['2', '3', '4', '5', '>=6']; GR = POS + ['ALL']; SAMPLES = ['A0', 'A1b', 'A1', 'A2']
pct = lambda q: 100 * (np.exp(q) - 1)
T['dec'] = np.where(T.release_year_n < 1980, '<1980', (T.release_year_n // 10 * 10).astype(int).astype(str) + 's')
DEC = ['<1980', '1980s', '1990s', '2000s', '2010s', '2020s']
t0 = time.time(); log = []
def say(s):
    print(s, flush=True); log.append(s)
def rows(d, g): return d if g == 'ALL' else d[d.pos_bin == g]
say(f'B={B} seed={SEED}')

# ================= C1. Thanh phan mau theo mau/vi tri/thap nien/gap/quy mo =================
c1 = []
for k in SAMPLES:
    d = T[T['in_' + k]]
    for g in GR:
        s = rows(d, g)
        r = dict(sample=k, group=g, n_transition=len(s), n_franchise=s.franchise_id.nunique(), gap_median=s.gap_years.median(), gap_q1=s.gap_years.quantile(.25), gap_q3=s.gap_years.quantile(.75),
                 open_prev_median=s.open_prev.median(), open_prev_q1=s.open_prev.quantile(.25), open_prev_q3=s.open_prev.quantile(.75),
                 share_open_prev_lt100k=(s.open_prev < 1e5).mean(), share_open_prev_lt1m=(s.open_prev < 1e6).mean(), share_any_open_lt100k=((s.open_prev < 1e5) | (s.open_curr < 1e5)).mean(),
                 release_year_N_median=s.release_year_n.median(), n_abs_Y_gt3=int((s.Y.abs() > 3).sum()))
        for dc in DEC: r['share_decade_' + dc] = (s.dec == dc).mean()
        c1.append(r)
C1 = pd.DataFrame(c1); C1.to_csv(os.path.join(OUT, 'T4_C1_sample_composition_by_position.csv'), index=False)
dec_tab = pd.concat([T[T['in_' + k]].groupby('dec').size().reindex(DEC, fill_value=0).rename(k) for k in SAMPLES], axis=1)
dec_tab.to_csv(os.path.join(OUT, 'T4_C1b_decade_counts_by_sample.csv'))
# tap bi loai moi buoc
steps = [('A0->A1b', 'A0', 'A1b'), ('A1b->A1', 'A1b', 'A1'), ('A1->A2', 'A1', 'A2')]; c1d = []
for lab, frm, to in steps:
    rem = T[T['in_' + frm] & ~T['in_' + to]]; keep = T[T['in_' + to]]
    for g in GR:
        sr = rows(rem, g); sf = rows(T[T['in_' + frm]], g)
        c1d.append(dict(step=lab, group=g, n_removed=len(sr), n_before=len(sf), share_removed=len(sr) / len(sf) if len(sf) else np.nan, n_franchise_with_removed=sr.franchise_id.nunique(),
                        removed_median_Y=sr.Y.median() if len(sr) else np.nan, removed_share_Y_lt0=(sr.Y < 0).mean() if len(sr) else np.nan, removed_n_abs_Y_gt3=int((sr.Y.abs() > 3).sum()),
                        removed_gap_median=sr.gap_years.median() if len(sr) else np.nan, removed_open_prev_median=sr.open_prev.median() if len(sr) else np.nan,
                        remaining_median_Y=sf[sf.transition_id.isin(keep.transition_id)].Y.median()))
    for dc in DEC:
        c1d.append(dict(step=lab, group='decade_' + dc, n_removed=int((rem.dec == dc).sum()), n_before=int((T[T['in_' + frm]].dec == dc).sum())))
C1D = pd.DataFrame(c1d); C1D.to_csv(os.path.join(OUT, 'T4_C1d_removed_sets_composition.csv'), index=False)
say(f'C1 xong ({time.time()-t0:.0f}s)')

# ================= C2. Thanh phan va chon loc: D / CH so voi mau chinh (vi tri 2) =================
a1b = T[T.in_A1b]
p2 = a1b[a1b.franchise_position_n == 2]
fD = set(Dt[Dt.in_A1b].franchise_id); fC = set(a1b[a1b.in_CH_A1b].franchise_id)
groups = {'Mau chinh: moi transition vi tri 2 (A1b)': p2, 'Mau PT3 (co Y o vi tri 2 va 3)': p2[p2.franchise_id.isin(fD)], 'Ngoai mau PT3 (co Y vt2, khong co Y vt3)': p2[~p2.franchise_id.isin(fD)],
          'Mau CH (chuoi Y lien tuc >=3 transition)': p2[p2.franchise_id.isin(fC)], 'Ngoai mau CH': p2[~p2.franchise_id.isin(fC)]}
boot1 = E.Boot(a1b.franchise_id.unique(), B=B, seed=SEED); defs = {}
for k, g in groups.items():
    defs[k + '|med'] = E.Def(g.Y, g.franchise_id, 'wq'); defs[k + '|lt0'] = E.Def(g.Y, g.franchise_id, 'lt0')
pts, reps = E.run(defs, boot1); c2 = []
for k, g in groups.items():
    lo, hi, _ = E.ci(reps[k + '|med']); l2, h2, _ = E.ci(reps[k + '|lt0'])
    r = dict(nhom=k, n_franchise=len(g), median_pct=pct(pts[k + '|med']), median_pct_ci_lo=pct(lo), median_pct_ci_hi=pct(hi), share_lt0=pts[k + '|lt0'], share_lt0_ci_lo=l2, share_lt0_ci_hi=h2,
             open_prev_median=g.open_prev.median(), share_open_prev_lt1m=(g.open_prev < 1e6).mean(), share_any_open_lt100k=((g.open_prev < 1e5) | (g.open_curr < 1e5)).mean(), gap_median=g.gap_years.median(), release_year_N_median=g.release_year_n.median())
    for dc in DEC: r['share_decade_' + dc] = (g.dec == dc).mean()
    c2.append(r)
pd.DataFrame(c2).to_csv(os.path.join(OUT, 'T4_C2_pos2_composition_PT3_CH_vs_main.csv'), index=False)
# CH so voi A1b theo vi tri
c2b = []
for g in GR:
    s = rows(a1b, g); sc = s[s.in_CH_A1b]; sn = s[~s.in_CH_A1b]
    c2b.append(dict(group=g, n_A1b=len(s), n_CH=len(sc), share_of_A1b_in_CH=len(sc) / len(s), F_CH=sc.franchise_id.nunique(), median_pct_CH=pct(sc.Y.median()) if len(sc) else np.nan, median_pct_nonCH=pct(sn.Y.median()) if len(sn) else np.nan,
                    share_lt0_CH=(sc.Y < 0).mean() if len(sc) else np.nan, share_lt0_nonCH=(sn.Y < 0).mean() if len(sn) else np.nan))
pd.DataFrame(c2b).to_csv(os.path.join(OUT, 'T4_C2b_CH_vs_rest_by_position.csv'), index=False)
say(f'C2 xong ({time.time()-t0:.0f}s)')

# ================= C4. Chan doan CI chenh lech co nhieu zero =================
boot0 = E.Boot(T.franchise_id.unique(), B=B, seed=SEED); idx0 = {f: i for i, f in enumerate(boot0.fr)}
defs0 = {}
for k in SAMPLES:
    d = T[T['in_' + k]]
    for g in GR:
        s = rows(d, g); defs0[f'{k}|{g}|med'] = E.Def(s.Y, s.franchise_id, 'wq'); defs0[f'{k}|{g}|lt0'] = E.Def(s.Y, s.franchise_id, 'lt0')
pts0, reps0 = E.run(defs0, boot0); c4 = []
for lab, frm, to in steps:
    rem = T[T['in_' + frm] & ~T['in_' + to]]
    for g in GR:
        rr = rows(rem, g); F_rem = sorted(rr.franchise_id.unique())
        if len(F_rem):
            cols = [idx0[f] for f in F_rem]; drawn = (boot0.C[:, cols] > 0).any(axis=1)
        else:
            drawn = np.zeros(boot0.B, bool)
        for stat in ('med', 'lt0'):
            dl = reps0[f'{to}|{g}|{stat}'] - reps0[f'{frm}|{g}|{stat}']; z = np.isclose(dl, 0, atol=1e-12)
            c4.append(dict(step=lab, group=g, stat={'med': 'median', 'lt0': 'share_lt0'}[stat], n_removed_transitions=len(rr), n_franchises_with_removed=len(F_rem),
                           share_reps_any_relevant_cluster_drawn=drawn.mean(), share_reps_diff_exactly_zero=z.mean(),
                           share_zero_given_relevant_drawn=z[drawn].mean() if drawn.any() else np.nan, share_zero_given_relevant_NOT_drawn=z[~drawn].mean() if (~drawn).any() else np.nan,
                           point_diff=pts0[f'{to}|{g}|{stat}'] - pts0[f'{frm}|{g}|{stat}']))
pd.DataFrame(c4).to_csv(os.path.join(OUT, 'T4_C4_zero_difference_diagnosis.csv'), index=False)
say(f'C4 xong ({time.time()-t0:.0f}s)')

# ================= C5. PT2-lite: tap franchise co dinh =================
piv = a1b.pivot_table(index='franchise_id', columns='franchise_position_n', values='Y', aggfunc='first')
have = piv.notna(); c5 = []; c5d = []
sets = {'B3 = {2,3,4}': [2, 3, 4], 'B4 = {2,3,4,5}': [2, 3, 4, 5]}
for nm, cols in sets.items():
    ids = have.index[have[cols].all(axis=1)]; sub = piv.loc[ids, cols]; boot = E.Boot(ids, B=B, seed=SEED); defs = {}
    for c in cols:
        defs[f'Y{c}|med'] = E.Def(sub[c].values, ids, 'wq'); defs[f'Y{c}|lt0'] = E.Def(sub[c].values, ids, 'lt0')
    for c1_, c2_ in zip(cols[:-1], cols[1:]):
        defs[f'D{c1_}{c2_}|med'] = E.Def((sub[c2_] - sub[c1_]).values, ids, 'wq'); defs[f'D{c1_}{c2_}|lt0'] = E.Def((sub[c2_] - sub[c1_]).values, ids, 'lt0')
    pts, reps = E.run(defs, boot)
    for c in cols:
        lo, hi, _ = E.ci(reps[f'Y{c}|med']); l2, h2, _ = E.ci(reps[f'Y{c}|lt0'])
        xs = a1b[a1b.franchise_position_n == c]
        c5.append(dict(set=nm, n_franchise=len(ids), position=c, median_Y=pts[f'Y{c}|med'], median_pct=pct(pts[f'Y{c}|med']), median_pct_ci_lo=pct(lo), median_pct_ci_hi=pct(hi), share_lt0=pts[f'Y{c}|lt0'], share_lt0_ci_lo=l2, share_lt0_ci_hi=h2,
                       cross_section_A1b_n=len(xs), cross_section_median_pct=pct(xs.Y.median()), cross_section_share_lt0=(xs.Y < 0).mean()))
    for c1_, c2_ in zip(cols[:-1], cols[1:]):
        lo, hi, _ = E.ci(reps[f'D{c1_}{c2_}|med']); l2, h2, _ = E.ci(reps[f'D{c1_}{c2_}|lt0'])
        c5d.append(dict(set=nm, n_franchise=len(ids), contrast=f'D = Y({c2_-1}->{c2_}) - Y({c1_-1}->{c1_})', median_D=pts[f'D{c1_}{c2_}|med'], median_D_ci_lo=lo, median_D_ci_hi=hi, share_D_lt0=pts[f'D{c1_}{c2_}|lt0'], share_D_lt0_ci_lo=l2, share_D_lt0_ci_hi=h2))
# D34, D45 doc lap (tat ca franchise A1b co Y o hai vi tri lien tiep)
for k0 in (3, 4):
    ids = have.index[have[[k0, k0 + 1]].all(axis=1)]; dv = (piv.loc[ids, k0 + 1] - piv.loc[ids, k0]).values; boot = E.Boot(ids, B=B, seed=SEED)
    pts, reps = E.run({'m': E.Def(dv, ids, 'wq'), 'l': E.Def(dv, ids, 'lt0')}, boot); lo, hi, _ = E.ci(reps['m']); l2, h2, _ = E.ci(reps['l'])
    c5d.append(dict(set=f'tat ca franchise A1b co Y o vi tri {k0} va {k0+1}', n_franchise=len(ids), contrast=f'D = Y({k0}->{k0+1}) - Y({k0-1}->{k0})', median_D=pts['m'], median_D_ci_lo=lo, median_D_ci_hi=hi, share_D_lt0=pts['l'], share_D_lt0_ci_lo=l2, share_D_lt0_ci_hi=h2))
pd.DataFrame(c5).to_csv(os.path.join(OUT, 'T4_C5_PT2lite_fixed_franchise_sets.csv'), index=False)
pd.DataFrame(c5d).to_csv(os.path.join(OUT, 'T4_C5b_PT2lite_within_franchise_differences.csv'), index=False)
say(f'C5 xong ({time.time()-t0:.0f}s)')

# ================= C6. Kich ban |Y|>3 (kiem tra bo tro) =================
c6a = []
for g in GR:
    s = rows(a1b, g); e = s[s.Y.abs() > 3]
    c6a.append(dict(group=g, n=len(s), n_abs_Y_gt3=len(e), n_Y_gt3=int((e.Y > 3).sum()), n_Y_lt_minus3=int((e.Y < -3).sum()), share=len(e) / len(s), n_in_small_open_lt100k=int(e.f_small_lt100k.sum()),
                    share_of_small_open_transitions_that_are_extreme=(e.f_small_lt100k.sum() / s.f_small_lt100k.sum()) if s.f_small_lt100k.sum() else np.nan))
pd.DataFrame(c6a).to_csv(os.path.join(OUT, 'T4_C6a_extreme_Y_counts_A1b.csv'), index=False)
ext = T.Y.abs() > 3
scen = {'A1b': T.in_A1b, 'A1b_noExt': T.in_A1b & ~ext, 'A1': T.in_A1, 'A1_noExt': T.in_A1 & ~ext, 'A2': T.in_A2, 'A2_noExt': T.in_A2 & ~ext}
defs6 = {}
for k, msk in scen.items():
    d = T[msk]
    for g in GR:
        s = rows(d, g); defs6[f'{k}|{g}|med'] = E.Def(s.Y, s.franchise_id, 'wq'); defs6[f'{k}|{g}|lt0'] = E.Def(s.Y, s.franchise_id, 'lt0')
pts6, reps6 = E.run(defs6, boot0); c6 = []
for lab, A_, B_ in (('A1b: bo |Y|>3 - giu', 'A1b_noExt', 'A1b'), ('A1->A2 (giu |Y|>3)', 'A2', 'A1'), ('A1->A2 (da bo |Y|>3 o ca hai)', 'A2_noExt', 'A1_noExt')):
    for g in GR:
        for stat in ('med', 'lt0'):
            dl = reps6[f'{A_}|{g}|{stat}'] - reps6[f'{B_}|{g}|{stat}']; lo, hi, nn = E.ci(dl)
            if stat == 'med':
                dp = pct(reps6[f'{A_}|{g}|med']) - pct(reps6[f'{B_}|{g}|med']); plo, phi, _ = E.ci(dp)
                c6.append(dict(contrast=lab, group=g, statistic='median', pct_from=pct(pts6[f'{B_}|{g}|med']), pct_to=pct(pts6[f'{A_}|{g}|med']), delta_pct_points=pct(pts6[f'{A_}|{g}|med']) - pct(pts6[f'{B_}|{g}|med']), ci_lo=plo, ci_hi=phi,
                               n_from=int(rows(T[scen[B_]], g).shape[0]), n_to=int(rows(T[scen[A_]], g).shape[0])))
            else:
                c6.append(dict(contrast=lab, group=g, statistic='share_lt0', pct_from=100 * pts6[f'{B_}|{g}|lt0'], pct_to=100 * pts6[f'{A_}|{g}|lt0'], delta_pct_points=100 * (pts6[f'{A_}|{g}|lt0'] - pts6[f'{B_}|{g}|lt0']), ci_lo=100 * lo, ci_hi=100 * hi,
                               n_from=int(rows(T[scen[B_]], g).shape[0]), n_to=int(rows(T[scen[A_]], g).shape[0])))
pd.DataFrame(c6).to_csv(os.path.join(OUT, 'T4_C6_extreme_Y_scenario.csv'), index=False)
rem126 = T[T.in_A1 & ~T.in_A2]
say(f'C6: |Y|>3 trong 126 cap bi loai A1->A2: {int((rem126.Y.abs()>3).sum())}; |Y|>3 trong A1b: {int(ext[T.in_A1b].sum())}, trong do thuoc nhom opening nho: {int((ext & T.in_A1b & T.f_small_lt100k).sum())}')
say(f'C6 xong ({time.time()-t0:.0f}s)')

# ================= C7. Ty le dao chieu theo cap transition ke tiep =================
rowsP = []
for f, g in a1b.sort_values(['franchise_id', 'franchise_position_n']).groupby('franchise_id'):
    pos = g.franchise_position_n.values; y = g.Y.values
    for i in range(len(pos) - 1):
        if pos[i + 1] == pos[i] + 1:
            rowsP.append(dict(franchise_id=f, k=int(pos[i]), y1=y[i], y2=y[i + 1], in_CH=bool(g.in_CH_A1b.values[i] and g.in_CH_A1b.values[i + 1])))
Pp = pd.DataFrame(rowsP); assert (Pp.y1 != 0).all() and (Pp.y2 != 0).all()
Pp['rev'] = (Pp.y1 < 0) != (Pp.y2 < 0); Pp['kg'] = np.where(Pp.k >= 5, '>=5', Pp.k.astype(str))
Pp.to_csv(os.path.join(OUT, 'T4_C7a_adjacent_pairs.csv'), index=False)
bootP = E.Boot(Pp.franchise_id.unique(), B=B, seed=SEED); defsP = {}; subsets = {'tat_ca_cap': Pp, 'cap_trong_CH': Pp[Pp.in_CH], 'cap_ngoai_CH': Pp[~Pp.in_CH]}
for k in ['2', '3', '4', '>=5']: subsets['k=' + k + '->' + ('k+1' if k != '>=5' else '..')] = Pp[Pp.kg == k]
for nm, s in subsets.items(): defsP[nm] = E.Def(np.where(s.rev, -1.0, 1.0), s.franchise_id, 'lt0')
ptsP, repsP = E.run(defsP, bootP); c7 = []
for nm, s in subsets.items():
    lo, hi, _ = E.ci(repsP[nm]); p1 = (s.y1 < 0).mean(); p2_ = (s.y2 < 0).mean()
    c7.append(dict(tap_cap=nm, n_pairs=len(s), n_franchises=s.franchise_id.nunique(), n_reversals=int(s.rev.sum()), reversal_share=ptsP[nm], ci_lo=lo, ci_hi=hi, share_first_lt0=p1, share_second_lt0=p2_,
                   reference_if_signs_independent=p1 * (1 - p2_) + (1 - p1) * p2_))
pd.DataFrame(c7).to_csv(os.path.join(OUT, 'T4_C7_reversal_rate_adjacent_pairs.csv'), index=False)
ch = a1b[a1b.in_CH_A1b]; lens = ch.groupby('franchise_id').size(); rv = Pp[Pp.in_CH].groupby('franchise_id').rev.sum()
pch = float((ch.Y < 0).mean())      # ty le Y<0 gop trong CH, dung lam tham chieu 'dau doc lap' (khong phai kiem dinh)
tb = pd.DataFrame({'chain_length': lens, 'n_pairs': lens - 1, 'reversals': rv.reindex(lens.index)}).groupby('chain_length').agg(n_franchise=('n_pairs', 'size'), n_pairs_each=('n_pairs', 'first'), franchises_with_ge1_reversal=('reversals', lambda s: int((s > 0).sum())),
    mean_reversals=('reversals', 'mean'))
tb['reference_expected_franchises_with_ge1_reversal_if_signs_independent'] = tb.n_franchise * (1 - (pch ** tb.index.values + (1 - pch) ** tb.index.values))
tb['reference_p_lt0_used'] = pch
tb.to_csv(os.path.join(OUT, 'T4_C7b_CH_reversals_by_chain_length.csv'))
say(f'CH: so franchise co >=1 dao chieu {int(tb.franchises_with_ge1_reversal.sum())}/58; tham chieu (dau doc lap, p<0={pch:.3f}) ~ {tb.reference_expected_franchises_with_ge1_reversal_if_signs_independent.sum():.1f}')
say(f'C7 xong ({time.time()-t0:.0f}s)')

# ================= C9. Tong hop do vung nhom >=6 =================
W = pd.read_csv(os.path.join(RS, 'R6_weighting_ge6_transition_vs_franchise.csv')); Lf = pd.read_csv(os.path.join(RS, 'R7_LOFO_ge6_A1b_optional.csv')); c9 = []
for _, r in W.iterrows():
    c9.append(dict(config=f"{r['sample']} / {'transition ngang nhau' if r.scheme=='transition_equal' else 'franchise ngang nhau (1/kf)'}", n_transition=int(r.n_transition), n_franchise=int(r.n_franchise), median_pct=r.median_pct, ci_lo=r.median_pct_ci_lo, ci_hi=r.median_pct_ci_hi, share_lt0=r.share_lt0, share_lt0_ci_lo=r.share_lt0_ci_lo, share_lt0_ci_hi=r.share_lt0_ci_hi,
                   direction='am' if r.median_pct < 0 else ('duong' if r.median_pct > 0 else 'bang 0')))
for nm, col in (('min', 'min'), ('max', 'max')):
    v = Lf.median_Y_transition_w.agg(col); c9.append(dict(config=f'LOFO A1b (bo 1 franchise), transition ngang nhau: {nm}', n_transition=np.nan, n_franchise=30, median_pct=pct(v), direction='am' if v < 0 else 'duong'))
for nm, col in (('min', 'min'), ('max', 'max')):
    v = Lf.median_Y_franchise_w.agg(col); c9.append(dict(config=f'LOFO A1b (bo 1 franchise), franchise ngang nhau: {nm}', n_transition=np.nan, n_franchise=30, median_pct=pct(v), direction='am' if v < 0 else 'duong'))
C9 = pd.DataFrame(c9); C9.to_csv(os.path.join(OUT, 'T4_C9_robustness_ge6_configs.csv'), index=False)
say(f'XONG ({time.time()-t0:.0f}s)')
open(os.path.join(R, 'logs', 't4_02_analysis_log.txt'), 'w', encoding='utf-8').write('\n'.join(log))
