
---

## 7. Dữ liệu số

### 7.1. Thống kê mô tả

{{include:numerical_statistics}}

*(Bảng đầy đủ hơn, gồm P99, outlier và các chỉ số log: `reports/numerical_statistics.csv`.)* `tmdb_id`, `person_id`, `tmdb_collection_id` là mã định danh nên không đưa vào thống kê. `theater_count` rỗng 100% nên không có thống kê.

**Finding:**
- **Biến tiền tệ lệch phải cực đoan:** skewness 3,15–6,04; kurtosis 14–56; Mean/Median từ 2,57× (domestic) đến **12,12× (international)**; P99/Median lên tới 171×. `international_gross` có median chỉ 3,8 triệu nhưng mean 46,1 triệu.
- **Điểm RT** gần như trải đều trên [0,100] với lệch trái nhẹ (critic −0,46; audience −0,25), kurtosis âm (−0,99; −0,90 → đỉnh phẳng hơn chuẩn); không có giá trị ngoài miền [0,100].
- **`vote_count` cực kỳ lệch** (skew 10,87; median 3, mean 252,6; 28,1% = 0 vote; top 1% phim chiếm 52,0% tổng vote, top 10% chiếm 95,5%).
- **`billing_order`** (cast): median 10, max 450 — hợp lệ như thứ hạng.

![ECDF các biến tiền](plots/numerical_distributions/num_01_ecdf_money.png)

*Hình 7.1 — ECDF (thang log10 chỉ để vẽ) của 5 biến tiền. Câu hỏi: dải giá trị trải rộng thế nào và phần đuôi trái nằm ở đâu?*

**Quan sát:** các biến trải ~9 bậc độ lớn (từ 1 USD tới ~3 tỷ USD). Mỗi biến có "chân" kéo dài về phía trái vạch 1.000 USD (225 giá trị ở budget, 91 ở international, 73 ở global). Median các biến nằm trong khoảng 10^6,6–10^7,4 USD. **Ý nghĩa:** phép đo trung bình/độ lệch chuẩn trên thang gốc không mô tả được "phim điển hình"; thang log cần cho trực quan hóa, nhưng đuôi trái (giá trị cực nhỏ) sẽ bị kéo giãn mạnh khi log.

![Mean/Median và skew](plots/numerical_distributions/num_02_mean_median_skew.png)

*Hình 7.2 — Trái: Mean/Median (và P99/Median). Phải: skewness trước và sau log10 (tính tạm).*

**Quan sát:** log10 đảo dấu độ lệch: skew gốc dương (3,15–6,04) thành **âm** (−0,64 đến −1,59). Tức là sau log, phân phối có **đuôi trái** (giá trị nhỏ) đáng kể thay vì đối xứng như một số nhận xét trước giả định. **Ý nghĩa:** log10 là phép biến đổi hữu ích để giảm ảnh hưởng đuôi phải, nhưng không "chuẩn hóa" hoàn toàn dữ liệu và làm nổi bật các giá trị < 1.000 USD.

![KDE log](plots/numerical_distributions/num_03_kde_log_money.png)

*Hình 7.3 — KDE trên log10 của 5 biến tiền.*

**Quan sát:** đỉnh chính nằm ở 10^6–10^8; `international_gross` có median thấp hơn (3,8 triệu) so với global (15,2 triệu) và domestic (24,9 triệu). **Hạn chế:** KDE làm mượt, không phát hiện được các giá trị lặp chính xác.

![Heaping điểm RT](plots/numerical_distributions/num_04_score_heaping.png)

*Hình 7.4 — Phân phối điểm theo từng điểm nguyên và mức dồn cụm.*

**Quan sát:** `critic_score` = 100 ở **729 phim (11,42%)** và = 0 ở 127 phim; 25,3% điểm critic là bội số của 10 (nếu đều chỉ ~10–11%). `audience_score`: 13,4% bội số của 10, chỉ 0,7% = 100. **Interpretation (giả thuyết):** điểm critic của phim ít review có độ phân giải thô (ví dụ 1 review → 0 hoặc 100); dữ liệu không có số review RT để kiểm chứng. **Ý nghĩa:** điểm biên có độ tin cậy thấp hơn.

![vote_count](plots/numerical_distributions/num_05_vote_count_concentration.png)

*Hình 7.5 — `vote_count`: phân phối log và độ tập trung tích lũy.*

