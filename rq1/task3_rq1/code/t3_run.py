#!/usr/bin/env python3
"""RQ1 Task 3 (Buoc 5-6): pipeline, tai lap E0, phan du, E1-E4, chon cau hinh, S1/S2, phan tich loi, hinh, khoa.
CHI doc du lieu dev trong goi Task 2. Khong mo/parse rq1_inputs_test_LOCKED.csv. Khong cham test.
Dung: python t3_run.py --pkg <thu muc task2_rq1> --out <thu muc task3_rq1> [--until diag]"""
import argparse, json, os, sys, shutil, platform
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)  # nhom con (6 dong co) khong du moi fold -> MAE fold = NaN, co chu y
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t3_common import *
from t3_checks import run_checks

ap = argparse.ArgumentParser(); ap.add_argument('--pkg', required=True); ap.add_argument('--out', required=True); ap.add_argument('--until', default='all')
a = ap.parse_args()
OUT = a.out; R = f'{OUT}/results'; LG = f'{OUT}/logs'; FG = f'{OUT}/figures'
for d_ in (R, LG, FG, f'{OUT}/inputs_dev'): os.makedirs(d_, exist_ok=True)
log = Log(f'{LG}/experiment_log.csv')
log.add('S0', 'bat dau', f'python {platform.python_version()} numpy {np.__version__} pandas {pd.__version__}')

# ---------- S0: kiem tra dau vao ----------
inp, bw, sp = run_checks(a.pkg, LG)
log.add('S0', 'kiem tra dau vao', 'tat ca PASS (xem logs/checks_task3_input.csv)')
for fn in ['rq1_inputs_dev.csv', 'baseline_v2_dev_preds_wide.csv', 'split_assignment.csv']:
    shutil.copy(os.path.join(a.pkg, 'data', fn), f'{OUT}/inputs_dev/{fn}')
dev = inp.sort_values('transition_id').reset_index(drop=True)
bwa = bw.set_index('transition_id').loc[dev.transition_id]
dev['stratum'] = np.where(dev.mau_chinh, '>=1M', '<1M')
n_params = {'Y0': 0, 'median': 1, 'E0': 2, 'E1': 3, 'E2': 3, 'E3': 5, 'E4': 7}

# ---------- S1: tai lap E0 va baseline ----------
pred = {'Y0': baseline_predict(dev, 'Y0'), 'median': baseline_predict(dev, 'median')}
pred['E0'], coef = cv_predict(dev, CONFIGS['E0'])
rep = {'pred_reg_log_open_prev': float(np.abs(pred['E0'] - bwa.pred_reg_log_open_prev.values).max()),
       'pred_median_train': float(np.abs(pred['median'] - bwa.pred_median_train.values).max()),
       'pred_Y0': float(np.abs(pred['Y0'] - bwa.pred_Y0.values).max())}
rep_ok = max(rep.values()) < 1e-9
pd.DataFrame([dict(item=k, max_abs_diff=v, tolerance=1e-9, status='PASS' if v < 1e-9 else 'FAIL') for k, v in rep.items()]).to_csv(f'{R}/e0_reproduction.csv', index=False)
log.add('S1', 'tai lap E0 va baseline theo transition_id', f'{rep} -> {"PASS" if rep_ok else "FAIL"}')
print('Tai lap E0/baseline:', rep)
if not rep_ok:
    log.save(); print('*** FAIL: E0 khong khop baseline tham chieu. DUNG. ***'); sys.exit(1)

# ---------- S2: phan du E4 ban dau (chi phan du, khong in MAE) ----------
p4, _ = cv_predict(dev, CONFIGS['E4'])
res = dev.Y.values - p4
grp = {
 'log_open_prev': pd.qcut(dev.log_open_prev, 5, labels=[f'Q{i}' for i in range(1, 6)]),
 'gap_years': pd.qcut(dev.gap_years, 5, labels=[f'Q{i}' for i in range(1, 6)]),
 'franchise_position_n': pd.cut(dev.franchise_position_n, [1, 2, 3, 5, 99], labels=['2', '3', '4-5', '6+']),
 'release_month_n': pd.cut(dev.release_month_n, [0, 3, 6, 9, 12], labels=['T1(1-3)', 'T2(4-6)', 'T3(7-9)', 'T4(10-12)']),
 'release_year_n': pd.cut(dev.release_year_n, [0, 1989, 1999, 2009, 2019, 2100], labels=['<1990', '1990s', '2000s', '2010s', '>=2020'])}
