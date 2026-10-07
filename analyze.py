"""
Bước 4: gọi AI viết phân tích, chỉ dựa trên sách đã tách.

Xem AI sẽ được đưa đoạn sách nào (chưa tốn tiền):
    .\\venv\\Scripts\\python.exe analyze.py --xem

Chạy thử một đoạn (tổng quan Mệnh - Thân):
    .\\venv\\Scripts\\python.exe analyze.py

Chạy đủ 4 chương, mỗi chương một lần gọi, rồi gộp thành một file Word:
    .\\venv\\Scripts\\python.exe analyze.py --laso laso\\ten_file.json --day-du

Bài ghi vào output\\năm-tháng-ngày_giờsinh\\
Trong đó có phan_tich.md và TuVi_Report.docx. Chạy lại cùng lá số thì ghi đè thư mục đó.

Viết lại bài đã có cho dễ đọc, không phân tích thêm:
    .\\venv\\Scripts\\python.exe analyze.py --viet-lai

Nếu Gemini báo quá tải, lệnh tự đợi rồi thử lại. Chạy lại cùng lệnh sẽ viết tiếp
phần còn thiếu trong thư mục của lá số đó.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from engine import phan_tich
from han import CHI, buoc, cac_nam, mot_nam, nam_sinh, viet_bang
from models import Chart, House, load_chart, thu_muc_bao_cao

ROOT = Path(__file__).resolve().parent
SACH = ROOT / "tai_lieu" / "TuVi_TanBien_Data.md"
KET_QUA = ROOT / "output" / "phan_tich.md"
LASO_PATH: Path | None = None
CHART: Chart | None = None

# Bảng trang 20: tam hợp, nhị hợp, xung. Vị trí không đổi theo cung.
TAM_HOP = (
    ("Thân", "Tý", "Thìn"),
    ("Dần", "Ngọ", "Tuất"),
    ("Tỵ", "Dậu", "Sửu"),
    ("Hợi", "Mão", "Mùi"),
)
NHI_HOP = {
    "Tý": "Sửu",
    "Sửu": "Tý",
    "Dần": "Hợi",
    "Hợi": "Dần",
    "Mão": "Tuất",
    "Tuất": "Mão",
    "Thìn": "Dậu",
    "Dậu": "Thìn",
    "Tỵ": "Thân",
    "Thân": "Tỵ",
    "Ngọ": "Mùi",
    "Mùi": "Ngọ",
}
XUNG = {
    "Tý": "Ngọ",
    "Ngọ": "Tý",
    "Sửu": "Mùi",
    "Mùi": "Sửu",
    "Dần": "Thân",
    "Thân": "Dần",
    "Mão": "Dậu",
    "Dậu": "Mão",
    "Thìn": "Tuất",
    "Tuất": "Thìn",
    "Tỵ": "Hợi",
    "Hợi": "Tỵ",
}
LOI_LIEN_HE = (
    "Sách mục 9.4: muốn xem một cung thì phải xem hai cung tam hợp, "
    "một cung xung chiếu và một cung nhị hợp. Vị trí này không đổi."
)

HE_THONG = """Bạn là một chuyên gia tư vấn Tử Vi thực tế, chân thành và logic. Nhiệm vụ của bạn là giải thích các cách cục Tử Vi bằng ngôn ngữ mộc mạc, giản dị, dễ hiểu nhất cho người bình thường.
[QUY TẮC HÀNH VĂN BẮT BUỘC]:
1. KHÔNG dùng từ ngữ hoa mỹ, sáo rỗng, hoặc các ẩn dụ văn chương (VD: tuyệt đối không dùng các cụm từ như 'chiếc rương báu', 'thanh kiếm lạnh lùng', 'dòng sông phản chiếu', 'đóa hồng gai').
2. Giải thích trực tiếp vào thực tế cuộc sống: Chỉ tập trung nói về tính cách thực, sự nghiệp, tiền bạc, và gia đình.
3. Giọng văn ngắn gọn, rõ ràng, chia ý rành mạch. Lời khuyên phải mang tính ứng dụng cao, dễ thực hiện, đời thường.

Chỉ dùng nguyên liệu trong filtered_context. Không dùng kiến thức tử vi bên ngoài. Nguyên liệu không nhắc thì bỏ qua, không bịa. Không viết dòng bắt đầu bằng dấu #."""

TRAN_TOKEN = 900

LOI_VIET_LAI = """Viết lại đoạn sau cho người không học tử vi vẫn đọc được.
Giữ nguyên tên sao, tên cung, số tuổi, năm tháng và ý đã có. Không thêm sao, không thêm việc mới.
Câu tiếng Việt thường, đoạn ngắn. Liệt kê sao thì dùng gạch đầu dòng.
Không mở đầu bằng "Dưới đây là" hay "dựa trên tài liệu"."""

TIEU_DE_MUC = re.compile(r"^(?:\d+\.)+\s+\S")


def doc_sach() -> list[tuple[str, str]]:
    muc: list[tuple[str, str]] = []
    tieu_de = ""
    dong: list[str] = []
    for raw in SACH.read_text(encoding="utf-8").splitlines():
        if raw.startswith("#"):
            continue
        if TIEU_DE_MUC.match(raw):
            if tieu_de:
                muc.append((tieu_de, "\n".join(dong).strip()))
            tieu_de = raw.strip()
            dong = []
        else:
            dong.append(raw)
    if tieu_de:
        muc.append((tieu_de, "\n".join(dong).strip()))
    return muc


def tim_muc(muc: list[tuple[str, str]], cum: str, gioi_han: int = 1400) -> str:
    """Lấy đúng mục sách có tên sao hoặc số mục, cắt ngắn để khỏi gửi cả cuốn."""
    khoa = cum.casefold().replace("ị", "ỵ").replace("kị", "kỵ")
    khop: list[tuple[str, str]] = []
    for tieu_de, than in muc:
        dau = tieu_de.casefold().replace("ị", "ỵ")
        if khoa[:1].isdigit():
            trung = dau.startswith(khoa)
        else:
            trung = re.search(rf"(?<![a-zà-ỹ]){re.escape(khoa)}(?![a-zà-ỹ])", dau) is not None
        if not trung:
            continue
        khop.append((tieu_de, than))
    if not khop:
        return ""
    # Mục 3.x là đặc tính sao. Mục 8 là cách an sao, không dùng để luận.
    dac_tinh = [item for item in khop if re.match(r"3\.\d+\.\s", item[0])]
    if dac_tinh:
        chon = dac_tinh[0]
    else:
        khac = [item for item in khop if not re.match(r"8\.\d+", item[0])]
        chon = khac[0] if khac else None
    if chon is None:
        return ""
    tieu_de, than = chon
    van = than.strip()
    if len(van) > gioi_han:
        van = van[:gioi_han].rsplit(" ", 1)[0] + "..."
    return f"{tieu_de}\n{van}".strip()


def kiem_bang_lien_he() -> None:
    """Bảng tam hợp, xung, nhị hợp phải phủ đủ 12 chi và đi hai chiều."""
    chi = {ten for bo in TAM_HOP for ten in bo}
    if chi != set(CHI) or set(XUNG) != set(CHI) or set(NHI_HOP) != set(CHI):
        raise SystemExit("Bảng liên hệ cung bị thiếu chi.")
    if any(XUNG[XUNG[ten]] != ten or NHI_HOP[NHI_HOP[ten]] != ten for ten in CHI):
        raise SystemExit("Bảng xung hoặc nhị hợp không khứ hồi.")
    for bo in TAM_HOP:
        if len(bo) != 3 or len(set(bo)) != 3:
            raise SystemExit(f"Bộ tam hợp không đủ 3 chi: {bo}")


