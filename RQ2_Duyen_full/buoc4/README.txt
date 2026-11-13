BƯỚC 4 — CHỌN PHƯƠNG PHÁP VÀ THIẾT KẾ

run.py xuất analysis_config.json, ghi đặc tả, ngưỡng, nhóm tham chiếu và phương pháp suy luận. Đây là cấu hình thiết kế. Lý do chọn nằm trong QUYET_DINH.md.

MỖI ZIP CHẠY ĐỘC LẬP
Giải nén ZIP trước, mở terminal tại thư mục có run.py.
Bước 4 chỉ dùng thư viện Python chuẩn.
Chạy: python run.py --master "duong/dan/analysis_master_transitions.csv"
Bước 4 có thể chạy đơn giản: python run.py
Kết quả ghi vào results cạnh run.py. Cần file Master nhóm quản lý cho các bước 3,5,6,7,8.
common.py chứa hàm tính dùng chung và được giữ trong từng ZIP để chạy độc lập.
Chạy sẽ ghi lại các kết quả do run.py tạo trong results.
Code chỉ đọc Master, không thay đổi file đó.
Dùng Python >=3.10.

Nguồn kết quả gốc: Task 3, Task 4, Task 5 do Duyên bàn giao.
Mã đã tách theo pipeline chung của RP5; số Task là mốc bàn giao, số bước là công đoạn.
