# RQ3 — Task 4: chốt bước 6 và đánh giá bước 7

Phiên bản Task 4 **v2** (sửa v1 theo bốn điểm; xem mục 7b và `docs/CHANGELOG_v1_to_v2.md`). Gói bước 5–6 được giữ nguyên trong `inherited_step5_6/`; mọi thay đổi của Task 4 nằm ở `results/`, `figures/`, `code/t4_*.py`, `docs/`.

Nhãn: **[KT]** kiểm tra trực tiếp trong Task 4 · **[KQ]** kết quả đã tính trong Task 4 · **[KẾ THỪA]** lấy từ bước 5–6 và đã được kiểm tra ở mục 1 · **[GĐ]** giả định · **[GH]** giới hạn.

## 0. Kết luận chốt

- **Mẫu chính A1b (910 transition / 557 franchise), phương pháp chính là mô tả theo vị trí (PT1) với bootstrap theo franchise, được giữ nguyên.** Không có lỗi trong kết quả bước 6; có hai chỗ diễn đạt và một nhãn bảng cần sửa (mục 7).
- Ở vị trí 2, 3 và 5, trung vị Y âm **trong các mẫu cắt ngang A0/A1b/A1/A2 và kịch bản loại ngoại lệ đã xét (|Y|>3)**. **PT2 trên tập franchise cố định cho kết quả khác ở vị trí 2 và 3** (tập {2,3,4}, n=69: +37,1% và +0,8%; tập {2,3,4,5}, n=32: +50,7% và +2,4%), nên dấu âm chỉ áp dụng cho các bảng cắt ngang. Vị trí 4: chưa có chiều rõ; CI rộng và chứa 0. Nhóm ≥6: chiều của trung vị đổi theo cấu hình, chưa có chiều nhất quán; chỉ tỷ lệ giảm quanh 50% là ổn định.
- Sự khác nhau giữa các nhóm vị trí phụ thuộc mạnh vào thành phần franchise. Trên cùng một tập franchise cố định ({2,3,4}, 69 franchise) trung vị vị trí 2 là +37,1% và vị trí 3 là +0,8%, trong khi bảng cắt ngang là −14,4% và −17,8%.
- PT3 (D) giữ làm bổ trợ; PT4 (CH) giữ làm bổ trợ. Số mô tả được giữ nguyên: **49/58 franchise có ≥1 đảo chiều trực tiếp và 89/176 cặp transition kề nhau đổi chiều (50,6%)**. Mức 50% chỉ là tham chiếu khi giả định dấu độc lập; không kết luận dấu thực sự độc lập, và không giải thích 49/58 bằng độ dài chuỗi.
- PT2 (tập franchise cố định) được làm ở dạng rút gọn (PT2-lite) vì nó trả lời một bất định còn lại sau PT3/CH: các khác biệt cắt ngang có phải do thành phần không.
- Chẩn đoán R9 được sửa cách gọi và tách theo dữ liệu thành 4 nhóm (mục 3.5); nhóm 11 franchise đã được đối chiếu lại đúng cặp 2→3 (mục 3.5, `R10c`).

## 1. Kiểm tra kết quả kế thừa [KT]

Log: `logs/t4_00_verify_inherited_log.txt`. Không chạy lại toàn bộ bước 6.

| Kiểm tra | Kết quả |
|---|---|
| Hash gói bước 5–6 | md5 `e8e3164d3a4965ddd249ce9f7e8bf3e2`, đúng file được giao ở bước trước |
| PT1: n, F, trung vị, Q1, Q3, tỷ lệ Y<0/=0/>0, % — tính lại độc lập bằng pandas/numpy (không dùng engine) trên 4 mẫu × 6 nhóm | Khớp R2, sai lệch tối đa 1,8e-15 |
| Bootstrap | Không có lần lặp nào bị bỏ vì ô rỗng; CI trong R2 (A1b) bằng percentile 2,5/97,5 của 10.000 bản lặp lưu trong npz |
| PT3 (A0, A1b, A1, A2) | Khớp R3; hai transition chung phim 2 trên mọi mẫu; D = Y23 − Y12 |
| CH | 58 franchise / 234 transition; ≥1 đảo chiều 49; toàn giảm 4; toàn tăng 5 — khớp R4b |
| LOFO nhóm ≥6 | 31 lần bỏ, trung vị tính lại độc lập khớp R7 |
| R8 | Các dòng PT1 chính và PT3 chính chứa đúng số của R2/R3 |
| Đối chiếu bootstrap với helper v4 đầy đủ 10.000 lần | 479 bản lặp đầu tiên của helper v4 (chạy từng lần lặp, seed 20260101) khớp từng lần lặp với bản lặp lưu của engine (sai lệch ≤ 8,9e-16) cho trung vị vị trí 2 và tỷ lệ Y<0 trọng số 1/k_f ở ≥6; cộng với 300 lần lặp kiểm ở bước 5–6. **Chưa chạy helper đủ 10.000 lần** (khoảng 0,5 giây mỗi lần lặp); phần còn lại dựa vào engine đã khớp helper ở mọi lần lặp đã kiểm |
| Phát hiện khi đọc | Nhãn R5 thiếu cột mẫu ở dòng trọng số (đã tạo `R5_v2`, số không đổi); hai cách giải thích CI zero và gọi tên R9 cần sửa (mục 7) |

