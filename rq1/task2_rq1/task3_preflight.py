#!/usr/bin/env python3
"""Task 3 preflight: CHI doc du lieu dev. Khong mo/parse rq1_inputs_test_LOCKED.csv (chi tinh hash byte).
Moi kiem tra quan trong FAIL -> in FAIL, thoat ma 1, Task 3 khong duoc chay.
Dung:  python task3_preflight.py [--root .]
"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument('--root', default=os.path.dirname(os.path.abspath(__file__))); a = ap.parse_args()
R = a.root; D = os.path.join(R, 'data')
CH = []
def chk(cid, desc, ok, detail=''):
    CH.append(dict(id=cid, description=desc, status='PASS' if bool(ok) else 'FAIL', detail=str(detail)))
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for c in iter(lambda: fh.read(1 << 20), b''): h.update(c)
    return h.hexdigest()
def finish():
    t = pd.DataFrame(CH); print(t.to_string(index=False))
    if (t.status == 'FAIL').any():
        print('\n*** FAIL: %d kiem tra khong dat. DUNG, KHONG chay Task 3. ***' % int((t.status == 'FAIL').sum())); sys.exit(1)
    print('\nPREFLIGHT PASS (%d kiem tra). Task 3 chi duoc chay tren dev; khong cham test.' % len(t)); sys.exit(0)

# P01 hash theo manifest
mp = os.path.join(R, 'manifest_outputs.csv')
if not os.path.exists(mp):
    chk('P00', 'manifest_outputs.csv ton tai', False); finish()
man = pd.read_csv(mp)
for _, r in man.iterrows():
    p = os.path.join(R, r.file)
    chk('P01_' + r.file, 'hash khop manifest: ' + r.file, os.path.exists(p) and sha(p) == r.sha256)
if (pd.DataFrame(CH).status == 'FAIL').any(): finish()

cfg = json.load(open(os.path.join(R, 'design_config_rq1.json')))
chk('P02', 'cau hinh ghi ro Task 3 chi chay tren dev', 'CHI chay tren dev' in cfg['phase_rules']['task3_current'])
inp = pd.read_csv(os.path.join(D, 'rq1_inputs_dev.csv'))
sp = pd.read_csv(os.path.join(D, 'split_assignment.csv'))
bw = pd.read_csv(os.path.join(D, 'baseline_v2_dev_preds_wide.csv'))
dev = sp[sp.role == 'dev']
chk('P03', 'rq1_inputs_dev: 725 dong, transition_id duy nhat, toan bo role=dev, fold 1-4',
    len(inp) == 725 and inp.transition_id.is_unique and (inp.role == 'dev').all() and inp.fold.between(1, 4).all(), (len(inp), inp.role.unique().tolist()))
chk('P04', 'tap ID dev khop split_assignment', set(inp.transition_id) == set(dev.transition_id) and len(dev) == 725)
chk('P05', 'khong dong test trong file dev/baseline', not (set(inp.transition_id) | set(bw.transition_id)) & set(sp[sp.role != 'dev'].transition_id))
chk('P06', 'moi franchise dev dung 1 fold; fold khop split', inp.groupby('franchise_id').fold.nunique().max() == 1 and inp.merge(dev, on='transition_id', suffixes=('', '_s')).eval('fold == fold_s').all())
chk('P07', 'fold dev 178/185/176/186', inp.fold.value_counts().sort_index().tolist() == [178, 185, 176, 186], inp.fold.value_counts().sort_index().tolist())
chk('P08', 'open_prev, open_curr duong huu han; Y == ln(open_curr)-ln(open_prev) (tol 1e-12)',
    (inp.open_prev > 0).all() and (inp.open_curr > 0).all() and np.abs(inp.Y - (np.log(inp.open_curr) - np.log(inp.open_prev))).max() < 1e-12)
chk('P09', 'log_open_prev == ln(open_prev)', np.abs(inp.log_open_prev - np.log(inp.open_prev)).max() < 1e-12)
chk('P10', 'mau_chinh == (open_prev >= 1e6); 576 / 149', (inp.mau_chinh == (inp.open_prev >= 1e6)).all() and int(inp.mau_chinh.sum()) == 576)
chk('P11', '5 feature loi khong thieu', inp[['log_open_prev', 'gap_years', 'franchise_position_n', 'release_month_n', 'release_year_n']].notna().all().all())
chk('P12', 'gap_years > 0, vi tri >= 2, thang 1-12', (inp.gap_years > 0).all() and (inp.franchise_position_n >= 2).all() and inp.release_month_n.between(1, 12).all())
chk('P13', 'S1: dung 6 dong dev co quality_flag_any', int(inp.quality_flag_any.sum()) == 6, int(inp.quality_flag_any.sum()))
chk('P14', 'baseline: dung tap dev, khong thieu/trung, Y khop file dau vao',
    set(bw.transition_id) == set(inp.transition_id) and bw.transition_id.is_unique and bw.isna().sum().sum() == 0 and
    np.allclose(bw.merge(inp[['transition_id', 'Y']], on='transition_id', suffixes=('', '_i')).eval('Y - Y_i'), 0))
# tai lap baseline tu CHI file dev
m = inp.merge(bw[['transition_id', 'pred_Y0', 'pred_median_train', 'pred_reg_log_open_prev']], on='transition_id')
worst = {'pred_Y0': 0.0, 'pred_median_train': 0.0, 'pred_reg_log_open_prev': 0.0}
for k in (1, 2, 3, 4):
    tr, te = m[m.fold != k], m[m.fold == k]
    worst['pred_Y0'] = max(worst['pred_Y0'], float(np.abs(te.pred_Y0).max()))
    worst['pred_median_train'] = max(worst['pred_median_train'], float(np.abs(te.pred_median_train - tr.Y.median()).max()))
    worst['pred_reg_log_open_prev'] = max(worst['pred_reg_log_open_prev'], float(np.abs(te.pred_reg_log_open_prev - np.polyval(np.polyfit(tr.log_open_prev, tr.Y, 1), te.log_open_prev)).max()))
chk('P15', 'baseline v2 tai lap tu file dev (fit tren moi dong dev cua fold con lai), sai lech < 1e-9', max(worst.values()) < 1e-9, worst)
# metric tham chieu
ref = {c: float(np.abs(m.Y - m[c]).mean()) for c in worst}
chk('P16', 'MAE gop baseline khop tham chieu (0.8253 / 0.8124 / 0.8218)',
    abs(ref['pred_reg_log_open_prev'] - 0.8253) < 5e-5 and abs(ref['pred_median_train'] - 0.8124) < 5e-5 and abs(ref['pred_Y0'] - 0.8218) < 5e-5, {k: round(v, 4) for k, v in ref.items()})
# file test bi niem phong: chi hash byte (da kiem o P01), khong parse
chk('P17', 'file test niem phong ton tai (chi hash, khong doc noi dung)', os.path.exists(os.path.join(D, 'rq1_inputs_test_LOCKED.csv')))
finish()
