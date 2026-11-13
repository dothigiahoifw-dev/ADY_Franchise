# BÁO CÁO DATA UNDERSTANDING (PHIÊN BẢN NÂNG CẤP)
## Phân tích dữ liệu thị trường điện ảnh — đánh giá chất lượng và đề xuất pipeline Data Preparation

| | |
|---|---|
| **Giai đoạn** | Data Understanding / EDA (CRISP-DM) — **chỉ đọc, không chỉnh sửa dữ liệu gốc** |
| **Dữ liệu** | 5 file CSV: `movies_raw`, `box_office_raw`, `box_office_detailed`, `credits_raw`, `rt_scores` (khóa `film_key`) |
| **Thời điểm thu thập** | `retrieval_date` = 2026-10-22 (movies/box_office/credits), 2026-10-23 (rt_scores) |
| **Mã nguồn tái tạo** | `code/data_understanding_eda.py` (sinh toàn bộ bảng trong `reports/` và biểu đồ trong `plots/`) |
| **Quy ước số liệu** | Dấu phẩy ngăn cách hàng nghìn, dấu chấm là dấu thập phân. Mọi số liệu được tính lại từ 5 CSV; các bảng lớn được chèn trực tiếp từ `reports/md/*.md` |

> **Phạm vi:** báo cáo chỉ *phát hiện – giải thích – đề xuất*. Không có bước điền thiếu, xóa dòng/cột, loại trùng, sửa giá trị, loại outlier, encode hay merge tạo dataset cuối nào được thực hiện. Các phép `log10`, parse ngày, merge thử, tính tương quan chỉ chạy trên bản sao trong bộ nhớ. Các bảng/ biểu đồ sinh ra là sản phẩm EDA, không phải dataset đã xử lý.

---

## Mục lục
1. Executive Summary
2. Bối cảnh, mục tiêu và đánh giá báo cáo cũ
3. Tổng quan 5 dataset
4. Schema và kiểu dữ liệu
5. Phân tích missing values
6. Duplicate và tính duy nhất
7. Dữ liệu số
8. Dữ liệu categorical / text / đa trị
9. Ngày tháng và xu hướng thời gian
10. Quan hệ giữa các biến
11. Phân tích liên bảng (Cross-dataset)
12. Phân tích 5 biểu đồ hiện có
13. Biểu đồ bổ sung và phát hiện mới
14. Tổng hợp vấn đề chất lượng dữ liệu
15. Kết luận Data Understanding
16. Đề xuất Data Preparation
17. Pipeline Data Preparation chi tiết
18. Sơ đồ pipeline
19. Đầu ra mong đợi và tiêu chí xác nhận
20. Giới hạn và các quyết định cần xác minh

---

## 1. Executive Summary

**Bức tranh chung.** Năm bảng mô tả **39.871 bộ phim** (TMDB) với khóa `film_key` sạch về cấu trúc: duy nhất ở các bảng 1-1, **0 khóa mồ côi**, 100% khóa của mọi bảng phụ đều có trong `movies_raw`. Vấn đề nằm ở **nội dung**, không phải cấu trúc: dữ liệu tài chính và điểm đánh giá cực kỳ thưa và thiên lệch theo mức độ nổi tiếng của phim.

**Năm phát hiện quan trọng nhất (đã kiểm chứng bằng tính toán):**

