# # HỆ THỐNG CÂU HỎI KHẢO SÁT HOÀN CẢNH ĐỘNG (CONTEXT-AWARENESS)

**Mục đích:** Thu thập chính xác bối cảnh thực tế và "nỗi đau" (pain point) của đương số để tiêm (inject) vào Prompt của AI. Giúp AI đóng vai trò như một chuyên gia tâm lý: phiên dịch ý nghĩa các sao và 12 Trực khớp 100% với hoàn cảnh thực tại, luận xoáy sâu vào đúng vấn đề người dùng đang trăn trở.

**Cơ chế kích hoạt (UI/UX Routing):**

1. Hệ thống tự tính: `Tuổi = Năm xem - Năm sinh`.
2. Dựa vào `Tuổi`, UI tự động hiển thị bộ câu hỏi tương ứng (1 trong 4 nhóm).

---

## NHÓM 1: THIẾU NHI & VỊ THÀNH NIÊN (0 đến 15 tuổi)

*Ghi chú UI: Dùng danh xưng "Đương số" hoặc "Bạn nhỏ", tuyệt đối không mặc định gọi là "bé".*

**Câu 1. Hoàn cảnh hiện tại của đương số đang nghiêng về hướng nào nhất?**

[A] Ở nhà, được gia đình chăm sóc và bao bọc hoàn toàn.

[B] Sống xa nhà (Học nội trú, ở nhờ nhà họ hàng).

[C] Phải phụ giúp gia đình mưu sinh hoặc đi làm từ sớm.

**Câu 2. (Chỉ hiện nếu Câu 1 = A hoặc B) - Tình hình học tập hiện tại?**

[A1] Chưa đi học hoặc đang học mầm non.

[A2] Đang học Tiểu học / Trung học cơ sở.

**Câu 3. (Chỉ hiện nếu Câu 1 = C) - Mức độ tham gia công việc?**

[C1] Vừa đi học vừa làm thêm phụ giúp gia đình.

[C2] Đã nghỉ học hoàn toàn để đi làm kiếm tiền.



### 🔴 SUY RA (LOGIC MAPPING - NHÓM 1)

- **1A + A1 (Trẻ nhỏ ở nhà):** CẤM nói về tiền bạc, sự nghiệp. **Chương 3:** Báo cáo tập trung vào sức khỏe (tiêu hóa, hô hấp), tính nết (ngoan ngoãn hay bướng bỉnh), nguy cơ té ngã, sinh hoạt hàng ngày. **Chương 4:** "Khai trương/Ký hợp đồng" dịch thành "Bắt đầu thói quen tốt, xin người lớn mua đồ chơi/sách vở". (Người đọc hướng dẫn là cha mẹ).
- **1A + A2 (Học sinh phổ thông):** CẤM nói kinh doanh. **Chương 3:** Tập trung vào trường lớp, thi cử, bạn bè, thầy cô, tâm lý tuổi mới lớn. **Chương 4:** "Ký kết/Giao dịch" dịch thành "Thi cử, nộp bài, đăng ký ngoại khóa".
- **1B + A2 (Đi học xa nhà):** **Chương 3:** Phân tích sự tự lập, nỗi nhớ nhà, nguy cơ bị lôi kéo bên ngoài, sức khỏe khi vắng người thân chăm sóc. **Chương 4:** Nhắc nhở an toàn khi tự di chuyển, sinh hoạt tập thể.
- **1C + C1 (Vừa học vừa làm):** MỞ KHÓA khái niệm tiền bạc (nhưng dùng từ: tiền công, phụ giúp). **Chương 3:** Luận về áp lực thời gian, vất vả thể chất, học hành bị ảnh hưởng. **Chương 4:** Khuyên giữ gìn sức khỏe, cẩn thận tai nạn lao động nhẹ, không nhận thêm việc ngày xấu.
- **1C + C2 (Nghỉ học, mưu sinh sớm):** **Chương 3:** Phân tích môi trường bươn chải sớm, giá trị đồng tiền mồ hôi nước mắt, nguy cơ bị chèn ép, bóc lột hoặc tai nạn. **Chương 4:** Chuyển hóa 12 Trực thành việc nhận ca làm, nhận tiền công, giữ gìn sức khỏe. Tuyệt đối KHÔNG khuyên "đầu tư", "mở công ty" hay "ký hợp đồng kinh tế".

