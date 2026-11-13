"""Tach cac bang markdown trong bao cao Task 4 thanh CSV may doc (bang quyet dinh, bang do vung theo phat hien)."""
import argparse, os, re
import pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument('--root', default='.'); R = ap.parse_args().root
txt = open(os.path.join(R, 'docs', 'RQ3_task4_chot_buoc6_va_buoc7_bao_cao.md'), encoding='utf-8').read()
def table_after(head):
    i = txt.index(head); lines = []
    for ln in txt[i:].split('\n')[1:]:
        if ln.startswith('|'): lines.append(ln)
        elif lines: break
    rows = [[c.strip() for c in l.strip()[1:-1].split(' | ')] for l in lines if not re.match(r'^\|[-| ]+\|$', l)]
    rows = [[c.strip(' |') if False else c for c in r] for r in rows]
    return pd.DataFrame(rows[1:], columns=rows[0])
table_after('## 2. Bảng quyết định chốt bước 6').to_csv(os.path.join(R, 'results', 'T4_decision_table.csv'), index=False, encoding='utf-8-sig')
table_after('### 4.1. Theo từng phát hiện').to_csv(os.path.join(R, 'results', 'T4_robustness_by_finding.csv'), index=False, encoding='utf-8-sig')
table_after('### 3.3. Mẫu thay đổi thế nào').to_csv(os.path.join(R, 'results', 'T4_sample_change_A0_to_A2.csv'), index=False, encoding='utf-8-sig')
print('extracted')