1. **Độ phủ tài chính rất thấp.** `production_budget` thiếu 89,49%, `global_gross` 88,74%, `domestic_gross` 91,11%, `opening_weekend_gross` 91,93%. Chỉ **2.844 phim (7,13%)** có đồng thời budget và global_gross; **24.790 phim (62,18%)** không có giá trị nào trong 7 biến tiền/điểm. (§5)
2. **Missingness không ngẫu nhiên theo mức độ nổi tiếng.** Median `vote_count` của phim có budget là 324 so với 2 ở phim thiếu; độ phủ budget tăng từ 1,9% (0 vote) lên 91,0% (≥1.000 vote). Điều này **loại trừ MCAR** đối với biến quan sát được `vote_count`, nhưng dữ liệu hiện có **không đủ để phân biệt MAR với MNAR**. (§5.4)
3. **Hai nguồn doanh thu bổ sung chứ không dư thừa, nhưng mâu thuẫn ở một số phim.** 2.782 phim chỉ có doanh thu ở `box_office_detailed` (global thiếu), 651 phim chỉ có `global_gross`; đồng thời 348/3.341 phim có `international_gross` > `global_gross` và 464/1.846 phim có (dom+intl) lệch global >1%. (§11.4)
4. **Rủi ro nhân dòng khi merge.** Left join trực tiếp `movies_raw` với `credits_raw` tạo **641.169 dòng (16,08×)** và làm tổng `production_budget` bị nhân **57,64×**. Cần gộp credits về mức phim trước khi merge. (§11.5)
5. **Số liệu của báo cáo cũ có nhiều chỗ sai** (median/mean của budget, global_gross, critic_score; bảng độ phủ theo vote_count; số cột và % thiếu của `box_office_detailed`) và **bỏ sót** cột `theater_count` rỗng 100%. Phiên bản này thay thế các số đó bằng số tính lại. (§2.2)

**Kết luận về mức sẵn sàng.** *Sẵn sàng về liên kết khóa; chưa sẵn sàng để phân tích tài chính trên toàn catalog.* Cần: (i) chia tập Catalog / Financial; (ii) điều tra giá trị tiền < 1.000 USD, xung đột nguồn doanh thu, ngày 01-01 và ngày tương lai; (iii) gộp credits và tách trường đa trị trước khi tích hợp; (iv) ra quyết định nghiệp vụ về nguồn doanh thu chuẩn và cách xử lý thiếu. Pipeline 15 bước ở §17 chuyển các phát hiện này thành hành động có thứ tự, điều kiện và tiêu chí kiểm tra.

---

## 2. Bối cảnh, mục tiêu và đánh giá báo cáo cũ

### 2.1. Bối cảnh và mục tiêu
Dự án phân tích dữ liệu phim cần hiểu chất lượng dữ liệu trước khi chuẩn bị (theo slide *From Understanding to Preparation*: Data Understanding trả lời "dữ liệu thu thập có đại diện cho bài toán không?"; Data Preparation trả lời "dữ liệu được chuẩn bị bằng cách nào?"). Mục tiêu mô hình hóa **chưa được xác định trong tài liệu**, nên báo cáo không giả định biến mục tiêu hay bài toán kinh doanh; các đề xuất nêu rõ điều kiện áp dụng và quyết định cần phê duyệt.

### 2.2. Đối chiếu báo cáo cũ với dữ liệu thực tế

**Giữ lại (đã kiểm chứng):** tính toàn vẹn khóa; tỷ lệ missing các cột chính; 22.906 dòng rỗng ở `box_office_detailed`; 225 phim budget < 1.000 USD và 73 phim global_gross < 1.000 USD; tương quan Pearson/Spearman; VIF (7,30 và 7,62); 348 và 464 phim mâu thuẫn doanh thu; 641.169 dòng khi join thô; 127 phim `critic_score = 0` và 11,4% = 100; skewness của các biến tiền.

**Sai hoặc không khớp dữ liệu:**

{{include:old_report_discrepancies}}

