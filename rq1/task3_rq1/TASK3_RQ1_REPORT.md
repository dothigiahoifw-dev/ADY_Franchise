# ADY_PRJ — RQ1 TASK 3: Chuẩn bị đầu vào, chạy thử và chọn cấu hình trên validation

**Phạm vi:** Bước 5 (chuẩn bị đầu vào cho phương pháp) và Bước 6 (chạy thử và chọn cấu hình). **Chỉ dùng 725 dòng dev**; file test chưa được mở hay chấm. Tất cả số liệu dưới đây là kết quả thực tế của code trong gói (`code/`), lưu ở `results/`.

**Phân biệt các loại kết quả (dùng xuyên suốt):**
- **[Đầu vào]** kiểm tra tính toàn vẹn và tái lập; **[Dev]** kết quả phát triển ngoài fold trên dev; **[Độ nhạy]** S1, S2; **[Hồi cứu]** E5–E7; **[Chờ test]** câu hỏi chỉ trả lời được khi chấm test ở task sau.

## 0. Kết quả chính

1. **[Đầu vào]** Gói Task 2 đúng phiên bản (hash khớp manifest); `task3_preflight.py` PASS (27/27); 8 kiểm tra bổ sung của Task 3 PASS.
2. **[Đầu vào]** E0 tái lập baseline hồi quy v2 theo `transition_id` với sai lệch lớn nhất 2,0×10⁻¹⁵ (dung sai 1e-9); median train và Y=0 khớp chính xác (sai lệch 0).
3. **[Dev]** Phần dư E4 không có dấu hiệu cụ thể theo tiêu chí khai báo trước → **0 thay đổi biểu diễn feature**.
4. **[Dev]** **Cấu hình được chọn theo quy tắc: E0** (`log_open_prev`). Không cấu hình E1–E4 nào đạt: cả bốn có MAE gộp cao hơn E0.
5. **[Dev]** **E0 không vượt baseline đơn giản.** MAE log gộp trên 725 dự báo ngoài fold: median train **0,8124**, Y=0 **0,8218**, E0 **0,8253**. E0 thấp hơn median và Y=0 ở 1/4 fold (fold 3). Đây là kết luận hợp lệ, không phải lỗi quy trình; không thêm thuật toán để tìm kết quả đẹp hơn.
6. **[Độ nhạy]** Cấu hình chọn giữ nguyên; S1 và S2 không đảo kết luận so với median, nhưng thứ hạng E0–Y0 mỏng manh (mục 7).
7. **[Hồi cứu]** E5–E7: **NOT RUN** (không có policy/registry trong gói).
8. **Khóa:** `locked_config_rq1.json` (E0, chưa chấm test).

## 1. Kiểm tra đầu vào [Đầu vào]

**Nhận diện gói.** Chỉ có một gói Task 2 (`task2_rq1.zip`, SHA-256 `23bd25207c7d…`); cấu trúc và nội dung khớp mô tả (báo cáo, cấu hình, registry, kế hoạch, preflight, `data/`). Preflight xác nhận hash 11 file khớp `manifest_outputs.csv`, gồm hash byte của `rq1_inputs_test_LOCKED.csv` (không mở nội dung).

| Mã | Kiểm tra | Kết quả |
|:---|:---------------------------|:---|
| C01 | `task3_preflight.py` | PASS (27 kiểm tra) |
| C02 | `transition_id` duy nhất | PASS (725) |
| C03 | Join một-một đầu vào dev ↔ split ↔ baseline wide, không nhân bản | PASS |
| C04 | Mỗi franchise nằm trong đúng một fold | PASS |
| C05 | `Y` hữu hạn; `open_prev`, `open_curr` > 0 | PASS |
| C06 | 5 feature lõi là số, hữu hạn, không thiếu | PASS |
| C07 | Miền: gap > 0; vị trí nguyên ≥ 2; tháng nguyên 1–12; năm 1900–2026 | PASS |
| C08 | Danh sách cột đưa vào model khai báo tường minh; không chứa ID, `open_curr`, `Y`, fold, cờ | PASS |

Chi tiết: `logs/checks_task3_input.csv`, `logs/preflight_output.txt`.

## 2. Bước 5 — Pipeline đầu vào

