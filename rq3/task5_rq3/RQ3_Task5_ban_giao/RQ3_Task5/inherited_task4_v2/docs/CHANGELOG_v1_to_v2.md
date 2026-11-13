# Nhật ký thay đổi Task 4: v1 → v2

Phạm vi: chỉ bốn điểm được yêu cầu. Mẫu chính (A1b), target Y, mọi ước lượng và CI giữ nguyên; không chạy lại bootstrap chính, không chạy helper đủ 10.000 lần. R10 chỉ được tính lại cho 4 nhóm nhỏ (cùng engine/seed) và cho ra số trùng v1.

| # | Điểm | Thay đổi | File ảnh hưởng | Ảnh hưởng số |
|---|---|---|---|---|
| 1 | Nhóm 11 franchise “phim 3 chưa phát hành” | Code v1 chỉ kiểm tra có cờ `unreleased_film` ở bất kỳ cặp nào của franchise. v2 đối chiếu đúng cặp vào vị trí 3 (xem kết quả ở dưới). Nhãn đổi thành “phim vị trí 3 bị cờ unreleased trong dữ liệu (đúng cặp 2→3)”, kèm giới hạn: ngày phát hành là lịch dự kiến trong dữ liệu và tình trạng thực tế hiện tại chưa xác minh. Giữ nhãn hạ cấp “nguyên nhân thiếu Y3 chưa xác minh; franchise có cờ unreleased” trong code cho trường hợp không đạt (kết quả: 0 franchise) | `code/t4_01_observability.py`, `results/R10*`, `results/R10c_G3_verification_11_franchises.csv`, `figures/T4_F1…`, `T4_interpretation_table.*`, báo cáo mục 3.5 | Không (n=11, +31,1%, CI −22,4; +159,3) |
| 2 | “Âm ở mọi mẫu/kịch bản” | Đổi thành “âm trong các mẫu cắt ngang A0/A1b/A1/A2 và kịch bản loại ngoại lệ đã xét (|Y|>3)”; nêu rõ PT2 trên tập cố định cho kết quả khác ở vị trí 2 (+37,1%/+50,7%) và 3 (+0,8%/+2,4%) | báo cáo mục 0, 2, 4.1, 5.1, 5.3; `T4_decision_table`, `T4_robustness_by_finding`, `T4_interpretation_table` | Không |
| 3 | Đảo chiều | Giữ 49/58 franchise và 89/176 cặp (50,6%). Mức 50% chỉ là tham chiếu giả định dấu độc lập; bỏ “ngang tham chiếu dấu độc lập”, “chủ yếu do chuỗi dài” và “49/58 phần lớn do chuỗi ≥3 transition”; không kết luận dấu thực sự độc lập | báo cáo mục 0, 2, 4.1, 5.1, 5.2; `T4_interpretation_table`; F4 | Không |
| 4 | Vị trí 4 và ngoại lệ | “Vị trí 4 ≈ 0” → “chưa có chiều rõ; CI rộng và chứa 0”. “Dịch chuyển không do ngoại lệ” → “dịch chuyển vẫn còn sau khi loại |Y|>3, nên không được giải thích hoàn toàn bởi nhóm này” | báo cáo mục 4.1, 4.3, 5.1, 5.2, 5.3; bảng diễn giải | Không |

## Kết quả kiểm tra nhóm 11 franchise (`R10c`)

Tiêu chí cho mỗi franchise (chỉ tính khi đủ cả năm điều kiện): cặp có `chain_pos_prev = 2` và `chain_pos_curr = 3`; phim 2 của cặp trùng phim 2 của transition vị trí 2 có Y; cặp `technically_valid = False` với `exclusion_reason = unreleased_film`; phim 3 có `is_unreleased_curr = True`; ngày phát hành của phim 3 trong dữ liệu sau `retrieval_date` của bảng films (2026-10-22 ở mọi dòng).

Kết quả: **11/11 đạt**; ngày phim 3 trong dữ liệu từ 2026-11-04 (The Last Temptation of Becky) đến 2028-10-05 (Gremlins 3). Cờ unreleased trong pairs_audit tách ở khoảng 2026-10-22/23 (dòng có ngày ≤ 2026-10-22 không bị cờ, dòng ≥ 2026-10-23 bị cờ). Không franchise nào dùng nhãn hạ cấp.

Chưa xác minh được: tình trạng phát hành thực tế hiện tại (dữ liệu chỉ có ngày dự kiến tại thời điểm thu thập); ngày 2026-11-04 của một phim đã qua so với ngày thu thập và có thể đã qua khi đọc báo cáo.

## Không thay đổi

Mẫu A1b (910/557), target, PT1/PT3/PT4, bootstrap (10.000 lần, seed 20260101), `inherited_step5_6/`, các bảng T4_C1…C9, R5_v2.
