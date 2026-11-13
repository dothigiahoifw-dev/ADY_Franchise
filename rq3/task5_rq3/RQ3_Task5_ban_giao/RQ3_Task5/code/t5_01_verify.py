"""Task 5 / RQ3 - kiem tra doc lap cac so lieu chinh cua Task 4 v2 truoc khi dua vao bao cao cuoi.
Tai tinh bang pandas/numpy tu input_tables (T1, T2) cua buoc 5-6 (khong dung engine bootstrap cho diem uoc luong).
- Diem uoc luong: tai tinh doc lap -> trang thai 'T5-KT'.
- CI: doc lai tu npz (PT1 A1b) hoac chay lai co muc tieu 1-2 o bang engine (khong chay lai toan bo) -> 'T5-KT (CI)'.
- Cac CI khac: giu 'KE THUA' (khong bootstrap lai o Task 5).
- Doi chieu bang chung cho nhom 11 franchise tu file tho (neu co --raw).
Chay: python code/t5_01_verify.py --root . [--raw /mnt/user-data/uploads]"""
import argparse, os, sys, json
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument('--root', default='.'); ap.add_argument('--raw', default=None); ap.add_argument('--skip_ci', action='store_true'); a = ap.parse_args()
R = a.root; T4 = os.path.join(R, 'inherited_task4_v2'); S56 = os.path.join(T4, 'inherited_step5_6')
sys.path.insert(0, os.path.join(T4, 'code'))
import rq3_stats_helpers as H, rq3_engine as E
RS4, RS56, IN = os.path.join(T4, 'results'), os.path.join(S56, 'results'), os.path.join(S56, 'input_tables')
OUT = os.path.join(R, 'results'); os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.join(R, 'logs'), exist_ok=True)
T = pd.read_csv(os.path.join(IN, 'T1_transitions_A0_with_sample_flags.csv')); D = pd.read_csv(os.path.join(IN, 'T2_D_table_franchises_with_Y2_and_Y3.csv'))
pct = lambda q: 100 * (np.exp(q) - 1)
rows = []; fails = []
def chk(item, source, v4, v5, tol=1e-9, status='T5-KT'):
    ok = (v4 == v5) if isinstance(v4, (str, bool)) or isinstance(v5, (str, bool)) else abs(float(v4) - float(v5)) <= tol
    rows.append(dict(item=item, source_file=source, value_in_task4_or_inherited=v4, value_recomputed_task5=v5, match=bool(ok), status=status))
    if not ok: fails.append(item)

P = pd.read_csv(os.path.join(RS56, 'R2_PT1_by_position_all_samples.csv')); src2 = 'inherited_task4_v2/inherited_step5_6/results/R2_PT1_by_position_all_samples.csv'
POS = ['2', '3', '4', '5', '>=6']; GR = POS + ['ALL']
a1b = T[T.in_A1b]
rows_ = lambda d, g: d if g == 'ALL' else d[d.pos_bin == g]
# ---------- 1. mau va PT1 (A1b + do nhay diem)
chk('A1b so transition', src2, 910, len(a1b)); chk('A1b so franchise', src2, 557, a1b.franchise_id.nunique())
for k in ['A1b', 'A0', 'A1', 'A2']:
    d = T[T['in_' + k]]
    for g in GR:
        s = rows_(d, g); y = s.Y.values; r = P[(P['sample'] == k) & (P.group == g)].iloc[0]
        chk(f'{k} {g}: n transition', src2, r.n_transition, len(s)); chk(f'{k} {g}: n franchise', src2, r.n_franchise, s.franchise_id.nunique())
        chk(f'{k} {g}: trung vi % thay doi', src2, r.median_pct, pct(np.median(y)), 1e-7); chk(f'{k} {g}: ty le Y<0', src2, r.share_lt0, (y < 0).mean())
        if k == 'A1b':
            chk(f'{k} {g}: Q1 %', src2, r.q1_pct, pct(np.percentile(y, 25)), 1e-7); chk(f'{k} {g}: Q3 %', src2, r.q3_pct, pct(np.percentile(y, 75)), 1e-7)
            chk(f'{k} {g}: so Y=0', src2, r.n_eq0, int((y == 0).sum()))
