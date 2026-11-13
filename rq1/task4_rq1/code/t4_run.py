#!/usr/bin/env python3
"""RQ1 Task 4. Giai doan 'prescore': chot buoc 6 (CHI hash byte file test). Giai doan 'score': cham test theo thiet ke da khoa.
python t4_run.py --t3 <thu muc task3_rq1> --t2 <thu muc task2_rq1> --out <thu muc task4_rq1> --stage prescore|score|all"""
import argparse, json, os, subprocess, sys, platform
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t3_common import *

ap = argparse.ArgumentParser()
ap.add_argument('--t3', required=True); ap.add_argument('--t2', required=True); ap.add_argument('--out', required=True); ap.add_argument('--stage', default='all')
ap.add_argument('--boot', type=int, default=10000); ap.add_argument('--seed', type=int, default=20261107)
a = ap.parse_args()
T3, T2, OUT = a.t3, a.t2, a.out
REC, RES, LOG = f'{OUT}/records', f'{OUT}/results', f'{OUT}/logs'
for d_ in (REC, RES, LOG, f'{OUT}/figures'): os.makedirs(d_, exist_ok=True)
D2 = f'{T2}/data'; TEST = f'{D2}/rq1_inputs_test_LOCKED.csv'
lock = json.load(open(f'{T3}/locked_config_rq1.json'))
events = []
def ev(stage, event, detail=''): events.append(dict(time_utc=now_utc(), stage=stage, event=event, detail=str(detail)))
def save_log(): 
    p = f'{LOG}/scoring_log.csv'
    old = pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
    pd.concat([old, pd.DataFrame(events)]).to_csv(p, index=False)

