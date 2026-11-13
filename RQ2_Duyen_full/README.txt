RQ2 DUYÊN — CHIA THEO BƯỚC 3,4,5,6,7,8

Có sáu thư mục bước và sáu ZIP riêng tương ứng.
Nếu up lên Drive: up sáu ZIP RQ2_Duyen_buoc3.zip ... buoc8.zip.
Nếu chạy toàn bộ: giải nén bộ tổng, dùng sáu thư mục buoc3 ... buoc8.
python -m pip install -r buoc6/requirements.txt
python run_all.py --master "duong/dan/analysis_master_transitions.csv"

Mỗi ZIP riêng có README.txt, run.py, kết quả results và common.py nếu cần.
Master không kèm lại; dùng Master nhóm đang quản lý.
Master SHA-256 nằm trong buoc5/results/metadata.json.
Không đổi công thức target, mẫu và đặc tả đã chốt.

VALIDATION.txt ghi đối chiếu số liệu mới với ba gói đã gửi.
Để chạy lại kiểm tra đối chiếu: python verify_bundle.py, sau khi chạy run_all.py.
tai_lieu_goc.zip giữ toàn bộ file của ba gói Task 3/4/5, phục vụ truy nguồn.
Code thực thi mới theo từng bước nằm trong buoc3 ... buoc8.

Bước 8 có báo cáo Modeling đã hoàn chỉnh để review, còn chờ đối chiếu Thống kê bước 3, phản hồi Người 4 và công thức cast retention.
