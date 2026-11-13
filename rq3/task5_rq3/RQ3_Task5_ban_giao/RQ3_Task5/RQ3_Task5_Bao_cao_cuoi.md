# RQ3 — Báo cáo cuối: Opening thay đổi thế nào khi franchise tiến qua các phần?

Dự án ADY — Franchise Sequel Revenue Decay · Task 5 (bước 8: diễn giải và bàn giao cuối)

Nền: gói bước 5–6 và Task 4 v2 (giữ nguyên trong `inherited_task4_v2/`). Task 5 không chạy lại toàn bộ bootstrap; chỉ tái tính độc lập các số chính và chạy lại có mục tiêu một số ô CI (mục C của phụ lục).

Nhãn bằng chứng dùng trong báo cáo: **[T5-KT]** số đã được tái tính độc lập ở Task 5; **[KẾ THỪA]** số lấy từ bước 5–6/Task 4 và chưa được tái tính ở Task 5; **[GĐ]** giả định; **[GH]** giới hạn. Một số được kế thừa không được nâng thành “đã kiểm tra trực tiếp”.

## Tóm tắt (câu trả lời ngắn)

- Trong dữ liệu quan sát được (910 transition của 557 franchise), opening của phim sau **thường thấp hơn** phim trước: trung vị −15,2% và 57,0% transition giảm. Nhưng mức thay đổi **rất phân tán** — một nửa số transition nằm trong khoảng từ −47,5% đến +39,8%.
- Theo vị trí: trung vị âm ở vị trí 2 (−14,4%), 3 (−17,8%) và 5 (−28,0%) trong các bảng cắt ngang và các kịch bản đã xét; vị trí 4 chưa có chiều rõ (CI rộng và chứa 0); nhóm vị trí 6 trở đi không có chiều nhất quán, với tỷ lệ giảm quanh 50%.
- Trong cùng franchise, mức thay đổi opening ở 2→3 thường thấp hơn ở 1→2 (D âm ở 72,2% franchise), nhưng điều này **không** có nghĩa opening phim 3 thấp hơn phim 2.
- Khác biệt giữa các nhóm vị trí phụ thuộc mạnh vào việc franchise nào có mặt ở nhóm đó: trên cùng một tập franchise cố định, kết quả ở vị trí 2 và 3 khác bảng cắt ngang.
- Dữ liệu mô tả mẫu hình; chưa đủ để kết luận nguyên nhân, để nói “sequel fatigue” đã được chứng minh, hay để đưa ra khuyến nghị sản xuất hoặc dừng sequel.

## 1. Câu hỏi và ý nghĩa business

**Câu hỏi RQ3:** những mẫu hình thay đổi opening xuất hiện thế nào khi franchise tiến qua các phần?

Với người lập kế hoạch phát hành hoặc đánh giá một sequel, câu hỏi thực tế là: so với phim trước, opening của phim sau thường cao hơn hay thấp hơn bao nhiêu, mức đó thay đổi ra sao ở các phần sau, và những con số này đáng tin đến đâu khi áp dụng cho một franchise cụ thể. Báo cáo này trả lời bằng cách **mô tả** các thay đổi đã quan sát, không dự báo và không giải thích nguyên nhân.

## 2. Target, đơn vị phân tích, mẫu và lý do chọn phương pháp

**Đơn vị:** một transition từ phim N−1 sang phim N trong cùng franchise (franchise theo TMDB collection quan sát được; vị trí N là thứ tự phát hành trong collection đó, chưa phải số phần chính thức đã xác minh).

**Target:** Y = ln(Open_N) − ln(Open_{N−1}). Phần trăm thay đổi = 100 × (exp(Y) − 1). Y<0 là opening giảm, Y>0 là tăng, Y=0 là bằng nhau. Dùng log để thay đổi tương đối đối xứng và để trung vị quy đổi được sang phần trăm.

**Mẫu** [T5-KT: kích thước và cách tái lập]:

| Mẫu | Điều kiện | Transition / franchise | Vai trò |
|---|---|---|---|
| **A1b** | Mọi transition có Y, trừ 8 cặp có bằng chứng bản ghi nghi vấn (opening lớn hơn domestic gross của chính phim, hoặc trùng cả opening và domestic giữa hai phim khác nhau) | 910 / 557 | **Mẫu chính** |
| A0 | Mọi transition có Y | 918 / 562 | Độ nhạy: giữ 8 cặp nghi vấn |
| A1 | A1b trừ 3 cặp chỉ bị cờ global gross | 907 / 555 | Độ nhạy |
| A2 | A1 trừ cặp có opening của một trong hai phim dưới 100.000 | 781 / 461 | Độ nhạy: thay đổi thành phần quy mô |