**Dữ liệu:** `inputs_dev/rq1_inputs_dev.csv` (725 dòng; bản sao đã đối chiếu hash). Dữ liệu nguồn không bị sửa; các cột biến đổi chỉ tồn tại trong bộ nhớ khi chạy.

| Nhóm | Cột sau biến đổi | Công thức | Số cột |
|:-------|:-------------------|:------------------------|:--:|
| `lop` | `log_open_prev` | ln(open_prev) | 1 |
| `gap` | `ln_gap_years` | ln(gap_years) | 1 |
| `pos` | `ln_franchise_position_n` | ln(franchise_position_n) | 1 |
| `season` | `sin_month`, `cos_month` | sin, cos của 2π × tháng / 12 | 2 |
| `year` | `year_c10` | (release_year_n − 2000) / 10 | 1 |

| Cấu hình | Nhóm | Số cột X | Số tham số (kèm hằng số) |
|:--:|:------------|:--:|:--:|
| E0 | lop | 1 | 2 |
| E1 | lop + gap | 2 | 3 |
| E2 | lop + pos | 2 | 3 |
| E3 | lop + season + year | 4 | 5 |
| E4 | cả năm nhóm | 6 | 7 |

**Missing, encoding, scaling.** Feature lõi không thiếu (đã kiểm tra); không scaling (OLS bất biến theo thang); tháng mã hóa tuần hoàn; hằng số `2000` và `10` cố định, không học từ dữ liệu. Giá trị không hợp lệ bị chặn bằng `assert` (xem C05–C07 và `build_X`). Không có bước nào học từ dữ liệu ngoài hệ số OLS và median, và chúng chỉ fit trên train của từng fold. **Không có xử lý hay biến mới ngoài thiết kế.**

**Đánh giá ngoài fold.** Với mỗi fold k ∈ {1,2,3,4}: fit OLS (`numpy.linalg.lstsq`, không phạt) trên ba fold còn lại, cả hai nhóm quy mô, rồi dự báo fold k. Không có yếu tố ngẫu nhiên.

## 3. Tái lập E0 và baseline [Đầu vào]

| Mô hình | Sai lệch tối đa so với dự báo tham chiếu theo `transition_id` | Dung sai | Kết quả |
|:--------------------|:------:|:----:|:---:|
| E0 (hồi quy `log_open_prev`) | 2,0×10⁻¹⁵ | 1e-9 | PASS |
| Median train | 0 | 1e-9 | PASS |
| Y=0 | 0 | 1e-9 | PASS |

Baseline tham chiếu v2 được dùng nguyên; `results/e0_reproduction.csv`.

## 4. Phần dư và biểu diễn feature [Dev]

Chạy E4 ban đầu ngoài fold, lấy phần dư và chia theo nhóm (ngũ phân vị cho `log_open_prev` và `gap_years`; vị trí 2/3/4–5/6+; quý của tháng chiếu; giai đoạn chiếu). **Tiêu chí khai báo trước trong code:** chỉ xem xét đổi biểu diễn khi có ít nhất hai nhóm liền kề cùng dấu, mỗi nhóm n ≥ 30, |phần dư trung bình| ≥ 0,15 và |z| > 2.

**Kết quả:** không feature nào đạt tiêu chí. Chỉ có một nhóm đơn lẻ (ngũ phân vị cao nhất của `log_open_prev`, n = 145, phần dư trung bình +0,157, z = 2,84) vượt ngưỡng, không có nhóm liền kề cùng dấu. Các nhóm khác có |phần dư trung bình| ≤ 0,196 và |z| ≤ 1,5. **Giữ nguyên biểu diễn ban đầu; 0 thay đổi** (`logs/representation_log.json`, `results/diag_residual_bins_E4.csv`).

**Lưu ý về diễn giải.** Việc xem phần dư vẫn là một bước phát triển mô hình trên dev. Bước này không dựa trên MAE và không đổi gì, nhưng kết quả dev dưới đây không nên được xem là quy trình lựa chọn hoàn toàn độc lập.

## 5. Bước 6 — Kết quả E0–E4 và baseline [Dev]

Dự báo ngoài fold cho 725 dòng; mọi cấu hình dùng cùng fold, cùng dòng validation.

