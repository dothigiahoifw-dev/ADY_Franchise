# ADY_PRJ — RQ1 TASK 2: Chốt mẫu, biến và thiết kế đánh giá

**Trạng thái tài liệu:** PHƯƠNG ÁN KHUYẾN NGHỊ TRIỂN KHAI — chưa phải quyết định đã được nhóm duyệt.
**Phạm vi đã làm:** kiểm tra dữ liệu, dựng mẫu/split/registry/kế hoạch; tái lập baseline v2 để xác nhận cách fit. **Không** huấn luyện E1–E8, không chọn biến bằng hiệu năng, không chấm test.
**Nhãn:** VERIFIED = tính lại bằng `verify_task2.py` trên file nhận được; REPORTED = từ tài liệu khác, chưa kiểm; ASSUMPTION; OPEN.

## 0. Tóm tắt thiết kế

| Hạng mục | Thiết kế |
|---|---|
| Mẫu chính | Toàn bộ **918** transition (562 franchise), không loại thêm dòng nào ngoài điều kiện `y_eligible` của `pairs_audit.csv` |
| Phân tầng báo cáo | `open_prev ≥ 1 triệu` (n=731) và `< 1 triệu` (n=187); chỉ để báo cáo |
| Dòng có cờ chất lượng opening | 10 dòng (dev 6, test 4): **đánh dấu, không loại**; chỉ dùng cho kiểm tra độ nhạy S1 |
| Split | Giữ `rq1_split_v2.csv` nguyên vẹn: dev 725 (fold 1–4), test 193 (fold 0) |
| Baseline | Giữ nguyên baseline v2 (đã tái lập: fit trên toàn bộ dòng train của các fold còn lại, cả hai tầng) |
| Thuật toán | Linear Regression (OLS) — không đổi |
| Cấu hình chính | E0–E4 (5 cấu hình) |
| Hồi cứu | E5–E7, chạy sau khi khóa mô hình chính; **bỏ E8** |
| Metric chính | MAE log gộp ngoài fold trên 725 dòng dev; quy tắc chọn ở mục 8 |

## 1. Đầu vào đã nhận và chưa nhận

Chi tiết hash/số dòng: `data/manifest_sources.csv`.

| File | Tình trạng |
|---|---|
| `pairs_audit.csv` (30.113 dòng × 48) | Đã nhận, dùng làm nguồn chính |
| `analysis_master_films.csv` (39.871 × 61) | Đã nhận (cấp phim) |
| `rq1_split_v2.csv`, `rq1_baseline_dev_preds_v2.csv` | Đã nhận |
| `analysis_master_transitions.csv`, `transitions_model_rq1.csv` | **Chưa nhận** |
| `rq1_feature_policy.csv`, `feature_registry_transitions.csv` | **Chưa nhận** |
| Báo cáo DP v3.3, README | **Chưa nhận** |

Hệ quả: tên cột trong master transitions và trạng thái policy chưa đối chiếu được. Các đặc trưng ứng viên được **tính lại** từ `pairs_audit.csv` + `analysis_master_films.csv` (cột nguồn ghi trong registry). Định nghĩa này có thể khác nhẹ cột cùng tên trong master transitions chưa nhận (ví dụ `cast_retention_top5` Task 1 báo thiếu 0,3%, bản tính lại thiếu 0%).

## 2. Mẫu

### 2.1 Kiểm tra khóa và grain [VERIFIED]
- `pairs_audit.csv`: 30.113 dòng cặp ứng viên; 25.943 dòng có `transition_id` (duy nhất); 4.170 dòng không hợp lệ không có ID.
- 918 dòng `y_eligible`: `transition_id = film_key_prev + "__" + film_key_curr`, không trùng; mỗi phim xuất hiện tối đa một lần ở vai trò N và một lần ở vai trò N−1 (không nhân bản dòng). Tập ID bằng đúng tập ID của `rq1_split_v2.csv`.
- Không join theo title. Join phim dùng `film_key`; opening N−1 và N trong `pairs_audit` khớp `analysis_master_films.csv` (918/918); ngày chiếu N khớp.

### 2.2 Điều kiện mẫu (theo thứ tự áp dụng)

