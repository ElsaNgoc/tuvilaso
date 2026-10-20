"""
The Trực (day officer) of a date and advice by age group.

Trực Kiến falls on the day whose Earthly Branch matches the month's branch.
Following days count forward: Kiến, Trừ, Mãn, Bình, Định, Chấp, Phá, Nguy, Thành, Thu, Khai, Bế.
"""

from __future__ import annotations

import json
from pathlib import Path

from han import CHI

ROOT = Path(__file__).resolve().parent
TRUC = ["Kiến", "Trừ", "Mãn", "Bình", "Định", "Chấp", "Phá", "Nguy", "Thành", "Thu", "Khai", "Bế"]

# Two sentences rewritten from knowledge_trachcat.json for each of the four age groups.
LOI = {
    "Kiến": {
        "tre": ("Nhận một việc nhỏ người lớn giao, rồi làm cho xong.", "Không bắt đầu môn học mới. Hạn chế chỗ đông, chú ý đi đứng kẻo ngã."),
        "thanh_nien": ("Giữ phần việc đã có trong nhóm học.", "Không nộp hồ sơ mới và không đi xa."),
        "truong_thanh": ("Chỉ nhận chức hoặc việc đã có sẵn.", "Không khai trương, không xuất hành, không cưới hỏi."),
        "cao_nien": ("Nhận một việc nhẹ trong nhà.", "Không đi xa và không khởi việc lớn."),
    },
    "Trừ": {
        "tre": ("Dọn đồ chơi, dọn góc học. Mệt thì nghỉ và nói với người lớn.", "Không bắt đầu việc mới khi chưa dọn xong."),
        "thanh_nien": ("Dọn chỗ học và bỏ thói quen cũ trước kỳ thi.", "Không ôm thêm hoạt động khi bài cũ chưa xong."),
        "truong_thanh": ("Dọn dẹp, chữa bệnh, bỏ việc cũ.", "Không ôm việc mới khi chưa dọn xong việc cũ."),
        "cao_nien": ("Dọn nhà vừa sức. Nếu mệt thì đi khám.", "Không bắt đầu việc nặng."),
    },
    "Mãn": {
        "tre": ("Xin người lớn mua sách vở hoặc đồ dùng học.", "Không tự ý uống thuốc."),
        "thanh_nien": ("Nộp hồ sơ thi hoặc xin tài liệu cần dùng.", "Không tự ý uống thuốc."),
        "truong_thanh": ("Cầu tài, nhận chức, cưới hỏi hoặc thu tiền.", "Không uống thuốc."),
        "cao_nien": ("Thăm họ hàng gần, nhận của đã hẹn.", "Không tự ý uống thuốc lạ."),
    },
    "Bình": {
        "tre": ("Sửa đồ dùng học và sắp lại chỗ ngồi.", "Không tự ý dọn nhà lớn hay đi chỗ lạ một mình."),
        "thanh_nien": ("Sửa bài và sắp lại lịch học.", "Không chuyển chỗ học một cách vội."),
        "truong_thanh": ("Sửa chữa, lợp mái, dời chỗ hoặc sửa đường.", "Không khởi một việc lớn mới."),
        "cao_nien": ("Sửa chỗ nhỏ trong nhà và tập dưỡng sinh nhẹ.", "Không dọn nhà quá sức và không đi xa."),
    },
    "Định": {
        "tre": ("Bắt đầu môn học mới hoặc tham gia ngoại khóa, rồi giữ đều.", "Không hứa với bạn việc quá sức."),
        "thanh_nien": ("Nộp hồ sơ thi hoặc đăng ký câu lạc bộ, rồi giữ đều.", "Không đổi nguyện vọng liên tục."),
        "truong_thanh": ("An giường, giao dịch, nạp tài hoặc ký hợp đồng dài hạn.", "Không đổi ý giữa chừng."),
        "cao_nien": ("Giữ giờ nghỉ và giờ tập dưỡng sinh cho đều.", "Không ký giấy tờ dài hạn một mình."),
    },
    "Chấp": {
        "tre": ("Làm nốt bài đang học và giữ nếp cũ.", "Hạn chế chỗ đông người, chú ý đi đứng kẻo ngã."),
        "thanh_nien": ("Làm nốt bài hoặc dự án thực tập đang dở.", "Không đi chơi xa và không đổi chỗ ở."),
        "truong_thanh": ("Xây dựng hoặc tu sửa việc đang có.", "Không xuất hành, không dời nhà, không mở tài khoản mới."),
        "cao_nien": ("Dọn nhà vừa sức và giữ nếp sinh hoạt.", "Không đi xa và không chuyển nhà."),
    },
    "Phá": {
        "tre": ("Bỏ một thói quen nhỏ chưa tốt, cất đồ hỏng.", "Không bắt đầu việc lớn và không đi chơi xa."),
        "thanh_nien": ("Bỏ kế hoạch học không còn hợp.", "Không bắt đầu dự án mới và không đi xa."),
        "truong_thanh": ("Chỉ phá dỡ nhà cũ hoặc công trình cũ.", "Không làm mọi việc lớn."),
        "cao_nien": ("Bỏ đồ hỏng và dọn một góc nhà.", "Không làm việc nặng và không đi xa."),
    },
    "Nguy": {
        "tre": ("Ở nhà làm một việc nhỏ cho xong.", "Không leo trèo, không xuống nước, chú ý đi đứng kẻo ngã."),
        "thanh_nien": ("Ở lại ôn bài, làm phần việc nhỏ.", "Không leo cao, không đi thuyền, không ký giấy tờ."),
        "truong_thanh": ("Chỉ lấp hố hoặc vá chỗ hỏng nhỏ.", "Không leo cao, không đi thuyền, không cầu tài, không ký kết."),
        "cao_nien": ("Ở nhà nghỉ, chỉ làm việc rất nhẹ.", "Không leo cao, không đi xa, không xuống nước."),
    },
    "Thành": {
        "tre": ("Bắt đầu môn học mới hoặc tham gia ngoại khóa.", "Không nhận quá nhiều việc một lúc."),
        "thanh_nien": ("Nộp hồ sơ, bắt đầu thực tập hoặc vào câu lạc bộ.", "Không nhận quá nhiều việc cùng lúc."),
        "truong_thanh": ("Khai trương, cưới hỏi, nhập học hoặc nhận chức.", "Không bỏ dở việc đang sắp xong."),
        "cao_nien": ("Đi khám bệnh hoặc thăm họ hàng gần.", "Không nhận việc mới quá sức."),
    },
    "Thu": {
        "tre": ("Xin người lớn mua sách vở, rồi cất đồ gọn.", "Không đòi quà hay tiền."),
        "thanh_nien": ("Thu bài, nhận điểm và cất tài liệu.", "Không tiêu tiền lớn."),
        "truong_thanh": ("Thu hoạch, đòi nợ, mua bảo hiểm hoặc cất của.", "Không chi tiêu lớn."),
        "cao_nien": ("Cất thuốc men, giấy tờ gọn, hoặc thăm người thân.", "Không đi xa để đòi việc."),
    },
    "Khai": {
        "tre": ("Bắt đầu môn học mới hoặc một việc mới ở lớp.", "Không tự ý đào bới và không trèo cao."),
        "thanh_nien": ("Làm quen bạn mới, vào câu lạc bộ hoặc bắt đầu thực tập.", "Không ký giấy tờ dài hạn khi chưa hỏi người lớn."),
        "truong_thanh": ("Khai trương, nhận chức, kết hôn hoặc động thổ.", "Không đóng cửa việc đang mở."),
        "cao_nien": ("Tập dưỡng sinh hoặc đi khám định kỳ.", "Không đi xa, không động thổ, không khởi việc lớn."),
    },
    "Bế": {
        "tre": ("Ở nhà nghỉ và ôn bài cũ.", "Hạn chế chỗ đông, không bắt đầu môn mới, chú ý đi đứng kẻo ngã."),
        "thanh_nien": ("Ở nhà ôn bài cũ.", "Không đi chơi đông, không nộp hồ sơ mới, không nhận việc mới."),
        "truong_thanh": ("Nghỉ và giữ việc cũ.", "Không giao dịch, không chữa bệnh, không xuất hành, không nhận chức."),
        "cao_nien": ("Ở nhà nghỉ và dọn nhẹ trong phòng.", "Không đi xa, không đi khám chỗ lạ, không nhận việc mới."),
    },
}