| Mô hình | MAE gộp | RMSE | Fold 1 | Fold 2 | Fold 3 | Fold 4 | TB fold | Độ lệch chuẩn fold | MAE TB theo franchise |
|:----|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|
| Y=0 | 0,8218 | 1,3087 | 0,9058 | 0,7565 | 0,9344 | 0,6998 | 0,8241 | 0,1138 | 0,9049 |
| Median train | **0,8124** | 1,3023 | 0,9154 | 0,7476 | 0,9139 | 0,6821 | 0,8148 | 0,1184 | **0,8787** |
| E0 | 0,8253 | 1,2844 | 0,9166 | 0,7655 | 0,9003 | 0,7264 | 0,8272 | 0,0954 | 0,8844 |
| E1 (+gap) | 0,8324 | 1,2881 | 0,9118 | 0,8010 | 0,8973 | 0,7263 | 0,8341 | 0,0871 | 0,8890 |
| E2 (+vị trí) | 0,8254 | **1,2797** | 0,9069 | 0,7619 | 0,9033 | 0,7368 | 0,8272 | 0,0905 | 0,8794 |
| E3 (+tháng/năm) | 0,8285 | 1,2896 | 0,9146 | 0,7753 | 0,9056 | 0,7261 | 0,8304 | 0,0943 | 0,8888 |
| E4 (đủ 5) | 0,8311 | 1,2869 | 0,8999 | 0,7855 | 0,9131 | 0,7333 | 0,8329 | 0,0877 | 0,8874 |

*Độ lệch chuẩn fold là độ lệch chuẩn mẫu của bốn MAE fold.* MAE gộp là trung bình có trọng số theo số dòng của MAE từng fold (176–186 dòng mỗi fold).

**Sai số điểm phần trăm** (đổi từng Y và dự báo sang 100 × (exp(·) − 1) rồi mới tính; không có giá trị không hữu hạn). Trung vị sai số tuyệt đối: median train 40,6; E0 43,1; E2 43,3; Y=0 45,6; E3 44,3; E4 45,0; E1 45,5 điểm phần trăm. Trung bình sai số tuyệt đối đều khoảng 369–371 điểm phần trăm và bị cực trị chi phối (Y tối đa khoảng 6 tương ứng exp(Y) − 1 lên tới hàng chục nghìn phần trăm), nên không dùng làm chỉ số chính.

**Theo nhóm quy mô** (MAE log):

| Mô hình | `open_prev` ≥ 1M (n=576) | `open_prev` < 1M (n=149) |
|:----|:----:|:----:|
| Y=0 | 0,6684 | **1,4150** |
| Median train | **0,6534** | 1,4271 |
| E0 | 0,6642 | 1,4480 |
| E1 | 0,6724 | 1,4507 |
| E2 | 0,6661 | 1,4411 |
| E3 | 0,6630 | 1,4684 |
| E4 | 0,6687 | 1,4590 |

### 5.1 Quy tắc chọn

Áp dụng đúng quy tắc Task 2 (quy tắc thực hành, không phải kiểm định thống kê): cấu hình E1–E4 đạt khi MAE gộp thấp hơn E0 và thấp hơn E0 ở ít nhất 3/4 fold.

| Cấu hình | MAE gộp − MAE E0 | Số fold thấp hơn E0 | Đạt? |
|:--:|:----:|:--:|:--:|
| E1 | +0,0071 | 3/4 | Không (MAE gộp cao hơn) |
| E2 | +0,0001 | 2/4 | Không |
| E3 | +0,0032 | 2/4 | Không |
| E4 | +0,0058 | 1/4 | Không |

Không cấu hình nào đạt → **giữ E0** (`results/selection_table.csv`, `selection_steps.txt`). E1 thấp hơn E0 ở fold 1, 3, 4 nhưng kém hơn rõ ở fold 2 (0,8010 so với 0,7655), nên MAE gộp cao hơn. Không có trường hợp nào cần dùng bước ưu tiên cấu hình đơn giản (ngưỡng 0,005).

### 5.2 So với từng baseline

Cổng kết luận: chỉ nói "tốt hơn" khi MAE gộp thấp hơn **và** thấp hơn ở ≥ 3/4 fold.