**Ghi chú diễn giải các điểm lệch:**
- Median `global_gross` trong báo cáo cũ (2.578.414) thực ra bằng **Q1**, không phải median; median thật là 15.200.000. Tỷ lệ Mean/Median 6,49× và P99/Median 69,64× của báo cáo cũ lại đúng với số thật (98,59 triệu / 15,2 triệu), nên bảng cũ tự mâu thuẫn nội bộ.
- Bảng "% có dữ liệu theo nhóm vote_count" của báo cáo cũ **không khớp** cả dữ liệu lẫn biểu đồ gốc (Hình 05): ví dụ nhóm 100–999 vote có budget 37,1% (không phải 51,2%). Cũng thiếu `audience_score`.
- Nhận định cũ "độ phủ tăng vọt sau năm 2000" **không được dữ liệu ủng hộ**: độ phủ budget/global_gross ổn định ~10–14% từ thập niên 1980, giảm ở 2020s (§9).
- Báo cáo cũ ghi `box_office_detailed` có 5 cột, 52,55% ô trống; thực tế có **6 cột** (thêm `theater_count`, rỗng 100%) và **60,46%** ô trống. Hình 01 cũng bỏ cột này (không vẽ cột rỗng hoàn toàn).
- "Tối đa 451 người/phim": 451 là số diễn viên lớn nhất; số **dòng** credits lớn nhất của một phim là 452 (451 cast + ≥1 director).
- Chưa kiểm chứng được: nhận định "median vote = 9" cho phim điểm biên. Tính lại: median `vote_count` của phim có `critic_score` ∈ {0,100} là **1**, của phim điểm 1–99 là **118**.

**Phần còn sơ sài của báo cáo cũ (được phát triển trong phiên bản này):** chưa có thống kê toàn bộ cột (§4), chưa phân tích categorical/đa trị (§8), chưa có phân tích ngày (§9), chưa kiểm tra xung đột doanh thu theo logic nghiệp vụ và vai trò bổ sung của `box_office_detailed` (§11), chưa phân tách "thiếu" theo `rt_status` (§5.5), chưa có bảng vấn đề có ưu tiên và tiêu chí kiểm tra (§14), pipeline chỉ gồm sơ đồ chung (§17–18).

---

## 3. Tổng quan 5 dataset

{{include:dataset_overview}}

**Quan hệ giữa các bảng** (số liệu §11):

![Sơ đồ quan hệ giữa 5 bảng](plots/cross_dataset/xd_07_table_relationship_diagram.png)

*Hình 3.1 — Quan hệ 5 bảng qua `film_key`. `movies_raw` là bảng gốc (spine); `box_office_raw` và `rt_scores` phủ 100% phim; `box_office_detailed` phủ 74,06%; `credits_raw` phủ 96,39% và là quan hệ 1-N.*

Vai trò: `movies_raw` giữ metadata và ngân sách; `box_office_raw` chỉ có **một** loại doanh thu (`market_scope` luôn = `global`); `box_office_detailed` định danh thêm bằng `imdb_id` và bổ sung doanh thu nội địa/quốc tế/mở màn; `credits_raw` là bảng quan hệ người–phim; `rt_scores` bổ sung điểm đánh giá và trạng thái khớp RT.

**Nhận xét cấu trúc đã kiểm chứng:**
- `film_key` = `"FK" + tmdb_id` đệm số 0 đủ 8 chữ số, đúng 100% dòng của `movies_raw`; `movies_raw`, `box_office_raw`, `rt_scores` cùng thứ tự dòng (không cần dựa vào thứ tự — vẫn phải join theo khóa).
- `imdb_id` ở `box_office_detailed` khớp 29.527/29.527 với `movies_raw`; `imdb_id` của `movies_raw` thiếu 10.335 dòng (25,92%).
- Không có ký tự nhiễu kiểu `$`, `,`, `%`, `N/A` trong các cột số (đọc đúng kiểu số); mọi thiếu đều là `NaN` rỗng. *Giới hạn:* với cột text, chưa kiểm tra toàn bộ token lạ ngoài các mẫu đã nêu ở §8.

---

## 4. Schema và kiểu dữ liệu

Bảng đầy đủ **41 cột** (`reports/column_overview.csv`). Cột "Role (suy luận)" do script suy ra từ kiểu và nội dung, **không phải mô tả chính thức** của nguồn.

{{include:column_overview}}

