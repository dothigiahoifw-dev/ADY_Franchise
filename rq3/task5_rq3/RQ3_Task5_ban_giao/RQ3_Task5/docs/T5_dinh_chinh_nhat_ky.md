# Task 5 — Nhật ký đính chính và kiểm tra

Phạm vi: chỉ ghi các điểm phát hiện khi kiểm tra kế thừa ở Task 5. Không sửa file của bước 5–6 hay Task 4 (đã giữ nguyên trong `inherited_task4_v2/`). Không có lỗi nào ảnh hưởng đến kết quả (số liệu, CI, kết luận).

## Đính chính

| # | Phát hiện | Bằng chứng | Phạm vi ảnh hưởng | Xử lý |
|---|---|---|---|---|
| E1 | Khoảng ngày phim vị trí 3 của nhóm 11 franchise ghi sai trong văn bản. Báo cáo Task 4 v2 (mục 3.5) và `CHANGELOG_v1_to_v2.md` ghi “từ 2026-11-04 đến 2028-10-05 (Gremlins 3)”. Khoảng đúng là **2026-11-04 đến 2028-12-13**; phim muộn nhất là *Black Panther 3* (2028-12-13), còn *Gremlins 3* (2028-10-05) là phim muộn thứ hai | `inherited_task4_v2/results/R10c_G3_verification_11_franchises.csv` (min 2026-11-04, max 2028-12-13); đối chiếu lại với `pairs_audit.csv` gốc ở Task 5 (`T5_numbers_check.csv`, các dòng R10c) | Chỉ văn bản. CSV đúng; kết luận (11/11 đạt, cờ unreleased tại thời điểm dữ liệu, ngày sau 2026-10-22) không đổi | Không sửa CSV (đúng). Task 5 dùng khoảng đúng. File văn bản Task 4 v2 được giữ nguyên làm bản kế thừa |
| E2 | Làm tròn: báo cáo bước 5–6 (mục 4.3) ghi trung vị Y(1→2) của mẫu PT3 là “+0,219 (+24,5%)”. Giá trị đúng là 0,2185 → **+24,4%** (24,43%) | `R3_PT3_D_all_samples.csv` (median_Y12 = 0,21854); `T4_C2` (+24,43%) | Chỉ làm tròn trong một câu của báo cáo bước 5–6; các bảng và báo cáo Task 4 dùng +24,4% | Báo cáo cuối dùng +24,4% |

## Kiểm tra đã chạy ở Task 5 (độc lập với bản kế thừa)

`code/t5_01_verify.py` → `logs/t5_01_verify_log.txt`, `results/T5_numbers_check.csv`: 198 mục, 198 khớp, 0 không khớp, 0 mục không chạy. Gồm: tái tính độc lập PT1 (4 mẫu × 6 nhóm), trọng số và LOFO ở nhóm ≥6, PT3, PT2-lite, CH, |Y|>3, thành phần vị trí 2; đọc lại CI PT1 từ 10.000 bản lặp lưu; chạy lại mục tiêu CI trung vị D và hai ô CI của PT2-lite; đối chiếu nhóm 11 franchise và `retrieval_date` với `pairs_audit.csv` và `analysis_master_films.csv` gốc.

## Kiểm tra kế thừa không tái tính ở Task 5

CI của các phép đối chiếu mẫu (ghép cặp), CI PT2-lite ngoài hai ô trên, CI D34/D45, CI PT3 ở A0/A1/A2, CI tỷ lệ đảo chiều, CI và trung vị các nhóm G1/G2/G3 (R10), bảng thành phần thập niên/khoảng cách năm (T4_C1, C1d), chẩn đoán CI zero (T4_C4), đối chiếu helper v4 (479 lần lặp đầu khớp từng lần lặp; chưa chạy đủ 10.000 lần ở Task 4 và Task 5).

## Không chạy lại

Bootstrap toàn bộ; helper đủ 10.000 lần; hồi quy hoặc phân tích mới.
