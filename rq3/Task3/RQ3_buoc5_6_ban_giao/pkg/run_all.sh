#!/bin/bash
set -e
M=${1:-/mnt/user-data/uploads/analysis_master_transitions.csv}
D=${2:-/mnt/user-data/uploads/box_office_detailed.csv}
G=${3:-/mnt/user-data/uploads/box_office_raw.csv}
python3 code/01_prepare.py --root . --master "$M" --bo_detailed "$D" --bo_raw "$G"
python3 code/00_validate_engine.py .
python3 code/02_analyze.py --root .
python3 code/03_figures.py --root .
python3 code/04_test_matrix.py --root .
python3 code/05_selection_diagnostic.py --root .
