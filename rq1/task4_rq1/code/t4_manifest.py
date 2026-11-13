#!/usr/bin/env python3
"""Tao hoac kiem tra manifest_task4.csv.  python t3_manifest.py <thu muc task3_rq1> [--verify]"""
import os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t3_common import sha256
root = sys.argv[1]; mp = f'{root}/manifest_task4.csv'
files = sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) for f in fs if f not in ('manifest_task4.csv',) and '__pycache__' not in d)
if '--verify' in sys.argv:
    m = pd.read_csv(mp); bad = [r.file for r in m.itertuples() if not os.path.exists(f'{root}/{r.file}') or sha256(f'{root}/{r.file}') != r.sha256]
    extra = sorted(set(files) - set(m.file))
    print('VERIFY:', 'PASS' if not bad and not extra else f'FAIL bad={bad} extra={extra}'); sys.exit(0 if not bad and not extra else 1)
pd.DataFrame([dict(file=f, sha256=sha256(f'{root}/{f}'), bytes=os.path.getsize(f'{root}/{f}')) for f in files]).to_csv(mp, index=False)
print('manifest', len(files), 'files')