def cung_o(chart: Chart, chi: str) -> House:
    for house in chart.cung:
        if house.vi_tri == chi:
            return house
    raise SystemExit(f"Lá số không có cung tại {chi}.")


def tom_tat(house: House) -> str:
    if house.vo_chinh_dieu:
        chinh = "vô chính diệu, xung " + ", ".join(house.sao_xung)
    else:
        chinh = ", ".join(star.ten for star in house.chinh_tinh) or "(không có chính tinh)"
    phu = ", ".join(star.ten for star in house.phu_tinh) or "(không có phụ tinh)"
    dan = []
    if house.tuan:
        dan.append("Tuần")
    if house.triet:
        dan.append("Triệt")
    if house.than_cu:
        dan.append("Thân cư")
    them = f"; {', '.join(dan)}" if dan else ""
    return f"cung {house.ten} tại {house.vi_tri}, hạn {house.dai_han}: {chinh}; phụ tinh {phu}{them}"


def uoc_token(van: str) -> int:
    """Ước lượng token theo số tiếng. Tiếng Việt tách bằng dấu cách."""
    return len(van.split())


def cat_token(van: str, tran: int) -> str:
    tu = van.split()
    if len(tu) <= tran:
        return van.strip()
    return " ".join(tu[:tran]).rstrip(".,;:") + "..."


def ghep_ngan(cac_doan: list[str], tran: int = TRAN_TOKEN) -> str:
    """Ghép các đoạn theo thứ tự ưu tiên, dừng trước mốc 1000 token."""
    chon: list[str] = []
    for doan in cac_doan:
        doan = doan.strip()
        if not doan:
            continue
        thu = "\n\n".join(chon + [doan])
        if uoc_token(thu) <= tran:
            chon.append(doan)
            continue
        da_dung = uoc_token("\n\n".join(chon)) if chon else 0
        con = tran - da_dung
        if con > 30:
            chon.append(cat_token(doan, con))
        break
    van = "\n\n".join(chon).strip()
    if uoc_token(van) > tran:
        van = cat_token(van, tran)
    return van


def ten_chinh(house: House) -> str:
    if house.vo_chinh_dieu:
        return "vô chính diệu, xung " + ", ".join(house.sao_xung)
    return ", ".join(star.ten for star in house.chinh_tinh) or "không có chính tinh"


def context_builder(
    chart: Chart,
    house: House,
    muc: list[tuple[str, str]],
    nhan_cung: list[str],
    tran: int = TRAN_TOKEN,
) -> str:
    """Tính tam hợp, xung, nhị hợp rồi chỉ lấy lý thuyết sao liên quan."""
    bo = next(nhom for nhom in TAM_HOP if house.vi_tri in nhom)
    ban = [cung_o(chart, chi) for chi in bo if chi != house.vi_tri]
    xung = cung_o(chart, XUNG[house.vi_tri])
    hop = cung_o(chart, NHI_HOP[house.vi_tri])
    dan = []
    if house.tuan:
        dan.append("Tuần")
    if house.triet:
        dan.append("Triệt")
    if house.than_cu:
        dan.append("Thân cư")
    phu = ", ".join(star.ten for star in house.phu_tinh) or "không"
    su_kien = (
        f"Cung {house.ten} tại {house.vi_tri}, đại hạn {house.dai_han}. "
        f"Chính tinh: {ten_chinh(house)}. Phụ tinh: {phu}. "
        f"Đánh dấu: {', '.join(dan) if dan else 'không'}. "
        f"Nhãn: {'; '.join(nhan_cung) if nhan_cung else 'không'}. "
        f"Tam hợp: cung {ban[0].ten} tại {ban[0].vi_tri} ({ten_chinh(ban[0])}); "
        f"cung {ban[1].ten} tại {ban[1].vi_tri} ({ten_chinh(ban[1])}). "
        f"Xung chiếu: cung {xung.ten} tại {xung.vi_tri} ({ten_chinh(xung)}). "
        f"Nhị hợp: cung {hop.ten} tại {hop.vi_tri} ({ten_chinh(hop)})."
    )
    manh = [su_kien]
    da_lay: set[str] = set()
    for ten in [star.ten for star in house.chinh_tinh] or list(house.sao_xung):
        if len(ten) < 4 or ten in da_lay:
            continue
        doan = tim_muc(muc, ten, 450)
        if not doan:
            continue
        da_lay.add(ten)
        manh.append(cat_token(doan, 110))
    if house.vo_chinh_dieu:
        vcd = tim_muc(muc, "4.1.10.", 280)
        if vcd:
            manh.append(cat_token(vcd, 70))
    for khac, vai in ((hop, "nhị hợp"), (ban[0], "tam hợp"), (ban[1], "tam hợp"), (xung, "xung chiếu")):
        sao = [star.ten for star in khac.chinh_tinh] or list(khac.sao_xung)
        for ten in sao:
            if len(ten) < 4 or ten in da_lay:
                continue
            doan = tim_muc(muc, ten, 280)
            if not doan:
                continue
            da_lay.add(ten)
            manh.append(f"Tương tác từ cung {vai} {khac.ten}:\n" + cat_token(doan, 60))
    return ghep_ngan(manh, tran)


def prompt_chuong(tieu: str, yeu_cau: str, filtered: str, tran: int) -> str:
    if uoc_token(filtered) > tran:
        filtered = cat_token(filtered, tran)
    return (
        f"Viết trọn {tieu}. Chưa viết các chương khác.\n"
        f"{yeu_cau}\n\n"
        "Dựa vào nguyên liệu thô sau đây:\n"
        "<filtered_context>\n"
        f"{filtered}\n"
        "</filtered_context>\n\n"
        f"Hãy viết {tieu} theo đúng hướng dẫn trên. Không viết dòng bắt đầu bằng dấu #."
    )


def prompt_ke_chuyen(ten_phan: str, filtered: str) -> str:
    return prompt_chuong(ten_phan, "Viết phần này.", filtered, 1000)


def token_nguyen_lieu(prompt: str) -> int:
    dau = prompt.find("<filtered_context>")
    cuoi = prompt.find("</filtered_context>")
    if dau >= 0 and cuoi > dau:
        return uoc_token(prompt[dau + len("<filtered_context>") : cuoi])
    return uoc_token(prompt)


def lien_he_cung(chart: Chart, house: House) -> str:
    bo = next(nhom for nhom in TAM_HOP if house.vi_tri in nhom)
    ban = [cung_o(chart, chi) for chi in bo if chi != house.vi_tri]
    xung = cung_o(chart, XUNG[house.vi_tri])
    hop = cung_o(chart, NHI_HOP[house.vi_tri])
    return (
        f"Tam hợp với {tom_tat(ban[0])}; và {tom_tat(ban[1])}.\n"
        f"Xung chiếu: {tom_tat(xung)}.\n"
        f"Nhị hợp: {tom_tat(hop)}."
    )


def trich_sao(muc: list[tuple[str, str]], ten_sao: list[str], gioi_han_chu: int) -> tuple[str, list[str]]:
    """Lấy mục sách của từng sao. Sao không có tiêu đề riêng được liệt kê để khỏi bịa."""
    khoi: list[str] = []
    thieu: list[str] = []
    da_gui: set[str] = set()
    for ten in ten_sao:
        if len(ten) < 4:
            if ten not in thieu:
                thieu.append(ten)
            continue
        doan = tim_muc(muc, ten, gioi_han_chu)
        if not doan:
            if ten not in thieu:
                thieu.append(ten)
            continue
        if doan not in da_gui:
            da_gui.add(doan)
            khoi.append(doan)
    return "\n\n".join(khoi), thieu


