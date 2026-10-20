"""
Label the lá số (birth chart) before calling the AI.

Run:
    .\\venv\\Scripts\\python.exe engine.py
"""

from __future__ import annotations

import json
from pathlib import Path

from models import Chart, House, load_chart

ROOT = Path(__file__).resolve().parent

SINH = {"Kim": "Thủy", "Thủy": "Mộc", "Mộc": "Hỏa", "Hỏa": "Thổ", "Thổ": "Kim"}
KHAC = {"Kim": "Mộc", "Mộc": "Thổ", "Thổ": "Thủy", "Thủy": "Hỏa", "Hỏa": "Kim"}
HANH = ("Kim", "Mộc", "Thủy", "Hỏa", "Thổ")


def hanh_trong_ten(ten: str) -> str:
    for hanh in HANH:
        if ten.endswith(hanh) or ten.startswith(hanh):
            return hanh
    raise ValueError(f"Không đọc được ngũ hành trong '{ten}'")


def nganh_sinh_khac(chart: Chart) -> str:
    menh = hanh_trong_ten(chart.ban_menh)
    cuc = hanh_trong_ten(chart.cuc)
    if SINH[cuc] == menh:
        return f"Cục sinh mệnh ({cuc} sinh {menh})"
    if SINH[menh] == cuc:
        return f"Mệnh sinh cục ({menh} sinh {cuc})"
    if KHAC[cuc] == menh:
        return f"Cục khắc mệnh ({cuc} khắc {menh})"
    if KHAC[menh] == cuc:
        return f"Mệnh khắc cục ({menh} khắc {cuc})"
    if cuc == menh:
        return f"Mệnh và cục cùng hành {menh}"
    return f"Mệnh {menh}, cục {cuc}"


def la_hung(house: House) -> bool:
    if house.vo_chinh_dieu:
        return True
    return (house.tuan or house.triet) and bool(house.chinh_tinh)


def la_cat(house: House) -> bool:
    return bool(house.chinh_tinh) and not house.tuan and not house.triet


def nhan_cung(house: House) -> list[str]:
    nhan: list[str] = []
    an_ngu = []
    if house.tuan:
        an_ngu.append("Tuần")
    if house.triet:
        an_ngu.append("Triệt")

    if house.vo_chinh_dieu:
        nhan.append("Vô chính diệu")
        if an_ngu and house.ten == "MỆNH":
            nhan.append(
                "Có " + ", ".join(an_ngu) + " án ngữ. Sách nói Mệnh vô chính diệu rất cần Tuần, Triệt"
            )
        elif an_ngu:
            nhan.append("Có " + ", ".join(an_ngu) + " án ngữ")
        return nhan

    if an_ngu and house.chinh_tinh:
        ten_sao = ", ".join(star.ten for star in house.chinh_tinh)
        nhan.append(f"Trắc trở buổi đầu: {ten_sao} gặp {', '.join(an_ngu)}")
    return nhan


def nhan_menh_tu(chart: Chart) -> list[str]:
    menh = chart.cung_ten("MỆNH")
    tu = chart.cung_ten("TỬ")
    nhan: list[str] = []
    if menh.vo_chinh_dieu:
        nhan.append("Mệnh vô chính diệu")
    if la_hung(menh) and la_cat(tu):
        nhan.append("Mệnh hung nhi cát, do hữu Tử cung cát")
    elif la_cat(menh) and la_hung(tu):
        nhan.append("Mệnh cát nhi hung, do hữu Tử cung hung")
    return nhan


def phan_tich(chart: Chart) -> dict:
    ket_qua = {
        "ban_menh": chart.ban_menh,
        "cuc": chart.cuc,
        "ngu_hanh": nganh_sinh_khac(chart),
        "menh_tu": nhan_menh_tu(chart),
        "cung": [],
    }
    for house in chart.cung:
        ket_qua["cung"].append(
            {
                "ten": house.ten,
                "vi_tri": house.vi_tri,
                "dai_han": house.dai_han,
                "nhan": nhan_cung(house),
            }
        )
    return ket_qua


def main() -> None:
    chart = load_chart()
    ket_qua = phan_tich(chart)
    out = ROOT / "output" / "laso_nhan.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(ket_qua, ensure_ascii=False, indent=2), encoding="utf-8")

    print(ket_qua["ngu_hanh"])
    for dong in ket_qua["menh_tu"]:
        print(dong)
    print()
    for cung in ket_qua["cung"]:
        if not cung["nhan"]:
            continue
        print(f"{cung['ten']} tại {cung['vi_tri']}:")
        for nhan in cung["nhan"]:
            print(f"  - {nhan}")
    print(f"\nĐã ghi: {out}")


if __name__ == "__main__":
    main()