## 2. Bảng quyết định chốt bước 6

| Hạng mục | Quyết định | Bằng chứng | Lý do |
|---|---|---|---|
| Mẫu chính A1b (910/557) | **Giữ** | Chuyển A0→A1b làm thay đổi trung vị ≤ 0,7 điểm % ở vị trí 2–5, không đổi dấu nào (R5); quy tắc loại là bằng chứng bản ghi đã đặt trước | Phù hợp RQ3; tránh Y=0 nghi vấn; ảnh hưởng nhỏ và đã đo |
| A0, A1 | **Giữ làm độ nhạy** | A1b→A1 đổi trung vị tối đa 0,7 điểm % (vị trí 2–5), −2,76 ở ≥6 vì chỉ 1 transition | Mỗi lần một thay đổi, đã có CI ghép cặp |
| A2 (loại opening < 100.000) | **Chỉ bổ trợ**, đọc là thay đổi thành phần quy mô | Loại 15,5% transition ở vị trí 2; trung vị open_prev ở vị trí 2 tăng 12,4M → 17,1M; 27/44 transition |Y|>3 nằm trong nhóm bị loại | Thay đổi cả cỡ mẫu lẫn thành phần; không quy cho riêng “opening nhỏ”; chưa xác minh tiền tệ |
| PT1: trung vị Y, Q1–Q3, tỷ lệ Y<0/=0/>0, bootstrap theo franchise | **Giữ (CORE)** | Khớp độc lập; CI tái lập; trung vị âm ở vị trí 2, 3, 5 trong các mẫu cắt ngang A0/A1b/A1/A2 và kịch bản loại |Y|>3 đã xét (PT2 tập cố định cho kết quả khác ở vị trí 2 và 3) | Trả lời trực tiếp RQ3; bền với ngoại lệ |
| Số gộp toàn mẫu | **Chỉ bổ trợ** | 512/910 transition ở vị trí 2 | Phản ánh chủ yếu vị trí 2 |
| Nhóm ≥6 | **Điều chỉnh diễn đạt**: trung vị + CI + phân phối; không nêu chiều | Trung vị đổi dấu: A1b −1,6%, A2 +2,9%, A1 trọng số franchise −11,3%, LOFO −7,6% đến +2,9%; CI rộng khoảng 35 điểm %; tỷ lệ Y<0 47–52% mọi cấu hình | Chiều đổi giữa cấu hình |
| Trọng số franchise (1/k_f) ở ≥6 | **Chỉ bổ trợ**, báo cáo cả hai | Franchise lớn nhất chiếm 8,8% vs 3,2% trọng số | Hai trọng số trả lời hai câu hỏi khác nhau |
| PT3 (D, 176 franchise) | **Giữ bổ trợ**, siết diễn đạt | Trung vị D −0,466, cùng chiều ở A0/A1/A2 và tập cố định | D ≠ opening phim 3 giảm; mẫu chọn lọc |
| D ở 3→4 (n=80), 4→5 (n=37) | **Chỉ bổ trợ** | 3→4: CI chứa 0; 4→5: −0,420 [−0,820; −0,155] | Cỡ mẫu nhỏ |
| PT4 / CH | **Giữ bổ trợ, điều chỉnh**: báo cáo cả 49/58 franchise và 89/176 cặp; mức 50% chỉ là tham chiếu | 49/58 franchise có ≥1 đảo chiều; 89/176 cặp (50,6%); tham chiếu giả định dấu độc lập: 50,0% theo cặp, ~47 franchise | Không kết luận dấu độc lập và không giải thích 49/58; chuỗi CH chọn lọc, hai transition kề nhau chia sẻ một opening |
| PT2 | **Làm rút gọn (PT2-lite), chỉ bổ trợ** | Mục 3.6 | Trả lời bất định “thành phần hay trong cùng franchise” |
| Kịch bản |Y|>3 | **Kiểm tra bổ trợ**, không đổi mẫu chính | 44 transition; bỏ chúng đổi trung vị vị trí 2 chỉ +0,70 điểm %; xem 4.3 | Câu hỏi: ảnh hưởng của ngoại lệ lên trung vị và lên chênh lệch A1→A2 |
| LOFO ≥6 | **Giữ bổ trợ** | Trung vị −7,6% … +2,9% | Cho thấy nhạy với một franchise |
| Hồi quy, genre, train/test | **Không làm** | — | RQ3 mô tả; ngoài phạm vi |