def tai_lieu_cung(
    muc: list[tuple[str, str]],
    house: House,
    chinh_chu: int = 1800,
    phu_chu: int = 600,
    kem_phu: bool = True,
) -> str:
    chinh = [star.ten for star in house.chinh_tinh] or list(house.sao_xung)
    van_chinh, thieu = trich_sao(muc, chinh, chinh_chu)
    phan = [van_chinh]
    if kem_phu:
        van_phu, thieu_phu = trich_sao(muc, [star.ten for star in house.phu_tinh], phu_chu)
        phan.append(van_phu)
        thieu.extend(thieu_phu)
    if house.vo_chinh_dieu:
        phan.append(tim_muc(muc, "4.1.10.", 1200))
    if thieu:
        phan.append(
            "Sách không có mục riêng cho: "
            + ", ".join(thieu)
            + ". Hãy nói sách không nói riêng các sao này, đừng bịa."
        )
    return "\n\n".join(doan for doan in phan if doan)


def danh_sao(houses: list[House], ca_phu: bool) -> list[str]:
    ten: list[str] = []
    for house in houses:
        nguon = list(house.chinh_tinh)
        if ca_phu:
            nguon += list(house.phu_tinh)
        for star in nguon:
            if star.ten not in ten:
                ten.append(star.ten)
        if house.vo_chinh_dieu:
            for star in house.sao_xung:
                if star not in ten:
                    ten.append(star)
    return ten


def sao_thieu(van: str, houses: list[House], ca_phu: bool, sao_them: list[str]) -> list[str]:
    thieu = []
    for ten in danh_sao(houses, ca_phu) + sao_them:
        if ten in thieu:
            continue
        if re.search(rf"(?<!\w){re.escape(ten)}(?!\w)", van, flags=re.IGNORECASE) is None:
            thieu.append(ten)
    return thieu


def mo_ta_cung(house: House, nhan: list[str]) -> str:
    if house.vo_chinh_dieu:
        chinh = "Vô chính diệu. Sao xung chiếu: " + ", ".join(house.sao_xung)
    else:
        chinh = ", ".join(star.ten for star in house.chinh_tinh) or "(không có)"
    phu = ", ".join(star.ten for star in house.phu_tinh) or "(không có)"
    dan = []
    if house.tuan:
        dan.append("Tuần")
    if house.triet:
        dan.append("Triệt")
    if house.than_cu:
        dan.append("Thân cư cung này")
    them = ", ".join(dan) if dan else "không"
    return (
        f"Cung {house.ten} tại {house.vi_tri} ({house.can_chi}). "
        f"Đại hạn {house.dai_han}. Chính tinh: {chinh}. Phụ tinh: {phu}. "
        f"Đánh dấu: {them}. Nhãn máy luật: {'; '.join(nhan) if nhan else 'không'}."
    )


@dataclass
class Viec:
    tieu: str
    noi_dung: str
    houses: list[House] = field(default_factory=list)
    goi: bool = True
    ca_phu: bool = True
    sao_them: list[str] = field(default_factory=list)
    he_thong: str = ""


def nhan_cua(nhan: dict, ten: str) -> list[str]:
    return next(item["nhan"] for item in nhan["cung"] if item["ten"] == ten)


def khoi_tong_quan(chart: Chart, nhan: dict, muc: list[tuple[str, str]]) -> Viec:
    menh = chart.cung_ten("MỆNH")
    than = chart.cung_ten(chart.than_cu)
    dong = (
        f"Đương số {chart.gioi_tinh}, {chart.am_duong}, bản mệnh {chart.ban_menh}, "
        f"cục {chart.cuc}, {nhan['ngu_hanh']}. Thân cư {chart.than_cu}."
    )
    them = ""
    if any("Mệnh hung nhi cát" in dong_nhan for dong_nhan in nhan["menh_tu"]):
        them = cat_token(tim_muc(muc, "18.1.", 300), 60)
    filtered = ghep_ngan(
        [
            dong,
            context_builder(chart, menh, muc, nhan_cua(nhan, "MỆNH"), 480),
            context_builder(chart, than, muc, nhan_cua(nhan, than.ten), 360),
            them,
        ]
    )
    houses = [menh] if menh.ten == than.ten else [menh, than]
    return Viec(
        "Tổng quan Mệnh - Thân",
        prompt_ke_chuyen("tổng quan Mệnh và Thân", filtered),
        houses,
        ca_phu=False,
    )


def khoi_tung_cung(chart: Chart, nhan: dict, muc: list[tuple[str, str]]) -> list[Viec]:
    viec: list[Viec] = []
    for house in chart.cung:
        filtered = context_builder(chart, house, muc, nhan_cua(nhan, house.ten))
        if house.ten == "MỆNH" and any("Mệnh hung nhi cát" in dong for dong in nhan["menh_tu"]):
            filtered = ghep_ngan([filtered, cat_token(tim_muc(muc, "18.1.", 300), 50)])
        viec.append(
            Viec(
                f"Cung {house.ten}",
                prompt_ke_chuyen(f"Cung {house.ten}", filtered),
                [house],
                ca_phu=False,
            )
        )
    return viec


TU_HOA = {
    "Giáp": ("Liêm Trinh", "Phá Quân", "Vũ Khúc", "Thái Dương"),
    "Ất": ("Thiên Cơ", "Thiên Lương", "Tử Vi", "Thái Âm"),
    "Bính": ("Thiên Đồng", "Thiên Cơ", "Văn Xương", "Liêm Trinh"),
    "Đinh": ("Thái Âm", "Thiên Đồng", "Thiên Cơ", "Cự Môn"),
    "Mậu": ("Tham Lang", "Thái Âm", "Hữu Bật", "Thiên Cơ"),
    "Kỷ": ("Vũ Khúc", "Tham Lang", "Thiên Lương", "Văn Khúc"),
    "Canh": ("Thái Dương", "Vũ Khúc", "Thái Âm", "Thiên Đồng"),
    "Tân": ("Cự Môn", "Thiên Lương", "Văn Khúc", "Văn Xương"),
    "Nhâm": ("Thiên Lương", "Tử Vi", "Tả Phụ", "Vũ Khúc"),
    "Qúy": ("Phá Quân", "Cự Môn", "Thái Âm", "Tham Lang"),
    "Quý": ("Phá Quân", "Cự Môn", "Thái Âm", "Tham Lang"),
}
TEN_HOA = ("Hóa Lộc", "Hóa Quyền", "Hóa Khoa", "Hóa Kỵ")
THU_MUC_TRI = ROOT / "tai_lieu"


def doc_tri_thuc(ten: str) -> dict | None:
    path = THU_MUC_TRI / ten
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def cung_co_sao(chart: Chart, ten: str) -> House | None:
    for house in chart.cung:
        if any(star.ten == ten for star in house.chinh_tinh + house.phu_tinh):
            return house
    return None


def thang_gio_sinh(chart: Chart) -> tuple[int, str]:
    van = chart.am_lich
    thang = re.search(r"tháng\s+0*(\d{1,2})", van)
    gio = re.search(r"giờ\s+(\S+)", van)
    if not thang or not gio:
        raise ValueError(f"Không đọc được tháng giờ trong '{van}'")
    ten_gio = gio.group(1).strip(".,")
    if ten_gio == "Tị":
        ten_gio = "Tỵ"
    return int(thang.group(1)), ten_gio