**Quan sát:** 28,1% phim 0 vote; top 1% phim giữ 52% vote; top 5% giữ 89,4%. **Ý nghĩa:** `vote_count` là biến phân tầng tự nhiên cho mọi so sánh (§5.4).

### 7.2. Outlier: phân biệt giá trị hợp lệ và giá trị đáng nghi

{{include:iqr_outliers}}

*Quy tắc IQR trên thang gốc, chỉ ghi nhận số lượng (không loại). Điểm RT: 0 outlier.*

{{include:log_outliers}}

![IQR raw vs log](plots/outliers/out_03_iqr_outliers_raw_vs_log.png)

*Hình 7.6 — % phim bị gắn cờ outlier theo IQR trên thang gốc (phía cao) và trên log10 (cao/thấp).*

**Finding:** trên thang gốc, 8,4–16,1% giá trị bị gắn cờ outlier **phía cao**; trên thang log10 **không còn outlier phía cao nào** nhưng xuất hiện outlier **phía thấp** (290 budget; 134 global; 126 international; 21 domestic; 5 opening).

**Interpretation:**
- *Outlier cao* = bom tấn. Giá trị lớn nhất (`reports/top_values_check.csv`): global_gross tối đa 2.925.713.609 (Avengers: Endgame), international tối đa 2.247.392.194 (Ne Zha 2), budget tối đa 658.800.000. Đây là các phim thật nổi tiếng, **không phải lỗi nhập**. *Lưu ý:* ngân sách tối đa lớn hơn ~34% so với giá trị lớn thứ hai (489.900.000) → nên đối chiếu nguồn ngoài cho vài giá trị lớn nhất trước khi dùng; dữ liệu hiện có không đủ để xác minh.
- *Outlier thấp (< 1.000 USD)* mới là điểm đáng nghi: `production_budget` 225 giá trị (103 < 100; 24 < 10; giá trị nhỏ nhất = 1), `global_gross` 73 (47 < 100), `international_gross` 91, `opening_weekend_gross` 14, `domestic_gross` 12. Với phim chiếu rạp thương mại, các giá trị này khó thật.

![Giá trị nhỏ và số tròn](plots/outliers/out_01_low_values_and_rounding.png)

*Hình 7.7 — Trái: số giá trị < 1.000/100/10 USD theo biến. Giữa: budget < 1.000 USD vs global_gross. Phải: tỷ lệ giá trị là bội số của 1 triệu/100 nghìn.*

**Kiểm tra hai giả thuyết về giá trị nhỏ:**
- *Giả thuyết "sai đơn vị" (triệu USD ghi thành USD):* **không được ủng hộ** ở nhóm budget < 1.000 USD: trong 48 phim có cả global_gross, median global_gross chỉ **50 USD**; chỉ 4,2% có global_gross ≥ 1 triệu. Nếu budget ghi theo triệu thì gross phải lớn tương ứng.
- *Giả thuyết "placeholder/phim vô danh":* phù hợp hơn nhưng chưa chứng minh được: median `vote_count` của 225 phim budget < 1.000 chỉ là 1; chỉ 9 phim có ≥ 100 vote. Các phim thấp ngân sách có doanh thu cũng rất thấp (nhỏ, nghiệp dư, hoặc dữ liệu giữ chỗ).
- *Số tròn:* 52,0% giá trị `production_budget` là bội số của 1 triệu (72,2% bội số của 100 nghìn) so với 6,4% / 17,3% ở `global_gross` và ≤ 1,0% ở doanh thu chi tiết → **ngân sách là con số ước lượng/làm tròn**, doanh thu thì chính xác hơn.
- **Kết luận:** nhóm giá trị nhỏ là *dấu hiệu bất thường cần điều tra*, chưa đủ bằng chứng để quyết định xóa/sửa. Các giá trị lặp nhiều nhất (ví dụ `domestic_gross` = 509 xuất hiện 5 lần; `international_gross` = 291 xuất hiện 4 lần) cũng cần kiểm tra thủ công.

![Tỷ lệ doanh thu/ngân sách](plots/outliers/out_02_gross_budget_ratio.png)

*Hình 7.8 — log10(global_gross / production_budget) trên 2.844 phim có cả hai.*

**Quan sát:** median tỷ lệ = 3,17×; **467 phim (16,4%) có doanh thu < ngân sách** (có thể là phim lỗ hợp lệ); 43 phim có tỷ lệ > 100×; 10 phim < 0,001×. **Ý nghĩa:** hai đuôi cực đoan này phần lớn do các giá trị nhỏ bất thường; ROI sẽ bị chi phối bởi chúng nếu không điều tra trước.

