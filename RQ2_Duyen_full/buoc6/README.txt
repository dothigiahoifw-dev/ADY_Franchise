BƯỚC 6 — ƯỚC LƯỢNG VÀ SO SÁNH

run.py chạy M0, M1, M1 trên mẫu M2, M2, M3, M1-C và M1 trên tập giao RT. coefficients.csv ghi mọi hệ số, SE, KTC và p-value. model_summary.csv ghi n, franchise và R².

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
