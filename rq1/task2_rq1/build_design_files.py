#!/usr/bin/env python3
"""Sinh feature_registry_rq1.csv, experiment_plan_rq1.csv, design_config_rq1.json (khong train model)."""
import json, hashlib, os, sys
import pandas as pd
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'data')
_chk = pd.read_csv(f'{out}/checks_source.csv')
if (_chk.status != 'PASS').any():
    print('*** FAIL: checks_source.csv co kiem tra khong dat. DUNG. ***'); sys.exit(1)
cov = pd.read_csv(f'{out}/feature_coverage_computed.csv').set_index('column')
def c(col):
    if col not in cov.index: return ('', '', '')
    r = cov.loc[col]; return (f"{r.miss_pct_918}%", f"{r.miss_pct_dev}%", int(r.n_unique))

R = []
def add(rq1_name, source_column, role, definition, source, timing, evidence, assumption, risk, decision, use_in, rationale, prep='', cov_col=None, policy='', status='VERIFIED(tinh lai)'):
    m918, mdev, nu = c(cov_col) if cov_col else ('', '', '')
    R.append(dict(rq1_name=rq1_name, source_column=source_column, source_file=source, role=role, definition=definition,
                  n_unique=nu, missing_918=m918, missing_dev=mdev, timing_class=timing, timing_evidence=evidence, assumption=assumption,
                  leakage_or_redundancy=risk, decision=decision, use_in=use_in, rationale=rationale, preprocessing=prep, policy_conflict=policy, evidence_status=status))

