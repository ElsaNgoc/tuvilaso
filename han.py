"""
Compute lưu đại hạn (yearly position within the decade period), tiểu hạn (annual period)
and sao lưu (transiting stars) following Tử Vi Đẩu Số Tân Biên (the reference book).

Run to self-check:
    .\\venv\\Scripts\\python.exe han.py
"""

from __future__ import annotations

from models import Chart, House, load_chart

CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]

# 10.3. Men and women differ in counting direction, not in the starting cung (palace).
KHOI_TIEU_HAN = {
    "Dần": "Thìn",
    "Ngọ": "Thìn",
    "Tuất": "Thìn",
    "Thân": "Tuất",
    "Tý": "Tuất",
    "Thìn": "Tuất",
    "Tỵ": "Mùi",
    "Dậu": "Mùi",
    "Sửu": "Mùi",
    "Hợi": "Sửu",
    "Mão": "Sửu",
    "Mùi": "Sửu",
}

# 4.3. Lưu Lộc Tồn table by the Heavenly Stem (can) of the year being read.
LOC_THEO_CAN = {
    "Giáp": "Dần",
    "Ất": "Mão",
    "Bính": "Tỵ",
    "Mậu": "Tỵ",
    "Đinh": "Ngọ",
    "Kỷ": "Ngọ",
    "Canh": "Thân",
    "Tân": "Dậu",
    "Nhâm": "Hợi",
    "Quý": "Tý",
}

# 4.4. Lưu Thiên Mã table by the Earthly Branch (chi) of the year being read.
MA_THEO_CHI = {
    "Dần": "Thân",
    "Ngọ": "Thân",
    "Tuất": "Thân",
    "Thân": "Dần",
    "Tý": "Dần",
    "Thìn": "Dần",
    "Tỵ": "Hợi",
    "Dậu": "Hợi",
    "Sửu": "Hợi",
    "Hợi": "Tỵ",
    "Mão": "Tỵ",
    "Mùi": "Tỵ",
}

# The book says a transiting star meeting the fixed star of the same name deserves attention.
SAO_CO_DINH = {
    "Lưu Thái Tuế": "Thái Tuế",
    "Lưu Tang Môn": "Tang Môn",
    "Lưu Bạch Hổ": "Bạch Hổ",
    "Lưu Thiên Khốc": "Thiên Khốc",
    "Lưu Thiên Hư": "Thiên Hư",
    "Lưu Lộc Tồn": "Lộc Tồn",
    "Lưu Kình Dương": "Kình Dương",
    "Lưu Đà La": "Đà La",
    "Lưu Thiên Mã": "Thiên Mã",
}


def buoc(chi: str, so: int, thuan: bool) -> str:
    i = CHI.index(chi)
    return CHI[(i + so) % 12] if thuan else CHI[(i - so) % 12]


def nhom_thuan(chart: Chart) -> bool:
    """Yang male and yin female go one way. Yin male and yang female go the other."""
    duong = "Dương" in chart.am_duong
    nam = chart.gioi_tinh == "Nam"
    return (duong and nam) or (not duong and not nam)


def nam_sinh(chart: Chart) -> tuple[str, str, int]:
    cum = chart.am_lich.split(",")[0].replace("Năm", "").strip().split()
    if len(cum) < 2:
        raise ValueError(f"Không đọc được năm sinh trong '{chart.am_lich}'")
    nam = int(chart.ngay_sinh.rsplit("/", 1)[-1])
    return cum[0], cum[1], nam


def can_chi_nam(can_goc: str, chi_goc: str, nam_goc: int, nam: int) -> tuple[str, str]:
    lech = nam - nam_goc
    can = CAN[(CAN.index(can_goc) + lech) % 10]
    chi = CHI[(CHI.index(chi_goc) + lech) % 12]
    return can, chi


def luu_dai_han(chi_goc: str, lech: int, di_thuan: bool) -> str:
    """Offset 0 is the first year of the ten-year đại hạn (decade period). Checked against the two examples on pages 16-17."""
    doi = buoc(chi_goc, 6, True)
    if lech == 0:
        return chi_goc
    if lech in (1, 3):
        return doi
    if lech == 2:
        return buoc(doi, 1, not di_thuan)
    return buoc(doi, lech - 3, di_thuan)


def bang_tieu_han(chi_sinh: str, nu: bool) -> dict[str, str]:
    """Branch (chi) of the year being read -> branch of the tiểu hạn palace."""
    cung = KHOI_TIEU_HAN[chi_sinh]
    chi = chi_sinh
    bang = {}
    for _ in range(12):
        bang[chi] = cung
        chi = buoc(chi, 1, True)
        cung = buoc(cung, 1, not nu)
    return bang


def sao_luu(can: str, chi: str) -> dict[str, str]:
    thai_tue = chi
    tang = buoc(thai_tue, 2, True)
    loc = LOC_THEO_CAN[can]
    return {
        "Lưu Thái Tuế": thai_tue,
        "Lưu Tang Môn": tang,
        "Lưu Bạch Hổ": buoc(tang, 6, True),
        "Lưu Thiên Khốc": buoc("Ngọ", (CHI.index(chi) - CHI.index("Tý")) % 12, False),
        "Lưu Thiên Hư": buoc("Ngọ", (CHI.index(chi) - CHI.index("Tý")) % 12, True),
        "Lưu Lộc Tồn": loc,
        "Lưu Kình Dương": buoc(loc, 1, True),
        "Lưu Đà La": buoc(loc, 1, False),
        "Lưu Thiên Mã": MA_THEO_CHI[chi],
    }