# ---------- 2. trong so >=6, LOFO
W = pd.read_csv(os.path.join(RS56, 'R6_weighting_ge6_transition_vs_franchise.csv')); srcw = 'inherited_task4_v2/inherited_step5_6/results/R6_weighting_ge6_transition_vs_franchise.csv'
for k in ['A0', 'A1b', 'A1', 'A2']:
    s6 = T[T['in_' + k] & (T.pos_bin == '>=6')]; w = H.franchise_weights(s6).values
    r = W[(W['sample'] == k) & (W.scheme == 'franchise_equal_1_over_kf')].iloc[0]
    chk(f'{k} >=6: trung vi % trong so franchise', srcw, r.median_pct, pct(H.wquantile(s6.Y, w, .5)), 1e-7)
    chk(f'{k} >=6: ty le Y<0 trong so franchise', srcw, r.share_lt0, float((w * (s6.Y < 0)).sum() / w.sum()), 1e-9)
L = pd.read_csv(os.path.join(RS56, 'R7_LOFO_ge6_A1b_optional.csv')); d6 = T[T.in_A1b & (T.pos_bin == '>=6')]
mm = [np.median(d6[d6.franchise_id != f].Y) for f in sorted(d6.franchise_id.unique())]
chk('LOFO >=6 (A1b): trung vi % nho nhat', 'R7_LOFO_ge6_A1b_optional.csv', pct(L.median_Y_transition_w.min()), pct(min(mm)), 1e-7); chk('LOFO >=6 (A1b): trung vi % lon nhat', 'R7_LOFO_ge6_A1b_optional.csv', pct(L.median_Y_transition_w.max()), pct(max(mm)), 1e-7)
chk('LOFO >=6: so lan bo', 'R7_LOFO_ge6_A1b_optional.csv', 31, len(mm))
# ---------- 3. PT3
P3 = pd.read_csv(os.path.join(RS56, 'R3_PT3_D_all_samples.csv')).set_index('sample'); srcd = 'inherited_task4_v2/inherited_step5_6/results/R3_PT3_D_all_samples.csv'
for k in ['A1b', 'A0', 'A1', 'A2']:
    dd = D[D['in_' + k]]; r = P3.loc[k]
    chk(f'PT3 {k}: n', srcd, r.n_franchise, len(dd)); chk(f'PT3 {k}: trung vi D', srcd, r.median_D, dd.D.median(), 1e-9); chk(f'PT3 {k}: ty le D<0', srcd, r.share_D_lt0, (dd.D < 0).mean())
dd = D[D.in_A1b]
chk('PT3 A1b: trung vi Y(1->2)', srcd, P3.loc['A1b'].median_Y12, dd.Y12.median(), 1e-9); chk('PT3 A1b: trung vi Y(2->3)', srcd, P3.loc['A1b'].median_Y23, dd.Y23.median(), 1e-9)
chk('PT3 A1b: ty le Y(2->3)<0', srcd, P3.loc['A1b'].share_Y23_lt0, (dd.Y23 < 0).mean())
chk('PT3 A1b: D = Y23 - Y12', srcd, True, bool(np.allclose(dd.D, dd.Y23 - dd.Y12)))
# ---------- 4. PT2-lite
C5 = pd.read_csv(os.path.join(RS4, 'T4_C5_PT2lite_fixed_franchise_sets.csv')); C5b = pd.read_csv(os.path.join(RS4, 'T4_C5b_PT2lite_within_franchise_differences.csv')); srcc5 = 'inherited_task4_v2/results/T4_C5_PT2lite_fixed_franchise_sets.csv'
piv = a1b.pivot_table(index='franchise_id', columns='franchise_position_n', values='Y', aggfunc='first'); have = piv.notna()
for nm, cols in {'B3 = {2,3,4}': [2, 3, 4], 'B4 = {2,3,4,5}': [2, 3, 4, 5]}.items():
    ids = have.index[have[cols].all(axis=1)]; sub = piv.loc[ids, cols]
    chk(f'PT2-lite {nm}: n franchise', srcc5, int(C5[C5.set == nm].n_franchise.iloc[0]), len(ids))
    for c in cols:
        rr = C5[(C5.set == nm) & (C5.position == c)].iloc[0]
        chk(f'PT2-lite {nm}: trung vi % vi tri {c}', srcc5, rr.median_pct, pct(sub[c].median()), 1e-7)
        chk(f'PT2-lite {nm}: cat ngang A1b vi tri {c}', srcc5, rr.cross_section_median_pct, pct(a1b[a1b.franchise_position_n == c].Y.median()), 1e-7)
