#!/usr/bin/env python3
"""Khoa phuong an (chi dua tren dev). Khong mo/cham test."""
import json, os, platform, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t3_common import *
OUT, PKG = sys.argv[1], sys.argv[2]; R = f'{OUT}/results'
st = json.load(open(f'{R}/_state.json')); SEL = st['selected']
M = pd.read_csv(f'{R}/metrics_models_dev.csv').set_index('model'); P = pd.read_csv(f'{R}/paired_comparisons.csv')
man = pd.read_csv(f'{PKG}/manifest_outputs.csv').set_index('file')
code_hash = {f: sha256(f'{OUT}/code/{f}') for f in sorted(os.listdir(f'{OUT}/code')) if f.endswith('.py')}
cfg = {
 'status': 'LOCKED - khoa tren dev, TRUOC khi cham test. Test chua duoc mo hoac cham.',
 'lock_time_utc': now_utc(),
 'selected_config': SEL,
 'selection_rule': 'Task 2 muc 7.3 (quy tac thuc hanh, khong phai kiem dinh thong ke): MAE gop < E0 va thap hon E0 o >= 3/4 fold; chon MAE thap nhat; uu tien cau hinh don gian neu kem < 0.005',
 'selection_steps': st['steps'],
 'selection_reason': 'Ca bon cau hinh E1-E4 deu co MAE gop cao hon E0 (E1 +0.0071 du thap hon E0 o 3/4 fold; E2 +0.0001; E3 +0.0032; E4 +0.0058) nen khong cau hinh nao dat cong; giu E0. Chon E0 KHONG co nghia E0 hon baseline don gian.',
 'algorithm': 'Linear Regression OLS (khong phat, co hang so), numpy.linalg.lstsq',
 'features_and_representation': {'log_open_prev': 'ln(open_prev) (cot log_open_prev)'},
 'unselected_candidates': {'E1': 'log_open_prev + ln(gap_years)', 'E2': 'log_open_prev + ln(franchise_position_n)', 'E3': 'log_open_prev + sin/cos(2*pi*thang/12) + (nam-2000)/10', 'E4': 'ca 5 feature loi'},
 'representation_changes': [], 'representation_note': 'Khong co dau hieu cu the theo tieu chi khai bao truoc tren phan du E4 (logs/representation_log.json); giu nguyen bieu dien ban dau',
 'preprocessing': 'Khong thieu du lieu o feature loi; khong scaling; moi buoc hoc tu du lieu fit trong train tung fold; khong ngau nhien',
 'baselines': ['Y=0', 'Median Y cua train', 'Linear Regression(log_open_prev) = E0'],
 'test_scoring_plan_for_later_task': 'fit E0 va hai baseline tren toan bo 725 dong dev; cham mot lan tren 193 dong test; khong cham E1-E4 de tranh chon theo test',
 'split': {'file': 'data/split_assignment.csv', 'sha256': man.loc['data/split_assignment.csv', 'sha256']},
 'inputs': {'rq1_inputs_dev.csv': man.loc['data/rq1_inputs_dev.csv', 'sha256'], 'baseline_v2_dev_preds_wide.csv': man.loc['data/baseline_v2_dev_preds_wide.csv', 'sha256'],
            'rq1_inputs_test_LOCKED.csv (chi hash byte, khong mo)': man.loc['data/rq1_inputs_test_LOCKED.csv', 'sha256'], 'design_config_rq1.json (Task 2)': man.loc['design_config_rq1.json', 'sha256']},
 'code_sha256': code_hash,
 'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__},
 'dev_results': {m: {'pooled_mae': round(float(M.loc[m, 'pooled_mae']), 6), 'rmse': round(float(M.loc[m, 'rmse']), 6), 'folds': [round(float(M.loc[m, f'fold{k}_mae']), 6) for k in range(1, 5)]} for m in M.index},
 'claim_gate_selected_vs_baselines': {r.reference: {'pooled_lower': bool(r.pooled_lower), 'folds_lower': int(r.folds_lower), 'pass': bool(r.pass_claim_gate)} for r in P[P.model == SEL].itertuples()},
 'e5_e7': 'NOT RUN (xem results/retro_E5_E7_status.csv)',
 'limitations': ['A1 (TMDB collection = franchise) va A2 (opening so sanh duoc) chua xac minh', 'Chon cau hinh chi tren dev; phan du E4 da duoc xem mot lan de kiem tra bieu dien (khong dua tren MAE)', 'Chi co franchise co opening ghi nhan; khong dai dien moi franchise', 'Cac transition cung franchise phu thuoc nhau'],
}
json.dump(cfg, open(f'{OUT}/locked_config_rq1.json', 'w'), ensure_ascii=False, indent=1)
lg = pd.read_csv(f'{OUT}/logs/experiment_log.csv')
lg = lg[~lg.stage.isin(['S7', 'S8'])]
lg = pd.concat([lg, pd.DataFrame([dict(time_utc=now_utc(), stage='S7', event='ve 5 bieu do + CSV tao hinh', detail='figures/'),
                                   dict(time_utc=now_utc(), stage='S8', event='khoa phuong an', detail=f'locked_config_rq1.json; selected={SEL}; khong mo/cham test')])])
lg.to_csv(f'{OUT}/logs/experiment_log.csv', index=False)
W = pd.read_csv(f'{R}/oof_predictions_wide.csv')
print('locked', SEL, '| pred E0 range', W.pred_E0.min().round(3), W.pred_E0.max().round(3), '| |resid|>6:', int(((W.Y - W.pred_E0).abs() > 6).sum()))
