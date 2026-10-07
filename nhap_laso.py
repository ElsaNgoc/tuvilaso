"""
Đổi bài lá số người dùng dán thành file JSON.

Cách dùng:
    .\\venv\\Scripts\\python.exe nhap_laso.py laso\\bai.txt

File JSON ra cùng tên, ví dụ laso\\bai.json.
Sau đó phân tích:
    .\\venv\\Scripts\\python.exe analyze.py --laso laso\\bai.json --day-du
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from models import load_chart

CHUAN = {
    "GIÁP": "Giáp",
    "ẤT": "Ất",
    "BÍNH": "Bính",
    "ĐINH": "Đinh",
    "MẬU": "Mậu",
    "KỶ": "Kỷ",
    "CANH": "Canh",
    "TÂN": "Tân",
    "NHÂM": "Nhâm",
    "QUÝ": "Quý",
    "TÝ": "Tý",
    "SỬU": "Sửu",
    "DẦN": "Dần",
    "MÃO": "Mão",
    "THÌN": "Thìn",
    "TỴ": "Tỵ",
    "TỊ": "Tỵ",
    "NGỌ": "Ngọ",
    "MÙI": "Mùi",
    "THÂN": "Thân",
    "DẬU": "Dậu",
    "TUẤT": "Tuất",
    "HỢI": "Hợi",
}


def sach(van: str) -> str:
    van = van.replace("**", "").replace("`", "")
    van = van.replace("Tị", "Tỵ").replace("TỊ", "TỴ")
    van = van.replace("Hỉ", "Hỷ").replace("Kị", "Kỵ")
    return van.strip()


def tu(van: str) -> str:
    """KỶ MÃO -> Kỷ Mão. Chữ thường giữ nguyên."""
    van = sach(van)
    khoi = []
    for tieng in van.split():
        khoa = tieng.upper()
        if khoa in CHUAN and tieng == tieng.upper():
            khoi.append(CHUAN[khoa])
        elif tieng == "Tị":
            khoi.append("Tỵ")
        else:
            khoi.append(tieng)
    return " ".join(khoi)


def o_bang(van: str, moc: str) -> list[list[str]]:
    hang: list[list[str]] = []
    dang_lay = False
    for dong in van.splitlines():
        if not dong.strip().startswith("|"):
            if dang_lay:
                break
            continue
        if moc in dong and not dang_lay:
            dang_lay = True
        if not dang_lay or re.match(r"^\|\s*-+", dong.strip()):
            continue
        cot = [sach(o) for o in dong.strip().strip("|").split("|")]
        hang.append(cot)
    return hang


def gia_tri(van: str, nhan: str) -> str:
    khop = re.search(rf"\*\*{re.escape(nhan)}:\*\*\s*(.+)", van)
    if not khop:
        khop = re.search(rf"{re.escape(nhan)}:\s*(.+)", van)
    return sach(khop.group(1)) if khop else ""


def tach_sao(o: str) -> list[str]:
    if not o or o.upper().startswith("VCD"):
        return []
    return [tu(sao) for sao in o.split(",") if sao.strip()]


def cung_phi(o: str) -> str:
    khop = re.search(r"->\s*([A-ZÀ-Ỹ]+)", o)
    return khop.group(1) if khop else ""


def doc_bai(van: str) -> dict:
    gioi = gia_tri(van, "Giới tính")
    sinh = gia_tri(van, "Ngày sinh")
    ngay = re.search(r"\d{1,2}/\d{1,2}/\d{4}", sinh)
    gio_hc = re.search(r"(\d{1,2}h\d{2})\s*\(Hành chính\)", sinh)
    gio_mt = re.search(r"(\d{1,2}h\d{2})\s*\(Giờ Mặt Trời\)", sinh)
    am = re.search(r"(Âm Nam|Dương Nam|Âm Nữ|Dương Nữ)", van)
    menh = re.search(r"\*\*Mệnh:\*\*\s*([^.]+)", van)
    cuc = re.search(r"\*\*Cục:\*\*\s*([^(]+)\(Khởi vận\s*(\d+)\s*tuổi\)", van)
    than = re.search(r"Thân cư\s+([A-ZÀ-Ỹ]+)", van)
    dac = re.search(r"\*\*Đặc điểm:\*\*\s*(.+)", van)
    dac_diem = [sach(y).rstrip(".") for y in (dac.group(1).split(",") if dac else []) if sach(y)]
    if am and "thuận lý" in van:
        dac_diem.insert(0, "Âm dương thuận lý")
    duong_loc = re.search(r"Đường K[ịỵ] chuyển Lộc:\s*(.+)", van)
    duong_ky = re.search(r"Đường chuyển K[ịỵ]:\s*(.+)", van)
    if duong_loc:
        dac_diem.append("Đường Kỵ chuyển Lộc: " + sach(duong_loc.group(1)).rstrip("."))
    if duong_ky:
        dac_diem.append("Đường chuyển Kỵ: " + sach(duong_ky.group(1)).rstrip("."))

    nien = re.search(
        r"Lộc \(A\)\s*->\s*(.+?)\s*\(([A-ZÀ-Ỹ]+)\)\s*\|\s*"
        r"Quyền \(B\)\s*->\s*(.+?)\s*\(([A-ZÀ-Ỹ]+)\)\s*\|\s*"
        r"Khoa \(C\)\s*->\s*(.+?)\s*\(([A-ZÀ-Ỹ]+)\)\s*\|\s*"
        r"Kỵ \(D\)\s*->\s*(.+?)\s*\(([A-ZÀ-Ỹ]+)\)",
        sach(van),
    )
    nien_hoa = {"loc": "", "quyen": "", "khoa": "", "ky": ""}
    if nien:
        nien_hoa = {
            "loc": f"{tu(nien.group(1))} tại {nien.group(2)}",
            "quyen": f"{tu(nien.group(3))} tại {nien.group(4)}",
            "khoa": f"{tu(nien.group(5))} tại {nien.group(6)}",
            "ky": f"{tu(nien.group(7))} tại {nien.group(8)}",
        }

    tru = o_bang(van, "Thành phần")
    theo_hang = {row[0]: row[1:] for row in tru[1:] if row}
    ten_cot = ["Năm", "Tháng", "Ngày", "Giờ"]
    cot = []
    for i, ten in enumerate(ten_cot):
        cot.append(
            {
                "ten": ten,
                "thap_than": theo_hang.get("Thập Thần", ["", "", "", ""])[i],
                "thien_can": tu(theo_hang.get("Thiên Can", ["", "", "", ""])[i]),
                "dia_chi": tu(theo_hang.get("Địa Chi", ["", "", "", ""])[i]),
                "tang_can": theo_hang.get("Tàng Can", ["", "", "", ""])[i],
                "truong_sinh": theo_hang.get("Trường Sinh", ["", "", "", ""])[i],
                "nap_am": tu(theo_hang.get("Nạp Âm", ["", "", "", ""])[i]),
            }
        )
    tiet = re.search(r"Tiết khí:\s*([^.]+)", van)
    chieu_van = re.search(r"\*\*Vận:\*\*\s*(\w+)", van)

    van_han = o_bang(van, "8-17")
    if not van_han:
        van_han = o_bang(van, "| Vận |")
    nhan_van = {row[0]: row[1:] for row in van_han if row}
    dai_van = []
    for i, o in enumerate(nhan_van.get("Vận", [])):
        so = re.search(r"(\d+)\s*\((\d+)-(\d+)", o)
        if not so:
            continue
        dai_van.append(
            {
                "van": int(so.group(1)),
                "tuoi_tu": int(so.group(2)),
                "tuoi_den": int(so.group(3)),
                "nam": int(re.search(r"\d{4}", nhan_van["Năm"][i]).group(0)),
                "can_chi": tu(nhan_van["Can Chi"][i]),
                "than": nhan_van["Thần"][i],
            }
        )

    bang_cung = o_bang(van, "Tên Cung")
    than_cu = than.group(1) if than else ""
    cung = []
    for row in bang_cung[1:]:
        if len(row) < 10 or not row[0]:
            continue
        ten = row[0].upper()
        chinh_o = row[4]
        vcd = chinh_o.upper().startswith("VCD")
        xung = []
        if vcd:
            trong = re.search(r"\((.+)\)", chinh_o)
            if trong:
                xung = [tu(sao) for sao in re.split(r"\s*-\s*", trong.group(1)) if sao.strip()]
        phu = tach_sao(row[5])
        co_tuan = "Tuần" in phu
        co_triet = "Triệt" in phu
        phu = [sao for sao in phu if sao not in ("Tuần", "Triệt")]
        han = re.search(r"(\d+)\s*-\s*(\d+)", row[3])
        muc = {
            "ten": ten,
            "vi_tri": tu(row[1]),
            "can_chi": tu(row[2]),
            "dai_han_tu": int(han.group(1)) if han else 0,
            "dai_han_den": int(han.group(2)) if han else 0,
            "phu_tinh": phu,
            "phi_loc": cung_phi(row[6]),
            "phi_quyen": cung_phi(row[7]),
            "phi_khoa": cung_phi(row[8]),
            "phi_ky": cung_phi(row[9]),
        }
        if vcd:
            muc["vo_chinh_dieu"] = True
            muc["sao_xung"] = xung
        else:
            muc["chinh_tinh"] = tach_sao(chinh_o)
        if co_tuan:
            muc["tuan"] = True
        if co_triet:
            muc["triet"] = True
        if ten == than_cu:
            muc["than_cu"] = True
        if len(row) > 10 and row[10]:
            muc["tu_hoa"] = row[10]
        if len(row) > 11 and row[11]:
            muc["phuong_vien"] = row[11]
        cung.append(muc)

    return {
        "gioi_tinh": gioi,
        "ngay_sinh": ngay.group(0) if ngay else "",
        "gio_hanh_chinh": gio_hc.group(1) if gio_hc else "",
        "gio_mat_troi": gio_mt.group(1) if gio_mt else "",
        "am_lich": gia_tri(van, "Âm lịch"),
        "noi_sinh": gia_tri(van, "Nơi sinh"),
        "am_duong": am.group(1) if am else "",
        "ban_menh": sach(menh.group(1)) if menh else "",
        "cuc": sach(cuc.group(1)) if cuc else "",
        "khoi_van_tuoi": int(cuc.group(2)) if cuc else 0,
        "than_cu": than_cu,
        "dac_diem": dac_diem,
        "nien_hoa": nien_hoa,
        "tu_tru": {
            "tiet_khi": sach(tiet.group(1)) if tiet else "",
            "van": chieu_van.group(1) if chieu_van else "",
            "cot": cot,
            "dai_van": dai_van,
        },
        "cung": cung,
    }


def chuyen(nguon: Path, dich: Path | None = None) -> Path:
    du_lieu = doc_bai(nguon.read_text(encoding="utf-8"))
    ra = dich or nguon.with_suffix(".json")
    ra.write_text(json.dumps(du_lieu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    la_so = load_chart(ra)
    print(f"Đã ghi {ra}")
    print(f"{la_so.gioi_tinh}, {la_so.am_duong}, sinh {la_so.ngay_sinh}, mệnh {la_so.ban_menh}, {la_so.cuc}")
    print(f"{len(la_so.cung)} cung. Thân cư {la_so.than_cu}.")
    return ra


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Thiếu file. Ví dụ: .\\venv\\Scripts\\python.exe nhap_laso.py laso\\bai.txt")
    chuyen(Path(sys.argv[1]))
