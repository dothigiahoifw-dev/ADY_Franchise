# RQ3 — Bước 4: Thiết kế phân tích (bản sửa v4)
ADY — Franchise Sequel Revenue Decay. **Trạng thái:** đề xuất để nhóm duyệt; chưa chạy phân tích chính, chưa bootstrap chính thức.
Nhãn: **[KT]** = kiểm tra trực tiếp trên file ở lượt này; **[KẾ THỪA]** = từ báo cáo trước, chưa tái lập ở lượt này; **[GIẢ ĐỊNH]**; **[ĐỀ XUẤT]**; **[UNVERIFIED]** = chưa xác minh được.

## 0. Tóm tắt
- Giữ nguyên RQ3, đơn vị (transition N−1→N), target Y = ln(Open_N) − ln(Open_{N−1}); % thay đổi = 100×(exp(q)−1), chỉ áp cho trung vị/phân vị/CI. Không lifetime gross, không suy luận nhân quả.
- **Mẫu chính đề xuất: A1b** = A0 trừ 8 cặp *nghi vấn bản ghi* → 910 transition / 557 franchise [KT]. Đây là đề xuất để nhóm duyệt; dự phòng: A1.
- Chuỗi độ nhạy, mỗi lần đổi một thứ: A0↔A1b (−8), A1b↔A1 (−3), A1↔A2 (−126).
- Bốn phép phân tích cốt lõi: **PT1** phân phối Y theo vị trí; **PT3** D = Y(2→3) − Y(1→2); **PT4** quỹ đạo trên chuỗi liên tục; bootstrap theo franchise. Độ nhạy trọng số franchise cho nhóm ≥6.
- Mọi thứ khác (Wilcoxon/kiểm định dấu, D vị trí cao, nhiều cách gộp vị trí, bỏ ngoại lệ, leave-one-franchise-out, PT2) là **tùy chọn có điều kiện** (mục 5).
- Chưa cần hồi quy, chưa cần train/test.

## 1. Kiểm tra đầu vào
| Hạng mục | Kết quả | Nhãn |
|---|---|---|
| Master transitions | 25.943 dòng, `transition_id` duy nhất, 228 cột | [KT] |
| Dòng có Y (A0) | 918 transition / 562 franchise; open_prev, open_curr > 0; vị trí nhỏ nhất = 2 | [KT] |
| Công thức Y | Tính lại từ open_prev/open_curr khớp cột Y | [KT] |
| open_prev/open_curr so với cột raw **nhúng trong master** (`raw_box_office_detailed__opening_weekend_gross_*`) | Khớp 918/918 ở cả hai phía | [KT] — chỉ là đối chiếu nội bộ master, **không** phải đối chiếu với file `box_office_*.csv` gốc |
| Đối chiếu opening/domestic/global master với file raw gốc | Báo cáo bàn giao trước nêu khớp 100%; **chưa tái lập ở lượt này** vì không có `box_office_detailed.csv`, `box_office_raw.csv` | [KẾ THỪA] |
| Cờ open > domestic | Tính lại từ cột raw nhúng: 4 transition | [KT] |
| Cờ "trùng bộ (opening, domestic) giữa phim khác nhau" | Lấy từ `audit_suspect_pairs_v3.csv`: 7 transition. Kiểm tra chéo trên các phim có trong master cho đúng cùng 7 ID | [KT] (kiểm tra chéo chỉ trên phim có trong master, không phải bảng phim đầy đủ) |
| Hai cờ trên gộp lại | 8 transition (3 cặp *Stolen Kisses* nằm ở cả hai cờ) | [KT] |
| 3 cặp chỉ có `open > global` | Khiladi 420→786, Powaqqatsi→Naqoyqatsi, Women in Trouble→Elektra Luxx; cả 3 có global < domestic của cùng phim, opening không vượt domestic | [KT] |
| Lồng nhau, đối chiếu bước 3 | A2 ⊂ A1 ⊂ A1b ⊂ A0; A1 và A2 trùng tập ID với `ids_A1_*_v3.csv`, `ids_A2_*_v3.csv` | [KT] |
| Nối A1b–master | 1:1, không mất/nhân dòng, không thiếu Y | [KT] |