---



## NHÓM 2: THANH NIÊN (16 đến 22 tuổi)

*Ghi chú UI: Độ tuổi chuyển giao ranh giới học và làm, mông lung định hướng.*

**Câu 1. Trạng thái học tập và làm việc hiện tại của bạn là gì?**

[A] Đang đi học (Phổ thông / Đại học / Học nghề).

[B] Vừa học vừa đi làm thêm.

[C] Vừa tốt nghiệp, đang loay hoay tìm việc hoặc chờ định hướng.

[D] Đã thôi học hoàn toàn để đi làm toàn thời gian.

[E] Gap-year, đang nghỉ ngơi hoặc mông lung chưa rõ định hướng.

**Câu 2. (Chỉ hiện nếu Câu 1 = A hoặc B) - Môi trường sinh sống hiện tại?**

[A1] Ở trong nước.

[A2] Đang du học / Sống tại nước ngoài.



### 🔴 SUY RA (LOGIC MAPPING - NHÓM 2)

- **[A] Đang đi học:** **Chương 3:** Thi cử, đồ án, câu lạc bộ, tình cảm học đường, áp lực bài vở. (Nếu chọn A2 Du học: thêm rào cản ngôn ngữ, văn hóa, chi phí sinh hoạt xứ người). **Chương 4:** Trực tốt dùng cho nộp hồ sơ, thi cử; Trực xấu khuyên cẩn thận xe cộ.
- **[B] Vừa học vừa làm:** **Chương 3:** Áp lực kép, thiếu ngủ, quản lý thu chi cá nhân, mâu thuẫn thời gian. **Chương 4:** Không nhận ca làm thêm vào ngày trực xấu để tránh kiệt sức, sắp xếp deadline hợp lý.
- **[C] Vừa tốt nghiệp:** **Chương 3:** Áp lực đồng trang lứa (peer pressure), sự chênh vênh khi rời ghế nhà trường, rải CV, phỏng vấn. **Chương 4:** Trực tốt khuyên đi phỏng vấn, gặp nhà tuyển dụng, nhận việc đầu tiên. 
- **[D] Thôi học, đi làm sớm:** **Chương 3:** Bỏ qua chuyện trường lớp. Phân tích việc làm, lương bổng, đồng nghiệp, sự va vấp sớm với người lớn tuổi ngoài xã hội. **Chương 4:** Tập trung vào nhận ca, nhận lương, cẩn thận mâu thuẫn đồng nghiệp (Không khuyên đầu tư vốn lớn).
- **[E] Gap-year / Mông lung:** **Chương 3:** Khủng hoảng tuổi 20, hành trình tìm kiếm bản ngã, các khóa học kỹ năng mềm. **Chương 4:** Trực tốt khuyên đi trải nghiệm, chữa lành, học kỹ năng mới. Tuyệt đối không tạo áp lực phải thành đạt kiếm tiền ngay.

---



## NHÓM 3: TRƯỞNG THÀNH (23 đến 60 tuổi)

*Ghi chú UI: Nhóm chủ lực. Mở khóa toàn bộ từ vựng (Hôn nhân, Kinh doanh, Pháp lý...). Áp dụng logic Focus (Trọng tâm) để AI xoáy sâu vào "Nỗi đau".*

**Câu 1. Trạng thái công việc hiện tại của bạn là gì?**

[A] Làm công ăn lương / Nhân viên / Cấp quản lý.

