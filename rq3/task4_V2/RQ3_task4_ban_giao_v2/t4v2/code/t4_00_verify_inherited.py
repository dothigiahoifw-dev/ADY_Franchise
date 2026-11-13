"""Task 4 / RQ3 - kiem tra ket qua ke thua (buoc 5-6) truoc khi dung.
Tai tinh DOC LAP bang pandas/numpy (khong dung engine) cac uoc luong diem; doi chieu CI voi npz; doi chieu CI voi helper v4 day du 10.000 lan tren 2 o.
Chay: python code/t4_00_verify_inherited.py --root .   (root chua inherited_step5_6/)"""
import argparse, os, sys, hashlib, json
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument('--root', default='.'); ap.add_argument('--with_helper', action='store_true', help='chay them helper day du 10.000 lan (rat cham, ~80 phut); mac dinh tat, xem t4_00b'); a = ap.parse_args()
R = a.root; INH = os.path.join(R, 'inherited_step5_6'); sys.path.insert(0, os.path.join(R, 'code'))
import rq3_stats_helpers as H
RS = os.path.join(INH, 'results'); IN = os.path.join(INH, 'input_tables')
log = []; bad = []
def say(s):
    print(s); log.append(s)
def chk(c, m):
    say(('PASS ' if c else 'FAIL ') + m)
    if not c: bad.append(m)
T = pd.read_csv(os.path.join(IN, 'T1_transitions_A0_with_sample_flags.csv'))
P = pd.read_csv(os.path.join(RS, 'R2_PT1_by_position_all_samples.csv'))
POS = ['2', '3', '4', '5', '>=6']; GR = POS + ['ALL']
# 1. diem uoc luong PT1 doc lap
mx = 0
for k in ['A0', 'A1b', 'A1', 'A2']:
    d = T[T['in_' + k]]
    for g in GR:
        s = d if g == 'ALL' else d[d.pos_bin == g]
        r = P[(P['sample'] == k) & (P.group == g)].iloc[0]
        y = s.Y.values
        vals = [(len(s), r.n_transition), (s.franchise_id.nunique(), r.n_franchise), (np.median(y), r.median_Y), (np.percentile(y, 25), r.q1_Y), (np.percentile(y, 75), r.q3_Y),
                ((y < 0).mean(), r.share_lt0), ((y == 0).mean(), r.share_eq0), ((y > 0).mean(), r.share_gt0), (100 * (np.exp(np.median(y)) - 1), r.median_pct)]
        mx = max(mx, max(abs(a_ - b_) for a_, b_ in vals))
chk(mx < 1e-9, f'PT1: n, F, trung vi, Q1, Q3, ty le, %: tai tinh doc lap khop R2 tren 4 mau x 6 nhom (sai lech toi da {mx:.1e})')
# 2. bootstrap khong rong o nao
nancols = [c for c in P.columns if c.endswith('_boot_nan')]
chk(int(P[nancols].sum().sum()) == 0, 'PT1: khong co lan lap nao bi bo vi o rong (tong boot_nan = 0)')
# 3. CI tu npz == CI trong R2 (A1b)
z = np.load(os.path.join(RS, 'bootstrap_reps_PT1_A1b.npz'))
ok = True
for g in GR:
    r = P[(P['sample'] == 'A1b') & (P.group == g)].iloc[0]
    for key, lo, hi in ((f'{g}__med', 'median_Y_ci_lo', 'median_Y_ci_hi'), (f'{g}__lt0', 'share_lt0_ci_lo', 'share_lt0_ci_hi')):
        v = z[key]; ok &= abs(np.percentile(v, 2.5) - r[lo]) < 1e-12 and abs(np.percentile(v, 97.5) - r[hi]) < 1e-12 and len(v) == 10000
chk(ok, 'PT1 A1b: CI trong R2 = percentile 2,5/97,5 cua 10.000 ban lap luu trong npz')
# 4. PT3 doc lap
D = pd.read_csv(os.path.join(IN, 'T2_D_table_franchises_with_Y2_and_Y3.csv')); P3 = pd.read_csv(os.path.join(RS, 'R3_PT3_D_all_samples.csv')).set_index('sample')
mx = 0
for k in ['A0', 'A1b', 'A1', 'A2']:
    d = D[D['in_' + k]]; r = P3.loc[k]
    mx = max(mx, abs(len(d) - r.n_franchise), abs(d.D.median() - r.median_D), abs((d.D < 0).mean() - r.share_D_lt0), abs(d.Y12.median() - r.median_Y12), abs(d.Y23.median() - r.median_Y23))
    chk(bool(np.allclose(d.D, d.Y23 - d.Y12)) and (d.film2_in_12 == d.film2_in_23).all(), f'PT3 {k}: D = Y23-Y12, hai transition chung phim 2')
chk(mx < 1e-9, f'PT3: n, trung vi D, ty le D<0, trung vi Y12/Y23 khop R3 (sai lech {mx:.1e})')
# 5. CH doc lap
ch = T[T.in_CH_A1b].sort_values(['franchise_id', 'franchise_position_n']); nrev = 0; allD = allI = 0
for f, g in ch.groupby('franchise_id'):
    y = g.Y.values; nrev += int(any((y[i] < 0 < y[i + 1]) or (y[i] > 0 > y[i + 1]) for i in range(len(y) - 1)))
    allD += int((y < 0).all()); allI += int((y > 0).all())
