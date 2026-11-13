"""ADY RQ3 Buoc 4 - tao mau A1b (de xuat mau chinh) tu A0 + co audit. Chi tao mau/kiem tra; KHONG chay phan tich chinh, KHONG bootstrap.
Chay:  python build_A1b.py --master analysis_master_transitions.csv --audit audit_suspect_pairs_v3.csv --out .
Quy tac A1b (dat truoc, theo bang chung ban ghi, khong dua vao ket qua):
  A0  = moi transition co Y (modeling_eligible)
  nghi_van_8 = (open > domestic cua phim_prev hoac phim_curr) HOAC (cap (opening, domestic) trung giua cac phim khac nhau)
  A1b = A0 tru nghi_van_8
  A1  = A1b tru 3 cap chi bi co global (open > global; cac cap nay cung co global < domestic - mau thuan giua truong, chua chung minh global sai)
  A2  = A1 tru cap co open_prev<1e5 hoac open_curr<1e5 (kich ban do nhay; tien te/cua so opening chua xac minh)
"""
import argparse, os, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--master', default='analysis_master_transitions.csv')
ap.add_argument('--audit', default='audit_suspect_pairs_v3.csv')
ap.add_argument('--out', default='.')
ap.add_argument('--ids_A1_ref', default='', help='(tuy chon) ids_A1_drop_suspect_v3.csv de doi chieu')
ap.add_argument('--ids_A2_ref', default='', help='(tuy chon) ids_A2_drop_suspect_and_lt100k_v3.csv de doi chieu')
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
P = lambda f: os.path.join(a.out, f)
log = []
def say(*x):
    s = ' '.join(str(i) for i in x); print(s); log.append(s)

# ---------- 1. nap + kiem tra master
m = pd.read_csv(a.master, low_memory=False, encoding='utf-8-sig')
assert m.transition_id.is_unique, 'transition_id trung trong master'
A0 = m[m.Y.notna()].copy()
assert A0.transition_id.is_unique and (A0.modeling_eligible.astype(str).str.lower().isin(['true','1'])).all()
assert (A0.open_prev > 0).all() and (A0.open_curr > 0).all()
assert np.allclose(np.log(A0.open_curr) - np.log(A0.open_prev), A0.Y), 'Y khong khop cong thuc'
assert (A0.franchise_position_n >= 2).all()
say('master', m.shape, '| A0 =', len(A0), 'transition /', A0.franchise_id.nunique(), 'franchise')

# doi chieu opening voi cot raw NHUNG trong master (khong phai file box_office_*.csv goc)
for s in ('prev', 'curr'):
    c = f'raw_box_office_detailed__opening_weekend_gross_{s}'
    if c in A0:
        ok = np.isclose(A0[f'open_{s}'], A0[c], equal_nan=False)
        say(f'open_{s} khop {c}: {ok.sum()}/{len(A0)}')

# ---------- 2. co audit (tinh lai tu master)
dom_p = A0['raw_box_office_detailed__domestic_gross_prev']; dom_c = A0['raw_box_office_detailed__domestic_gross_curr']
glo_p = A0['raw_box_office_raw__global_gross_prev'];       glo_c = A0['raw_box_office_raw__global_gross_curr']
A0['f_open_gt_domestic'] = (A0.open_prev > dom_p) | (A0.open_curr > dom_c)           # NaN -> False (thieu != vi pham)
A0['f_open_gt_global'] = (A0.open_prev > glo_p) | (A0.open_curr > glo_c)
A0['f_global_lt_domestic_same_film'] = (glo_p < dom_p) | (glo_c < dom_c)
A0['f_small_lt100k'] = (A0.open_prev < 1e5) | (A0.open_curr < 1e5)

# co trung bo (opening, domestic) giua cac phim khac nhau: lay tu file audit (tinh tren bang phim day du ma ban giao truoc dung)
au = pd.read_csv(a.audit, encoding='utf-8-sig')
assert au.transition_id.is_unique and au.transition_id.isin(A0.transition_id).all()
A0['f_dup_value_across_films'] = A0.transition_id.isin(au.loc[au.f_dup_value_across_films.astype(bool), 'transition_id'])
# kiem tra cheo (chi tren cac phim xuat hien trong master; khong thay the bang phim day du)
fl = pd.concat([A0[['film_key_prev', 'open_prev']].set_axis(['fk', 'op'], axis=1).assign(dom=dom_p.values),
                A0[['film_key_curr', 'open_curr']].set_axis(['fk', 'op'], axis=1).assign(dom=dom_c.values)]).drop_duplicates('fk')