# =================== PRESCORE ===================
def prescore():
    CH = []
    def chk(cid, desc, ok, detail='', note=False):
        CH.append(dict(id=cid, description=desc, status=('NOTE' if note else ('PASS' if bool(ok) else 'FAIL')), detail=str(detail)))
    # P01 manifest Task 3
    m3 = pd.read_csv(f'{T3}/manifest_task3.csv')
    bad = [r.file for r in m3.itertuples() if not os.path.exists(f'{T3}/{r.file}') or sha256(f'{T3}/{r.file}') != r.sha256]
    files3 = sorted(os.path.relpath(os.path.join(d, f), T3) for d, _, fs in os.walk(T3) for f in fs if f != 'manifest_task3.csv' and '__pycache__' not in d)
    chk('P01', 'manifest_task3.csv: moi file khop hash, khong file thua', not bad and set(files3) == set(m3.file), f'{len(m3)} file; bad={bad}')
    # P02 hash trong locked_config
    man2 = pd.read_csv(f'{T2}/manifest_outputs.csv').set_index('file')
    act = {'split': sha256(f'{D2}/split_assignment.csv'), 'dev_inputs': sha256(f'{D2}/rq1_inputs_dev.csv'), 'baseline_wide': sha256(f'{D2}/baseline_v2_dev_preds_wide.csv'),
           'test_bytes': sha256(TEST), 'design_config_t2': sha256(f'{T2}/design_config_rq1.json')}
    li = lock['inputs']
    exp = {'split': lock['split']['sha256'], 'dev_inputs': li['rq1_inputs_dev.csv'], 'baseline_wide': li['baseline_v2_dev_preds_wide.csv'],
           'test_bytes': li['rq1_inputs_test_LOCKED.csv (chi hash byte, khong mo)'], 'design_config_t2': li['design_config_rq1.json (Task 2)']}
    for k in act: chk(f'P02_{k}', f'hash thuc te == hash trong locked_config: {k}', act[k] == exp[k], f'{act[k][:12]} vs {exp[k][:12]}')
    chk('P03', 'manifest_outputs.csv Task 2: moi file khop hash', all(os.path.exists(f'{T2}/{f}') and sha256(f'{T2}/{f}') == r.sha256 for f, r in man2.iterrows()), f'{len(man2)} file')
    pf = subprocess.run([sys.executable, f'{T2}/task3_preflight.py', '--root', T2], capture_output=True, text=True)
    open(f'{LOG}/task2_preflight_output.txt', 'w').write(pf.stdout + pf.stderr)
    chk('P04', 'preflight Task 2 PASS (hash byte test, khong parse)', pf.returncode == 0, pf.stdout.strip().splitlines()[-1] if pf.stdout.strip() else '')
    ch = {f: sha256(f'{T3}/code/{f}') for f in lock['code_sha256']}
    chk('P05', 'hash code Task 3 khop locked_config', ch == lock['code_sha256'], f'{len(ch)} file code')
    chk('P06', 'hash t3_common.py ban sao trong goi Task 4 == ban Task 3 da khoa', sha256(f'{OUT}/code/t3_common.py') == lock['code_sha256']['t3_common.py'])
    chk('P07', 'locked_config: trang thai khoa, E0, 1 feature log_open_prev, OLS', lock['status'].startswith('LOCKED') and lock['selected_config'] == 'E0' and list(lock['features_and_representation']) == ['log_open_prev'] and 'OLS' in lock['algorithm'], lock['selected_config'])
    chk('P08', 'khong thay doi bieu dien trong Task 3', lock['representation_changes'] == [] and json.load(open(f'{T3}/logs/representation_log.json'))['changes'] == [] and not pd.read_csv(f'{T3}/results/diag_representation_trigger.csv').triggered.any())
    # OOF
    oof = pd.read_csv(f'{T3}/results/oof_predictions_wide.csv'); dev = pd.read_csv(f'{D2}/rq1_inputs_dev.csv').sort_values('transition_id').reset_index(drop=True)
    sp = pd.read_csv(f'{D2}/split_assignment.csv')
    chk('P09', 'OOF: 725 dong, ID duy nhat, trung tap dev; fold 178/185/176/186; Y khop dau vao', len(oof) == 725 and oof.transition_id.is_unique and set(oof.transition_id) == set(dev.transition_id) and oof.fold.value_counts().sort_index().tolist() == [178, 185, 176, 186] and np.allclose(oof.sort_values('transition_id').Y.values, dev.Y.values))
    models = ['Y0', 'median', 'E0', 'E1', 'E2', 'E3', 'E4']
    mae = {m: float(np.abs(oof.Y - oof[f'pred_{m}']).mean()) for m in models}
    chk('P10', 'MAE log gop tinh lai tu OOF khop locked_config (1e-5) va so trong yeu cau (4 chu so)', all(abs(mae[m] - lock['dev_results'][m]['pooled_mae']) < 1e-5 for m in models) and [round(mae[m], 4) for m in ('E0', 'median', 'Y0')] == [0.8253, 0.8124, 0.8218], {m: round(v, 4) for m, v in mae.items()})
    fm = {m: [float(np.abs(oof.Y - oof[f'pred_{m}'])[oof.fold == k].mean()) for k in FOLDS] for m in models}
    rows = []; allfail = True
    for m in ['E1', 'E2', 'E3', 'E4']:
        fb = sum(fm[m][i] < fm['E0'][i] for i in range(4)); ok = (mae[m] < mae['E0']) and fb >= 3; allfail &= (not ok)
        rows.append(f'{m}: MAE {mae[m]:.4f} vs E0 {mae["E0"]:.4f}; fold thap hon E0 {fb}/4; dat={ok}')
    chk('P11', 'E1-E4 deu KHONG dat quy tac (MAE gop < E0 va thap hon o >=3/4 fold)', allfail, ' | '.join(rows))
    p0, _ = cv_predict(dev, CONFIGS['E0'])
    o = oof.set_index('transition_id').loc[dev.transition_id]
    chk('P12', 'E0 tai lap tu dau vao dev: bo cot dung la [log_open_prev]; OOF khop (<1e-9)', build_X(dev, CONFIGS['E0'])[1] == ['log_open_prev'] and np.abs(p0 - o.pred_E0.values).max() < 1e-9, float(np.abs(p0 - o.pred_E0.values).max()))
    chk('P13', 'baseline Y=0 va median tai lap tu dau vao dev khop OOF', np.abs(baseline_predict(dev, 'Y0') - o.pred_Y0.values).max() < 1e-9 and np.abs(baseline_predict(dev, 'median') - o.pred_median.values).max() < 1e-9)
    chk('P14', 'split_assignment: 725 dev / 193 test, franchise dev-test khong chong lan (khong mo file test)', (sp.role == 'dev').sum() == 725 and (sp.role != 'dev').sum() == 193 and not set(sp[sp.role == 'dev'].franchise_id) & set(sp[sp.role != 'dev'].franchise_id), sp.role.value_counts().to_dict())
    src = open(f'{T3}/code/t3_run.py').read()
    bug = ('rep_over = json.load' in src) and ('REP = {}' in src)
    chk('P15', 'GHI NHAN GIOI HAN: t3_run.py doc rep_decision.json (rep_over) roi van gan REP = {}; nhanh doi bieu dien khong duoc kich hoat trong lan chay da khoa (trigger=False, 0 thay doi)', bug, 'khong sua ZIP/cau hinh/ket qua Task 3', note=True)
    t = pd.DataFrame(CH); t.to_csv(f'{LOG}/prescore_checks.csv', index=False); print(t[['id', 'status', 'description']].to_string(index=False))
    if (t.status == 'FAIL').any():
        ev('prescore', 'FAIL truoc cham test', t[t.status == 'FAIL'].id.tolist()); save_log(); print('*** FAIL truoc cham test. DUNG; khong doc file test. ***'); sys.exit(1)
    rec = {'record': 'PRESCORE - ghi truoc khi doc noi dung file test', 'time_utc': now_utc(), 'task3_locked_config_sha256': sha256(f'{T3}/locked_config_rq1.json'),
           'task3_manifest_sha256': sha256(f'{T3}/manifest_task3.csv'), 'hashes_actual': act, 'task3_code_sha256': ch,
           'locked_design': {'selected': 'E0', 'algorithm': 'OLS co he so chan, chi log_open_prev = ln(open_prev)', 'baselines': ['Y=0', 'median Y cua 725 dong dev'], 'e1_e4': 'da thu tren dev, khong dat quy tac thay E0; KHONG cham tren test',
                             'fit_for_test': 'fit tren toan bo 725 dong dev; he so E0 va median uoc luong lai truoc khi du bao test'},
           'dev_oof_mae_recomputed': {m: round(v, 6) for m, v in mae.items()}, 'dev_oof_fold_mae': {m: [round(x, 6) for x in v] for m, v in fm.items()},
           'evaluation_object': '193 transition test (fold 0), cung tap cho ba phuong an',
           'metric_definitions': {'primary': 'MAE log gop = mean |Y - Y_hat| tren 193 transition', 'secondary': ['RMSE log gop', 'MAE TB theo franchise (TB cua MAE moi franchise)', 'sai so diem phan tram: |100(exp(Y)-1) - 100(exp(Y_hat)-1)|, bao mean va median', 'theo tang open_prev <1M va >=1M kem n dong, n franchise'],
                                  'paired': 'delta_MAE = MAE_baseline - MAE_E0; duong = E0 sai so thap hon', 'bootstrap': 'bo tro: boot theo franchise, ghep cap, giu du bao co dinh'},
           'rule_note': 'Quy tac 3/4 fold chi dung giai thich lua chon tren dev; test la mot tap giu lai duy nhat',
           'selection_reason': lock['selection_reason'], 'known_limitation_task3': 'xem P15', 'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__}}
    json.dump(rec, open(f'{REC}/prescore_record.json', 'w'), ensure_ascii=False, indent=1)
    open(f'{REC}/prescore_record.sha256', 'w').write(sha256(f'{REC}/prescore_record.json') + '\n')
    ev('prescore', 'PASS; ghi prescore_record.json (chi hash byte file test)', sha256(f'{REC}/prescore_record.json')[:16]); save_log()
    print('PRESCORE PASS; da ghi', f'{REC}/prescore_record.json')

# =================== SCORE ===================
def score():
    if sha256(f'{REC}/prescore_record.json') != open(f'{REC}/prescore_record.sha256').read().strip():
        print('*** FAIL: prescore_record bi thay doi. DUNG. ***'); sys.exit(1)
    pr = json.load(open(f'{REC}/prescore_record.json'))
    if sha256(TEST) != pr['hashes_actual']['test_bytes']:
        print('*** FAIL: hash file test khac ban ghi truoc cham. DUNG. ***'); sys.exit(1)
    ev('score', 'bat dau; da xac nhan prescore_record va hash test'); 
    dev = pd.read_csv(f'{D2}/rq1_inputs_dev.csv').sort_values('transition_id').reset_index(drop=True)
    sp = pd.read_csv(f'{D2}/split_assignment.csv')
    # fit tren toan bo 725 dong dev
    beta = ols_fit(dev[['log_open_prev']].values, dev.Y.values); med = float(np.median(dev.Y.values))
    pd.DataFrame([dict(intercept=beta[0], slope_log_open_prev=beta[1], n_fit=len(dev), median_Y_dev=med)]).to_csv(f'{RES}/e0_dev_fit_coefficients.csv', index=False)
    json.dump({'median_Y_dev': med, 'n': len(dev), 'E0_intercept': float(beta[0]), 'E0_slope_log_open_prev': float(beta[1])}, open(f'{RES}/dev_fit_parameters.json', 'w'), indent=1)
    ev('score', 'fit tren 725 dong dev', f'E0: intercept={beta[0]:.6f} slope={beta[1]:.6f}; median_Y_dev={med:.6f}')
    # doc va kiem tra test
    te = pd.read_csv(TEST).sort_values('transition_id').reset_index(drop=True)
    st = sp[sp.role != 'dev']
    CH = []
    def chk(cid, desc, ok, detail=''): CH.append(dict(id=cid, description=desc, status='PASS' if bool(ok) else 'FAIL', detail=str(detail)))
    chk('T01', '193 dong; ID duy nhat; trung tap test cua split', len(te) == 193 and te.transition_id.is_unique and set(te.transition_id) == set(st.transition_id), len(te))
    chk('T02', 'role = test_cuoi va fold = 0 o moi dong; khop split', (te.role != 'dev').all() and (te.fold == 0).all() and te.merge(st, on='transition_id').eval('franchise_id_x == franchise_id_y').all(), te.role.unique().tolist())
    chk('T03', 'khong chong lan franchise voi dev', not set(te.franchise_id) & set(dev.franchise_id))
    chk('T04', 'open_prev, open_curr > 0, huu han; Y == ln(open_curr) - ln(open_prev) (1e-12)', (te.open_prev > 0).all() and (te.open_curr > 0).all() and np.isfinite(te.Y).all() and np.abs(te.Y - (np.log(te.open_curr) - np.log(te.open_prev))).max() < 1e-12)
    chk('T05', 'log_open_prev == ln(open_prev), huu han, khong thieu', np.abs(te.log_open_prev - np.log(te.open_prev)).max() < 1e-12 and te.log_open_prev.notna().all())
    chk('T06', 'mau_chinh == (open_prev >= 1e6); cot khop dev', (te.mau_chinh == (te.open_prev >= 1e6)).all() and set(dev.columns) == set(te.columns))
    t = pd.DataFrame(CH); t.to_csv(f'{LOG}/test_input_checks.csv', index=False); print(t[['id', 'status', 'description']].to_string(index=False))
    if (t.status == 'FAIL').any():
        ev('score', 'FAIL kiem tra dau vao test', t[t.status == 'FAIL'].id.tolist()); save_log(); print('*** FAIL: tap cham sai. DUNG, khong cham. ***'); sys.exit(1)
    ev('score', 'kiem tra dau vao test PASS', '193 dong, 113 franchise')
    y = te.Y.values
    pred = {'Y0': np.zeros(len(te)), 'median': np.full(len(te), med), 'E0': beta[0] + beta[1] * te.log_open_prev.values}
    names = {'Y0': 'Y=0', 'median': 'Median train (dev)', 'E0': 'E0 (OLS log_open_prev)'}
    ae = {m: np.abs(y - pred[m]) for m in pred}
    pe = {m: np.abs(pct(y) - pct(pred[m])) for m in pred}
    assert all(np.isfinite(v).all() for v in pe.values())
    strat = {'tat ca': np.ones(len(te), bool), 'open_prev >=1M': te.mau_chinh.values, 'open_prev <1M': ~te.mau_chinh.values}
    rows = []
    for m in pred:
        for sn, mk in strat.items():
            fr = pd.Series(ae[m][mk]).groupby(te.franchise_id.values[mk]).mean()
            rows.append(dict(model=m, model_label=names[m], scope=sn, n_transitions=int(mk.sum()), n_franchises=int(te.franchise_id[mk].nunique()), mae_log=ae[m][mk].mean(), rmse_log=float(np.sqrt(((y - pred[m])[mk] ** 2).mean())),
                             mae_log_franchise_mean=fr.mean(), pp_abs_err_mean=pe[m][mk].mean(), pp_abs_err_median=float(np.median(pe[m][mk]))))
    Mx = pd.DataFrame(rows); Mx.to_csv(f'{RES}/test_metrics.csv', index=False)
    # du bao theo transition_id
    P = te[['transition_id', 'franchise_id', 'fold', 'mau_chinh', 'quality_flag_any', 'open_prev', 'open_curr']].copy(); P['Y_true'] = y; P['pct_change_true'] = pct(y)
    for m in pred:
        P[f'Y_pred_{m}'] = pred[m]; P[f'pct_pred_{m}'] = pct(pred[m]); P[f'abs_err_log_{m}'] = ae[m]; P[f'abs_err_pp_{m}'] = pe[m]
    P.to_csv(f'{RES}/test_predictions_by_transition.csv', index=False)
    # so sanh ghep cap + bootstrap theo franchise
    rng = np.random.default_rng(a.seed); frs = te.franchise_id.values
    uf = np.unique(frs); idx = {f: np.where(frs == f)[0] for f in uf}
    pr_rows = []
    for ref in ('median', 'Y0'):
        for sn, mk in strat.items():
            d = (ae[ref] - ae['E0'])[mk]; f_mk = frs[mk]
            ufm = np.unique(f_mk); n_f = np.array([(f_mk == f).sum() for f in ufm]); s_f = np.array([d[f_mk == f].sum() for f in ufm])
            draws = rng.integers(0, len(ufm), size=(a.boot, len(ufm)))
            bs = s_f[draws].sum(1) / n_f[draws].sum(1)
            fr_d = np.array([d[f_mk == f].mean() for f in ufm])
            pr_rows.append(dict(reference=ref, scope=sn, n_transitions=int(mk.sum()), n_franchises=len(ufm), mae_reference=ae[ref][mk].mean(), mae_E0=ae['E0'][mk].mean(), delta_MAE=d.mean(),
                                direction='E0 sai so thap hon' if d.mean() > 0 else ('E0 sai so cao hon' if d.mean() < 0 else 'bang nhau'),
                                median_paired_diff=float(np.median(d)), share_transitions_E0_lower=float((d > 0).mean()), share_franchises_E0_lower=float((fr_d > 0).mean()),
                                boot_ci95_low=float(np.percentile(bs, 2.5)), boot_ci95_high=float(np.percentile(bs, 97.5)), boot_share_delta_positive=float((bs > 0).mean()),
                                pp_median_ref_minus_E0=float(np.median(pe[ref][mk]) - np.median(pe['E0'][mk])), note='bo tro: boot theo franchise (%d lan, seed %d), du bao co dinh, khong tinh bat dinh cua buoc fit tren dev' % (a.boot, a.seed)))
    pd.DataFrame(pr_rows).to_csv(f'{RES}/test_paired_comparison.csv', index=False)
    # transition anh huong lon
    tot = ae['E0'].sum(); T = P.copy(); T['share_total_abs_err_E0'] = T.abs_err_log_E0 / tot
    T.sort_values('abs_err_log_E0', ascending=False).head(15)[['transition_id', 'franchise_id', 'mau_chinh', 'quality_flag_any', 'open_prev', 'open_curr', 'Y_true', 'Y_pred_E0', 'abs_err_log_E0', 'abs_err_log_median', 'abs_err_log_Y0', 'share_total_abs_err_E0']].assign(note='quan sat sai so lon; chua phai loi du lieu da xac minh').to_csv(f'{RES}/test_top_errors.csv', index=False)
    infl = []
    for nm, mk in (('4 dong co co chat luong', te.quality_flag_any.values), ('|Y|>3', np.abs(y) > 3), ('open_prev>=1M nhung open_curr<1M', te.mau_chinh.values & (te.open_curr.values < 1e6)), ('15 dong sai so lon nhat (E0)', ae['E0'] >= np.sort(ae['E0'])[-15])):
        infl.append(dict(category=nm, n=int(mk.sum()), share_of_rows=float(mk.mean()), share_of_total_abs_err_E0=float(ae['E0'][mk].sum() / tot), mae_E0=float(ae['E0'][mk].mean()), mae_median=float(ae['median'][mk].mean()), mae_Y0=float(ae['Y0'][mk].mean())))
    pd.DataFrame(infl).to_csv(f'{RES}/test_influential_summary.csv', index=False)
    ev('score', 'cham 3 phuong an tren 193 dong', f"MAE E0={ae['E0'].mean():.6f} median={ae['median'].mean():.6f} Y0={ae['Y0'].mean():.6f}")
    # doi chieu dev/test
    def comp(df, tag):
        r = {}
        r['n_transitions'] = len(df); r['n_franchises'] = df.franchise_id.nunique()
        for lab, mk in (('open_prev>=1M', df.mau_chinh), ('open_prev<1M', ~df.mau_chinh)):
            r[f'n_{lab}'] = int(mk.sum()); r[f'fr_{lab}'] = int(df.franchise_id[mk].nunique())
        for lab, b in (('open_prev <1M', df.open_prev < 1e6), ('open_prev 1-10M', (df.open_prev >= 1e6) & (df.open_prev < 1e7)), ('open_prev 10-50M', (df.open_prev >= 1e7) & (df.open_prev < 5e7)), ('open_prev >=50M', df.open_prev >= 5e7)): r[f'n_{lab}'] = int(b.sum())
        for lab, b in (('<1990', df.release_year_n < 1990), ('1990s', df.release_year_n.between(1990, 1999)), ('2000s', df.release_year_n.between(2000, 2009)), ('2010s', df.release_year_n.between(2010, 2019)), ('>=2020', df.release_year_n >= 2020)): r[f'n_period {lab}'] = int(b.sum())
        for lab, b in (('pos 2', df.franchise_position_n == 2), ('pos 3', df.franchise_position_n == 3), ('pos 4-5', df.franchise_position_n.between(4, 5)), ('pos 6+', df.franchise_position_n >= 6)): r[f'n_{lab}'] = int(b.sum())
        for lab, b in (('gap <1', df.gap_years < 1), ('gap 1-3', df.gap_years.between(1, 3, inclusive='left')), ('gap 3-6', df.gap_years.between(3, 6, inclusive='left')), ('gap 6-10', df.gap_years.between(6, 10, inclusive='left')), ('gap >=10', df.gap_years >= 10)): r[f'n_{lab}'] = int(b.sum())
        r['n_quality_flag'] = int(df.quality_flag_any.sum()); r['n_open_curr<1M_in_>=1M'] = int((df.mau_chinh & (df.open_curr < 1e6)).sum()); r['n_|Y|>3'] = int((df.Y.abs() > 3).sum())
        for q in (0.05, 0.25, 0.5, 0.75, 0.95): r[f'Y_q{int(q*100):02d}'] = float(df.Y.quantile(q))
        r['Y_mean'] = float(df.Y.mean()); r['Y_sd'] = float(df.Y.std()); r['share_Y_negative'] = float((df.Y < 0).mean()); r['log_open_prev_mean'] = float(df.log_open_prev.mean()); r['log_open_prev_sd'] = float(df.log_open_prev.std())
        r['year_median'] = float(df.release_year_n.median()); r['year_min'] = int(df.release_year_n.min()); r['year_max'] = int(df.release_year_n.max()); r['gap_median'] = float(df.gap_years.median()); r['position_median'] = float(df.franchise_position_n.median())
        return pd.Series(r, name=tag)
    cmp_ = pd.concat([comp(dev, 'dev'), comp(te, 'test')], axis=1)
    cmp_['test_minus_dev_or_ratio'] = np.nan
    cmp_.index.name = 'metric'; cmp_.to_csv(f'{RES}/dev_test_composition.csv')
    # dev OOF vs test
    oof = pd.read_csv(f'{T3}/results/oof_predictions_wide.csv')
    drows = []
    for scope, mk in (('tat ca', np.ones(len(oof), bool)), ('open_prev >=1M', (oof.stratum == '>=1M').values), ('open_prev <1M', (oof.stratum == '<1M').values)):
        for m, lab in (('Y0', 'Y0'), ('median', 'median'), ('E0', 'E0')):
            dm = float(np.abs(oof.Y - oof[f'pred_{m}'])[mk].mean()); tm = float(Mx[(Mx.model == m) & (Mx.scope == scope)].mae_log.iloc[0])
            drows.append(dict(scope=scope, model=lab, dev_oof_mae=dm, test_mae=tm, test_minus_dev=tm - dm, protocol_note='dev: ngoai fold 4 lan; test: fit tren 725 dong, giu lai 193 dong'))
    DC = pd.DataFrame(drows); DC.to_csv(f'{RES}/dev_vs_test_mae.csv', index=False)
    dd = []
    for scope, mk in (('tat ca', np.ones(len(oof), bool)), ('open_prev >=1M', (oof.stratum == '>=1M').values), ('open_prev <1M', (oof.stratum == '<1M').values)):
        for ref in ('median', 'Y0'):
            dv = float(np.abs(oof.Y - oof[f'pred_{ref}'])[mk].mean() - np.abs(oof.Y - oof.pred_E0)[mk].mean())
            tv = float(pd.DataFrame(pr_rows).query('reference==@ref and scope==@scope').delta_MAE.iloc[0])
            dd.append(dict(scope=scope, reference=ref, delta_MAE_dev_oof=dv, delta_MAE_test=tv, same_direction=bool(np.sign(dv) == np.sign(tv))))
    pd.DataFrame(dd).to_csv(f'{RES}/delta_mae_dev_vs_test.csv', index=False)
    # tai lap dev S1/S2 (chi dev) va tong hop
    dev['stratum'] = np.where(dev.mau_chinh, '>=1M', '<1M')
    flag = dev.quality_flag_any.values; mods = ['Y0', 'median', 'E0']
    def vp(mask):
        return {'Y0': baseline_predict(dev, 'Y0', mask), 'median': baseline_predict(dev, 'median', mask), 'E0': cv_predict(dev, CONFIGS['E0'], None, mask)[0]}
    main = vp(None); s1 = vp(~flag); s2 = vp(dev.mau_chinh.values)
    s1m = pd.read_csv(f'{T3}/results/s1_metrics.csv'); s2m = pd.read_csv(f'{T3}/results/s2_metrics.csv')
    rows = []; maxdiff = 0
    for m in mods:
        for tag, pv, mk_, scope, ref_df, ref_scope in (('S1', s1, ~flag, '719 dong khong co', s1m, '719 dong khong co'), ('S1', s1, flag, '6 dong co co', s1m, '6 dong co co'),
                                                     ('S2', s2, np.ones(len(dev), bool), '725 dong dev', s2m, '725 dong dev'), ('S2', s2, dev.mau_chinh.values, '>=1M (576)', s2m, '>=1M'), ('S2', s2, ~dev.mau_chinh.values, '<1M (149)', s2m, '<1M')):
            mm = float(np.abs(dev.Y.values - main[m])[mk_].mean()); vv = float(np.abs(dev.Y.values - pv[m])[mk_].mean())
            t3 = ref_df[(ref_df.model == m) & (ref_df.scope == ref_scope) & (ref_df.variant == tag)].pooled_mae.iloc[0]; t3m = ref_df[(ref_df.model == m) & (ref_df.scope == ref_scope) & (ref_df.variant == 'main')].pooled_mae.iloc[0]
            maxdiff = max(maxdiff, abs(vv - t3), abs(mm - t3m))
            rows.append(dict(variant=tag, scope=scope, model=m, n=int(mk_.sum()), mae_main=mm, mae_variant=vv, main_minus_variant=mm - vv, task3_mae_main=t3m, task3_mae_variant=t3))
    pd.DataFrame(rows).to_csv(f'{RES}/s1_s2_dev_summary.csv', index=False)
    pd.DataFrame([dict(item='S1/S2 tai lap tren dev (chi dev) so voi bang Task 3', max_abs_diff=maxdiff, tolerance=1e-9, status='PASS' if maxdiff < 1e-9 else 'FAIL')]).to_csv(f'{RES}/s1_s2_reproduction_check.csv', index=False)
    ev('score', 'tong hop S1/S2 dev (khong chay tren test)', f'max_abs_diff vs Task 3 = {maxdiff:.2e}')
    save_log(); print(Mx.round(4).to_string(index=False)); print(pd.DataFrame(pr_rows)[['reference', 'scope', 'n_transitions', 'delta_MAE', 'boot_ci95_low', 'boot_ci95_high']].round(4).to_string(index=False)); print('S1/S2 repro diff', maxdiff)

if a.stage in ('prescore', 'all'): prescore()
if a.stage in ('score', 'all'): score()