**Phương pháp:**
- **PT1 (chính):** mô tả Y theo vị trí 2, 3, 4, 5 và ≥6 — trung vị, khoảng Q1–Q3, tỷ lệ opening giảm; khoảng tin cậy (CI) bằng bootstrap theo franchise (10.000 lần, percentile 95%, seed 20260101). Chọn mô tả và trung vị vì phân phối Y lệch và có ngoại lệ, và vì câu hỏi là về mẫu hình, không phải dự báo.
- **Bootstrap theo franchise** vì các transition cùng franchise không độc lập (hai transition kề nhau còn chia sẻ một opening); CI chỉ phản ánh sai số lấy mẫu theo franchise.
- **Bổ trợ:** PT2 rút gọn (cùng một tập franchise qua nhiều vị trí), PT3 (D = Y(2→3) − Y(1→2)), PT4 (chuỗi liên tục, đảo chiều).
- **Độ vững:** đổi mẫu A0/A1b/A1/A2, trọng số franchise, bỏ từng franchise ở nhóm ≥6, bỏ |Y|>3.
- **Không dùng:** hồi quy, train/test, nhân quả. Không có phép kiểm định giả thuyết.

## 3. Kết quả toàn mẫu và theo vị trí

![Hình 1](figures/main/Hinh1_phan_phoi_va_mau_hinh_theo_vi_tri.png)

**Hình 1.** Mẫu A1b (910 transition / 557 franchise). (a) Phân phối Y toàn mẫu; (b) trung vị % thay đổi theo vị trí kèm CI 95% và khoảng Q1–Q3; (c) tỷ lệ opening giảm kèm CI 95%. n = số transition, F = số franchise (ở vị trí 2–5 mỗi franchise đóng góp một transition). *Thông điệp:* opening thường giảm nhưng phân tán rất lớn; các nhóm vị trí gồm tập franchise khác nhau. Dữ liệu vẽ: `figures/data/Hinh1_data_PT1_A1b.csv`.

**Toàn mẫu** [T5-KT điểm ước lượng và CI]: trung vị Y = −0,165, tức −15,2% (CI 95% −19,1% đến −7,7%); opening giảm ở 519/910 transition (57,0%, CI 53,8%–60,2%), tăng ở 391, không có Y=0. Con số gộp phản ánh chủ yếu vị trí 2 (512/910 transition).

**Theo vị trí** (mẫu A1b) [T5-KT điểm ước lượng; CI T5-KT đọc lại từ 10.000 bản lặp lưu]:

| Vị trí | n transition / n franchise | Trung vị % (CI 95%) | Q1–Q3 (%) | Opening giảm (CI 95%) |
|---|---|---|---|---|
| 2 | 512 / 512 | −14,4 (−22,1; −6,5) | −51,6; +56,9 | 56,6% (52,3; 60,9) |
| 3 | 204 / 204 | −17,8 (−26,0; −10,2) | −44,5; +27,6 | 61,8% (55,2; 68,4) |
| 4 | 85 / 85 | +2,2 (−15,8; +11,8) | −44,9; +38,4 | 48,2% (37,5; 59,0) |
| 5 | 41 / 41 | −28,0 (−36,8; −6,4) | −44,9; +3,7 | 68,3% (53,5; 82,2) |
| ≥6 (vị trí 6–15, gộp) | 68 / 31 | −1,6 (−18,9; +16,9) | −33,2; +59,6 | 50,0% (40,5; 59,0) |

Cách đọc:
- **Vị trí 2, 3 và 5:** trung vị âm trong các mẫu cắt ngang A0, A1b, A1, A2 và trong kịch bản loại |Y|>3. Đây là mô tả của các transition quan sát được ở từng vị trí; không phải thay đổi của cùng một franchise (xem mục 4.1, nơi phân tích trên tập cố định cho kết quả khác ở vị trí 2 và 3).
- **Vị trí 4:** chưa có chiều rõ; CI rộng và chứa 0. Không diễn giải là “phục hồi”.
- **Nhóm ≥6:** gộp nhiều vị trí (6–15), không phải “phần 6”. Chiều của trung vị không nhất quán giữa các cấu hình (mục 4.5); tỷ lệ giảm quanh 50% trong các cấu hình đã kiểm tra.
- **Phân tán lớn:** khoảng Q1–Q3 rộng hơn nhiều so với khác biệt giữa các trung vị. Biết vị trí của phim chưa cho biết mức thay đổi của một franchise cụ thể.

## 4. Trong cùng franchise, thành phần mẫu và độ vững

### 4.1. Cắt ngang so với cùng một tập franchise (PT2 rút gọn)

![Hình 2](figures/main/Hinh2_cat_ngang_vs_tap_franchise_co_dinh.png)

**Hình 2.** Mẫu A1b. Tập cố định {2,3,4}: 69 franchise có Y ở cả ba vị trí; tập {2,3,4,5}: 32 franchise. Đường xanh: trung vị % trên cùng tập (CI 95% bootstrap theo franchise); đường đỏ: bảng cắt ngang (512 / 204 / 85 / 41 transition). *Thông điệp:* trên cùng một tập franchise, trung vị ở vị trí 2 và 3 khác bảng cắt ngang (rõ nhất ở vị trí 2; CI ở vị trí 3 chứa 0). Dữ liệu: `figures/data/Hinh2_data.csv`.

**Mục đích:** kiểm tra xem khác biệt giữa các nhóm vị trí ở Mục 3 phản ánh thành phần franchise hay thay đổi trong cùng franchise. Kết quả [điểm ước lượng T5-KT; CI T5-KT cho hai ô, còn lại KẾ THỪA]:
- Tập {2,3,4} (69 franchise): vị trí 2 là +37,1% (CI +24,6; +61,7), vị trí 3 là +0,8% (CI −15,4; +12,6), vị trí 4 là +2,2%; bảng cắt ngang là −14,4%, −17,8% và +2,2%.
- Tập {2,3,4,5} (32 franchise): +50,7%, +2,4%, +10,7% và −27,9%.

