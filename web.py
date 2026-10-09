"""
Trang dán lá số. Bài hiện trên trang, nút bên cạnh tải file Word.

Mở trang:
    .\\venv\\Scripts\\python.exe web.py

Rồi vào trình duyệt: http://127.0.0.1:8765
"""

from __future__ import annotations

import html
import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time
import traceback
import urllib.parse
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dotenv import load_dotenv

from db import tao as tao_db
from kho_laso import (
    bai_moi,
    bat_dau,
    danh_loi,
    danh_sach,
    don_khach_cu,
    ghi_cau,
    hoan_tat,
    la_so_gan,
    lich_su,
    ma_bai,
    nam_cua,
    noi_bai,
    byte_word,
)
from models import load_chart, thu_muc_bao_cao
from tai_khoan import (
    LoiTaiKhoan,
    banh_phien,
    banh_xoa,
    dang_nhap_google,
    dang_xuat,
    tai_khoan_tu_token,
    ten_tu_token,
)
from ngay import TRUC, doc_truc, loi_theo_tuoi, truc_cua_ngay
from nhap_laso import chuyen

ROOT = Path(__file__).resolve().parent
CONG = 8765
KHOA = threading.Lock()
KHOA_DEM = threading.Lock()
# Số giây còn lại. Mỗi chương một mức, rồi giảm 1 mỗi giây cho tới khi xong.
TIEN_DO = {"con": None}
CAC_BUOC = (
    ("[1/4]", 405),
    ("[2/4]", 360),
    ("[3/4]", 210),
    ("Phần 2", 160),
    ("[4/4]", 70),
    ("Xong.", 15),
)
TAM = ROOT / "laso" / "vua_dan.txt"


def nam_sinh_da_dan() -> int | None:
    tep = ROOT / "laso" / "vua_dan.json"
    if not tep.is_file():
        return None
    data = json.loads(tep.read_text(encoding="utf-8"))
    nam = str(data.get("ngay_sinh", "")).rsplit("/", 1)[-1]
    if not nam.isdigit():
        return None
    return int(nam)


def goi_hom_nay(chi_thang: str, chi_ngay: str, nam: int | None = None, ten_nguoi: str = "") -> dict:
    ten = truc_cua_ngay(chi_thang, chi_ngay)
    if nam is None:
        return {
            "truc": ten,
            "cat_hung": doc_truc()[ten]["cat_hung"],
            "nen": "Chưa có lá số để biết tuổi.",
            "cam": "Hãy dán lá số ở trang chính.",
            "tuoi": None,
            "nam_sinh": None,
            "ten_nguoi": "",
        }
    ket = loi_theo_tuoi(ten, date.today().year - nam)
    ket["nam_sinh"] = nam
    ket["ten_nguoi"] = ten_nguoi
    return ket


def liet_ke_truc() -> list[dict]:
    bang = doc_truc()
    return [
        {
            "ten": ten,
            "cat_hung": bang[ten]["cat_hung"],
            "nen": bang[ten]["nen"],
            "kieng": bang[ten]["kieng"],
        }
        for ten in TRUC
    ]


def bai_gan_nhat() -> dict | None:
    tep = ROOT / "laso" / "vua_dan.json"
    if not tep.is_file():
        return None
    chart = load_chart(tep)
    thu_muc = thu_muc_bao_cao(chart)
    bai = thu_muc / "phan_tich.md"
    if not bai.is_file():
        return None
    return {"ten": f"TuVi_{thu_muc.name}.docx", "html": html_bai(bai.read_text(encoding="utf-8"))}


def hoi_la_so(cau: str, chi_thang: str, chi_ngay: str, cac_cau: list, van: str, nam: int | None, ten_nguoi: str) -> str:
    if not van:
        raise ValueError("Chưa có bài phân tích. Hãy bấm Bắt đầu trước.")
    if len(van) > 24000:
        van = van[:24000]
    hom_nay = ""
    if chi_thang and chi_ngay:
        try:
            viec = goi_hom_nay(chi_thang, chi_ngay, nam, ten_nguoi)
            hom_nay = (
                f"\nHôm nay là Trực {viec['truc']}, {viec['cat_hung']}. "
                f"Nên: {viec['nen']} Kỵ: {viec['cam']}\n"
            )
        except ValueError:
            hom_nay = ""
    trao = []
    for mot in cac_cau[-6:]:
        if not isinstance(mot, dict):
            continue
        hoi = str(mot.get("hoi", ""))[:500]
        dap = str(mot.get("dap", ""))[:800]
        if hoi:
            trao.append(f"Hỏi: {hoi}\nĐáp: {dap}")
    from analyze import goi_ai

    he = (
        "Bạn giải thích bài phân tích lá số đã viết sẵn. "
        "Chỉ dùng bài và câu hôm nay được đưa. Không bịa sao, không bịa Trực. "
        "Giữ đúng lứa tuổi trong bài, không khuyên trẻ em việc của người lớn. "
        "Viết tiếng Việt mộc mạc, vài câu, không dùng dấu sao. "
        "Nếu bài không có ý đó thì nói bài chưa viết phần này."
    )
    goi = f"Bài phân tích:\n{van}\n{hom_nay}\n"
    if trao:
        goi += "Các câu trước:\n" + "\n".join(trao) + "\n"
    goi += f"Câu hỏi: {cau}"
    return goi_ai(he, goi).strip()



