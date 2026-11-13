#!/bin/bash
# Chạy từ thư mục gốc gói (đường dẫn tương đối). Cần pandas, numpy, matplotlib.
# Tham số tùy chọn: thư mục chứa file thô (pairs_audit.csv, analysis_master_films.csv) để đối chiếu nhóm 11 franchise.
set -e
RAW=${1:-}
if [ -n "$RAW" ]; then python3 code/t5_01_verify.py --root . --raw "$RAW"; else python3 code/t5_01_verify.py --root .; fi
python3 code/t5_02_figures.py --root .
python3 code/t5_03_findings_table.py --root .
python3 code/t5_04_build_report.py --root .
