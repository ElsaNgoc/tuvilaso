# Các bảng cần tạo

Database đã tạo thành file `du_lieu/tuvilaso.db`. Trang web đã nối vào file này. Đăng nhập bằng Gmail.

Tạo lại bảng (không xóa dữ liệu đã có):

    .\venv\Scripts\python.exe db.py

## Vì sao cần

Hiện lá số nằm trong file `laso/vua_dan.json`. Mỗi lần dán lá số mới, file này bị ghi đè. Bài phân tích nằm trong thư mục đặt theo ngày giờ sinh. Hai người sinh cùng ngày cùng giờ sẽ dùng chung một thư mục, bài sau đè bài trước.

Khung hỏi đáp chỉ nhớ câu hỏi khi trang còn mở. Tải lại trang là mất hết. Máy cũng chỉ đọc được lá số vừa dán, không lần lại lá số cũ.

Chỉ khi đã đăng nhập thì tên, lá số, bài phân tích và cuộc trò chuyện mới được giữ lại. Chưa đăng nhập thì vẫn dán lá số, xem bài, tải Word và hỏi trong lần mở trang đó. Đóng trang là những thứ vừa xem được xóa. Trong lúc bài còn đang viết thì chưa xóa, để người dùng còn đợi kết quả và tải file.

## Cùng một lá số, lời khuyên vẫn đổi

Lá số là ngày giờ sinh, không đổi. Lời khuyên đổi theo ngày đang xem và năm đang xem.

Lời từng ngày không lưu thành hàng trong database. Mỗi lần mở trang, máy lấy ngày hôm nay, tính Trực của ngày đó, rồi lấy tuổi của đúng người trong năm nay để viết hai câu nên làm và kiêng kỵ. Ngày mai Trực đổi, hai câu đổi theo. Sang năm tuổi tăng, câu cũng có thể đổi nhóm tuổi.

Lời từng năm là bài 4 chương. Cùng một lá số, năm 2026 một bài, năm 2027 một bài khác. Bảng `bai_phan_tich` giữ từng bài theo cột `nam_xem`.

## Biết lá số của ai

Bài dán hiện không có tên người. Chỉ có giới tính, ngày sinh, giờ sinh và nơi sinh. Hai người sinh cùng lúc sẽ không phân biệt được nếu chỉ nhìn các mục đó.

Tên chỉ lưu khi đã đăng nhập. Một tài khoản có nhiều lá số, mỗi lá số một tên, ví dụ tên từng người trong nhà. Danh sách tên chỉ hiện sau khi đăng nhập, để chọn đúng người rồi mới xem bài, xem việc hôm nay, hoặc hỏi.

Chưa đăng nhập thì không có danh sách. Lá số vừa dán chỉ sống trong lần mở trang đó.

Sách trong `tai_lieu` và bảng 12 Trực vẫn để trong file JSON. Đó là tài liệu cố định, sửa bằng tay khi cần. Không nhét vào database.

File Word vẫn để trong thư mục `output`. Database chỉ ghi đường dẫn tới file, không nhét cả file Word vào trong.

## Bảng `tai_khoan`

Một dòng là một người đăng nhập.

Cần bảng này vì chỉ tài khoản mới được giữ tên, lịch sử lá số và cuộc trò chuyện. Hai người dùng trên cùng một trang không thấy lá số của nhau.

| Cột | Giữ gì |
| --- | --- |
| ma | Số riêng của tài khoản |
| ten_dang_nhap | Gmail của người dùng |
| mat_khau | Khóa ngẫu nhiên, người dùng không gõ mật khẩu |
| email | Gmail |
| google_sub | Mã riêng Google cấp cho Gmail đó |
| luc_tao | Lúc tạo tài khoản |

Bảng `phien` nhớ lần đăng nhập. Trình duyệt giữ một mã, máy đối mã đó với tài khoản. Mật khẩu không nằm trong mã này. Đóng trình duyệt lâu ngày thì phiên hết hạn sau 30 ngày.

## Bảng `la_so`

Một dòng là một lần dán lá số.

Cần bảng này vì số thứ tự riêng không phụ thuộc ngày giờ sinh. Hai người sinh cùng lúc vẫn là hai dòng.