[B] Làm chủ / Tự kinh doanh / Đầu tư tự do.

[C] Nội trợ / Chăm sóc gia đình toàn thời gian.

[D] Đang chuyển giao (Thất nghiệp, tìm việc mới, học chuyển ngành).

**Câu 2. Trạng thái gia đạo hiện tại ra sao?**

[A] Độc thân (Chưa có người yêu hoặc đang tìm hiểu).

[B] Đã lập gia đình / Sống chung (Chưa có con).

[C] Đã có gia đình và đang nuôi con.

[D] Độc thân nuôi con (Mẹ/Cha đơn thân).

**Câu 3. Đâu là mối bận tâm lớn nhất (ưu tiên hàng đầu) của bạn trong năm nay?**

[A] Đột phá sự nghiệp, gia tăng tài sản, khởi nghiệp hoặc trả nợ.

[B] Tìm kiếm tình yêu, cứu vãn hôn nhân, gìn giữ gia đình, lo cho con cái.

[C] Sức khỏe thể chất, chữa lành tâm lý, tìm sự bình yên.

[D] Giải quyết các rắc rối pháp lý, kiện tụng, thị phi.



### 🔴 SUY RA (LOGIC MAPPING - NHÓM 3)

*Hệ thống sẽ mix 3 đáp án lại để định hình giọng văn cho AI:*

- **1. Logic Công việc (Câu 1):**
  - **A (Làm thuê):** Thăng tiến, KPI, quan hệ Sếp/Đồng nghiệp. Trực tốt: ký HĐ lao động, đi công tác.
  - **B (Làm chủ):** Dòng vốn, đối tác, thị trường. Trực tốt: Khai trương, ký HĐ kinh tế lớn, thu hồi công nợ.
  - **C (Nội trợ):** Cấm khuyên kinh doanh/khai trương. Tập trung chi tiêu gia đình, chăm lo tổ ấm.
  - **D (Thất nghiệp/Chuyển nghề):** Bế tắc tạm thời, rải CV. Trực tốt: Phỏng vấn, rèn luyện.
- **2. Logic Gia đạo (Câu 2):**
  - **A (Độc thân):** Luận tình duyên mới, đào hoa kiếp (Không nói mâu thuẫn vợ chồng).
  - **B (Có vợ/chồng):** Luận sự đồng thuận, mâu thuẫn gia đạo, kế hoạch mua nhà/sinh con.
  - **C (Có con):** Mở khóa chủ đề "Nuôi dạy con cái", áp lực gánh vác chi phí bỉm sữa.
  - **D (Đơn thân):** Phân tích sự vất vả, cô độc khi gồng gánh tài chính một mình. Góc nhìn đồng cảm, chữa lành (Cấm khuyên "Bàn bạc với bạn đời").
- **3. Trọng số Bài luận (Câu 3 - BẮT BUỘC):**
  - **Nếu [3A] (Tiền/Sự nghiệp):** LLM dồn 70% thời lượng Chương 3 phân tích sao tại Quan Lộc, Tài Bạch. Luận kỹ dòng tiền, đầu tư.
  - **Nếu [3B] (Tình cảm/Gia đình):** Lướt qua sự nghiệp, xoáy sâu phân tích Phu Thê, Tử Tức. Dịch hóa kỵ, sát tinh thành mâu thuẫn, ly thân, hoặc tin vui con cái.
  - **Nếu [3C] (Sức khỏe/Bình yên):** Chuyển văn phong thành "Bác sĩ tâm lý", dùng cung Phúc Đức và Tật Ách làm trung tâm. Khuyên buông bỏ, bảo toàn sinh lực.
  - **Nếu [3D] (Pháp lý):** Phân tích kỹ sao Cự Môn, Thiên Hình, Liêm Trinh, Hóa Kỵ, Thái Tuế. Cảnh báo giấy tờ, hợp đồng cẩn trọng.

---