## 3. Kiểm tra thành phần mẫu

### 3.1. Cỡ mẫu theo mẫu và vị trí [KT] (`input_tables/T5`, `T4_C1`)

| Vị trí | A0 | A1b | A1 | A2 |
|---|---|---|---|---|
| 2 | 515/515 | 512/512 | 511/511 | 432/432 |
| 3 | 207/207 | 204/204 | 203/203 | 175/175 |
| 4 | 86/86 | 85/85 | 85/85 | 77/77 |
| 5 | 42/42 | 41/41 | 41/41 | 39/39 |
| ≥6 | 68/31 | 68/31 | 67/31 | 58/26 |
| Tổng | 918/562 | 910/557 | 907/555 | 781/461 |

(n transition / n franchise.) Mỗi franchise đóng góp tối đa 1 transition ở vị trí 2–5; chỉ nhóm ≥6 có franchise đóng góp nhiều transition.

### 3.2. Thành phần mẫu chính A1b theo vị trí [KQ] (`T4_C1`)

| Vị trí | n | Năm phát hành phim N (trung vị) | Khoảng cách năm (trung vị; Q1–Q3) | open_prev trung vị | open_prev < 1 triệu | Có opening < 100.000 | 2010s | 2020s |
|---|---|---|---|---|---|---|---|---|
| 2 | 512 | 2009 | 3,0 (2,0–5,1) | 12,3 triệu | 20,3% | 15,6% | 34,4% | 15,0% |
| 3 | 204 | 2011 | 3,0 (2,0–5,1) | 16,1 triệu | 21,1% | 14,2% | 34,8% | 19,6% |
| 4 | 85 | 2011 | 4,0 (2,3–7,0) | 20,1 triệu | 17,6% | 9,4% | 30,6% | 24,7% |
| 5 | 41 | 2013 | 3,0 (1,2–5,6) | 21,7 triệu | 9,8% | 4,9% | 48,8% | 12,2% |
| ≥6 | 68 | 2015 | 2,4 (1,7–5,7) | 17,0 triệu | 19,1% | 14,7% | 45,6% | 20,6% |

Mẫu chủ yếu thuộc 2000s–2020s (thập niên 2010s chiếm 35,6%; 1980s 10,9%; trước 1980 chỉ 2 transition). Quy mô opening trước tăng theo vị trí từ 2 đến 5 — các nhóm vị trí cao gồm franchise có phim trước lớn hơn, là một khác biệt thành phần. Đơn vị tiền tệ và cửa sổ opening chưa xác minh, nên không gọi “triệu USD”.

### 3.3. Mẫu thay đổi thế nào qua A0 → A1b → A1 → A2 [KQ] (`T4_C1d`, `T4_C4`)

| Bước | Số loại | Vị trí (2/3/4/5/≥6) | Franchise liên quan | Thành phần phần bị loại | Trung vị Y toàn mẫu sau bước |
|---|---|---|---|---|---|
| A0→A1b | 8 | 3/3/1/1/0 | 5 | 7/8 thuộc thập niên < 1980 (còn lại 1990s); 7 transition Y=0 chính xác trong A0 nằm trong nhóm này; trung vị open_prev của nhóm bị loại ~11.206 | −0,165 |
| A1b→A1 | 3 | 1/1/0/0/1 | 3 | 1 transition 2000s, 2 transition 2010s; khoảng cách năm trung vị 11,9 | −0,164 |
| A1→A2 | 126 | 79/28/8/2/9 | 104 | Bị loại 3% (1980s), 14% (1990s), 15% (2000s), 19% (2010s), 10% (2020s); trung vị open_prev nhóm bị loại ~40.907; 27 trong 126 có |Y|>3 | −0,127 |

Hai bước đầu hầu như chỉ chạm các transition cũ và vài cặp lẻ. Bước A1→A2 là thay đổi thành phần thật sự (15,5% transition ở vị trí 2, 13,4% ở ≥6), làm lệch mẫu về phía phim có opening trước lớn (trung vị open_prev ở vị trí 2 từ 12,4 triệu lên 17,1 triệu).

### 3.4. Mẫu PT3 và mẫu CH so với mẫu chính — vị trí 2 [KQ] (`T4_C2`, `T4_C2b`)

| Nhóm (A1b, transition vị trí 2) | n | Trung vị % (CI) | Y<0 | open_prev trung vị | Năm phim N (trung vị) | Khoảng cách năm | 2020s |
|---|---|---|---|---|---|---|---|
| Mẫu chính (mọi transition vị trí 2) | 512 | −14,4 (−22,1; −6,5) | 56,6% | 12,3 triệu | 2009 | 3,0 | 15,0% |
| Mẫu PT3 (có Y ở vị trí 2 và 3) | 176 | +24,4 (+9,2; +37,1) | 37,5% | 15,9 triệu | 2005,5 | 2,5 | 8,5% |
| Ngoài mẫu PT3 | 336 | −33,1 (−39,4; −26,0) | 66,7% | 10,5 triệu | 2011 | 3,5 | 18,5% |
| Mẫu CH | 58 | +47,0 (+27,3; +81,5) | 22,4% | 21,9 triệu | 2004 | 2,5 | 0% |
| Ngoài mẫu CH | 454 | −22,6 (−29,0; −14,4) | 61,0% | 11,4 triệu | 2010 | 3,1 | 17,0% |

