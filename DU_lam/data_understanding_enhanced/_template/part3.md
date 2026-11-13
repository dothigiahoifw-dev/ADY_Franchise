
---

## 12. Phân tích 5 biểu đồ hiện có

Năm ảnh gốc được lưu nguyên vẹn tại `plots/existing/`. Với mỗi ảnh, các số liệu đã được **tính lại từ dataset** (không đọc số từ hình). Cấu trúc: (1) mục đích; (2) dữ liệu; (3) quan sát; (4) số liệu hỗ trợ; (5) ý nghĩa; (6) vấn đề chất lượng gợi ý; (7) chưa thể kết luận; (8) phân tích bổ sung; (9) liên hệ Data Preparation.

### 12.1. Hình 01 — Tỷ lệ missing theo cột và theo dataset

![Hình 01](plots/existing/01_missing_values.png)

1. **Mục đích:** nhìn nhanh cột nào thiếu và dataset nào thiếu nhiều nhất (thang màu 0% / >0–5% / 5–20% / 20–50% / >50%).
2. **Dữ liệu:** tất cả cột của 5 dataset; panel cuối là % ô thiếu cả bảng.
3. **Quan sát:** cụm đỏ (>50%) gồm `production_budget`, `global_gross`, 3 cột doanh thu chi tiết, 2 điểm RT; cam (20–50%) gồm `imdb_id`, `production_company_ids`, `rt_url`; mọi cột khóa và metadata truy vết đầy đủ.
4. **Số liệu hỗ trợ:** tính lại khớp: 89,49% / 88,74% / 91,11% / 79,72% / 91,93% / 83,99% / 71,53%; `rt_url` 49,46%. Ô thiếu toàn bảng: 52,55% / 29,28% / 14,79% / 11,19% / 1,07%.
5. **Ý nghĩa:** thiếu tập trung ở nhóm biến cốt lõi cho phân tích tài chính, khác với metadata gần đầy đủ — đây là giới hạn chính về mức đại diện của dữ liệu.
6. **Vấn đề gợi ý:** độ phủ thấp; nhưng hình **bỏ cột `theater_count`** (rỗng 100%) khỏi `box_office_detailed` nên con số 52,6% bảng chi tiết **không phải** tỷ lệ của toàn bảng (60,46% khi tính đủ 6 cột).
7. **Chưa kết luận được:** lý do thiếu (chưa thu thập vs không tồn tại), mức độ chồng lấn giữa các cột thiếu (biểu đồ chỉ cho tỷ lệ riêng lẻ), ý nghĩa khác nhau của "thiếu" ở `rt_scores`.
8. **Bổ sung:** pattern thiếu ở mức phim (Hình 5.2–5.4), thiếu theo `vote_count`/thập niên/thể loại (5.5, 5.6, 9.3), phân loại thiếu theo `rt_status` (5.7).
9. **Data Preparation:** không impute mặc định; tạo cờ presence; tách tập Catalog/Financial (S04, S14).

### 12.2. Hình 02 — Phân phối các biến chính

![Hình 02](plots/existing/02_histograms.png)

1. **Mục đích:** kiểm tra hình dạng phân phối của budget, global_gross, critic, audience ở thang gốc và thang log.
2. **Dữ liệu:** `production_budget` (n=4.192), `global_gross` (4.490), `critic_score` (6.383), `audience_score` (11.351).
3. **Quan sát:** hai biến tiền dồn sát 0 ở thang gốc, đuôi phải kéo tới 6,6×10^8 và 2,9×10^9; ở thang log tạo hình chuông lệch trái với một "chân" kéo tới 10^0; critic có đỉnh cao tại 100; audience trải rộng, nhiều cột nhọn.
4. **Số liệu hỗ trợ:** hình ghi median/mean đúng với tính lại: budget 5.425.000/26.198.471; global 15.200.000/98.591.610; critic 69/63; audience 61/59. **Các số này mâu thuẫn bảng trong báo cáo cũ** (5.000.000/24.161.424; 2.578.414/16.738.450; 67/61,6).
5. **Ý nghĩa:** mean không đại diện cho giá trị điển hình ở biến tiền (4,83×; 6,49×); thang log phù hợp để quan sát nhưng nhận định "gần đối xứng" của báo cáo cũ cần điều chỉnh vì skewness log là −1,54 và −1,59 (đuôi trái).
6. **Vấn đề gợi ý:** giá trị nhỏ (< 1.000 USD) ở chân trái; dồn cụm ở 0/100 của điểm critic (127 và 729 phim).
7. **Chưa kết luận được:** các giá trị nhỏ là lỗi hay thật; hình đã gộp bin nên không thấy giá trị lặp.
8. **Bổ sung:** ECDF, KDE (Hình 7.1, 7.3), heaping điểm (7.4), kiểm tra giá trị nhỏ và tỷ lệ gross/budget (7.7–7.8).
9. **Data Preparation:** quyết định cách xử lý < 1.000 USD trước khi log (S05–S06, S10); log10 tạo cột mới, không thay cột gốc.

