BƯỚC 8 — DIỄN GIẢI VÀ BÀN GIAO

BAO_CAO_RQ2.md là báo cáo Task 5 đã sửa. run.py tạo bảng diễn giải hệ số chính và biểu đồ từ Master. Các hình bổ trợ lưu kèm để báo cáo mở được trong thư mục này. Modeling chờ review, còn chờ Thống kê bước 3, review Người 4 và xác minh cast retention.

MỖI ZIP CHẠY ĐỘC LẬP
Giải nén ZIP trước, mở terminal tại thư mục có run.py.
Cài thư viện: python -m pip install -r requirements.txt
Chạy: python run.py --master "duong/dan/analysis_master_transitions.csv"
Bước 4 có thể chạy đơn giản: python run.py
Kết quả ghi vào results cạnh run.py. Cần file Master nhóm quản lý cho các bước 3,5,6,7,8.
common.py chứa hàm tính dùng chung và được giữ trong từng ZIP để chạy độc lập.
Chạy sẽ ghi lại các kết quả do run.py tạo trong results.
Code chỉ đọc Master, không thay đổi file đó.
Dùng Python >=3.10.

Nguồn kết quả gốc: Task 3, Task 4, Task 5 do Duyên bàn giao.
Mã đã tách theo pipeline chung của RP5; số Task là mốc bàn giao, số bước là công đoạn.

THƯ MỤC doi_chieu_goc
Giữ bản nguyên gốc để tra cứu các file đã đổi tên/gộp khi tách bước.
Code vận hành theo từng bước là run.py và common.py.
Các script cũ trong doi_chieu_goc được lưu để đối chiếu nguồn, có thể phụ thuộc cấu trúc thư mục Task cũ.