rows = []; trig = {}
for f_, g_ in grp.items():
    t = pd.DataFrame({'g': g_.values, 'r': res}).groupby('g', observed=True).r.agg(['size', 'mean', 'std']).reset_index()
    t['se'] = t['std'] / np.sqrt(t['size']); t['z'] = t['mean'] / t['se']
    t['strong'] = (t['size'] >= 30) & (t['mean'].abs() >= 0.15) & (t['z'].abs() > 2)
    t.insert(0, 'feature', f_); rows.append(t)
    s = t.reset_index(drop=True); fired = False
    for i in range(len(s) - 1):
        if s.strong[i] and s.strong[i + 1] and np.sign(s['mean'][i]) == np.sign(s['mean'][i + 1]): fired = True
    trig[f_] = fired
diag = pd.concat(rows); diag.rename(columns={'g': 'bin', 'size': 'n', 'mean': 'mean_residual', 'std': 'sd_residual'}, inplace=True)
diag.to_csv(f'{R}/diag_residual_bins_E4.csv', index=False)
pd.DataFrame([dict(feature=k, triggered=v) for k, v in trig.items()]).to_csv(f'{R}/diag_representation_trigger.csv', index=False)
log.add('S2', 'phan du E4 ban dau (OOF) theo feature', f'tieu chi khai bao truoc: >=2 bin lien ke cung dau, moi bin n>=30, |mean|>=0.15, |z|>2; ket qua trigger={trig}')
print('Trigger bieu dien:', trig)
rep_dec_path = f'{OUT}/rep_decision.json'
rep_over = {}
if any(trig.values()):
    if not os.path.exists(rep_dec_path):
        log.save(); print('*** CAN XEM XET BIEU DIEN: co trigger, chua co rep_decision.json. Dung. ***'); sys.exit(3)
    rep_over = json.load(open(rep_dec_path))
else:
    json.dump({'changes': [], 'reason': 'khong co dau hieu cu the theo tieu chi khai bao truoc; giu bieu dien ban dau', 'time_utc': now_utc()}, open(f'{LG}/representation_log.json', 'w'), ensure_ascii=False, indent=1)
    log.add('S2', 'quyet dinh bieu dien', 'giu nguyen bieu dien ban dau (0 thay doi)')
if a.until == 'diag':
    log.save(); print('Dung sau diag'); sys.exit(0)
REP = {}   # khong co override (xem representation_log.json)

# ---------- S3: chay E1-E4 ----------
for m in ['E1', 'E2', 'E3', 'E4']:
    pred[m], c_ = cv_predict(dev, CONFIGS[m], REP); c_.insert(0, 'model', m); coef = pd.concat([coef.assign(model='E0') if 'model' not in coef.columns else coef, c_])
coef = coef[['model', 'fold', 'n_train', 'intercept', 'log_open_prev', 'ln_gap_years', 'ln_franchise_position_n', 'sin_month', 'cos_month', 'year_c10']]
coef.to_csv(f'{R}/coefficients_by_fold_main.csv', index=False)
order = ['Y0', 'median', 'E0', 'E1', 'E2', 'E3', 'E4']
M = pd.DataFrame([metrics_row(m, dev, pred[m], n_params[m]) for m in order]); M.to_csv(f'{R}/metrics_models_dev.csv', index=False)
ae = {m: np.abs(dev.Y.values - pred[m]) for m in order}
foldm = {m: np.array([ae[m][dev.fold.values == k].mean() for k in FOLDS]) for m in order}
# so sanh ghep cap theo transition_id
pr = []
for m in order:
    for ref in ['Y0', 'median', 'E0']:
        if m == ref: continue
        d_ = ae[ref] - ae[m]; fb = int((foldm[m] < foldm[ref]).sum())
        pr.append(dict(model=m, reference=ref, mean_diff_ref_minus_model=d_.mean(), median_diff=float(np.median(d_)), share_transitions_improved=float((d_ > 0).mean()),
                       pooled_lower=bool(ae[m].mean() < ae[ref].mean()), folds_lower=fb, pass_claim_gate=bool(ae[m].mean() < ae[ref].mean() and fb >= 3),
                       fold_diffs=';'.join(f'{x:.4f}' for x in (foldm[ref] - foldm[m]))))