### 12.3. Hình 03 — Boxplot các biến quan trọng

![Hình 03](plots/existing/03_boxplots.png)

1. **Mục đích:** so sánh phân tán và outlier của 5 biến tiền và 2 điểm RT.
2. **Dữ liệu:** như bảng IQR (§7.2).
3. **Quan sát:** tiền vẽ trên trục log10; hộp tập trung ở 10^6–10^8; **các chấm outlier nằm ở phía dưới** (giá trị nhỏ); điểm RT không có outlier.
4. **Số liệu hỗ trợ:** tiêu đề mỗi panel ghi % outlier **tính trên thang gốc** (13,1% / 8,4% / 16,1% / 13,5% / 8,9%) — các tỷ lệ này tính lại khớp và là outlier **phía cao**. Trên thang log, outlier phía thấp là 290 / 21 / 126 / 134 / 5 và phía cao bằng 0.
5. **Ý nghĩa:** cùng một biến nhưng hai thang đo cho hai nhóm outlier khác nhau: bom tấn (thang gốc) và giá trị cực nhỏ (thang log). Phải xử lý hai nhóm theo hai cách (giữ vs điều tra).
6. **Vấn đề gợi ý:** hình **dễ gây hiểu nhầm** vì tỷ lệ % ở tiêu đề (cao, thang gốc) không phải thứ nhìn thấy trên đồ thị (thấp, thang log).
7. **Chưa kết luận được:** nguồn gốc outlier thấp (xem §7.2); boxplot không chỉ ra giá trị lặp hay cụm giá trị.
8. **Bổ sung:** so sánh IQR raw/log (7.6), ECDF, kiểm tra đối chiếu với ngân sách (7.7–7.8).
9. **Data Preparation:** *không* loại outlier cao; gắn cờ outlier thấp và điều tra (S05–S06, S10).

### 12.4. Hình 04 — Correlation heatmap (Pearson và Spearman)

![Hình 04](plots/existing/04_correlation.png)

1. **Mục đích:** nhìn tổng thể quan hệ giữa 7 biến số (pairwise, tối thiểu 30 cặp).
2. **Dữ liệu:** budget, domestic, international, global, opening, critic, audience.
3. **Quan sát:** khối doanh thu/ngân sách tương quan cao (0,69–0,97); hai điểm RT tương quan 0,72–0,73 với nhau nhưng rất thấp với doanh thu.
4. **Số liệu hỗ trợ:** tính lại khớp mọi ô kiểm tra (budget~global 0,78/0,81; domestic~opening 0,92/0,94; critic~global 0,18/0,09).
5. **Ý nghĩa:** ngân sách và doanh thu đồng biến mạnh; đa cộng tuyến ở cụm doanh thu; điểm RT gần như độc lập với tiền.
6. **Vấn đề gợi ý:** `domestic~opening` (0,94) và các biến vốn là thành phần của nhau (global ≈ dom + intl) → tương quan "cơ học", không phải bằng chứng độc lập.
7. **Chưa kết luận được:** (i) **n mỗi ô rất khác nhau** (1.860–11.351) nhưng hình không ghi n; (ii) `international~global` Pearson 0,97 so với Spearman 0,85 và Pearson(log) 0,70 — chênh lớn do leverage của bom tấn và xung đột nguồn; (iii) không có kiểm tra log hay phân tầng; (iv) không suy ra nhân quả.
8. **Bổ sung:** ma trận Spearman kèm n (Hình 10.7), so sánh 3 thước đo (10.6), ổn định theo thời kỳ/mẫu (10.2), VIF.
9. **Data Preparation:** chọn một trong `domestic`/`opening` hoặc dùng chính quy hóa khi mô hình hóa; mô tả mẫu cho từng hệ số (S10, S14).

