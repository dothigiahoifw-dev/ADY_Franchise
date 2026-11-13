# ADY — RQ3 Task 4 (chốt bước 6 + đánh giá bước 7), phiên bản v2

Đọc theo thứ tự (v2: xem `docs/CHANGELOG_v1_to_v2.md` và kết quả kiểm tra nhóm 11 franchise `results/R10c_G3_verification_11_franchises.csv`):
1. `docs/RQ3_task4_chot_buoc6_va_buoc7_bao_cao.md` — báo cáo chính (quyết định, thành phần mẫu, độ vững, diễn giải, nhật ký thay đổi).
2. `results/T4_decision_table.csv`, `T4_robustness_by_finding.csv`, `T4_interpretation_table.csv|md`, `T4_sample_change_A0_to_A2.csv` — các bảng bàn giao.
3. `results/T4_C1…C9`, `R10…`, `R5_v2…` — kết quả bổ sung; `figures/T4_F1…F4` — biểu đồ (dữ liệu vẽ: `figures/data/`).

`inherited_step5_6/` là bản sao nguyên trạng đầu ra bước 5–6 (không sửa) để Task 4 tái lập được. Gói bước 5–6 gốc không bị thay đổi.

Chạy lại (cần pandas, numpy, matplotlib; từ thư mục gốc gói):

    python code/t4_00_verify_inherited.py --root .          # kiểm tra kế thừa, độc lập với engine
    python code/t4_00b_helper_crosscheck.py --root . --chunk 100000   # tùy chọn, rất chậm; chạy lặp nhiều lần
    python code/t4_01_observability.py --root . --raw <thư mục chứa analysis_master_transitions.csv, analysis_master_films.csv, pairs_audit.csv>
    python code/t4_02_analysis.py --root .
    python code/t4_03_figures.py --root .
    python code/t4_04_tables.py --root .
    python code/t4_05_extract_report_tables.py --root .

- Bootstrap: cùng engine, seed 20260101, 10.000 lần, percentile 95% như bước 6; `--B` chỉ để thử nhanh.
- `t4_01` cần ba file gốc ở trên; các script khác chỉ cần `inherited_step5_6/`.
- Số liệu trong `docs/` do người viết điền từ kết quả; bảng tự sinh nằm trong `results/`.