P = pd.DataFrame(pr); P.to_csv(f'{R}/paired_comparisons.csv', index=False)
sel_tab = pd.DataFrame([dict(model=m, pooled_mae=ae[m].mean(), diff_vs_E0=ae['E0'].mean() - ae[m].mean(),
                             folds_better_vs_E0=int((foldm[m] < foldm['E0']).sum()) if m != 'E0' else np.nan) for m in ['E0', 'E1', 'E2', 'E3', 'E4']])
chosen, steps, cand = select_config(sel_tab)
cand['complexity'] = cand.model.map(COMPLEXITY)
sel_out = sel_tab.merge(cand[['model', 'eligible', 'complexity']], on='model', how='left'); sel_out.to_csv(f'{R}/selection_table.csv', index=False)
open(f'{R}/selection_steps.txt', 'w').write('\n'.join(steps) + '\n')
log.add('S3', 'chay E1-E4 va ap quy tac chon', ' | '.join(steps))
print('\n'.join(steps)); print(M[['model', 'pooled_mae', 'rmse', 'mean_fold_mae', 'sd_fold_mae']].round(4).to_string(index=False))
SEL = chosen
# du bao OOF theo transition_id (mot dong / transition, khong nhan ban)
W = dev[['transition_id', 'franchise_id', 'fold', 'Y', 'stratum', 'quality_flag_any', 'open_prev', 'open_curr']].copy()
for m in order: W[f'pred_{m}'] = pred[m]
for m in order: W[f'ae_{m}'] = ae[m]
assert len(W) == 725 and W.transition_id.is_unique
W.to_csv(f'{R}/oof_predictions_wide.csv', index=False)
S = dev[['transition_id', 'franchise_id', 'fold', 'Y', 'stratum', 'quality_flag_any']].copy()
S['prediction'] = pred[SEL]; S['residual'] = dev.Y.values - pred[SEL]; S['absolute_error_log'] = ae[SEL]; S['selected_config'] = SEL
S.to_csv(f'{R}/oof_predictions_selected_{SEL}.csv', index=False)

# ---------- S4: do nhay S1 / S2 ----------
def variant(train_mask, tag):
    pv = {'Y0': baseline_predict(dev, 'Y0', train_mask), 'median': baseline_predict(dev, 'median', train_mask)}
    pv['E0'], c0 = cv_predict(dev, CONFIGS['E0'], None, train_mask)
    pv[SEL], cs = cv_predict(dev, CONFIGS[SEL], REP, train_mask) if SEL != 'E0' else (pv['E0'], c0)
    cs.insert(0, 'variant', tag); return pv, cs
flag = dev.quality_flag_any.values
mods = ['Y0', 'median', 'E0'] + ([SEL] if SEL != 'E0' else [])
def metr(d, p, name, tag, scope):
    r = metrics_row(name, d, p); r['variant'] = tag; r['scope'] = scope; return r
# S1
p1, c1 = variant(~flag, 'S1'); unflag = ~flag
rows = []; pair1 = []
for m in mods:
    base_p = pred[m]
    rows.append(metr(dev[unflag], base_p[unflag], m, 'main', '719 dong khong co'))
    rows.append(metr(dev[unflag], p1[m][unflag], m, 'S1', '719 dong khong co'))
    d_ = np.abs(dev.Y.values - base_p)[unflag] - np.abs(dev.Y.values - p1[m])[unflag]
    pair1.append(dict(model=m, n=int(unflag.sum()), mae_main=float(np.abs(dev.Y.values - base_p)[unflag].mean()), mae_S1=float(np.abs(dev.Y.values - p1[m])[unflag].mean()),
                      mean_diff_main_minus_S1=float(d_.mean()), share_rows_S1_lower=float((d_ > 0).mean()), mean_abs_pred_shift=float(np.abs(base_p - p1[m])[unflag].mean()), max_abs_pred_shift=float(np.abs(base_p - p1[m])[unflag].max())))
    if flag.any():
        rows.append(metr(dev[flag], base_p[flag], m, 'main', '6 dong co co')); rows.append(metr(dev[flag], p1[m][flag], m, 'S1', '6 dong co co'))
