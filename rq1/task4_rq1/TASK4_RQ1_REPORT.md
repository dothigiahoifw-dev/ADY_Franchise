# ADY_PRJ — RQ1 TASK 4: Chốt bước 6, đánh giá cuối trên test và diễn giải ban đầu

**Nguồn:** `task3_rq1.zip` (SHA-256 `a8b1394aee41…`) và gói đầu vào Task 2 `task2_rq1.zip` (SHA-256 `23bd25207c7d…`). Tệp `task2(1).zip` không có mặt trong phiên làm việc; mình dùng `task2_rq1.zip` hiện có, và hash của mọi file trong gói này (split, dev, baseline, test, design) **khớp** với hash ghi trong `locked_config_rq1.json` của Task 3.

**Nhãn:** **[Đã khóa]** quyết định từ Task 3; **[Đã kiểm tra]** tính lại trong Task 4; **[Test]** kết quả trên 193 dòng test; **[Bổ trợ]** phân tích thêm, không dùng để chọn lại.

## 0. Tóm tắt

1. **Bước 6 chốt:** 25/25 kiểm tra trước chấm PASS (1 ghi chú giới hạn). Bản ghi trước chấm `records/prescore_record.json` (SHA-256 `8299a245af2e…`) được ghi **trước khi mở nội dung file test**.
2. **Test (193 transition, 113 franchise), MAE log chính:** E0 **0,8801**; median train (dev) **0,8821**; Y=0 **0,8879**. Cả ba trong khoảng 0,88.
3. **ΔMAE = MAE_baseline − MAE_E0:** so với median **+0,0020**; so với Y=0 **+0,0078** (dương: E0 sai số thấp hơn). Cả hai rất nhỏ; khoảng bootstrap 95% theo franchise (bổ trợ) là [−0,0386; +0,0422] và [−0,0322; +0,0486], đều chứa 0.
4. **Khác chiều với dev.** Trên dev (ngoài fold) median dẫn đầu và E0 kém nhất (ΔMAE −0,0129 và −0,0035); trên test E0 nhỉnh hơn nhẹ. Thứ hạng đổi, và cỡ chênh lệch nằm trong dao động của mẫu.
5. **Kết luận ban đầu cho RQ1:** với `log_open_prev` và OLS, **chưa có bằng chứng đủ mạnh rằng E0 dự báo tốt hơn baseline đơn giản trên franchise chưa thấy**; cũng không có bằng chứng ngược lại. Sai số điển hình vẫn lớn: sai số điểm phần trăm trung vị khoảng 41 điểm phần trăm ở cả E0 và median.

## 1. Chốt bước 6 trước khi đọc test [Đã kiểm tra]

Script: `code/t4_run.py --stage prescore` (log: `logs/prescore_checks.csv`). Ở bước này file test chỉ được **tính hash byte**, không đọc nội dung.

| Mã | Kiểm tra | Kết quả |
|:--|:--------------------------------|:--:|
| P01 | `manifest_task3.csv`: mọi file khớp hash, không file thừa (47 file) | PASS |
| P02 | Hash thực tế = hash trong `locked_config`: split, đầu vào dev, baseline wide, **test (byte)**, `design_config` Task 2 | PASS ×5 |
| P03 | `manifest_outputs.csv` Task 2: mọi file khớp hash | PASS |
| P04 | Preflight Task 2 PASS | PASS (27/27) |
| P05 | Hash code Task 3 khớp `locked_config` | PASS |
| P06 | `t3_common.py` trong gói Task 4 = bản Task 3 đã khóa | PASS |
| P07 | Cấu hình khóa: E0, một feature `log_open_prev`, OLS | PASS |
| P08 | Không đổi biểu diễn (0 thay đổi, không trigger) | PASS |
| P09 | OOF: 725 dòng, ID duy nhất, trùng tập dev, fold 178/185/176/186, Y khớp | PASS |
| P10 | MAE log gộp tính lại từ OOF khớp bảng khóa: E0 0,8253; median 0,8124; Y=0 0,8218 | PASS |
| P11 | E1–E4 đều **không** đạt quy tắc (MAE gộp < E0 và thấp hơn ở ≥ 3/4 fold) | PASS |
| P12 | E0 tái lập từ đầu vào dev, bộ cột đúng `[log_open_prev]`, khớp OOF (< 1e-9) | PASS |
| P13 | Y=0 và median tái lập khớp OOF | PASS |
| P14 | Split: 725 dev / 193 test; không chồng lấn franchise (đọc từ bảng split) | PASS |
| P15 | Ghi nhận giới hạn Task 3 (bên dưới) | NOTE |

