# ADY_PRJ RQ1 — Task 4: chốt bước 6 và đánh giá cuối trên test

Chỉ chấm **ba phương án đã khóa** trên **193 transition test**: E0 (OLS `log_open_prev`), median Y của dev, Y=0. Không chạy E1–E7 trên test.

## Thứ tự đọc
1. `TASK4_RQ1_REPORT.md` — bảng chốt bước 6, kết quả test, độ vững, diễn giải RQ1, giới hạn.
2. `records/prescore_record.json` — bản ghi ghi **trước** khi mở nội dung file test.
3. `results/` — metric, so sánh ghép cặp, dự báo theo `transition_id`, đối chiếu dev/test, S1/S2 dev.
4. `logs/` — kiểm tra trước chấm, kiểm tra tập test, nhật ký lượt chấm.
5. `figures/`, `manifest_task4.csv`.

## Tái lập
Cần: Python 3.12, numpy, pandas, matplotlib; gói `task3_rq1` và `task2_rq1` đã giải nén.
```
python code/t4_run.py --t3 <task3_rq1> --t2 <task2_rq1> --out . --stage prescore
python code/t4_run.py --t3 <task3_rq1> --t2 <task2_rq1> --out . --stage score
python code/t4_figures.py .
python code/t4_manifest.py .            # tạo manifest;  --verify để kiểm
```
- `prescore` dừng (mã 1) nếu hash hoặc thiết kế không khớp; không đọc nội dung file test (chỉ hash byte).
- `score` dừng nếu `prescore_record.json` bị đổi, hash test khác bản ghi, hoặc tập test sai (193 dòng, ID, franchise, target). Không tự loại dòng.
- Bootstrap bổ trợ dùng seed cố định (20261107); các giá trị khác không có yếu tố ngẫu nhiên. Chạy lại sẽ đổi mốc thời gian trong log nhưng không đổi số liệu.

## Lưu ý
- Quy tắc 3/4 fold chỉ giải thích lựa chọn trên dev; không áp dụng lên test.
- Gói Task 3 giữ nguyên (không sửa); giới hạn kỹ thuật nhánh `rep_decision.json` được ghi trong báo cáo (P15).
