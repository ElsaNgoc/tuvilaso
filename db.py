"""
Create the tables.

The local machine uses the file du_lieu/tuvilaso.db.
When TURSO_DATABASE_URL and TURSO_AUTH_TOKEN are set, the tables live on Turso.
Render only serves the site and keeps no data.

    .\\venv\\Scripts\\python.exe db.py
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
THU_MUC = ROOT / "du_lieu"
TEP = THU_MUC / "tuvilaso.db"

LENH = """
CREATE TABLE IF NOT EXISTS tai_khoan (
    ma INTEGER PRIMARY KEY,
    ten_dang_nhap TEXT NOT NULL UNIQUE,
    mat_khau TEXT NOT NULL,
    luc_tao TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS la_so (
    ma INTEGER PRIMARY KEY,
    ma_tai_khoan INTEGER REFERENCES tai_khoan(ma) ON DELETE CASCADE,
    ma_phien TEXT,
    ten TEXT,
    luc_tao TEXT NOT NULL DEFAULT (datetime('now')),
    gioi_tinh TEXT NOT NULL,
    ngay_sinh TEXT NOT NULL,
    gio_hanh_chinh TEXT NOT NULL,
    gio_mat_troi TEXT NOT NULL,
    am_lich TEXT NOT NULL,
    noi_sinh TEXT NOT NULL,
    am_duong TEXT NOT NULL,
    ban_menh TEXT NOT NULL,
    cuc TEXT NOT NULL,
    khoi_van_tuoi INTEGER NOT NULL,
    than_cu TEXT NOT NULL,
    ban_day_du TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bai_phan_tich (
    ma INTEGER PRIMARY KEY,
    ma_la_so INTEGER NOT NULL REFERENCES la_so(ma) ON DELETE CASCADE,
    nam_xem INTEGER NOT NULL,
    tuoi INTEGER NOT NULL,
    noi_dung TEXT NOT NULL DEFAULT '',
    tep_word TEXT NOT NULL DEFAULT '',
    trang_thai TEXT NOT NULL DEFAULT 'dang_viet' CHECK (trang_thai IN ('dang_viet', 'xong', 'loi')),
    luc_xong TEXT,
    UNIQUE (ma_la_so, nam_xem)
);

CREATE TABLE IF NOT EXISTS hoi_dap (
    ma INTEGER PRIMARY KEY,
    ma_la_so INTEGER NOT NULL REFERENCES la_so(ma) ON DELETE CASCADE,
    ma_bai INTEGER REFERENCES bai_phan_tich(ma) ON DELETE SET NULL,
    nguoi_gui TEXT NOT NULL CHECK (nguoi_gui IN ('nguoi', 'may')),
    noi_dung TEXT NOT NULL,
    luc TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS phien (
    ma INTEGER PRIMARY KEY,
    ma_tai_khoan INTEGER NOT NULL REFERENCES tai_khoan(ma) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    luc_het TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS la_so_theo_tai_khoan ON la_so(ma_tai_khoan);
CREATE INDEX IF NOT EXISTS la_so_theo_phien ON la_so(ma_phien);
CREATE INDEX IF NOT EXISTS bai_theo_la_so ON bai_phan_tich(ma_la_so);
CREATE INDEX IF NOT EXISTS hoi_theo_la_so ON hoi_dap(ma_la_so);
"""


class Dong(dict):
    """One row, accessible by column name or by index."""

    def __getitem__(self, khoa):
        if isinstance(khoa, int):
            return list(self.values())[khoa]
        return dict.__getitem__(self, khoa)


class Bang:
    def __init__(self, con_tro):
        self.con_tro = con_tro

    def _dong(self, hang):
        if hang is None:
            return None
        if isinstance(hang, sqlite3.Row):
            return hang
        ten = [cot[0] for cot in self.con_tro.description]
        return Dong(zip(ten, hang))

    def fetchone(self):
        return self._dong(self.con_tro.fetchone())

    def fetchall(self):
        return [self._dong(hang) for hang in self.con_tro.fetchall()]

    def __iter__(self):
        for hang in self.con_tro:
            yield self._dong(hang)


class KetNoi:
    def __init__(self, goc):
        self.goc = goc

    def execute(self, cau, tham=()):
        return Bang(self.goc.execute(cau, tham))

    def executescript(self, chuoi: str) -> None:
        if hasattr(self.goc, "executescript"):
            self.goc.executescript(chuoi)
            return
        for cau in chuoi.split(";"):
            if cau.strip():
                self.goc.execute(cau)

    def __enter__(self):
        return self

    def __exit__(self, loai, _gia, _vet) -> bool:
        if loai is None:
            self.goc.commit()
        else:
            self.goc.rollback()
        self.goc.close()
        return False


def _tai_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except Exception:
        return


def mo() -> KetNoi:
    _tai_env()
    url = os.environ.get("TURSO_DATABASE_URL", "").strip()
    token = os.environ.get("TURSO_AUTH_TOKEN", "").strip()
    if url and token:
        import turso_serverless

        goc = turso_serverless.connect(url, auth_token=token)
    else:
        THU_MUC.mkdir(parents=True, exist_ok=True)
        goc = sqlite3.connect(TEP)
        goc.row_factory = sqlite3.Row
        goc.execute("PRAGMA foreign_keys = ON")
    return KetNoi(goc)


def _them_cot(ket: KetNoi, bang: str, cot: str, kieu: str) -> None:
    co = {dong[1] for dong in ket.execute(f"PRAGMA table_info({bang})")}
    if cot not in co:
        ket.execute(f"ALTER TABLE {bang} ADD COLUMN {cot} {kieu}")


def tao() -> Path:
    with mo() as ket:
        ket.executescript(LENH)
        _them_cot(ket, "tai_khoan", "email", "TEXT")
        _them_cot(ket, "tai_khoan", "google_sub", "TEXT")
        _them_cot(ket, "bai_phan_tich", "noi_word", "BLOB")
        ket.execute("CREATE UNIQUE INDEX IF NOT EXISTS tai_khoan_email ON tai_khoan(email)")
        ket.execute("CREATE UNIQUE INDEX IF NOT EXISTS tai_khoan_google ON tai_khoan(google_sub)")
    return TEP


if __name__ == "__main__":
    tep = tao()
    with mo() as ket:
        bang = [dong[0] for dong in ket.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
    if os.environ.get("TURSO_DATABASE_URL", "").strip() and os.environ.get("TURSO_AUTH_TOKEN", "").strip():
        print("Xong. Các bảng nằm ở Turso.")
    else:
        print(f"Xong. File: {tep}")
    print("Các bảng: " + ", ".join(bang))