| So sánh | MAE gộp (mô hình − tham chiếu) | Số fold mô hình thấp hơn | Đạt cổng |
|:------------------|:----:|:----:|:----:|
| E0 so với E0 | — | — | — |
| E0 so với Y=0 | +0,0035 | 1/4 | Không |
| E0 so với median train | +0,0129 | 1/4 | Không |
| Median so với Y=0 (tham khảo) | −0,0094 | 3/4 | Đạt |
| E1…E4 so với Y=0 | từ +0,0036 đến +0,0106 | 1–2/4 | Không |
| E1…E4 so với median | từ +0,0130 đến +0,0200 | 1–2/4 | Không |

Thắng E0 không đồng nghĩa thắng hai baseline còn lại, và ở đây không cấu hình nào thắng E0. Chi tiết ghép cặp theo `transition_id` (tỷ lệ transition được cải thiện, chênh lệch từng fold): `results/paired_comparisons.csv`; tỷ lệ transition có sai số thấp hơn so với E0 là khoảng 45–50% (E1 45,1%, E2 48,8%, E3 49,9%, E4 49,2%).

**Độ ổn định.** MAE từng fold biến động 0,68–0,93 (độ lệch chuẩn giữa fold 0,087–0,118), lớn hơn nhiều so với chênh lệch giữa các mô hình (cùng thang 0,01–0,02). Với RMSE (hàm mất mát mà OLS tối ưu), cả E0–E4 đều thấp hơn hai baseline đơn giản (E2: 1,2797 so với median 1,3023, thấp hơn 1,7%), nhưng RMSE không phải chỉ số chính và bị chi phối bởi cực trị.

**Hệ số (chỉ để mô tả, không nhân quả).** Hệ số `log_open_prev` của E0 theo fold từ −0,115 đến −0,071 (âm: opening phần trước càng cao thì Y dự báo càng thấp; phù hợp hiệu ứng hồi quy về trung bình vì `log_open_prev` có mặt trong Y). Trong E4, hệ số `ln_gap_years` +0,046 đến +0,170; `ln_franchise_position_n` +0,212 đến +0,332 (`results/coefficients_by_fold_main.csv`).

## 6. Độ nhạy S1 và S2 [Độ nhạy]

Cấu hình chọn (E0) giữ nguyên, không chọn lại. Baseline fit lại cùng cách. Vì cấu hình chọn là E0, các mô hình được so sánh là Y=0, median train và E0.

### S1 — bỏ 6 dòng có cờ chất lượng khỏi tập train của mỗi fold

| Trên 719 dòng không cờ | MAE run chính | MAE S1 | Chênh (chính − S1) | Dịch dự báo trung bình / tối đa |
|:----|:----:|:----:|:----:|:----:|
| Y=0 | 0,8066 | 0,8066 | 0,0000 | 0 / 0 |
| Median train | 0,7966 | 0,7968 | −0,0002 | 0,0044 / 0,0077 |
| E0 | 0,8077 | 0,8057 | +0,0020 | 0,0172 / 0,0726 |

Sáu dòng có cờ, báo riêng (MAE log): Y=0 2,6468; median 2,7041 → 2,7016; E0 2,9382 → 2,9076 (`results/s1_flagged_rows.csv`). Hệ số dốc E0 theo fold: run chính −0,082/−0,109/−0,071/−0,115; S1 −0,078/−0,105/−0,078/−0,108.

**Tách hai ảnh hưởng.** Ảnh hưởng lên hệ số và dự báo: nhỏ (dịch dự báo trung bình 0,017 với E0). Ảnh hưởng lên metric: E0 cải thiện 0,0020, vẫn **nhỏ hơn khoảng cách 0,0129 so với median**. Lưu ý thứ hạng E0 so với Y=0 đổi dấu: run chính E0 cao hơn Y=0 0,0011; S1 thấp hơn 0,0009. Chênh lệch này nằm trong dao động giữa fold nên không nên diễn giải thành bằng chứng E0 hơn Y=0.

### S2 — fit chỉ trên dòng `open_prev` ≥ 1 triệu thuộc fold train; đánh giá 725 dòng dev

