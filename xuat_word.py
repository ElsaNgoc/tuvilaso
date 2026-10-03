"""
Bước 5: gộp bài phân tích thành file Word.

    .\\venv\\Scripts\\python.exe xuat_word.py

File ra: output\\TuVi_Report.docx
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from models import load_chart

ROOT = Path(__file__).resolve().parent
NGUON = ROOT / "output" / "phan_tich.md"
DICH = ROOT / "output" / "TuVi_Report.docx"
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


def them_thong_tin(tai_lieu) -> None:
    chart = load_chart()
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


def xuat() -> None:
    if not NGUON.is_file():
        raise SystemExit("Chưa có output\\phan_tich.md. Hãy chạy analyze.py trước.")
    tai_lieu = Document()
    for section in tai_lieu.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)
    them_thong_tin(tai_lieu)

    for raw in NGUON.read_text(encoding="utf-8").splitlines():
        dong = raw.strip()
        if not dong or dong == "# Phân tích lá số":
            continue
        if dong.startswith("## "):
            tieu = tai_lieu.add_heading(dong[3:].strip(), level=1)
            for run in tieu.runs:
                gan_font(run, True)
                run.font.size = Pt(16)
            continue
        if dong.startswith("* ") or dong.startswith("- "):
            doan = tai_lieu.add_paragraph(style="List Bullet")
            them_chu(doan, dong[2:].strip())
            continue
        doan = tai_lieu.add_paragraph()
        them_chu(doan, dong)

    tai_lieu.save(DICH)
    print(f"Xong. Mở file: {DICH}")


if __name__ == "__main__":
    xuat()