for k0 in (3, 4):
    ids = have.index[have[[k0, k0 + 1]].all(axis=1)]; dv = piv.loc[ids, k0 + 1] - piv.loc[ids, k0]
    rr = C5b[C5b.set.str.startswith('tat ca') & C5b.contrast.str.contains(rf'Y\({k0}->{k0+1}\)')].iloc[0]
    chk(f'D({k0}->{k0+1}) n', 'T4_C5b_PT2lite_within_franchise_differences.csv', int(rr.n_franchise), len(ids)); chk(f'D({k0}->{k0+1}) trung vi', 'T4_C5b_PT2lite_within_franchise_differences.csv', rr.median_D, dv.median(), 1e-9)
# ---------- 5. CH, dao chieu
ch = a1b[a1b.in_CH_A1b].sort_values(['franchise_id', 'franchise_position_n']); pairs = []; nrev = ad = ai = 0
for f, g in ch.groupby('franchise_id'):
    y = g.Y.values; r_ = [(y[i] < 0) != (y[i + 1] < 0) for i in range(len(y) - 1)]; pairs += r_; nrev += int(any(r_)); ad += int((y < 0).all()); ai += int((y > 0).all())
chk('CH: so franchise', 'T4_C7b / R4b', 58, ch.franchise_id.nunique()); chk('CH: so transition', 'R4b', 234, len(ch)); chk('CH: franchise co >=1 dao chieu', 'R4b', 49, nrev); chk('CH: so cap ke nhau', 'T4_C7_reversal_rate_adjacent_pairs.csv', 176, len(pairs))
chk('CH: so cap dao chieu', 'T4_C7_reversal_rate_adjacent_pairs.csv', 89, int(sum(pairs))); chk('CH: ty le cap dao chieu', 'T4_C7_reversal_rate_adjacent_pairs.csv', float(pd.read_csv(os.path.join(RS4, 'T4_C7_reversal_rate_adjacent_pairs.csv')).set_index('tap_cap').loc['cap_trong_CH'].reversal_share), sum(pairs) / len(pairs))
chk('CH: toan giam', 'R4b', 4, ad); chk('CH: toan tang', 'R4b', 5, ai)
# ---------- 6. ngoai le |Y|>3 (diem)
e = a1b[a1b.Y.abs() > 3]; chk('|Y|>3 trong A1b', 'T4_C6a', 44, len(e)); chk('|Y|>3 duong', 'T4_C6a', 21, int((e.Y > 3).sum())); chk('|Y|>3 am', 'T4_C6a', 23, int((e.Y < -3).sum())); chk('|Y|>3 o vi tri 2', 'T4_C6a', 31, int((e.franchise_position_n == 2).sum()))
ne = a1b[a1b.Y.abs() <= 3]
C6 = pd.read_csv(os.path.join(RS4, 'T4_C6_extreme_Y_scenario.csv')); r = C6[(C6.contrast == 'A1b: bo |Y|>3 - giu') & (C6.group == '>=6') & (C6.statistic == 'median')].iloc[0]
chk('bo |Y|>3: trung vi >=6 sau', 'T4_C6_extreme_Y_scenario.csv', r.pct_to, pct(ne[ne.pos_bin == '>=6'].Y.median()), 1e-7)
# ---------- 7. thanh phan (vi tri 2)
p2 = a1b[a1b.franchise_position_n == 2]; fD = set(D[D.in_A1b].franchise_id); fC = set(a1b[a1b.in_CH_A1b].franchise_id); C2 = pd.read_csv(os.path.join(RS4, 'T4_C2_pos2_composition_PT3_CH_vs_main.csv')).set_index('nhom')
for lab, sub in (('Mau PT3 (co Y o vi tri 2 va 3)', p2[p2.franchise_id.isin(fD)]), ('Ngoai mau PT3 (co Y vt2, khong co Y vt3)', p2[~p2.franchise_id.isin(fD)]), ('Mau CH (chuoi Y lien tuc >=3 transition)', p2[p2.franchise_id.isin(fC)]), ('Ngoai mau CH', p2[~p2.franchise_id.isin(fC)])):
    chk(f'Vi tri 2, {lab}: n', 'T4_C2', int(C2.loc[lab].n_franchise), len(sub)); chk(f'Vi tri 2, {lab}: trung vi %', 'T4_C2', C2.loc[lab].median_pct, pct(sub.Y.median()), 1e-7)