| Bước | Điều kiện | Transition | Franchise | Loại |
|---|---|---:|---:|---:|
| S0 | Cặp ứng viên trong `pairs_audit` | 30.113 | 9.718 | — |
| S1 | `technically_valid` (cùng collection, kế tiếp, có ngày hợp lệ, không trùng ngày, chưa phát hành bị loại) | 25.943 | 8.731 | 4.170 |
| S2 | Có opening cả N−1 và N (`y_eligible`) | 918 | 562 | 25.025 |
| S3 | Có trong split v2 | 918 | 562 | 0 |

Lý do loại S1 (số dòng, một cặp có thể nhiều lý do): trùng ngày chiếu 2.239; collection có phim chưa có ngày 912; thiếu ngày + collection có phim chưa có ngày 713; phim chưa phát hành 176; còn lại là tổ hợp nhỏ. Lý do loại S2: thiếu opening cả hai 24.209; chỉ thiếu N 574; chỉ thiếu N−1 242. Toàn bộ danh sách: `data/exclusions.csv`.

### 2.3 Kiểm tra trên 918 dòng [VERIFIED]
Y = ln(open_curr) − ln(open_prev) (sai lệch tối đa 1,8×10⁻¹⁵); hai opening dương và hữu hạn; `chain_pos_curr − chain_pos_prev = 1` ở 918/918 (không nối qua phim trung gian); ngày chiếu N sau N−1 ở mọi dòng (gap nhỏ nhất 27 ngày); `gap_years` = số ngày/365,25 (sai lệch 7×10⁻¹⁵); `franchise_position_n` khớp xếp hạng độc lập theo ngày chiếu trong collection ở 918/918; `release_month_n`/`release_year_n` tính từ ngày chiếu N; không có dòng tied/undated/unreleased trong mẫu; `comparability_status = ASSUMED_NOT_VERIFIED` ở 918/918.

**Không có dòng nào bị loại thêm.** Mọi dòng đều có Y hợp lệ. Cờ pending (`ASSUMED_NOT_VERIFIED`, A1, A2) là giả định chưa xác minh, không phải bằng chứng dữ liệu sai.

### 2.4 Cờ chất lượng opening (đánh dấu, không loại)
`opening_low_warning_prev` 1 dòng, `opening_low_warning_curr` 5 dòng, `opening_inconsistent` 4 dòng → 10 dòng gộp (dev 6, test 4). ID dev: `FK00080280__FK00185341`, `FK00000256__FK00000255`, `FK00000255__FK00000258`, `FK00000258__FK00000259` (ba dòng chuỗi có open_prev = open_curr = 11.206, Y = 0), `FK00008982__FK00110552` (open_curr = 270 sau 5,03 triệu, Y = −9,83), `FK00454699__FK00823609` (576 → 57.501). Ý nghĩa của các cờ chưa xác minh; chỉ dùng cho S1.

### 2.5 Mẫu chính, tầng báo cáo, độ nhạy

| Nhóm | Dev | Test | Ghi chú |
|---|---:|---:|---|
| Toàn mẫu | 725 (449 franchise) | 193 (113 franchise) | 562 franchise tổng |
| `open_prev ≥ 1M` | 576 (342 fr.) | 155 (87 fr.) | Trùng 100% cờ `mau_chinh` |
| `open_prev < 1M` | 149 (120 fr.) | 38 (29 fr.) | |
| Dev: franchise có dòng ở cả hai tầng | 13 | | 342+120−13 = 449 |
| Dev: số transition/franchise | 1:297, 2:97, 3:26, 4:17, 5:4, 6–10: 8 | | Phụ thuộc trong franchise |

Bucket báo cáo thêm (dev): `<1M` 149; `1–10M` 151; `10–50M` 294; `≥50M` 131.

Dòng `open_curr < 1M` trong dev mẫu chính: 31 dòng — **giữ**, không loại. Độ nhạy (chỉ trên dev, không dùng để chọn cấu hình):
- **S1:** 6 dòng dev có cờ chất lượng bị bỏ khỏi **tập fit** của mọi fold (các dòng này vẫn được dự báo ngoài fold). Cả ba baseline cũng fit lại cùng cách. So sánh trên **cùng tập dòng validation**: (a) 719 dòng dev không có cờ, so run chính với run S1, ghép cặp theo `transition_id`; (b) 6 dòng có cờ báo riêng. Nhờ đó khác biệt chỉ đến từ tập fit, không đến từ việc đổi dòng đánh giá.
- **S2:** fit chỉ trên dòng `≥ 1M` của các fold còn lại; baseline cũng fit lại cùng cách; đánh giá trên **cùng 725 dòng dev** (cả hai tầng), dự báo ngoài fold, ghép cặp theo `transition_id`.