**UNVERIFIED (giữ nguyên):** thị trường, tiền tệ, cửa sổ opening; thứ tự tính trước khi lọc opening; quan hệ sequel/prequel và độ đầy đủ collection TMDB; khớp với file raw gốc (xem trên).
*Không còn gọi là "bị chặn":* việc đối chiếu raw gốc chỉ là chưa làm được ở lượt này vì thiếu file; nếu nhóm bổ sung file, thực hiện ở Bước 5 (mục 6).

## 2. Chọn mẫu
**Đề xuất nhóm trước:** A0 làm mẫu chính, A1/A2 độ nhạy. **Điều chỉnh đề xuất:** A1b.

Lý do (không dựa vào kết quả, quy tắc đặt trước):
1. 4 cặp có opening > domestic gross của chính phim đó là **mâu thuẫn nội tại giữa hai trường** trong cùng bản ghi.
2. 7 cặp có cùng cả opening lẫn domestic với một phim khác. Đây là **nghi vấn gán chung bản ghi**; chưa xác nhận lỗi (có thể do nguồn gộp số liệu, hoặc do trùng thật).
3. **Y = 0 tự nó không phải lý do loại.** Cả 7 cặp trùng đều có Y = 0 vì chia sẻ bản ghi, nhưng căn cứ loại là cờ trùng/mâu thuẫn bản ghi, không phải giá trị Y. Khi báo cáo, Y = 0 vẫn được đếm riêng (không gộp vào giảm/tăng).
4. 3 cặp chỉ có `open > global`: global < domestic của cùng phim là **mâu thuẫn giữa các trường**, chưa chứng minh global sai. Target dùng opening, và opening không vượt domestic ở các cặp này → giữ lại trong A1b; loại ở A1 như một độ nhạy.

Định nghĩa (đã có trong `build_A1b.py`):
| Mẫu | Định nghĩa | n transition / n franchise | Vai trò |
|---|---|---|---|
| **A1b** | A0 trừ 8 cặp nghi vấn (open>domestic hoặc trùng bộ số liệu giữa phim khác nhau) | **910 / 557** [KT] | Chính [ĐỀ XUẤT] |
| A0 | Tất cả có Y | 918 / 562 [KT] | Độ nhạy 1 (so với A1b) |
| A1 | A1b trừ 3 cặp chỉ có cờ global | 907 / 555 [KT] | Độ nhạy 2 (so với A1b) |
| A2 | A1 trừ 126 cặp có open_prev<100.000 hoặc open_curr<100.000 | 781 / 461 [KT] | Độ nhạy 3 (so với A1) |

8 cặp bị loại: xem `excluded_8_pairs_A1b.csv`. Chúng chỉ bị loại khỏi mẫu chính đề xuất; ảnh hưởng luôn được báo cáo qua A0↔A1b. Ngưỡng 100.000 chỉ là kịch bản độ nhạy (tiền tệ/cửa sổ chưa xác minh), không gọi là USD, không coi là quy tắc dữ liệu sai.

Cỡ mẫu theo vị trí (n transition = n franchise ở vị trí 2–5) [KT]:
| Vị trí | A0 | **A1b** | A1 | A2 |
|---|---|---|---|---|
| 2 | 515 | **512** | 511 | 432 |
| 3 | 207 | **204** | 203 | 175 |
| 4 | 86 | **85** | 85 | 77 |
| 5 | 42 | **41** | 41 | 39 |
| ≥6 (transition / franchise) | 68 / 31 | **68 / 31** | 67 / 31 | 58 / 26 |