TEN_WORD = re.compile(r"^TuVi_(\d{4}-\d{2}-\d{2}_\d{2}h\d{2})\.docx$")


def in_dam(van: str) -> str:
    """Đổi chữ đậm và link nội bộ thành thẻ, sau khi đã thoát ký tự HTML."""
    phan = re.split(r"(\[[^\]]+\]\(/[^)]+\))", van)
    roi = []
    for mot in phan:
        khop = re.fullmatch(r"\[([^\]]+)\]\((/[^)]+)\)", mot)
        if khop:
            duong = html.escape(khop.group(2), quote=True)
            roi.append(f'<a href="{duong}">{html.escape(khop.group(1))}</a>')
            continue
        an_toan = html.escape(mot)
        an_toan = re.sub(r"&lt;br\s*/?&gt;", "<br>", an_toan, flags=re.I)
        roi.append(re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", an_toan))
    return "".join(roi)


def la_dong_ke(dong: str) -> bool:
    return dong.replace("|", "").replace("-", "").replace(":", "").strip() == ""


def o_bang(dong: str) -> list[str]:
    return [o.strip() for o in dong.strip("|").split("|")]


def html_bang(hang: list[list[str]]) -> str:
    if not hang:
        return ""
    dau = "".join(f"<th>{in_dam(o)}</th>" for o in hang[0])
    than = []
    for mot in hang[1:]:
        than.append("<tr>" + "".join(f"<td>{in_dam(o)}</td>" for o in mot) + "</tr>")
    return "<table><thead><tr>" + dau + "</tr></thead><tbody>" + "".join(than) + "</tbody></table>"


def html_bai(van: str) -> str:
    """Đổi bài markdown thành HTML để hiện trên trang. Chữ lấy từ bài đã thoát ký tự."""
    dong = van.splitlines()
    khoi: list[str] = []
    i = 0
    while i < len(dong):
        chu = dong[i].strip()
        if not chu or chu == "# Phân tích lá số" or chu.startswith("Cách viết:") or chu == "---":
            i += 1
            continue
        if chu.startswith("|") and chu.endswith("|"):
            hang: list[list[str]] = []
            while i < len(dong) and dong[i].strip().startswith("|") and dong[i].strip().endswith("|"):
                if not la_dong_ke(dong[i].strip()):
                    hang.append(o_bang(dong[i].strip()))
                i += 1
            khoi.append(html_bang(hang))
            continue
        if chu.startswith("## "):
            khoi.append(f"<h2>{in_dam(chu[3:].strip())}</h2>")
            i += 1
            continue
        if chu.startswith("- ") or chu.startswith("* "):
            muc = []
            while i < len(dong) and (
                dong[i].strip().startswith("- ") or dong[i].strip().startswith("* ")
            ):
                muc.append(f"<li>{in_dam(dong[i].strip()[2:].strip())}</li>")
                i += 1
            khoi.append("<ul>" + "".join(muc) + "</ul>")
            continue
        khoi.append(f"<p>{in_dam(chu)}</p>")
        i += 1
    return "\n".join(khoi)


def tim_word(ten: str) -> Path | None:
    khop = TEN_WORD.fullmatch(urllib.parse.unquote(ten))
    if not khop:
        return None
    tep = ROOT / "output" / khop.group(1) / "TuVi_Report.docx"
    if tep.is_file():
        return tep
    return None


def dat_con(giay: int | None) -> None:
    with KHOA_DEM:
        TIEN_DO["con"] = giay


def giam_moi_giay() -> None:
    while True:
        time.sleep(1)
        with KHOA_DEM:
            con = TIEN_DO["con"]
            if con is not None and con > 1:
                TIEN_DO["con"] = con - 1


def chay_viet(lenh: list[str], moi_truong: dict) -> tuple[int, str]:
    """Chạy phần viết bài và chỉnh số giây còn lại theo chương đang viết."""
    dat_con(CAC_BUOC[0][1] + 25)
    tien = subprocess.Popen(
        lenh,
        cwd=ROOT,
        env=moi_truong,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    dong_ra: list[str] = []
    bat_dau = time.time()
    assert tien.stdout is not None
    for dong in tien.stdout:
        dong_ra.append(dong)
        for moc, giay in CAC_BUOC:
            if moc in dong:
                dat_con(giay)
        if time.time() - bat_dau > 1200:
            tien.kill()
            break
    return tien.wait(), "".join(dong_ra)


def phan_tich_bai(bai: str):
    """Đổi bài dán thành lá số, viết báo cáo, trả file Word, tên tải về và HTML để hiện trang."""
    chu = bai.strip()
    if len(chu) < 80:
        raise ValueError("Bài dán còn quá ngắn. Hãy dán đủ thông tin, tứ trụ và bảng 12 cung.")
    TAM.parent.mkdir(parents=True, exist_ok=True)
    TAM.write_text(chu, encoding="utf-8")
    try:
        tep_json = chuyen(TAM)
    except Exception as loi:
        raise ValueError(
            "Chưa đọc được lá số trong bài dán.\n"
            "Bài cần có mục thông tin, bảng tứ trụ và bảng 12 cung, giống mẫu đã dùng trước đây.\n"
            f"Chi tiết: {loi}"
        ) from loi
    chart = load_chart(tep_json)
    thu_muc = thu_muc_bao_cao(chart)
    lenh = [
        sys.executable,
        str(ROOT / "analyze.py"),
        "--laso",
        str(tep_json),
        "--day-du",
    ]
    moi_truong = dict(os.environ)
    moi_truong["PYTHONIOENCODING"] = "utf-8"
    ma_thoat, nhat_ky = chay_viet(lenh, moi_truong)
    word = thu_muc / "TuVi_Report.docx"
    bai_md = thu_muc / "phan_tich.md"
    if ma_thoat != 0 or not word.is_file() or not bai_md.is_file():
        raise RuntimeError("Chưa viết xong báo cáo.\n" + nhat_ky[-1200:].strip())
    ten = f"TuVi_{thu_muc.name}.docx"
    return chart, tep_json, word, ten, bai_md.read_text(encoding="utf-8")


class TraLoi(BaseHTTPRequestHandler):
    def log_message(self, dinh_dang: str, *tham_so) -> None:
        print(dinh_dang % tham_so, flush=True)

    def gui(self, ma: int, than: bytes, kieu: str, ten_tep: str = "", cookie: str | list[str] = "") -> None:
        self.send_response(ma)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(than)))
        if ten_tep:
            self.send_header("Content-Disposition", f'attachment; filename="{ten_tep}"')
        danh = [cookie] if isinstance(cookie, str) else list(cookie)
        for mot in danh:
            if mot:
                self.send_header("Set-Cookie", mot)
        self.end_headers()
        self.wfile.write(than)

    def cookie(self, ten_cookie: str) -> str:
        for phan in self.headers.get("Cookie", "").split(";"):
            if "=" not in phan:
                continue
            ten, gia = phan.strip().split("=", 1)
            if ten == ten_cookie:
                return gia
        return ""

    def token_phien(self) -> str:
        return self.cookie("phien")

    def an_toan(self) -> bool:
        if os.environ.get("COOKIE_SECURE") == "1":
            return True
        return self.headers.get("X-Forwarded-Proto", "") == "https"

    def khach(self) -> tuple[str, str]:
        co = self.cookie("khach")
        if co:
            return co, ""
        moi = secrets.token_urlsafe(18)
        khoa = "; Secure" if self.an_toan() else ""
        return moi, f"khach={moi}; Path=/; HttpOnly; SameSite=Lax{khoa}"

    def nguoi_dang_nhap(self) -> tuple[int | None, str, str]:
        """Trả mã tài khoản, mã phiên khách, và cookie khách cần gắn nếu mới tạo."""
        cap = tai_khoan_tu_token(self.token_phien())
        ma_tk = None if cap is None else cap[0]
        ma_phien, banh = self.khach()
        return ma_tk, ma_phien, banh

    def doc_json(self, gioi_han: int) -> dict:
        do_dai = int(self.headers.get("Content-Length", "0"))
        if do_dai > gioi_han:
            raise LoiTaiKhoan("Dữ liệu quá dài.")
        try:
            return json.loads(self.rfile.read(do_dai).decode("utf-8"))
        except json.JSONDecodeError as loi:
            raise LoiTaiKhoan("Không đọc được dữ liệu.") from loi

    def do_GET(self) -> None:
        duong = urllib.parse.unquote(self.path.split("?", 1)[0])
        if duong == "/tien-do":
            with KHOA_DEM:
                con = TIEN_DO["con"]
            than = json.dumps({"con": con}).encode("utf-8")
            self.gui(200, than, "application/json; charset=utf-8")
            return
        if duong == "/cau-hinh":
            than = json.dumps(
                {"google_client_id": os.environ.get("GOOGLE_CLIENT_ID", "").strip()},
                ensure_ascii=False,
            ).encode("utf-8")
            self.gui(200, than, "application/json; charset=utf-8")
            return
        if duong == "/":
            _phien, banh = self.khach()
            noi = (ROOT / "trang_chinh.html").read_text(encoding="utf-8")
            self.gui(200, noi.encode("utf-8"), "text/html; charset=utf-8", cookie=banh)
            return
        if duong == "/ngay":
            noi = (ROOT / "trang_ngay.html").read_text(encoding="utf-8")
            self.gui(200, noi.encode("utf-8"), "text/html; charset=utf-8")
            return
        if duong == "/thu_vien/lunar.js":
            tep = ROOT / "thu_vien" / "lunar.js"
            self.gui(200, tep.read_bytes(), "application/javascript; charset=utf-8")
            return
        if duong == "/api/hom-nay":
            tham = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            chi_thang = tham.get("chi_thang", [""])[0]
            chi_ngay = tham.get("chi_ngay", [""])[0]
            ma_tk, ma_phien, _banh = self.nguoi_dang_nhap()
            ma_chu = tham.get("ma", [""])[0]
            nam = None
            ten_nguoi = ""
            if ma_chu.isdigit():
                cap = nam_cua(int(ma_chu), ma_tk, ma_phien)
                if cap:
                    nam, ten_nguoi = cap
            if nam is None:
                gan = la_so_gan(ma_tk, ma_phien)
                if gan is not None:
                    cap = nam_cua(gan, ma_tk, ma_phien)
                    if cap:
                        nam, ten_nguoi = cap
            try:
                than = json.dumps(goi_hom_nay(chi_thang, chi_ngay, nam, ten_nguoi), ensure_ascii=False).encode("utf-8")
            except ValueError as loi:
                self.gui(400, json.dumps({"loi": str(loi)}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
                return
            self.gui(200, than, "application/json; charset=utf-8")
            return
        if duong == "/la-so":
            ma_tk, ma_phien, banh = self.nguoi_dang_nhap()
            than = json.dumps(danh_sach(ma_tk, ma_phien), ensure_ascii=False).encode("utf-8")
            self.gui(200, than, "application/json; charset=utf-8", cookie=banh)
            return
        if duong.startswith("/bai/"):
            so = duong[len("/bai/") :]
            if not so.isdigit():
                self.gui(404, "Không thấy bài.".encode("utf-8"), "text/plain; charset=utf-8")
                return
            ma_tk, ma_phien, _banh = self.nguoi_dang_nhap()
            bai = bai_moi(int(so), ma_tk, ma_phien)
            if bai is None:
                self.gui(404, "Không thấy bài.".encode("utf-8"), "text/plain; charset=utf-8")
                return
            than = json.dumps(
                {
                    "ma": bai["ma"],
                    "ten_nguoi": bai["ten_nguoi"],
                    "ten": f"TuVi_{bai['ten_nguoi']}.docx",
                    "html": html_bai(bai["noi_dung"]),
                },
                ensure_ascii=False,
            ).encode("utf-8")
            self.gui(200, than, "application/json; charset=utf-8")
            return
        if duong.startswith("/hoi-su/"):
            so = duong[len("/hoi-su/") :]
            if not so.isdigit():
                self.gui(404, "Không thấy.".encode("utf-8"), "text/plain; charset=utf-8")
                return
            ma_tk, ma_phien, _banh = self.nguoi_dang_nhap()
            ds = lich_su(int(so), ma_tk, ma_phien)
            if ds is None:
                self.gui(404, "Không thấy lá số.".encode("utf-8"), "text/plain; charset=utf-8")
                return
            self.gui(200, json.dumps(ds, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            return
        if duong.startswith("/tai-bai/"):
            so = duong[len("/tai-bai/") :]
            if not so.isdigit():
                self.gui(404, "Chưa có file Word.".encode("utf-8"), "text/plain; charset=utf-8")
                return
            ma_tk, ma_phien, _banh = self.nguoi_dang_nhap()
            noi_word = byte_word(int(so), ma_tk, ma_phien)
            if noi_word is None:
                self.gui(404, "Chưa có file Word.".encode("utf-8"), "text/plain; charset=utf-8")
                return
            self.gui(
                200,
                noi_word,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                f"TuVi_{so}.docx",
            )
            return
        if duong == "/api/lich":
            than = json.dumps(liet_ke_truc(), ensure_ascii=False).encode("utf-8")
            self.gui(200, than, "application/json; charset=utf-8")
            return
        if duong == "/toi":
            ten = ten_tu_token(self.token_phien())
            than = json.dumps({"ten": ten}, ensure_ascii=False).encode("utf-8")
            self.gui(200, than, "application/json; charset=utf-8")
            return
        if duong == "/bai-gan":
            bai = bai_gan_nhat()
            if bai is None:
                self.gui(404, "Chưa có bài.".encode("utf-8"), "text/plain; charset=utf-8")
                return
            than = json.dumps(bai, ensure_ascii=False).encode("utf-8")
            self.gui(200, than, "application/json; charset=utf-8")
            return
        if duong.startswith("/tai/"):
            tep = tim_word(duong[len("/tai/") :])
            if tep is None:
                self.gui(404, "Chưa có file Word.".encode("utf-8"), "text/plain; charset=utf-8")
                return
            self.gui(
                200,
                tep.read_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                duong[len("/tai/") :],
            )
            return
        self.gui(404, "Không thấy trang.".encode("utf-8"), "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        duong = self.path.split("?", 1)[0]
        if duong == "/hoi":
            self.tra_loi_cau_hoi()
            return
        if duong in ("/dang-nhap-google", "/dang-xuat"):
            self.xu_ly_tai_khoan(duong)
            return
        if duong != "/phan-tich":
            self.gui(404, "Không thấy trang.".encode("utf-8"), "text/plain; charset=utf-8")
            return
        do_dai = int(self.headers.get("Content-Length", "0"))
        if do_dai > 500_000:
            self.gui(400, "Bài dán quá dài.".encode("utf-8"), "text/plain; charset=utf-8")
            return
        than = self.rfile.read(do_dai).decode("utf-8", errors="replace")
        form = urllib.parse.parse_qs(than)
        bai = form.get("bai", [""])[0]
        ten_nguoi = form.get("ten_nguoi", [""])[0].strip()
        ma_tk, ma_phien, banh = self.nguoi_dang_nhap()
        if ma_tk is not None and not ten_nguoi:
            self.gui(400, "Hãy gõ tên người của lá số.".encode("utf-8"), "text/plain; charset=utf-8", cookie=banh)
            return
        if not KHOA.acquire(blocking=False):
            self.gui(
                409,
                "Đang viết một lá số khác. Hãy đợi lần đó xong rồi dán tiếp.".encode("utf-8"),
                "text/plain; charset=utf-8",
            )
            return
        ma_la = None
        try:
            chart, tep_json, word, ten, noi_dung = phan_tich_bai(bai)
            ma_la = bat_dau(chart, tep_json.read_text(encoding="utf-8"), ten_nguoi, ma_tk, ma_phien)
            hoan_tat(ma_la, noi_dung, word)
            than = json.dumps(
                {"ten": ten, "html": html_bai(noi_dung), "ma": ma_la, "ten_nguoi": ten_nguoi or "Người xem"},
                ensure_ascii=False,
            ).encode("utf-8")
            self.gui(200, than, "application/json; charset=utf-8", cookie=banh)
        except (ValueError, RuntimeError) as loi:
            if ma_la is not None:
                danh_loi(ma_la)
            self.gui(400, str(loi).encode("utf-8"), "text/plain; charset=utf-8", cookie=banh)
        except Exception:
            if ma_la is not None:
                danh_loi(ma_la)
            self.gui(500, traceback.format_exc()[-1500:].encode("utf-8"), "text/plain; charset=utf-8", cookie=banh)
        finally:
            dat_con(None)
            KHOA.release()

    def xu_ly_tai_khoan(self, duong: str) -> None:
        if duong == "/dang-xuat":
            dang_xuat(self.token_phien())
            self.gui(200, b"{}", "application/json; charset=utf-8", cookie=banh_xoa(self.an_toan()))
            return
        try:
            goi = self.doc_json(12_000)
            email, token = dang_nhap_google(str(goi.get("token", "")))
        except LoiTaiKhoan as loi:
            than = json.dumps({"loi": str(loi)}, ensure_ascii=False).encode("utf-8")
            self.gui(400, than, "application/json; charset=utf-8")
            return
        than = json.dumps({"ten": email}, ensure_ascii=False).encode("utf-8")
        self.gui(200, than, "application/json; charset=utf-8", cookie=banh_phien(token, self.an_toan()))

    def tra_loi_cau_hoi(self) -> None:
        do_dai = int(self.headers.get("Content-Length", "0"))
        if do_dai > 20_000:
            self.gui(400, "Câu hỏi quá dài.".encode("utf-8"), "text/plain; charset=utf-8")
            return
        try:
            goi = json.loads(self.rfile.read(do_dai).decode("utf-8"))
        except json.JSONDecodeError:
            self.gui(400, "Câu hỏi không đọc được.".encode("utf-8"), "text/plain; charset=utf-8")
            return
        cau = str(goi.get("cau", "")).strip()
        if not cau or len(cau) > 800:
            self.gui(400, "Hãy viết một câu hỏi ngắn.".encode("utf-8"), "text/plain; charset=utf-8")
            return
        ma_tk, ma_phien, _banh = self.nguoi_dang_nhap()
        ma_chu = str(goi.get("ma", "")).strip()
        if ma_chu.isdigit():
            ma_la = int(ma_chu)
        else:
            ma_la = la_so_gan(ma_tk, ma_phien)
        if ma_la is None or noi_bai(ma_la, ma_tk, ma_phien) is None:
            self.gui(400, "Hãy chọn một lá số đã phân tích.".encode("utf-8"), "text/plain; charset=utf-8")
            return
        if not KHOA.acquire(blocking=False):
            self.gui(
                409,
                "Đang bận viết lá số hoặc trả lời câu khác. Hãy đợi một lát.".encode("utf-8"),
                "text/plain; charset=utf-8",
            )
            return
        try:
            van = noi_bai(ma_la, ma_tk, ma_phien) or ""
            cap = nam_cua(ma_la, ma_tk, ma_phien)
            nam = None if cap is None else cap[0]
            ten_nguoi = "" if cap is None else cap[1]
            cu = lich_su(ma_la, ma_tk, ma_phien) or []
            cac_cau = []
            hoi_truoc = ""
            for m in cu:
                if m["nguoi_gui"] == "nguoi":
                    hoi_truoc = m["noi_dung"]
                elif hoi_truoc:
                    cac_cau.append({"hoi": hoi_truoc, "dap": m["noi_dung"]})
                    hoi_truoc = ""
            ghi_cau(ma_la, ma_bai(ma_la), "nguoi", cau)
            dap = hoi_la_so(cau, str(goi.get("chi_thang", "")), str(goi.get("chi_ngay", "")), cac_cau, van, nam, ten_nguoi)
            ghi_cau(ma_la, ma_bai(ma_la), "may", dap)
            than = json.dumps({"tra_loi": dap}, ensure_ascii=False).encode("utf-8")
            self.gui(200, than, "application/json; charset=utf-8")
        except ValueError as loi:
            self.gui(400, str(loi).encode("utf-8"), "text/plain; charset=utf-8")
        except SystemExit as loi:
            self.gui(503, str(loi).encode("utf-8"), "text/plain; charset=utf-8")
        except Exception:
            self.gui(500, "Chưa trả lời được. Hãy thử lại.".encode("utf-8"), "text/plain; charset=utf-8")
        finally:
            KHOA.release()


def main() -> None:
    load_dotenv(ROOT / ".env")
    tao_db()
    don_khach_cu()
    threading.Thread(target=giam_moi_giay, daemon=True).start()
    cong = int(os.environ.get("PORT", str(CONG)))
    host = os.environ.get("HOST", "0.0.0.0" if "PORT" in os.environ else "127.0.0.1")
    may = ThreadingHTTPServer((host, cong), TraLoi)
    print(f"Mở trình duyệt tại http://127.0.0.1:{cong}", flush=True)
    print("Muốn tắt thì bấm Ctrl+C ở cửa sổ này.", flush=True)
    may.serve_forever()


if __name__ == "__main__":
    main()