Mẫu CH chiếm 11,3% transition vị trí 2 nhưng 28,4% ở vị trí 3, 68,2% ở vị trí 4, 63,4% ở vị trí 5 và 50,0% ở ≥6 (34/68 transition, 13/31 franchise). **Mẫu PT3 và CH đã chọn lọc rõ so với mẫu chính** về mức thay đổi ở vị trí 2, quy mô phim trước và thời kỳ (ở vị trí 2, mẫu CH không có phim thuộc 2020s). Vì vậy kết quả PT3/CH mô tả các franchise có chuỗi dữ liệu dài chứ không mô tả franchise nói chung.

### 3.5. Y ở vị trí 3 có hoặc không quan sát được — cách gọi đã sửa [KQ] (`R10`, Hình T4_F1)

Gọi là “**có/không quan sát được Y ở vị trí 3**”, không gọi là “có/không sản xuất phim 3”. Với 512 franchise có Y ở vị trí 2 trong A1b, dữ liệu cho phép tách 336 franchise không có Y ở vị trí 3 thành ba nhóm đã chứng minh được bằng file nguồn (khớp 176 + 67 + 258 + 11 = 512):

| Nhóm theo dữ liệu | n | Cơ sở | Trung vị % vị trí 2 (CI) | Y<0 |
|---|---|---|---|---|
| Có Y ở vị trí 3 | 176 | Y hợp lệ trong A1b | +24,4 (+9,2; +37,1) | 37,5% |
| Có transition vị trí 3 trong master, opening phim 3 thiếu | 67 | `y_ineligible_reason = opening_missing_N` | −33,8 (−46,8; −10,8) | 62,7% |
| Không có transition vị trí 3; collection trong bảng films chỉ có đúng 2 phim | 258 | số phim theo collection | −34,9 (−41,7; −27,7) | 68,6% |
| Không có transition vị trí 3; collection có ≥3 phim; **đúng cặp 2→3** bị loại kỹ thuật `unreleased_film`, phim 3 bị cờ unreleased và có ngày phát hành trong dữ liệu sau ngày thu thập | 11 | `pairs_audit` (chain_pos 2→3, `is_unreleased_curr`), films (`retrieval_date`); từng franchise: `R10c` | +31,1 (−22,4; +159,3) | 45,5% |

Đây là bốn nhóm theo dữ liệu, không phải nguyên nhân đã được giải thích. Chưa phân biệt được vì sao một franchise có collection chỉ 2 phim (không có phim thứ ba trong dữ liệu collection quan sát được, không có nghĩa phim 3 không tồn tại) và chưa giải thích vì sao các nhóm khác nhau về Y ở vị trí 2. Không có bằng chứng ở đây để nói selection bias đã được giải thích; bảng chỉ cho thấy tập franchise có Y ở vị trí 3 khác tập còn lại ngay từ vị trí 2.

**Kiểm tra nhóm 11 franchise (v2, `R10c_G3_verification_11_franchises.csv`).** Ở v1 nhãn nhóm này dựa trên việc franchise có cờ `unreleased_film` ở bất kỳ cặp nào. v2 đối chiếu từng franchise với đúng cặp vào vị trí 3: `chain_pos_prev = 2`, `chain_pos_curr = 3`, phim 2 của cặp trùng phim 2 của transition vị trí 2 có Y, cặp bị loại với `exclusion_reason = unreleased_film`, phim 3 có `is_unreleased_curr = True` và ngày phát hành trong dữ liệu sau ngày thu thập (`retrieval_date` là 2026-10-22 ở mọi dòng bảng films). **Cả 11/11 franchise đạt**, ngày phim 3 trong dữ liệu từ 2026-11-04 đến 2028-10-05; không franchise nào phải hạ xuống nhãn “nguyên nhân thiếu Y3 chưa xác minh; franchise có cờ unreleased” (số này là 0, code vẫn giữ nhãn đó cho trường hợp xảy ra). Nhãn dùng: “**phim vị trí 3 bị cờ unreleased trong dữ liệu**”. Giới hạn: ngày phát hành là lịch dự kiến trong dữ liệu và tình trạng phát hành thực tế hiện tại chưa được xác minh (một phim, *The Last Temptation of Becky*, có ngày trong dữ liệu là 2026-11-04, sau ngày thu thập nhưng có thể đã qua khi đọc báo cáo); báo cáo không khẳng định phim 3 “chưa phát hành” ở hiện tại.