**Điểm đáng chú ý về schema:**
- **10 cột hằng số/rỗng** (≤ 1 giá trị duy nhất): `source`, `retrieval_date` (ở 4 bảng), `market_scope`, và `theater_count` (0 giá trị). Chúng là metadata truy vết, không mang thông tin phân biệt phim.
- Ngày (`release_date_ref`, `retrieval_date`) đang là **text** (`str`), không phải datetime; tất cả 39.117 ngày không thiếu đều đúng định dạng `YYYY-MM-DD` (độ dài 10; parse lỗi 0).
- `release_month` là float chỉ vì có NaN; khớp 100% với tháng của `release_date_ref`.
- `tmdb_collection_id`, `billing_order`, `theater_count` là float do NaN — là mã/thứ hạng, không nên coi là biến liên tục.
- Các cờ `budget_missing_flag` (movies) và `missing_flag` (box_office_raw) **khớp 100%** với trạng thái null của `production_budget` / `global_gross` → dư thừa thông tin, không phải biến độc lập.
- Cột đa trị: `genre_ids`, `director_ids`, `lead_cast_ids_superset`, `production_company_ids` lưu nhiều ID trong một ô, ngăn cách bằng `|` (§8).

---

## 5. Phân tích missing values

### 5.1. Tỷ lệ thiếu theo cột và theo dataset

![Xếp hạng missing](plots/missing_values/mv_01_missing_ranking_all_columns.png)

*Hình 5.1 — Xếp hạng % missing của mọi cột có thiếu. Dữ liệu: cả 5 dataset. Biểu đồ dạng thanh ngang xếp hạng để so sánh trực tiếp giữa các dataset (khác Hình 01 gốc, vốn tách theo bảng).*

**Quan sát:** 7 biến tài chính/điểm đều thiếu ≥ 71,5%; các cột metadata thiếu 9–26% (`imdb_id` 25,92%, `production_company_ids` 20,95%, `genre_ids` 17,64%, `director_ids` 12,31%, `lead_cast_ids_superset` 8,88%); `release_date_ref`/`release_month` 1,89%; `tmdb_collection_id` 0,08%; `credits_raw.billing_order` 6,43%.

{{include:missing_values}}

**Tỷ lệ ô thiếu cả bảng:** `box_office_detailed` 60,46% (52,55% nếu loại cột rỗng `theater_count`), `rt_scores` 29,28%, `box_office_raw` 14,79%, `movies_raw` 11,19%, `credits_raw` 1,07%.

### 5.2. Pattern thiếu ở mức phim

![Heatmap missingness](plots/missing_values/mv_02_missingness_heatmap_films.png)

*Hình 5.2 — Missingness heatmap trên 2.500 phim lấy mẫu ngẫu nhiên (seed 42), xếp theo độ đầy đủ. Xanh = có dữ liệu.*

![Độ đầy đủ từng phim](plots/missing_values/mv_03_film_completeness.png)

*Hình 5.3 — Phân phối số biến có dữ liệu trên 7 biến (5 tiền + 2 điểm).*

**Quan sát:** 24.790 phim (62,18%) không có biến nào trong 7 biến; chỉ **1.482 phim (3,72%)** có đủ cả 7. Heatmap cho thấy thiếu **có cấu trúc khối**: các biến doanh thu cùng xuất hiện/cùng vắng theo cụm phim, thay vì rải đều; các khoảng trống của `genre_ids`, `production_company_ids`, `imdb_id` tập trung ở nửa dưới (phim ít thông tin tài chính), trong khi `release_date_ref` hầu như đầy đủ ở mọi mức.

![UpSet tổ hợp có dữ liệu](plots/missing_values/mv_04_upset_data_presence.png)

*Hình 5.4 — UpSet: tổ hợp biến cùng có dữ liệu (top 12/32).*