### 2.6 Khác biệt so với Task 1
Các con số mẫu/split khớp Task 1 (918; 725/193; 731 = 576+155; 4 dòng `opening_inconsistent`). Tên cột `franchise_position_n` trong Task 1 tương ứng `chain_pos_curr` trong `pairs_audit` (phân bố và giá trị khớp). Tác động đến split/baseline: **không có**.

### 2.7 Giới hạn quan trọng: chọn lọc theo sự có mặt của opening [VERIFIED]
Trong 25.943 transition hợp lệ chỉ **918 (3,5%)** có opening cả hai phim. Tỷ lệ theo thập niên (năm chiếu N): 1930–1970 gần 0%; 1980: 6,4%; 1990: 5,3%; 2000: 4,3%; 2010: 4,3%; 2020: 2,9%. Mẫu vì vậy là các franchise có ghi nhận opening trong nguồn, không đại diện cho mọi franchise. Mọi kết luận chỉ áp dụng cho quần thể này. Đây là giới hạn dữ liệu, không thể giải quyết trong Task 2.

## 3. Vai trò biến và quyết định

Bảng đầy đủ (26 dòng, kèm độ phủ, thời điểm, bằng chứng, rủi ro, xung đột policy): `feature_registry_rq1.csv`.

**Phân loại thời điểm:** 1 lịch sử trước N; 2 biết trước N về mặt khái niệm nhưng thiếu phiên bản lịch sử; 3 cập nhật sau mốc dự báo; 4 outcome của N.
**Giả định:** A1 (TMDB collection = franchise); A2 (opening so sánh được); A-R1a (ngày chiếu thực tế đại diện lịch phát hành biết tại mốc; chưa có dữ liệu để kiểm tra mức lệch); A-R1b (các phim trước N trong collection đã biết tại mốc).

| Biến | Phạm vi giả định | Missing (918 / dev) | Quyết định |
|---|---|---|---|
| `log_open_prev` = ln(open_prev) | A2 | 0% / 0% | Lõi |
| `gap_years` | A-R1a | 0% / 0% | Lõi |
| `franchise_position_n` (`chain_pos_curr`) | A1 + A-R1b | 0% / 0% | Lõi |
| `release_month_n` | A-R1a | 0% / 0% | Lõi |
| `release_year_n` | A-R1a | 0% / 0% | Lõi |
| `is_director_changed` | từng biến | 0% / 0% | Hồi cứu (E5) |
| `studio_changed` (công ty **sản xuất**, không phải nhà phát hành) | từng biến | 2,0% / 2,1% | Hồi cứu (E6) |
| `genre_jaccard` | từng biến | 0% / 0% | Hồi cứu (E7) |
| `production_budget_prev` | — | 11,2% / 11,3% | Không dùng cho RQ1 (policy `rq1_allowed = no` theo Task 1, chưa kiểm file); để RQ2; USD danh nghĩa |
| `production_budget_curr`, `budget_log_ratio` | — | 17,5% / 17,2% | Loại (loại 3) |
| `cast_retention_top5` | — | 0% (bản tính lại) | Không dùng cho RQ1; thứ tự billing chưa xác minh |
| `critic/audience_score_prev` | — | 7,6% / 8,4%; 3,7% / 4,0% | Không dùng; điểm scrape 2026-10-23, không phải trước N |
| `vote_count_*` | — | 0% | Loại |
| lifetime N−1 / N | — | chưa tính độ phủ | Không dùng (N: outcome; N−1: gap tối thiểu 27 ngày) |
| `theater_count` | — | 100% / 100% | Loại (không có dữ liệu) |
| `relationship_type_candidate` | — | — | Loại (UNVERIFIED_HEURISTIC theo Task 1) |