![Điểm biên vs vote](plots/outliers/out_04_score_extremes_vs_votes.png)

*Hình 7.9 — Median `vote_count` theo khoảng điểm RT.*

**Quan sát:** phim có critic = 0 hoặc 100 có median vote = 1 so với 118 ở nhóm 1–99. **Ý nghĩa:** điểm ở biên đi cùng phim ít thông tin; nhưng `vote_count` là của TMDB, không phải số review RT, nên chỉ là bằng chứng gián tiếp.

---

## 8. Dữ liệu categorical, text và đa trị

{{include:categorical_statistics}}

### 8.1. Thể loại (`genre_ids`)

![Tần suất thể loại](plots/categorical/cat_01_genre_frequency.png)

*Hình 8.1 — Tần suất token của 19 `genre_id` (tên theo bảng TMDB chuẩn, **không có trong dataset**; cần bảng tra cứu chính thức khi chuẩn bị).*

**Quan sát:** 19 thể loại; Comedy chiếm 14,79% lượt, Drama 11,4%, Action 9,5% (top 10 = 76,65%). Mỗi ô có trung bình 2,08 thể loại (tối đa 10); 7.035 phim (17,64%) không có thể loại.

![Tổ hợp thể loại](plots/categorical/cat_05_genre_combinations.png)

*Hình 8.2 — Top 15 tổ hợp thể loại sau khi sắp lại thứ tự tạm thời.*

**Finding quan trọng:** có **3.833 chuỗi** `genre_ids` khác nhau nhưng chỉ **1.573 tập hợp** thể loại khác nhau; **38,4% ô không sắp theo thứ tự số**. Nghĩa là cùng một tổ hợp (ví dụ {35, 18}) có thể bị lưu thành nhiều chuỗi khác nhau → group-by trực tiếp trên chuỗi sẽ **chia nhỏ sai** nhóm. Thứ tự trong ô thể loại có vẻ không mang ý nghĩa (khác `lead_cast_ids_superset`, nơi thứ tự có thể là thứ hạng billing — 90,1% ô "không sắp xếp", cần xác nhận với nguồn).

### 8.2. Trường đa trị và độ tập trung

![Số token mỗi ô](plots/categorical/cat_02_multivalue_cells.png)

*Hình 8.3 — Số giá trị trong mỗi ô đa trị.*

![Độ tập trung](plots/categorical/cat_03_concentration.png)

*Hình 8.4 — Đường tập trung tích lũy của đạo diễn, hãng sản xuất, diễn viên chính.*

**Quan sát:** đạo diễn: 14.590 id, **6.911 id (47,4%) chỉ xuất hiện 1 lần**, id phổ biến nhất chỉ chiếm 0,27% lượt; hãng SX: 14.288 id, 7.072 xuất hiện 1 lần, tối đa 42 hãng/phim; diễn viên chính: 183.357 id, 113.425 xuất hiện 1 lần, tối đa 20 người/ô. **Ý nghĩa:** đuôi dài cực đoan → không thể one-hot đầy đủ; id hiếm không đủ mẫu để học thống kê; cần gom nhóm/đếm/tần suất. Chỉ có ID, **không có tên** → không đánh giá được tính nhất quán chính tả, trùng người khác id.

### 8.3. Nhóm `tmdb_collection_id`

![Collection](plots/categorical/cat_04_collection_sizes.png)

*Hình 8.5 — Kích thước nhóm `tmdb_collection_id`.*

**Quan sát:** 39.841 phim (99,92%) có giá trị; 9.728 nhóm; median 3 phim/nhóm; chỉ 10 nhóm 1 phim; nhóm lớn nhất 148 phim. Tỷ lệ phim thuộc một nhóm bất thường cao và kích thước nhóm nhiều phim. **Limitation:** không xác minh được trường này biểu diễn "nhượng quyền thật" hay một cách gom nhóm khác (cần hỏi nguồn); không suy diễn thêm.

### 8.4. `title` và `credits_raw`

![Credits](plots/categorical/cat_06_credits_roles.png)

*Hình 8.6 — Số dòng theo role; số cast và director mỗi phim.*