S = pd.read_csv(os.path.join(RS, 'R4b_PT4_sign_patterns.csv')); s = S[(S.chain_sample == 'CH_A1b') & (S.sign_pattern == '__SUMMARY__')].iloc[0]
chk((ch.franchise_id.nunique(), len(ch), nrev, allD, allI) == (58, 234, int(s.n_with_ge1_reversal), int(s.n_all_decrease), int(s.n_all_increase)) and nrev == 49, f'CH: 58/234; >=1 dao chieu {nrev}; toan giam {allD}; toan tang {allI} khop R4b')
# 6. LOFO >=6 doc lap
L = pd.read_csv(os.path.join(RS, 'R7_LOFO_ge6_A1b_optional.csv')); d6 = T[T.in_A1b & (T.pos_bin == '>=6')]
mm = [np.median(d6[d6.franchise_id != f].Y) for f in L.dropped_franchise]
chk(np.allclose(mm, L.median_Y_transition_w) and len(L) == 31, 'LOFO >=6: 31 lan bo, trung vi (transition ngang nhau) tai tinh doc lap khop R7')
# 7. R8 so voi R2/R3 (chuoi dinh dang) cho PT1 chinh va PT3
M = pd.read_csv(os.path.join(RS, 'R8_test_matrix.csv'), encoding='utf-8-sig'); good = True
pc = lambda x: f'{x:+.1f}%'
for g in GR:
    r = P[(P['sample'] == 'A1b') & (P.group == g)].iloc[0]
    row = M[(M['Phương án'] == 'PT1 CHÍNH') & M['Đại lượng'].str.contains({'ALL': 'toàn mẫu'}.get(g, f'Vị trí {"≥6" if g == ">=6" else g}:' ))]
    good &= len(row) == 1 and pc(r.median_pct) in row.iloc[0]['Kết quả'] and f'{r.share_lt0:.1%}' in row.iloc[0]['Kết quả']
chk(good, 'R8: 6 dong PT1 CHINH chua dung trung vi % va ty le Y<0 cua R2')
r = P3.loc['A1b']; row = M[M['Phương án'] == 'PT3 CHÍNH'].iloc[0]['Kết quả']
chk(f'{r.median_D:+.3f}' in row and f'{r.share_D_lt0:.1%}' in row, 'R8: dong PT3 CHINH khop R3')
# 8. nhan R5 (phat hien khi doc)
R5 = pd.read_csv(os.path.join(RS, 'R5_sensitivity_paired_differences.csv'))
w = R5[R5.contrast == 'weights']
say(f'LUU Y R5: {len(w)} dong trong so co contrast="weights" va khong co cot mau rieng (mau nam trong from_/to_); dong A0 va A1b trung gia tri vi nhom >=6 giong het nhau (khong co cap bi loai o >=6 giua A0 va A1b)')
# 9. helper day du 10.000 lan tren 2 o (cung seed)
if a.with_helper:
    d = T[T.in_A1b].reset_index(drop=True); blocks = [g.index.values for _, g in d.groupby('franchise_id', sort=True)]
    rng = np.random.default_rng(20260101); r2, r6w = [], []
    for b in range(10000):
        idx, pick = H.cluster_bootstrap_indices(blocks, rng); x = H.resampled(d, blocks, pick)
        s2 = x[x.pos_bin == '2']; r2.append(H.wquantile(s2.Y, np.ones(len(s2)), .5))
        s6 = x[x.pos_bin == '>=6']; r6w.append((lambda w_: (w_ * (s6.Y < 0)).sum() / w_.sum())(H.franchise_weights(s6, 'boot_cluster').values))
    a2 = np.percentile(r2, [2.5, 97.5]); a6 = np.percentile(r6w, [2.5, 97.5])
    q = P[(P['sample'] == 'A1b') & (P.group == '2')].iloc[0]; W6 = pd.read_csv(os.path.join(RS, 'R6_weighting_ge6_transition_vs_franchise.csv'))
    w6 = W6[(W6['sample'] == 'A1b') & (W6.scheme == 'franchise_equal_1_over_kf')].iloc[0]
    chk(abs(a2[0] - q.median_Y_ci_lo) < 1e-12 and abs(a2[1] - q.median_Y_ci_hi) < 1e-12, 'helper v4 10.000 lan: CI trung vi vi tri 2 (A1b) = R2')
    chk(abs(a6[0] - w6.share_lt0_ci_lo) < 1e-12 and abs(a6[1] - w6.share_lt0_ci_hi) < 1e-12, 'helper v4 10.000 lan: CI ty le Y<0 trong so 1/k_f nhom >=6 (A1b) = R6')
# 10. hash goi buoc 5-6
z5 = '/mnt/user-data/outputs/RQ3_buoc5_6_ban_giao.zip'
if os.path.exists(z5):
    say('md5 goi buoc 5-6: ' + hashlib.md5(open(z5, 'rb').read()).hexdigest())
open(os.path.join(R, 'logs', 't4_00_verify_inherited_log.txt'), 'w', encoding='utf-8').write('\n'.join(log))
if bad: sys.exit('CO KIEM TRA THAT BAI: ' + '; '.join(bad))
say('OK: ket qua ke thua duoc xac nhan.')