### 12.5. Hình 05 — Tích hợp và độ phủ dữ liệu

![Hình 05](plots/existing/05_integration_coverage.png)

1. **Mục đích:** bốn góc nhìn: hiện diện khóa, độ phủ theo vote_count, theo thập niên, số dòng credits/phim.
2. **Dữ liệu:** `film_key` của 5 bảng; `vote_count`; `release_date_ref`; `credits_raw`.
3. **Quan sát:** (trái-trên) 4 tổ hợp hiện diện; (phải-trên) độ phủ tăng mạnh theo vote_count; (trái-dưới) số phim tăng rất mạnh đến 2010s rồi giảm, độ phủ thấp (<20%) và giảm về 0 ở thập niên 2030; (phải-dưới) lệch phải, median 12, max 452.
4. **Số liệu hỗ trợ:** 29.287/9.143/1.201/240 khớp; độ phủ theo vote_count của hình **khớp tính lại** (ví dụ ≥1.000 vote: 91,0% budget; 97,0% audience) và **không khớp bảng trong báo cáo cũ**; max 452 khớp tính lại (báo cáo cũ ghi 451).
5. **Ý nghĩa:** phát hiện cốt lõi về thiên lệch lựa chọn nằm ở panel phải-trên; panel trái-dưới cho thấy độ phủ không "tăng vọt sau 2000".
6. **Vấn đề gợi ý:** thiên lệch lựa chọn; thiên lệch thời gian; nguy cơ nhân dòng khi join credits; thập niên "2030" gồm 2 phim ngày tương lai.
7. **Chưa kết luận được:** panel trái-trên chỉ nói khóa **hiện diện**, không nói có dữ liệu thực (23.740 phim chỉ có credits); histogram cắt ở 80 nên ẩn đuôi (max 452); không cho biết cơ chế thiếu.
8. **Bổ sung:** UpSet thông tin thực (11.4), giao nhau (11.3), mô phỏng merge (11.7), kiểm tra Jan-1 và ngày tương lai (9.1–9.2).
9. **Data Preparation:** aggregate credits trước join; kiểm soát số dòng; phân tầng theo vote_count/thập niên (S07, S12–S14).

---

## 13. Biểu đồ bổ sung và phát hiện mới

Đã tạo **41 biểu đồ mới** (script chạy 0 lỗi), lưu theo chủ đề trong `plots/`. Phần lớn được nhúng và diễn giải tại vị trí phù hợp (cột "Mục"). Mỗi biểu đồ trả lời một câu hỏi cụ thể mà 5 hình gốc chưa trả lời.

