# ## CẤU TRÚC REPORT ĐẦU RA BẮT BUỘC (FINAL REPORT SCHEMA)

Hệ thống Python sẽ tạo một vòng lặp gọi LLM (Gemini/OpenAI) để viết lần lượt 4 Chương sau. Mỗi chương chỉ được cung cấp Context từ các file JSON tương ứng để tránh quá tải.

### CHƯƠNG 1: TỔNG QUAN BẢN MỆNH VÀ ĐẠI CỤC

- **Dữ liệu cung cấp (Context):** tai_lieu/`knowledge_tutru.json`, luật Âm Dương/Ngũ Hành của Tân Biên.
- **Nội dung LLM cần viết:**
  - Phân tích Âm Dương thuận/nghịch lý.
  - Phân tích Cục và Mệnh (Ví dụ: Cục sinh Mệnh thì cuộc đời ưu ái thế nào, Mệnh khắc Cục thì nghịch cảnh ra sao).
  - Tổng quan tính cách cốt lõi dựa trên Tứ Trụ (năm, tháng, ngày, giờ).

### CHƯƠNG 2: GIẢI MÃ 12 CUNG & TƯƠNG TÁC NGẦM (NHỊ HỢP/TAM HỢP)

- **Dữ liệu cung cấp (Context):** tai_lieu/`knowledge_lucsat.json`, dữ liệu 14 Chính tinh từ Tân Biên.
- **Nội dung LLM cần viết:**
  - Quét qua 12 cung (Mệnh, Phụ Mẫu, Phúc Đức, Điền Trạch, Quan Lộc, Giao Hữu...).
  - Mỗi cung phải giải thích: Ảnh hưởng đến sự nghiệp, sức khỏe, gia đình, tiền bạc...
  - **Bắt buộc phân tích tương tác:** Sao tại bản cung chịu tác động của Tam hợp (bề nổi) và Nhị hợp/Lục hợp (bề chìm) như thế nào. (Ví dụ: Cung Nô Bộc nhị hợp cung Tử Tức -> Bạn bè và con cái có mối liên hệ ngầm gì? Bị lừa gạt hay được giúp đỡ?).

### CHƯƠNG 3: VẬN HẠN 12 THÁNG

- **Dữ liệu cung cấp (Context):** Cung và sao của từng tháng âm lịch, sao lưu đóng tại tháng đó, lục sát và đoạn chính tinh trong Tân Biên.
- **Nội dung LLM cần viết:**
  - **Dự báo 12 tháng âm lịch:** Python tính cung của từng tháng theo cách 1 mục 10.4 Tân Biên (từ tiểu hạn, đếm nghịch tới tháng sinh, rồi đếm thuận tới giờ sinh). Mỗi tháng viết 3 ý: sự nghiệp và tiền bạc, tình cảm và gia đạo, một việc nên làm và một việc tránh.

### CHƯƠNG 4: CẨM NANG HÀNH ĐỘNG (TRẠCH CÁT)

- **Dữ liệu cung cấp (Context):** `knowledge_trachcat.json`.
- **Nội dung LLM cần viết:**
  - Một bảng 3 cột: Tên Trực, Cát/Hung, việc nên làm và việc cấm kỵ. Lời khuyên ngắn, đúng ý trong file.
  - File không ghi ngày Tý, Sửu thuộc Trực nào, nên không gán.
  - Cuối bảng: một đoạn hướng dẫn mở lịch vạn niên, xem hôm nay là Trực gì, rồi dò bảng.
