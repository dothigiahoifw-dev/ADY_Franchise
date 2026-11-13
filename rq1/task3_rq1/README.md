# ADY_PRJ RQ1 — Task 3 (Bước 5–6): gói kết quả

Chỉ dùng **725 dòng dev**. File test **chưa được mở hay chấm**. Cấu hình đã khóa: **E0** (`locked_config_rq1.json`).

## Thứ tự đọc
1. `TASK3_RQ1_REPORT.md` — báo cáo kết quả thực tế.
2. `locked_config_rq1.json` — cấu hình đã khóa, hash, phiên bản thư viện.
3. `results/` — bảng kết quả (xem bảng dưới); `figures/` — 5 biểu đồ PNG và CSV tạo hình.
4. `logs/` — nhật ký thử nghiệm, kiểm tra đầu vào, quyết định biểu diễn, output preflight.
5. `manifest_task3.csv` — hash mọi file.

| File | Nội dung |
|:-----------------------------|:-------------------------------------|
| `results/metrics_models_dev.csv` | MAE gộp, RMSE, từng fold, theo franchise, theo tầng, sai số điểm phần trăm: Y=0, median, E0–E4 |
| `results/paired_comparisons.csv` | So sánh ghép cặp theo `transition_id` và cổng kết luận so với từng baseline |
| `results/selection_table.csv`, `selection_steps.txt` | Chọn cấu hình theo quy tắc Task 2 |
| `results/oof_predictions_wide.csv` | Dự báo, sai số ngoài fold của mọi mô hình (1 dòng/transition) |
| `results/oof_predictions_selected_E0.csv` | Dự báo, phần dư, sai số log của cấu hình chọn |
| `results/coefficients_by_fold_main.csv` | Hệ số OLS theo fold |
| `results/e0_reproduction.csv` | Tái lập E0, median, Y=0 |
| `results/diag_*.csv` | Phần dư E4 theo nhóm và kết quả tiêu chí đổi biểu diễn |
| `results/s1_*.csv`, `s2_*.csv` | Độ nhạy S1/S2 (cùng dòng đánh giá), hệ số, dòng có cờ |
| `results/error_by_group.csv`, `error_by_id.csv`, `error_contribution_summary.csv` | Phân tích lỗi |
| `results/retro_E5_E7_status.csv` | E5–E7: NOT RUN và lý do |
| `inputs_dev/` | Bản sao đầu vào dev (hash khớp gói Task 2) |

## Chạy lại
Yêu cầu: Python 3.12, numpy, pandas, matplotlib; gói Task 2 đã giải nén (đường dẫn `PKG`).
```
python code/t3_run.py     --pkg PKG --out .      # kiểm tra đầu vào, tái lập E0, phần dư, E0-E4, chọn, S1/S2, phân tích lỗi
python code/t3_figures.py .                      # 5 biểu đồ
python code/t3_lock.py    . PKG                  # khóa cấu hình
python code/t3_manifest.py .                     # tạo manifest;  thêm --verify để kiểm tra hash
```
`t3_run.py` dừng với mã 1 nếu preflight hoặc kiểm tra đầu vào FAIL, hoặc E0 không khớp baseline; dừng với mã 3 nếu phần dư kích hoạt tiêu chí đổi biểu diễn mà chưa có `rep_decision.json`. Kết quả không có yếu tố ngẫu nhiên.

## Ghi chú
- Khi chạy lại, các mốc thời gian trong `logs/` và `locked_config_rq1.json` sẽ đổi; số liệu không đổi.
- Task sau (chấm test) cần khóa này và sự đồng ý của nhóm; không chấm E1–E4 trên test.