Nghĩa là **không thể nói trung vị âm ở mọi cấu hình**: dấu âm ở vị trí 2 và 3 áp dụng cho bảng cắt ngang, còn trên tập franchise cố định kết quả khác. Tập cố định chỉ gồm các franchise có đủ các phim sau, tức là đã được chọn lọc, nên cũng không phải “franchise điển hình”.

### 4.2. Phép so D trong cùng franchise (PT3)

![Hình 3](figures/main/Hinh3_phep_so_D.png)

**Hình 3.** Mẫu A1b: 176 franchise có Y ở cả vị trí 2 và 3 (352 transition). (a) Phân phối D = Y(2→3) − Y(1→2), CI 95% của trung vị bằng bootstrap theo franchise; (b) Y(2→3) theo Y(1→2), mỗi chấm một franchise, đường y = x là D = 0. *Thông điệp:* mức thay đổi ở 2→3 thường thấp hơn ở 1→2, không đồng nghĩa opening phim 3 thấp hơn phim 2. Dữ liệu: `figures/data/Hinh3_data.csv`.

Kết quả [T5-KT điểm ước lượng; CI trung vị D T5-KT, chạy lại mục tiêu]: trung vị D = −0,466 (CI −0,609 đến −0,358); D<0 ở 127/176 franchise (72,2%), D>0 ở 49; trung vị Y(1→2) là +24,4% và Y(2→3) là −17,8%. Kết quả cùng chiều ở A0, A1 và A2 (trung vị D −0,465; −0,466; −0,452) và trên các tập cố định ở mục 4.1.

**D âm** nghĩa là mức thay đổi ở 2→3 thấp hơn ở 1→2. Nó **không** đồng nghĩa opening phim 3 thấp hơn phim 2: trong chính tập này Y(2→3) âm ở 62,5% franchise, không phải 100%. D dùng chung opening phim 2 (hệ số −2), nên biến động bất thường của opening phim 2 ảnh hưởng mạnh đến D. Dùng chung opening phim 2 không tự buộc D âm, nhưng cũng làm D khó đọc như một chỉ báo độc lập. D ở 3→4 là −0,165 (CI −0,361; +0,033; n=80), chưa có chiều rõ; ở 4→5 là −0,420 (CI −0,820; −0,155; n=37) [điểm ước lượng T5-KT; CI KẾ THỪA].

### 4.3. Chuỗi liên tục và đảo chiều (PT4)

Trong 58 franchise có chuỗi Y liên tục từ vị trí 2 (234 transition, ít nhất 3 transition mỗi franchise), 49/58 franchise có ít nhất một lần đảo chiều trực tiếp giữa hai transition kề nhau; 4 franchise giảm ở mọi transition và 5 tăng ở mọi transition. Tính theo cặp kề nhau, 89/176 cặp (50,6%; CI 43,4%–57,5%) đổi chiều [số đếm T5-KT; CI KẾ THỪA]. Đây là mô tả. Mức 50% chỉ là tham chiếu khi giả định dấu độc lập, không chứng minh dấu thực sự độc lập (hai transition kề nhau còn chia sẻ một opening). Chuỗi chỉ gồm franchise có dữ liệu liên tục nên không phải toàn collection và không đại diện cho mọi franchise.

### 4.4. Thành phần mẫu và chọn lọc

![Hình 4](figures/main/Hinh4_thanh_phan_mau_va_chon_loc.png)

**Hình 4.** Mẫu A1b. (a) 512 franchise có Y ở vị trí 2, chia theo việc có quan sát được Y ở vị trí 3 (176 / 67 / 258 / 11); trung vị % ở vị trí 2 kèm CI 95%. (b) Theo vị trí: tỷ lệ transition thuộc chuỗi CH (cột) và trung vị opening phim trước (đường; đơn vị chưa xác minh). *Thông điệp:* tập franchise có Y ở vị trí 3 đã khác phần còn lại ngay từ vị trí 2, và thành phần mẫu thay đổi theo vị trí. Dữ liệu: `figures/data/Hinh4a_data.csv`, `Hinh4b_data.csv`.

Các nhóm là nhóm **theo dữ liệu**, không theo nguyên nhân [số nhóm T5-KT, đối chiếu file thô]:

| Nhóm (vị trí 2, A1b) | n | Trung vị % ở vị trí 2 |
|---|---|---|
| Có Y ở vị trí 3 (mẫu PT3) | 176 | +24,4 |
| Có transition vị trí 3 trong master, thiếu opening phim 3 | 67 | −33,8 |
| Không có transition vị trí 3; collection quan sát chỉ có 2 phim | 258 | −34,9 |
| Có phim vị trí 3 bị cờ unreleased trong dữ liệu | 11 | +31,1 (CI −22,4; +159,3) |

