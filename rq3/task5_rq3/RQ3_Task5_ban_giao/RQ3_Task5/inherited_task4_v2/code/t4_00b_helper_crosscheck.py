"""Doi chieu CI voi helper v4 (rq3_stats_helpers) day du 10.000 lan, cung seed, chay theo tung dot de khong bi gioi han thoi gian.
Cac o: PT1 A1b vi tri 2 (trung vi) va nhom >=6 ty le Y<0 trong so 1/k_f. Chay lap lai den khi xong:  python code/t4_00b_helper_crosscheck.py --root . --chunk 1500"""
import argparse, os, sys, pickle, time
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument('--root', default='.'); ap.add_argument('--chunk', type=int, default=1500); a = ap.parse_args()
R = a.root; sys.path.insert(0, os.path.join(R, 'code')); import rq3_stats_helpers as H
INH = os.path.join(R, 'inherited_step5_6'); T = pd.read_csv(os.path.join(INH, 'input_tables', 'T1_transitions_A0_with_sample_flags.csv'))
d = T[T.in_A1b].reset_index(drop=True); blocks = [g.index.values for _, g in d.groupby('franchise_id', sort=True)]
ck = os.path.join(R, 'logs', 'helper_crosscheck_state.pkl'); NB = 10000
st = pickle.load(open(ck, 'rb')) if os.path.exists(ck) else dict(done=0, r2=[], r6w=[], state=np.random.default_rng(20260101).bit_generator.state)
rng = np.random.default_rng(0); rng.bit_generator.state = st['state']; t0 = time.time()
while st['done'] < NB and time.time() - t0 < 240 and (st['done'] % a.chunk != 0 or st['done'] == 0 or time.time() - t0 < 1) :
    idx, pick = H.cluster_bootstrap_indices(blocks, rng); x = H.resampled(d, blocks, pick)
    s2 = x[x.pos_bin == '2']; st['r2'].append(H.wquantile(s2.Y, np.ones(len(s2)), .5))
    s6 = x[x.pos_bin == '>=6']; w_ = H.franchise_weights(s6, 'boot_cluster').values; st['r6w'].append((w_ * (s6.Y < 0)).sum() / w_.sum()); st['done'] += 1
st['state'] = rng.bit_generator.state; pickle.dump(st, open(ck, 'wb')); print('done', st['done'], 'of', NB, f'({time.time()-t0:.0f}s)')
if st['done'] >= NB:
    RS = os.path.join(INH, 'results'); P = pd.read_csv(os.path.join(RS, 'R2_PT1_by_position_all_samples.csv')); q = P[(P['sample'] == 'A1b') & (P.group == '2')].iloc[0]
    W6 = pd.read_csv(os.path.join(RS, 'R6_weighting_ge6_transition_vs_franchise.csv')); w6 = W6[(W6['sample'] == 'A1b') & (W6.scheme == 'franchise_equal_1_over_kf')].iloc[0]
    a2 = np.percentile(st['r2'], [2.5, 97.5]); a6 = np.percentile(st['r6w'], [2.5, 97.5])
    ok1 = abs(a2[0] - q.median_Y_ci_lo) < 1e-12 and abs(a2[1] - q.median_Y_ci_hi) < 1e-12; ok2 = abs(a6[0] - w6.share_lt0_ci_lo) < 1e-12 and abs(a6[1] - w6.share_lt0_ci_hi) < 1e-12
    msg = f'helper v4 10.000 lan: CI trung vi vi tri 2 (A1b) = R2: {ok1}; CI ty le Y<0 trong so 1/k_f nhom >=6 (A1b) = R6: {ok2}'
    print(msg); open(os.path.join(R, 'logs', 't4_00b_helper_crosscheck_log.txt'), 'w').write(msg + '\n')
