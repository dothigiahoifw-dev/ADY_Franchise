# RQ3 — Bước 5–6: báo cáo kết quả vòng đầu

Trạng thái: **kết quả vòng đầu, chưa phải đánh giá cuối bước 7.** Mọi số liệu dưới đây được tạo từ dữ liệu thật bằng code trong gói (`code/`), seed 20260101, bootstrap 10.000 lần. Thiết kế đã được nhóm duyệt; không đổi mẫu hay cấu hình theo kết quả.

Nhãn: **[KT]** kiểm tra trực tiếp trong lần chạy này · **[KQ]** kết quả phân tích · **[GĐ]** giả định · **[GH]** giới hạn.

## 1. Câu hỏi và phạm vi

RQ3: What patterns of change appear as a franchise progresses across sequels? Đơn vị: transition N−1→N. Target Y = ln(Open_N) − ln(Open_{N−1}); % thay đổi = 100·(exp(Y)−1). Y<0: opening giảm; Y=0: bằng nhau (báo cáo riêng); Y>0: tăng. Không đặt ngưỡng “ổn định”, không kết luận nhân quả, không hồi quy, không train/test.

## 2. Bước 5 — chuẩn bị đầu vào [KT]

Toàn bộ kiểm tra trong `logs/01_prepare_log.txt` đạt (không có FAIL); không ép dữ liệu khớp mốc.

| Hạng mục | Kết quả |
|---|---|
| Master | 25.943 dòng, `transition_id` duy nhất |
| A0 (có Y) | 918 transition / 562 franchise; Y hữu hạn, opening > 0, Y khớp công thức, vị trí ≥ 2, mỗi franchise tối đa 1 transition mỗi vị trí |
| Nối ID–master 1:1 | Không mất, không nhân dòng, không thiếu Y |
| Đối chiếu file raw gốc | `open_prev`/`open_curr` khớp `box_office_detailed.csv` 918/918 mỗi phía; domestic và global gross khớp raw (kiểm tra ở lượt trước, trên cùng 918 dòng) |
| Cờ nghi vấn tính lại từ raw | trùng (opening, domestic) giữa phim khác nhau: 7; opening > domestic: 4; khớp audit v3 |
| Mẫu | A0 918/562 · A1b 910/557 · A1 907/555 · A2 781/461; khớp tập ID của bước 3 (A0, A1, A2) và `ids_A1b.csv` bước 4; A2 ⊂ A1 ⊂ A1b ⊂ A0 |
| Bảng D | 177 / 176 / 176 / 160 franchise (A0 / A1b / A1 / A2); hai transition 1→2 và 2→3 nối đúng cùng phim 2 (cùng `film_key` và cùng opening) trên cả 177; D = Y23 − Y12 = ln O3 − 2 ln O2 + ln O1 khớp |
| Chuỗi CH | 58/234 (A1b = A0 = A1) và 55/225 (A2); mọi ID CH thuộc A1b; vị trí liên tục từ 2; không mở rộng mẫu |
| Y=0 | 7 trong A0 (tất cả nằm trong 8 cặp bị loại), 0 trong A1b |
| \|Y\|>3 | 44 transition trong A1b; chỉ báo cáo, không loại |
| Helper v4 | selftest đạt; engine vector hóa khớp helper **từng lần lặp** (B=300, dữ liệu thật A1b), `logs/00_validate_engine_log.txt` |

## 3. Phương pháp (như thiết kế đã duyệt)

- Bootstrap theo franchise: rút lại toàn bộ cụm franchise có hoàn lại từ **toàn bộ** franchise của mẫu, giữ đủ số bản sao; 10.000 lần; percentile 95%; seed 20260101; trọng số 1/k_f tính theo từng bản sao; ô rỗng bị bỏ và đếm (kết quả: 0 lần rỗng ở mọi ô).
- Trung vị/phân vị: quy tắc nghịch đảo CDF của helper cho các so sánh trọng số; Q1–Q3 mô tả dùng nội suy tuyến tính. Với trọng số ngang nhau trung vị trùng `np.median`.
- CI chênh lệch giữa hai mẫu: bootstrap **ghép cặp** (cùng cụm rút chung trên universe A0, 562 franchise), không suy ra từ CI từng mẫu.
- CI từng mẫu của PT1/PT3 lấy từ universe của chính mẫu đó (như thiết kế); phần đối chiếu dùng universe chung A0 nên CI hơi khác nhưng điểm ước lượng giống hệt.