| Thư mục / Hình | Câu hỏi | Loại biểu đồ (lý do) | Phát hiện chính | Mục |
|---|---|---|---|---|
| missing_values/mv_01 | Cột nào thiếu nhiều nhất, trên mọi dataset? | Thanh ngang xếp hạng, màu theo dataset (so sánh trực tiếp) | 7 biến ≥71,5% thiếu | 5.1 |
| missing_values/mv_02 | Thiếu có theo khối không? | Heatmap nhị phân ở mức phim (thấy cấu trúc) | Thiếu theo cụm, cùng vắng | 5.2 |
| missing_values/mv_03 | Một phim có bao nhiêu biến? | Cột đếm (phân phối độ đầy đủ) | 62,18% phim không có biến nào; 3,72% đủ 7 | 5.2 |
| missing_values/mv_04 | Tổ hợp biến nào đi cùng nhau? | UpSet (giao nhau nhiều tập) | Chỉ 5,09% có đủ 5 nhóm biến | 5.2 |
| missing_values/mv_05 | "Thiếu điểm" nghĩa là gì? | Thanh chồng theo `rt_status` | 3 loại thiếu khác nghĩa | 5.5 |
| missing_values/mv_06 | Thiếu có liên quan độ nổi tiếng? | Đường + boxplot | 1,9% → 91,0%; median vote 324 vs 2 | 5.4 |
| missing_values/mv_07 | Thiếu có khác theo thể loại? | Thanh nhóm | Doc 3,8% vs Thriller 26,8% | 5.4 |
| numerical_distributions/num_01 | Dải giá trị và đuôi trái? | ECDF thang log | 9 bậc độ lớn | 7.1 |
| numerical_distributions/num_02 | Mean/Median và skew trước-sau log? | Thanh | Skew đổi dấu sau log | 7.1 |
| numerical_distributions/num_03 | Hình dạng log của 5 biến? | KDE chồng | Đỉnh 10^6–10^8, chân trái | 7.1 |
| numerical_distributions/num_04 | Điểm RT có dồn cụm? | Histogram 1 điểm/bin | critic=100: 11,42% | 7.1 |
| numerical_distributions/num_05 | Phim nổi tiếng chiếm bao nhiêu vote? | Histogram + tích lũy | top 1% = 52% vote | 7.1 |
| outliers/out_01 | Giá trị nhỏ là lỗi đơn vị hay placeholder? | Thanh + scatter log-log + số tròn | Không giống lỗi triệu USD | 7.2 |
| outliers/out_02 | Tỷ lệ gross/budget có cực đoan? | Histogram log-tỷ lệ | 467 phim < 1×; 43 > 100× | 7.2 |
| outliers/out_03 | Outlier raw vs log khác nhau thế nào? | Thanh nhóm | Cao (raw) ↔ thấp (log) | 7.2 |
| outliers/out_04 | Điểm biên có đi với ít vote? | Đường median theo bin | Median vote 1 vs 118 | 7.2 |
| categorical/cat_01 | Phân bố thể loại? | Thanh ngang top-N | Comedy 14,79%; top10 76,65% | 8.1 |
| categorical/cat_02 | Mỗi ô đa trị có bao nhiêu giá trị? | 4 histogram | tối đa 10/35/42/20 | 8.2 |
| categorical/cat_03 | Mức độ tập trung? | Đường tích lũy | 47,4% đạo diễn chỉ 1 lần | 8.2 |
| categorical/cat_04 | Kích thước nhóm collection? | Histogram log-log + top 10 | 9.728 nhóm; max 148 | 8.3 |
| categorical/cat_05 | Tổ hợp thể loại có nhất quán? | Thanh top-15 | 3.833 chuỗi vs 1.573 tập | 8.1 |
| categorical/cat_06 | Cấu trúc credits? | Thanh + histogram | median 12; max 452 | 8.4 |
| dates/date_01 | Phân bố năm + ngày tương lai? | Thanh theo năm | 200 phim sau 2026-10-22 | 9 |
| dates/date_02 | Độ phủ theo thập niên? | Thanh + đường | Không tăng vọt sau 2000 | 9 |
| dates/date_03 | Có ngày mặc định 01-01? | Đường + thanh tháng | 6,26% vs 0,27% | 9 |
| dates/date_04 | Xu hướng median theo năm? | Đường log (n ≥ 20/năm) | Danh nghĩa, thiên lệch mẫu | 9 |
| correlations/cor_01 | Budget–global có bền? | Hexbin log-log | ρ=0,81; đám giá trị nhỏ tách | 10 |
| correlations/cor_02 | Quan hệ trong họ doanh thu? | 3 scatter log-log | opening~domestic ρ=0,94 | 10 |
| correlations/cor_03 | Critic và audience đồng thuận? | Hexbin | r=0,72 | 10 |
| correlations/cor_04 | Điểm có tách doanh thu? | Boxplot theo bin | Không đơn điệu | 10 |
| correlations/cor_05 | Thước đo ảnh hưởng kết luận? | Thanh nhóm 3 thước đo | international~global 0,97/0,85/0,70 | 10 |
| correlations/cor_06 | Tương quan có ổn định? | Thanh theo thời kỳ/mẫu | 0,61 → 0,87 theo thời kỳ | 10 |
| correlations/cor_07 | n mỗi ô tương quan? | Heatmap kèm n | n từ 1.860 đến 11.351 | 10 |
| cross_dataset/xd_01 | Dòng vs khóa duy nhất? | Thanh log | Chỉ credits 1-N | 11 |
| cross_dataset/xd_02 | Giao nhau thông tin thực? | Heatmap Jaccard + số | Mỏng hơn hiện diện khóa | 11 |
| cross_dataset/xd_03 | Hiện diện khóa? | UpSet | 73,46% đủ 5 bảng | 11 |
| cross_dataset/xd_04 | Hai nguồn doanh thu dư thừa? | Thanh | Không: 2.782 chỉ có detailed | 11 |
| cross_dataset/xd_05 | Hai nguồn mâu thuẫn? | Histogram + scatter | 348, 464 phim | 11 |
| cross_dataset/xd_06 | Merge có nhân dòng? | Thanh mô phỏng | 641.169 dòng; 57,64× tổng | 11 |
| cross_dataset/xd_07 | Quan hệ bảng | Sơ đồ | 1-1 / 1-N | 3 |
| cross_dataset/xd_08 | Tổ hợp nguồn có dữ liệu thực | UpSet | 23.740 phim chỉ có credits | 11 |