Khi so A1 với A2, lưu ý 126 cặp bị loại không đều theo vị trí (tỷ lệ cặp có opening nhỏ trong A1 [KT]: vị trí 2 ≈ 15%, 3 ≈ 14%, 4 ≈ 9%, 5 ≈ 5%, ≥6 ≈ 13%), nên A2 đổi cả cỡ lẫn thành phần từng nhóm.

## 3. Đặc tả các phép phân tích
Quy ước chung: quantile type 7 (tuyến tính) cho thống kê không trọng số; % = 100×(exp(q)−1) chỉ cho trung vị/phân vị/CI, không quy đổi trung bình Y; Y=0 báo cáo riêng.

### PT1 — Phân phối Y theo vị trí (CORE)
| Mục | Nội dung |
|---|---|
| Câu hỏi | Phân phối Y và tỷ lệ opening giảm khác nhau thế nào giữa các vị trí 2, 3, 4, 5, ≥6? |
| Mẫu | A1b (chính); độ nhạy A0, A1, A2 |
| Đại lượng | n transition, n franchise; trung vị Y và % tương ứng; Q1, Q3; tỷ lệ Y<0, Y=0, Y>0 |
| Phương pháp | Mô tả theo nhóm; CI bootstrap theo franchise (mục 4) |
| Phép so | Từng nhóm với mốc Y=0; các nhóm đặt cạnh nhau, **không kiểm định giữa nhóm** vì cùng franchise xuất hiện ở nhiều vị trí |
| Bảng/biểu đồ | Bảng đầy đủ (kèm n_transition/n_franchise mỗi nhóm); biểu đồ trung vị + CI + dải IQR; strip/ECDF của Y |
| Giả định | Opening so sánh được giữa hai phim [GIẢ ĐỊNH, UNVERIFIED]; vị trí = thứ tự phát hành trong collection TMDB quan sát được |
| Giới hạn | Mỗi nhóm gồm tập franchise khác nhau (chỉ franchise còn phim tiếp theo có opening) → khác biệt giữa nhóm không đọc thành "franchise tiến triển". Nhóm ≥6 gộp vị trí 6–15, đọc là "transition vào phim thứ 6 trở đi". Y<0 mới là opening giảm; Y thấp không đồng nghĩa opening thấp |

**Chẩn đoán chọn lọc [KT, A0, không phải kết quả]:** trong 515 franchise có Y vị trí 2, nhóm có tiếp Y vị trí 3 có trung vị Y2 ≈ +0,22 (log), nhóm không có ≈ −0,40. So sánh giữa các nhóm vị trí vì vậy bị lẫn bởi chọn lọc.

### PT3 — D = Y(2→3) − Y(1→2) (CORE bổ trợ)
| Mục | Nội dung |
|---|---|
| Câu hỏi | Trong cùng franchise, thay đổi opening ở 2→3 khác 1→2 bao nhiêu (theo log)? |
| Mẫu | Franchise có cả Y vị trí 2 và 3. Cỡ [KT]: A0 177; **A1b 176**; A1 176; A2 160 (mỗi franchise đúng một D) |
| Biến | D = Y₃ − Y₂ = ln O₃ − 2 ln O₂ + ln O₁ |
| Đại lượng | Trung vị D, Q1–Q3, tỷ lệ D<0 / D=0 / D>0; thêm trung bình D để đối chiếu |
| Phương pháp | Ước lượng D từng franchise, bootstrap percentile theo franchise cho trung vị D |
| Phép so | Mốc D=0: mức thay đổi ở 2→3 bằng ở 1→2 |
| Bảng/biểu đồ | Histogram/strip của D; scatter Y2–Y3 với đường y=x (mô tả); bảng Y3 theo dấu Y2 (Y2>0, Y2≤0) |
| Giả định | Phim 1, 2, 3 liên tiếp trong collection, đều có opening |
| Giới hạn | (a) D<0 không có nghĩa opening phim 3 thấp hơn phim 2. (b) O₂ xuất hiện với hệ số −2 trong D, nên D **nhạy với sai số hoặc biến động bất thường của opening phim 2**; điều này không tự buộc D âm. Chẩn đoán [KT]: tương quan Y2–Y3 ≈ −0,21 trên A1b (A0: −0,21); chỉ để minh họa độ nhạy, không dùng làm kết luận. Diễn giải D chỉ mô tả |