def nhom_tuoi(tuoi: int) -> str:
    if tuoi <= 15:
        return "tre"
    if tuoi <= 22:
        return "thanh_nien"
    if tuoi <= 60:
        return "truong_thanh"
    return "cao_nien"


def truc_cua_ngay(chi_thang: str, chi_ngay: str) -> str:
    """The day sharing the month's branch is Trực Kiến. Later days count forward around the 12 branches."""
    if chi_thang not in CHI or chi_ngay not in CHI:
        raise ValueError(f"Địa chi không hợp: tháng {chi_thang}, ngày {chi_ngay}")
    lech = (CHI.index(chi_ngay) - CHI.index(chi_thang)) % 12
    return TRUC[lech]


def doc_truc() -> dict:
    tep = ROOT / "tai_lieu" / "knowledge_trachcat.json"
    data = json.loads(tep.read_text(encoding="utf-8"))
    return data["thap_nhi_truc"]


def loi_theo_tuoi(ten_truc: str, tuoi: int) -> dict:
    bang = doc_truc()
    if ten_truc not in bang:
        raise ValueError(f"File trạch cát không có Trực {ten_truc}")
    nhom = nhom_tuoi(tuoi)
    nen, cam = LOI[ten_truc][nhom]
    return {
        "truc": ten_truc,
        "cat_hung": bang[ten_truc]["cat_hung"],
        "nen": nen,
        "cam": cam,
        "tuoi": tuoi,
        "nhom": nhom,
    }