n_in = fl.groupby(['op', 'dom'], dropna=False).fk.transform('size')
dupfk = set(fl.loc[n_in > 1, 'fk'])
xchk = A0.film_key_prev.isin(dupfk) | A0.film_key_curr.isin(dupfk)
say('cross-check dup tren phim trong master: tinh lai', int(xchk.sum()), '| co trong audit', int(A0.f_dup_value_across_films.sum()),
    '| khop tap ID:', bool((xchk == A0.f_dup_value_across_films).all()))

# ---------- 3. mau
A0['nghi_van_8'] = A0.f_open_gt_domestic | A0.f_dup_value_across_films
A0['global_only_3'] = (~A0.nghi_van_8) & A0.f_open_gt_global      # quy tac buoc 3: co 'open > global'; global<domestic chi la mau thuan truong, khong phai co loai
S = {'A0': pd.Series(True, index=A0.index),
     'A1b': ~A0.nghi_van_8}
S['A1'] = S['A1b'] & ~A0.global_only_3
S['A2'] = S['A1'] & ~A0.f_small_lt100k
exp = {'A0': 918, 'A1b': 910, 'A1': 907, 'A2': 781}
for k, v in S.items():
    d = A0[v]; say(f'{k}: {len(d)} transition / {d.franchise_id.nunique()} franchise')
    assert d.transition_id.is_unique and len(d) == exp[k], f'{k} lech ky vong {exp[k]}'
assert set(A0[S['A2']].transition_id) <= set(A0[S['A1']].transition_id) <= set(A0[S['A1b']].transition_id) <= set(A0.transition_id)
assert int(A0.nghi_van_8.sum()) == 8 and int(A0.global_only_3.sum()) == 3
# A1 theo quy tac nay phai trung A1/A2 cua buoc 3 (neu co file doi chieu)
for k, f in (('A1', a.ids_A1_ref), ('A2', a.ids_A2_ref)):
    if f:
        ref = set(pd.read_csv(f, encoding='utf-8-sig').transition_id)
        say(f'doi chieu {k} voi {os.path.basename(f)}:', ref == set(A0[S[k]].transition_id))
        assert ref == set(A0[S[k]].transition_id)

# ---------- 4. noi 1:1 voi master
A1b = A0[S['A1b']]
chk = A1b[['transition_id']].merge(m, on='transition_id', how='left', validate='1:1', indicator=True)
assert (chk._merge == 'both').all() and len(chk) == len(A1b) and chk.Y.notna().all()
say('noi A1b-master 1:1 OK; khong mat/nhan dong; khong thieu Y')

# ---------- 5. dem theo vi tri
def pos(s): return np.where(s >= 6, '>=6', s.astype(int).astype(str))
for k in ('A0', 'A1b', 'A1', 'A2'):
    d = A0[S[k]].assign(pos=lambda x: pos(x.franchise_position_n))
    t = d.groupby('pos').agg(n_transition=('Y', 'size'), n_franchise=('franchise_id', 'nunique'))
    say(k, 'theo vi tri:', t.to_dict('index'))

# ---------- 6. xuat
A0[S['A1b']][['transition_id']].to_csv(P('ids_A1b.csv'), index=False)
cols = ['transition_id', 'franchise_id', 'franchise_position_n', 'title_prev', 'title_curr', 'open_prev', 'open_curr', 'Y',
        'f_open_gt_domestic', 'f_dup_value_across_films']
ex = A0[A0.nghi_van_8][cols].copy()
ex['ly_do_nghi_van'] = np.select(
    [ex.f_open_gt_domestic & ex.f_dup_value_across_films, ex.f_open_gt_domestic], ['open>domestic + trung bo so lieu', 'open>domestic'],
    'trung bo (opening,domestic) giua phim khac nhau')
ex['ghi_chu'] = 'NGHI VAN ban ghi (chua xac nhan loi); loai khoi mau chinh de xuat, giu o do nhay A0<->A1b'
ex.to_csv(P('excluded_8_pairs_A1b.csv'), index=False, encoding='utf-8-sig')
g3 = A0[A0.global_only_3][cols[:8] + ['f_global_lt_domestic_same_film']]
g3.to_csv(P('kept_3_global_only_pairs.csv'), index=False, encoding='utf-8-sig')
flags = A0[['transition_id', 'franchise_id', 'franchise_position_n', 'Y', 'f_open_gt_domestic', 'f_dup_value_across_films',
            'nghi_van_8', 'global_only_3', 'f_small_lt100k']].copy()
for k in S: flags['in_' + k] = S[k].values
flags.to_csv(P('sample_flags_A0.csv'), index=False)
say('xuat: ids_A1b.csv', len(A1b), '| excluded_8_pairs_A1b.csv', len(ex), '| kept_3_global_only_pairs.csv', len(g3))
open(P('build_A1b_log.txt'), 'w', encoding='utf-8').write('\n'.join(log))