| Phạm vi | Mô hình | MAE chính | MAE S2 | Chênh (chính − S2) |
|:----|:----|:----:|:----:|:----:|
| 725 dòng | Y=0 | 0,8218 | 0,8218 | 0 |
| 725 dòng | Median | 0,8124 | 0,8126 | −0,0002 |
| 725 dòng | E0 | 0,8253 | 0,8401 | −0,0148 |
| ≥ 1M (576) | Median | 0,6534 | 0,6529 | +0,0005 |
| ≥ 1M (576) | E0 | 0,6642 | 0,6591 | +0,0052 |
| < 1M (149) | Median | 1,4271 | 1,4298 | −0,0028 |
| < 1M (149) | E0 | 1,4480 | 1,5401 | −0,0921 |

Hệ số dốc của E0 đổi dấu (từ khoảng −0,07…−0,12 sang +0,015…+0,100), và dịch dự báo trung bình lớn (0,29 toàn mẫu; 0,88 ở nhóm < 1M). Nhóm < 1M bị dự báo ngoài miền huấn luyện nên sai số tăng; ở nhóm ≥ 1M, E0-S2 thấp hơn Y=0 (0,6591 so với 0,6684) nhưng vẫn cao hơn median (0,6529). S2 không thay đổi kết luận so với median.

Biểu đồ: `figures/fig5_sensitivity.png`. Không dòng nào được gọi là lỗi chỉ vì sai số lớn.

## 7. Phân tích lỗi [Dev]

Cấu hình chọn: E0. Mọi nhóm có n ≥ 30 (không nhóm nào bị cờ ít mẫu). Bảng đầy đủ: `results/error_by_group.csv`.

| Nhóm | n transition (franchise) | MAE E0 | MAE median | MAE Y=0 | Tỷ trọng tổng sai số E0 |
|:----|:----:|:----:|:----:|:----:|:----:|
| `open_prev` < 1M | 149 (120) | 1,448 | 1,427 | 1,415 | 36,1% |
| 1–10M | 151 (116) | 0,919 | 0,921 | 0,917 | 23,2% |
| 10–50M | 294 (201) | 0,602 | 0,604 | 0,632 | 29,6% |
| ≥ 50M | 131 (82) | 0,511 | 0,455 | 0,463 | 11,2% |
| gap < 1 năm | 65 (47) | 0,684 | 0,684 | 0,704 | 7,4% |
| gap 1–3 | 294 (217) | 0,711 | 0,665 | 0,671 | 34,9% |
| gap 3–6 | 217 (180) | 0,812 | 0,826 | 0,849 | 29,5% |
| gap 6–10 | 79 (72) | 0,904 | 0,907 | 0,916 | 11,9% |
| gap ≥ 10 | 70 (63) | 1,389 | 1,405 | 1,376 | 16,3% |
| Vị trí 2 | 409 (409) | 0,906 | 0,892 | 0,906 | 61,9% |
| Vị trí 3 | 161 (161) | 0,755 | 0,752 | 0,774 | 20,3% |
| Vị trí 4–5 | 95 (66) | 0,634 | 0,608 | 0,590 | 10,1% |
| Vị trí 6+ | 60 (24) | 0,767 | 0,753 | 0,742 | 7,7% |
| Chiếu < 1990 | 86 (56) | 0,665 | 0,669 | 0,659 | 9,6% |
| 1990s | 104 (83) | 0,901 | 0,935 | 0,936 | 15,7% |
| 2000s | 156 (119) | 0,872 | 0,845 | 0,848 | 22,7% |
| 2010s | 253 (191) | 0,781 | 0,756 | 0,776 | 33,0% |
| ≥ 2020 | 126 (107) | 0,902 | 0,882 | 0,897 | 19,0% |

**Nhận xét mô tả.** Nhóm `open_prev` < 1 triệu chiếm 20,6% số dòng nhưng 36,1% tổng sai số tuyệt đối; sai số cao hơn ở đó không chứng minh dữ liệu nhóm này nhiễu. Ở nhóm ≥ 50M, E0 kém hơn median 0,056. Sai số tăng theo gap rất dài (≥ 10 năm: 1,389).

**Kiểm tra theo ID** (`results/error_by_id.csv`, `error_contribution_summary.csv`; không loại dòng nào):