**Nguyên tắc áp dụng.** Ngày scrape muộn không bị dùng làm lý do loại: các biến hồi cứu được xét từng biến ở loại 2. Giả định lịch chiếu (A-R1a) không loại `franchise_position_n`, vốn dùng A1 và A-R1b. Snapshot 2026-10 (movies 2026-10-22, RT 2026-10-23; ngày chiếu N muộn nhất 2026-10-07) chưa cho biết giá trị tại mốc dự báo; mức cải thiện của nhóm hồi cứu **không** được diễn giải là giá trị dự báo trước opening đã chứng minh.

**Xung đột policy.** Task 1 báo director/studio là `RQ2_ONLY_PENDING` và budget `rq1_allowed = no`. File policy chưa nhận nên chưa xác nhận. Xử lý: budget không đưa vào RQ1; director/studio/genre chỉ chạy như phân tích hồi cứu tách biệt sau khi khóa mô hình chính, và không đưa vào kết luận chính. Nếu file policy cấm hẳn, bỏ E5–E7; mô hình chính không ảnh hưởng.

**Trùng thông tin.** Tương quan tuyệt đối cặp lớn nhất giữa 5 biến lõi (ở dạng biểu diễn dự kiến, trên dev) là 0,198 [VERIFIED]. Chỉ mô tả, không dùng để chọn biến.

## 4. Split [VERIFIED]

Split v2 đạt yêu cầu và mẫu không đổi → **giữ nguyên, không đổi seed**.
- 918 dòng, `transition_id` duy nhất; mỗi dòng đúng một vai trò/fold; dev = fold 1–4, test = fold 0.
- Mỗi franchise đúng một vai trò và một fold; **0** franchise chồng lấn giữa dev và test; các fold dev không chồng lấn.
- Fold dev: 178/185/176/186. Tầng `≥ 1M` theo fold: 143/145/132/156; `< 1M`: 35/40/44/30.
- Quan hệ giữa split và thời gian: năm chiếu N của test trải 1932–2026 và chồng lấn dev. Split theo franchise đo tổng quát hóa sang **franchise chưa thấy**, không chứng minh khả năng dự báo theo thời gian.

Bảng bàn giao: `data/split_assignment.csv` (transition_id, franchise_id, role, fold) và `data/sample_rq1_membership.csv` (thêm tầng, cờ chất lượng, film_key).

## 5. Baseline

Ba baseline: Y=0; median Y của train tương ứng; Linear Regression chỉ dùng `log_open_prev`.

**Cách fit của baseline v2 [VERIFIED].** Tái lập từ `pairs_audit` + split: nếu fit trên toàn bộ dòng dev của các fold còn lại (cả hai tầng), sai lệch dự báo tối đa 1,4×10⁻¹⁵ (hồi quy) và 0 (median); nếu fit chỉ trên tầng `≥ 1M`, sai lệch 1,86 (hồi quy) và 0,031 (median). Y=0 không phụ thuộc tập fit. Cột `ae_log` bằng |Y − pred| và Y khớp `pairs_audit`. Kết quả: baseline v2 **tương thích** với thiết kế (train toàn dev), nên **không phải chạy lại**. Khi nào phải chạy lại: đổi mẫu, split, tập fit hoặc target; riêng S2 phải fit lại cả ba baseline theo cách S2.

**Số tham chiếu (dev, 725 dòng) [VERIFIED]:**

| | Hồi quy log_open_prev | Median train | Y=0 |
|---|---:|---:|---:|
| MAE gộp | 0,8253 | 0,8124 | 0,8218 |
| Trung bình 4 fold | 0,8272 | 0,8148 | 0,8241 |
| Fold 1 / 2 / 3 / 4 | 0,9166 / 0,7655 / 0,9003 / 0,7264 | 0,9154 / 0,7476 / 0,9139 / 0,6821 | 0,9058 / 0,7565 / 0,9344 / 0,6998 |
| MAE trung bình theo franchise | 0,8844 | 0,8787 | 0,9049 |
| Tầng `≥ 1M` (576) | 0,6642 | 0,6534 | 0,6684 |
| Tầng `< 1M` (149) | 1,4480 | 1,4271 | 1,4150 |
| RMSE gộp | 1,2844 | 1,3023 | 1,3087 |

Hồi quy một biến thấp hơn median ở 1/4 fold và thấp hơn Y=0 ở 1/4 fold. Thứ hạng các baseline đổi theo cách đo (MAE gộp: median < Y=0 < hồi quy; theo franchise: median < hồi quy < Y=0; RMSE: hồi quy < median < Y=0). Đây là lý do báo nhiều cách đo. **E0 tái lập baseline hồi quy; E0 không được gọi là thắng baseline đơn giản.**