def luu_nguyet(chi_tieu: str, thang_sinh: int, gio_sinh: str) -> list[str]:
    """Cách 1, mục 10.4 Tân Biên.

    Cung tiểu hạn năm nay kể là tháng Giêng của bước đếm.
    Đếm nghịch, tức ngược chiều kim đồng hồ trên lá số, tới tháng sinh.
    Cung dừng lại kể là giờ Tý. Từ đó đếm thuận, cùng chiều kim đồng hồ, tới giờ sinh.
    Cung dừng lại là tháng Giêng. Tháng sau đi thuận, mỗi cung một tháng.
    """
    gio_ty = buoc(chi_tieu, thang_sinh - 1, False)
    thang_gieng = buoc(gio_ty, CHI.index(gio_sinh), True)
    cung = thang_gieng
    bang = []
    for _ in range(12):
        bang.append(cung)
        cung = buoc(cung, 1, True)
    return bang


def dong_tu_tru(chart: Chart) -> str:
    if chart.tu_tru is None:
        return "Lá số không có tứ trụ."
    dong = [f"Tiết khí {chart.tu_tru.tiet_khi}. Chiều vận tứ trụ: {chart.tu_tru.van}."]
    for cot in chart.tu_tru.cot:
        dong.append(
            f"{cot.ten}: {cot.thien_can} {cot.dia_chi}, "
            f"thập thần {cot.thap_than}, nạp âm {cot.nap_am}."
        )
    return " ".join(dong)


def nguyen_lieu_chuong_1(chart: Chart, nhan: dict) -> str:
    dac = [dong for dong in chart.dac_diem if not dong.startswith("Đường")]
    khoi = [
        f"Đương số {chart.gioi_tinh}, {chart.am_duong}, sinh {chart.am_lich}. "
        f"Bản mệnh {chart.ban_menh}. Cục {chart.cuc}. {nhan['ngu_hanh']}. "
        f"Nhãn: {'; '.join(nhan['menh_tu']) or 'không'}. "
        f"Đặc điểm: {'; '.join(dac) or 'không'}.",
        dong_tu_tru(chart),
    ]
    thien_can = doc_tri_thuc("knowledge_thiencan.json")
    if thien_can:
        khoi.append("Luật thiên can và ngũ hành:\n" + json.dumps(thien_can, ensure_ascii=False))
    tu_tru = doc_tri_thuc("knowledge_tutru.json")
    if tu_tru:
        khoi.append("Tri thức tứ trụ:\n" + json.dumps(tu_tru, ensure_ascii=False))
    else:
        khoi.append(
            "Chưa có file knowledge_tutru.json. "
            "Thập thần chỉ là nhãn trên lá số, không bịa ý nghĩa thập thần."
        )
    return ghep_ngan(khoi, 1400)


def dong_luc_sat(chart: Chart, data: dict) -> str:
    dong = [data.get("nguyen_tac_cot_loi", "")]
    for muc_sao in data.get("danh_sach_sao", []):
        ten = muc_sao["sao"]
        for house in chart.cung:
            if not any(star.ten == ten for star in house.chinh_tinh + house.phu_tinh):
                continue
            dat = house.vi_tri in muc_sao.get("dac_dia", {}).get("vi_tri", [])
            y = muc_sao["dac_dia"]["y_nghia"] if dat else muc_sao["ham_dia"]["y_nghia"]
            the = "đắc địa" if dat else "hãm địa"
            dong.append(f"{ten} tại cung {house.ten} ({house.vi_tri}), {the}: {y}")
    return "\n".join(dong for dong in dong if dong)


def nguyen_lieu_chuong_2(chart: Chart, nhan: dict, muc: list[tuple[str, str]]) -> str:
    dong_cung = []
    for house in chart.cung:
        bo = next(nhom for nhom in TAM_HOP if house.vi_tri in nhom)
        ban = [cung_o(chart, chi) for chi in bo if chi != house.vi_tri]
        hop = cung_o(chart, NHI_HOP[house.vi_tri])
        xung = cung_o(chart, XUNG[house.vi_tri])
        dan = []
        if house.tuan:
            dan.append("Tuần")
        if house.triet:
            dan.append("Triệt")
        if house.than_cu:
            dan.append("Thân cư")
        dong_cung.append(
            f"Cung {house.ten} tại {house.vi_tri}, hạn {house.dai_han}: {ten_chinh(house)}. "
            f"Đánh dấu: {', '.join(dan) or 'không'}. "
            f"Tam hợp với {ban[0].ten} ({ten_chinh(ban[0])}) và {ban[1].ten} ({ten_chinh(ban[1])}). "
            f"Nhị hợp với {hop.ten} ({ten_chinh(hop)}). "
            f"Xung {xung.ten} ({ten_chinh(xung)})."
        )
    khoi = ["\n".join(dong_cung)]
    luc = doc_tri_thuc("knowledge_lucsat.json")
    if luc:
        khoi.append("Lục sát trên lá số này:\n" + dong_luc_sat(chart, luc))
    else:
        khoi.append("Chưa có file knowledge_lucsat.json.")
    da_lay: set[str] = set()
    for house in chart.cung:
        for ten in [star.ten for star in house.chinh_tinh] or list(house.sao_xung):
            if len(ten) < 4 or ten in da_lay:
                continue
            doan = tim_muc(muc, ten, 320)
            if not doan:
                continue
            da_lay.add(ten)
            khoi.append(cat_token(doan, 70))
    if any("Mệnh hung nhi cát" in dong for dong in nhan["menh_tu"]):
        khoi.append(cat_token(tim_muc(muc, "18.1.", 240), 50))
    return ghep_ngan(khoi, 1800)


def dong_tu_hoa(chart: Chart, can: str) -> str:
    bo = TU_HOA.get(can)
    if not bo:
        return f"Không có bảng tứ hóa cho can {can}."
    dong = [f"Lưu niên tứ hóa theo can {can}, bảng mục 8.23 Tân Biên:"]
    for ten_hoa, ten_sao in zip(TEN_HOA, bo):
        house = cung_co_sao(chart, ten_sao)
        if house is None:
            dong.append(f"{ten_hoa} là {ten_sao}, sao này không có trên lá số.")
        else:
            dong.append(f"{ten_hoa} là {ten_sao}, đóng tại cung {house.ten} ({house.vi_tri}).")
    return "\n".join(dong)


def muc_hoa_ky(data: dict, can: str, sao_ky: str) -> dict | None:
    can_sach = "Qúy" if can == "Quý" else can
    for muc_sao in data.get("danh_sach_hoa_ky", []):
        if muc_sao.get("sao") == sao_ky and muc_sao.get("can_hoa_ky") in (can, can_sach):
            return muc_sao
    return None


def dong_hoa_ky(can: str, sao_ky: str) -> str:
    """Chỉ gửi Hóa Kỵ của can năm đang xem, không gửi cả tám sao trong file."""
    for ten in ("knowledge_bacphai.json", "knowledge_hoaky_trungchau.json"):
        data = doc_tri_thuc(ten)
        if not data:
            continue
        muc_sao = muc_hoa_ky(data, can, sao_ky)
        if not muc_sao:
            return (
                f"{ten} không có Hóa Kỵ của sao {sao_ky} cho can {can}. "
                "Không bịa ý nghĩa Hóa Lộc, Hóa Quyền, Hóa Khoa, Hóa Kỵ."
            )
        gon = {"nguyen_tac": data.get("nguyen_tac_cot_loi", ""), **muc_sao}
        return f"Ý Hóa Kỵ năm nay, lấy từ {ten}:\n" + json.dumps(gon, ensure_ascii=False)
    return "Chưa có file tứ hóa. Không bịa ý nghĩa Hóa Lộc, Hóa Quyền, Hóa Khoa, Hóa Kỵ."