| Cột | Giữ gì |
| --- | --- |
| ma | Số riêng của lá số. Máy dùng số này để biết bài và câu hỏi thuộc lá số nào |
| ma_tai_khoan | Lá số này của tài khoản nào. Trống khi khách chưa đăng nhập, và dòng đó sẽ bị xóa khi đóng trang |
| ma_phien | Mã lần mở trang của khách. Dùng để chỉ xóa lá số của người vừa đóng trang, không xóa nhầm khách khác |
| ten | Tên người của lá số, chỉ giữ khi đã đăng nhập |
| luc_tao | Lúc dán vào |
| gioi_tinh | Nam hoặc Nữ |
| ngay_sinh | Ngày dương lịch |
| gio_hanh_chinh | Giờ trên giấy tờ |
| gio_mat_troi | Giờ mặt trời |
| am_lich | Ngày âm |
| noi_sinh | Nơi sinh |
| am_duong | Ví dụ Âm Nam, Dương Nữ |
| ban_menh | Bản mệnh |
| cuc | Cục |
| khoi_van_tuoi | Tuổi bắt đầu đại hạn |
| than_cu | Thân cư cung nào |
| ban_day_du | Cả lá số dạng gốc, gồm 12 cung, sao, tứ trụ, niên hóa |

Cột `ban_day_du` giữ nguyên nội dung file JSON hiện tại. Nhờ đó không mất chi tiết khi mới chuyển sang database. 12 cung chưa tách thành bảng riêng ở bước này. Khi nào cần tìm “sao này đứng ở cung nào” mà không đọc cả lá số, lúc đó mới tách thêm bảng `cung` và bảng `sao`.

## Bảng `bai_phan_tich`

Một dòng là một lần viết xong 4 chương cho một lá số.

Cần bảng này vì cùng một lá số có thể viết lại năm sau. Bài năm nay và bài năm sau phải còn cả hai. Tuổi dùng lúc viết cũng phải được ghi lại, vì lời khuyên trẻ em và người lớn khác nhau.

| Cột | Giữ gì |
| --- | --- |
| ma | Số riêng của bài |
| ma_la_so | Bài này thuộc lá số nào |
| nam_xem | Năm đang luận, ví dụ 2026 |
| tuoi | Tuổi dương lúc viết bài |
| noi_dung | Toàn bộ bài dạng chữ |
| tep_word | Đường dẫn file Word trong thư mục output |
| trang_thai | Đang viết, xong, hoặc lỗi |
| luc_xong | Lúc viết xong |

## Bảng `hoi_dap`

Một dòng là một câu trong khung hỏi về lá số. Câu của người dùng một dòng, câu của máy một dòng.

Cần bảng này vì người đã đăng nhập tải lại trang vẫn còn cuộc nói chuyện. Lần hỏi sau, máy đọc lại các câu cũ của đúng lá số đó, rồi mới trả lời. Khách chưa đăng nhập thì các câu này bị xóa khi đóng trang.

| Cột | Giữ gì |
| --- | --- |
| ma | Số riêng của câu |
| ma_la_so | Câu này hỏi về lá số nào |
| ma_bai | Câu trả lời dựa trên bài phân tích nào |
| nguoi_gui | Người dùng hoặc máy |
| noi_dung | Nội dung câu |
| luc | Lúc gửi |

## Các bảng nối với nhau thế nào

Một tài khoản có nhiều lá số. Một lá số có nhiều bài phân tích, mỗi năm một bài. Một lá số có nhiều câu hỏi. Mỗi câu hỏi trỏ về đúng lá số và đúng bài đã dùng để trả lời.

Khách chưa đăng nhập vẫn dùng được một lượt. Dòng lá số, bài và câu hỏi của khách không gắn tài khoản, và được xóa khi đóng trang.

## Chưa tạo

Bảng `cung` và bảng `sao`. Nội dung đó đang nằm trong cột `ban_day_du` của lá số. Tách sau khi cần tìm từng sao.

Bảng đoạn sách. Máy vẫn lấy đoạn sách từ file trong `tai_lieu` như hiện tại.