## 6. Cấu hình ứng viên

Thuật toán (OLS), baseline (3) và cấu hình feature (E*) được tách riêng. Bảng: `experiment_plan_rq1.csv`.

| Mã | Câu hỏi | Feature | Điều kiện | Phép so |
|---|---|---|---|---|
| E0 | Tái lập baseline hồi quy | log_open_prev | Điều kiện fit trùng v2 (đã xác minh) | Phải khớp dự báo baseline theo `transition_id` |
| E1 | Gap có bổ sung? | E0 + ln(gap_years) | A-R1a | E1 vs E0 |
| E2 | Vị trí phần có bổ sung? | E0 + ln(franchise_position_n) | A1, A-R1b | E2 vs E0 |
| E3 | Mùa/năm chiếu có bổ sung? | E0 + sin/cos(tháng) + (năm−2000)/10 | A-R1a | E3 vs E0 |
| E4 | Bộ lõi đầy đủ | 5 feature lõi (6 hệ số dốc) | cả bốn giả định | E4 vs E0 |
| E5/E6/E7 | Bổ sung hồi cứu: đổi đạo diễn / hãng sản xuất / thể loại | E4 + từng biến | Chỉ sau khi khóa mô hình chính; xem mục 3 | So với mô hình chính đã khóa |

E8 (gộp mọi nhóm hồi cứu) **bỏ**: không có câu hỏi riêng và tăng nguy cơ tìm kiếm cấu hình. Nếu một giả định lõi bị bác, quay về bộ nhỏ hơn: bác A-R1a → chỉ E0 (và E2 nếu A1, A-R1b được chấp nhận); không giữ biến bằng mọi giá. Cần lưu ý cả E0 cũng phụ thuộc A1 và A2.

Phân biệt phép so: E1–E4 so với E0 trả lời "biến nào bổ sung"; so với ba baseline trả lời "mô hình có hơn baseline không" — hai câu hỏi khác nhau (mục 8).

## 7. Kế hoạch tiền xử lý

Mọi bước học từ dữ liệu fit trong train của từng fold. Dữ liệu nguồn giữ nguyên; bản xử lý lưu riêng.

| Hạng mục | Quy tắc |
|---|---|
| Giá trị không hợp lệ | `assert`: open_prev > 0, gap_years > 0; không điền, không tự sửa. Dừng nếu vi phạm |
| log_open_prev | ln(open_prev) |
| gap_years | ln(gap_years); lý do: lệch phải (5% = 0,94; trung vị 3,01; 95% = 14,11; max 41,5). Cấu hình ban đầu, chưa chứng minh tối ưu |
| franchise_position_n | ln(vị trí); lý do: 409/725 dòng dev ở vị trí 2, đuôi tới 15. Giả định chênh lệch giảm dần giữa các phần; cấu hình ban đầu, chưa chứng minh tối ưu |
| release_month_n | sin(2πm/12), cos(2πm/12): 2 cột; chỉ bắt mùa dạng một chu kỳ |
| release_year_n | (năm−2000)/10, hằng số cố định, không học từ dữ liệu. Chỉ 7 dòng dev trước 1980 (86 trước 1990) nên hệ số chủ yếu dựa vào giai đoạn gần đây |
| Scaling | Không cần cho OLS; hệ số chuẩn hóa chỉ tính khi diễn giải |
| Missing | 5 feature lõi không thiếu. Biến hồi cứu: median/mode + cờ thiếu, fit trên train. Không điền 0 cho budget (budget không dùng trong RQ1) |
| Mã hóa biến phân loại | Biến nhị phân 0/1; không có biến phân loại nhiều mức trong bộ lõi |

**Điều chỉnh sau khi xem phần dư (Task 3, trên dev):** tối đa **một** thay đổi biểu diễn cho mỗi feature, chỉ dựa trên đồ thị phần dư theo feature (không dựa trên MAE), áp dụng thống nhất cho E1–E4, ghi nhật ký có thời điểm trước khi so MAE. Không thử hàng loạt biến thể.

## 8. Metrics, tổng hợp fold, quy tắc chọn