VIEC_CUNG = {
    "MỆNH": "bản thân và cách ra quyết định",
    "PHỤ": "cha mẹ và cấp trên",
    "PHÚC": "đời sống tinh thần, họ hàng",
    "ĐIỀN": "nhà cửa, chỗ ở",
    "QUAN": "việc làm, chức vụ",
    "NÔ": "bạn bè, đồng nghiệp",
    "DI": "đi xa, ra ngoài",
    "TẬT": "sức khỏe",
    "TÀI": "tiền bạc",
    "TỬ": "con cái, cấp dưới",
    "PHỐI": "vợ chồng, đối tác",
    "BÀO": "anh em, bạn cùng trang lứa",
}

HE_THANG = """Bạn là chuyên gia tư vấn Tử Vi thực tế. Dựa trên dữ liệu các sao của từng tháng được cung cấp, hãy viết dự báo chi tiết cho 12 tháng âm lịch của năm nay.
[QUY TẮC HÀNH VĂN BẮT BUỘC]:
1. KHÔNG giải thích lý thuyết sao. Cấm viết kiểu "Tháng này có Hóa Kỵ nên..." hoặc "Sách nói sao này nghĩa là...".
2. Viết bằng ngôn ngữ đời thường, mộc mạc, đi thẳng vào vấn đề.
3. Trình bày mỗi tháng thành một mục rõ ràng. Dưới mỗi tháng bắt buộc có đúng 3 gạch đầu dòng:
- Sự nghiệp và tiền bạc: gặp thuận lợi gì, rủi ro mất tiền ở đâu.
- Tình cảm và gia đạo: có mâu thuẫn hay niềm vui gì.
- Hành động cốt lõi: một lời khuyên thực tế, cụ thể. Nên làm gì, tuyệt đối tránh làm gì trong tháng này.
Chỉ dùng nguyên liệu trong filtered_context. Không bịa sao, không đổi tháng sang cung khác. Không viết dòng bắt đầu bằng dấu #."""


def nguyen_lieu_chuong_3(chart: Chart, _nhan: dict, muc: list[tuple[str, str]]) -> str:
    """12 tháng âm lịch, mỗi tháng kèm sao đang đóng tại cung đó."""
    _, _, nam_goc = nam_sinh(chart)
    nam_nay = 2026
    tuoi = nam_nay - nam_goc + 1
    nam = mot_nam(chart, tuoi, nam_nay)
    thang_sinh, gio_sinh = thang_gio_sinh(chart)
    cac_thang = luu_nguyet(nam["tieu_han"].vi_tri, thang_sinh, gio_sinh)
    can = nam["can_chi"].split()[0]
    bo = TU_HOA.get(can, ())
    hoa: dict[str, tuple[str, House]] = {}
    for ten_hoa, ten_sao in zip(TEN_HOA, bo):
        nha = cung_co_sao(chart, ten_sao)
        if nha is not None:
            hoa[ten_hoa] = (ten_sao, nha)
    dong = [
        f"Năm {nam['nam']} {nam['can_chi']}, tuổi {nam['tuoi']}. "
        f"Tiểu hạn tại cung {nam['tieu_han'].ten} ({nam['tieu_han'].vi_tri}) là mốc đếm tháng Giêng. "
        f"Tháng sinh {thang_sinh}, giờ sinh {gio_sinh}. "
        "12 tháng dưới đây đã tính xong. Viết đúng cung của từng tháng."
    ]
    sao_chinh: list[str] = []
    for so, chi in enumerate(cac_thang, start=1):
        house = cung_o(chart, chi)
        luu = [ten for ten, nha in nam["sao_luu"].items() if nha.vi_tri == chi]
        hoa_o = [f"{ten_hoa} là {ten_sao}" for ten_hoa, (ten_sao, nha) in hoa.items() if nha.vi_tri == chi]
        dong.append(
            f"Tháng {so}: cung {house.ten} tại {chi}. Việc của cung: {VIEC_CUNG.get(house.ten, 'việc của cung này')}. "
            f"{tom_tat(house)}. "
            f"Sao lưu năm nay tại đây: {', '.join(luu) or 'không'}. "
            f"Tứ hóa năm nay tại đây: {', '.join(hoa_o) or 'không'}."
        )
        sao_chinh.extend(star.ten for star in house.chinh_tinh)
        if house.vo_chinh_dieu:
            sao_chinh.extend(house.sao_xung)
    khoi = ["\n".join(dong)]
    luc = doc_tri_thuc("knowledge_lucsat.json")
    if luc:
        khoi.append("Ý lục sát, chỉ áp vào tháng có sao đó:\n" + dong_luc_sat(chart, luc))
    da_lay: set[str] = set()
    for ten in sao_chinh:
        if len(ten) < 4 or ten in da_lay:
            continue
        doan = tim_muc(muc, ten, 280)
        if not doan:
            continue
        da_lay.add(ten)
        khoi.append(cat_token(doan, 40))
    if bo:
        khoi.append(dong_hoa_ky(can, bo[3]))
    return ghep_ngan(khoi, 1800)


def nguyen_lieu_chuong_4(_chart: Chart) -> str:
    trach = doc_tri_thuc("knowledge_trachcat.json")
    if not trach or not trach.get("thap_nhi_truc"):
        return (
            "Chưa có file knowledge_trachcat.json. "
            "Dừng bài. Không viết dự báo 12 tháng, không lập ngày Tý Sửu, không bịa việc nên làm."
        )
    dong = [
        "12 Trực lấy từ knowledge_trachcat.json. "
        "File không ghi ngày Tý, Sửu, Dần, Mão, Thìn, Tỵ, Ngọ, Mùi, Thân, Dậu, Tuất, Hợi thuộc Trực nào. "
        "Không được tự gán Trực cho những ngày đó."
    ]
    for ten, muc_truc in trach["thap_nhi_truc"].items():
        dong.append(f"Trực {ten} ({muc_truc.get('cat_hung', '')}): {muc_truc.get('y_nghia', '')}")
    return ghep_ngan(dong, 1400)