# ---------- 8. CI: doc lai tu npz va chay lai co muc tieu
z = np.load(os.path.join(RS56, 'bootstrap_reps_PT1_A1b.npz')); okci = True
for g in GR:
    r = P[(P['sample'] == 'A1b') & (P.group == g)].iloc[0]
    for key, lo, hi in ((f'{g}__med', 'median_Y_ci_lo', 'median_Y_ci_hi'), (f'{g}__lt0', 'share_lt0_ci_lo', 'share_lt0_ci_hi')):
        okci &= abs(np.percentile(z[key], 2.5) - r[lo]) < 1e-12 and abs(np.percentile(z[key], 97.5) - r[hi]) < 1e-12
chk('PT1 A1b: CI trong R2 = percentile 2,5/97,5 cua 10.000 ban lap luu (6 nhom x 2 dai luong)', 'bootstrap_reps_PT1_A1b.npz', True, bool(okci), status='T5-KT (CI)')
if not a.skip_ci:
    cfg = json.load(open(os.path.join(S56, 'config.json'))); B = cfg['bootstrap']['B']; seed = cfg['bootstrap']['seed']
    boot = E.Boot(dd.franchise_id.unique(), B=B, seed=seed); pts, reps = E.run({'m': E.Def(dd.D.values, dd.franchise_id.values, 'wq'), 'l': E.Def(dd.D.values, dd.franchise_id.values, 'lt0')}, boot)
    chk('PT3 A1b: CI 95% trung vi D (chay lai muc tieu 10.000 lan, seed 20260101) - can duoi', srcd, P3.loc['A1b'].median_D_ci_lo, float(np.percentile(reps['m'], 2.5)), 1e-12, 'T5-KT (CI)')
    chk('PT3 A1b: CI 95% trung vi D - can tren', srcd, P3.loc['A1b'].median_D_ci_hi, float(np.percentile(reps['m'], 97.5)), 1e-12, 'T5-KT (CI)')
    ids = have.index[have[[2, 3, 4]].all(axis=1)]; boot = E.Boot(ids, B=B, seed=seed); sub = piv.loc[ids, [2, 3, 4]]
    pts, reps = E.run({'m2': E.Def(sub[2].values, ids, 'wq'), 'm3': E.Def(sub[3].values, ids, 'wq')}, boot); b3 = C5[C5.set == 'B3 = {2,3,4}'].set_index('position')
    chk('PT2-lite {2,3,4}: CI trung vi % vi tri 2 - can duoi', srcc5, b3.loc[2].median_pct_ci_lo, pct(np.percentile(reps['m2'], 2.5)), 1e-7, 'T5-KT (CI)'); chk('PT2-lite {2,3,4}: CI trung vi % vi tri 3 - can tren', srcc5, b3.loc[3].median_pct_ci_hi, pct(np.percentile(reps['m3'], 97.5)), 1e-7, 'T5-KT (CI)')
