# ## CẤU TRÚC REPORT ĐẦU RA BẮT BUỘC (FINAL REPORT SCHEMA)

Hệ thống Python sẽ tạo một vòng lặp gọi LLM (Gemini/OpenAI) để viết lần lượt 4 Chương sau. Mỗi chương chỉ được cung cấp Context từ các file JSON tương ứng để tránh quá tải.

### CHƯƠNG 1: TỔNG QUAN BẢN MỆNH VÀ ĐẠI CỤC

- **Dữ liệu cung cấp (Context):** tai_lieu/`knowledge_tutru.json`, luật Âm Dương/Ngũ Hành của Tân Biên.
- **Nội dung LLM cần viết:** Đúng 4 mục, mỗi gạch là một đoạn vài câu. Lời khuyên đổi theo tuổi: trẻ em chỉ sức khỏe, học hành, cha mẹ; thanh niên thì thi cử và tình cảm học trò; trưởng thành thì sự nghiệp và tiền bạc; trên 60 tuổi thì sức khỏe và con cháu.

### CHƯƠNG 2: GIẢI MÃ 12 CUNG & TƯƠNG TÁC NGẦM (NHỊ HỢP/TAM HỢP)

- **Dữ liệu cung cấp (Context):** tai_lieu/`knowledge_lucsat.json`, dữ liệu 14 Chính tinh từ Tân Biên.
- **Nội dung LLM cần viết:** Đủ 12 cung. Mỗi cung một tiêu đề, rồi 3 đoạn: thực tế cuộc sống, tam hợp bề nổi, nhị hợp bề chìm. Mỗi đoạn gọi tên sao và cung liên quan.

### CHƯƠNG 3: VẬN HẠN NĂM NAY

- **Dữ liệu cung cấp (Context):** Phần 1 dùng Lưu Thái Tuế và lưu niên tứ hóa. Phần 2 dùng 12 tháng đã tính theo mục 10.4 Tân Biên.
- **Nội dung LLM cần viết:** Viết phần 1 trước (sự kiện lớn của năm), rồi mới viết 12 tháng. Chủ đề từng tháng theo đúng nhóm tuổi, không khuyên trẻ em về tiền bạc hay đầu tư.

### CHƯƠNG 4: CẨM NANG HÀNH ĐỘNG (TRẠCH CÁT)

- **Dữ liệu cung cấp (Context):** `knowledge_trachcat.json`.
- **Nội dung LLM cần viết:**
  - Một bảng 3 cột: Tên Trực, Cát/Hung, việc nên làm và việc cấm kỵ. Cát/Hung giữ nguyên file. Việc làm được dịch sang đúng lứa tuổi trước khi ghi bảng.
  - File không ghi ngày Tý, Sửu thuộc Trực nào, nên không gán.
  - Cuối bảng: một đoạn hướng dẫn mở trang Việc nên làm hôm nay trong ứng dụng, xem Trực và việc đúng tuổi. Lịch 12 Trực chung nằm ở mục Lịch vạn niên.