pd.DataFrame(rows).to_csv(f'{R}/s1_metrics.csv', index=False); pd.DataFrame(pair1).to_csv(f'{R}/s1_paired_effect.csv', index=False)
fl = dev[flag][['transition_id', 'franchise_id', 'fold', 'open_prev', 'open_curr', 'Y']].copy()
for m in mods:
    fl[f'pred_main_{m}'] = pred[m][flag]; fl[f'pred_S1_{m}'] = p1[m][flag]; fl[f'ae_main_{m}'] = ae[m][flag]; fl[f'ae_S1_{m}'] = np.abs(dev.Y.values - p1[m])[flag]
fl.to_csv(f'{R}/s1_flagged_rows.csv', index=False)
cm = coef[coef.model == SEL].drop(columns=['model']).assign(variant='main'); cm = pd.concat([cm, c1]); cm.to_csv(f'{R}/s1_s2_coefficients_selected.csv', index=False)
# S2
p2, c2 = variant(dev.mau_chinh.values, 'S2')
rows = []; pair2 = []
for m in mods:
    for scope, mk in (('725 dong dev', np.ones(len(dev), bool)), ('>=1M', dev.mau_chinh.values), ('<1M', ~dev.mau_chinh.values)):
        rows.append(metr(dev[mk], pred[m][mk], m, 'main', scope)); rows.append(metr(dev[mk], p2[m][mk], m, 'S2', scope))
        d_ = (np.abs(dev.Y.values - pred[m]) - np.abs(dev.Y.values - p2[m]))[mk]
        pair2.append(dict(model=m, scope=scope, n=int(mk.sum()), mae_main=float(np.abs(dev.Y.values - pred[m])[mk].mean()), mae_S2=float(np.abs(dev.Y.values - p2[m])[mk].mean()),
                          mean_diff_main_minus_S2=float(d_.mean()), share_rows_S2_lower=float((d_ > 0).mean()), mean_abs_pred_shift=float(np.abs(pred[m] - p2[m])[mk].mean())))
pd.DataFrame(rows).to_csv(f'{R}/s2_metrics.csv', index=False); pd.DataFrame(pair2).to_csv(f'{R}/s2_paired_effect.csv', index=False)
pd.concat([cm, c2]).drop_duplicates(['variant', 'fold']).to_csv(f'{R}/s1_s2_coefficients_selected.csv', index=False)
# do nhay: hang Y/n cua baseline S1/S2 de so sanh claim gate
log.add('S4', 'chay S1, S2 (cau hinh da chon, khong chon lai)', f'selected={SEL}')

# ---------- S5: phan tich loi ----------
dev['pred_sel'] = pred[SEL]; dev['ae_sel'] = ae[SEL]
tot = dev.ae_sel.sum()
dims = {
 'open_prev': pd.cut(dev.open_prev, [0, 1e6, 1e7, 5e7, 1e13], right=False, labels=['<1M', '1-10M', '10-50M', '>=50M']),
 'gap_years': pd.cut(dev.gap_years, [0, 1, 3, 6, 10, 100], right=False, labels=['<1', '1-3', '3-6', '6-10', '>=10']),
 'franchise_position_n': pd.cut(dev.franchise_position_n, [1, 2, 3, 5, 99], labels=['2', '3', '4-5', '6+']),
 'release_period': pd.cut(dev.release_year_n, [0, 1989, 1999, 2009, 2019, 2100], labels=['<1990', '1990s', '2000s', '2010s', '>=2020']),
 'stratum': dev.stratum}
