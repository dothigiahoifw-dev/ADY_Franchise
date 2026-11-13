| Dataset | Number of Rows | Number of Columns | Key | Unique film_key | Full-row duplicates | Missing cells % | Main Purpose |
|---|---|---|---|---|---|---|---|
| movies_raw | 39,871 | 16 | film_key | 39,871 | 0 | 11.19 | Metadata phim (TMDB): tên, ngày phát hành, ngân sách, thể loại, đạo diễn, diễn viên, hãng SX, vote_count |
| box_office_raw | 39,871 | 6 | film_key | 39,871 | 0 | 14.79 | Doanh thu toàn cầu (global_gross) từ TMDB API |
| box_office_detailed | 29,527 | 6 | film_key | 29,527 | 0 | 60.46 | Doanh thu nội địa / quốc tế / tuần mở màn (theo imdb_id) |
| credits_raw | 639,728 | 6 | film_key | 38,430 | 0 | 1.07 | Đoàn làm phim: mỗi dòng = 1 người x 1 vai trò (cast/director) x 1 phim (quan hệ 1-N) |
| rt_scores | 39,871 | 7 | film_key | 39,871 | 0 | 29.28 | Điểm Rotten Tomatoes (critic/audience) + trạng thái khớp RT |