def khoi_bon_chuong(chart: Chart, nhan: dict, muc: list[tuple[str, str]]) -> list[Viec]:
    kiem_bang_lien_he()
    yeu_cau = [
        (
            "Chương 1: Tổng quan bản mệnh và đại cục",
            "Phân tích âm dương thuận hay nghịch. Phân tích Cục và Mệnh: Cục sinh Mệnh thì cuộc đời được nâng thế nào, "
            "Mệnh khắc Cục thì nghịch cảnh ra sao. Tổng quan tính cách cốt lõi từ bốn trụ năm, tháng, ngày, giờ, "
            "chỉ bằng luật ngũ hành đã cho.",
            nguyen_lieu_chuong_1(chart, nhan),
            1400,
            "",
        ),
        (
            "Chương 2: Giải mã 12 cung và tương tác ngầm",
            "Đi lần lượt 12 cung. Mỗi cung một đoạn về sự nghiệp, sức khỏe, gia đình hoặc tiền bạc, đúng việc của cung đó. "
            "Bắt buộc nói tam hợp là bề nổi và nhị hợp là bề chìm tác động lên sao tại bản cung như thế nào. "
            "Không liệt kê lý thuyết từng sao.",
            nguyen_lieu_chuong_2(chart, nhan, muc),
            1800,
            "",
        ),
        (
            "Chương 3: Vận hạn 12 tháng",
            "Viết dự báo đủ 12 tháng âm lịch, đúng cung đã tính trong nguyên liệu.\n"
            "Không giải thích lý thuyết sao. Cấm viết 'Tháng này có Hóa Kỵ nên...' hoặc 'Sách nói sao này nghĩa là...'.\n"
            "Ngôn ngữ đời thường, mộc mạc, đi thẳng vào việc.\n"
            "Mỗi tháng một mục. Dưới mỗi tháng bắt buộc có đúng 3 gạch đầu dòng:\n"
            "- Sự nghiệp và tiền bạc: gặp thuận lợi gì, rủi ro mất tiền ở đâu.\n"
            "- Tình cảm và gia đạo: có mâu thuẫn hay niềm vui gì.\n"
            "- Hành động cốt lõi: một lời khuyên thực tế. Nên làm gì, tuyệt đối tránh làm gì trong tháng này.",
            nguyen_lieu_chuong_3(chart, nhan, muc),
            1800,
            HE_THANG,
        ),
        (
            "Chương 4: Cẩm nang hành động",
            "Dựa vào 12 Trực trong nguyên liệu, tạo một bảng tra cứu nhanh ngày tốt xấu.\n"
            "Trình bày bằng bảng Markdown đúng 3 cột: Tên Trực | Cát/Hung | Việc nên làm và việc cấm kỵ.\n"
            "Mỗi Trực một dòng. Lời khuyên cực ngắn, chỉ việc file đã nói. "
            "Ví dụ cách viết: 'Tuyệt đối không ký hợp đồng', 'Tốt để đòi nợ'.\n"
            "File không ghi ngày Tý, Sửu thuộc Trực nào. Không được gán.\n"
            "Cuối bảng viết một đoạn ngắn: người đọc mở lịch vạn niên, xem hôm nay là Trực gì, rồi dò đúng dòng trong bảng để biết nên làm gì và tránh gì.",
            nguyen_lieu_chuong_4(chart),
            1400,
            "",
        ),
    ]
    return [
        Viec(tieu, prompt_chuong(tieu, cau, filtered, tran), goi=True, ca_phu=False, he_thong=he)
        for tieu, cau, filtered, tran, he in yeu_cau
    ]


def tao_viec(chart: Chart, nhan: dict, muc: list[tuple[str, str]], day_du: bool) -> list[Viec]:
    chuong = khoi_bon_chuong(chart, nhan, muc)
    if day_du:
        return chuong
    return chuong[:1]