*Không tạo thêm* biểu đồ trùng lặp: ví dụ không vẽ thêm bar chart missing theo bảng (đã có ở Hình 01), và không vẽ phân phối theo từng thể loại vì mẫu có dữ liệu quá nhỏ ở nhiều thể loại để so sánh đáng tin.

---

## 14. Tổng hợp vấn đề chất lượng dữ liệu

Phân loại **Trạng thái**: *Đã xác nhận* (số liệu trực tiếp); *Dấu hiệu — cần điều tra* (bất thường, chưa rõ nguyên nhân); *Rủi ro* (chỉ xác minh được khi thực hiện bước sau). **Mức ưu tiên** dựa trên (a) độ nghiêm trọng, (b) phạm vi ảnh hưởng, (c) vai trò trong pipeline (vấn đề chặn các bước sau = HIGH). Đặc điểm tự nhiên của dữ liệu (outlier bom tấn, đa cộng tuyến) **không** được liệt kê như lỗi.

### 14.1. Bảng tóm tắt

{{include:issues_summary}}

### 14.2. Bảng chi tiết

{{include:issues_full}}

*Bản CSV: `reports/data_quality_issues.csv`.*

**Đặc điểm KHÔNG coi là lỗi:** outlier cao (bom tấn); lệch phải của biến tiền; Mean ≫ Median; đa cộng tuyến (DQ-15 chỉ là cảnh báo cho giai đoạn mô hình); `billing_order` thiếu ở director; quan hệ 1-N của credits; title trùng giữa các phim khác nhau; `rt_scores` UNMATCHED.

---

## 15. Kết luận Data Understanding

**1. Chất lượng tổng thể.** Năm dataset có **cấu trúc tốt, nội dung thưa và thiên lệch**. Khóa `film_key` đạt yêu cầu (duy nhất, không mồ côi, định dạng đồng nhất, quan hệ 1-1 và 1-N rõ ràng); kiểu số đọc sạch; không có token nhiễu ở cột số. Ngược lại, các biến mang ý nghĩa phân tích (tiền, điểm RT) thiếu 71,5–91,9%, và phim có dữ liệu là mẫu có chọn lọc.

**2. Đặc điểm quan trọng nhất.** (a) Tập hợp phim là một "catalog" rộng: 28,1% phim không có vote nào, median vote chỉ 3, phần lớn phim chỉ có metadata; (b) một lõi nhỏ phim phổ biến (≈ 4,1% có ≥ 1.000 vote) có dữ liệu gần đầy đủ (≈ 81–97% độ phủ tùy biến); (c) biến tiền lệch phải cực đoan, dải trải 9 bậc độ lớn; (d) ngân sách là ước lượng làm tròn (52% bội số của 1 triệu), doanh thu chính xác hơn; (e) ngân sách và doanh thu đồng biến mạnh (ρ ≈ 0,81) và ổn định theo mẫu, còn điểm RT gần như không liên quan tuyến tính với doanh thu (ρ 0,09–0,18).