## NHÓM 4: CAO NIÊN (Trên 60 tuổi)

*Ghi chú UI: Hạn chế khuyên bon chen, mạo hiểm. Hướng về sự an bình, sức khỏe và di sản truyền lại.*

**Câu 1. Trạng thái sức khỏe và sinh hoạt hiện tại như thế nào?**

[A] Khỏe mạnh, đã nghỉ hưu, chủ yếu nghỉ ngơi vui thú điền viên.

[B] Vẫn đang điều hành công việc, kinh doanh hoặc làm việc nhẹ nhàng.

[C] Sức khỏe kém, thường xuyên đau ốm hoặc cần người chăm sóc.

**Câu 2. Hoàn cảnh chung sống hiện tại thế nào?**

[A] Sống cùng con cháu.

[B] Sống cùng bạn đời (Vợ/Chồng).

[C] Sống một mình.

**Câu 3. Điều gì khiến bác suy nghĩ và trăn trở nhiều nhất ở độ tuổi này?**

[A] Tình trạng sức khỏe, bệnh tật của bản thân hoặc bạn đời.

[B] Sự nghiệp, tài chính và hạnh phúc của thế hệ con cháu.

[C] Phân chia tài sản, đất đai, thừa kế, di sản để lại.

[D] Tu tập tâm linh, thiện nguyện, sự thanh thản trong tâm hồn.



### 🔴 SUY RA (LOGIC MAPPING - NHÓM 4)

- **1. Tình trạng chung (Câu 1 + Câu 2):**
  - **Nghỉ hưu (1A) / Ốm yếu (1C):** Cấm tuyệt đối khuyên khai trương, khởi nghiệp. Nhấn mạnh việc khám bệnh, đi lại nhẹ nhàng. Nếu sống một mình (2C), cảnh báo rủi ro té ngã không ai biết, khuyên gia nhập câu lạc bộ người cao tuổi. Nếu sống cùng bạn đời (2B), nói về sự nương tựa tuổi già.
  - **Vẫn làm việc (1B):** Phân tích việc chuyển giao quyền lực, làm cố vấn, không vắt kiệt sức.
- **2. Trọng số Bài luận (Câu 3 - BẮT BUỘC):**
  - **Nếu [3A] (Sức khỏe):** Xoáy sâu vào Tật Ách, Phúc Đức. Trạch cát ở Chương 4 chỉ luận ngày đi khám bệnh, phẫu thuật, tịnh dưỡng.
  - **Nếu [3B] (Lo cho con cháu):** Luận cung Tử Tức làm trọng tâm. Khuyên buông bỏ bớt kiểm soát, để con cháu tự lập, tránh lo âu thái quá sinh bệnh.
  - **Nếu [3C] (Di sản):** Phân tích cung Điền Trạch và Tài Bạch dưới góc độ gìn giữ và trao truyền. Bảng Trạch Cát Chương 4 ưu tiên ngày lập di chúc, sang tên sổ đỏ, họp mặt gia tộc.
  - **Nếu [3D] (Tâm linh):** Khuyên tham gia hoạt động thiện nguyện, tu tập, giải nghiệp. Trạch cát luận ngày đi lễ, phóng sinh, dọn dẹp ban thờ.

---

**[QUY TẮC TIÊM PROMPT CHO LLM (SYSTEM INSTRUCTION)]:**

Tất cả các "SUY RA" ở trên sẽ được nối thành một đoạn văn bản thực tế `<user_real_context>`.

Luôn đính kèm câu lệnh sau vào đầu Chương 3 và 4:

*"Đây là hoàn cảnh thực tế của đương số: {user_real_context}. Bạn phải đóng vai trò người phiên dịch hoàn cảnh. TUYỆT ĐỐI KHÔNG dùng từ vựng lệch khỏi bối cảnh này. Mọi phân tích và lời khuyên phải khớp 100% với ưu tiên và nỗi đau thực tại của họ."*