er = []
for dn, g_ in dims.items():
    for lab in pd.Series(g_).astype(str).unique():
        mk = (pd.Series(g_).astype(str) == lab).values
        if mk.sum() == 0: continue
        r = dict(dimension=dn, group=lab, n_transitions=int(mk.sum()), n_franchises=int(dev.franchise_id[mk].nunique()), small_n_flag=bool(mk.sum() < 30), share_of_total_abs_error_selected=float(ae[SEL][mk].sum() / tot))
        for m in sorted(set(['Y0', 'median', 'E0', SEL]), key=order.index): r[f'mae_{m}'] = float(ae[m][mk].mean())
        r['mae_selected'] = float(ae[SEL][mk].mean()); er.append(r)
ER = pd.DataFrame(er); ER.to_csv(f'{R}/error_by_group.csv', index=False)
dev['cat_flag6'] = dev.quality_flag_any; dev['cat_31'] = dev.mau_chinh & (dev.open_curr < 1e6); dev['cat_absY3'] = dev.Y.abs() > 3
dev['rank_ae'] = dev.ae_sel.rank(ascending=False, method='first'); dev['cat_top30'] = dev.rank_ae <= 30
idr = dev[dev.cat_flag6 | dev.cat_31 | dev.cat_absY3 | dev.cat_top30][['transition_id', 'franchise_id', 'fold', 'stratum', 'open_prev', 'open_curr', 'Y', 'pred_sel', 'ae_sel', 'cat_flag6', 'cat_31', 'cat_absY3', 'cat_top30']].copy()
idr['ae_median'] = ae['median'][idr.index]; idr['share_total_abs_error_selected'] = idr.ae_sel / tot
idr['note'] = 'can doi chieu dinh nghia nguon; chua ket luan sai du lieu'
idr.sort_values('ae_sel', ascending=False).to_csv(f'{R}/error_by_id.csv', index=False)
cs = []
for nm, col in (('6 dong co chat luong', 'cat_flag6'), ('31 dong open_prev>=1M, open_curr<1M', 'cat_31'), ('|Y|>3', 'cat_absY3'), ('30 dong sai so lon nhat', 'cat_top30')):
    mk = dev[col].values
    cs.append(dict(category=nm, n=int(mk.sum()), share_of_rows=float(mk.mean()), share_of_total_abs_error_selected=float(ae[SEL][mk].sum() / tot), mae_selected=float(ae[SEL][mk].mean()),
                   mae_median=float(ae['median'][mk].mean()), mae_Y0=float(ae['Y0'][mk].mean())))
mk_any = (dev.cat_flag6 | dev.cat_31 | dev.cat_absY3).values
cs.append(dict(category='hop cua (6 co, 31 dong, |Y|>3)', n=int(mk_any.sum()), share_of_rows=float(mk_any.mean()), share_of_total_abs_error_selected=float(ae[SEL][mk_any].sum() / tot), mae_selected=float(ae[SEL][mk_any].mean()), mae_median=float(ae['median'][mk_any].mean()), mae_Y0=float(ae['Y0'][mk_any].mean())))
pd.DataFrame(cs).to_csv(f'{R}/error_contribution_summary.csv', index=False)
log.add('S5', 'phan tich loi theo nhom va theo ID', 'khong loai dong nao')

# ---------- E5-E7: trang thai ----------
polfiles = [f for f in ('rq1_feature_policy.csv', 'feature_registry_transitions.csv') if os.path.exists(os.path.join(a.pkg, f)) or os.path.exists(os.path.join(a.pkg, 'data', f))]
st = [dict(id=i, features=f_, status='NOT RUN', reason='Khong co rq1_feature_policy.csv / feature_registry_transitions.csv trong goi Task 2; Task 1 bao director/studio la RQ2_ONLY_PENDING (ke thua, chua kiem). Cot ton tai trong dev khong dong nghia duoc phep dung. Khong chan ket qua loi.')
      for i, f_ in (('E5', 'E4 + is_director_changed'), ('E6', 'E4 + studio_changed (+co thieu)'), ('E7', 'E4 + genre_jaccard'))]
pd.DataFrame(st).to_csv(f'{R}/retro_E5_E7_status.csv', index=False)
log.add('S6', 'E5-E7', f'NOT RUN; file policy/registry trong goi: {polfiles}')
log.save()
json.dump(dict(selected=SEL, steps=steps, rep_override=REP), open(f'{R}/_state.json', 'w'))
print('XONG tables; chon:', SEL)
