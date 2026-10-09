"""Tạo tài khoản, đăng nhập và phiên làm việc."""

from __future__ import annotations

import hashlib
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from db import mo

TEN = re.compile(r"^[\w]{3,40}$", re.UNICODE)
HAN_PHIEN = 30


class LoiTaiKhoan(ValueError):
    pass


def _bay_gio() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _het_han() -> str:
    luc = datetime.now(timezone.utc) + timedelta(days=HAN_PHIEN)
    return luc.strftime("%Y-%m-%d %H:%M:%S")


def bam_mat_khau(mat_khau: str, muoi: bytes | None = None) -> str:
    if muoi is None:
        muoi = secrets.token_bytes(16)
    khoa = hashlib.pbkdf2_hmac("sha256", mat_khau.encode("utf-8"), muoi, 200_000)
    return muoi.hex() + "$" + khoa.hex()


def khop_mat_khau(mat_khau: str, da_bam: str) -> bool:
    muoi_hex, _khoa = da_bam.split("$", 1)
    thu = bam_mat_khau(mat_khau, bytes.fromhex(muoi_hex))
    return secrets.compare_digest(thu, da_bam)


def kiem_ten(ten: str) -> str:
    chu = ten.strip()
    if not TEN.fullmatch(chu):
        raise LoiTaiKhoan("Tên đăng nhập từ 3 đến 40 ký tự, không có dấu cách.")
    return chu


def kiem_mat_khau(mat_khau: str) -> str:
    if len(mat_khau) < 8 or len(mat_khau) > 72:
        raise LoiTaiKhoan("Mật khẩu cần từ 8 đến 72 ký tự.")
    return mat_khau


def _mo_phien(ket: sqlite3.Connection, ma_tai_khoan: int) -> str:
    token = secrets.token_urlsafe(32)
    ket.execute(
        "INSERT INTO phien (ma_tai_khoan, token, luc_het) VALUES (?, ?, ?)",
        (ma_tai_khoan, token, _het_han()),
    )
    return token


def dang_ky(ten: str, mat_khau: str) -> tuple[str, str]:
    chu = kiem_ten(ten)
    khoa = kiem_mat_khau(mat_khau)
    with mo() as ket:
        try:
            ket.execute(
                "INSERT INTO tai_khoan (ten_dang_nhap, mat_khau) VALUES (?, ?)",
                (chu, bam_mat_khau(khoa)),
            )
        except sqlite3.IntegrityError as loi:
            raise LoiTaiKhoan("Tên này đã có người dùng.") from loi
        ma = ket.execute("SELECT last_insert_rowid()").fetchone()[0]
        token = _mo_phien(ket, ma)
    return chu, token


def dang_nhap_google(token: str) -> tuple[str, str]:
    """Nhận mã Google gửi về, tạo tài khoản nếu Gmail này chưa có."""
    import os

    ma_trang = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    if not ma_trang:
        raise LoiTaiKhoan("Chưa có mã Gmail. Thêm GOOGLE_CLIENT_ID vào file .env rồi mở lại chương trình.")
    if not token:
        raise LoiTaiKhoan("Google không nhận lần đăng nhập này.")
    try:
        from google.auth.transport import requests as yeu_cau_google
        from google.oauth2 import id_token

        info = id_token.verify_oauth2_token(token, yeu_cau_google.Request(), ma_trang)
    except Exception as loi:
        raise LoiTaiKhoan("Google không nhận lần đăng nhập này.") from loi
    if not info.get("email_verified"):
        raise LoiTaiKhoan("Gmail này chưa được xác nhận.")
    email = str(info.get("email", "")).strip().lower()
    sub = str(info.get("sub", "")).strip()
    if not email or not sub:
        raise LoiTaiKhoan("Google không gửi đủ email.")
    with mo() as ket:
        dong = ket.execute(
            "SELECT ma, email FROM tai_khoan WHERE google_sub = ?",
            (sub,),
        ).fetchone()
        if dong is None:
            dong = ket.execute(
                "SELECT ma, email FROM tai_khoan WHERE email = ?",
                (email,),
            ).fetchone()
            if dong is not None:
                ket.execute("UPDATE tai_khoan SET google_sub = ? WHERE ma = ?", (sub, dong["ma"]))
        if dong is None:
            ket.execute(
                "INSERT INTO tai_khoan (ten_dang_nhap, mat_khau, email, google_sub) VALUES (?, ?, ?, ?)",
                (email, bam_mat_khau(secrets.token_urlsafe(24)), email, sub),
            )
            ma = int(ket.execute("SELECT last_insert_rowid()").fetchone()[0])
        else:
            ma = int(dong["ma"])
        phien = _mo_phien(ket, ma)
    return email, phien


def dang_nhap(ten: str, mat_khau: str) -> tuple[str, str]:
    chu = ten.strip()
    with mo() as ket:
        dong = ket.execute(
            "SELECT ma, ten_dang_nhap, mat_khau FROM tai_khoan WHERE ten_dang_nhap = ?",
            (chu,),
        ).fetchone()
        if dong is None or not khop_mat_khau(mat_khau, dong["mat_khau"]):
            raise LoiTaiKhoan("Tên hoặc mật khẩu chưa đúng.")
        ten_that = dong["ten_dang_nhap"]
        token = _mo_phien(ket, dong["ma"])
    return ten_that, token


def dang_xuat(token: str) -> None:
    if not token:
        return
    with mo() as ket:
        ket.execute("DELETE FROM phien WHERE token = ?", (token,))


def tai_khoan_tu_token(token: str) -> tuple[int, str] | None:
    if not token:
        return None
    with mo() as ket:
        dong = ket.execute(
            """
            SELECT tai_khoan.ma AS ma, tai_khoan.ten_dang_nhap AS ten
            FROM phien
            JOIN tai_khoan ON tai_khoan.ma = phien.ma_tai_khoan
            WHERE phien.token = ? AND phien.luc_het > ?
            """,
            (token, _bay_gio()),
        ).fetchone()
    if dong is None:
        return None
    return int(dong["ma"]), dong["ten"]


def ten_tu_token(token: str) -> str | None:
    cap = tai_khoan_tu_token(token)
    if cap is None:
        return None
    return cap[1]


def banh_phien(token: str, an_toan: bool = False) -> str:
    giay = HAN_PHIEN * 24 * 3600
    khoa = "; Secure" if an_toan else ""
    return f"phien={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={giay}{khoa}"


def banh_xoa(an_toan: bool = False) -> str:
    khoa = "; Secure" if an_toan else ""
    return f"phien=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0{khoa}"