**Đơn vị đánh giá chính:** transition. Mỗi dòng dev được dự báo bởi mô hình fit trên 3 fold còn lại (ngoài fold theo franchise, gồm cả tầng `< 1M`).

**Metric chính:** MAE log gộp (micro) trên 725 dự báo ngoài fold. Vì các fold có kích thước khác nhau, MAE gộp là trung bình có trọng số theo số dòng của MAE từng fold; báo thêm trung bình đơn giản 4 fold.

**Bổ trợ:** RMSE; MAE từng fold; MAE trung bình theo franchise (trung bình của trung bình franchise, để nhìn tác động phụ thuộc: franchise dev có tới 10 transition); MAE theo tầng và bucket open_prev kèm n; chênh lệch ghép cặp theo `transition_id` (trung bình, trung vị, tỷ lệ transition cải thiện).

**Sai số điểm phần trăm:** đổi từng Y và Ŷ sang 100×(exp(·)−1) rồi mới tính |sai lệch|; báo **trung vị** và trung bình (trung bình bị cực trị chi phối vì exp(6,65) − 1 ≈ 77.000%). Không đổi MAE log trực tiếp.

**Quy tắc chọn (thực hành, không phải kiểm định thống kê), áp dụng trong E1–E4:**
1. Cổng S1: cấu hình đạt khi MAE gộp **thấp hơn E0** và thấp hơn E0 ở **≥ 3/4 fold**.
2. Trong nhóm đạt, chọn MAE gộp thấp nhất. Nếu cấu hình phức tạp hơn chỉ hơn cấu hình đơn giản hơn cũng đạt **< 0,005 log**, chọn cấu hình đơn giản (thứ tự độ phức tạp E1 = E2 < E3 < E4). Ngưỡng 0,005 khai báo trước, bằng khoảng 40% khoảng cách 0,013 giữa các baseline v2.
3. Không cấu hình nào đạt → giữ E0.
4. Chênh lệch theo tầng/fold chỉ để đọc đánh đổi, không dùng làm điều kiện chặn.

**Cổng kết luận so với baseline** (tách khỏi chọn cấu hình): cấu hình được chọn chỉ được nói "tốt hơn baseline X" khi MAE gộp thấp hơn X và thấp hơn X ở ≥ 3/4 fold; báo riêng từng baseline. Thắng E0 **không** có nghĩa thắng Y=0 hoặc median. Với số liệu v2 (hồi quy chưa thắng hai baseline đơn giản), kết quả "chưa vượt baseline đơn giản" là một khả năng hợp lệ và cần được báo cáo trung thực. Nhóm hồi cứu E5–E7 dùng cùng cổng nhưng báo riêng, không tham gia chọn mô hình chính.

## 9. Test và tái lập
- Y của toàn mẫu (gồm test) đã được mô tả ở Task 1 (hai cực trị −10,36 và 6,65 là dòng test); script của Task 2 tái lập số đó chỉ để đối chiếu. Không quyết định nào trong Task 2 dựa vào Y hay hiệu năng của test. Không tuyên bố test chưa từng được xem, cũng không tuyên bố test mất giá trị.
- Từ đây mọi quyết định phát triển dùng dev. Task 2 không chấm test.
- Khóa trước khi chấm test: `design_config_rq1.json` và `split_assignment.csv` (hash trong `manifest_outputs.csv`) cùng cấu hình cuối được chọn. Test: fit trên toàn bộ 725 dòng dev, chấm một lần trên 193 dòng; baseline cũng fit trên 725 dòng dev.
- Mọi thay đổi ghi nhật ký (thời điểm, lý do, file ảnh hưởng); đối chiếu bằng `transition_id`.

## 10. Giả định, giới hạn, kiểm tra đã thực hiện
- **Giả định chưa xác minh:** A1, A2 (nguồn thiếu thị trường, tiền tệ, cửa sổ, số rạp), A-R1a, A-R1b.
- **Chọn lọc theo có mặt opening:** mục 2.7.
- **Cực trị:** open_curr 270 và 742 sau opening N−1 hàng triệu (Y −9,83 và −10,36) là các điểm ảnh hưởng mạnh đến OLS; chưa biết là dự báo đúng hay lỗi so sánh opening. Giữ trong mẫu; S1 đo độ nhạy.
- **OLS và MAE:** OLS tối thiểu squared error trong khi chỉ số chính là MAE; không đổi thuật toán, báo thêm RMSE.
- **Phụ thuộc franchise:** số dòng 725 không phải số quan sát độc lập; báo số dòng và số franchise, cấu trúc transition/franchise, không diễn giải p-value như độc lập.
- **Kiểm tra đã thực hiện (VERIFIED):** toàn bộ mục 2–5 từ `verify_task2.py`; kết quả máy đọc `data/verified_numbers.json`.
- **Chưa thể làm:** đối chiếu master transitions, policy/registry, báo cáo DP; độ phủ lifetime. Tên cột trong master transitions chưa kiểm.