- `title`: 8,74% có ký tự phi-ASCII (tiếng Nhật, Hàn, v.v.); khoảng trắng đầu/cuối: 0; không dùng làm khóa.
- `credits_raw`: 598.612 dòng `cast`, 41.116 dòng `director`; median 12 dòng/phim, trung bình 16,65, tối đa 452. 3.467 phim có credits nhưng **không có đạo diễn**; 2.101 phim có credits nhưng không có diễn viên; tối đa 35 đạo diễn/phim.
- **Đối chiếu:** `movies_raw.director_ids` khớp 100% (34.963/34.963 phim, cùng tập hợp) với dòng `director` trong `credits_raw` → **thông tin dư thừa**. `lead_cast_ids_superset` (≤ 20 người) luôn không nhiều hơn số cast ở `credits_raw` (tương quan số lượng 0,71) → là tập con cắt tại 20.

---

## 9. Ngày tháng và xu hướng thời gian

![Số phim theo năm](plots/dates/date_01_films_per_year.png)

*Hình 9.1 — Số phim theo năm phát hành. Cột đỏ: các năm sau 2026.*

**Finding:** `release_date_ref` từ 1897-03-07 đến **2031-12-17**; 754 thiếu (1,89%); 0 lỗi định dạng. **200 phim có ngày sau 2026-10-22** (124 phim từ năm 2027). Trong 200 phim này có 19 phim có `production_budget` và 23 có `critic_score` nhưng 0 phim có `global_gross`. 6.400 phim (16,36% số phim có ngày) trước năm 1980. Năm 2025–2026 có 1.702 phim.

**Interpretation:** phim phát hành trong tương lai là *chưa phát hành*; ngân sách dự kiến có thể hợp lệ (kế hoạch) nhưng điểm RT cho phim chưa chiếu cần kiểm tra (có thể là ngày dự kiến sai hoặc điểm của phim khác bị khớp nhầm — **chưa thể xác định**).

![Dồn cụm 01-01](plots/dates/date_03_jan1_heaping_and_month.png)

*Hình 9.2 — Trái: % phim có ngày 01-01 theo năm (n ≥ 30). Phải: phân bố theo tháng.*

**Finding:** **2.447 phim (6,26%) có ngày đúng 01-01**, trong khi nếu đều chỉ ~0,27%; tập trung nhiều nhất ở thập niên 1990 (639 phim) và 2000 (576). Tháng 1 vì vậy bị thổi phồng trong phân bố tháng. **Interpretation (giả thuyết):** 01-01 có thể là ngày mặc định khi nguồn chỉ biết năm; không thể xác nhận từ dữ liệu. **Ý nghĩa:** phân tích theo tháng/mùa vụ cần xử lý 01-01 riêng; phân tích theo năm không bị ảnh hưởng.

![Độ phủ theo thập niên](plots/dates/date_02_coverage_by_decade.png)

*Hình 9.3 — Số phim và % có dữ liệu theo thập niên (tính lại).*

{{include:decade_coverage}}

**Finding:** độ phủ `production_budget` ≤ 8,7% trước 1980, rồi ~11–13% từ 1980 đến 2010s và **giảm xuống 9,8% ở 2020s**; `global_gross` tương tự (11,3% ở 2020s). Chỉ `critic_score` tăng đều (1,9% → 18,1%). Khác nhận định cũ, **không có bước tăng vọt sau 2000**.

![Xu hướng median](plots/dates/date_04_nominal_median_trend.png)

*Hình 9.4 — Median budget và global_gross theo năm (năm có ≥ 20 phim có dữ liệu; USD danh nghĩa).*

**Limitation:** giá trị danh nghĩa (chưa điều chỉnh lạm phát; cần chỉ số CPI ngoài dataset để điều chỉnh) và chỉ tính trên phim có dữ liệu (thiên lệch, §5.4). Xu hướng này **không đại diện cho toàn bộ thị trường**.

---

## 10. Quan hệ giữa các biến

{{include:correlations}}

*Pearson trên thang gốc, Spearman (hạng) và Pearson trên log10 của biến tiền/vote. Mỗi hàng dùng quan sát chung của hai biến (pairwise), nên n khác nhau.*

![Budget vs global gross](plots/correlations/cor_01_budget_vs_global_gross.png)

*Hình 10.1 — Hexbin budget vs global_gross (log–log), n = 2.844.*

**Finding:** Spearman 0,81; Pearson(log) 0,82. Quan hệ đồng biến mạnh trải qua nhiều bậc độ lớn. Đám nhỏ phía dưới-trái (giá trị < 1.000) tách biệt khỏi dải chính. **Kiểm tra độ ổn định:**

