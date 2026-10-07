"""
Trang dán lá số, nhận file Word.

Mở trang:
    .\\venv\\Scripts\\python.exe web.py

Rồi vào trình duyệt: http://127.0.0.1:8765
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dotenv import load_dotenv

from models import load_chart, thu_muc_bao_cao
from nhap_laso import chuyen

ROOT = Path(__file__).resolve().parent
CONG = 8765
KHOA = threading.Lock()
TAM = ROOT / "laso" / "vua_dan.txt"

TRANG = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phân tích lá số</title>
<style>
  :root { color-scheme: light; }
  body {
    margin: 0;
    background: #f4efe6;
    color: #1c1915;
    font: 18px/1.5 "Segoe UI", sans-serif;
  }
  main {
    max-width: 46rem;
    margin: 0 auto;
    padding: 2.5rem 1.25rem 4rem;
  }
  h1 { font-size: 1.8rem; font-weight: 650; margin: 0 0 0.4rem; }
  p { margin: 0.4rem 0 1rem; }
  textarea {
    width: 100%;
    min-height: 22rem;
    box-sizing: border-box;
    padding: 0.8rem;
    border: 1px solid #c8bfb0;
    border-radius: 8px;
    background: #fffdf8;
    font: 15px/1.45 Consolas, monospace;
    resize: vertical;
  }
  button {
    margin-top: 0.8rem;
    background: #1f4d3a;
    color: #fff;
    border: 0;
    border-radius: 8px;
    padding: 0.7rem 1.2rem;
    font: 600 1rem/1 "Segoe UI", sans-serif;
    cursor: pointer;
  }
  button:disabled { background: #8a847a; cursor: wait; }
  #tinh_trang { min-height: 1.5rem; margin-top: 0.8rem; }
  .loi { color: #8a1f1f; white-space: pre-wrap; }
</style>
</head>
<body>
<main>
  <h1>Phân tích lá số</h1>
  <p>Dán nguyên bài lá số (phần thông tin, tứ trụ và bảng 12 cung), rồi bấm nút. Máy viết 4 chương và tải về file Word. Có thể mất vài phút. Đừng đóng trang.</p>
  <form id="form">
    <textarea name="bai" placeholder="Dán bài lá số vào đây" required></textarea>
    <button type="submit" id="nut">Tạo file Word</button>
  </form>
  <div id="tinh_trang"></div>
</main>
<script>
const form = document.getElementById("form");
const nut = document.getElementById("nut");
const hop = document.getElementById("tinh_trang");
form.addEventListener("submit", async (su_kien) => {
  su_kien.preventDefault();
  nut.disabled = true;
  hop.className = "";
  hop.textContent = "Đang viết 4 chương. Cứ để trang này mở.";
  try {
    const tra_loi = await fetch("/phan-tich", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
      body: new URLSearchParams({ bai: form.bai.value }),
    });
    if (!tra_loi.ok) {
      hop.className = "loi";
      hop.textContent = await tra_loi.text();
      return;
    }
    const tep = await tra_loi.blob();
    const ten = (tra_loi.headers.get("Content-Disposition") || "").match(/filename=\"([^\"]+)\"/);
    const link = document.createElement("a");
    link.href = URL.createObjectURL(tep);
    link.download = ten ? ten[1] : "TuVi_Report.docx";
    link.click();
    hop.textContent = "Xong. File Word đã tải xuống.";
  } catch (loi) {
    hop.className = "loi";
    hop.textContent = "Không nối được với chương trình. Hãy xem cửa sổ đang chạy web.py.";
  } finally {
    nut.disabled = false;
  }
});
</script>
</body>
</html>
"""


def phan_tich_bai(bai: str) -> tuple[Path, str]:
    """Đổi bài dán thành lá số, viết báo cáo, trả đường dẫn file Word và tên tải về."""
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
    ket = subprocess.run(
        lenh,
        cwd=ROOT,
        env=moi_truong,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1200,
    )
    word = thu_muc / "TuVi_Report.docx"
    if ket.returncode != 0 or not word.is_file():
        duoi = (ket.stdout or "") + "\n" + (ket.stderr or "")
        raise RuntimeError("Chưa viết xong báo cáo.\n" + duoi[-1200:].strip())
    ten = f"TuVi_{thu_muc.name}.docx"
    return word, ten


class TraLoi(BaseHTTPRequestHandler):
    def log_message(self, dinh_dang: str, *tham_so) -> None:
        print(dinh_dang % tham_so, flush=True)

    def gui(self, ma: int, than: bytes, kieu: str, ten_tep: str = "") -> None:
        self.send_response(ma)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(than)))
        if ten_tep:
            self.send_header("Content-Disposition", f'attachment; filename="{ten_tep}"')
        self.end_headers()
        self.wfile.write(than)

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] != "/":
            self.gui(404, "Không thấy trang.".encode("utf-8"), "text/plain; charset=utf-8")
            return
        self.gui(200, TRANG.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/phan-tich":
            self.gui(404, "Không thấy trang.".encode("utf-8"), "text/plain; charset=utf-8")
            return
        do_dai = int(self.headers.get("Content-Length", "0"))
        if do_dai > 500_000:
            self.gui(400, "Bài dán quá dài.".encode("utf-8"), "text/plain; charset=utf-8")
            return
        than = self.rfile.read(do_dai).decode("utf-8", errors="replace")
        bai = urllib.parse.parse_qs(than).get("bai", [""])[0]
        if not KHOA.acquire(blocking=False):
            self.gui(
                409,
                "Đang viết một lá số khác. Hãy đợi lần đó xong rồi dán tiếp.".encode("utf-8"),
                "text/plain; charset=utf-8",
            )
            return
        try:
            word, ten = phan_tich_bai(bai)
            self.gui(
                200,
                word.read_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ten,
            )
        except (ValueError, RuntimeError) as loi:
            self.gui(400, str(loi).encode("utf-8"), "text/plain; charset=utf-8")
        except Exception:
            self.gui(500, traceback.format_exc()[-1500:].encode("utf-8"), "text/plain; charset=utf-8")
        finally:
            KHOA.release()


def main() -> None:
    load_dotenv(ROOT / ".env")
    may = ThreadingHTTPServer(("127.0.0.1", CONG), TraLoi)
    print(f"Mở trình duyệt tại http://127.0.0.1:{CONG}", flush=True)
    print("Muốn tắt thì bấm Ctrl+C ở cửa sổ này.", flush=True)
    may.serve_forever()


if __name__ == "__main__":
    main()
