# ADY — RQ3 bước 5–6 (gói bàn giao)

Chạy lại toàn bộ (từ thư mục gốc gói này; cần pandas, numpy, matplotlib):

    python code/01_prepare.py --root . --master <analysis_master_transitions.csv> --bo_detailed <box_office_detailed.csv> --bo_raw <box_office_raw.csv>
    python code/00_validate_engine.py .
    python code/02_analyze.py --root .
    python code/03_figures.py --root .
    python code/04_test_matrix.py --root .
    python code/05_selection_diagnostic.py --root .
    # hoặc: bash run_all.sh <master> <detailed> <raw>

- Cấu hình: `config.json` (B = 10.000, seed = 20260101, các mốc cỡ mẫu). `--B` ở 02_analyze chỉ để thử nhanh.
- `01_prepare.py` dừng ngay (FAIL) nếu mọi kiểm tra/mốc không khớp.
- `ref_step3_step4/`: file ID/audit của bước 3–4 (đầu vào tham chiếu). File master 25.943 dòng và hai file box_office **không** nằm trong gói; truyền đường dẫn bằng tham số.
- Sau bước 5 và chỉ cần `input_tables/`, có thể chạy 02–05 mà không cần master.
- Thời gian chạy 02: khoảng 10 giây với 10.000 lần lặp.
- `rq3_stats_helpers.py` là helper v4 gốc (không sửa); `rq3_engine.py` là bản vector hóa, đã đối chiếu từng lần lặp với helper (`00_validate_engine.py`).
- Báo cáo: `docs/RQ3_buoc5_6_bao_cao_ket_qua_vong_dau.md`.
