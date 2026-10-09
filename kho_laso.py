"""Lưu lá số, bài phân tích và câu hỏi vào database."""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from db import mo
from models import Chart

ROOT = Path(__file__).resolve().parent


def don_khach_cu() -> None:
    """Xóa lá số khách để quá 12 giờ, trừ bài đang viết."""
    with mo() as ket:
        ket.execute(
            """
            DELETE FROM la_so
            WHERE ma_tai_khoan IS NULL
              AND luc_tao < datetime('now', '-12 hours')
              AND ma NOT IN (
                SELECT ma_la_so FROM bai_phan_tich WHERE trang_thai = 'dang_viet'
              )
            """
        )


def _nam(ngay_sinh: str) -> int:
    nam = str(ngay_sinh).rsplit("/", 1)[-1]
    if not nam.isdigit():
        raise ValueError("Ngày sinh không có năm.")
    return int(nam)


def bat_dau(chart: Chart, ban_goc: str, ten_nguoi: str, ma_tai_khoan: int | None, ma_phien: str) -> int:
    ten = ten_nguoi.strip() or "Người xem"
    with mo() as ket:
        if ma_tai_khoan is None:
            ket.execute(
                """
                DELETE FROM la_so
                WHERE ma_tai_khoan IS NULL AND ma_phien = ?
                  AND ma NOT IN (
                    SELECT ma_la_so FROM bai_phan_tich WHERE trang_thai = 'dang_viet'
                  )
                """,
                (ma_phien,),
            )
            ma_la = None
        else:
            cu = ket.execute(
                """
                SELECT ma FROM la_so
                WHERE ma_tai_khoan = ? AND ten = ? AND ngay_sinh = ? AND gio_hanh_chinh = ?
                """,
                (ma_tai_khoan, ten, chart.ngay_sinh, chart.gio_hanh_chinh),
            ).fetchone()
            ma_la = None if cu is None else int(cu["ma"])
        if ma_la is None:
            ket.execute(
                """
                INSERT INTO la_so (
                    ma_tai_khoan, ma_phien, ten, gioi_tinh, ngay_sinh, gio_hanh_chinh,
                    gio_mat_troi, am_lich, noi_sinh, am_duong, ban_menh, cuc,
                    khoi_van_tuoi, than_cu, ban_day_du
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ma_tai_khoan,
                    None if ma_tai_khoan else ma_phien,
                    ten if ma_tai_khoan else ten,
                    chart.gioi_tinh,
                    chart.ngay_sinh,
                    chart.gio_hanh_chinh,
                    chart.gio_mat_troi,
                    chart.am_lich,
                    chart.noi_sinh,
                    chart.am_duong,
                    chart.ban_menh,
                    chart.cuc,
                    chart.khoi_van_tuoi,
                    chart.than_cu,
                    ban_goc,
                ),
            )
            ma_la = int(ket.execute("SELECT last_insert_rowid()").fetchone()[0])
        else:
            ket.execute(
                "UPDATE la_so SET ban_day_du = ?, ban_menh = ?, cuc = ?, than_cu = ? WHERE ma = ?",
                (ban_goc, chart.ban_menh, chart.cuc, chart.than_cu, ma_la),
            )
        nam_xem = date.today().year
        tuoi = nam_xem - _nam(chart.ngay_sinh)
        co = ket.execute(
            "SELECT ma FROM bai_phan_tich WHERE ma_la_so = ? AND nam_xem = ?",
            (ma_la, nam_xem),
        ).fetchone()
        if co is None:
            ket.execute(
                """
                INSERT INTO bai_phan_tich (ma_la_so, nam_xem, tuoi, trang_thai)
                VALUES (?, ?, ?, 'dang_viet')
                """,
                (ma_la, nam_xem, tuoi),
            )
        else:
            ket.execute(
                "UPDATE bai_phan_tich SET trang_thai = 'dang_viet', tuoi = ? WHERE ma = ?",
                (tuoi, int(co["ma"])),
            )
    return ma_la


def hoan_tat(ma_la: int, noi_dung: str, tep_word: Path) -> str:
    thu = ROOT / "output" / "theo_ma" / str(ma_la)
    thu.mkdir(parents=True, exist_ok=True)
    dich = thu / "TuVi_Report.docx"
    shutil.copy2(tep_word, dich)
    tuong_doi = str(dich.relative_to(ROOT))
    with mo() as ket:
        ket.execute(
            """
            UPDATE bai_phan_tich
            SET noi_dung = ?, tep_word = ?, trang_thai = 'xong', luc_xong = datetime('now')
            WHERE ma_la_so = ? AND nam_xem = ?
            """,
            (noi_dung, tuong_doi, ma_la, date.today().year),
        )
    return tuong_doi


def danh_loi(ma_la: int) -> None:
    with mo() as ket:
        ket.execute(
            """
            UPDATE bai_phan_tich SET trang_thai = 'loi'
            WHERE ma_la_so = ? AND nam_xem = ? AND trang_thai = 'dang_viet'
            """,
            (ma_la, date.today().year),
        )


def _duoc_xem(dong, ma_tai_khoan: int | None, ma_phien: str) -> bool:
    if dong is None:
        return False
    if ma_tai_khoan is not None:
        return dong["ma_tai_khoan"] == ma_tai_khoan
    return dong["ma_tai_khoan"] is None and dong["ma_phien"] == ma_phien


def danh_sach(ma_tai_khoan: int | None, ma_phien: str) -> list[dict]:
    with mo() as ket:
        if ma_tai_khoan is not None:
            hang = ket.execute(
                """
                SELECT ma, ten, ngay_sinh, gio_hanh_chinh
                FROM la_so WHERE ma_tai_khoan = ?
                ORDER BY luc_tao DESC
                """,
                (ma_tai_khoan,),
            ).fetchall()
        else:
            hang = ket.execute(
                """
                SELECT ma, ten, ngay_sinh, gio_hanh_chinh
                FROM la_so WHERE ma_tai_khoan IS NULL AND ma_phien = ?
                ORDER BY luc_tao DESC
                """,
                (ma_phien,),
            ).fetchall()
    return [dict(mot) for mot in hang]


def lay_la_so(ma: int, ma_tai_khoan: int | None, ma_phien: str):
    with mo() as ket:
        dong = ket.execute("SELECT * FROM la_so WHERE ma = ?", (ma,)).fetchone()
    if not _duoc_xem(dong, ma_tai_khoan, ma_phien):
        return None
    return dong


def bai_moi(ma: int, ma_tai_khoan: int | None, ma_phien: str) -> dict | None:
    if lay_la_so(ma, ma_tai_khoan, ma_phien) is None:
        return None
    with mo() as ket:
        dong = ket.execute(
            """
            SELECT noi_dung, tep_word, nam_xem, tuoi, trang_thai
            FROM bai_phan_tich
            WHERE ma_la_so = ? AND trang_thai = 'xong'
            ORDER BY nam_xem DESC LIMIT 1
            """,
            (ma,),
        ).fetchone()
        la = ket.execute("SELECT ten FROM la_so WHERE ma = ?", (ma,)).fetchone()
    if dong is None:
        return None
    return {
        "ma": ma,
        "ten_nguoi": la["ten"],
        "nam_xem": dong["nam_xem"],
        "tuoi": dong["tuoi"],
        "noi_dung": dong["noi_dung"],
        "tep_word": dong["tep_word"],
    }


def tep_word(ma: int, ma_tai_khoan: int | None, ma_phien: str) -> Path | None:
    bai = bai_moi(ma, ma_tai_khoan, ma_phien)
    if bai is None or not bai["tep_word"]:
        return None
    tep = (ROOT / bai["tep_word"]).resolve()
    goc = (ROOT / "output" / "theo_ma").resolve()
    if goc not in tep.parents or not tep.is_file():
        return None
    return tep


def nam_cua(ma: int, ma_tai_khoan: int | None, ma_phien: str) -> tuple[int, str] | None:
    dong = lay_la_so(ma, ma_tai_khoan, ma_phien)
    if dong is None:
        return None
    return _nam(dong["ngay_sinh"]), dong["ten"] or ""


def la_so_gan(ma_tai_khoan: int | None, ma_phien: str) -> int | None:
    ds = danh_sach(ma_tai_khoan, ma_phien)
    if not ds:
        return None
    return int(ds[0]["ma"])


def noi_bai(ma: int, ma_tai_khoan: int | None, ma_phien: str) -> str | None:
    bai = bai_moi(ma, ma_tai_khoan, ma_phien)
    if bai is None:
        return None
    return bai["noi_dung"]


def ghi_cau(ma_la: int, ma_bai: int | None, nguoi_gui: str, noi_dung: str) -> None:
    with mo() as ket:
        ket.execute(
            "INSERT INTO hoi_dap (ma_la_so, ma_bai, nguoi_gui, noi_dung) VALUES (?, ?, ?, ?)",
            (ma_la, ma_bai, nguoi_gui, noi_dung),
        )


def ma_bai(ma_la: int) -> int | None:
    with mo() as ket:
        dong = ket.execute(
            """
            SELECT ma FROM bai_phan_tich
            WHERE ma_la_so = ? AND trang_thai = 'xong'
            ORDER BY nam_xem DESC LIMIT 1
            """,
            (ma_la,),
        ).fetchone()
    if dong is None:
        return None
    return int(dong["ma"])


def lich_su(ma_la: int, ma_tai_khoan: int | None, ma_phien: str) -> list[dict] | None:
    if lay_la_so(ma_la, ma_tai_khoan, ma_phien) is None:
        return None
    with mo() as ket:
        hang = ket.execute(
            """
            SELECT nguoi_gui, noi_dung FROM hoi_dap
            WHERE ma_la_so = ? ORDER BY ma DESC LIMIT 12
            """,
            (ma_la,),
        ).fetchall()
    return [{"nguoi_gui": mot["nguoi_gui"], "noi_dung": mot["noi_dung"]} for mot in reversed(hang)]