### 3.6. PT2 (tập franchise cố định): quyết định và kết quả [KQ] (`T4_C5`, `T4_C5b`, Hình T4_F2)

**Mục đích:** trả lời một bất định còn quan trọng sau PT3/CH — các khác biệt giữa nhóm vị trí ở bảng cắt ngang phản ánh thành phần franchise hay thay đổi trong cùng franchise. **Mẫu:** A1b; tập {2,3,4} = franchise có Y ở cả ba vị trí (69), tập {2,3,4,5} (32). Ước lượng bằng bootstrap theo franchise, cùng engine/seed; chỉ mô tả, không kiểm định.

| Vị trí | Tập {2,3,4} (n=69): trung vị % [CI] | Cắt ngang A1b | Tập {2,3,4,5} (n=32): trung vị % [CI] |
|---|---|---|---|
| 2 | +37,1 [+24,6; +61,7] | −14,4 | +50,7 [+25,9; +93,7] |
| 3 | +0,8 [−15,4; +12,6] | −17,8 | +2,4 [−17,5; +16,2] |
| 4 | +2,2 [−15,8; +12,6] | +2,2 | +10,7 [−6,3; +32,4] |
| 5 | — | −28,0 | −27,9 [−36,6; −1,7] |

Thay đổi trong cùng franchise (trung vị D, CI): 2→3 so với 1→2: −0,433 [−0,536; −0,296] (n=69), −0,449 [−0,843; −0,264] (n=32); 3→4 so với 2→3: −0,120 [−0,362; +0,092] (n=69), −0,094 [−0,395; +0,289] (n=32); 4→5 so với 3→4: −0,387 [−0,781; −0,118] (n=32); tất cả franchise có Y ở 4 và 5 (n=37): −0,420 [−0,820; −0,155]; ở 3 và 4 (n=80): −0,165 [−0,361; +0,033]. Cách đọc: trên cùng một tập franchise, trung vị vị trí 2 dương và cao, khác hẳn bảng cắt ngang; chiều “mức thay đổi thấp hơn ở transition sau” của PT3 giữ ở tập cố định, còn từ 3→4 thì chưa phân biệt được với 0. Tập cố định cũng là tập “sống sót” đến phim sau, nên đây vẫn không phải quỹ đạo của franchise nói chung.

## 4. Đánh giá độ vững

### 4.1. Theo từng phát hiện (bảng đầy đủ: `T4_robustness_by_finding.csv`, `T4_interpretation_table.md`)

| Phát hiện | Chiều | Độ lớn / CI | Cỡ mẫu | Độ vững |
|---|---|---|---|---|
| Toàn mẫu: trung vị −15,2%, 57,0% giảm | Âm trong mẫu cắt ngang A0/A1b/A1/A2 | CI −19,1% đến −7,7% | 910/557 | Đổi mẫu ≤ 3,2 điểm % |
| Vị trí 2: −14,4% | Âm trong mẫu cắt ngang A0/A1b/A1/A2 và kịch bản loại |Y|>3; **PT2 tập cố định {2,3,4}: +37,1%** | CI −22,1% đến −6,5% | 512 | Dịch +3,1 điểm % ở A2 (CI −0,16; +8,29) |
| Vị trí 3: −17,8% | Âm trong mẫu cắt ngang A0/A1b/A1/A2 và kịch bản loại |Y|>3; **PT2 tập cố định {2,3,4}: +0,8%** | CI −26,0% đến −10,2% | 204 | Dịch ≤ 0,5 điểm % ở A0/A1/A2 |
| Vị trí 4: +2,2% | Chưa có chiều rõ; CI rộng và chứa 0 (trung vị dương nhỏ trong A0/A1b/A1/A2) | CI −15,8% đến +11,8% | 85 | Chưa có chiều rõ |
| Vị trí 5: −28,0% | Âm trong mẫu cắt ngang A0/A1b/A1/A2 và kịch bản loại |Y|>3; tập {2,3,4,5} (n=32): −27,9% | CI −36,8% đến −6,4% | 41 | Dịch ≤ 0,2 điểm % ở A0/A1/A2; CI rộng |
| Nhóm ≥6: −1,6% | **Đổi dấu theo cấu hình** | CI −18,9% đến +16,9% | 68/31 | Chưa có chiều nhất quán; tỷ lệ Y<0 47–52% |
| PT3: trung vị D −0,466; D<0 72,2% | Âm ở A0/A1b/A1/A2 và tập cố định | CI −0,609 đến −0,358 | 176 | Dịch ≤ 0,02 giữa các mẫu |
| CH: 49/58 franchise có ≥1 đảo chiều; 89/176 cặp (50,6%) | — | CI theo cặp 43,4%–57,5% | 176 cặp/58 | Tham chiếu giả định dấu độc lập 50,0% (không phải kiểm định) |