def goi_openai(system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    tra_loi = client.chat.completions.create(
        model=model,
        temperature=0.7,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return tra_loi.choices[0].message.content or ""


class ThuLai(Exception):
    """Gemini bận hoặc model này không gọi được. Thử lại hoặc đổi model."""

    def __init__(self, code: int, thong_bao: str, doi_model: bool = False):
        super().__init__(thong_bao)
        self.code = code
        self.doi_model = doi_model


CHO_LAI = (12, 25, 45, 70)
MODEL_DU_PHONG = ("gemini-3.1-flash-lite", "gemini-3.5-flash-lite")


def goi_gemini_mot_lan(system: str, user: str, model: str, co_suy_nghi: bool) -> str:
    key = os.environ["GEMINI_API_KEY"]
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={key}"
    )
    cau_hinh: dict = {"temperature": 0.7}
    if co_suy_nghi:
        cau_hinh["thinkingConfig"] = {"thinkingLevel": "low"}
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": cau_hinh,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as loi:
        chi_tiet = loi.read().decode("utf-8", errors="replace")
        if loi.code in (429, 500, 503):
            raise ThuLai(loi.code, chi_tiet) from loi
        if loi.code == 404:
            raise ThuLai(loi.code, chi_tiet, doi_model=True) from loi
        if loi.code == 400 and co_suy_nghi and "thinking" in chi_tiet.casefold():
            raise ThuLai(loi.code, chi_tiet) from loi
        if loi.code in (400, 401, 403):
            raise SystemExit(
                f"Gemini từ chối (mã {loi.code}).\n{chi_tiet}\n"
                "Xem lại dòng GEMINI_API_KEY trong file .env."
            ) from loi
        raise ThuLai(loi.code, chi_tiet, doi_model=True) from loi
    except (urllib.error.URLError, TimeoutError) as loi:
        raise ThuLai(0, str(loi)) from loi
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as loi:
        raise ThuLai(0, json.dumps(data, ensure_ascii=False)[:500]) from loi
    chu = [p["text"] for p in parts if p.get("text") and not p.get("thought")]
    if not chu:
        chu = [p["text"] for p in parts if p.get("text")]
    if not chu:
        raise ThuLai(0, "Gemini trả về rỗng.")
    return "\n".join(chu).strip()


def goi_gemini(system: str, user: str) -> str:
    chinh = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    danh_sach = [chinh]
    for phu in MODEL_DU_PHONG:
        if phu not in danh_sach:
            danh_sach.append(phu)
    loi_cuoi = ""
    for thu_tu, model in enumerate(danh_sach):
        # Model chính đông người thì đổi sang model nhẹ sau một lần đợi ngắn.
        # Model dự phòng mới đợi lâu hơn, vì đó là đường còn lại.
        cho = (15,) if thu_tu == 0 else CHO_LAI
        co_suy_nghi = True
        for lan, giay in enumerate((0, *cho), start=1):
            if giay:
                print(f"  {model} đang bận. Đợi {giay} giây rồi thử lại (lần {lan}).", flush=True)
                time.sleep(giay)
            try:
                return goi_gemini_mot_lan(system, user, model, co_suy_nghi)
            except ThuLai as loi:
                loi_cuoi = str(loi)
                if loi.code == 400 and co_suy_nghi:
                    co_suy_nghi = False
                    print(f"  {model} không nhận cấu hình suy nghĩ. Gọi lại ngay.", flush=True)
                    try:
                        return goi_gemini_mot_lan(system, user, model, False)
                    except ThuLai as loi_moi:
                        loi = loi_moi
                        loi_cuoi = str(loi_moi)
                if loi.doi_model:
                    print(f"  Bỏ {model}, chuyển model khác.", flush=True)
                    break
                print(f"  Quá tải mã {loi.code} với {model}.", flush=True)
        else:
            print(f"  {model} vẫn bận. Chuyển model khác.", flush=True)
    raise SystemExit(
        "Gemini vẫn quá tải sau nhiều lần đợi.\n"
        f"Phần đã viết vẫn nằm trong {KET_QUA}.\n"
        "Chạy lại đúng lệnh cũ, chương trình sẽ viết tiếp phần còn thiếu.\n"
        f"Lỗi cuối: {loi_cuoi[:400]}"
    )


def goi_ai(system: str, user: str) -> str:
    if os.environ.get("OPENAI_API_KEY"):
        return goi_openai(system, user)
    if os.environ.get("GEMINI_API_KEY"):
        return goi_gemini(system, user)
    raise SystemExit(
        "Chưa có khóa API.\n"
        "Tạo file .env trong thư mục dự án, rồi ghi MỘT dòng:\n"
        "    GEMINI_API_KEY=khoa_cua_ban\n"
        "hoặc:\n"
        "    OPENAI_API_KEY=sk-...\n"
        "Xem mẫu trong file .env.example."
    )


def cat_sach(bat_dau: str, ket_thuc: str, gioi_han: int = 1400) -> str:
    van = SACH.read_text(encoding="utf-8")
    i = van.find(bat_dau)
    if i < 0:
        return ""
    j = van.find(ket_thuc, i + len(bat_dau))
    doan = van[i : j if j > i else i + gioi_han]
    doan = doan.strip()
    if len(doan) > gioi_han:
        doan = doan[:gioi_han].rsplit(" ", 1)[0] + "..."
    return doan


def tai_lieu_han() -> str:
    mau = [
        ("10.2. Lưu đại hạn", "10.3.", 900),
        ("10.3. Lưu niên tiểu hạn", "10.4.", 900),
        ("2.1. Liên hệ giữa đại hạn và tiểu hạn", "2.2.", 900),
        ("2.3. Liên hệ giữa Bản Mệnh và cung nhập hạn", "2.4.", 1200),
        ("4.1. Lưu Thái Tuế, Lưu Tang Môn, Lưu Bạch Hổ", "4.2.", 900),
        ("4.2. Lưu Thiên Khốc, Lưu Thiên Hư", "4.3.", 800),
        ("4.3. Lưu Lộc Tồn, Lưu Kình Dương, Lưu Đà La", "4.4.", 900),
        ("4.4. Lưu Thiên Mã", "5. LUẬN ĐOÁN CHẾT", 700),
    ]
    return "\n\n".join(doan for doan in (cat_sach(*muc) for muc in mau) if doan)


def prompt_mot_nam(chart: Chart, nhan: dict, muc: list[tuple[str, str]], nam: dict) -> str:
    houses: list[House] = []
    for house in (nam["goc"], nam["luu_dai_han"], nam["tieu_han"]):
        if house.ten not in {item.ten for item in houses}:
            houses.append(house)
    sao = "; ".join(f"{ten} tại cung {house.ten} ({house.vi_tri})" for ten, house in nam["sao_luu"].items())
    trung = "; ".join(nam["trung"]) or "không có sao lưu trùng sao cố định cùng tên"
    dong = (
        f"Năm {nam['nam']} {nam['can_chi']}, tuổi {nam['tuoi']}. "
        f"Đại hạn mười năm tại cung {nam['goc'].ten} ({nam['goc'].vi_tri}), hạn {nam['goc'].dai_han}. "
        f"Lưu đại hạn tại cung {nam['luu_dai_han'].ten} ({nam['luu_dai_han'].vi_tri}). "
        f"Tiểu hạn tại cung {nam['tieu_han'].ten} ({nam['tieu_han'].vi_tri}). "
        f"Sao lưu: {sao}. Chỗ trùng: {trung}."
    )
    manh = [dong]
    phan = 220
    for house in houses:
        manh.append(context_builder(chart, house, muc, nhan_cua(nhan, house.ten), phan))
    return prompt_ke_chuyen(f"năm {nam['nam']} tuổi {nam['tuoi']}", ghep_ngan(manh))


CACH_VIET = "Cách viết: 4 chương, 12 thang"
TIEU_CHUONG = (
    "Chương 1: Tổng quan bản mệnh và đại cục",
    "Chương 2: Giải mã 12 cung và tương tác ngầm",
    "Chương 3: Vận hạn 12 tháng",
    "Chương 4: Cẩm nang hành động",
)


def chuan_van(van: str) -> str:
    """Bỏ tiêu đề chương do model tự thêm, để khi ghép không bị tách nhầm."""
    dong = []
    for raw in van.splitlines():
        chu = raw.strip()
        if chu.startswith("#"):
            chu = chu.lstrip("#").strip()
            if chu.lower().startswith("chương"):
                continue
            if chu:
                dong.append(chu)
            continue
        dong.append(raw)
    return "\n".join(dong).strip()


def sap_chuong(cac_phan: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Luôn xếp Chương 1, 2, 3 rồi mới đến Chương 4."""
    theo_ten = {tieu: chuan_van(van) for tieu, van in cac_phan}
    thu_tu: list[tuple[str, str]] = []
    da_ghi: set[str] = set()
    for tieu in TIEU_CHUONG:
        if tieu in theo_ten:
            thu_tu.append((tieu, theo_ten[tieu]))
            da_ghi.add(tieu)
    for tieu, van in cac_phan:
        if tieu not in da_ghi:
            thu_tu.append((tieu, chuan_van(van)))
            da_ghi.add(tieu)
    return thu_tu


def ghi_bai(cac_phan: list[tuple[str, str]]) -> None:
    KET_QUA.parent.mkdir(parents=True, exist_ok=True)
    dong = ["# Phân tích lá số", ""]
    if CHART is not None:
        dong.append(
            f"Sinh ngày {CHART.ngay_sinh}, giờ {CHART.gio_hanh_chinh}. "
            f"{CHART.gioi_tinh}, {CHART.am_duong}."
        )
        dong.append(CACH_VIET)
        dong.append("")
    for tieu_de, van in sap_chuong(cac_phan):
        dong.append(f"## {tieu_de}")
        dong.append("")
        dong.append(van.strip())
        dong.append("")
    KET_QUA.write_text("\n".join(dong).rstrip() + "\n", encoding="utf-8")


def dung_kieu_ke() -> bool:
    """Bài cũ viết theo kiểu liệt kê thì không nối tiếp, để viết lại bằng prompt kể chuyện."""
    if not KET_QUA.is_file():
        return False
    dau = "\n".join(KET_QUA.read_text(encoding="utf-8").splitlines()[:8])
    return CACH_VIET in dau


def doc_bai_cu() -> dict[str, str]:
    """Đọc các phần đã viết để lần chạy sau nối tiếp, không gọi lại AI."""
    if not KET_QUA.is_file():
        return {}
    van = KET_QUA.read_text(encoding="utf-8")
    da_co: dict[str, str] = {}
    khop = list(re.finditer(r"(?m)^## (Chương \d+:.+)$", van))
    for i, moc in enumerate(khop):
        tieu_de = moc.group(1).strip()
        dau = moc.end()
        cuoi = khop[i + 1].start() if i + 1 < len(khop) else len(van)
        than = chuan_van(van[dau:cuoi])
        if tieu_de and than:
            da_co[tieu_de] = than
    return da_co


def chay_han(chart: Chart, nhan: dict, muc: list[tuple[str, str]], chi_xem: bool) -> None:
    _, _, nam_goc = nam_sinh(chart)
    nam_nay = 2026
    tuoi_nay = nam_nay - nam_goc + 1
    tuoi_dau = (tuoi_nay - chart.khoi_van_tuoi) // 10 * 10 + chart.khoi_van_tuoi
    danh = cac_nam(chart, tuoi_dau, tuoi_dau + 19)
    tieu_bang = "Lưu đại hạn, tiểu hạn và sao lưu"
    viec = [(tieu_bang, viet_bang(chart, danh))]
    for tuoi in (tuoi_nay, tuoi_nay + 1):
        nam = mot_nam(chart, tuoi, nam_goc + tuoi - 1)
        tieu = f"Năm {nam['nam']} tuổi {nam['tuoi']}"
        viec.append((tieu, prompt_mot_nam(chart, nhan, muc, nam)))

    if chi_xem:
        for tieu_de, van in viec:
            print("=" * 12, tieu_de)
            print(van[:1200])
            print()
        print("Lệnh này chưa gọi AI. Bảng vị trí không cần AI.")
        return

    cu = doc_bai_cu()
    tieu_de_cu: list[str] = []
    if KET_QUA.is_file():
        for dong in KET_QUA.read_text(encoding="utf-8").splitlines():
            if dong.startswith("## "):
                tieu_de_cu.append(dong[3:].strip())
    xong = [(tieu, cu[tieu]) for tieu in tieu_de_cu if tieu in cu and tieu != tieu_bang]
    xong.append((tieu_bang, viec[0][1]))
    ghi_bai(xong)
    print("Đã ghi bảng vị trí. Tiếp theo viết lời luận từng năm.")
    for tieu_de, prompt in viec[1:]:
        if tieu_de in cu:
            print(f"Giữ: {tieu_de}")
            xong.append((tieu_de, cu[tieu_de]))
            ghi_bai(xong)
            continue
        print(f"Viết: {tieu_de}", flush=True)
        van = goi_ai(HE_THONG, prompt)
        xong.append((tieu_de, van))
        ghi_bai(xong)
        time.sleep(4)
    print(f"Xong. Mở file: {KET_QUA}")
    xuat_report()


def chon_laso(laso: str | None) -> Chart:
    """Chọn lá số. Bài ghi vào thư mục đặt theo ngày và giờ sinh."""
    global KET_QUA, LASO_PATH, CHART
    if not laso:
        path = None
        chart = load_chart()
    else:
        path = Path(laso)
        if not path.is_file():
            path = ROOT / "laso" / laso
        if not path.is_file():
            raise SystemExit(
                "Không thấy file lá số.\n"
                "Hãy copy laso\\mau.json thành một file mới trong thư mục laso, sửa số liệu, rồi chạy:\n"
                "    .\\venv\\Scripts\\python.exe analyze.py --laso laso\\ten_file.json --day-du"
            )
        chart = load_chart(path)
    LASO_PATH = path
    CHART = chart
    KET_QUA = thu_muc_bao_cao(chart) / "phan_tich.md"
    return chart


def xuat_report() -> None:
    if not KET_QUA.is_file():
        return
    from xuat_word import xuat

    xuat(str(LASO_PATH) if LASO_PATH else None)


def viet_mot_phan(viec: Viec) -> str:
    """Một lần gọi. Không viết lại để liệt kê sao, vì prompt kể chuyện cấm kiểu đó."""
    return goi_ai(viec.he_thong or HE_THONG, viec.noi_dung)


def viet_lai_bai() -> None:
    """Đổi câu văn cho dễ đọc. Bảng vị trí hạn giữ nguyên vì đó là số đã tính."""
    cu = doc_bai_cu()
    if not cu:
        raise SystemExit(f"Chưa có bài để viết lại: {KET_QUA}")
    tieu_de: list[str] = []
    for dong in KET_QUA.read_text(encoding="utf-8").splitlines():
        if dong.startswith("## "):
            tieu_de.append(dong[3:].strip())
    dau = KET_QUA.with_name("da_viet_de.txt")
    xong_roi = set(dau.read_text(encoding="utf-8").splitlines()) if dau.is_file() else set()
    giu_nguyen = "Lưu đại hạn, tiểu hạn và sao lưu"
    bai = [(tieu, cu[tieu]) for tieu in tieu_de if tieu in cu]
    can_viet = [tieu for tieu, _ in bai if tieu not in xong_roi and tieu != giu_nguyen]
    print(f"Viết lại {len(can_viet)} phần cho dễ đọc. Bảng hạn giữ nguyên.")
    for tieu, than in bai:
        if tieu == giu_nguyen or tieu in xong_roi:
            continue
        print(f"Viết lại: {tieu}", flush=True)
        moi = goi_ai(LOI_VIET_LAI, than)
        for i, (ten, _) in enumerate(bai):
            if ten == tieu:
                bai[i] = (ten, moi)
                break
        ghi_bai(bai)
        dau.write_text("\n".join(sorted(xong_roi | {tieu})) + "\n", encoding="utf-8")
        xong_roi.add(tieu)
        time.sleep(4)
    print(f"Xong. Mở file: {KET_QUA}")
    xuat_report()


def main() -> None:
    parser = argparse.ArgumentParser(description="Gọi AI viết phân tích tử vi theo sách Tân Biên.")
    parser.add_argument("--xem", action="store_true", help="Chỉ in đoạn sách sẽ gửi, không gọi AI.")
    parser.add_argument(
        "--day-du",
        action="store_true",
        help="Viết đủ 4 chương rồi gộp thành một file Word.",
    )
    parser.add_argument(
        "--han",
        action="store_true",
        help="Viết đủ 4 chương. Vận hạn và ngày tháng nằm ở chương 3 và chương 4.",
    )
    parser.add_argument(
        "--laso",
        help="File lá số trong thư mục laso, ví dụ laso\\nguoi_moi.json. Bỏ trống thì dùng lá số mẫu.",
    )
    parser.add_argument(
        "--viet-lai",
        action="store_true",
        help="Viết lại bài đã có cho dễ đọc, không phân tích thêm.",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    if not SACH.is_file():
        raise SystemExit("Chưa có tai_lieu\\TuVi_TanBien_Data.md. Hãy chạy pdf_parser.py rồi để file đó trong thư mục tai_lieu.")

    chart = chon_laso(args.laso)
    if args.viet_lai:
        viet_lai_bai()
        return
    nhan = phan_tich(chart)
    muc = doc_sach()
    if args.han:
        args.day_du = True
    viec = tao_viec(chart, nhan, muc, args.day_du)

    if args.xem:
        vuot = []
        for mot in viec:
            if not mot.goi:
                print("=" * 12, mot.tieu, "(bảng tính sẵn, không gọi AI)")
                continue
            token = token_nguyen_lieu(mot.noi_dung)
            print("=" * 12, mot.tieu, f"({token} token)")
            print(mot.noi_dung[:700])
            print()
            if token > 2000:
                vuot.append(mot.tieu)
        print(f"Có {len(viec)} phần. Lệnh này chưa gọi AI. Bài sẽ ghi vào {KET_QUA.parent}.")
        if vuot:
            raise SystemExit("Nguyên liệu dài quá 1000 token: " + ", ".join(vuot))
        return

    da_co = doc_bai_cu() if args.day_du and dung_kieu_ke() else {}
    con_lai = sum(1 for mot in viec if mot.goi and mot.tieu not in da_co)
    print(f"Sẽ gọi AI {con_lai} lần. Giữ {len([mot for mot in viec if mot.goi]) - con_lai} phần đã viết.")
    print(f"Ghi vào thư mục: {KET_QUA.parent}")
    xong: list[tuple[str, str]] = []
    for so, mot in enumerate(viec, start=1):
        if not mot.goi:
            print(f"[{so}/{len(viec)}] Bảng tính sẵn: {mot.tieu}")
            xong.append((mot.tieu, mot.noi_dung))
            ghi_bai(xong)
            continue
        if mot.tieu in da_co:
            print(f"[{so}/{len(viec)}] Giữ: {mot.tieu}")
            xong.append((mot.tieu, da_co[mot.tieu]))
            continue
        print(f"[{so}/{len(viec)}] {mot.tieu}", flush=True)
        xong.append((mot.tieu, viet_mot_phan(mot)))
        ghi_bai(xong)
        time.sleep(4)
    ghi_bai(xong)
    xuat_report()
    print(f"Xong. Mở thư mục: {KET_QUA.parent}")


if __name__ == "__main__":
    main()