**3. Vấn đề nghiêm trọng nhất.** (i) Độ phủ tài chính thấp và thiên lệch theo độ nổi tiếng (DQ-01, DQ-02); (ii) giá trị tiền cực nhỏ chưa rõ bản chất (DQ-05); (iii) hai nguồn doanh thu bổ sung nhau nhưng mâu thuẫn (DQ-06); (iv) merge `credits_raw` nhân dòng 16,08× và nhân tổng 57,64× (DQ-07); (v) số liệu báo cáo cũ không đáng tin ở nhiều chỗ (DQ-19).

**4. Dataset/cột cần ưu tiên.** `movies_raw.production_budget`, `box_office_raw.global_gross`, 3 cột doanh thu của `box_office_detailed`, `credits_raw` (trùng và aggregate), `movies_raw.release_date_ref`, `rt_scores.rt_status`.

**5. Ảnh hưởng đến độ tin cậy phân tích doanh thu/ngân sách/điểm.** Mọi kết luận về ROI, quan hệ budget–gross hoặc điểm–doanh thu chỉ có hiệu lực cho tập 2.844 phim (7,13%) (hoặc 2.154 cho phân tích kèm 2 điểm), vốn nghiêng về phim phổ biến, USD danh nghĩa, ngân sách làm tròn và một số giá trị nghi ngờ; chưa đại diện cho toàn bộ catalog.

**6. Ảnh hưởng đến tích hợp.** Credits 1-N; hai nguồn doanh thu mâu thuẫn; trường đa trị lưu dưới dạng chuỗi không chuẩn thứ tự (38,4% genre); nguy cơ dùng `imdb_id` làm khóa phụ bị hổng (25,92% thiếu ở movies); `tmdb_collection_id` có ý nghĩa chưa xác định.

**7. Có thể xử lý bằng quy tắc kỹ thuật xác định.** Ép kiểu ngày; tách trường đa trị; chuẩn hóa thứ tự token genre; cờ presence (has_budget...); aggregate credits (số cast, số director); gắn cờ ngày 01-01/ngày sau thời điểm thu thập/giá trị < 1.000; kiểm tra rows_before == rows_after; loại cột hằng số khỏi tập đặc trưng.

**8. Cần kiểm tra nguồn hoặc quyết định nghiệp vụ.** Giá trị < 1.000 USD là gì; nguồn doanh thu chuẩn khi mâu thuẫn; quy tắc xử lý credits trùng (giữ billing_order nào); ngày 01-01 có phải mặc định; ý nghĩa `tmdb_collection_id`; có cần quy đổi theo lạm phát; `theater_count` thật sự không có dữ liệu?

**9. Chưa đủ bằng chứng để chọn phương pháp.** Cơ chế thiếu (MAR hay MNAR) nên chưa thể chọn phương pháp impute; nguyên nhân mâu thuẫn doanh thu; độ tin cậy điểm biên; xử lý 200 phim tương lai (giữ ngân sách, bỏ điểm?).

**10. Điều kiện trước khi chuyển sang Data Preparation.** (1) Xác nhận mục tiêu phân tích (xác định tập con cần dùng); (2) phê duyệt quy tắc nguồn doanh thu chuẩn; (3) có kết quả điều tra mẫu cho nhóm giá trị < 1.000; (4) chốt quy tắc dedupe credits; (5) có bảng tra cứu tên genre/(tùy chọn) nhân sự; (6) thống nhất cách báo cáo phân tầng theo `vote_count`; (7) snapshot (hash) 5 file gốc để bảo đảm tái lập.

**Thông điệp tổng kết:** dữ liệu *đủ để phân tích mô tả toàn catalog* và *đủ để khám phá ban đầu* quan hệ ngân sách–doanh thu trên lõi phim phổ biến, nhưng **chưa đủ để suy rộng kết luận tài chính cho toàn bộ 39.871 phim**.