**Đối chiếu quy tắc chọn từ OOF [Đã kiểm tra].** MAE gộp − MAE E0 và số fold thấp hơn E0: E1 +0,0071 (3/4); E2 +0,0001 (2/4); E3 +0,0032 (2/4); E4 +0,0058 (1/4). Cả bốn đều có MAE gộp cao hơn E0 nên không đạt; E0 được giữ. Median và Y=0 vẫn là baseline bắt buộc.

**Giới hạn của Task 3 (P15).** Trong `t3_run.py`, nhánh đổi biểu diễn đọc `rep_decision.json` (`rep_over`) rồi vẫn gán `REP = {}`, nên nếu nhánh này được kích hoạt thì quyết định đổi biểu diễn sẽ không có hiệu lực. Nhánh này **không được kích hoạt** trong lần chạy đã khóa: không feature nào đạt tiêu chí (`diag_representation_trigger.csv`: tất cả False), `representation_log.json` ghi 0 thay đổi. Vì vậy cấu hình, ZIP và kết quả Task 3 **được giữ nguyên, không sửa**. Nếu sau này cần đổi biểu diễn, phải sửa lỗi này và mở phiên bản mới.

**Phạm vi “khóa”.** Khóa thuật toán (OLS có hệ số chặn), feature (`log_open_prev`), tiền xử lý và quy tắc fit. Hệ số E0 và median được **ước lượng lại trên toàn bộ 725 dòng dev** trước khi dự báo test.

## 2. Bước 7 — Chấm test

### 2.1 Tham số fit từ 725 dòng dev [Đã khóa quy tắc, ước lượng mới]

| Tham số | Giá trị |
|:--|:--:|
| E0: hệ số chặn | 1,33828 |
| E0: hệ số `log_open_prev` | −0,09432 |
| Median Y của dev (baseline median) | −0,16381 |
| Y=0 | 0 |

Hệ số dốc −0,094 nằm trong dải theo fold của Task 3 (−0,115 đến −0,071). `results/e0_dev_fit_coefficients.csv`, `dev_fit_parameters.json`.

### 2.2 Kiểm tra tập chấm (đọc file test sau khi bản ghi trước chấm được khóa)

| Mã | Kiểm tra | Kết quả |
|:--|:--------------------------------|:--:|
| T01 | 193 dòng; ID duy nhất; trùng tập test của split | PASS |
| T02 | `role` = test, fold = 0; franchise khớp split | PASS |
| T03 | Không chồng lấn franchise với dev (113 franchise test) | PASS |
| T04 | `open_prev`, `open_curr` > 0; Y = ln(open_curr) − ln(open_prev) (1e-12) | PASS |
| T05 | `log_open_prev` = ln(open_prev), hữu hạn, không thiếu | PASS |
| T06 | `mau_chinh` = (open_prev ≥ 1M); cột khớp dev | PASS |

Không dòng nào bị loại. Chỉ chấm ba phương án (E0, median, Y=0); không chạy E1–E7 trên test.

### 2.3 Kết quả [Test]

Sai số điểm phần trăm = |100(exp(Y) − 1) − 100(exp(Ŷ) − 1)|, đổi từng giá trị trước khi lấy chênh lệch (không có giá trị không hữu hạn).

| Phương án | MAE log | RMSE log | MAE log TB theo franchise | Sai số điểm % TB | Sai số điểm % trung vị |
|:----------|:----:|:----:|:----:|:----:|:----:|
| Y=0 | 0,8879 | 1,5026 | 0,9662 | 554,06 | 48,44 |
| Median train (dev) | 0,8821 | 1,4927 | 0,9486 | 553,49 | **40,63** |
| **E0** | **0,8801** | **1,4688** | **0,9233** | **553,09** | 40,66 |

