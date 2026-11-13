# ADY — RQ3 Task 5: báo cáo cuối và bàn giao (v1)

RQ3: Những mẫu hình thay đổi opening xuất hiện thế nào khi franchise tiến qua các phần? Target Y = ln(Open_N) − ln(Open_{N−1}); mẫu chính A1b (910 transition / 557 franchise). Task 5 giữ nguyên gói bước 5–6 và Task 4 v2 (trong `inherited_task4_v2/`) và xuất sản phẩm riêng.

## Dùng file nào cho việc gì

| Mục đích | File |
|---|---|
| **Báo cáo cuối** | `RQ3_Task5_Bao_cao_cuoi.md` (hình chèn theo đường dẫn tương đối `figures/main/…`) |
| **Kết luận ngắn ghép báo cáo chung** | `RQ3_Task5_ket_luan_ngan.md` |
| **Thuyết trình** | 5 hình chính `figures/main/Hinh1…Hinh5` (mỗi hình có chú thích mẫu, n/F, đại lượng, CI, thông điệp trong chính hình và trong báo cáo); bảng `results/T5_findings_table.md`; ý chính ở “Tóm tắt” và mục 5 của báo cáo |
| Bảng tổng hợp phát hiện (kèm nguồn số liệu và mức kiểm tra) | `results/T5_findings_table.csv` / `.md` |
| Dữ liệu vẽ hình chính | `figures/data/` |
| Hình phụ lục | `figures/appendix/PL1…PL6` (sao chép nguyên trạng từ bước 5–6 và Task 4; mô tả ở Phụ lục B) |
| Kiểm tra và đính chính | `logs/t5_01_verify_log.txt`, `results/T5_numbers_check.csv`, `docs/T5_dinh_chinh_nhat_ky.md` |
| **Tái lập** | `code/`, `run_all.sh`, `inherited_task4_v2/` (bản sao nguyên trạng Task 4 v2, bên trong có gói bước 5–6) |

## Thứ tự chạy (đường dẫn tương đối, từ thư mục gốc gói)

    bash run_all.sh [<thư mục chứa pairs_audit.csv và analysis_master_films.csv>]
    # hoặc từng bước:
    python code/t5_01_verify.py --root . [--raw <thư mục file thô>]   # kiểm tra độc lập: tái tính số chính, đọc lại CI, chạy lại mục tiêu 2–3 ô CI
    python code/t5_02_figures.py --root .                              # 5 hình chính + chép hình phụ lục
    python code/t5_03_findings_table.py --root .                       # bảng tổng hợp phát hiện
    python code/t5_04_build_report.py --root .                         # lắp RQ3_Task5_Bao_cao_cuoi.md từ docs/_templates/report_template.md

- **Thư viện:** Python 3, pandas, numpy, matplotlib. Không cần mạng.
- **Seed và bootstrap:** seed 20260101, 10.000 lần, percentile 95%, bootstrap theo franchise — kế thừa từ bước 6. Task 5 chỉ chạy lại có mục tiêu: CI trung vị D (A1b) và hai ô CI của PT2-lite (tập {2,3,4}); phần còn lại đọc từ kết quả kế thừa.
- **Không có trong gói:** `analysis_master_transitions.csv`, `analysis_master_films.csv`, `pairs_audit.csv`, `box_office_*.csv` (dữ liệu lớn). Các bảng đầu vào đã xử lý nằm trong `inherited_task4_v2/inherited_step5_6/input_tables/`. Nếu không truyền `--raw`, bước đối chiếu nhóm 11 franchise với file thô được ghi “KHÔNG CHẠY”, không tuyên bố đã tái lập (trong gói này, lần chạy có `--raw` đã cho kết quả khớp 198/198).
- **Đường dẫn:** mọi đường dẫn trong code và báo cáo là tương đối so với thư mục gốc của gói.

## Trạng thái kiểm tra

- **Đã chạy ở Task 5:** 198 mục kiểm tra, 198 khớp (tái tính độc lập điểm ước lượng chính, đọc lại CI PT1, chạy lại mục tiêu một số ô CI, đối chiếu nhóm 11 franchise với file thô).
- **Kế thừa, chưa tái tính:** CI ghép cặp, nhiều CI của PT2-lite/PT3 ở mẫu độ nhạy/PT4, bảng thành phần thập niên, chẩn đoán CI zero, đối chiếu helper v4 (479 lần lặp đầu). Xem Phụ lục C của báo cáo.
- **Đính chính:** khoảng ngày nhóm 11 franchise (đúng: 2026-11-04 đến 2028-12-13) và một làm tròn (+24,4%); xem `docs/T5_dinh_chinh_nhat_ky.md`.
