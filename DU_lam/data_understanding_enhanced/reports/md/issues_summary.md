| ID | Dataset | Column / Key | Finding | Priority | Status |
|---|---|---|---|---|---|
| DQ-01 | movies_raw, box_office_raw, box_office_detailed, rt_scores | production_budget, global_gross, domestic_gross, international_gross, opening_weekend_gross, critic_score, audience_score | Các biến tài chính và điểm RT thiếu rất nhiều (79,7%–91,9%; audience_score 71,5%) | HIGH | Đã xác nhận |
| DQ-02 | tất cả (liên bảng) | vote_count ~ missingness | Missingness gắn chặt với mức độ nổi tiếng (vote_count): phim nhiều vote có dữ liệu hơn hẳn | HIGH | Đã xác nhận mối liên hệ; cơ chế chưa xác định |
| DQ-03 | box_office_detailed | domestic_gross, international_gross, opening_weekend_gross | Phần lớn dòng chỉ có film_key + imdb_id ('dòng vỏ rỗng') | MEDIUM | Đã xác nhận |
| DQ-04 | box_office_detailed | theater_count | Cột rỗng 100% (0 giá trị) - báo cáo cũ không ghi nhận (ghi 5 cột) | LOW | Đã xác nhận |
| DQ-05 | movies_raw, box_office_raw, box_office_detailed | production_budget, global_gross, international_gross | Có nhiều giá trị tiền cực nhỏ (< 1.000 USD) khó phù hợp phim chiếu rạp thương mại; giả thuyết 'sai đơn vị' không được ủng hộ (gross cũng cực nhỏ), còn lại placeholder / phim vô danh - chưa chứng minh | HIGH | Dấu hiệu bất thường - cần điều tra |
| DQ-06 | box_office_raw vs box_office_detailed | global_gross vs international_gross/domestic_gross | Hai nguồn doanh thu mâu thuẫn ở một số phim | HIGH | Đã xác nhận mâu thuẫn; nguyên nhân chưa xác định |
| DQ-07 | credits_raw ↔ movies_raw | film_key | Quan hệ 1-N: join trực tiếp làm nhân dòng và nhân bội các tổng | HIGH | Rủi ro đã đo (mô phỏng) |
| DQ-08 | credits_raw | (film_key, person_id, role), billing_order | Cùng một người lặp trong cùng vai trò của cùng một phim (khác billing_order) | MEDIUM | Đã xác nhận trùng; quy tắc xử lý cần quyết định |
| DQ-09 | movies_raw | genre_ids, director_ids, lead_cast_ids_superset, production_company_ids | Trường đa trị phân tách bằng '\|' trong một ô; thứ tự không chuẩn hóa; chỉ có ID, không có tên | MEDIUM | Đã xác nhận |
| DQ-10 | movies_raw | director_ids, lead_cast_ids_superset ↔ credits_raw | director_ids là thông tin có thể suy ra từ credits_raw (trùng 100%); lead_cast_ids_superset là tập con ≤ 20 diễn viên | LOW | Đã xác nhận (đối chiếu) |
| DQ-11 | movies_raw | release_date_ref, release_month | Ngày thiếu, ngày ở tương lai so với thời điểm thu thập và dồn cụm ngày 01-01 | MEDIUM | Đã xác nhận (nguyên nhân 01-01 là giả thuyết) |
| DQ-12 | movies_raw + box_office + rt_scores | release_date_ref, tiền tệ | Thiên lệch thời gian và giá trị danh nghĩa (chưa điều chỉnh lạm phát) | MEDIUM | Đã xác nhận quan sát; cần quyết định |
| DQ-13 | rt_scores | critic_score, audience_score, rt_status, rt_url | Thiếu điểm có nhiều ý nghĩa khác nhau (không tìm thấy trên RT / có trang nhưng không có điểm) | MEDIUM | Đã xác nhận |
| DQ-14 | rt_scores | critic_score | Điểm dồn ở biên 0/100 (phim ít review - giả thuyết) | LOW | Dấu hiệu - cần dữ liệu bổ sung |
| DQ-15 | box_office_detailed | domestic_gross, opening_weekend_gross | Đa cộng tuyến rất cao giữa các biến doanh thu (đặc tính dữ liệu, không phải lỗi) | MEDIUM | Đã xác nhận (đặc tính) |
| DQ-16 | movies_raw | tmdb_collection_id | Gần như mọi phim đều có collection id; ý nghĩa của trường chưa rõ | MEDIUM | Cần điều tra |
| DQ-17 | movies_raw | title | Title trùng giữa các phim khác nhau; 1 nhóm trùng cả title lẫn ngày | LOW | Đã xác nhận / nghi vấn nhỏ |
| DQ-18 | movies_raw, box_office_raw, credits_raw, rt_scores | source, retrieval_date, market_scope, budget_missing_flag, missing_flag | Cột hằng số hoặc cờ dư thừa so với null | LOW | Đã xác nhận |
| DQ-19 | BAO_CAO cũ | số liệu thống kê trong báo cáo phiên bản trước | Một số số liệu của báo cáo cũ không khớp dữ liệu thật | HIGH | Đã xác nhận |