Trung bình sai số điểm phần trăm bị vài cực trị chi phối (Y tối đa 6,6 ứng với hàng chục nghìn phần trăm), nên không dùng để so sánh; trung vị phản ánh sai số điển hình tốt hơn. Cỡ sai số: MAE log 0,88 tương ứng sai lệch điển hình gần gấp 2,4 lần (e^0,88) về tỷ lệ opening N so với N−1.

**Theo tầng `open_prev`:**

| Tầng | n (franchise) | Phương án | MAE log | RMSE log | MAE theo franchise | Sai số điểm % trung vị |
|:--|:--:|:--|:--:|:--:|:--:|:--:|
| ≥ 1 triệu | 155 (87) | Y=0 | 0,7540 | 1,3396 | 0,8514 | 41,16 |
| | | Median | **0,7395** | 1,3113 | 0,8165 | 36,63 |
| | | E0 | 0,7442 | 1,3131 | **0,8052** | **33,94** |
| < 1 triệu | 38 (29) | Y=0 | **1,4341** | 2,0367 | 1,5528 | 74,84 |
| | | Median | 1,4641 | 2,0743 | 1,5828 | **62,58** |
| | | E0 | 1,4347 | **1,9810** | **1,5201** | 120,47 |

Số franchise ở hai tầng cộng lại (116) lớn hơn 113 vì 3 franchise có dòng ở cả hai tầng. Nhóm < 1M chỉ có 38 dòng nên các số ở tầng này rất không ổn định.

### 2.4 So sánh ghép cặp E0 với từng baseline (ΔMAE = MAE_baseline − MAE_E0)

| Tham chiếu | Tầng | n | ΔMAE | Chiều | Khoảng bootstrap 95% [Bổ trợ] | % transition E0 thấp hơn | % franchise E0 thấp hơn |
|:--|:--|:--:|:--:|:--|:--:|:--:|:--:|
| Median | Tất cả | 193 | **+0,0020** | E0 thấp hơn | [−0,0386; +0,0422] | 50,3% | 59,3% |
| Median | ≥ 1M | 155 | −0,0047 | E0 cao hơn | [−0,0258; +0,0154] | 50,3% | 59,8% |
| Median | < 1M | 38 | +0,0295 | E0 thấp hơn | [−0,1537; +0,2198] | 50,0% | 51,7% |
| Y=0 | Tất cả | 193 | **+0,0078** | E0 thấp hơn | [−0,0322; +0,0486] | 51,3% | 61,1% |
| Y=0 | ≥ 1M | 155 | +0,0098 | E0 thấp hơn | [−0,0281; +0,0486] | 52,3% | 64,4% |
| Y=0 | < 1M | 38 | −0,0006 | E0 cao hơn | [−0,1361; +0,1400] | 47,4% | 51,7% |

*Bootstrap:* 10.000 lần lấy lại theo franchise có hoàn lại, ghép cặp, dự báo cố định (seed 20261107). Đây là phân tích bổ trợ và **không tính độ bất định của bước fit trên dev**; nó chỉ phản ánh biến động do thành phần franchise của tập test. Tỷ lệ lần lấy mẫu có ΔMAE > 0: 54,8% (so với median), 64,7% (so với Y=0).

Test là một tập giữ lại duy nhất nên **quy tắc 3/4 fold không được áp dụng lên test**; nó chỉ giải thích lựa chọn trên dev.

## 3. Độ vững và thành phần mẫu

### 3.1 S1 và S2 trên dev (kế thừa, đã tái lập)

Chạy lại chỉ trên dev; chênh lệch tối đa so với bảng Task 3 là 4,4×10⁻¹⁶ (`results/s1_s2_reproduction_check.csv`). **Không chạy S1/S2 trên test** và không dùng chúng để chọn lại cấu hình.