P, M, S = 'pairs_audit.csv', 'analysis_master_films.csv', 'rq1_split_v2.csv'
add('transition_id','transition_id','ID','film_key_prev + "__" + film_key_curr; duy nhat 918/918',P,'-','-','-','Khong dung lam feature','KHONG DUNG LAM FEATURE','key','Khoa doi chieu moi bang')
add('franchise_id','franchise_id','GROUP','TMDB collection id (TMDBC<id>); khoa nhom chia fold',P,'-','-','A1','Khong dung lam feature','GROUP (chia fold, phan tich phu thuoc)','group','franchise_id dung de nhom, khong dua vao mo hinh')
add('film_key_prev / film_key_curr','film_key_prev, film_key_curr','ID','Khoa phim N-1 va N; moi phim xuat hien toi da 1 lan o vai tro N va 1 lan o vai tro N-1',P,'-','-','-','-','KHONG DUNG LAM FEATURE','key','Khoa join sang analysis_master_films.csv')
add('Y','Y','TARGET','ln(open_curr) - ln(open_prev); tai lap sai lech toi da 1.8e-15',P,'4','Outcome cua N','A2','Khong duoc la feature','TARGET CO DINH','target','Target du an')
add('open_prev','open_prev','STRATUM_SOURCE','opening_weekend_gross N-1 (USD); khop analysis_master_films.csv',P,'1','Opening N-1 ghi nhan truoc N','A2','-','DUNG de tinh log_open_prev va phan tang','input','Gia tri nguon cua feature loi va nhan tang')
add('open_curr','open_curr','OUTCOME','opening_weekend_gross N',P,'4','Outcome cua N','A2','Leakage truc tiep (nam trong Y)','LOAI','excluded','Khong duoc dung lam feature hay dieu kien chon mau')
add('mau_chinh / stratum_open_prev','mau_chinh','STRATUM','open_prev >= 1.000.000 USD (khop 100% quy tac); chi phan tang bao cao',S,'1','Chi dung open_prev','-','Nguon goc nguong khong co tai lieu','PHAN TANG BAO CAO, KHONG LOAI DONG','report','Khong chon quan the bang MAE')
add('role / fold','role, fold','SPLIT','dev (fold 1-4) / test_cuoi (fold 0), chia theo franchise',S,'-','-','-','-','DUNG CHO SPLIT','split','Giu split v2')
add('quality_flag_any','opening_low_warning_prev, opening_low_warning_curr, opening_inconsistent','QUALITY_FLAG','Co bat ky co chat luong opening (10 dong: dev 6, test 4)',P,'-','-','A2','Co la canh bao, chua chung minh loi','DANH DAU, KHONG LOAI','sensitivity S1','Chi dung cho kiem tra do nhay')
add('comparability_status','comparability_status','QUALITY_FLAG','Hang so ASSUMED_NOT_VERIFIED o 918/918',P,'-','-','A2','Khong mang thong tin phan biet','KHONG DUNG','metadata','Cung nhan cho moi dong; khong loc')
add('log_open_prev','open_prev','FEATURE_CORE','ln(open_prev)',P,'1','Opening N-1 co truoc N (release_date_prev < release_date_curr o 918/918; khoang cach toi thieu 27 ngay)','A2','Co trong Y (hoi quy ve trung binh); phien ban USD danh nghia','DUNG (E0-E4)','main','Opening phan truoc la bien lich su duy nhat; trung baseline','ln(open_prev), open_prev>0 kiem tra bang assert','log_open_prev')
add('gap_years','gap_years','FEATURE_CORE','(release_date_curr - release_date_prev) / 365.25 (tai lap sai lech 7e-15)',P,'2','Ngay chieu N co the biet truoc; khong co ngay cong bo','A-R1a','Ngay thuc te thay lich cong bo','DUNG (E1,E4) neu chap nhan A-R1a','main','Khoang cach giua cac phan; min 0.074 nam','ln(gap_years); gap>0 assert','gap_years')
add('franchise_position_n','chain_pos_curr','FEATURE_CORE','So thu tu cua N trong TMDB collection theo ngay chieu (2-15). Khop 100% voi xep hang doc lap theo ngay trong collection; khong co ngay trung trong mau',P,'2','Chi dem cac phim chieu truoc N trong collection','A1 + A-R1b','Khong phai so phan chinh thuc; collection la snapshot 2026','DUNG (E2,E4)','main','Phan muon co the mat suc hut/on dinh','ln(position)','franchise_position_n')
add('release_month_n','derived from release_date_curr','FEATURE_CORE','Thang chieu cua N (1-12)',P,'2','Ngay chieu N','A-R1a','Bien tuan hoan','DUNG (E3,E4)','main','Mua chieu','sin(2*pi*m/12), cos(2*pi*m/12)','release_month_n')
add('release_year_n','derived from release_date_curr','FEATURE_CORE','Nam chieu cua N (1932-2026; 7 dong dev truoc 1980, 86 truoc 1990)',P,'2','Ngay chieu N','A-R1a','Hap thu hieu ung do luong/USD danh nghia; it dong rat cu','DUNG (E3,E4)','main','Giai doan thi truong','(year-2000)/10, hang so co dinh, khong hoc tu du lieu','release_year_n')
add('is_director_changed','raw_movies__director_ids (so sanh tap N-1 vs N)','FEATURE_RETRO','1 neu tap director_ids khac nhau; khop credits__directors_person_ids o 918/918',M,'2','Dao dien thuong cong bo truoc chieu; snapshot 2026-10-22','Tung bien','ID dao dien co the khong dong nhat; khong co phien ban lich su','HOI CUU (E5), sau khi khoa mo hinh chinh','retro','Tin hieu lien tuc ekip','nhi phan 0/1; khong thieu','is_director_changed','Task 1 bao policy RQ2_ONLY_PENDING (REPORTED, chua co file policy)','VERIFIED(tinh lai)')
add('studio_changed','raw_movies__production_company_ids (so sanh tap)','FEATURE_RETRO','1 neu tap cong ty SAN XUAT khac nhau. Khong phai nha phat hanh',M,'2','Snapshot 2026-10-22','Tung bien','Danh sach co the duoc bo sung sau; thieu 2.0%','HOI CUU (E6)','retro','Thay doi hang san xuat','nhi phan; thieu: mode cua train + co thieu, fit trong train','studio_changed','Task 1 bao policy RQ2_ONLY_PENDING (REPORTED)')
add('genre_jaccard','raw_movies__genre_ids','FEATURE_RETRO','Jaccard giua tap the loai N-1 va N (0.2-1)',M,'2','Snapshot 2026-10-22','Tung bien','Nhan the loai co the sua sau; chua co policy','HOI CUU (E7)','retro','Thay doi the loai','lien tuc, khong thieu','genre_jaccard','Chua co policy (REPORTED)')
add('production_budget_prev','raw_movies__production_budget (N-1)','EXCLUDED','Ngan sach N-1 (USD danh nghia); co budget_missing_flag',M,'1-2','Snapshot 2026-10-22','-','Thieu ~11%; USD danh nghia; khong dieu chinh lam phat','KHONG DUNG CHO RQ1','RQ2','Policy ghi rq1_allowed = no (REPORTED); khong ghi de im lang','Giu null, khong dien 0','production_budget_prev','Co: de xuat khong dung de tranh xung dot')
add('production_budget_curr / budget_log_ratio','raw_movies__production_budget (N)','EXCLUDED','Ngan sach N',M,'3','Thuong cong bo/cap nhat sau chieu','-','Thieu 17%','LOAI','-','Khong co bang chung thoi diem','', 'production_budget_curr')
add('cast_retention_top5','credits__cast_person_ids (5 ten dau theo thu tu liet ke)','EXCLUDED','Giao top-5 cua N-1 va N / 5. Thu tu = billing_order la gia dinh chua kiem',M,'2-3','Billing cuoi chi ro sau chieu','Gia dinh thu tu','Danh sach cuoi snapshot 2026','KHONG DUNG CHO RQ1','RQ2','Chua xac minh billing tai moc du bao','', 'cast_retention_top5_diag')
add('critic_score_prev / audience_score_prev','raw_rt_scores__critic_score, audience_score (N-1)','EXCLUDED','Diem RT N-1, scrape 2026-10-23',M,'3','Diem tai thoi diem scrape, khong phai truoc N','-','Thieu 7.6% / 3.7%; diem khan gia troi theo thoi gian','KHONG DUNG CHO RQ1','RQ2','Khong co phien ban truoc N','', 'critic_score_prev')
add('vote_count_prev / vote_count_curr','raw_movies__vote_count','EXCLUDED','So vote TMDB',M,'3','Tang theo thoi gian','-','Nhiem snapshot','LOAI','-','Registry ghi excluded (REPORTED)','', 'vote_count_curr')
add('lifetime_gross_prev / lifetime_gross_curr','raw_box_office_detailed__domestic_gross, international_gross','EXCLUDED','Tong doanh thu',M,'1 (N-1, neu gap du dai) / 4 (N)','Gap toi thieu 27 ngay nen N-1 chua chin tai moc','-','N: outcome','KHONG DUNG','-','Khong dua vao loi','', None, '', 'CHUA TINH DO PHU')
add('theater_count','raw_box_office_detailed__theater_count','EXCLUDED','So rap',M,'-','-','-','Thieu 100% (0/918 ca N-1 va N)','LOAI','-','Khong co du lieu','', 'theater_count_prev')
add('relationship_type_candidate','relationship_type_candidate','EXCLUDED','Nhan UNVERIFIED_HEURISTIC tu tieu de',M,'-','-','-','Heuristic chua xac minh','LOAI','-','Khong xac minh quan he phan','', status='REPORTED (theo Task 1; chua tinh lai)')
pd.DataFrame(R).to_csv(f'{out}/../feature_registry_rq1.csv', index=False)