# ---------- 9. nhom 11 franchise (tu file tho) + khoang ngay
R10c = pd.read_csv(os.path.join(RS4, 'R10c_G3_verification_11_franchises.csv'))
chk('R10c: so franchise', 'R10c_G3_verification_11_franchises.csv', 11, len(R10c)); chk('R10c: ngay phim 3 som nhat', 'R10c', '2026-11-04', R10c.film3_release_date_in_data.min()); chk('R10c: ngay phim 3 muon nhat', 'R10c', '2028-12-13', R10c.film3_release_date_in_data.max())
chk('R10c: moi franchise cap 2->3, unreleased_film, ngay sau retrieval', 'R10c', True, bool(((R10c.chain_pos_prev == 2) & (R10c.chain_pos_curr == 3) & (R10c.exclusion_reason == 'unreleased_film') & (R10c.film3_release_after_retrieval) & (R10c.film2_of_pair_equals_film2_with_Y)).all()))
if a.raw and os.path.exists(os.path.join(a.raw, 'pairs_audit.csv')):
    pa = pd.read_csv(os.path.join(a.raw, 'pairs_audit.csv'), low_memory=False, usecols=['film_key_curr', 'release_date_curr', 'chain_pos_prev', 'chain_pos_curr', 'exclusion_reason', 'is_unreleased_curr', 'technically_valid'])
    x = pa[pa.film_key_curr.isin(R10c.film3_key)]; x = x[(x.chain_pos_prev == 2) & (x.chain_pos_curr == 3)]
    chk('R10c vs pairs_audit goc: 11 cap 2->3 co ton tai, khong hop le ky thuat, cho unreleased_film', 'pairs_audit.csv (raw)', True, bool(len(x) == 11 and (x.technically_valid == False).all() and (x.exclusion_reason == 'unreleased_film').all()))
    chk('R10c vs pairs_audit goc: khoang ngay phim 3', 'pairs_audit.csv (raw)', '2026-11-04..2028-12-13', f"{pd.to_datetime(x.release_date_curr).min().date()}..{pd.to_datetime(x.release_date_curr).max().date()}")
    fl = pd.read_csv(os.path.join(a.raw, 'analysis_master_films.csv'), usecols=['raw_movies__retrieval_date'], low_memory=False); rd = pd.to_datetime(fl.raw_movies__retrieval_date, errors='coerce')
    chk('films: retrieval_date duy nhat tren 39.871 dong', 'analysis_master_films.csv (raw)', '2026-10-22 x 39871', f"{rd.min().date()} x {int((rd == rd.min()).sum())}" if rd.nunique() == 1 else f'nunique={rd.nunique()}')
    chk('R10c: phim 3 muon nhat (ten)', 'R10c', 'Black Panther 3', R10c.sort_values('film3_release_date_in_data').iloc[-1].film3_title)
    ob = pd.read_csv(os.path.join(RS4, 'R10b_observability_per_franchise.csv')); chk('R10b: 176/67/258/11 nhom', 'R10b_observability_per_franchise.csv', '176/67/258/11', '/'.join(str(int((ob.group.str.startswith(g)).sum())) for g in ['G0', 'G1', 'G2', 'G3']))
else:
    rows.append(dict(item='R10c doi chieu voi pairs_audit.csv goc', source_file='pairs_audit.csv (raw)', value_in_task4_or_inherited='', value_recomputed_task5='', match='', status='KHONG CHAY (thieu --raw)'))
V = pd.DataFrame(rows); V.to_csv(os.path.join(OUT, 'T5_numbers_check.csv'), index=False, encoding='utf-8-sig')
msg = [f'T5 kiem tra: {len(V)} muc; khop {int((V.match == True).sum())}; khong khop {len(fails)}; khong chay {int((V.status.str.startswith("KHONG")).sum())}']
if fails: msg += ['KHONG KHOP: ' + '; '.join(fails)]
print('\n'.join(msg)); open(os.path.join(R, 'logs', 't5_01_verify_log.txt'), 'w', encoding='utf-8').write('\n'.join(msg) + '\n')
if fails: sys.exit(1)