| Phép thử (dev) | Phạm vi | Y=0 | Median | E0 chính | E0 biến thể |
|:--|:--|:--:|:--:|:--:|:--:|
| S1: bỏ 6 dòng cờ khỏi tập fit | 719 dòng không cờ | 0,8066 | 0,7966 → 0,7968 | 0,8077 | 0,8057 |
| | 6 dòng có cờ | 2,6468 | 2,7041 → 2,7016 | 2,9382 | 2,9076 |
| S2: chỉ fit trên ≥ 1M | 725 dòng | 0,8218 | 0,8124 → 0,8126 | 0,8253 | 0,8401 |
| | ≥ 1M (576) | 0,6684 | 0,6534 → 0,6529 | 0,6642 | 0,6591 |
| | < 1M (149) | 1,4150 | 1,4271 → 1,4298 | 1,4480 | 1,5401 |

Trên dev, S1 làm E0 tốt hơn 0,0020, nhỏ hơn khoảng cách 0,0129 đến median; S2 làm E0 xấu hơn ở toàn mẫu và nhóm < 1M (dự báo ngoài miền huấn luyện). Cả hai không đảo kết luận "median dẫn đầu trên dev". Không thể chạy S1/S2 tương ứng trên test mà không tạo thêm lần thử trên test, nên khả năng chịu đựng của kết quả test đối với các điều kiện này **chưa được đánh giá**.

### 3.2 Dev so với test

| Chỉ tiêu | Dev | Test |
|:--|:--:|:--:|
| Transition (franchise) | 725 (449) | 193 (113) |
| `open_prev` ≥ 1M / < 1M | 576 / 149 | 155 / 38 |
| Nhóm opening: < 1M, 1–10M, 10–50M, ≥ 50M | 149, 151, 294, 131 | 38, 47, 76, 32 |
| Giai đoạn: < 1990, 1990s, 2000s, 2010s, ≥ 2020 | 86, 104, 156, 253, 126 | 22, 32, 37, 71, 31 |
| Vị trí 2 / 3 / 4–5 / 6+ | 409 / 161 / 95 / 60 | 106 / 46 / 33 / 8 |
| Gap < 1, 1–3, 3–6, 6–10, ≥ 10 năm | 65, 294, 217, 79, 70 | 17, 77, 57, 19, 23 |
| Dòng có cờ chất lượng | 6 (0,8%) | 4 (2,1%) |
| `open_prev` ≥ 1M nhưng `open_curr` < 1M | 31 (4,3%) | 11 (5,7%) |
| Dòng \|Y\| > 3 | 32 (4,4%) | 12 (6,2%) |
| Y: trung vị / độ lệch chuẩn | −0,164 / 1,302 | −0,083 / 1,497 |
| Y: phân vị 5% / 95% | −1,84 / 1,65 | −2,32 / 1,59 |
| Tỷ lệ Y < 0 | 56,7% | 56,5% |
| Năm chiếu N: nhỏ nhất, trung vị | 1959, 2010 | 1932, 2011 |

Cơ cấu opening, giai đoạn và gap khá tương đồng. Khác biệt đáng chú ý: test có đuôi Y dài hơn (độ lệch chuẩn 1,497 so với 1,302; nhiều dòng \|Y\| > 3 và dòng có cờ hơn theo tỷ lệ) và chỉ 8 dòng ở vị trí 6+ (so với 60 ở dev). Mọi MAE trên test đều **cao hơn** MAE dev ngoài fold 0,055–0,070 (`results/dev_vs_test_mae.csv`); hai giao thức khác nhau (dev: ngoài fold bốn lần; test: fit trên 725 dòng, giữ lại 193), nên không so trực tiếp hai con số như cùng một thước đo. Không suy ra nguyên nhân khi chưa có bằng chứng.

### 3.3 Chiều của ΔMAE: dev và test