**Quan sát:** sau nhóm "không có gì" (24.790), các tổ hợp phổ biến nhất chỉ có `audience_score` (3.536), `critic+audience` (3.028), cả 5 nhóm biến (2.030), và chỉ `dom/intl/open` (1.685). Phim có đủ budget + global_gross + doanh thu chi tiết + 2 điểm RT chỉ 2.030 (5,09%).

**Ý nghĩa:** phân tích đa biến cần chọn tập con theo biến, và mỗi tập con có n rất khác nhau (2.844 cho budget∩global; 2.154 cho budget∩global∩critic∩audience).

### 5.3. Thiếu trong `box_office_detailed`: "dòng vỏ rỗng" và cột rỗng

| Mẫu (dom, intl, opening) | Số dòng |
|---|---:|
| không có giá trị nào | **22.906** (77,58% của 29.527 dòng) |
| chỉ international | 3.996 |
| đủ cả 3 | 1.860 |
| dom + opening (không intl) | 524 |
| dom + intl (không opening) | 132 |
| chỉ domestic | 109 |
| `theater_count` | 0/29.527 (rỗng 100%) |

Số phim thật sự có doanh thu chi tiết là **6.621**, không phải 29.527 dòng. Điều này là **giá trị chưa được ghi nhận** (không biết do chưa thu thập hay không tồn tại), không thể coi là 0.

### 5.4. Missingness và mức độ nổi tiếng (`vote_count`)

![Missingness vs popularity](plots/missing_values/mv_06_missingness_vs_popularity.png)

*Hình 5.5 — Trái: % phim có dữ liệu theo nhóm vote_count (tính lại; cột xám = tỷ trọng nhóm). Phải: phân phối log10(vote+1) của phim có vs thiếu dữ liệu.*

{{include:coverage_by_vote}}

{{include:missingness_vs_votes}}

**Finding:** độ phủ tăng đơn điệu mạnh theo `vote_count` (budget: 1,9% → 91,0%; global_gross: 0,7% → 91,2%; domestic: 0% → 85,3%). Median `vote_count`: phim có budget 324 vs thiếu 2; có domestic_gross 1.201 vs 2. Rank-biserial 0,35–0,93; Cramér V (nhóm vote × có/thiếu) 0,52–0,71.

**Interpretation:** dữ liệu tài chính **không thiếu ngẫu nhiên hoàn toàn** (không MCAR) đối với `vote_count`. Hai cách giải thích còn mở: (a) *MAR* — thiếu phụ thuộc vào biến quan sát được (độ nổi tiếng, năm, thể loại) và có thể điều chỉnh bằng cách điều kiện hóa các biến này; (b) *MNAR* — thiếu phụ thuộc vào chính giá trị doanh thu/ngân sách (ví dụ phim doanh thu thấp ít được ghi nhận). Dữ liệu hiện có **không cho phép phân biệt** hai khả năng.

**Limitation:** vote_count là số vote của TMDB, vừa là proxy độ phổ biến vừa có thể bị tác động bởi chính việc phim được thu thập nhiều thông tin; không thể kết luận quan hệ nhân quả. Nhóm 0 vote chiếm 28,1% phim.

**Hệ quả:** bất kỳ kết luận nào rút từ phim có dữ liệu (ví dụ "ngân sách giải thích doanh thu") chỉ áp dụng cho **phim tương đối phổ biến**, không suy rộng được cho toàn bộ 39.871 phim.

**Độ phủ theo thể loại** (cùng chiều với phát hiện trên: thể loại có nhiều phim phổ biến có độ phủ cao hơn):

![Độ phủ theo thể loại](plots/missing_values/mv_07_coverage_by_genre.png)

*Hình 5.6 — % phim có budget/global_gross/critic_score theo thể loại (tên theo bảng TMDB chuẩn, ngoài dataset). Thriller 26,8%, Adventure 24,2%, Sci-Fi 24,7% cao nhất; Documentary 3,8% và TV Movie 2,9% thấp nhất.*

### 5.5. Thiếu ở `rt_scores`: ba loại "thiếu" khác nhau