### PT4 — Quỹ đạo trong chuỗi liên tục (SUPPORTING)
| Mục | Nội dung |
|---|---|
| Câu hỏi | Trong chuỗi Y liên tục từ vị trí 2, các transition liên tiếp tăng, giảm hay dao động thế nào? |
| Mẫu chuỗi CH | Franchise có Y ở mọi vị trí từ 2 liên tục, mọi transition quan sát trong master đều có Y, ≥3 transition. **A1b: 58 franchise / 234 transition** (trùng A0 và A1) [KT]; A2: 55 / 225 |
| Đại lượng | Mỗi franchise: số transition, số Y<0, dấu từng bước, số lần đổi dấu, min/max Y; toàn mẫu: số franchise theo mẫu hình dấu, tỷ lệ franchise có mọi Y<0 |
| Phương pháp | Mô tả có đếm; không mô hình, không kiểm định |
| Biểu đồ | Đường Y theo vị trí (mỗi franchise một đường mờ, thêm đường trung vị chỉ để tham chiếu); bảng mẫu hình dấu |
| Giới hạn | Chọn lọc theo sống sót: 32/58 franchise chỉ có đúng 3 transition [KT]; không khái quát cho mọi franchise. Chưa khẳng định "đủ toàn collection"; cần đối chiếu vị trí cuối và phim bị loại kỹ thuật với bảng films. Không dùng tự tương quan hay ICC (cặp liền kề chia sẻ opening) |

*(Đổi tên: các phép phân tích trước đây gọi A1, A2, S1, B nay là PT1, PT2, PT3, PT4; "Mẫu B" đổi thành "mẫu chuỗi CH". Tên A0/A1b/A1/A2 chỉ dành cho mẫu.)*

## 4. Bootstrap, trọng số, độ vững
**Phụ thuộc [KT]:** ở vị trí 2–5 mỗi franchise đóng góp tối đa một transition; chỉ nhóm ≥6 có franchise đóng góp nhiều (31 franchise cho 68 transition, tối đa 6/franchise). Phụ thuộc quan trọng ở nhóm ≥6, ở mọi phép so qua nhiều vị trí (PT3, PT4) và ở tổng hợp gộp mọi vị trí.

### Bootstrap theo franchise (dùng cho PT1, PT3, PT4 khi cần CI)
| Mục | Đặc tả |
|---|---|
| Đơn vị lấy mẫu lại | Franchise, lấy **cả cụm** transition của nó, **có hoàn lại**, từ toàn bộ franchise của mẫu đang phân tích (không lấy riêng từng nhóm vị trí) |
| Số bản sao | Franchise được chọn m lần phải đóng góp **đủ m bản sao** các transition của nó. Cài đặt: nối (concatenate) các khối đã rút; **không dùng `isin`** hay cách khác làm mất số lần lặp. Mỗi bản sao có `boot_cluster` riêng |
| Số lần lặp / seed / CI | 10.000; seed cố định `20260101` (cùng seed cho mọi mẫu để so được); percentile 95% |
| Ô rỗng trong một lần lặp | Bỏ lần lặp đó khỏi thống kê của ô, ghi số lần bỏ |
| Nhóm ít franchise | Không loại; luôn in n_transition và n_franchise. Nhóm ≥6 (31 franchise; 26 trên A2) gán nhãn "mô tả, CI rộng", không đặt ngưỡng "đủ ổn định" |
| Không phủ | CI chỉ phản ánh sai số lấy mẫu theo franchise; không phản ánh lỗi đo opening, chọn lọc sống sót hay sai quan hệ phần phim |
| Trạng thái | Chưa chạy chính thức. Hàm và kiểm tra cơ học trên dữ liệu giả lập: `rq3_stats_helpers.py` (`python rq3_stats_helpers.py` → `selftest OK`) |