E = [
 ('E0','Hoi quy 1 bien co the tai lap baseline v2 khong?','log_open_prev','Doi chieu tai lap (trung baseline hoi quy v2)','Dieu kien fit trung baseline v2 (da xac minh)','Phai khop du bao baseline hoi quy theo transition_id','Khong coi la ket qua moi','CHINH'),
 ('E1','Gap co bo sung so voi E0?','log_open_prev + ln(gap_years)','Tach dong gop khoang cach','A-R1a','E1 vs E0','Neu qua cong S1','CHINH'),
 ('E2','Vi tri phan co bo sung so voi E0?','log_open_prev + ln(franchise_position_n)','Tach dong gop vi tri','A1 + A-R1b','E2 vs E0','Neu qua cong S1','CHINH'),
 ('E3','Mua/nam chieu co bo sung so voi E0?','log_open_prev + sin/cos(thang) + (nam-2000)/10','Tach dong gop lich chieu','A-R1a','E3 vs E0','Neu qua cong S1','CHINH'),
 ('E4','Bo loi day du co bo sung so voi E0?','5 feature loi (6 he so doc lap)','Mo hinh chinh du kien','A1, A2, A-R1a, A-R1b','E4 vs E0','Neu qua cong S1','CHINH'),
 ('E5','Doi dao dien co bo sung so voi E4 (hoi cuu)?','E4 + is_director_changed','Hoi cuu, tach tung nhom','Chi sau khi khoa mo hinh chinh; policy chua xac nhan','E5 vs mo hinh chinh da khoa','Khong tham gia chon mo hinh chinh; khong dien giai la du bao truoc opening','HOI CUU'),
 ('E6','Doi hang san xuat co bo sung (hoi cuu)?','E4 + studio_changed (+ co thieu)','Hoi cuu','Nhu E5','E6 vs mo hinh chinh da khoa','Nhu E5','HOI CUU'),
 ('E7','Doi the loai co bo sung (hoi cuu)?','E4 + genre_jaccard','Hoi cuu','Nhu E5','E7 vs mo hinh chinh da khoa','Nhu E5','HOI CUU'),
 ('S1','Ket qua co nhay voi 6 dong dev co co chat luong opening?','Cau hinh da khoa; 6 dong co quality_flag_any bi bo khoi TAP FIT cua moi fold (van duoc du bao ngoai fold). Ca ba baseline cung fit lai theo cach nay','Do nhay (khong chon cau hinh)','Chi dev','Danh gia tren CUNG tap dong validation: (a) 719 dong dev khong co co: so run chinh voi run S1, ghep cap theo transition_id; (b) 6 dong co co: bao rieng. Khac biet chi den tu tap fit','Chi bao cao','NHAY CAM'),
 ('S2','Ket qua co nhay voi tap fit chi gom open_prev>=1M?','Cau hinh da khoa; fit chi tren dong dev open_prev>=1M cua cac fold con lai; ca ba baseline cung fit lai theo cach nay','Do nhay (khong chon cau hinh)','Chi dev','Danh gia tren CUNG 725 dong dev (ca hai tang), du bao ngoai fold; so run chinh voi run S2 ghep cap theo transition_id','Chi bao cao','NHAY CAM'),
]
pd.DataFrame(E, columns=['id','question','features','purpose','conditions','comparison','use_of_result','tier']).to_csv(f'{out}/../experiment_plan_rq1.csv', index=False)
cfg = {
 'version': 'task2_design_v1', 'status': 'PHUONG AN KHUYEN NGHI TRIEN KHAI - chua duoc nhom duyet; chua train; chua cham test',
 'sample': {'main_sample': 'all 918 transitions of rq1_split_v2.csv (= y_eligible of pairs_audit.csv)', 'extra_exclusions': 0,
            'strata_report': {'ge_1M': 'open_prev >= 1,000,000', 'lt_1M': 'open_prev < 1,000,000'},
            'quality_flag_sensitivity_dev_ids': ['FK00080280__FK00185341','FK00000256__FK00000255','FK00000255__FK00000258','FK00000258__FK00000259','FK00008982__FK00110552','FK00454699__FK00823609']},
 'split': {'file': 'rq1_split_v2.csv', 'dev_folds': [1,2,3,4], 'test_fold': 0, 'by': 'franchise_id', 'rationale': 'giu nguyen split, khong doi seed'},
 'algorithm': 'Linear Regression (OLS, khong phat), quyet dinh cua nhom',
 'sensitivity': {
   'S1': {'fit': 'bo 6 dong dev co quality_flag_any khoi tap fit moi fold; baseline fit lai cung cach', 'evaluation_rows': 'cung tap: 719 dong dev khong co co (so run chinh vs S1, ghep cap theo transition_id) + 6 dong co co bao rieng', 'purpose': 'do nhay, khong chon cau hinh'},
   'S2': {'fit': 'chi dong dev open_prev>=1M cua cac fold con lai; baseline fit lai cung cach', 'evaluation_rows': 'cung 725 dong dev (ca hai tang), du bao ngoai fold', 'purpose': 'do nhay, khong chon cau hinh'}},
 'phase_rules': {'task3_current': 'CHI chay tren dev (rq1_inputs_dev.csv, baseline_v2_dev_preds_wide.csv); khong doc rq1_inputs_test_LOCKED.csv; khong cham test',
                 'test_scoring': 'o task rieng sau khi khoa cau hinh (hash) va duoc nhom dong y'},
 'baselines': ['Y=0', 'Median Y cua train', 'LinearRegression(log_open_prev)'],
 'baseline_fit_set': 'tat ca dong dev cua cac fold con lai (da tai lap, sai lech <= 1.4e-15)',
 'features_core_initial_config': {'log_open_prev': 'ln(open_prev)', 'gap': 'ln(gap_years)', 'position': 'ln(franchise_position_n)', 'month': 'sin/cos(2*pi*m/12)', 'year': '(release_year_n-2000)/10 (hang so co dinh)'},
 'allowed_representation_changes': 'toi da 1 thay doi bieu dien/feature, chi dua tren do thi phan du tren dev (khong dua tren MAE), ghi nhat ky co thoi diem, ap dung dong nhat cho E1-E4',
 'metrics': {'primary': 'MAE log gop (micro) tren du bao ngoai fold cua 725 dong dev',
             'secondary': ['RMSE', 'MAE tung fold + macro tb fold', 'MAE tb theo franchise (trung binh cua trung binh)', 'MAE theo tang open_prev kem n', 'AE diem phan tram (doi tung Y va Y_hat roi moi tinh; bao median va mean)', 'chenh lech ghep cap theo transition_id']},
 'selection_rule': {'candidates': ['E1','E2','E3','E4'], 'anchor': 'E0',
                    'gate_S1': 'MAE gop < E0 va MAE thap hon E0 o it nhat 3/4 fold',
                    'choose': 'trong nhom dat: MAE gop thap nhat; neu cau hinh phuc tap hon hon cau hinh don gian hon da dat < 0.005 log thi chon don gian (E1=E2 < E3 < E4); khong dat -> giu E0',
                    'claim_gate': 'chi noi hon mot baseline khi MAE gop thap hon va thap hon o >=3/4 fold so voi baseline do; bao rieng tung baseline',
                    'threshold_note': '0.005 la nguong thuc hanh khai bao truoc (khoang 40% khoang cach 0.013 giua cac baseline v2), khong phai kiem dinh thong ke'},
 'test_protocol': 'khoa design_config + split_assignment (hash) truoc khi cham; fit tren toan bo 725 dong dev; cham mot lan; baseline cung fit tren 725 dong dev',
 'test_exposure_note': 'Y cua test da duoc mo ta o cap toan mau (Task 1); Task 2 khong dung test de ra quyet dinh',
}
json.dump(cfg, open(f'{out}/../design_config_rq1.json', 'w'), ensure_ascii=False, indent=1)
# manifest cho cac file thiet ke
rows = []
for fn in ['feature_registry_rq1.csv','experiment_plan_rq1.csv','design_config_rq1.json','data/sample_rq1_membership.csv','data/split_assignment.csv','data/exclusions.csv','data/sample_funnel.csv','data/rq1_inputs_dev.csv','data/rq1_inputs_test_LOCKED.csv','data/baseline_v2_dev_preds_wide.csv','data/checks_source.csv']:
    p = os.path.join(out, '..', fn); h = hashlib.sha256(open(p,'rb').read()).hexdigest()
    rows.append(dict(file=fn, sha256=h, bytes=os.path.getsize(p)))
pd.DataFrame(rows).to_csv(f'{out}/../manifest_outputs.csv', index=False)
print('ok', len(R), 'registry rows')
