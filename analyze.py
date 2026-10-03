"""
Bước 4: gọi AI viết phân tích, chỉ dựa trên sách đã tách.

Xem AI sẽ được đưa đoạn sách nào (chưa tốn tiền):
    .\\venv\\Scripts\\python.exe analyze.py --xem

Chạy thử một đoạn (tổng quan Mệnh - Thân):
    .\\venv\\Scripts\\python.exe analyze.py

Chạy đủ: tổng quan, 12 cung, 12 đại hạn:
    .\\venv\\Scripts\\python.exe analyze.py --day-du

Nếu Gemini báo quá tải, lệnh tự đợi rồi thử lại. Chạy lại cùng lệnh sẽ viết tiếp
phần còn thiếu, không viết đè những phần đã có trong output\\phan_tich.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

from engine import phan_tich
from models import Chart, House, load_chart

ROOT = Path(__file__).resolve().parent
SACH = ROOT / "output" / "TuVi_TanBien_Data.md"
KET_QUA = ROOT / "output" / "phan_tich.md"

HE_THONG = """Bạn là một hệ thống phân tích Tử Vi chuyên nghiệp. Bạn CHỈ ĐƯỢC PHÉP tổng hợp và hành văn dựa TRÊN ĐÚNG tài liệu tham khảo được cung cấp bên dưới. [CẤM]: Tuyệt đối không sử dụng kiến thức Tử Vi bên ngoài tài liệu này. Nếu tài liệu không nhắc đến, hãy bỏ qua.
Viết tiếng Việt, ngắn gọn, có gạch đầu dòng. Không bịa sao, không nói phi hóa, không nói tứ trụ."""

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


def tim_muc(muc: list[tuple[str, str]], cum: str) -> str:
    """Lấy đúng mục sách có tên sao hoặc số mục, cắt ngắn để khỏi gửi cả cuốn."""
    khoa = cum.casefold().replace("ị", "ỵ").replace("kị", "kỵ")
    for tieu_de, than in muc:
        dau = tieu_de.casefold().replace("ị", "ỵ")
        if khoa[:1].isdigit():
            trung = dau.startswith(khoa)
        else:
            trung = re.search(rf"(?<![a-zà-ỹ]){re.escape(khoa)}(?![a-zà-ỹ])", dau) is not None
        if not trung:
            continue
        van = than.strip()
        if len(van) > 1400:
            van = van[:1400].rsplit(" ", 1)[0] + "..."
        return f"{tieu_de}\n{van}".strip()
    return ""


def doan_sao(muc: list[tuple[str, str]], ten_sao: list[str], gioi_han: int) -> str:
    khoi = []
    for ten in ten_sao:
        if len(ten) < 4:
            continue
        doan = tim_muc(muc, ten)
        if doan and doan not in khoi:
            khoi.append(doan)
        if len(khoi) >= gioi_han:
            break
    return "\n\n".join(khoi)


def boi_canh_cung(muc: list[tuple[str, str]], house: House, nhan: list[str]) -> str:
    chinh = [star.ten for star in house.chinh_tinh]
    phu = [star.ten for star in house.phu_tinh]
    sao = chinh or house.sao_xung
    doan = [doan_sao(muc, sao, 2), doan_sao(muc, phu, 2)]
    if house.vo_chinh_dieu:
        doan.append(tim_muc(muc, "4.1.10."))
    if any("Mệnh hung nhi cát" in dong for dong in nhan):
        doan.append(tim_muc(muc, "18.1."))
    return "\n\n".join(phan for phan in doan if phan)


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


def tao_viec(chart: Chart, nhan: dict, muc: list[tuple[str, str]], day_du: bool) -> list[tuple[str, str]]:
    viec: list[tuple[str, str]] = []
    menh = chart.cung_ten("MỆNH")
    than = chart.cung_ten(chart.than_cu)
    nhan_menh = next(item["nhan"] for item in nhan["cung"] if item["ten"] == "MỆNH")
    sach = boi_canh_cung(muc, menh, nhan["menh_tu"] + nhan_menh)
    sach_than = boi_canh_cung(muc, than, [])
    viec.append(
        (
            "Tổng quan Mệnh - Thân",
            "Viết tổng quan Mệnh và Thân.\n"
            f"Đương số: {chart.gioi_tinh}, {chart.am_duong}, bản mệnh {chart.ban_menh}, "
            f"cục {chart.cuc}, {nhan['ngu_hanh']}. Thân cư {chart.than_cu}.\n"
            f"{mo_ta_cung(menh, nhan_menh)}\n"
            f"Cung Thân: {mo_ta_cung(than, [])}\n"
            f"Nhãn chung: {'; '.join(nhan['menh_tu']) or 'không'}.\n\n"
            f"Tài liệu:\n{sach}\n\n{sach_than}",
        )
    )
    if not day_du:
        return viec

    for house in chart.cung:
        nhan_cung = next(item["nhan"] for item in nhan["cung"] if item["ten"] == house.ten)
        viec.append(
            (
                f"Cung {house.ten}",
                "Viết riêng cung này.\n"
                f"{mo_ta_cung(house, nhan_cung)}\n\n"
                f"Tài liệu:\n{boi_canh_cung(muc, house, nhan_cung) or '(Sách không có mục riêng.)'}",
            )
        )

    dai_han = tim_muc(muc, "10.1.")
    for house in chart.cung:
        nhan_cung = next(item["nhan"] for item in nhan["cung"] if item["ten"] == house.ten)
        viec.append(
            (
                f"Đại hạn {house.dai_han} - cung {house.ten}",
                "Viết vận hạn mười năm của cung này. Nếu sách không nói rõ hạn đó thì chỉ nhắc sao trong cung, đừng bịa sự kiện.\n"
                f"{mo_ta_cung(house, nhan_cung)}\n\n"
                f"Tài liệu:\n{dai_han}\n\n{boi_canh_cung(muc, house, nhan_cung)}",
            )
        )
    return viec


def goi_openai(system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    tra_loi = client.chat.completions.create(
        model=model,
        temperature=0.3,
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
    cau_hinh: dict = {"temperature": 0.3}
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
        "Phần đã viết vẫn nằm trong output\\phan_tich.md.\n"
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


def ghi_bai(cac_phan: list[tuple[str, str]]) -> None:
    dong = ["# Phân tích lá số", ""]
    for tieu_de, van in cac_phan:
        dong.append(f"## {tieu_de}")
        dong.append("")
        dong.append(van.strip())
        dong.append("")
    KET_QUA.write_text("\n".join(dong).rstrip() + "\n", encoding="utf-8")


def doc_bai_cu() -> dict[str, str]:
    """Đọc các phần đã viết để lần chạy sau nối tiếp, không gọi lại AI."""
    if not KET_QUA.is_file():
        return {}
    van = KET_QUA.read_text(encoding="utf-8")
    da_co: dict[str, str] = {}
    for phan in re.split(r"(?m)^## ", van)[1:]:
        dong = phan.splitlines()
        tieu_de = dong[0].strip()
        than = "\n".join(dong[1:]).strip()
        if tieu_de and than:
            da_co[tieu_de] = than
    return da_co


def main() -> None:
    parser = argparse.ArgumentParser(description="Gọi AI viết phân tích tử vi theo sách Tân Biên.")
    parser.add_argument("--xem", action="store_true", help="Chỉ in đoạn sách sẽ gửi, không gọi AI.")
    parser.add_argument("--day-du", action="store_true", help="Viết tổng quan, 12 cung và 12 đại hạn.")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    if not SACH.is_file():
        raise SystemExit("Chưa có output\\TuVi_TanBien_Data.md. Hãy chạy pdf_parser.py trước.")

    chart: Chart = load_chart()
    nhan = phan_tich(chart)
    muc = doc_sach()
    viec = tao_viec(chart, nhan, muc, args.day_du)

    if args.xem:
        for tieu_de, prompt in viec:
            print("=" * 12, tieu_de)
            print(prompt[:900])
            print()
        print(f"Có {len(viec)} phần. Lệnh này chưa gọi AI.")
        return

    da_co = doc_bai_cu() if args.day_du else {}
    con_lai = sum(1 for tieu_de, _ in viec if tieu_de not in da_co)
    print(f"Sẽ gọi AI {con_lai} lần. Giữ {len(viec) - con_lai} phần đã viết. Ghi vào {KET_QUA.name}.")
    xong: list[tuple[str, str]] = []
    for so, (tieu_de, prompt) in enumerate(viec, start=1):
        if tieu_de in da_co:
            print(f"[{so}/{len(viec)}] Giữ: {tieu_de}")
            xong.append((tieu_de, da_co[tieu_de]))
            continue
        print(f"[{so}/{len(viec)}] {tieu_de}", flush=True)
        van = goi_ai(HE_THONG, prompt)
        xong.append((tieu_de, van))
        ghi_bai(xong)
        time.sleep(4)
    print(f"Xong. Mở file: {KET_QUA}")


if __name__ == "__main__":
    main()