| Phạm vi | Tham chiếu | ΔMAE dev (ngoài fold) | ΔMAE test | Cùng chiều? |
|:--|:--|:--:|:--:|:--:|
| Tất cả | Median | −0,0129 | +0,0020 | Không |
| Tất cả | Y=0 | −0,0035 | +0,0078 | Không |
| ≥ 1M | Median | −0,0108 | −0,0047 | Có (E0 kém hơn) |
| ≥ 1M | Y=0 | +0,0041 | +0,0098 | Có (E0 tốt hơn) |
| < 1M | Median | −0,0209 | +0,0295 | Không |
| < 1M | Y=0 | −0,0330 | −0,0006 | Có (E0 kém hơn, rất nhỏ ở test) |

Ở nhóm ≥ 1M (n lớn hơn), kết quả test cùng chiều với dev ở cả hai baseline. Chiều đảo ở toàn mẫu và nhóm < 1M phần lớn nằm trong khoảng bất định (nhóm < 1M chỉ 38 dòng).

### 3.4 Các transition ảnh hưởng lớn [Test]

| Nhóm | n | % số dòng | % tổng sai số tuyệt đối E0 |
|:--|:--:|:--:|:--:|
| 4 dòng có cờ chất lượng | 4 | 2,1% | 9,9% |
| 12 dòng \|Y\| > 3 | 12 | 6,2% | 31,8% |
| 11 dòng `open_prev` ≥ 1M nhưng `open_curr` < 1M | 11 | 5,7% | 23,3% |
| 15 dòng sai số lớn nhất | 15 | 7,8% | 36,4% |

Dòng sai số lớn nhất là `FK00010065__FK00203835` (`open_prev` ≈ 23,5 triệu, `open_curr` = 742, Y ≈ −10,36, có cờ chất lượng; chiếm 5,9% tổng sai số E0; sai số log 10,10 với E0, 10,20 với median, 10,36 với Y=0). Danh sách: `results/test_top_errors.csv`. Đây là **quan sát sai số lớn, không phải lỗi dữ liệu đã xác minh**; cần đối chiếu định nghĩa nguồn (thị trường, cửa sổ, tính so sánh opening). Tất cả dòng vẫn nằm trong bảng điểm chính. Chênh lệch ΔMAE chỉ +0,0020 nhỏ hơn nhiều so với mức một vài dòng cực trị có thể gây ra, nên chiều của ΔMAE toàn mẫu rất nhạy với tập dòng này.

## 4. Diễn giải ban đầu cho RQ1

**E0 sai bao nhiêu trên 193 transition test?** MAE log 0,8801 (RMSE log 1,4688). Về điểm phần trăm, sai số tuyệt đối trung vị khoảng 41 điểm phần trăm; trung bình 553 điểm phần trăm bị cực trị chi phối. Sai số lớn hơn nhiều ở nhóm opening N−1 dưới 1 triệu (MAE 1,43, n = 38) so với nhóm từ 1 triệu (0,74, n = 155).

**So với median train và Y=0?** E0 thấp hơn median 0,0020 và thấp hơn Y=0 0,0078 theo MAE log; theo RMSE log E0 thấp hơn cả hai (1,4688 so với 1,4927 và 1,5026); theo MAE trung bình theo franchise E0 thấp hơn (0,9233 so với 0,9486 và 0,9662). Tuy nhiên chênh lệch MAE chính rất nhỏ, khoảng bootstrap chứa 0, và ở nhóm ≥ 1M E0 cao hơn median 0,0047. Sai số điểm phần trăm trung vị của E0 (40,66) và median (40,63) gần như bằng nhau. **Không đủ cơ sở để nói E0 vượt baseline.**

**Cùng chiều hay khác chiều với dev?** Khác chiều ở MAE gộp: dev có median dẫn đầu, E0 cuối; test có E0 nhỉnh hơn. Ở nhóm ≥ 1M, hai tập cùng chiều. Cỡ các chênh lệch (≤ 0,03) nhỏ hơn dao động giữa các fold trên dev (độ lệch chuẩn khoảng 0,1) và độ rộng khoảng bootstrap trên test (±0,04).

**Khi xem S1/S2 và các tầng?** Trên dev, S1 và S2 không đổi kết luận về median; S1/S2 chưa được chạy trên test. Theo tầng, kết quả trên test không nhất quán giữa hai baseline (ví dụ nhóm < 1M: E0 hơn median 0,0295 nhưng ngang Y=0), và nhóm < 1M quá nhỏ để kết luận.

