"""Kiem tra dau vao Task 3 (dev-only). FAIL -> thoat ma 1."""
import os, subprocess, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from t3_common import *

def run_checks(pkg, out_logs):
    CH = []
    def chk(cid, desc, ok, detail=''): CH.append(dict(id=cid, description=desc, status='PASS' if bool(ok) else 'FAIL', detail=str(detail)))
    pf = subprocess.run([sys.executable, os.path.join(pkg, 'task3_preflight.py'), '--root', pkg], capture_output=True, text=True)
    open(os.path.join(out_logs, 'preflight_output.txt'), 'w').write(pf.stdout + pf.stderr)
    chk('C01', 'task3_preflight.py PASS (ma thoat 0)', pf.returncode == 0, pf.stdout.strip().splitlines()[-1] if pf.stdout.strip() else pf.stderr[-200:])
    D = os.path.join(pkg, 'data')
    inp = pd.read_csv(os.path.join(D, 'rq1_inputs_dev.csv')); sp = pd.read_csv(os.path.join(D, 'split_assignment.csv')); bw = pd.read_csv(os.path.join(D, 'baseline_v2_dev_preds_wide.csv'))
    chk('C02', 'transition_id duy nhat trong dau vao dev', inp.transition_id.is_unique, len(inp))
    j1 = inp.merge(sp[sp.role == 'dev'], on='transition_id', suffixes=('', '_s'))
    j2 = inp.merge(bw, on='transition_id', suffixes=('', '_b'))
    chk('C03', 'join mot-mot dau vao dev / split / baseline wide (725 dong, khong nhan ban)', len(j1) == len(inp) == len(j2) == 725 and sp[sp.role == 'dev'].transition_id.is_unique and bw.transition_id.is_unique, (len(j1), len(j2)))
    chk('C04', 'moi franchise nam trong dung mot fold', inp.groupby('franchise_id').fold.nunique().max() == 1)
    chk('C05', 'Y huu han; open_prev, open_curr > 0', np.isfinite(inp.Y).all() and (inp.open_prev > 0).all() and (inp.open_curr > 0).all())
    chk('C06', '5 feature loi la so, huu han, khong thieu', all(pd.api.types.is_numeric_dtype(inp[c]) for c in CORE_RAW) and np.isfinite(inp[CORE_RAW].values.astype(float)).all())
    chk('C07', 'mien gia tri: gap>0, vi tri nguyen >=2, thang nguyen 1-12, nam 1900-2026',
        (inp.gap_years > 0).all() and (inp.franchise_position_n >= 2).all() and (inp.franchise_position_n % 1 == 0).all() and inp.release_month_n.between(1, 12).all() and (inp.release_month_n % 1 == 0).all() and inp.release_year_n.between(1900, 2026).all())
    allcols = set()
    for cfg in CONFIGS.values():
        _, names = build_X(inp, cfg); allcols |= set(names)
    chk('C08', 'cot dau vao model khai bao tuong minh, khong chua ID/open_curr/Y', not (allcols & FORBIDDEN_IN_X), sorted(allcols))
    t = pd.DataFrame(CH); t.to_csv(os.path.join(out_logs, 'checks_task3_input.csv'), index=False)
    print(t[['id', 'status', 'description']].to_string(index=False))
    if (t.status == 'FAIL').any():
        print('*** FAIL: dung Task 3 ***'); sys.exit(1)
    return inp, bw, sp