| Nhóm | n | Tỷ trọng dòng | Tỷ trọng tổng sai số E0 | MAE E0 |
|:------------------------|:--:|:---:|:---:|:---:|
| 6 dòng có cờ chất lượng | 6 | 0,8% | 2,9% | 2,938 |
| 31 dòng `open_prev` ≥ 1M nhưng `open_curr` < 1M | 31 | 4,3% | 15,2% | 2,926 |
| 32 dòng |Y| > 3 | 32 | 4,4% | 23,1% | 4,326 |
| 30 dòng sai số lớn nhất | 30 | 4,1% | 22,2% | 4,423 |
| Hợp của ba nhóm đầu (55 dòng) | 55 | 7,6% | 29,1% | 3,164 |

Dòng sai số lớn nhất là `FK00008982__FK00110552` (`open_curr` = 270 USD, Y ≈ −9,83; chiếm 1,6% tổng sai số). Các dòng này cần đối chiếu với định nghĩa nguồn (thị trường, cửa sổ, tính so sánh opening); **chưa kết luận sai dữ liệu hay giải thích kinh doanh**. Median và Y=0 cũng sai gần như bằng nhau ở các dòng này (MAE 2,87 và 3,03 ở nhóm 31 dòng), tức là mô hình không bù trừ được các điểm đó.

## 8. Nhóm hồi cứu E5–E7

| ID | Biến | Trạng thái | Lý do |
|:--|:----|:--|:----------------|
| E5 | E4 + `is_director_changed` | **NOT RUN** | Không có `rq1_feature_policy.csv` hay `feature_registry_transitions.csv` trong gói; Task 1 ghi `RQ2_ONLY_PENDING` (kế thừa, chưa kiểm) |
| E6 | E4 + `studio_changed` | **NOT RUN** | Như trên |
| E7 | E4 + `genre_jaccard` | **NOT RUN** | Như trên; chưa có policy cho genre |

Sự tồn tại cột trong dev không đồng nghĩa được phép dùng. Kết quả lõi không phụ thuộc E5–E7 (`results/retro_E5_E7_status.csv`).

## 9. Khóa phương án

`locked_config_rq1.json` (khóa lúc ghi trong file): cấu hình **E0**, OLS không phạt, feature `log_open_prev`, không thay đổi biểu diễn, quy tắc tiền xử lý, hash split/đầu vào/test, hash code và phiên bản thư viện (Python 3.12.3, numpy 2.5.4, pandas 3.0.6), lý do chọn, kết quả dev và giới hạn. Kế hoạch cho task sau: fit E0 và hai baseline trên toàn bộ 725 dòng dev, chấm một lần trên test; **không chấm E1–E4** để tránh chọn theo test. Hash của mọi file trong gói: `manifest_task3.csv` (kiểm bằng `python code/t3_manifest.py . --verify`).

## 10. Giới hạn và câu hỏi còn lại

**Giới hạn.**
1. A1 (TMDB collection là franchise) và A2 (opening so sánh được) chưa xác minh; chưa biết các cực trị là dự báo đúng hay lỗi so sánh.
2. Mẫu chỉ gồm franchise có opening được ghi nhận (3,5% transition hợp lệ).
3. Kết quả dev có chọn lọc nhẹ qua việc xem phần dư E4; không có hiệu chỉnh cho việc so sánh bốn cấu hình.
4. Các transition cùng franchise phụ thuộc nhau; số dòng không phải số quan sát độc lập.
5. MAE log nhạy với vài chục dòng cực trị (55 dòng chiếm 29,1% tổng sai số).
6. OLS tối thiểu bình phương, chỉ số chính là MAE.

**Câu hỏi cần test trả lời (task sau).** (a) Median train và Y=0 có tiếp tục không kém E0 theo MAE trên franchise chưa thấy? (b) Sai số E0 trên 193 dòng test có cùng cỡ với dev (≈ 0,8)? (c) Thứ hạng giữa E0 và Y=0, vốn mỏng manh, có lặp lại không?

**Trung thực về kết luận RQ1 ở giai đoạn dev.** Với bộ feature lõi hiện có và Linear Regression OLS, dự báo log-change ngoài fold trên franchise chưa thấy **chưa cho thấy cải thiện MAE so với baseline đơn giản** (median train). Chưa có cơ sở để kết luận nguyên nhân (feature thiếu, nhiễu đo opening, cực trị, cỡ mẫu hay bản chất của dữ liệu).
