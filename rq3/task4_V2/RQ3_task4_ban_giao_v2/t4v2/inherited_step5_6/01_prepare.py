"""RQ3 Buoc 5 - chuan bi dau vao. Doc master + file ID/co, kiem tra, tai lap A0/A1b/A1/A2, tao bang dau vao.
Chay: python code/01_prepare.py --root .   (config.json nam o thu muc goc)
Khong impute, khong loai ngoai le, khong chuan hoa. Dung ngay khi mot kiem tra that bai."""
import argparse, json, os, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--master', default=None)
ap.add_argument('--bo_detailed', default=None)
ap.add_argument('--bo_raw', default=None)
a = ap.parse_args()
R = a.root
cfg = json.load(open(os.path.join(R, 'config.json')))
master_p = a.master or cfg['inputs']['master']
bo_p = a.bo_detailed or cfg['inputs']['box_office_detailed']
bor_p = a.bo_raw or cfg['inputs'].get('box_office_raw', bo_p.replace('box_office_detailed', 'box_office_raw'))
REF = os.path.join(R, 'ref_step3_step4')
OUT = os.path.join(R, 'input_tables')
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(R, 'logs'), exist_ok=True)
log = []


def flush():
    open(os.path.join(R, 'logs', '01_prepare_log.txt'), 'w', encoding='utf-8').write('\n'.join(log))


def say(*x):
    s = ' '.join(str(i) for i in x)
    print(s)
    log.append(s)


def check(cond, msg):
    say(('PASS ' if cond else 'FAIL ') + msg)
    if not cond:
        flush()
        sys.exit('FAIL: ' + msg)


# ---- 1. master
m = pd.read_csv(master_p, low_memory=False, encoding='utf-8-sig')
say('master', m.shape)
check(m.transition_id.is_unique, 'master transition_id duy nhat')
A0 = m[m.Y.notna()].copy()
check(len(A0) == 918 and A0.transition_id.is_unique, f'A0 co Y = {len(A0)} dong (moc 918)')
check(bool(np.isfinite(A0.Y).all()), 'Y huu han tren A0')
check(bool((A0.open_prev > 0).all() and (A0.open_curr > 0).all()), 'opening > 0 tren A0')
check(bool(np.allclose(np.log(A0.open_curr) - np.log(A0.open_prev), A0.Y)), 'Y = ln(open_curr) - ln(open_prev)')
check(bool((A0.franchise_position_n >= 2).all()), 'franchise_position_n >= 2')
check(bool(A0.modeling_eligible.astype(str).str.lower().isin(['true', '1']).all()), 'modeling_eligible tren A0')
check(not A0.duplicated(['franchise_id', 'franchise_position_n']).any(), 'moi franchise toi da 1 transition moi vi tri')
say('A0:', len(A0), 'transition /', A0.franchise_id.nunique(), 'franchise')

# ---- 2. doi chieu voi file raw goc
det = pd.read_csv(bo_p).set_index('film_key')
for s in ('prev', 'curr'):
    k = A0['film_key_' + s]
    check(bool(np.isclose(k.map(det.opening_weekend_gross), A0['open_' + s]).all()), f'open_{s} khop box_office_detailed.csv goc (918/918)')
d = det.dropna(subset=['opening_weekend_gross'])
n = d.groupby(['opening_weekend_gross', 'domestic_gross'], dropna=False).imdb_id.transform('size')
dup_fk = set(d[n > 1].index)
A0['f_dup_value_across_films'] = A0.film_key_prev.isin(dup_fk) | A0.film_key_curr.isin(dup_fk)
au = pd.read_csv(os.path.join(REF, 'audit_suspect_pairs_v3.csv'), encoding='utf-8-sig')
check(set(A0[A0.f_dup_value_across_films].transition_id) == set(au[au.f_dup_value_across_films.astype(bool)].transition_id),
      'co trung gia tri tinh lai tu raw = co trong audit v3 (7 cap)')
dom_p = A0.film_key_prev.map(det.domestic_gross)
dom_c = A0.film_key_curr.map(det.domestic_gross)
A0['f_open_gt_domestic'] = (A0.open_prev > dom_p) | (A0.open_curr > dom_c)
check(set(A0[A0.f_open_gt_domestic].transition_id) == set(au[au.f_open_gt_domestic.astype(bool)].transition_id),
      'co open>domestic tinh lai tu raw = audit v3 (4 cap)')
rg = pd.read_csv(bor_p).set_index('film_key').global_gross
A0['f_open_gt_global'] = (A0.open_prev > A0.film_key_prev.map(rg)) | (A0.open_curr > A0.film_key_curr.map(rg))
A0['f_small_lt100k'] = (A0.open_prev < 1e5) | (A0.open_curr < 1e5)