## 4. Kết quả

### 4.1. Toàn mẫu A1b (910 transition / 557 franchise) — Hình F1

Trung vị Y = −0,165 (−15,2%; CI 95% −19,1% đến −7,7%); Q1–Q3 từ −47,5% đến +39,8%. Opening giảm ở 519 transition (57,0%; CI 53,8%–60,2%), tăng ở 391 (43,0%), bằng nhau 0. Con số tổng gộp chủ yếu phản ánh vị trí 2 (512/910 transition).

### 4.2. PT1 — Y theo vị trí (A1b) — Hình F2, F3, F4

| Vị trí | n transition | n franchise | Trung vị % (CI 95%) | Q1–Q3 (%) | Y<0 (CI 95%) |
|---|---|---|---|---|---|
| 2 | 512 | 512 | −14,4 (−22,1; −6,5) | −51,6; +56,9 | 56,6% (52,3; 60,9) |
| 3 | 204 | 204 | −17,8 (−26,0; −10,2) | −44,5; +27,6 | 61,8% (55,2; 68,4) |
| 4 | 85 | 85 | +2,2 (−15,8; +11,8) | −44,9; +38,4 | 48,2% (37,5; 59,0) |
| 5 | 41 | 41 | −28,0 (−36,8; −6,4) | −44,9; +3,7 | 68,3% (53,5; 82,2) |
| ≥6 (vị trí 6–15, gộp) | 68 | 31 | −1,6 (−18,9; +16,9) | −33,2; +59,6 | 50,0% (40,5; 59,0) |

Quan sát mô tả: trung vị Y ở vị trí 2, 3 và 5 âm và CI không chứa 0; ở vị trí 4 và nhóm ≥6 CI chứa 0 và rộng (nhóm ≥6 chỉ có 31 franchise). Phân phối Y rộng ở mọi nhóm (khoảng IQR lớn hơn nhiều so với khác biệt giữa các trung vị). **Không đọc đây là xu hướng trong cùng franchise** — mỗi nhóm là một tập franchise khác nhau (xem 4.5 về chọn lọc).

### 4.3. PT3 — D = Y(2→3) − Y(1→2) (A1b, 176 franchise) — Hình F5

Trung vị D = −0,466 (CI 95% −0,609 đến −0,358); Q1–Q3 từ −1,195 đến +0,048. D<0: 127 franchise (72,2%; CI 65,3%–78,4%), D=0: 0, D>0: 49 (27,8%). Trong chính tập này, trung vị Y(1→2) = +0,219 (+24,5%) và trung vị Y(2→3) = −0,196 (−17,8%).

Diễn giải: mức thay đổi opening ở 2→3 thấp hơn ở 1→2 trong đa số franchise của tập này. D<0 **không** có nghĩa opening phim 3 thấp hơn phim 2 (trong tập này Y(2→3)<0 ở 62,5% franchise). D dùng chung opening phim 2 với hệ số −2: biến động bất thường của O2 ảnh hưởng mạnh tới D và làm Y(1→2), Y(2→3) lệch ngược chiều; tương quan Pearson giữa hai Y là −0,21 nhưng Spearman chỉ −0,03 (nhạy với ngoại lệ). Dùng chung O2 không tự buộc D âm, nhưng cũng không cho phép đọc D như bằng chứng riêng về “sequel fatigue” hay nhân quả.

### 4.4. PT4 — quỹ đạo trong chuỗi CH (58 franchise / 234 transition) — Hình F6

