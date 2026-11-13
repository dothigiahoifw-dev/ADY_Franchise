"""Task 4 / RQ3 - Tach cac ly do khong quan sat duoc Y o vi tri 3 (chi tach khi du lieu CHUNG MINH duoc), cho cac franchise co Y o vi tri 2 trong A1b.
Dau vao tho: analysis_master_transitions.csv, analysis_master_films.csv, pairs_audit.csv (duong dan trong config.json hoac tham so).
Dau ra: results/R10_observability_position3_groups.csv, results/R10b_observability_per_franchise.csv
Nhan nhom (theo du lieu, khong phai theo nguyen nhan kinh te):
  G0  co Y o vi tri 3 (trong A1b)
  G1  khong co Y o vi tri 3; master co transition ky thuat hop le o vi tri 3 nhung opening phim 3 thieu (y_ineligible_reason = opening_missing_N)
  G2  khong co transition vi tri 3 trong master; collection trong bang films chi co dung 2 phim
  G3  khong co transition vi tri 3 trong master; collection co >=3 phim; DUNG cap 2->3 (chain_pos 2->3, phim 2 la phim 2 cua transition co Y) bi loai ky thuat 'unreleased_film', phim 3 co is_unreleased_curr va ngay phat hanh trong du lieu SAU ngay thu thap (retrieval_date).
      Day la quan he trong du lieu; KHONG xac minh tinh trang phat hanh thuc te hien tai (ngay la lich du kien TMDB).
  G3b neu mot franchise co co unreleased o cap KHAC hoac khong khop kiem tra tren: 'nguyen nhan thieu Y3 chua xac minh; franchise co co unreleased' (ky vong 0)
  G4  phan con lai (kiem tra phai = 0)"""
import argparse, json, os, sys
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument('--root', default='.'); ap.add_argument('--raw', default='/mnt/user-data/uploads'); a = ap.parse_args()
R = a.root; INH = os.path.join(R, 'inherited_step5_6'); sys.path.insert(0, os.path.join(R, 'code'))
import rq3_engine as E
cfg = json.load(open(os.path.join(INH, 'config.json')))
T = pd.read_csv(os.path.join(INH, 'input_tables', 'T1_transitions_A0_with_sample_flags.csv'))
a1b = T[T.in_A1b]
p2 = a1b[a1b.franchise_position_n == 2].set_index('franchise_id')
has3 = set(a1b[a1b.franchise_position_n == 3].franchise_id)
m = pd.read_csv(os.path.join(a.raw, 'analysis_master_transitions.csv'), usecols=['franchise_id', 'franchise_position_n', 'y_ineligible_reason', 'Y'], low_memory=False)
m3 = m[m.franchise_position_n == 3].groupby('franchise_id').y_ineligible_reason.first()
f = pd.read_csv(os.path.join(a.raw, 'analysis_master_films.csv'), usecols=['derived__collection_id'], low_memory=False)
f['fid'] = 'TMDBC' + f.derived__collection_id.astype('Int64').astype(str)
sz = f.groupby('fid').size()
pa = pd.read_csv(os.path.join(a.raw, 'pairs_audit.csv'), low_memory=False, usecols=['franchise_id', 'film_key_prev', 'film_key_curr', 'title_prev', 'title_curr', 'release_date_curr', 'chain_pos_prev', 'chain_pos_curr',
                                                                                  'is_unreleased_prev', 'is_unreleased_curr', 'technically_valid', 'exclusion_reason'])
films = pd.read_csv(os.path.join(a.raw, 'analysis_master_films.csv'), usecols=['film_key', 'raw_movies__retrieval_date', 'raw_movies__release_date_ref'], low_memory=False).set_index('film_key')
# G3 CHI khi dung CAP VAO VI TRI 3 (phim 2 -> phim 3) thoa: chain_pos_prev=2, chain_pos_curr=3, phim 2 la phim cua transition vi tri 2 co Y, phim 3 co co is_unreleased_curr, exclusion_reason chua unreleased_film, khong hop le ky thuat
ver = {}
rows3 = pa[(pa.chain_pos_prev == 2) & (pa.chain_pos_curr == 3) & (pa.technically_valid == False) & (pa.exclusion_reason.astype(str).str.contains('unreleased_film')) & (pa.is_unreleased_curr.astype(str) == 'True')]
rows3 = rows3.drop_duplicates('franchise_id').set_index('franchise_id')
def g3_check(fr):
    if fr not in rows3.index: return None
    r = rows3.loc[fr]
    ok_film2 = r.film_key_prev == p2.loc[fr, 'film_key_curr']                      # phim 2 cua cap dung la phim 2 cua transition co Y
    ret = pd.to_datetime(films.loc[r.film_key_curr, 'raw_movies__retrieval_date']) if r.film_key_curr in films.index else pd.NaT
    rel = pd.to_datetime(r.release_date_curr, errors='coerce')
    return dict(franchise_id=fr, title_film2=r.title_prev, film3_title=r.title_curr, film3_key=r.film_key_curr, film3_release_date_in_data=str(rel.date()), data_retrieval_date=str(ret.date()) if pd.notna(ret) else '',
                chain_pos_prev=int(r.chain_pos_prev), chain_pos_curr=int(r.chain_pos_curr), pair_technically_valid=bool(r.technically_valid), exclusion_reason=r.exclusion_reason, is_unreleased_curr=str(r.is_unreleased_curr),
                film2_of_pair_equals_film2_with_Y=bool(ok_film2), film3_release_after_retrieval=bool(pd.notna(rel) and pd.notna(ret) and rel > ret))