Nhóm vị trí 4 và ≥6 là những nơi “có chiều” hoặc “không có chiều” không nên đọc từ dấu của trung vị: CI rộng so với độ lớn.

### 4.2. CI chênh lệch có nhiều giá trị zero — nguyên nhân [KQ] (`T4_C4`)

Có cả hai cơ chế, không chỉ một:
- **(a) cụm liên quan không được rút:** khi chỉ 1 franchise có transition bị loại (A1b→A1 ở vị trí 2, ≥6), cụm đó không có mặt trong 36,1–36,6% số lần lặp; với 3 transition ở 3 franchise (A0→A1b, vị trí 2) chỉ 4,9%.
- **(b) trung vị không đổi dù cặp xuất hiện:** ví dụ A0→A1b ở vị trí 2: chênh lệch trung vị bằng đúng 0 ở 41,8% số lần lặp, nhưng chỉ 4,9% vì cụm không được rút; còn lại ~36,9% là trung vị không đổi dù cặp có mặt. Với A1→A2 (126 cặp), cụm luôn được rút và chênh lệch trung vị vẫn bằng 0 ở 1,8% (toàn mẫu) đến 20,8% (≥6).
- Với tỷ lệ Y<0, giá trị zero gần như chỉ do (a) (tỷ lệ zero khi cụm có mặt ≈ 0).

→ Câu “đa số zero là do cặp bị loại không có mặt” ở báo cáo bước 5–6 **không đúng cho trung vị**; đã sửa (mục 7). CI chạm 0 hoặc rất hẹp không phải kiểm định ý nghĩa.

### 4.3. Kịch bản |Y|>3 (kiểm tra bổ trợ) [KQ] (`T4_C6`, `T4_C6a`)

Câu hỏi: nhiễu ngoại lệ có tạo ra dịch chuyển trung vị ở A1→A2 và có làm đổi chiều kết luận không. A1b có 44 transition |Y|>3 (21 dương, 23 âm; 31 ở vị trí 2; 27/44 thuộc nhóm opening < 100.000). Bỏ chúng khỏi A1b làm trung vị đổi: vị trí 2 +0,70 điểm % [−2,74; +3,41], vị trí 3 +0,31, vị trí 5 0,00, toàn mẫu +0,14 [−1,34; +1,86]; **nhóm ≥6 đổi −6,00 điểm % (từ −1,6% xuống −7,6%) [−16,5; +2,8]**. Tỷ lệ Y<0 đổi tối đa 1,6 điểm %. Chênh lệch A1→A2 ở vị trí 2 vẫn +2,85 điểm % [0,00; +7,89] sau khi bỏ |Y|>3 ở cả hai mẫu (so với +3,10): dịch chuyển vẫn còn sau khi loại |Y|>3, nên không được giải thích hoàn toàn bởi nhóm này. Kịch bản không thay mẫu chính.

### 4.4. Nhóm ≥6 [KẾ THỪA + KQ]

Trung vị −1,6% (CI −18,9; +16,9), Q1–Q3 −33,2% đến +59,6%, 68 transition / 31 franchise, 50,0% giảm. Các cấu hình: A0/A1b −1,6% (trọng số transition) và −4,3% (trọng số franchise); A1 −4,3% và −11,3%; A2 +2,9% và +4,5%; bỏ từng franchise −7,6% đến +2,9% (trọng số transition); bỏ |Y|>3 −7,6%. Chiều đổi giữa âm và dương: **chưa có chiều tăng/giảm nhất quán**; chỉ tỷ lệ giảm gần 50% giữ nguyên (47–52%). Hình T4_F3.

## 5. Diễn giải ban đầu

### 5.1. Bảng diễn giải (đầy đủ: `T4_interpretation_table.md`)

