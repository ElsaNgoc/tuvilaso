# PROJECT SPECIFICATION: AI TỬ VI GENERATOR (DỰA TRÊN TỬ VI ĐẨU SỐ TÂN BIÊN)

## 1. MỤC TIÊU DỰ ÁN & LƯU Ý DÀNH CHO CURSOR AI
*   **Mục tiêu:** Xây dựng một hệ thống Agentic Workflow tự động đọc dữ liệu lá số Tử Vi, đối chiếu với cơ sở tri thức (Knowledge Base) ĐỘC QUYỀN từ cuốn "Tử Vi Đẩu Số Tân Biên - Vân Đằng Thái Thứ Lang" và xuất ra báo cáo phân tích chi tiết (file Word/PDF).
*   **Lưu ý ĐẶC BIỆT cho Cursor AI:** User (người dùng) là người CHƯA CÓ KINH NGHIỆM lập trình Python. Do đó, khi yêu cầu thực hiện bất kỳ Phase nào, Cursor phải:
    1. Cung cấp câu lệnh Terminal chi tiết (cách tạo môi trường ảo, cách pip install).
    2. Giải thích rõ code này lưu ở file nào, thư mục nào.
    3. Chỉ hướng dẫn cách bấm nút "Run" hoặc gõ lệnh để chạy script.
    4. Không dùng biệt ngữ quá phức tạp.

## 2. TECH STACK & THƯ VIỆN
*   **Ngôn ngữ chính:** Python.
*   **Bóc tách PDF (PDF Parsing):** Dùng `pdfplumber` (hoặc `LlamaParse API`) để bóc tách text và xử lý các Bảng biểu phức tạp mà không bị vỡ cột/hàng.
*   **Xử lý Logic (Rule Engine):** Python thuần & Pydantic.
*   **LLM Framework:** LangChain hoặc OpenAI SDK thuần.
*   **Output:** `python-docx` để xuất file Word.

## 3. KIẾN TRÚC HỆ THỐNG VÀ WORKFLOW (CORE LOGIC)

### Bước 1: Tiền xử lý PDF & Tạo Cơ sở tri thức (Knowledge Base)
TUYỆT ĐỐI KHÔNG ném file PDF 200+ trang trực tiếp cho LLM. Code Python phải làm nhiệm vụ:
*   Trích xuất các "Bảng biểu cứng" (Ví dụ: Bảng Can Chi, Lập Cục, Bản mệnh) thành file `rules.json` (Hard Logic).
*   Trích xuất phần văn bản lý thuyết (Ví dụ: Ý nghĩa sao, 12 cung, Vận hạn) thành file `TuVi_TanBien_Data.md` (Soft Logic).

### Bước 2: Data Parsing & Rule-Based Filtering (Bộ lọc Logic)
*   Code Python đọc file `laso_input.json` của User.
*   **Xử lý mâu thuẫn (Hard-code):** Hệ thống dùng `rules.json` để kiểm tra. Nếu một cung có Sao rất đẹp nhưng dính Tuần/Triệt, code Python phải tự động gán tag là "Tốt hóa Xấu" hoặc "Trắc trở buổi đầu" để định hướng cho LLM.
*   **Tính toán bù trừ:** Áp dụng luật "Mệnh hung nhi cát, do hữu Tử cung cát".

### Bước 3: Retrieval & Strict Knowledge Confinement (Kỷ Luật Tri Thức)
Đây là chốt chặn quan trọng nhất để chống AI "ảo giác" (hallucination).
*   **Zero-Knowledge Override:** LLM CHỈ ĐƯỢC PHÉP sử dụng đoạn context được trích xuất từ `TuVi_TanBien_Data.md`. CẤM dùng kiến thức pre-trained trên Internet.
*   **System Prompt Mẫu:**
    "Bạn là một hệ thống phân tích Tử Vi chuyên nghiệp. Bạn CHỈ ĐƯỢC PHÉP tổng hợp và hành văn dựa TRÊN ĐÚNG tài liệu tham khảo được cung cấp bên dưới. [CẤM]: Tuyệt đối không sử dụng kiến thức Tử Vi bên ngoài tài liệu này. Nếu tài liệu không nhắc đến, hãy bỏ qua."
*   **Vòng lặp Prompt:** Hệ thống dùng For-loop gửi từng Prompt nhỏ (kèm Context) cho LLM để viết từng phần: (1) Tổng quan Mệnh-Thân -> (2) Từng Cung -> (3) Từng Đại hạn.

### Bước 4: Assembly & Export
*   Gộp toàn bộ văn bản từ LLM, dùng `python-docx` xuất ra file `.docx` với Headings, Bullet points trình bày đẹp mắt.

---

## 4. HƯỚNG DẪN TRIỂN KHAI TỪNG BƯỚC CHO CURSOR AI (PHASED APPROACH)
*Cursor AI hãy đọc kỹ và hướng dẫn User thực hiện tuần tự từng Phase:*

### **Phase 0: Môi trường & Setup (Cursor phải hướng dẫn User cài đặt)**
- Kiểm tra cài đặt Python, tạo Virtual Environment (`venv`).
- Tạo file `requirements.txt` và hướng dẫn chạy lệnh `pip install pdfplumber pandas pydantic python-dotenv openai python-docx`.

### **Phase 1: PDF Parser & Knowledge Base (Xử lý file 200 trang)**
- Viết file `pdf_parser.py` dùng `pdfplumber` để đọc file PDF (User sẽ cung cấp file vào thư mục).
- Hướng dẫn User cách chạy file này để trích xuất các bảng biểu thành `rules.json` và văn bản thành `TuVi_TanBien_Data.md`.

### **Phase 2: Data Modeling (Khai báo Lá Số)**
- Tạo file `models.py` chứa Pydantic models cho `Chart`, `House`, `Star`.
- Tạo file `sample_laso.json` (Nữ, sinh 1/1/2000 10h30, Bản mệnh Tuyền Trung Thủy, Cục: Kim Tứ Cục) để làm mock data.

### **Phase 3: The Rule Engine (Xử lý Mâu Thuẫn)**
- Viết file `engine.py` để xử lý logic Tuần/Triệt, Sinh/Khắc Ngũ hành, Mệnh Vô Chính Diệu trước khi gọi LLM.

### **Phase 4: LLM Integration (OpenAI/Gemini API)**
- Tích hợp API gọi LLM. Đưa System Prompt (Kỷ Luật Tri Thức) vào.
- Viết vòng lặp gửi prompt cho LLM để phân tích từng Cung.

### **Phase 5: Output Generation (Xuất Word)**
- Code logic lưu kết quả LLM trả về thành file `TuVi_Report.docx` hoàn chỉnh.

**[LỆNH BẮT ĐẦU DÀNH CHO CURSOR]:** Đóng vai trò Senior Python Developer kiêm Mentor. Đọc kỹ Project Spec này. Bắt đầu bằng **Phase 0**, hãy hướng dẫn tôi bằng Tiếng Việt cách tạo thư mục dự án, kiểm tra Python trên máy tính và cài đặt các thư viện cần thiết đi.