![Ổn định](plots/correlations/cor_06_stability_checks.png)

*Hình 10.2 — Trái: Spearman budget~global theo thời kỳ. Phải: độ nhạy theo cách chọn mẫu.*

Spearman theo thời kỳ: <1980: 0,61 (n=241); 1980–99: 0,72; 2000–09: 0,83; 2010–19: 0,87; 2020+: 0,83. Chỉ phim ≥ 100 vote: 0,77 (n=2.329); sau khi tạm bỏ giá trị < 1.000: 0,80 (n=2.787). **Interpretation:** mối quan hệ **bền vững** với cách chọn mẫu nhưng yếu hơn ở phim cũ (mẫu nhỏ, dữ liệu thưa). **Limitation:** đây là tương quan, không chứng minh nhân quả; cả hai biến cùng bị chi phối bởi quy mô và độ nổi tiếng (budget~vote_count Spearman 0,76; gross~vote_count 0,74).

![Họ biến doanh thu](plots/correlations/cor_02_gross_family_scatter.png)

*Hình 10.3 — Opening vs domestic; domestic vs international; international vs global.*

**Finding:** `opening_weekend_gross`~`domestic_gross` Spearman **0,94**, Pearson(log) 0,94 → cực mạnh; `international_gross`~`global_gross` Pearson **0,97** nhưng Spearman 0,85 và Pearson(log) 0,70 — chênh lớn giữa ba thước đo cho thấy hệ số 0,97 bị chi phối bởi vài phim rất lớn (leverage) và bởi quan hệ cơ học (global gần như = dom + intl) cùng các xung đột nguồn (§11.4). `domestic`~`international` Pearson 0,81 nhưng log chỉ 0,50.
**VIF** (log10, n=1.496 phim đủ 6 biến): domestic 7,30; opening 7,62; budget 2,07; critic 2,03; audience 1,98; international 1,65. → domestic và opening mang gần cùng thông tin (đa cộng tuyến), **là đặc tính dữ liệu chứ không phải lỗi**.

![Critic vs Audience](plots/correlations/cor_03_critic_vs_audience.png)

*Hình 10.4 — Critic vs Audience, n = 6.211.*

Pearson 0,72, Spearman 0,73: đồng thuận mạnh nhưng không hoàn toàn; hai điểm không thay thế nhau hoàn toàn.

![Điểm vs doanh thu](plots/correlations/cor_04_scores_vs_gross_binned.png)

*Hình 10.5 — log10(global_gross) theo khoảng điểm.*

**Finding:** `critic_score`~`global_gross` Spearman 0,09 (n=2.531); `audience_score`~`global_gross` 0,18 (n=3.243); `critic_score`~`production_budget` −0,05. Median global_gross theo bin critic: 0–20: 23,5 triệu; 21–40: 58,8 triệu; 41–60: 59,2 triệu; 61–80: 67,5 triệu; 81–100: 58,6 triệu → **không đơn điệu**. **Interpretation:** điểm đánh giá hầu như không tuyến tính/đơn điệu với doanh thu trong mẫu này. **Limitation:** n nhỏ (mẫu phim có cả hai), thiên lệch chọn mẫu; không loại trừ quan hệ phi tuyến theo thể loại.

![So sánh các thước đo](plots/correlations/cor_05_pearson_spearman_log.png)

*Hình 10.6 — So sánh Pearson, Spearman, Pearson(log10) theo cặp biến.*

![Ma trận Spearman](plots/correlations/cor_07_spearman_matrix_with_n.png)

*Hình 10.7 — Ma trận Spearman kèm n. Lưu ý n biến thiên từ 1.860 đến 11.351 giữa các ô; vote_count tương quan mạnh với mọi biến doanh thu (0,56–0,81) nhưng âm nhẹ với điểm critic (−0,18).*

---

## 11. Phân tích liên bảng (Cross-dataset)

### 11.1. Khóa và số lượng

![Dòng vs khóa](plots/cross_dataset/xd_01_rows_vs_unique_keys.png)

*Hình 11.1 — Số dòng so với số `film_key` duy nhất (thang log).*

Xem bảng `key_consistency` ở §6: không khóa thiếu, không khóa mồ côi; `credits_raw` 639.728 dòng cho 38.430 phim (trung bình 16,65 dòng/phim).

### 11.2. Hiện diện của phim trong các bảng