| Phát hiện | Mẫu và số | Ước lượng + CI | Bằng chứng độ vững | Giới hạn | Cách diễn đạt được phép |
|---|---|---|---|---|---|
| Toàn mẫu, opening thường giảm | A1b, 910/557 | −15,2% [−19,1; −7,7]; 57,0% giảm | Chiều không đổi ở A0/A1/A2 | Chủ yếu vị trí 2; chưa xác minh thị trường, tiền tệ, cửa sổ | “Ở các transition quan sát được, trung vị thay đổi opening là âm.” |
| Vị trí 2, 3, 5 | A1b, 512/204/41 | −14,4%, −17,8%, −28,0% | Âm trong mẫu cắt ngang A0/A1b/A1/A2 và kịch bản loại |Y|>3; PT2 tập cố định cho kết quả khác ở vị trí 2 (+37,1%) và 3 (+0,8%) | Tập franchise khác nhau theo vị trí; chọn lọc | “Trong bảng cắt ngang, transition vào vị trí 2, 3, 5 có trung vị opening thấp hơn phim trước; trên tập franchise cố định kết quả ở vị trí 2 và 3 khác.” Không: “franchise suy giảm khi tiến qua các phần.” |
| Vị trí 4 | A1b, 85 | +2,2% [−15,8; +11,8] | CI chứa 0 | CI rộng | “Chưa có chiều rõ; CI rộng và chứa 0.” Không: “phục hồi.” |
| Nhóm ≥6 | A1b, 68/31 | −1,6% [−18,9; +16,9]; 50,0% giảm | Chiều đổi theo cấu hình | Gộp vị trí 6–15 | “Chưa có chiều nhất quán; khoảng một nửa transition giảm.” |
| PT3 (D) | 176 franchise | trung vị D −0,466 [−0,609; −0,358]; D<0 72,2% | Cùng chiều mọi mẫu và tập cố định | D ≠ opening phim 3 giảm; mẫu chọn lọc | “Mức thay đổi opening từ phim 2 sang 3 thường thấp hơn từ 1 sang 2.” |
| PT4 (CH) | 58/234 | 49/58 franchise có ≥1 đảo chiều; 89/176 cặp (50,6% [43,4; 57,5]) | Tham chiếu giả định dấu độc lập: 50,0% theo cặp | Chuỗi dài chọn lọc; hai transition kề nhau chia sẻ một opening | “Khoảng một nửa số cặp kề nhau đổi chiều (89/176) và 49/58 franchise có ít nhất một đảo chiều; mức 50% chỉ là tham chiếu giả định dấu độc lập.” |
| Chọn lọc | 512 franchise vị trí 2 | +24,4% (có Y3) so với −33,8%, −34,9% | Tách theo master/films/pairs_audit | Mô tả, chưa giải thích | “Tập có Y ở vị trí 3 khác tập còn lại từ vị trí 2.” |

### 5.2. Đoạn văn dùng được cho báo cáo

**Mẫu hình theo vị trí.** Trong mẫu chính A1b (910 transition thuộc 557 franchise), trung vị thay đổi opening giữa hai phim liên tiếp là −15,2% (CI 95% −19,1% đến −7,7%) và 57,0% transition ghi nhận opening giảm. Theo vị trí, trung vị là −14,4% ở vị trí 2, −17,8% ở vị trí 3 và −28,0% ở vị trí 5, đều với CI không chứa 0; ở vị trí 4 trung vị là +2,2% với CI từ −15,8% đến +11,8%: chưa có chiều rõ (CI rộng và chứa 0). Dấu âm này áp dụng cho các bảng cắt ngang; trên tập franchise cố định {2,3,4} (69 franchise) trung vị ở vị trí 2 và 3 là +37,1% và +0,8%. Phân tán rất lớn trong từng nhóm: khoảng Q1–Q3 ở vị trí 2 chạy từ −51,6% đến +56,9%. Do mỗi nhóm vị trí gồm tập franchise khác nhau và các franchise có Y ở vị trí 3 khác các franchise còn lại ngay từ vị trí 2, các chênh lệch giữa nhóm không được đọc như thay đổi trong cùng một franchise.

**Nhóm vị trí 6 trở đi.** Nhóm gộp các vị trí 6–15 gồm 68 transition của 31 franchise có trung vị −1,6% (CI −18,9% đến +16,9%) và 50,0% transition giảm. Chiều của trung vị đổi dấu khi đổi mẫu, trọng số hoặc bỏ từng franchise (−11,3% đến +4,5%), nên chưa có chiều tăng hay giảm nhất quán; tỷ lệ giảm giữ quanh 50% ở mọi cấu hình.

**Trong cùng franchise.** Ở 176 franchise có opening ở cả ba phim đầu, D = Y(2→3) − Y(1→2) có trung vị −0,466 (CI −0,609 đến −0,358) và âm ở 72,2% franchise; kết quả cùng chiều ở A0, A1 và A2 và ở tập cố định có thêm vị trí 4. D âm nghĩa là mức thay đổi opening ở 2→3 thấp hơn ở 1→2, không có nghĩa opening phim 3 thấp hơn phim 2 (Y(2→3)<0 ở 62,5% franchise). Mẫu này gồm franchise có Y ở cả vị trí 2 và 3, với trung vị thay đổi ở 1→2 là +24,4%, nên không đại diện cho mọi franchise. Chuỗi liên tục (58 franchise, 234 transition) cho thấy 89/176 cặp transition kề nhau đổi chiều (50,6%) và 49/58 franchise có ít nhất một đảo chiều trực tiếp. Mức 50% chỉ là tham chiếu khi giả định dấu độc lập; không kết luận dấu thực sự độc lập và không giải thích 49/58 bằng độ dài chuỗi.