- Độ dài chuỗi (số transition): 3 → 32 franchise; 4 → 13; 5 → 6; 6 → 2; 7, 8, 9 → 1 mỗi loại; 10 → 2.
- Toàn giảm: 4 franchise; toàn tăng: 5; có ít nhất một đảo chiều trực tiếp giữa hai transition kề nhau: 49 franchise (89 lần đảo chiều tổng); không đảo chiều: 9. Không có Y=0 (không phải xử lý nối qua zero). 29 mẫu hình dấu khác nhau; thường gặp nhất `++-` (8), `+--` (7), `+-+` (5), `+++` (4).
- Trung vị Y theo vị trí (số franchise đóng góp): vị trí 2: +47,0% (58), 3: +2,4% (58), 4: +1,7% (58), 5: −23,3% (26), 6: +7,5% (13), 7: +22,1% (7), 8: −24,2% (5), 9: −30,0% (4), 10: +16,7% (3), 11: +128,9% (2). Đường này đổi thành phần franchise theo vị trí; không phải quỹ đạo của một franchise điển hình, và các vị trí ≥8 chỉ có 2–5 franchise.
- Độ nhạy CH_A2 (55/225): 3 toàn giảm, 4 toàn tăng, 48 có đảo chiều; cùng bức tranh.
- **Không gọi CH là toàn collection đã xác minh.**

### 4.5. Chọn lọc theo việc franchise có phim tiếp theo — chẩn đoán mô tả (`R9`)

Ở vị trí 2 (A1b): franchise **có** Y ở vị trí 3 (n=176) có trung vị +24,4% (CI +9,2; +37,1) và Y<0 là 37,5%; franchise **không có** Y ở vị trí 3 (n=336) có trung vị −33,1% (CI −39,4; −26,0) và Y<0 là 66,7%. Franchise thuộc chuỗi CH (n=58) có trung vị +47,0% và Y<0 là 22,4% ở vị trí 2. Các nhóm vị trí cao và mẫu D, CH vì vậy là các tập franchise chọn lọc theo việc có thêm phim có opening; điều này giải thích vì sao so sánh giữa nhóm vị trí và PT3/PT4 không thể đọc như hành vi của một franchise điển hình.

### 4.6. Độ nhạy (mỗi lần một thay đổi) — Hình F7, F8; bảng đầy đủ `R5`, `R8`

| Đối chiếu | Cỡ mẫu | Thay đổi trung vị (điểm % của %thay đổi) theo vị trí 2 / 3 / 4 / 5 / ≥6 / toàn mẫu | Thay đổi tỷ lệ Y<0 (điểm %) |
|---|---|---|---|
| A0 → A1b (−8 cặp) | 918 → 910 | −0,70 / −0,51 / +0,49 / −0,12 / 0,00 / −1,51 | từ 0,0 đến +1,6 mỗi vị trí; toàn mẫu +0,4 |
| A1b → A1 (−3 cặp) | 910 → 907 | +0,70 / +0,31 / 0,00 / 0,00 / −2,76 / +0,06 | từ −0,2 đến +0,7 |
| A1 → A2 (−126 cặp) | 907 → 781 | +3,10 / 0,00 / +1,32 / −0,16 / +7,21 / +3,15 | từ −2,8 đến +3,5; toàn mẫu −0,3 |

Cách đọc: loại 8 hoặc 3 cặp nghi vấn đổi các số ở vị trí 2–5 rất ít và không đổi chiều nào; riêng nhóm ≥6 có 1 transition bị loại ở A1b→A1 nên trung vị đổi −2,76 điểm %. Khi loại 126 cặp có opening nhỏ, trung vị ở vị trí 2 dịch +3,1 điểm % (CI ghép cặp −0,2 đến +8,3), toàn mẫu +3,15 (−0,005 đến +4,9) và nhóm ≥6 dịch +7,2 điểm % (CI −4,5 đến +19,2); chiều của các trung vị vị trí 2, 3, 5 không đổi, còn nhóm ≥6 đổi dấu (−4,3% → +2,9%) trong khoảng bất định rất rộng. Đây là thay đổi cả cỡ mẫu lẫn thành phần (loại 15% transition ở vị trí 2), nên không quy cho riêng “opening nhỏ”.

Lưu ý CI ghép cặp: ở các phép loại ít cặp, đa số lần lặp cho chênh lệch đúng bằng 0 (cặp bị loại không có mặt) nên CI rất hẹp hoặc chạm 0; **không dùng làm kiểm định ý nghĩa**.

**Trọng số ở nhóm ≥6 (cùng quy tắc phân vị):**