![UpSet membership](plots/cross_dataset/xd_03_upset_key_membership.png)

*Hình 11.2 — Phim hiện diện trong tổ hợp bảng nào.*

| Hiện diện | Số phim | % |
|---|---:|---:|
| cả 5 bảng | 29.287 | 73,46% |
| thiếu `box_office_detailed` | 9.143 | 22,93% |
| thiếu `box_office_detailed` và `credits_raw` | 1.201 | 3,01% |
| thiếu `credits_raw` (có detailed) | 240 | 0,60% |

*Hiện diện theo khóa ≠ có dữ liệu thực* (xem 11.3).

### 11.3. Độ phủ thông tin thực (non-null)

![Giao nhau thông tin](plots/cross_dataset/xd_02_informative_overlap_matrix.png)

*Hình 11.3 — Số phim chung giữa các tập "có giá trị thực" (màu = Jaccard).*

![UpSet thông tin](plots/cross_dataset/xd_08_upset_informative_sources.png)

*Hình 11.4 — Tổ hợp nguồn có dữ liệu thực.*

**Finding:** 23.740 phim (59,5%) chỉ có credits mà không có bất kỳ giá trị tài chính/điểm nào; **1.050 phim** không có thông tin thực ở cả 6 nguồn. Phim có budget∩global = 2.844; có thêm critic và audience = 2.154. Mức độ phủ thực mỏng hơn nhiều so với mức hiện diện khóa (73,5% hiện diện đủ 5 bảng).

### 11.4. `box_office_raw` so với `box_office_detailed`: bổ sung hay dư thừa?

![Raw vs detailed](plots/cross_dataset/xd_04_raw_vs_detailed_revenue.png)

*Hình 11.5 — Phân loại phim theo nguồn doanh thu có giá trị.*

| Tình huống | Số phim |
|---|---:|
| có cả `global_gross` và dom/intl/open | 3.839 |
| chỉ `global_gross` | 651 |
| chỉ dom/intl/open (global thiếu) | 2.782 |
| không có doanh thu ở cả hai | 32.599 |

**Kết luận:** hai bảng **không trùng lặp**: 2.782 phim chỉ có doanh thu ở bảng chi tiết (trong đó 3.996 phim có international nhưng không có domestic), 651 phim chỉ có global. Do đó **không được mặc định bỏ một bảng**.

![Nhất quán doanh thu](plots/cross_dataset/xd_05_revenue_consistency.png)

*Hình 11.6 — Trái: độ lệch (dom + intl) so với global. Phải: international vs global.*

| Kiểm tra | Kết quả |
|---|---|
| international > global (>1%) | 348 / 3.341 phim (10,4%) |
| domestic > global (>1%) | 51 / 2.344 |
| \|dom + intl − global\| > 1% | 464 / 1.846 (25,1%): 219 thấp hơn, 245 cao hơn global |
| dom + intl = global (độ lệch < 1e-9) | 886 / 1.846 |
| trong ±1% | 1.382 / 1.846 |
| opening > domestic | 10 / 2.384 |

**Interpretation:** ở đa số phim có đủ 3 biến, global ≈ dom + intl (886 phim khớp chính xác, median độ lệch ~1,4e-6) — gợi ý global được tính từ hai thành phần ở nguồn nhiều phim; nhưng ~25% phim lệch hơn 1%, và 348 phim có phần quốc tế lớn hơn tổng toàn cầu (vô lý về logic). Nguyên nhân (thời điểm thu thập khác nhau, phạm vi thị trường khác, lỗi) **chưa xác định được**. Opening > domestic ở 10 phim cũng vô lý.

### 11.5. Rủi ro tăng dòng khi merge

![Merge](plots/cross_dataset/xd_06_merge_row_explosion.png)

*Hình 11.7 — Số dòng sau các phép merge mô phỏng (trong bộ nhớ).*

- Left join `movies_raw` ⟕ `box_office_raw` ⟕ `box_office_detailed` ⟕ `rt_scores` giữ nguyên **39.871 dòng** (các khóa duy nhất).
- Left join thêm `credits_raw` nguyên bản → **641.169 dòng (16,08×)**; tổng `production_budget` bị nhân **57,64×** vì bom tấn có nhiều dòng credits (một phim có 452 dòng). Tương tự mọi phép tổng/trung bình.
- Chiều ngược lại: join inner với `box_office_detailed` làm mất 25,9% phim (10.344).