### Trọng số
- **Chính:** mỗi transition trọng số ngang nhau trong từng nhóm vị trí. Ở 2–5 điều này đồng nghĩa mỗi franchise ngang nhau; ở ≥6, franchise có nhiều transition đóng góp nhiều hơn.
- **Độ nhạy cho nhóm ≥6 — cân bằng đóng góp giữa franchise:** mỗi transition có trọng số w = 1/k_f, với k_f là số transition của franchise đó **trong nhóm ≥6 của mẫu đang phân tích** (nên đổi theo mẫu; trong bootstrap, k_f lấy theo từng bản sao `boot_cluster`, không gộp các bản sao cùng franchise). Mỗi franchise có tổng trọng số 1.
- **Quy tắc phân vị có trọng số** (`wquantile`): sắp Y tăng dần; F_i = tổng trọng số tích lũy đến i / tổng trọng số; phân vị q là y_i đầu tiên có F_i ≥ q; nếu F_i = q (sai số 1e-12) lấy trung bình y_i và y_{i+1}. Với trọng số bằng nhau, trung vị trùng `np.median`; Q1/Q3 có thể lệch type 7. Vì vậy trong bảng độ nhạy phải báo cả bản **không trọng số tính bằng cùng quy tắc này**, rồi mới so với bản có trọng số. Tỷ lệ Y<0 có trọng số = tổng trọng số của Y<0 / tổng trọng số.
- **Diễn giải:** số có trọng số cho biết kết quả nhóm ≥6 thay đổi thế nào khi cân bằng đóng góp giữa các franchise. Không gọi là "trung vị franchise điển hình"; chỉ báo cáo hai bản cạnh nhau, nêu khác nhau về ý nghĩa, không chọn bản đẹp hơn.
- Không đề xuất một con số gộp mọi vị trí làm kết quả chính (chủ yếu phản ánh vị trí 2).

### Độ vững (cốt lõi)
1. A0↔A1b, A1b↔A1, A1↔A2: với mỗi nhóm vị trí, hiệu trung vị Y (sau−trước), hiệu tỷ lệ Y<0, hiệu độ rộng CI.
2. Trọng số franchise ở ≥6 (trên).
3. Đọc độ vững theo ba yếu tố: chiều (dấu trung vị, tỷ lệ Y<0 so với 50%), độ lớn (độ dịch trung vị theo % và log so với CI/IQR), bất định (CI có chứa Y=0 không, độ rộng). Không đặt ngưỡng định lượng cho "vững".

## 5. Phần tùy chọn (chỉ làm khi có lý do cụ thể, ghi lý do khi kích hoạt)
| Mục tùy chọn | Khi nào làm |
|---|---|
| Wilcoxon signed-rank / kiểm định dấu cho D | Nếu nhóm cần một kiểm tra phụ ngoài CI bootstrap; không thay CI |
| D(3→4) [n=80 trên A1b], D(4→5) [n=37] | Nếu nhóm quan tâm vị trí cao; nêu rõ cỡ mẫu nhỏ [KT] |
| Cách gộp vị trí khác (6–7/8+, cắt ≥5, từng vị trí 6…15 không CI) | Nếu kết quả nhóm ≥6 nhạy với cách gộp hoặc nhóm yêu cầu |
| Bỏ ngoại lệ \|Y\|>3 (44 cặp trên A1b, 31 ở vị trí 2 [KT]) | Nếu phát hiện cụm ngoại lệ gắn với lỗi đo; không loại mặc định. Trung vị/IQR/tỷ lệ Y<0 vốn bền |
| Leave-one-franchise-out ở ≥6 (31 lần), bỏ 3 franchise đóng nhiều nhất | Nếu một franchise dài chi phối kết quả nhóm ≥6 |
| PT2 — cùng franchise qua vị trí (A1b có Y ở {2,3}, {2,3,4}, {2..5}; cỡ trên A1b [KT]: 176 / 69 / 32) | Nếu nhóm cần tách thành phần franchise khỏi khác biệt giữa vị trí; chọn lọc mạnh |
| Bảng độ phủ vị trí × thập niên, median gap_years, median open_prev | Nếu cần bối cảnh mô tả |