![rt_status](plots/missing_values/mv_05_rt_status_vs_scores.png)

*Hình 5.7 — `rt_status` × có điểm.*

| `rt_status` | Số phim | % | Ý nghĩa dữ liệu |
|---|---:|---:|---|
| UNMATCHED | 19.719 | 49,46% | không khớp được trang RT; `rt_url` trống; không có điểm nào |
| MATCHED | 11.521 | 28,90% | có trang RT: 6.211 có cả 2 điểm; 5.140 chỉ audience; 170 chỉ critic |
| MATCHED_NO_SCORES | 8.629 | 21,64% | có trang RT nhưng **không có điểm nào** |
| SEARCH_ONLY | 2 | 0,01% | `rt_url` trống; có `critic_score` (ca hiếm, cần xem lại) |

`critic_score` thiếu 33.488 = 19.719 + 8.629 + 5.140 (đúng khớp). Tức là **"thiếu điểm" gồm ít nhất 3 nghĩa khác nhau**: không tìm thấy phim trên RT, tìm thấy nhưng chưa có điểm, và có điểm audience nhưng không có điểm critic. Chỉ dữ liệu hiện có không cho biết lý do (ví dụ chưa đủ review hay lỗi thu thập).

### 5.6. Thiếu ở các cột metadata
`imdb_id` thiếu rất nhiều ở phim ít vote (66,2% ở nhóm 0 vote → 0,0% ở nhóm ≥1.000). `credits_raw.billing_order` thiếu 41.116 = **đúng bằng số dòng `director`** → thiếu *theo thiết kế* (không áp dụng), không phải lỗi. 1.441 phim (3,61%) không có dòng credits nào; median vote của nhóm này là 0.

### 5.7. Tác động và định hướng (không thực hiện ở giai đoạn này)
- *Giá trị không áp dụng* (billing_order của director): không impute.
- *Giá trị chưa ghi nhận* (budget, doanh thu, điểm): cần tạo cờ có/không có dữ liệu; impute chỉ cân nhắc sau khi quyết định mục tiêu và giả định cơ chế thiếu (§16, §17 S14).
- *Dòng vỏ rỗng / cột rỗng*: xử lý ở mức diễn giải (cờ `has_detail_values`), không xóa ở nguồn.
- Với tỷ lệ thiếu 80–92%, impute bằng median/mode **không được khuyến nghị mặc định**: sẽ tạo phân phối giả và làm yếu tương quan thật.

---

## 6. Duplicate và tính duy nhất

{{include:duplicate_report}}

{{include:key_consistency}}

**Finding & Interpretation:**
- **Không có dòng trùng toàn bộ** ở bất kỳ bảng nào; `film_key`, `tmdb_id`, `imdb_id` (non-null) duy nhất ở `movies_raw`; `film_key` duy nhất ở 4 bảng 1-1.
- **`credits_raw`:** 1.021 dòng dư có cùng (`film_key`, `person_id`, `role`), **toàn bộ là role `cast`** và khác nhau ở `billing_order` (một người được liệt kê hai lần với thứ tự billing khác nhau); 3 dòng trùng (`film_key`, `billing_order`) trong cast. 6.265 dòng dư theo (`film_key`, `person_id`) gồm cả trường hợp một người vừa đạo diễn vừa diễn xuất — **hợp lệ**, không phải trùng.
- **`title` trùng** ở 652 dòng (39.519 title khác nhau/39.871) vì có phim cùng tên khác nhau (ví dụ các tập đặc biệt có tên giống nhau, phiên bản làm lại). Chỉ **1 nhóm** trùng cả title lẫn `release_date_ref` → ứng viên trùng phim cần kiểm tra thủ công.
- **Tác động merge:** chỉ `credits_raw` làm tăng dòng khi join (§11.5).
- **Không xóa bản ghi nào.** Đề xuất xử lý ở S03 và S07.

