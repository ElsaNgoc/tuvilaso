"""
Khuôn dữ liệu của một lá số.

Chạy để kiểm tra file mẫu:
    .\\venv\\Scripts\\python.exe models.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parent


class Star(BaseModel):
    ten: str
    loai: Literal["chinh_tinh", "phu_tinh"] = "phu_tinh"


class House(BaseModel):
    """Một cung trên lá số."""

    ten: str
    vi_tri: str
    can_chi: str
    dai_han_tu: int
    dai_han_den: int
    chinh_tinh: list[Star] = Field(default_factory=list)
    vo_chinh_dieu: bool = False
    sao_xung: list[str] = Field(default_factory=list)
    phu_tinh: list[Star] = Field(default_factory=list)
    tuan: bool = False
    triet: bool = False
    than_cu: bool = False
    phi_loc: str = ""
    phi_quyen: str = ""
    phi_khoa: str = ""
    phi_ky: str = ""
    tu_hoa: str = ""
    phuong_vien: str = ""

    @field_validator("chinh_tinh", "phu_tinh", mode="before")
    @classmethod
    def ep_sao(cls, value, info):
        loai = "chinh_tinh" if info.field_name == "chinh_tinh" else "phu_tinh"
        stars = []
        for item in value or []:
            if isinstance(item, str):
                stars.append({"ten": item, "loai": loai})
            else:
                stars.append(item)
        return stars

    @property
    def dai_han(self) -> str:
        return f"{self.dai_han_tu} - {self.dai_han_den}"


class TuTruCot(BaseModel):
    ten: str
    thap_than: str
    thien_can: str
    dia_chi: str
    tang_can: str
    truong_sinh: str
    nap_am: str


class DaiVanTuTru(BaseModel):
    van: int
    tuoi_tu: int
    tuoi_den: int
    nam: int
    can_chi: str
    than: str


class TuTru(BaseModel):
    tiet_khi: str
    van: str
    cot: list[TuTruCot]
    dai_van: list[DaiVanTuTru]


class NienHoa(BaseModel):
    loc: str
    quyen: str
    khoa: str
    ky: str


class Chart(BaseModel):
    """Cả lá số. Phần tử vi dùng cho sách Tân Biên. Phần tứ trụ giữ để sau."""

    gioi_tinh: str
    ngay_sinh: str
    gio_hanh_chinh: str
    gio_mat_troi: str
    am_lich: str
    noi_sinh: str
    am_duong: str
    ban_menh: str
    cuc: str
    khoi_van_tuoi: int
    than_cu: str
    dac_diem: list[str] = Field(default_factory=list)
    nien_hoa: NienHoa
    cung: list[House] = Field(min_length=12, max_length=12)
    tu_tru: TuTru | None = None

    def cung_ten(self, ten: str) -> House:
        for house in self.cung:
            if house.ten == ten:
                return house
        raise KeyError(f"Không thấy cung {ten}")


def load_chart(path: Path | None = None) -> Chart:
    file_path = path or (ROOT / "sample_laso.json")
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return Chart.model_validate(data)


if __name__ == "__main__":
    chart = load_chart()
    print(f"Giới tính: {chart.gioi_tinh}")
    print(f"Sinh: {chart.ngay_sinh} {chart.gio_hanh_chinh}")
    print(f"Âm lịch: {chart.am_lich}")
    print(f"Bản mệnh: {chart.ban_menh}")
    print(f"Cục: {chart.cuc}, khởi vận {chart.khoi_van_tuoi} tuổi")
    print(f"Thân cư: {chart.than_cu}")
    print(f"Số cung: {len(chart.cung)}")
    for house in chart.cung:
        if house.vo_chinh_dieu:
            chinh = "Vô chính diệu, xung " + " - ".join(house.sao_xung)
        else:
            chinh = ", ".join(star.ten for star in house.chinh_tinh)
        danh_dau = []
        if house.tuan:
            danh_dau.append("Tuần")
        if house.triet:
            danh_dau.append("Triệt")
        if house.than_cu:
            danh_dau.append("Thân")
        them = f" ({', '.join(danh_dau)})" if danh_dau else ""
        print(f"- {house.ten} tại {house.vi_tri}, hạn {house.dai_han}: {chinh}{them}")