## 6. Kế hoạch triển khai bước 5–7
- **Missing/biến đổi:** không imputation; không dùng biến phụ (budget, theater_count, genre…). Biến tạo: `pos_bin` (2,3,4,5,≥6), `pct` = 100(exp(q)−1), `sign3` (Y<0, =0, >0), cờ mẫu A0/A1b/A1/A2 từ `sample_flags_A0.csv`.
- **Thứ tự:** (B5) nạp, nối 1:1, assert 918/910/907/781 và lồng nhau; nếu có `box_office_*.csv` gốc thì đối chiếu opening/domestic/global và kiểm tra tiền tệ, cửa sổ opening. (B6) PT1 trên A1b + bootstrap → chuỗi độ nhạy A0↔A1b↔A1↔A2 → PT3 → PT4 → trọng số ≥6. (B7) bảng/biểu đồ/ghi chú giới hạn; chỉ mô tả có số, không ngôn ngữ nhân quả, không "phục hồi"/"càng nhiều phần càng giảm".
- **Đầu ra:** `run_config` (seed, B=10.000, phiên bản mẫu), `ids_A1b.csv`, bảng PT1 theo từng mẫu, bảng độ nhạy từng bước, bảng PT3, bảng PT4 + mẫu hình dấu, biểu đồ, nhật ký kiểm tra, code chạy một lệnh.
- **Hồi quy / train-test:** không cần cho RQ3 mô tả. Chỉ cân nhắc nếu nhóm đặt câu hỏi mới (ví dụ Y theo gap_years sau khi cố định vị trí), khi đó cần SE theo cụm franchise hoặc hiệu ứng ngẫu nhiên.

## 7. Quyết định cần nhóm duyệt
| # | Quyết định | Khuyến nghị |
|---|---|---|
| 1 | Mẫu chính | A1b (910/557), **đề xuất**; dự phòng A1 nếu không muốn thêm danh sách |
| 2 | Thứ tự so độ nhạy | A0↔A1b, A1b↔A1, A1↔A2, mỗi lần một thay đổi |
| 3 | Trọng số | Transition ngang nhau (chính); trọng số 1/k_f cho ≥6 (độ nhạy, diễn giải: cân bằng đóng góp giữa franchise) |
| 4 | CI | Bootstrap cụm franchise có hoàn lại, đủ số bản sao, 10.000 lần, percentile 95%, seed cố định |
| 5 | Đưa PT3 (D) vào | Có, ước lượng trực tiếp trên 176 franchise, kèm lưu ý D nhạy với opening phim 2 |
| 6 | Gộp vị trí | 2,3,4,5,≥6; các cách gộp khác là tùy chọn |
| 7 | Quy ước báo cáo Y | Target Y cố định; % chỉ cho trung vị/phân vị/CI; Y=0 báo cáo riêng, không là lý do loại; không quy đổi trung bình Y thành "% trung bình" |
| 8 | Phạm vi PT4 | Chỉ mô tả "chuỗi Y liên tục từ vị trí 2 theo master" (mẫu chuỗi CH); không khái quát |
| 9 | Hồi quy / train-test | Không ở RQ3 mô tả |
| 10 | File gốc `box_office_*.csv` | Cần bổ sung để đối chiếu; nếu chưa có, giữ UNVERIFIED cho khớp raw, thị trường, tiền tệ, cửa sổ opening |
