"""Task 5 / RQ3 - lap bao cao cuoi tu mau docs/_templates/report_template.md: chen bang tong hop phat hien (tu results/T5_findings_table.csv) va tom tat kiem tra (tu logs).
Chay: python code/t5_04_build_report.py --root .   -> RQ3_Task5_Bao_cao_cuoi.md (o thu muc goc de duong dan hinh tuong doi dung)"""
import argparse, os
import pandas as pd
R = argparse.ArgumentParser(); R.add_argument('--root', default='.'); R = R.parse_args().root
t = open(os.path.join(R, 'docs', '_templates', 'report_template.md'), encoding='utf-8').read()
F = pd.read_csv(os.path.join(R, 'results', 'T5_findings_table.csv'))
cols = ['ID', 'Loại', 'Câu hỏi', 'Kết quả và CI', 'Kết luận được phép', 'Giới hạn', 'Mức kiểm tra ở Task 5']
tab = '| ' + ' | '.join(cols) + ' |\n|' + '---|' * len(cols) + '\n' + '\n'.join('| ' + ' | '.join(str(v).replace('|', '/') for v in r) + ' |' for r in F[cols].values)
log = open(os.path.join(R, 'logs', 't5_01_verify_log.txt'), encoding='utf-8').read().strip().split('\n')[0]
V = pd.read_csv(os.path.join(R, 'results', 'T5_numbers_check.csv')); n = len(V); ok = int((V.match == True).sum())
summ = f'{n} mục, {ok} khớp, {n - ok} không khớp' + (' (chi tiết từng mục trong `results/T5_numbers_check.csv`).' if n else '.')
t = t.replace('{{FINDINGS_TABLE}}', tab).replace('{{CHECK_SUMMARY}}', summ)
assert '{{' not in t
open(os.path.join(R, 'RQ3_Task5_Bao_cao_cuoi.md'), 'w', encoding='utf-8').write(t); print('report built;', summ)