# ---- 3. mau
A0['nghi_van_8'] = A0.f_open_gt_domestic | A0.f_dup_value_across_films
A0['global_only_3'] = (~A0.nghi_van_8) & A0.f_open_gt_global
S = {'A0': pd.Series(True, index=A0.index)}
S['A1b'] = ~A0.nghi_van_8
S['A1'] = S['A1b'] & ~A0.global_only_3
S['A2'] = S['A1'] & ~A0.f_small_lt100k
for k, v in S.items():
    d_ = A0[v]
    say(f'{k}: {len(d_)} transition / {d_.franchise_id.nunique()} franchise')
    check(len(d_) == cfg['samples'][k] and d_.franchise_id.nunique() == cfg['expected_franchises'][k], f'{k} khop moc {cfg["samples"][k]}/{cfg["expected_franchises"][k]}')


def ids(f):
    return set(pd.read_csv(os.path.join(REF, f), encoding='utf-8-sig').transition_id)


check(ids('ids_A0_ref_all_Y_v3.csv') == set(A0.transition_id), 'A0 = ids_A0_ref_all_Y_v3.csv')
check(ids('ids_A1_drop_suspect_v3.csv') == set(A0[S['A1']].transition_id), 'A1 = ids_A1_drop_suspect_v3.csv')
check(ids('ids_A2_drop_suspect_and_lt100k_v3.csv') == set(A0[S['A2']].transition_id), 'A2 = ids_A2_drop_suspect_and_lt100k_v3.csv')
check(ids('ids_A1b.csv') == set(A0[S['A1b']].transition_id), 'A1b = ids_A1b.csv (buoc 4)')
check(int(A0.nghi_van_8.sum()) == 8 and int(A0.global_only_3.sum()) == 3, '8 cap nghi van; 3 cap chi co global')
check(set(A0[S['A2']].transition_id) < set(A0[S['A1']].transition_id) < set(A0[S['A1b']].transition_id) < set(A0.transition_id), 'A2 < A1 < A1b < A0 long nhau')
chk = A0[['transition_id']].merge(m, on='transition_id', how='left', validate='1:1', indicator=True)
check(bool((chk._merge == 'both').all()) and len(chk) == 918, 'noi ID-master 1:1, khong mat/nhan dong')

