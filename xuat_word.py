"""
Bước 5: gộp bài phân tích thành file Word.

    .\\venv\\Scripts\\python.exe xuat_word.py
    .\\venv\\Scripts\\python.exe xuat_word.py --laso laso\\ten_file.json

File ra nằm trong thư mục output\\năm-tháng-ngày_giờsinh\\TuVi_Report.docx
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from models import load_chart, thu_muc_bao_cao

ROOT = Path(__file__).resolve().parent
MAU_IN = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*")


def gan_font(run, dam: bool = False, nghieng: bool = False) -> None:
    run.bold = dam
    run.italic = nghieng
    run.font.name = "Times New Roman"
    run.font.size = Pt(13)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")


def them_chu(doan, van: str, dam: bool = False) -> None:
    vi_tri = 0
    for khop in MAU_IN.finditer(van):
        if khop.start() > vi_tri:
            gan_font(doan.add_run(van[vi_tri : khop.start()]), dam)
        if khop.group(1) is not None:
            gan_font(doan.add_run(khop.group(1)), True)
        else:
            gan_font(doan.add_run(khop.group(2)), dam, True)
        vi_tri = khop.end()
    if vi_tri < len(van):
        gan_font(doan.add_run(van[vi_tri:]), dam)


def la_dong_bang(dong: str) -> bool:
    return dong.startswith("|") and dong.endswith("|") and dong.count("|") >= 3


def la_dong_ke(dong: str) -> bool:
    ruot = dong.replace("|", "").replace("-", "").replace(":", "").strip()
    return ruot == ""


def o_bang(dong: str) -> list[str]:
    return [o.strip() for o in dong.strip("|").split("|")]


def ve_bang(tai_lieu, hang: list[list[str]]) -> None:
    if not hang:
        return
    so_cot = max(len(mot) for mot in hang)
    bang = tai_lieu.add_table(rows=len(hang), cols=so_cot)
    bang.style = "Table Grid"
    for i, mot in enumerate(hang):
        for j in range(so_cot):
            chu = mot[j] if j < len(mot) else ""
            o = bang.cell(i, j)
            o.text = ""
            doan = o.paragraphs[0]
            gan_font(doan.add_run(chu), i == 0)


def them_thong_tin(tai_lieu, laso: Path | None) -> None:
    chart = load_chart(laso)
    tieu_de = tai_lieu.add_heading("Báo cáo lá số Tử Vi", level=0)
    for run in tieu_de.runs:
        gan_font(run, True)
        run.font.size = Pt(18)
    dong = [
        f"Giới tính: {chart.gioi_tinh}. {chart.am_duong}.",
        f"Sinh: {chart.ngay_sinh}, giờ hành chính {chart.gio_hanh_chinh}, giờ mặt trời {chart.gio_mat_troi}.",
        f"Âm lịch: {chart.am_lich}. Nơi sinh: {chart.noi_sinh}.",
        f"Bản mệnh {chart.ban_menh}. Cục {chart.cuc}, khởi vận {chart.khoi_van_tuoi} tuổi. Thân cư {chart.than_cu}.",
        "Phần dưới chỉ tổng hợp từ sách Tử Vi Đẩu Số Tân Biên.",
    ]
    for cau in dong:
        doan = tai_lieu.add_paragraph()
        them_chu(doan, cau)


def xuat(laso: str | None = None) -> None:
    chart_path = None
    if laso:
        chart_path = Path(laso)
        if not chart_path.is_file():
            chart_path = ROOT / "laso" / laso
        if not chart_path.is_file():
            raise SystemExit(f"Không thấy file lá số: {laso}")
        chart = load_chart(chart_path)
    else:
        chart = load_chart()
    thu_muc = thu_muc_bao_cao(chart)
    nguon = thu_muc / "phan_tich.md"
    dich = thu_muc / "TuVi_Report.docx"
    if not nguon.is_file():
        raise SystemExit(f"Chưa có bài phân tích: {nguon}")
    tai_lieu = Document()
    for section in tai_lieu.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)
    them_thong_tin(tai_lieu, chart_path)

    cac_dong = nguon.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(cac_dong):
        dong = cac_dong[i].strip()
        if not dong or dong == "# Phân tích lá số" or dong.startswith("Cách viết:"):
            i += 1
            continue
        if la_dong_bang(dong):
            hang = []
            while i < len(cac_dong) and la_dong_bang(cac_dong[i].strip()):
                if not la_dong_ke(cac_dong[i].strip()):
                    hang.append(o_bang(cac_dong[i].strip()))
                i += 1
            ve_bang(tai_lieu, hang)
            continue
        if dong.startswith("## "):
            tieu = tai_lieu.add_heading(dong[3:].strip(), level=1)
            for run in tieu.runs:
                gan_font(run, True)
                run.font.size = Pt(16)
            i += 1
            continue
        if dong.startswith("* ") or dong.startswith("- "):
            doan = tai_lieu.add_paragraph(style="List Bullet")
            them_chu(doan, dong[2:].strip())
            i += 1
            continue
        doan = tai_lieu.add_paragraph()
        them_chu(doan, dong)
        i += 1

    tai_lieu.save(dich)
    print(f"Xong. Mở file: {dich}")


if __name__ == "__main__":
    import argparse

    tham_so = argparse.ArgumentParser(description="Xuất bài phân tích ra file Word.")
    tham_so.add_argument("--laso", help="Cùng file lá số đã dùng với analyze.py, nếu không phải lá số mẫu.")
    xuat(tham_so.parse_args().laso)