unrel = set()
G3ROWS = []
for fr in p2.index:
    c = g3_check(fr)
    if c is not None and c['film2_of_pair_equals_film2_with_Y'] and c['film3_release_after_retrieval']:
        unrel.add(fr); G3ROWS.append(c)
lab = {}
for fr in p2.index:
    if fr in has3: lab[fr] = 'G0_co_Y_o_vi_tri_3'
    elif fr in m3.index and str(m3[fr]) == 'opening_missing_N': lab[fr] = 'G1_co_transition_vt3_nhung_thieu_opening_phim_3'
    elif fr in m3.index: lab[fr] = 'G4_khac'
    elif sz.get(fr, 0) == 2: lab[fr] = 'G2_collection_quan_sat_chi_co_2_phim'
    elif sz.get(fr, 0) >= 3 and fr in unrel: lab[fr] = 'G3_phim_vi_tri_3_bi_co_unreleased_dung_cap_2_3'
    elif fr in set(pa[(pa.technically_valid == False) & (pa.exclusion_reason.astype(str).str.contains('unreleased_film'))].franchise_id): lab[fr] = 'G3b_nguyen_nhan_thieu_Y3_chua_xac_minh_franchise_co_co_unreleased'
    else: lab[fr] = 'G4_khac'
L = pd.Series(lab, name='group')
assert (L == 'G4_khac').sum() == 0, 'co franchise khong phan loai duoc'
pd.DataFrame(G3ROWS).to_csv(os.path.join(R, 'results', 'R10c_G3_verification_11_franchises.csv'), index=False)
print('G3 xac minh dung cap 2->3:', len(G3ROWS), '| G3b (chua xac minh):', int((L == 'G3b_nguyen_nhan_thieu_Y3_chua_xac_minh_franchise_co_co_unreleased').sum()))
d = p2.join(L).reset_index()
d[['franchise_id', 'group', 'transition_id', 'Y', 'open_prev', 'open_curr', 'release_year_n', 'gap_years']].to_csv(os.path.join(R, 'results', 'R10b_observability_per_franchise.csv'), index=False)
boot = E.Boot(a1b.franchise_id.unique(), B=cfg['bootstrap']['B'], seed=cfg['bootstrap']['seed'])
defs = {}
for g, s in d.groupby('group'):
    defs[g + '|med'] = E.Def(s.Y, s.franchise_id, 'wq'); defs[g + '|lt0'] = E.Def(s.Y, s.franchise_id, 'lt0')
pts, reps = E.run(defs, boot)
rows = []
for g, s in d.groupby('group'):
    lo, hi, nn = E.ci(reps[g + '|med']); l2, h2, _ = E.ci(reps[g + '|lt0'])
    rows.append(dict(group=g, n_franchise=len(s), n_position2_transitions=len(s), median_Y_pos2=pts[g + '|med'], median_pct_pos2=100 * (np.exp(pts[g + '|med']) - 1),
                     median_pct_ci_lo=100 * (np.exp(lo) - 1), median_pct_ci_hi=100 * (np.exp(hi) - 1), share_lt0_pos2=pts[g + '|lt0'], share_lt0_ci_lo=l2, share_lt0_ci_hi=h2,
                     median_open_prev=s.open_prev.median(), median_open_curr=s.open_curr.median(), median_release_year_N=s.release_year_n.median(), median_gap_years=s.gap_years.median()))
out = pd.DataFrame(rows)
out.loc[len(out)] = dict(group='TONG_vi_tri_2', n_franchise=len(d), n_position2_transitions=len(d), median_Y_pos2=d.Y.median(), median_pct_pos2=100 * (np.exp(d.Y.median()) - 1), share_lt0_pos2=(d.Y < 0).mean(),
                         median_open_prev=d.open_prev.median(), median_open_curr=d.open_curr.median(), median_release_year_N=d.release_year_n.median(), median_gap_years=d.gap_years.median())
out.to_csv(os.path.join(R, 'results', 'R10_observability_position3_groups.csv'), index=False)
pd.set_option('display.width', 250); print(out.round(3).to_string())
assert out.n_franchise.iloc[:-1].sum() == 512