## 11. Trạng thái Task 2
**Đã hoàn thành:** kiểm kê và manifest; funnel và danh sách loại trừ; xác nhận mẫu 918 và split v2 (giữ nguyên); tái lập baseline v2 (tương thích, không cần chạy lại); registry feature; kế hoạch thử nghiệm; kế hoạch tiền xử lý; metric và quy tắc chọn; quy tắc test.
**Trở ngại còn lại:** (1) thiếu file policy/registry/master transitions → xung đột policy của nhóm hồi cứu chưa đóng; (2) A1, A2 không xác minh được từ file hiện có; (3) lý do ngưỡng 1 triệu không có tài liệu (không còn chặn vì chỉ phân tầng).
**Sẵn sàng cho task tiếp theo:** có thể bắt đầu ngay (xem README): mẫu, split, baseline, cấu hình và quy tắc chọn đã cố định; việc cần chờ chỉ là E5–E7.

## 12. Bổ sung bàn giao (đầu vào Task 3 và cổng kiểm tra)

**Đầu vào có sẵn trong gói, tra theo `transition_id`** (không phải truy cập file nguồn):
- `data/rq1_inputs_dev.csv` — 725 dòng dev: target `Y`, `open_prev`, `open_curr`, `log_open_prev`, 5 feature lõi, 3 biến hồi cứu, `fold`, `mau_chinh`, cờ chất lượng, ID phim, ngày chiếu.
- `data/baseline_v2_dev_preds_wide.csv` — dự báo ngoài fold của ba baseline v2 theo `transition_id` (`pred_Y0`, `pred_median_train`, `pred_reg_log_open_prev`), kèm `Y`, `fold`, `mau_chinh`. Đã đối chiếu từng giá trị với file dài `rq1_baseline_dev_preds_v2.csv` gốc.
- `data/rq1_inputs_test_LOCKED.csv` — 193 dòng test, **niêm phong**: Task 3 hiện tại không mở file này; chỉ kiểm hash byte.
- Nguồn gốc và hash các file nguồn (`pairs_audit.csv`, `analysis_master_films.csv`, `rq1_split_v2.csv`, `rq1_baseline_dev_preds_v2.csv`): `data/manifest_sources.csv`. Hash các file bàn giao: `manifest_outputs.csv`.

**Cổng kiểm tra (FAIL thì dừng):**
- `verify_task2.py`: chạy 25 kiểm tra quan trọng *trước khi* ghi bất kỳ output nào (ID duy nhất và khớp split; 918/725/193 và fold 178/185/176/186; dev = fold 1–4, test = fold 0; không franchise chồng lấn; Y và gap tái lập; cặp liên tiếp; `mau_chinh` = quy tắc 1 triệu; opening khớp master; feature lõi không thiếu; baseline đúng 3 model × 725 dòng dev, không dòng test; baseline tái lập sai lệch < 1e-9; đúng 6 dòng dev có cờ). Kết quả: `data/checks_source.csv` (25/25 PASS). Có kiểm tra nào FAIL: in FAIL, thoát mã 1, chỉ ghi `checks_source.csv`. Mình đã thử trên bản split bị sửa cố ý: 7 kiểm tra FAIL và dừng đúng.
- `build_design_files.py`: từ chối chạy nếu `checks_source.csv` còn FAIL.
- `task3_preflight.py`: chỉ đọc file dev, chạy 27 kiểm tra (hash theo manifest, tập dev, không dòng test, fold, Y, `log_open_prev`, `mau_chinh`, feature lõi, 6 dòng S1, baseline tái lập **chỉ từ file dev**, MAE gộp khớp 0,8253/0,8124/0,8218). Bản thử bị sửa một giá trị baseline: FAIL, thoát mã 1.