Nhóm 11 franchise: đối chiếu đúng cặp 2→3, cả 11 cặp bị cờ `unreleased_film` và phim 3 có ngày phát hành trong dữ liệu từ 2026-11-04 đến 2028-12-13, sau ngày thu thập dữ liệu (2026-10-22) [T5-KT, đối chiếu `pairs_audit.csv` gốc]. Đây là cờ tại thời điểm dữ liệu, **không** phải tình trạng phát hành hiện tại. Với nhóm “collection chỉ có 2 phim”, điều này chỉ nói collection quan sát được có hai phim, không nói phim thứ ba không tồn tại.

Mẫu PT3 và CH đã chọn lọc rõ so với mẫu chính ở vị trí 2: trung vị +24,4% (PT3) và +47,0% (CH) so với −14,4% của toàn bộ; CH có opening phim trước lớn hơn (trung vị 21,9 triệu so với 12,3 triệu, đơn vị chưa xác minh) và không có phim thuộc thập niên 2020 ở vị trí 2 [T5-KT cho trung vị; KẾ THỪA cho thành phần thập niên]. Bảng này không giải thích nguyên nhân của khác biệt và không nói rằng cơ chế chọn lọc đã được xác định.

### 4.5. Độ vững

**Đổi mẫu (mỗi lần một thay đổi)** [điểm ước lượng T5-KT; CI chênh lệch KẾ THỪA]:

| Bước | Số transition bị loại | Đổi trung vị tối đa (điểm %) | Ghi chú |
|---|---|---|---|
| A0 → A1b | 8 | 1,51 (toàn mẫu); ≤0,70 ở vị trí 2–5 | Không đổi dấu nào |
| A1b → A1 | 3 | 0,70 ở vị trí 2–5; 2,76 ở nhóm ≥6 (chỉ 1 transition bị loại) | Không đổi dấu ở vị trí 2–5 |
| A1 → A2 | 126 | 3,15 (toàn mẫu); 3,10 ở vị trí 2; 7,21 ở ≥6 | Thay đổi thành phần quy mô: bỏ 15,5% transition ở vị trí 2; trung vị opening phim trước ở vị trí 2 tăng từ 12,4 triệu lên 17,1 triệu |

**Ngoại lệ |Y|>3** (kiểm tra bổ trợ; 44 transition, 31 ở vị trí 2) [điểm ước lượng T5-KT cho nhóm ≥6; còn lại KẾ THỪA]: bỏ chúng đổi trung vị vị trí 2 thêm +0,70 điểm %, toàn mẫu +0,14, nhóm ≥6 −6,00 (từ −1,6% xuống −7,6%). Dịch chuyển A1→A2 ở vị trí 2 là +3,10 điểm % khi giữ |Y|>3 và +2,85 khi đã bỏ |Y|>3 ở cả hai mẫu: dịch chuyển vẫn còn sau khi loại |Y|>3, nên không được giải thích hoàn toàn bởi nhóm này.

**CI chênh lệch có nhiều giá trị zero:** có cả hai cơ chế — cụm liên quan không được rút trong một số lần lặp, và trung vị không đổi dù các cặp có mặt. Không dùng CI chạm 0 như kiểm định.

![Hình 5](figures/main/Hinh5_do_vung_nhom_tu_vi_tri_6.png)

**Hình 5.** Nhóm vị trí ≥6 (A1b: 68 transition / 31 franchise; A2: 58 / 26). (a) Trung vị % theo mẫu (A0, A1b, A1, A2) và trọng số (mỗi transition ngang nhau hoặc mỗi franchise ngang nhau, 1/k_f), CI 95%; vùng tô là khoảng trung vị khi lần lượt bỏ từng franchise (A1b). (b) Tỷ lệ opening giảm. *Thông điệp:* chiều của trung vị đổi giữa âm và dương theo cấu hình; tỷ lệ giảm quanh 50%. Dữ liệu: `figures/data/Hinh5_data.csv`.

Nhóm ≥6 [điểm ước lượng và LOFO T5-KT; CI KẾ THỪA]: trung vị −1,6% (A1b, transition ngang nhau), −4,3% (A1b, franchise ngang nhau), −4,3% và −11,3% (A1), +2,9% và +4,5% (A2); bỏ từng franchise cho −7,6% đến +2,9%; bỏ |Y|>3 cho −7,6%. Tỷ lệ giảm 47,4%–51,9% ở các cấu hình có CI. Chiều của trung vị thay đổi giữa các cấu hình, nên **chưa có chiều tăng hay giảm nhất quán**.

## 5. Câu trả lời trực tiếp cho RQ3

Trong dữ liệu opening quan sát được, khi franchise tiến qua các phần:

1. Opening của phim sau **thường thấp hơn** phim trước (trung vị −15,2%; 57% transition giảm), nhưng mức thay đổi **phân tán rất rộng**: một nửa số transition nằm giữa −47,5% và +39,8%, và có cả những thay đổi rất lớn ngoài khoảng đó.
2. Theo vị trí, trung vị âm ở vị trí 2, 3 và 5 trong các bảng cắt ngang và các kịch bản đã xét; vị trí 4 chưa có chiều rõ (CI rộng, chứa 0); nhóm từ vị trí 6 trở đi không có chiều nhất quán và khoảng một nửa transition giảm.
3. Trong cùng franchise, mức thay đổi opening ở 2→3 thường thấp hơn ở 1→2 (D<0 ở 72,2% franchise có đủ ba phim đầu). Điều này không có nghĩa opening phim 3 thấp hơn phim 2.
4. Các khác biệt giữa nhóm vị trí phụ thuộc mạnh vào thành phần franchise: trên tập franchise cố định, kết quả ở vị trí 2 và 3 khác bảng cắt ngang, và các franchise có Y ở vị trí 3 đã khác phần còn lại ngay từ vị trí 2. Vì vậy các nhóm vị trí không nên đọc như “đường đi” của một franchise điển hình.
5. Đảo chiều giữa các transition kề nhau là phổ biến (49/58 franchise có ít nhất một lần; 89/176 cặp), không có mẫu hình đơn điệu nào chiếm ưu thế.