**Giới hạn.** Kết quả mô tả opening được ghi nhận trong nguồn hiện có; chưa xác minh thị trường, tiền tệ, cửa sổ opening, quan hệ phần phim và độ đầy đủ của collection; vị trí là thứ tự phát hành trong collection TMDB quan sát được; giá trị danh nghĩa chưa điều chỉnh lạm phát; CI chỉ phản ánh sai số lấy mẫu theo franchise, không phản ánh lỗi đo, chọn lọc hay quan hệ franchise sai. Không có kết luận nhân quả.

### 5.3. Ý cho slide

- 910 transition / 557 franchise; trung vị −15,2%; 57% giảm.
- Âm ở vị trí 2, 3, 5 trong các bảng cắt ngang (PT2 tập cố định khác ở vị trí 2 và 3); vị trí 4 chưa có chiều rõ, CI rộng và chứa 0; nhóm ≥6 chưa có chiều.
- Cùng franchise: mức thay đổi sau thấp hơn trước (D<0 ở 72%), nhưng đó không phải “opening phim 3 giảm”.
- Chọn lọc là điểm cảnh báo chính: mẫu có Y ở vị trí 3 khác mẫu còn lại ngay từ vị trí 2.

## 6. Giới hạn của Task 4

Mọi giới hạn bước 5–6 giữ nguyên. Thêm: nhóm theo khả năng quan sát Y chỉ phân loại theo dữ liệu, không giải thích nguyên nhân; PT2-lite chỉ gồm franchise đủ chuỗi nên chọn lọc; tỷ lệ đảo chiều tham chiếu giả định dấu độc lập nên chỉ để so quy mô; mọi CI bootstrap theo franchise, không cho đa so sánh; không có kiểm định giả thuyết.

## 7. Nhật ký thay đổi so với bước 5–6

| # | Nội dung | Loại | Ảnh hưởng số |
|---|---|---|---|
| 1 | Mục 4.5 báo cáo bước 5–6 gọi nhóm “có/không có phim tiếp theo” → đổi thành “có/không quan sát được Y ở vị trí 3” và tách nhóm theo dữ liệu (R10) | Sửa diễn đạt | Không đổi số R9 (176 và 336) |
| 2 | Lưu ý CI ghép cặp “đa số lần lặp cho chênh lệch bằng 0 vì cặp bị loại không có mặt” → có cả hai cơ chế (mục 4.2) | Sửa giải thích | Không |
| 3 | `R5` thiếu cột mẫu cho 8 dòng trọng số → `R5_v2` thêm cột `sample`; các giá trị không đổi | Sửa nhãn | Không |
| 4 | Thêm PT2-lite, kịch bản |Y|>3, tỷ lệ đảo chiều theo cặp, thành phần mẫu, tổng hợp độ vững ≥6 | Bổ sung | Mới |
| 5 | Câu “49/58 franchise đảo chiều” nay đi kèm 89/176 cặp; mức 50% là tham chiếu giả định (xem 7b) | Sửa diễn đạt | Không |

Không có lỗi số trong kết quả bước 6 được kế thừa. Các file bước 5–6 không bị sửa.

## 7b. Thay đổi v1 → v2 (chi tiết: `docs/CHANGELOG_v1_to_v2.md`)

| # | Nội dung | Ảnh hưởng số |
|---|---|---|
| 1 | Nhóm 11 franchise: đối chiếu đúng cặp vào vị trí 3 (`R10c`), 11/11 đạt; nhãn đổi thành “phim vị trí 3 bị cờ unreleased trong dữ liệu”; không khẳng định tình trạng phát hành thực tế; R10, T4_F1, bảng diễn giải cập nhật | Không (n và ước lượng giữ nguyên) |
| 2 | “Âm ở mọi mẫu/kịch bản” → “âm trong các mẫu cắt ngang A0/A1b/A1/A2 và kịch bản loại ngoại lệ đã xét”; nêu PT2 cho kết quả khác ở vị trí 2 và 3 | Không |
| 3 | Đảo chiều: giữ 49/58 và 89/176; 50% chỉ là tham chiếu giả định dấu độc lập; bỏ câu “chủ yếu do chuỗi dài” và “ngang tham chiếu dấu độc lập” | Không |
| 4 | “Vị trí 4 ≈ 0” → “chưa có chiều rõ; CI rộng và chứa 0”; “không do ngoại lệ” → “vẫn còn sau khi loại |Y|>3, không được giải thích hoàn toàn bởi nhóm này” | Không |

## 8. Bản đồ file

`results/R5_v2…`, `R10…` (gồm `R10c_G3_verification_11_franchises.csv`), `T4_C1…C9`, `T4_decision_table.csv`, `T4_robustness_by_finding.csv`, `T4_interpretation_table.csv|md`; `figures/T4_F1…F4` và `figures/data/`; `code/t4_00…t4_05`; `logs/`; `inherited_step5_6/` (bản sao bước 5–6, chỉ để tái lập). Chạy lại: xem `README.md`.