**Câu có thể đưa vào báo cáo nhóm.** *"Trên franchise chưa thấy, mô hình hồi quy tuyến tính chỉ dùng log opening phần trước đạt MAE log 0,880 trên 193 transition test (113 franchise), tương đương sai lệch điển hình khoảng 2,4 lần về tỷ lệ opening hoặc khoảng 41 điểm phần trăm theo trung vị. Mức này gần như trùng với hai baseline không dùng thông tin (median −0,164 và Y = 0), chênh 0,002 và 0,008 log và khoảng bất định bao trùm 0. Dữ liệu hiện có vì vậy chưa chứng minh khả năng dự báo tốt hơn baseline đơn giản cho thay đổi opening giữa các phần liên tiếp."*

## 5. Giới hạn

1. **Khả năng tổng quát hóa:** đánh giá sang franchise chưa thấy, **không** xác nhận dự báo theo thời gian (năm chiếu dev và test chồng lấn).
2. **Độ phủ opening:** chỉ 918/25.943 transition hợp lệ (3,5%) có opening cả hai phim; kết luận chỉ áp dụng cho quần thể có opening được ghi nhận.
3. **Quy ước collection (A1) và tính so sánh opening (A2)** chưa xác minh; các cực trị chưa phân biệt được là dự báo đúng hay lỗi so sánh.
4. **Cỡ test:** 193 dòng, 113 franchise; tầng < 1M chỉ 38 dòng, vị trí 6+ chỉ 8 dòng.
5. **Bootstrap** chỉ phản ánh biến động theo thành phần franchise của test, không tính độ bất định của bước fit; là bổ trợ.
6. **Test chỉ chấm một lần** theo thiết kế khóa; đã mô tả phân phối Y của test ở các bước trước (Task 1) nhưng không dùng nó cho thiết kế. E5–E7 chưa chạy (chưa xác nhận policy); E1–E4 không chấm trên test.
7. **Giới hạn kỹ thuật Task 3** (nhánh `rep_decision.json`): không ảnh hưởng kết quả đã khóa, nhưng cần sửa nếu mở lại việc đổi biểu diễn.

## Phụ lục A — File và tái lập

| File | Nội dung |
|:--|:--|
| `records/prescore_record.json` (+`.sha256`) | Bản ghi trước chấm: hash, cấu hình, định nghĩa metric, đối tượng đánh giá, lý do chọn |
| `reference/locked_config_rq1.json`, `manifest_task3.csv` | Bản sao tham chiếu từ Task 3 |
| `logs/prescore_checks.csv`, `test_input_checks.csv`, `scoring_log.csv`, `task2_preflight_output.txt` | Kiểm tra và nhật ký lượt chấm |
| `results/test_metrics.csv`, `test_paired_comparison.csv`, `test_predictions_by_transition.csv` | Metric test; so sánh ghép cặp; dự báo, Y thật, sai số log và điểm phần trăm từng `transition_id` |
| `results/dev_test_composition.csv`, `dev_vs_test_mae.csv`, `delta_mae_dev_vs_test.csv`, `s1_s2_dev_summary.csv` | Đối chiếu dev/test và tổng hợp S1/S2 |
| `results/test_top_errors.csv`, `test_influential_summary.csv` | Transition ảnh hưởng lớn |
| `results/e0_dev_fit_coefficients.csv`, `dev_fit_parameters.json` | Hệ số E0 và median Y fit trên dev |
| `figures/` | Hai biểu đồ PNG và CSV tạo hình |

```
python code/t4_run.py --t3 <task3_rq1> --t2 <task2_rq1> --out . --stage prescore   # chốt bước 6 (chỉ hash byte file test)
python code/t4_run.py --t3 <task3_rq1> --t2 <task2_rq1> --out . --stage score      # chấm test (cần prescore_record hợp lệ)
python code/t4_figures.py .   ;   python code/t4_manifest.py .   # thêm --verify để kiểm hash
```