Dữ liệu này mô tả mẫu hình của các opening được ghi nhận; không chứng minh nguyên nhân và không chứng minh “sequel fatigue”.

## 6. Ý nghĩa business và giới hạn

**Dữ liệu giúp:**
- Có điểm tham chiếu thực nghiệm về mức thay đổi opening giữa hai phim liên tiếp (trung vị khoảng −15%, nhưng dải thường gặp rất rộng) để đặt kỳ vọng và biết khi nào một kịch bản “opening tăng” hay “giảm mạnh” là bình thường hay hiếm trong dữ liệu.
- Nhận ra rằng so sánh theo “phần thứ mấy” dễ gây hiểu lầm vì thành phần franchise ở từng phần khác nhau.
- Biết rằng thay đổi opening không đi theo một đường cố định: đảo chiều là phổ biến.

**Dữ liệu chưa đủ để:**
- Kết luận rằng phần nào đó “sẽ” giảm hay tăng cho một franchise cụ thể, hoặc dùng các trung vị này làm dự báo.
- Khuyến nghị sản xuất hay dừng một sequel; báo cáo không cung cấp khuyến nghị tự động nào.
- Kết luận nguyên nhân (chất lượng phim, khoảng cách giữa các phần, marketing, thị trường…) hoặc xác nhận “sequel fatigue”.

**Giới hạn cần giữ:**
- **Tính so sánh của opening chưa xác minh.** Opening trong master khớp 100% với `box_office_detailed.csv` gốc (918/918 mỗi phía) chỉ xác nhận dữ liệu được chuyển đúng; không xác nhận opening so sánh được giữa các phim. Thị trường, tiền tệ, cửa sổ opening và quan hệ phần phim vẫn chưa xác minh; giá trị là danh nghĩa (chưa điều chỉnh lạm phát).
- **Franchise là TMDB collection quan sát được**; vị trí là thứ tự phát hành trong collection, không phải số phần chính thức; độ đầy đủ của collection chưa xác minh.
- **Chọn lọc:** mẫu D, CH và tập cố định chỉ gồm franchise có thêm phim với opening; các nhóm vị trí cao gồm franchise có phim trước lớn hơn.
- **CI** chỉ phản ánh sai số lấy mẫu theo franchise, không phản ánh lỗi đo, chọn lọc hay quan hệ franchise sai; không có điều chỉnh đa so sánh và không có kiểm định giả thuyết.
- **Nhóm 11 franchise** là cờ unreleased tại thời điểm dữ liệu (2026-10-22), không phải tình trạng phát hành hiện tại.
- Nhóm ≥6 gộp 10 vị trí (6–15) với 31 franchise.

---

# Phụ lục

## A. Bảng tổng hợp phát hiện

Câu hỏi → phương pháp/mẫu → kết quả và CI → kết luận được phép → giới hạn → nguồn → mức kiểm tra ở Task 5. Bảng đầy đủ: `results/T5_findings_table.csv` / `.md` (mọi số truy được về file nguồn trong cột “Nguồn số liệu”). Loại: **Chính** (PT1), **Bổ trợ** (PT2-lite, PT3, PT4), **Thành phần / chọn lọc**, **Độ vững**.