# ---- 4. bang transition
A0['pos_bin'] = np.where(A0.franchise_position_n >= 6, '>=6', A0.franchise_position_n.astype(int).astype(str))
A0['sign3'] = np.select([A0.Y < 0, A0.Y == 0], ['giam', 'bang'], 'tang')
A0['pct_change'] = 100 * (np.exp(A0.Y) - 1)
A0['decade'] = (A0.release_year_n // 10 * 10).astype(int)
for k in S:
    A0['in_' + k] = S[k].values
cols = ['transition_id', 'franchise_id', 'franchise_position_n', 'pos_bin', 'film_key_prev', 'film_key_curr', 'title_prev', 'title_curr',
        'release_date_prev', 'release_date_curr', 'release_year_n', 'decade', 'gap_years', 'open_prev', 'open_curr', 'Y', 'pct_change', 'sign3',
        'f_open_gt_domestic', 'f_dup_value_across_films', 'f_open_gt_global', 'f_small_lt100k', 'nghi_van_8', 'global_only_3',
        'in_A0', 'in_A1b', 'in_A1', 'in_A2']
T = A0[cols].sort_values(['franchise_id', 'franchise_position_n']).reset_index(drop=True)

# ---- 5. bang D
t2 = T[T.franchise_position_n == 2].set_index('franchise_id')
t3 = T[T.franchise_position_n == 3].set_index('franchise_id')
both = t2.index.intersection(t3.index)
Dt = pd.DataFrame({
    'franchise_id': both,
    'transition_id_12': t2.loc[both, 'transition_id'].values, 'transition_id_23': t3.loc[both, 'transition_id'].values,
    'film1': t2.loc[both, 'film_key_prev'].values, 'film2_in_12': t2.loc[both, 'film_key_curr'].values,
    'film2_in_23': t3.loc[both, 'film_key_prev'].values, 'film3': t3.loc[both, 'film_key_curr'].values,
    'O1': t2.loc[both, 'open_prev'].values, 'O2_from_12': t2.loc[both, 'open_curr'].values,
    'O2_from_23': t3.loc[both, 'open_prev'].values, 'O3': t3.loc[both, 'open_curr'].values,
    'Y12': t2.loc[both, 'Y'].values, 'Y23': t3.loc[both, 'Y'].values})
check(bool((Dt.film2_in_12 == Dt.film2_in_23).all() and np.allclose(Dt.O2_from_12, Dt.O2_from_23)),
      f'hai transition noi dung cung phim 2 (film_key va opening) tren {len(Dt)} franchise')
Dt['D'] = Dt.Y23 - Dt.Y12
check(bool(np.allclose(Dt.D, np.log(Dt.O3) - 2 * np.log(Dt.O2_from_12) + np.log(Dt.O1))), 'D = Y23 - Y12 = ln O3 - 2 ln O2 + ln O1')
for k in S:
    Dt['in_' + k] = (Dt.transition_id_12.isin(A0[S[k]].transition_id) & Dt.transition_id_23.isin(A0[S[k]].transition_id)).values
    say(f'D {k}: {int(Dt["in_" + k].sum())} franchise (moc {cfg["D_expected_franchises"][k]})')
check(all(int(Dt['in_' + k].sum()) == cfg['D_expected_franchises'][k] for k in S), 'co mau D khop moc buoc 4')
Dt.to_csv(os.path.join(OUT, 'T2_D_table_franchises_with_Y2_and_Y3.csv'), index=False)

# ---- 6. chuoi CH (ID buoc 3, khong tu mo rong)
CH = {}
for k, f in (('A0', 'ids_B_full_chain_ge3_on_A0_ref_all_Y_v3.csv'), ('A1', 'ids_B_full_chain_ge3_on_A1_drop_suspect_v3.csv'),
             ('A2', 'ids_B_full_chain_ge3_on_A2_drop_suspect_and_lt100k_v3.csv')):
    b = pd.read_csv(os.path.join(REF, f), encoding='utf-8-sig')
    CH[k] = b
    say(f'CH ({k}): {len(b)} transition / {b.franchise_id.nunique()} franchise')
check(set(CH['A0'].transition_id) == set(CH['A1'].transition_id), 'CH(A0) = CH(A1) cung ID')
check(set(CH['A1'].transition_id) <= set(A0[S['A1b']].transition_id), 'moi ID CH thuoc A1b -> CH(A1b) = CH(A1) (khong mo rong)')
check(len(CH['A1']) == 234 and CH['A1'].franchise_id.nunique() == 58 and len(CH['A2']) == 225 and CH['A2'].franchise_id.nunique() == 55,
      'CH 58/234 (A1b) va 55/225 (A2) khop moc')
T['in_CH_A1b'] = T.transition_id.isin(CH['A1'].transition_id)
T['in_CH_A2'] = T.transition_id.isin(CH['A2'].transition_id)
check(int(T.in_CH_A1b.sum()) == 234 and int(T.in_CH_A2.sum()) == 225, 'noi CH-master 1:1')
g = T[T.in_CH_A1b].groupby('franchise_id').franchise_position_n.apply(lambda s: sorted(s) == list(range(2, 2 + len(s))))
check(bool(g.all()), 'CH: vi tri lien tuc tu 2 trong moi franchise')
T.to_csv(os.path.join(OUT, 'T1_transitions_A0_with_sample_flags.csv'), index=False, encoding='utf-8-sig')
T[T.in_CH_A1b][['transition_id', 'franchise_id', 'franchise_position_n', 'Y', 'in_CH_A2']].to_csv(os.path.join(OUT, 'T3_chain_CH_transitions.csv'), index=False)
say('xuat T1', T.shape)

# ---- 7. do phu + cỡ mau
cov = T[T.in_A1b].pivot_table(index='pos_bin', columns='decade', values='Y', aggfunc='size', fill_value=0).reindex(['2', '3', '4', '5', '>=6'])
cov.to_csv(os.path.join(OUT, 'T4_coverage_position_by_decade_A1b.csv'))
cnt = []
for k in S:
    q = T[T['in_' + k]].groupby('pos_bin').agg(n_transition=('Y', 'size'), n_franchise=('franchise_id', 'nunique')).reindex(['2', '3', '4', '5', '>=6']).reset_index()
    q.insert(0, 'sample', k)
    cnt.append(q)
pd.concat(cnt).to_csv(os.path.join(OUT, 'T5_sample_sizes_by_position.csv'), index=False)
say('Y=0 trong A0:', int((T.Y == 0).sum()), '| Y=0 trong A1b:', int(((T.Y == 0) & T.in_A1b).sum()))
say('|Y|>3 trong A1b (chi bao cao, khong loai):', int(((T.Y.abs() > 3) & T.in_A1b).sum()))
say('OK buoc 5')
flush()
