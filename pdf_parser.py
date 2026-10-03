"""
Bóc tách PDF "Tử Vi Đẩu Số Tân Biên".

Để file PDF trong thư mục tai_lieu.

Chạy cả cuốn:
    .\\venv\\Scripts\\python.exe pdf_parser.py

Chạy thử 10 trang:
    .\\venv\\Scripts\\python.exe pdf_parser.py --pages 10
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent

TABLE_SETTINGS = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 3,
    "join_tolerance": 3,
    "intersection_tolerance": 5,
}

HEADER_RE = re.compile(
    r"^Vân Đằng Thái Thứ Lang\s+T\s*ử Vi đẩu số tân biên\s*$",
    re.IGNORECASE,
)
PAGE_NO_RE = re.compile(r"^-\s*\d+\s*-\s*$")
VOWEL = (
    "àáảãạăằắặẳẵâầấậẩẫèéẻẽẹêềếệểễìíỉĩị"
    "òóỏõọôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵ"
    "ÀÁẢÃẠĂẰẮẶẲẴÂẦẤẬẨẪÈÉẺẼẸÊỀẾỆỂỄÌÍỈĨỊ"
    "ÒÓỎÕỌÔỒỐỘỔỖƠỜỚỢỞỠÙÚỦŨỤƯỪỨỰỬỮỲÝỶỸỴ"
    "aeiouyAEOUY"
)


def repair_spacing(text: str) -> str:
    """Sửa khoảng trắng do PDF canh đều hai bên bị chèn vào giữa một chữ."""
    onset = (
        r"(?:[Gg]i|[Nn]h|[Tt]h|[Pp]h|[Cc]h|[Gg]h|[Kk]h|[Nn]g|[Tt]r|[Qq]u|"
        r"[BbCcDdĐđGgHhKkLlMmNnPpQqRrSsTtVvXx])"
    )
    # "Thi ếu", "Tu ế", "Quy ền": phụ âm đầu + một nguyên âm, rồi dấu cách, rồi nguyên âm có dấu.
    text = re.sub(
        rf"(?<![A-Za-zÀ-ỹ])({onset}[iueoaIUEOAyY])\s+(?=[{VOWEL}])",
        r"\1",
        text,
    )
    # "H ỷ", "T ử", "B ạch": phụ âm đầu bị tách khỏi nguyên âm.
    text = re.sub(
        rf"(?<![A-Za-zÀ-ỹ])({onset})\s+(?=[{VOWEL}])",
        r"\1",
        text,
    )
    text = re.sub(rf"([Đđ])\s+(?=[ưứừựửữêềếệểễ])", r"\1", text)
    text = re.sub(r"([ẤấẦầ])\s+t\b", r"\1t", text)
    text = re.sub(r"([,;:])(?=\S)", r"\1 ", text)
    # Chỉ chữ thường. Không dùng khoảng à-ỹ vì chữ HOA tiếng Việt nằm lẫn trong khoảng đó.
    lower = "a-zàáảãạăằắặẳẵâầấậẩẫèéẻẽẹêềếệểễìíỉĩịòóỏõọôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵ"
    text = re.sub(rf"([{lower}])(?=[A-ZĐ])", r"\1 ", text)
    # Chữ "đ" luôn đứng đầu âm tiết, nên dính vào chữ trước là thiếu dấu cách.
    text = re.sub(rf"([{lower}])(?=đ)", r"\1 ", text)
    return text


def overlapped_space_ids(chars: list[dict]) -> set[int]:
    """Bỏ dấu cách nằm đè lên chữ thật (PDF chèn space vào giữa 'Ất')."""
    nonempty = [char for char in chars if char.get("text", " ").strip()]
    bad: set[int] = set()
    for space in chars:
        if space.get("text") != " ":
            continue
        width = space.get("width") or 0.1
        for char in nonempty:
            if abs(char["top"] - space["top"]) > 2:
                continue
            overlap = min(space["x1"], char["x1"]) - max(space["x0"], char["x0"])
            if overlap / width >= 0.9:
                bad.add(id(space))
                break
    return bad


def find_pdf(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            raise SystemExit(f"Không thấy file PDF: {path}")
        return path
    folders = [ROOT, ROOT / "tai_lieu"]
    pdfs = sorted(path for folder in folders if folder.is_dir() for path in folder.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(
            "Không thấy file PDF. Hãy để sách trong thư mục tai_lieu rồi chạy lại."
        )
    if len(pdfs) > 1:
        names = ", ".join(p.name for p in pdfs)
        raise SystemExit(f"Có nhiều file PDF ({names}). Hãy chỉ định bằng --pdf.")
    return pdfs[0]


def clean_cell(value) -> str:
    if value is None:
        return ""
    lines = []
    for raw_line in str(value).replace("\r", "").split("\n"):
        line = repair_spacing(re.sub(r"[ \t]+", " ", raw_line).strip())
        if line == "Dậ":
            line = "Dậu"
        if line.startswith("Dân,"):
            line = "Dần," + line[4:]
        if line:
            lines.append(line)
    return "\n".join(lines)


def merge_complementary_columns(rows: list[list[str]]) -> list[list[str]]:
    """Gộp cột trống do ô bị kẻ gộp: tiêu đề và nội dung nằm hai cột kề nhau."""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    columns = [[row[index] for row in rows] for index in range(width)]
    columns = [column for column in columns if any(column)]

    changed = True
    while changed and len(columns) > 1:
        changed = False
        merged: list[list[str]] = []
        index = 0
        while index < len(columns):
            if index + 1 < len(columns):
                left, right = columns[index], columns[index + 1]
                conflict = any(a and b for a, b in zip(left, right))
                if not conflict:
                    merged.append([a or b for a, b in zip(left, right)])
                    index += 2
                    changed = True
                    continue
            merged.append(columns[index])
            index += 1
        columns = merged

    height = len(rows)
    combined = [
        [columns[col][row] for col in range(len(columns))]
        for row in range(height)
    ]
    return [row for row in combined if any(row)]


def clean_table(raw_rows: list[list]) -> list[list[str]]:
    rows = [[clean_cell(cell) for cell in row] for row in raw_rows]
    if not rows:
        return []
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    keep_cols = [index for index in range(width) if any(row[index] for row in rows)]
    trimmed = [[row[index] for index in keep_cols] for row in rows]
    trimmed = [row for row in trimmed if any(cell for cell in row)]
    if not trimmed:
        return []
    # Lá số 4x4 phải giữ nguyên ô giữa. Gộp cột chỉ dùng cho bảng số liệu.
    if not is_laso(trimmed):
        trimmed = merge_complementary_columns(trimmed)
    content_cells = sum(1 for row in trimmed for cell in row if cell)
    if content_cells < 2:
        return []
    return trimmed


def char_inside_boxes(obj: dict, boxes: list[tuple]) -> bool:
    if obj.get("object_type") != "char":
        return False
    x = (obj["x0"] + obj["x1"]) / 2
    y = (obj["top"] + obj["bottom"]) / 2
    for x0, top, x1, bottom in boxes:
        if x0 - 2 <= x <= x1 + 2 and top - 2 <= y <= bottom + 2:
            return True
    return False


def page_prose(page, boxes: list[tuple]) -> str:
    kept = page.filter(lambda obj: not char_inside_boxes(obj, boxes))
    bad_spaces = overlapped_space_ids(kept.chars)
    filtered = kept.filter(lambda obj: id(obj) not in bad_spaces)
    text = filtered.extract_text(x_tolerance=7, y_tolerance=3) or ""
    lines = []
    for raw in text.splitlines():
        line = repair_spacing(re.sub(r"\s+", " ", raw).strip())
        if not line or HEADER_RE.match(line) or PAGE_NO_RE.match(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def pad_grid(rows: list[list[str]]) -> list[list[str]]:
    width = max(len(row) for row in rows)
    return [row + [""] * (width - len(row)) for row in rows]


def is_laso(rows: list[list[str]]) -> bool:
    """Lá số là lưới 4x4: 12 cung vòng ngoài, ô 2x2 ở giữa là Thiên bàn."""
    grid = pad_grid(rows)
    if len(grid) != 4 or any(len(row) != 4 for row in grid):
        return False
    center = [grid[1][1], grid[1][2], grid[2][1], grid[2][2]]
    if sum(1 for cell in center if cell.strip()) > 1:
        return False
    outer = [
        grid[0][0], grid[0][1], grid[0][2], grid[0][3],
        grid[1][0], grid[1][3],
        grid[2][0], grid[2][3],
        grid[3][0], grid[3][1], grid[3][2], grid[3][3],
    ]
    return sum(1 for cell in outer if cell.strip()) >= 8


def flatten_cell(cell: str) -> str:
    return cell.replace("\n", " ").strip()


def render_laso(rows: list[list[str]]) -> str:
    grid = pad_grid(rows)
    center_lines = []
    for cell in (grid[1][1], grid[1][2], grid[2][1], grid[2][2]):
        center_lines.extend(line.strip() for line in cell.split("\n") if line.strip())
    if not center_lines:
        center_lines = ["", ""]

    outer = {
        (row, col): flatten_cell(grid[row][col])
        for row in range(4)
        for col in range(4)
        if not (row in (1, 2) and col in (1, 2))
    }
    side = max(8, *(len(text) for text in outer.values()))
    center_w = side * 2 + 3
    longest_center = max(len(line) for line in center_lines)
    if longest_center > center_w:
        side += (longest_center - center_w + 1) // 2
        center_w = side * 2 + 3

    def fit(text: str, width: int) -> str:
        return text[:width].ljust(width)

    def border_top() -> str:
        return "+" + "+".join("-" * (side + 2) for _ in range(4)) + "+"

    def border_mid() -> str:
        return (
            "+"
            + "-" * (side + 2)
            + "+"
            + "-" * (center_w + 2)
            + "+"
            + "-" * (side + 2)
            + "+"
        )

    def row_outer(a: str, b: str, c: str, d: str) -> str:
        cells = " | ".join(fit(text, side) for text in (a, b, c, d))
        return f"| {cells} |"

    lines = [
        border_top(),
        row_outer(outer[(0, 0)], outer[(0, 1)], outer[(0, 2)], outer[(0, 3)]),
        border_mid(),
    ]
    body_h = max(2, len(center_lines))
    for index in range(body_h):
        if index == 0:
            left, right = outer[(1, 0)], outer[(1, 3)]
        elif index == body_h - 1:
            left, right = outer[(2, 0)], outer[(2, 3)]
        else:
            left, right = "", ""
        center = center_lines[index] if index < len(center_lines) else ""
        lines.append(f"| {fit(left, side)} | {fit(center, center_w)} | {fit(right, side)} |")
    lines.extend(
        [
            border_mid(),
            row_outer(outer[(3, 0)], outer[(3, 1)], outer[(3, 2)], outer[(3, 3)]),
            border_top(),
        ]
    )
    return "```\n" + "\n".join(lines) + "\n```"


def laso_payload(rows: list[list[str]]) -> dict:
    grid = pad_grid(rows)
    center_lines = []
    for cell in (grid[1][1], grid[1][2], grid[2][1], grid[2][2]):
        center_lines.extend(line.strip() for line in cell.split("\n") if line.strip())
    # Chiều thuận kim đồng hồ, bắt đầu từ ô thường là cung Tý.
    thu_tu = [(3, 2), (3, 1), (3, 0), (2, 0), (1, 0), (0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 3)]
    cung = []
    for index, (row, col) in enumerate(thu_tu, start=1):
        label = flatten_cell(grid[row][col])
        cung.append({"thu_tu_vong": index, "hang": row + 1, "cot": col + 1, "noi_dung": label})
    return {
        "loai": "la_so",
        "mo_ta": "12 cung vòng ngoài, ô giữa là Thiên bàn",
        "thien_ban": center_lines,
        "cung": cung,
    }


# Tên cung in trong sách -> tên cột cho thống nhất.
PALACE_NAMES = (
    ("MỆNH VIÊN", "MỆNH"),
    ("PHỤ MẪU", "PHỤ MẪU"),
    ("PHÚC ĐỨC", "PHÚC ĐỨC"),
    ("ĐIỀN TRẠCH", "ĐIỀN TRẠCH"),
    ("QUAN LỘC", "QUAN LỘC"),
    ("NÔ BỘC", "NÔ BỘC"),
    ("THIÊN DI", "THIÊN DI"),
    ("TẬT ÁCH", "TẬT ÁCH"),
    ("TÀI BẠCH", "TÀI BẠCH"),
    ("TỬ TỨC", "TỬ TỨC"),
    ("PHU THÊ", "PHU THÊ"),
    ("HUYNH ĐỆ", "HUYNH ĐỆ"),
    ("MỆNH", "MỆNH"),
)
CHINH_TINH = (
    "Thiên Tướng",
    "Thiên Lương",
    "Thiên Đồng",
    "Thiên Phủ",
    "Thiên Cơ",
    "Thái Dương",
    "Thái Âm",
    "Tham Lang",
    "Liêm Trinh",
    "Phá Quân",
    "Thất Sát",
    "Vũ Khúc",
    "Cự Môn",
    "Tử Vi",
)
PHU_TINH = (
    "Thiên Không", "Thiên Khốc", "Thiên Khôi", "Thiên Hình", "Thiên Hư",
    "Thiên Hỷ", "Thiên Việt", "Thiên Qúy", "Thiên Quý", "Thiên Giải",
    "Thiên Tài", "Thiên Thọ", "Thiên Trù", "Thiên Đức", "Thiên Mã",
    "Thiên Quan", "Thiên Phúc", "Thiên Riêu", "Thiên Y", "Thiên Thương",
    "Thiên Sứ", "Thiên La", "Địa Võng", "Địa Giải", "Địa Không", "Địa Kiếp",
    "Hóa Quyền", "Hóa Khoa", "Hóa Lộc", "Hóa Kỵ", "Hóa Kị",
    "Văn Xương", "Văn Khúc", "Tả Phụ", "Tả Phù", "Hữu Bật", "Long Trì", "Phượng Các",
    "Tam Thai", "Bát Tọa", "Ân Quang", "Quốc Ấn", "Đường Phù", "Phong Cáo",
    "Hồng Loan", "Đào Hoa", "Nguyệt Đức", "Dương Đức", "Âm Đức",
    "Thai Phụ", "Đẩu Quân", "Hoa Cái", "Kiếp Sát", "Phá Toái", "Lưu Hà",
    "Lưu Niên", "Cô Thần", "Quả Tú", "Văn Tinh", "Thiên Diêu",
    "Kình Dương", "Đà La", "Hỏa Tinh", "Linh Tinh",
    "Thái Tuế", "Thiếu Dương", "Tang Môn", "Thiếu Âm", "Quan Phù", "Quan Phủ", "Tử Phù",
    "Tuế Phá", "Long Đức", "Bạch Hổ", "Phúc Đức", "Điếu Khách", "Trực Phù",
    "Lộc Tồn", "Lực Sỹ", "Lực Sĩ", "Thanh Long", "Tiểu Hao", "Tướng Quân",
    "Tấu Thư", "Phi Liêm", "Hỷ Thần", "Hỉ Thần", "Bệnh Phù", "Đại Hao",
    "Phục Binh", "Bác Sỹ", "Bác Sĩ",
    "Tràng Sinh", "Mộc Dục", "Quan Đới", "Lâm Quan", "Đế Vượng",
    "Suy", "Bệnh", "Tử", "Mộ", "Tuyệt", "Thai", "Dưỡng",
    "Giải Thần",
)
STAR_ALIAS = {
    "Tả Phù": "Tả Phụ",
    "Hóa Kị": "Hóa Kỵ",
    "Quốc Ân": "Quốc Ấn",
    "Phong Cao": "Phong Cáo",
}


def _normalize_star_text(text: str) -> str:
    text = re.sub(r"Quy\s*ền", "Quyền", text)
    text = text.replace("Quốc Ân", "Quốc Ấn").replace("Phong Cao", "Phong Cáo")
    return text


PHU_TINH_SORTED = tuple(sorted(set(PHU_TINH), key=len, reverse=True))
# Chiều thuận, bắt đầu từ Tý. (hàng, cột) theo lưới 4x4, hàng 1 là mép trên.
VONG_THUAN = (
    (4, 3, "Tý"), (4, 2, "Sửu"), (4, 1, "Dần"), (3, 1, "Mão"),
    (2, 1, "Thìn"), (1, 1, "Tỵ"), (1, 2, "Ngọ"), (1, 3, "Mùi"),
    (1, 4, "Thân"), (2, 4, "Dậu"), (3, 4, "Tuất"), (4, 4, "Hợi"),
)
SHORT_CUNG = {
    "MỆNH": "Mệnh",
    "PHỤ MẪU": "Phụ",
    "PHÚC ĐỨC": "Phúc",
    "ĐIỀN TRẠCH": "Điền",
    "QUAN LỘC": "Quan",
    "NÔ BỘC": "Nô",
    "THIÊN DI": "Di",
    "TẬT ÁCH": "Tật",
    "TÀI BẠCH": "Tài",
    "TỬ TỨC": "Tử",
    "PHU THÊ": "Phối",
    "HUYNH ĐỆ": "Bào",
}


def _is_letter(char: str) -> bool:
    return bool(re.match(r"[A-Za-zÀ-ỹ]", char))


def _consume_known_stars(text: str) -> tuple[list[str], list[str]]:
    stars: list[str] = []
    leftover: list[str] = []
    index = 0
    unknown: list[str] = []
    while index < len(text):
        if text[index] in " -":
            if unknown:
                leftover.append("".join(unknown).strip(" -"))
                unknown = []
            index += 1
            continue
        found = ""
        for name in PHU_TINH_SORTED:
            after = index + len(name)
            if text.startswith(name, index) and (after >= len(text) or not _is_letter(text[after])):
                found = name
                break
        if found:
            if unknown:
                leftover.append("".join(unknown).strip(" -"))
                unknown = []
            stars.append(STAR_ALIAS.get(found, found))
            index += len(found)
        else:
            unknown.append(text[index])
            index += 1
    if unknown:
        leftover.append("".join(unknown).strip(" -"))
    leftover = [piece for piece in leftover if len(piece) >= 2]
    return stars, leftover


def parse_cung_cell(text: str, vi_tri: str) -> dict | None:
    raw = flatten_cell(text)
    if not raw:
        return None
    palace = ""
    for source, display in PALACE_NAMES:
        if source in raw:
            palace = display
            raw = raw.replace(source, " ", 1)
            break
    if not palace:
        return None
    raw = _normalize_star_text(raw)
    dai_han = ""
    number = re.search(r"(\d{1,3})\s*$", raw)
    if number:
        start = int(number.group(1))
        dai_han = f"{start} - {start + 9}"
        raw = raw[: number.start()]
    tuan = bool(re.search(r"\bTuần\b", raw))
    triet = bool(re.search(r"\bTriệt\b", raw))
    than = bool(re.search(r"\bTHÂN\b", raw))
    raw = re.sub(r"\b(Tuần|Triệt|THÂN)\b", " ", raw)
    chinh: list[tuple[int, str]] = []
    pattern = "|".join(CHINH_TINH)
    for match in re.finditer(rf"({pattern})\s*\(([MĐVHBDmdvhbd])\)", raw):
        brightness = match.group(2).upper()
        if brightness == "D":
            brightness = "Đ"
        chinh.append((match.start(), f"{match.group(1)} ({brightness})"))
    raw = re.sub(rf"({pattern})\s*\(([MĐVHBDmdvhbd])\)", " ", raw)
    chinh_names = [label for _pos, label in sorted(chinh)]
    raw = re.sub(r"\s+", " ", raw).strip(" -")
    phu, leftover = _consume_known_stars(raw)
    for name in CHINH_TINH:
        if name in leftover:
            chinh_names.append(name)
            leftover = [piece for piece in leftover if piece != name]
    hoa = [star for star in phu if star.startswith("Hóa ")]
    phu = [star for star in phu if not star.startswith("Hóa ")]
    phu.extend(leftover)
    marks = [label for label, present in (("Tuần", tuan), ("Triệt", triet)) if present]
    return {
        "ten": palace,
        "vi_tri": vi_tri,
        "dai_han": dai_han,
        "chinh_tinh": chinh_names,
        "phu_tinh": phu,
        "hoa": hoa,
        "tuan_triet": ", ".join(marks),
        "than_cu": than,
    }


def _center_info(center_lines: list[str]) -> dict:
    text = " ".join(center_lines)
    info = {"gioi_tinh": "", "am_duong": "", "am_lich": "", "ban_menh": "", "cuc": ""}
    gender = re.search(r"(Âm|Dương)\s*(Nam|Nữ)", text)
    if gender:
        info["am_duong"] = f"{gender.group(1)} {gender.group(2)}"
        info["gioi_tinh"] = gender.group(2)
    birth = re.search(
        r"Năm\s+(.+?),\s*tháng\s+(\d+),\s*ngày\s+(\d+),\s*giờ\s+([A-Za-zÀ-ỹ]+)",
        text,
    )
    if birth:
        info["am_lich"] = (
            f"Năm {birth.group(1).strip()}, ngày {birth.group(3)} "
            f"tháng {birth.group(2)}, giờ {birth.group(4)}"
        )
    menh = re.search(
        r"Mệnh\s+(.+?)\s+(?=(?:Kim Tứ|Mộc Tam|Thủy Nhị|Thổ Ngũ|Hỏa Lục)\s+Cục)",
        text,
    )
    if menh:
        info["ban_menh"] = menh.group(1).strip(" ,.")
    cuc = re.search(r"((?:Kim|Mộc|Thủy|Thổ|Hỏa)\s+(?:Tứ|Tam|Nhị|Ngũ|Lục)\s+Cục)", text, re.I)
    if cuc:
        info["cuc"] = cuc.group(1)
    return info


def is_detailed_laso(rows: list[list[str]]) -> bool:
    """Lá số có tên 12 cung và sao, khác với sơ đồ an sao chỉ ghi số hoặc địa chi."""
    hits = 0
    for row_index, col_index, _chi in VONG_THUAN:
        cell = pad_grid(rows)[row_index - 1][col_index - 1]
        if any(name in flatten_cell(cell) for name, _display in PALACE_NAMES):
            hits += 1
    return hits >= 6


def parse_detailed_laso(rows: list[list[str]]) -> dict:
    grid = pad_grid(rows)
    by_pos = {}
    for row_index, col_index, chi in VONG_THUAN:
        parsed = parse_cung_cell(grid[row_index - 1][col_index - 1], chi)
        if parsed:
            by_pos[(row_index, col_index)] = parsed
    ordered_pos = [(row, col) for row, col, _chi in VONG_THUAN]
    start = 0
    for index, pos in enumerate(ordered_pos):
        if pos in by_pos and by_pos[pos]["ten"] == "MỆNH":
            start = index
            break
    cung = [by_pos[pos] for pos in (ordered_pos[start:] + ordered_pos[:start]) if pos in by_pos]
    center = []
    for cell in (grid[1][1], grid[1][2], grid[2][1], grid[2][2]):
        center.extend(line.strip() for line in cell.split("\n") if line.strip())
    info = _center_info(center)
    than = next((item["ten"] for item in cung if item["than_cu"]), "")
    return {**info, "than_cu": than, "cung": cung}


def render_detailed_laso(rows: list[list[str]]) -> str:
    data = parse_detailed_laso(rows)
    lines = ["## THÔNG TIN LÁ SỐ CƠ BẢN", ""]
    if data["gioi_tinh"]:
        lines.append(f"* **Giới tính:** {data['gioi_tinh']}")
    if data["am_duong"]:
        lines.append(f"* **Âm dương:** {data['am_duong']}")
    if data["am_lich"]:
        lines.append(f"* **Âm lịch:** {data['am_lich']}")
    if data["ban_menh"]:
        lines.append(f"* **Bản mệnh:** {data['ban_menh']}")
    if data["cuc"]:
        lines.append(f"* **Cục:** {data['cuc']}")
    if data["than_cu"]:
        lines.append(f"* **Thân:** Thân cư {SHORT_CUNG.get(data['than_cu'], data['than_cu'])}")

    bits = []
    for item in data["cung"]:
        if item["ten"] not in ("MỆNH", "TÀI BẠCH", "QUAN LỘC"):
            continue
        stars = ", ".join(item["chinh_tinh"]) if item["chinh_tinh"] else "vô chính diệu"
        bits.append(
            f"Cung {SHORT_CUNG[item['ten']]} tại {item['vi_tri']} có {stars}"
        )
    if bits:
        lines.append(f"* **Tử vi cơ bản:** {'. '.join(bits)}.")
    lines.extend(["", "---", "", "## TỬ VI CHI TIẾT 12 CUNG", ""])
    lines.append(
        "| Tên Cung | Vị trí | Đại hạn | Chính tinh | Phụ tinh | Hóa | Tuần / Triệt |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")

    def cell(value: str) -> str:
        return value.replace("|", "\\|")

    for item in data["cung"]:
        chinh = ", ".join(item["chinh_tinh"]) if item["chinh_tinh"] else "Vô chính diệu"
        phu = ", ".join(item["phu_tinh"])
        hoa = ", ".join(item["hoa"])
        han = f"**{item['dai_han']}**" if item["dai_han"] else ""
        ten = f"**{item['ten']}**"
        if item["than_cu"]:
            ten += " (Thân)"
        lines.append(
            "| "
            + " | ".join(
                cell(part)
                for part in (ten, item["vi_tri"], han, chinh, phu, hoa, item["tuan_triet"])
            )
            + " |"
        )
    if any(not item["dai_han"] for item in data["cung"]):
        lines.extend(
            [
                "",
                "Cung để trống cột Đại hạn là bản in không ghi số tuổi, vì hạn đó đã hơn 70 tuổi.",
            ]
        )
    return "\n".join(lines)


def markdown_table(rows: list[list[str]]) -> str:
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]

    def esc(cell: str) -> str:
        return flatten_cell(cell).replace("|", "\\|")

    header = normalized[0]
    body = normalized[1:]
    lines = [
        "| " + " | ".join(esc(cell) for cell in header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(esc(cell) for cell in row) + " |")
    return "\n".join(lines)


def parse_pdf(pdf_path: Path, start_page: int, end_page: int) -> tuple[str, dict]:
    md_parts: list[str] = []
    tables_out: list[dict] = []

    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        if start_page < 1 or end_page > total or start_page > end_page:
            raise SystemExit(
                f"Khoảng trang không hợp lệ. Sách có {total} trang, "
                f"bạn chọn {start_page}-{end_page}."
            )

        md_parts.append(f"# Tử Vi Đẩu Số Tân Biên — trang {start_page} đến {end_page}")
        md_parts.append("")
        md_parts.append(f"- File gốc: `{pdf_path.name}`")
        md_parts.append(f"- Tổng số trang của sách: {total}")
        if end_page - start_page + 1 < total:
            md_parts.append(f"- Đây là bản trích {end_page - start_page + 1} trang, chưa phải cả cuốn.")
        md_parts.append("- Sơ đồ an sao vẫn vẽ theo 12 cung. Lá số chi tiết được lập thành bảng từng cung. Bảng số liệu (Can Chi, Bản Mệnh, Cục...) giữ dạng bảng.")
        md_parts.append("")

        for number in range(start_page, end_page + 1):
            if number == start_page or number % 20 == 0 or number == end_page:
                print(f"Đang đọc trang {number}/{end_page}...", flush=True)
            page = pdf.pages[number - 1]
            found = page.find_tables(TABLE_SETTINGS)
            boxes = [table.bbox for table in found]
            prose = page_prose(page, boxes)
            cleaned_tables = []
            for table in found:
                rows = clean_table(table.extract() or [])
                if rows:
                    cleaned_tables.append(rows)

            md_parts.append(f"## Trang {number}")
            md_parts.append("")
            md_parts.append(prose if prose else "_(Trang này không có đoạn chữ ngoài bảng.)_")
            md_parts.append("")

            for index, rows in enumerate(cleaned_tables, start=1):
                record = {
                    "trang": number,
                    "thu_tu": index,
                    "so_hang": len(rows),
                    "so_cot": max(len(row) for row in rows),
                    "du_lieu": rows,
                }
                if is_laso(rows):
                    record.update(laso_payload(rows))
                    if is_detailed_laso(rows):
                        md_parts.append(f"### Lá số — trang {number}")
                        md_parts.append("")
                        md_parts.append(render_detailed_laso(rows))
                        record["cach_trinh_bay"] = "bang_12_cung"
                        record["chi_tiet"] = parse_detailed_laso(rows)
                    else:
                        center_text = " ".join(record["thien_ban"])
                        if "Họ tên" in center_text or "Bản Mệnh" in center_text:
                            caption = (
                                "Lá số: 12 cung vòng ngoài. "
                                "Ô giữa là Thiên bàn, chỗ ghi họ tên, ngày giờ sinh và bản mệnh của đương số."
                            )
                        elif center_text.strip():
                            caption = "Sơ đồ 12 cung. Ô giữa là phần trung tâm, không phải một cột trong bảng."
                        else:
                            caption = "Sơ đồ 12 cung. Ô giữa để trống."
                        md_parts.append(f"### Lá số — trang {number}")
                        md_parts.append("")
                        md_parts.append(caption)
                        md_parts.append("")
                        md_parts.append(render_laso(rows))
                else:
                    md_parts.append(f"### Bảng {index} — trang {number}")
                    md_parts.append("")
                    md_parts.append(markdown_table(rows))
                md_parts.append("")
                tables_out.append(record)

    rules = {
        "mo_ta": f"Bảng biểu cứng trích từ trang {start_page} đến {end_page}",
        "file_pdf": pdf_path.name,
        "tu_trang": start_page,
        "den_trang": end_page,
        "tong_trang_sach": total,
        "so_bang": len(tables_out),
        "bang": tables_out,
    }
    return "\n".join(md_parts).rstrip() + "\n", rules


def main() -> None:
    parser = argparse.ArgumentParser(description="Bóc tách PDF Tử Vi thành chữ và bảng.")
    parser.add_argument("--pdf", help="Đường dẫn file PDF. Bỏ trống nếu chỉ có 1 file PDF trong thư mục dự án.")
    parser.add_argument("--start", type=int, default=1, help="Trang bắt đầu (mặc định: 1).")
    parser.add_argument(
        "--pages",
        type=int,
        default=0,
        help="Số trang cần lấy. 0 nghĩa là lấy đến hết sách.",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Thư mục chứa kết quả. Mặc định: kiem_tra_10_trang nếu giới hạn trang, còn không thì output.",
    )
    args = parser.parse_args()

    pdf_path = find_pdf(args.pdf)
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)

    start = args.start
    if args.pages and args.pages > 0:
        end = min(total, start + args.pages - 1)
    else:
        end = total

    out_name = args.out or ("kiem_tra_10_trang" if args.pages else "output")
    out_dir = Path(out_name)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    markdown, rules = parse_pdf(pdf_path, start, end)
    md_path = out_dir / "TuVi_TanBien_Data.md"
    json_path = out_dir / "rules.json"
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"PDF: {pdf_path.name}")
    print(f"Đã lấy trang {start} đến {end} (sách có {total} trang).")
    print(f"Số bảng tìm được: {rules['so_bang']}")
    print(f"File chữ: {md_path}")
    print(f"File bảng: {json_path}")


if __name__ == "__main__":
    main()