| ID | Loại | Câu hỏi | Kết quả và CI | Kết luận được phép | Giới hạn | Mức kiểm tra ở Task 5 |
|---|---|---|---|---|---|---|
| F1 | Chính | Toàn mẫu: opening phim N so với phim N−1 thay đổi thế nào? | Trung vị Y -0.165 (-15,2%; CI -19,1% đến -7,7%); Y<0 57,0% (CI 53,8%–60,2%); Q1–Q3 -47,5% đến +39,8%. Độ nhạy: trung vị đổi tối đa 3,15 điểm % giữa A0/A1b/A1/A2 | Trong các transition quan sát được, trung vị thay đổi opening là âm và khoảng 57% transition giảm; mô tả, không nhân quả. | Số gộp chủ yếu phản ánh vị trí 2 (512/910 transition); thị trường, tiền tệ, cửa sổ opening chưa xác minh | Điểm ước lượng: T5-KT (tái tính độc lập). CI: T5-KT (đọc lại 10.000 bản lặp lưu, R2 A1b). Độ nhạy: điểm T5-KT; CI chênh lệch kế thừa. |
| F2 | Chính | Vị trí 2: opening phim N so với phim N−1 thay đổi thế nào? | Trung vị Y -0.156 (-14,4%; CI -22,1% đến -6,5%); Y<0 56,6% (CI 52,3%–60,9%); Q1–Q3 -51,6% đến +56,9%. Độ nhạy: trung vị đổi tối đa 3,1 điểm % giữa A0/A1b/A1/A2 | Trong các bảng cắt ngang A0/A1b/A1/A2 và kịch bản loại /Y/>3, trung vị vị trí 2 âm. Không đọc thành thay đổi trong cùng franchise. | Mỗi nhóm là tập franchise khác nhau; PT2 trên tập cố định cho kết quả khác (F7) | Điểm ước lượng: T5-KT (tái tính độc lập). CI: T5-KT (đọc lại 10.000 bản lặp lưu, R2 A1b). Độ nhạy: điểm T5-KT; CI chênh lệch kế thừa. |
| F3 | Chính | Vị trí 3: opening phim N so với phim N−1 thay đổi thế nào? | Trung vị Y -0.196 (-17,8%; CI -26,0% đến -10,2%); Y<0 61,8% (CI 55,2%–68,4%); Q1–Q3 -44,5% đến +27,6%. Độ nhạy: trung vị đổi tối đa 0,51 điểm % giữa A0/A1b/A1/A2 | Trong các bảng cắt ngang A0/A1b/A1/A2 và kịch bản loại /Y/>3, trung vị vị trí 3 âm. Không đọc thành thay đổi trong cùng franchise. | Như F2; tập cố định {2,3,4} cho trung vị vị trí 3 xấp xỉ +0,8% (F7) | Điểm ước lượng: T5-KT (tái tính độc lập). CI: T5-KT (đọc lại 10.000 bản lặp lưu, R2 A1b). Độ nhạy: điểm T5-KT; CI chênh lệch kế thừa. |
| F4 | Chính | Vị trí 4: opening phim N so với phim N−1 thay đổi thế nào? | Trung vị Y +0.022 (+2,2%; CI -15,8% đến +11,8%); Y<0 48,2% (CI 37,5%–59,0%); Q1–Q3 -44,9% đến +38,4%. Độ nhạy: trung vị đổi tối đa 1,32 điểm % giữa A0/A1b/A1/A2 | Chưa có chiều rõ; CI rộng và chứa 0. | CI rộng; n=85 | Điểm ước lượng: T5-KT (tái tính độc lập). CI: T5-KT (đọc lại 10.000 bản lặp lưu, R2 A1b). Độ nhạy: điểm T5-KT; CI chênh lệch kế thừa. |
| F5 | Chính | Vị trí 5: opening phim N so với phim N−1 thay đổi thế nào? | Trung vị Y -0.329 (-28,0%; CI -36,8% đến -6,4%); Y<0 68,3% (CI 53,5%–82,2%); Q1–Q3 -44,9% đến +3,7%. Độ nhạy: trung vị đổi tối đa 0,16 điểm % giữa A0/A1b/A1/A2 | Trong các bảng cắt ngang A0/A1b/A1/A2 và kịch bản loại /Y/>3, trung vị vị trí 5 âm; CI rộng (n=41). | n=41; tập cố định {2,3,4,5} (n=32) cho −27,9% ở vị trí 5 | Điểm ước lượng: T5-KT (tái tính độc lập). CI: T5-KT (đọc lại 10.000 bản lặp lưu, R2 A1b). Độ nhạy: điểm T5-KT; CI chênh lệch kế thừa. |
| F6 | Chính + độ vững | Nhóm từ vị trí 6 trở đi: chiều thay đổi? | Trung vị -1,6% (CI -18,9% đến +16,9%); Y<0 50,0%. Trung vị theo cấu hình: A2 +2,9%; A1 trọng số franchise -11,3%; bỏ từng franchise -7,6% đến +2,9% (transition ngang nhau), -11,3% đến +4,5% (franchise ngang nhau); tỷ lệ giảm 47,4%–51,9% ở các cấu hình có CI | Chiều của trung vị không nhất quán giữa các cấu hình; tỷ lệ giảm quanh 50%. | Gộp vị trí 6–15; 31 franchise (26 ở A2); CI rộng; không gọi là “phần 6” | Điểm ước lượng và LOFO: T5-KT; CI: kế thừa (không bootstrap lại) |
| F7 | Bổ trợ (PT2 rút gọn) | Khác biệt giữa các nhóm vị trí là do thành phần franchise hay thay đổi trong cùng franchise? | Tập {2,3,4}: vị trí 2 +37,1% [+24,6%; +61,7%], vị trí 3 +0,8% [-15,4%; +12,6%], vị trí 4 +2,2%; tập {2,3,4,5}: +50,7%, +2,4%, +10,7%, -27,9%. Cắt ngang A1b: -14,4%, -17,8%, +2,2%, -28,0% | Trên tập franchise cố định, trung vị ở vị trí 2 và 3 khác bảng cắt ngang; chênh lệch cắt ngang phụ thuộc mạnh vào thành phần franchise. Không nói “âm ở mọi cấu hình”. | Tập cố định chỉ gồm franchise có đủ các phim sau (chọn lọc); n nhỏ; không phải franchise điển hình | Điểm ước lượng: T5-KT. CI: T5-KT cho 2 ô (vị trí 2 cận dưới, vị trí 3 cận trên); các CI khác kế thừa |
| F8 | Bổ trợ (PT3) | Trong cùng franchise, mức thay đổi opening ở 2→3 khác 1→2 bao nhiêu? | Trung vị D -0.466 (CI -0.609 đến -0.358); D<0 72,2% (CI 65,3%–78,4%); trung vị Y(1→2) +24,4%, Y(2→3) -17,8%; Y(2→3)<0 ở 62,5% franchise. Cùng chiều ở A0/A1/A2 (trung vị D -0.465; -0.466; -0.452) | Mức thay đổi opening ở 2→3 thường thấp hơn ở 1→2 trong các franchise có opening ở cả ba phim đầu. D<0 không đồng nghĩa opening phim 3 thấp hơn phim 2. | Dùng chung opening phim 2; mẫu D chọn lọc (trung vị Y(1→2) +24,4% so với −14,4% ở toàn bộ vị trí 2); không khẳng định sequel fatigue | Điểm ước lượng: T5-KT. CI trung vị D: T5-KT (chạy lại mục tiêu 10.000 lần). Độ nhạy mẫu: điểm T5-KT |
| F9 | Bổ trợ | D ở các transition cao hơn (3→4, 4→5)? | D34 -0.165 [-0.361; +0.033]; D45 -0.420 [-0.820; -0.155] | D34: chưa có chiều rõ (CI chứa 0); D45: âm, CI rộng. | Cỡ mẫu nhỏ; chọn lọc mạnh hơn | Điểm ước lượng và n: T5-KT; CI kế thừa |
| F10 | Bổ trợ (PT4) | Trong chuỗi Y liên tục, các transition kề nhau đổi chiều thế nào? | 49/58 franchise có ≥1 đảo chiều trực tiếp; 89/176 cặp đổi chiều (50,6%; CI 43,4%–57,5%); toàn giảm 4, toàn tăng 5. Tham chiếu giả định dấu độc lập: 50,0% theo cặp | Khoảng một nửa số cặp kề nhau đổi chiều; 49/58 franchise có ít nhất một đảo chiều. Đây là mô tả; mức 50% chỉ là tham chiếu giả định, không chứng minh dấu độc lập. | CH chọn lọc (chuỗi dài); hai transition kề nhau chia sẻ một opening; không gọi là toàn collection | Số đếm (58/234, 49, 89/176, 4, 5): T5-KT. CI theo cặp: kế thừa |
| F11 | Thành phần / chọn lọc | Các franchise có Y ở vị trí 3 có giống phần còn lại ngay từ vị trí 2 không? | Trung vị vị trí 2: có Y3 +24,4%; thiếu opening phim 3 -33,8%; collection chỉ có 2 phim -34,9%; phim vị trí 3 bị cờ unreleased trong dữ liệu +31,1% (n=11, CI rộng). Mẫu PT3 +24,4% và CH +47,0% so với -14,4% toàn vị trí 2 | Tập có Y ở vị trí 3 khác tập còn lại ngay từ vị trí 2; mẫu PT3 và CH đã chọn lọc. Chưa giải thích cơ chế. | Nhóm theo dữ liệu, không theo nguyên nhân; nhóm 11 franchise là cờ unreleased tại thời điểm dữ liệu (2026-10-22), không phải tình trạng phát hành hiện tại | Số nhóm (176/67/258/11) và khoảng ngày R10c: T5-KT (đối chiếu pairs_audit.csv gốc). Trung vị: T5-KT (mẫu PT3, CH). CI: kế thừa |
| F12 | Độ vững | Kết quả có đổi theo mẫu (A0/A1b/A1/A2) và ngoại lệ không? | Đổi trung vị (điểm %): A0→A1b tối đa 1,51; A1b→A1 tối đa 2,76; A1→A2 tối đa 7,21 (A2 loại 15,5% transition ở vị trí 2). Bỏ /Y/>3: vị trí 2 +0.70 [-2.74; +3.41], nhóm ≥6 -6.00. Dịch chuyển A1→A2 ở vị trí 2: +3.10 (giữ /Y/>3) và +2.85 (đã bỏ /Y/>3 ở cả hai mẫu) | Chiều của kết quả vị trí 2, 3, 5 không đổi trong các mẫu cắt ngang và kịch bản đã xét. Dịch chuyển ở A1→A2 vẫn còn sau khi loại /Y/>3 nên không được giải thích hoàn toàn bởi nhóm này; A2 là thay đổi thành phần quy mô. | CI chênh lệch có nhiều giá trị zero do cả hai cơ chế (cụm không được rút và trung vị không đổi); không dùng làm kiểm định | Điểm ước lượng A0/A1/A2 và kịch bản /Y/>3 (nhóm ≥6): T5-KT. CI chênh lệch: kế thừa |