| Mẫu | n / F | Transition ngang nhau | Franchise ngang nhau (1/k_f) |
|---|---|---|---|
| A1b | 68 / 31 | −1,6% · Y<0 50,0% | −4,3% (CI −27,6; +35,3) · Y<0 50,3% |
| A1 | 67 / 31 | −4,3% · 50,7% | −11,3% (CI −31,2; +22,3) · 51,9% |
| A2 | 58 / 26 | +2,9% · 48,3% | +4,5% (CI −24,1; +35,3) · 47,4% |

Franchise lớn nhất chiếm 8,8% tổng trọng số (transition ngang nhau) so với 3,2% (franchise ngang nhau) ở A1b. Chênh lệch trung vị giữa hai trọng số ở A1b: −2,76 điểm % (CI ghép cặp −17,9 đến +20,6). Tỷ lệ Y<0 gần như không đổi (+0,3 điểm %).
Quét bỏ từng franchise ở ≥6 (A1b, tùy chọn, `R7`): trung vị (transition ngang nhau) dao động từ −7,6% đến +2,9% và Y<0 từ 48,4% đến 51,5%; trung vị franchise ngang nhau chỉ nhận vài giá trị rời rạc (−11,3% … +4,5%). Kết luận mô tả: **trung vị của nhóm ≥6 không ổn định theo cấu hình nhỏ**, còn tỷ lệ giảm ≈ 50% khá ổn định; không đặt ngưỡng “ổn định” định lượng.

## 5. Điều khác biệt hoặc cần lưu ý so với tài liệu đầu vào

1. Mọi số đếm mốc (918/910/907/781, 562/557/555/461, D 177/176/176/160, CH 58/234 và 55/225, cỡ mẫu theo vị trí) **khớp**; không có chênh lệch.
2. Mục 2 của bản thiết kế ghi “Claude lượt trước báo cáo khớp 100%”: lần này đã đối chiếu trực tiếp opening với `box_office_detailed.csv` gốc (918/918 mỗi phía); thị trường, tiền tệ, cửa sổ opening vẫn UNVERIFIED (file raw không có trường tiền tệ/cửa sổ).
3. Cùng seed giữa các mẫu không tạo bootstrap ghép cặp; vì vậy chênh lệch được tính ở universe A0 riêng.
4. Điều tôi nêu trong thiết kế trước (“tương quan Y2–Y3 ≈ −0,2”) là hệ số Pearson trên A0; Spearman chỉ ≈ −0,03, nên không dùng làm bằng chứng.

## 6. Giới hạn

Opening chưa xác minh comparability; vị trí là thứ tự phát hành trong collection TMDB quan sát được; quan hệ phần phim và độ đầy đủ collection UNVERIFIED; giá trị danh nghĩa chưa điều chỉnh lạm phát; chọn lọc theo việc có phim tiếp theo (mục 4.5) và mẫu CH/D chọn lọc; nhóm ≥6 gộp nhiều vị trí và chỉ 31 franchise; CI chỉ phản ánh sai số lấy mẫu theo franchise, không phản ánh sai số đo opening, chọn lọc hay sai quan hệ franchise; nhiều so sánh được trình bày song song và không có điều chỉnh đa so sánh (không kiểm định).

## 7. Việc để bước 7 và quyết định cần nhóm xem

- Có cần PT2 (cùng tập franchise qua các vị trí) để tách thành phần khỏi chọn lọc? Kiểm tra cỡ mẫu ở bước thiết kế (trên A0): 177 / 69 / 32 franchise có Y ở đủ {2,3} / {2,3,4} / {2,3,4,5}, nên tập cố định thu hẹp nhanh.
- Cách trình bày nhóm ≥6: giữ trung vị kèm CI rộng, hay chuyển sang mô tả phân phối.
- Có thêm kịch bản loại |Y|>3 (44 transition) như độ nhạy hay không.
- Giữ ghi chú về mức không ổn định của trung vị ≥6 trong báo cáo cuối.

## 8. Bản đồ file

`results/R1`…`R9` (bảng), `results/R8_test_matrix.csv|md` (bảng thử nghiệm), `figures/F1`…`F9` (PNG) và `figures/data/` (dữ liệu vẽ), `input_tables/T1`…`T5` (bảng đầu vào), `logs/`, `code/`, `config.json`, `README.md`.