def cung_tai(chart: Chart, chi: str) -> House:
    for house in chart.cung:
        if house.vi_tri == chi:
            return house
    raise KeyError(f"Không có cung tại {chi}")


def co_sao(house: House, ten: str) -> bool:
    return any(star.ten == ten for star in house.chinh_tinh + house.phu_tinh)


def mot_nam(chart: Chart, tuoi: int, nam: int) -> dict:
    can_goc, chi_goc, nam_goc = nam_sinh(chart)
    can, chi = can_chi_nam(can_goc, chi_goc, nam_goc, nam)
    goc = next(house for house in chart.cung if house.dai_han_tu <= tuoi <= house.dai_han_den)
    lech = tuoi - goc.dai_han_tu
    chi_luu = luu_dai_han(goc.vi_tri, lech, nhom_thuan(chart))
    chi_tieu = bang_tieu_han(chi_goc, chart.gioi_tinh == "Nữ")[chi]
    luu = sao_luu(can, chi)
    trung = []
    for ten_luu, vi in luu.items():
        co_dinh = SAO_CO_DINH[ten_luu]
        if co_sao(cung_tai(chart, vi), co_dinh):
            trung.append(f"{ten_luu} trùng {co_dinh} cố định tại {vi}")
    return {
        "tuoi": tuoi,
        "nam": nam,
        "can_chi": f"{can} {chi}",
        "goc": goc,
        "luu_dai_han": cung_tai(chart, chi_luu),
        "tieu_han": cung_tai(chart, chi_tieu),
        "sao_luu": {ten: cung_tai(chart, vi) for ten, vi in luu.items()},
        "trung": trung,
    }


def cac_nam(chart: Chart, tuoi_tu: int, tuoi_den: int) -> list[dict]:
    _, _, nam_goc = nam_sinh(chart)
    return [mot_nam(chart, tuoi, nam_goc + tuoi - 1) for tuoi in range(tuoi_tu, tuoi_den + 1)]


def viet_bang(chart: Chart, danh: list[dict]) -> str:
    dong = [
        "Vị trí dưới đây tính theo sách Tân Biên: lưu đại hạn (mục 10.2), "
        "lưu niên tiểu hạn (mục 10.3) và sao lưu động (mục 4, phần luận đoán vận hạn).",
        "Đây là hạn của tử vi. Phần tứ trụ không đưa vào.",
        f"Đương số {chart.gioi_tinh}, {chart.am_duong}, sinh {chart.am_lich.split(',')[0]}.",
        "",
    ]
    for nam in danh:
        goc = nam["goc"]
        luu = nam["luu_dai_han"]
        tieu = nam["tieu_han"]
        sao = ", ".join(f"{ten} tại {house.ten} ({house.vi_tri})" for ten, house in nam["sao_luu"].items())
        trung = ""
        if nam["trung"]:
            trung = " Chú ý: " + "; ".join(nam["trung"]) + "."
        dong.append(
            f"- Tuổi {nam['tuoi']}, năm {nam['nam']} {nam['can_chi']}. "
            f"Đại hạn {goc.dai_han} tại cung {goc.ten} ({goc.vi_tri}). "
            f"Lưu đại hạn tại cung {luu.ten} ({luu.vi_tri}). "
            f"Tiểu hạn tại cung {tieu.ten} ({tieu.vi_tri}). "
            f"Sao lưu: {sao}.{trung}"
        )
    return "\n".join(dong)


def _kiem_tra() -> None:
    # Page 16: yang male, base Thìn, age 27 falls in Hợi.
    assert luu_dai_han("Thìn", 27 - 23, True) == "Hợi"
    assert luu_dai_han("Thìn", 2, True) == "Dậu"
    # Page 17: yin male, base Dậu, age 38 falls in Dần.
    assert luu_dai_han("Dậu", 38 - 34, False) == "Dần"
    assert luu_dai_han("Dậu", 2, False) == "Thìn"
    # A boy born in a Tý year starts Tý at Tuất. A girl born in a Ngọ year starts Ngọ at Thìn, Mùi at Mão.
    assert bang_tieu_han("Tý", False)["Tý"] == "Tuất"
    assert bang_tieu_han("Tý", False)["Sửu"] == "Hợi"
    assert bang_tieu_han("Ngọ", True)["Ngọ"] == "Thìn"
    assert bang_tieu_han("Ngọ", True)["Mùi"] == "Mão"
    # Mùi year: Thái Tuế at Mùi, Tang Môn at Dậu, Bạch Hổ at Mão, Khốc at Hợi, Hư at Sửu.
    muoi = sao_luu("Ất", "Mùi")
    assert muoi["Lưu Thái Tuế"] == "Mùi"
    assert muoi["Lưu Tang Môn"] == "Dậu"
    assert muoi["Lưu Bạch Hổ"] == "Mão"
    assert muoi["Lưu Thiên Khốc"] == "Hợi"
    assert muoi["Lưu Thiên Hư"] == "Sửu"
    assert muoi["Lưu Lộc Tồn"] == "Mão"
    assert muoi["Lưu Kình Dương"] == "Thìn"
    assert muoi["Lưu Đà La"] == "Dần"
    assert sao_luu("Giáp", "Tý")["Lưu Thiên Mã"] == "Dần"
    chart = load_chart()
    nam = mot_nam(chart, 23, 2026)
    print(f"Năm 2026 tuổi 23: lưu đại hạn {nam['luu_dai_han'].ten}, tiểu hạn {nam['tieu_han'].ten}")
    print("Khớp thí dụ trong sách.")


if __name__ == "__main__":
    _kiem_tra()