## B. Hình phụ lục

Các hình dưới đây là hình đã có từ bước 5–6 và Task 4, sao chép nguyên trạng (nhãn gốc), dùng để tra cứu.

| Hình | Nội dung | Mẫu | File |
|---|---|---|---|
| PL1 | Phân phối Y theo vị trí (boxplot kèm chấm) | A1b | `figures/appendix/PL1_phan_phoi_Y_theo_vi_tri_boxplot.png` |
| PL2 | Chuỗi Y của 58 franchise và các mẫu hình dấu thường gặp | A1b, CH 58/234 | `figures/appendix/PL2_chuoi_CH_va_mau_hinh_dau.png` |
| PL3 | Tỷ lệ đảo chiều theo cặp kề nhau, kèm tham chiếu giả định dấu độc lập | A1b | `figures/appendix/PL3_ty_le_dao_chieu_theo_cap.png` |
| PL4 | Chênh lệch trung vị và tỷ lệ giảm khi đổi mẫu (A0→A1b→A1→A2), CI ghép cặp | A0–A2 | `figures/appendix/PL4_do_nhay_chenh_lech_theo_cap_mau.png` |
| PL5 | Trọng số transition so với trọng số franchise ở nhóm ≥6 | A0–A2 | `figures/appendix/PL5_trong_so_nhom_tu_vi_tri_6.png` |
| PL6 | Độ phủ vị trí × thập niên | A1b | `figures/appendix/PL6_do_phu_vi_tri_x_thap_nien.png` |

Kết quả bổ trợ khác (bảng CSV): `inherited_task4_v2/results/T4_C1…C9`, `R10…`, `R5_v2…`.

## C. Kiểm tra đã chạy ở Task 5 so với kiểm tra kế thừa

**Đã chạy ở Task 5** (`code/t5_01_verify.py`, `logs/t5_01_verify_log.txt`, `results/T5_numbers_check.csv`): 198 mục, 198 khớp, 0 không khớp (chi tiết từng mục trong `results/T5_numbers_check.csv`).

| Nhóm kiểm tra | Cách làm | Trạng thái |
|---|---|---|
| PT1: n, F, trung vị, Q1, Q3, tỷ lệ giảm, số Y=0, trên 4 mẫu × 6 nhóm | Tái tính độc lập bằng pandas/numpy từ bảng transition | T5-KT |
| CI PT1 (A1b, 6 nhóm × trung vị và tỷ lệ) | Đọc lại 10.000 bản lặp lưu, tính percentile 2,5/97,5 | T5-KT |
| Trọng số 1/k_f ở ≥6 (4 mẫu), LOFO ≥6 (31 lần bỏ) | Tái tính | T5-KT |
| PT3 (A0/A1b/A1/A2), D = Y23 − Y12, trung vị Y(1→2), Y(2→3), tỷ lệ Y(2→3)<0 | Tái tính | T5-KT |
| CI trung vị D (A1b) | Chạy lại mục tiêu, cùng engine/seed/10.000 lần | T5-KT |
| PT2-lite: n, trung vị theo vị trí (2 tập), D34, D45, cắt ngang | Tái tính | T5-KT |
| CI PT2-lite: tập {2,3,4}, vị trí 2 cận dưới và vị trí 3 cận trên | Chạy lại mục tiêu | T5-KT |
| CH: 58/234, 49/58, 89/176, toàn giảm 4, toàn tăng 5 | Tái tính | T5-KT |
| |Y|>3: 44 (21 dương, 23 âm), 31 ở vị trí 2; trung vị ≥6 sau khi bỏ | Tái tính | T5-KT |
| Trung vị vị trí 2: mẫu PT3, ngoài PT3, CH, ngoài CH | Tái tính | T5-KT |
| Nhóm 11 franchise: cặp 2→3, `unreleased_film`, ngày phim 3, `retrieval_date` duy nhất (2026-10-22 ở 39.871 dòng films); số nhóm 176/67/258/11 | Đối chiếu `pairs_audit.csv`, `analysis_master_films.csv` gốc | T5-KT |

**Kế thừa, chưa tái tính ở Task 5:** CI của các phép đối chiếu mẫu (bootstrap ghép cặp, R5, T4_C4, T4_C6); CI của PT2-lite ngoài hai ô trên; CI của D34/D45 và PT3 ở A0/A1/A2; CI tỷ lệ đảo chiều; CI các nhóm quan sát (R10) và trung vị các nhóm G1, G2, G3; bảng thành phần thập niên/khoảng cách năm/quy mô (T4_C1, C1d); chẩn đoán CI zero (T4_C4); đối chiếu helper v4 (479 lần lặp đầu khớp từng lần lặp; chưa chạy đủ 10.000 lần). Những mục này giữ nhãn KẾ THỪA.

**Không chạy lại:** bootstrap toàn bộ; helper đủ 10.000 lần.

## D. Đính chính

Xem `docs/T5_dinh_chinh_nhat_ky.md`. Tóm tắt: báo cáo Task 4 v2 (mục 3.5) và `CHANGELOG_v1_to_v2.md` ghi khoảng ngày phim 3 của nhóm 11 franchise là 2026-11-04 đến 2028-10-05 (Gremlins 3). Khoảng đúng trong `R10c_G3_verification_11_franchises.csv` là **2026-11-04 đến 2028-12-13** (Black Panther 3); Gremlins 3 (2028-10-05) là phim muộn thứ hai. Chỉ là lỗi ghi trong văn bản; CSV và mọi số liệu giữ nguyên.

## E. Tái lập và bản đồ file

Xem `README.md` (file dùng cho báo cáo, thuyết trình, tái lập; đầu vào, thư viện, thứ tự chạy, seed).
