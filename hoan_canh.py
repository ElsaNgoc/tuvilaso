"""Dịch đáp án khảo sát thành hoàn cảnh thật, để bài viết bám đúng việc đương số đang sống."""

from __future__ import annotations

NAM_XEM = 2026


def nhom(tuoi: int) -> str:
    if tuoi <= 15:
        return "tre"
    if tuoi <= 22:
        return "thanh_nien"
    if tuoi <= 60:
        return "truong_thanh"
    return "cao_nien"


def _dap(ma: str, chu: str) -> dict:
    return {"ma": ma, "chu": chu}


def _cau(ma: str, hoi: str, dap: list[dict], khi: dict | None = None) -> dict:
    dong = {"ma": ma, "hoi": hoi, "dap": dap}
    if khi:
        dong["khi"] = khi
    return dong


def bo_cau(tuoi: int) -> dict:
    """Đúng bộ câu của một nhóm tuổi. Câu có 'khi' chỉ hiện khi đáp án trước khớp."""
    if tuoi < 0 or tuoi > 120:
        raise ValueError("Tuổi không hợp lệ.")
    ten = nhom(tuoi)
    if ten == "tre":
        cau = [
            _cau(
                "q1",
                "Hoàn cảnh hiện tại của đương số đang nghiêng về hướng nào nhất?",
                [
                    _dap("A", "Ở nhà, được gia đình chăm sóc và bao bọc hoàn toàn."),
                    _dap("B", "Sống xa nhà (học nội trú, ở nhờ nhà họ hàng)."),
                    _dap("C", "Phải phụ giúp gia đình mưu sinh hoặc đi làm từ sớm."),
                ],
            ),
            _cau(
                "q2",
                "Tình hình học tập hiện tại?",
                [
                    _dap("A1", "Chưa đi học hoặc đang học mầm non."),
                    _dap("A2", "Đang học tiểu học hoặc trung học cơ sở."),
                ],
                {"q1": ["A", "B"]},
            ),
            _cau(
                "q3",
                "Mức độ tham gia công việc?",
                [
                    _dap("C1", "Vừa đi học vừa làm thêm phụ giúp gia đình."),
                    _dap("C2", "Đã nghỉ học hoàn toàn để đi làm kiếm tiền."),
                ],
                {"q1": ["C"]},
            ),
        ]
    elif ten == "thanh_nien":
        cau = [
            _cau(
                "q1",
                "Trạng thái học tập và làm việc hiện tại của bạn là gì?",
                [
                    _dap("A", "Đang đi học (phổ thông, đại học hoặc học nghề)."),
                    _dap("B", "Vừa học vừa đi làm thêm."),
                    _dap("C", "Vừa tốt nghiệp, đang loay hoay tìm việc hoặc chờ định hướng."),
                    _dap("D", "Đã thôi học hoàn toàn để đi làm toàn thời gian."),
                    _dap("E", "Gap-year, đang nghỉ ngơi hoặc mông lung chưa rõ định hướng."),
                ],
            ),
            _cau(
                "q2",
                "Môi trường sinh sống hiện tại?",
                [
                    _dap("A1", "Ở trong nước."),
                    _dap("A2", "Đang du học hoặc sống tại nước ngoài."),
                ],
                {"q1": ["A", "B"]},
            ),
        ]
    elif ten == "truong_thanh":
        cau = [
            _cau(
                "q1",
                "Trạng thái công việc hiện tại của bạn là gì?",
                [
                    _dap("A", "Làm công ăn lương, nhân viên hoặc cấp quản lý."),
                    _dap("B", "Làm chủ, tự kinh doanh hoặc đầu tư tự do."),
                    _dap("C", "Nội trợ, chăm sóc gia đình toàn thời gian."),
                    _dap("D", "Đang chuyển giao (thất nghiệp, tìm việc mới, học chuyển ngành)."),
                ],
            ),
            _cau(
                "q2",
                "Trạng thái gia đạo hiện tại ra sao?",
                [
                    _dap("A", "Độc thân (chưa có người yêu hoặc đang tìm hiểu)."),
                    _dap("B", "Đã lập gia đình hoặc sống chung, chưa có con."),
                    _dap("C", "Đã có gia đình và đang nuôi con."),
                    _dap("D", "Độc thân nuôi con (mẹ hoặc cha đơn thân)."),
                ],
            ),
            _cau(
                "q3",
                "Đâu là mối bận tâm lớn nhất của bạn trong năm nay?",
                [
                    _dap("A", "Đột phá sự nghiệp, gia tăng tài sản, khởi nghiệp hoặc trả nợ."),
                    _dap("B", "Tìm kiếm tình yêu, cứu vãn hôn nhân, gìn giữ gia đình, lo cho con cái."),
                    _dap("C", "Sức khỏe thể chất, chữa lành tâm lý, tìm sự bình yên."),
                    _dap("D", "Giải quyết các rắc rối pháp lý, kiện tụng, thị phi."),
                ],
            ),
        ]
    else:
        cau = [
            _cau(
                "q1",
                "Trạng thái sức khỏe và sinh hoạt hiện tại như thế nào?",
                [
                    _dap("A", "Khỏe mạnh, đã nghỉ hưu, chủ yếu nghỉ ngơi."),
                    _dap("B", "Vẫn đang điều hành công việc, kinh doanh hoặc làm việc nhẹ."),
                    _dap("C", "Sức khỏe kém, thường xuyên đau ốm hoặc cần người chăm sóc."),
                ],
            ),
            _cau(
                "q2",
                "Hoàn cảnh chung sống hiện tại thế nào?",
                [
                    _dap("A", "Sống cùng con cháu."),
                    _dap("B", "Sống cùng bạn đời."),
                    _dap("C", "Sống một mình."),
                ],
            ),
            _cau(
                "q3",
                "Điều gì khiến đương số suy nghĩ nhiều nhất ở độ tuổi này?",
                [
                    _dap("A", "Sức khỏe, bệnh tật của bản thân hoặc bạn đời."),
                    _dap("B", "Sự nghiệp, tài chính và hạnh phúc của con cháu."),
                    _dap("C", "Phân chia tài sản, đất đai, thừa kế, di sản để lại."),
                    _dap("D", "Tu tập tâm linh, thiện nguyện, sự thanh thản trong tâm hồn."),
                ],
            ),
        ]
    return {"tuoi": tuoi, "nam_xem": NAM_XEM, "nhom": ten, "cau": cau}


def _chon(dap: dict, ma: str, hop: set[str]) -> str:
    gia = str(dap.get(ma, "")).strip()
    if gia not in hop:
        raise ValueError("Hãy chọn đủ câu hỏi về hoàn cảnh đang sống.")
    return gia


def _bo(dap: dict, *ma) -> None:
    for mot in ma:
        if str(dap.get(mot, "")).strip():
            raise ValueError("Có đáp án không thuộc nhóm tuổi này.")


def user_real_context(tuoi: int, dap: dict) -> tuple[str, str]:
    """Trả về mã ngắn và đoạn văn hoàn cảnh. Mã dùng để biết đáp án có đổi hay không."""
    if tuoi < 0 or tuoi > 120:
        raise ValueError("Tuổi không hợp lệ.")
    ten = nhom(tuoi)
    dau = f"Đương số {tuoi} tuổi, tính bằng năm xem {NAM_XEM} trừ năm sinh. "
    if ten == "tre":
        van, ma = _tre(dap)
    elif ten == "thanh_nien":
        van, ma = _thanh(dap)
    elif ten == "truong_thanh":
        van, ma = _truong(dap)
    else:
        van, ma = _gia(dap)
    van = (
        dau
        + van
        + " Danh xưng dùng Đương số. Mọi lời ở chương 3 và chương 4 phải khớp đúng hoàn cảnh này."
    )
    return f"{ten}|{ma}", van


def _tre(dap: dict) -> tuple[str, str]:
    q1 = _chon(dap, "q1", {"A", "B", "C"})
    if q1 in {"A", "B"}:
        q2 = _chon(dap, "q2", {"A1", "A2"})
        _bo(dap, "q3")
        o_nha = q1 == "A"
        noi = (
            "Ở nhà, được gia đình chăm sóc và bao bọc hoàn toàn."
            if o_nha
            else "Sống xa nhà, học nội trú hoặc ở nhờ nhà họ hàng."
        )
        if q2 == "A1":
            hoc = "Chưa đi học hoặc đang học mầm non."
            if o_nha:
                viec = (
                    "CẤM nói tiền bạc và sự nghiệp. "
                    "Chương 3 tập trung sức khỏe tiêu hóa và hô hấp, tính nết ngoan hay bướng, nguy cơ té ngã, sinh hoạt hàng ngày. "
                    "Chương 4 dịch khai trương và ký hợp đồng thành bắt đầu thói quen tốt, xin người lớn mua đồ chơi hoặc sách vở. "
                    "Người đọc hướng dẫn là cha mẹ."
                )
            else:
                viec = (
                    "CẤM nói tiền bạc, sự nghiệp và tình yêu. "
                    "Chương 3 nói sức khỏe khi vắng người thân, nỗi nhớ nhà và sinh hoạt ở chỗ ở nhờ. "
                    "Chương 4 nhắc an toàn khi di chuyển. Người lớn là người đọc hướng dẫn."
                )
        else:
            hoc = "Đang học tiểu học hoặc trung học cơ sở."
            if o_nha:
                viec = (
                    "CẤM nói kinh doanh. "
                    "Chương 3 tập trung trường lớp, thi cử, bạn bè, thầy cô và tâm lý tuổi mới lớn. "
                    "Chương 4 dịch ký kết và giao dịch thành thi cử, nộp bài, đăng ký ngoại khóa."
                )
            else:
                viec = (
                    "Chương 3 phân tích sự tự lập, nỗi nhớ nhà, nguy cơ bị lôi kéo bên ngoài, sức khỏe khi vắng người thân chăm sóc. "
                    "Chương 4 nhắc an toàn khi tự di chuyển và sinh hoạt tập thể. "
                    "CẤM tình yêu người lớn, đầu tư và kinh doanh."
                )
        return f"{noi} {hoc} {viec} Gọi là Đương số hoặc Bạn nhỏ, không gọi là bé.", f"{q1}|{q2}"
    q3 = _chon(dap, "q3", {"C1", "C2"})
    _bo(dap, "q2")
    if q3 == "C1":
        return (
            "Vừa đi học vừa làm thêm để phụ giúp gia đình. "
            "Được nói tiền công và việc phụ giúp, không nói đầu tư hay mở công ty. "
            "Chương 3 luận áp lực thời gian, vất vả thể chất và học hành bị ảnh hưởng. "
            "Chương 4 khuyên giữ sức khỏe, cẩn thận tai nạn lao động nhẹ, không nhận thêm việc vào ngày xấu. "
            "Gọi là Đương số hoặc Bạn nhỏ, không gọi là bé.",
            "C|C1",
        )
    return (
        "Đã nghỉ học hoàn toàn để đi làm kiếm tiền từ sớm. "
        "Chương 3 phân tích môi trường bươn chải sớm, đồng tiền do mồ hôi nước mắt, nguy cơ bị chèn ép, bóc lột hoặc tai nạn. "
        "Chương 4 chuyển 12 Trực thành nhận ca làm, nhận tiền công và giữ sức khỏe. "
        "Tuyệt đối không khuyên đầu tư, mở công ty hay ký hợp đồng kinh tế. "
        "Gọi là Đương số hoặc Bạn nhỏ, không gọi là bé.",
        "C|C2",
    )


def _thanh(dap: dict) -> tuple[str, str]:
    q1 = _chon(dap, "q1", {"A", "B", "C", "D", "E"})
    if q1 in {"A", "B"}:
        q2 = _chon(dap, "q2", {"A1", "A2"})
        _bo(dap, "q3")
        if q2 == "A2":
            cho_hoc = " Đang du học hoặc sống ở nước ngoài, nên viết thêm rào cản ngôn ngữ, khác văn hóa và chi phí sinh hoạt xứ người."
            cho_lam = " Đang du học hoặc sống ở nước ngoài, thêm rào cản ngôn ngữ, khác văn hóa, chi phí sinh hoạt và ca làm thêm ở xứ người."
        else:
            cho_hoc = " Đang ở trong nước."
            cho_lam = " Đang ở trong nước."
        if q1 == "A":
            return (
                "Đang đi học, phổ thông, đại học hoặc học nghề."
                + cho_hoc
                + " Chương 3 nói thi cử, đồ án, câu lạc bộ, tình cảm học đường và áp lực bài vở. "
                "Chương 4: ngày tốt dùng cho nộp hồ sơ và thi cử, ngày xấu khuyên cẩn thận xe cộ. "
                "Không khuyên đầu tư, kinh doanh, quản lý cấp dưới hay cưới xin.",
                f"A|{q2}",
            )
        return (
            "Vừa học vừa đi làm thêm."
            + cho_lam
            + " Chương 3 nói áp lực hai việc một lúc, thiếu ngủ, tiền chi tiêu cá nhân và lịch học với ca làm bị chồng. "
            "Chương 4 khuyên không nhận ca thêm vào ngày xấu để khỏi kiệt sức, và sắp xếp hạn nộp bài cho hợp. "
            "Không khuyên đầu tư vốn lớn hay đứng ra làm chủ.",
            f"B|{q2}",
        )
    _bo(dap, "q2", "q3")
    if q1 == "C":
        return (
            "Vừa tốt nghiệp, đang loay hoay tìm việc hoặc chờ định hướng. "
            "Chương 3 nói áp lực nhìn bạn bè cùng tuổi, sự chênh vênh khi rời trường, gửi hồ sơ và đi phỏng vấn. "
            "Chương 4: ngày tốt khuyên đi phỏng vấn, gặp nơi tuyển dụng và nhận việc đầu tiên. "
            "Không khuyên đầu tư vốn lớn.",
            "C",
        )
    if q1 == "D":
        return (
            "Đã thôi học hoàn toàn để đi làm toàn thời gian. Bỏ chuyện trường lớp. "
            "Chương 3 phân tích việc làm, lương, đồng nghiệp và va vấp sớm với người lớn tuổi ngoài xã hội. "
            "Chương 4 tập trung nhận ca, nhận lương và tránh mâu thuẫn đồng nghiệp. "
            "Không khuyên đầu tư vốn lớn.",
            "D",
        )
    return (
        "Đang gap-year: nghỉ ngơi hoặc còn mông lung, chưa rõ định hướng. "
        "Chương 3 nói khủng hoảng tuổi 20, hành trình tìm lại mình và các khóa học kỹ năng mềm. "
        "Chương 4: ngày tốt khuyên đi trải nghiệm, chữa lành và học kỹ năng mới. "
        "Tuyệt đối không tạo áp lực phải thành đạt hay kiếm tiền ngay.",
        "E",
    )


_VIEC_TRUONG = {
    "A": (
        "Công việc: làm công ăn lương, nhân viên hoặc cấp quản lý. "
        "Viết thăng tiến, chỉ tiêu, quan hệ với sếp và đồng nghiệp. "
        "Ngày tốt dùng để ký hợp đồng lao động hoặc đi công tác. "
        "Cấm khuyên khai trương hay ký hợp đồng kinh tế như người làm chủ."
    ),
    "B": (
        "Công việc: làm chủ, tự kinh doanh hoặc đầu tư tự do. "
        "Viết dòng vốn, đối tác và thị trường. "
        "Ngày tốt dùng để khai trương, ký hợp đồng kinh tế lớn và thu hồi công nợ."
    ),
    "C": (
        "Công việc: nội trợ, chăm sóc gia đình toàn thời gian. "
        "Cấm khuyên kinh doanh và khai trương. Tập trung chi tiêu gia đình và chăm tổ ấm."
    ),
    "D": (
        "Công việc: đang chuyển giao, thất nghiệp, tìm việc mới hoặc học chuyển ngành. "
        "Viết bế tắc tạm thời và gửi hồ sơ xin việc. "
        "Ngày tốt dùng để đi phỏng vấn và rèn luyện. Không khuyên khai trương."
    ),
}

_NHA_TRUONG = {
    "A": "Gia đạo: độc thân, chưa có người yêu hoặc đang tìm hiểu. Luận tình duyên mới. Không viết mâu thuẫn vợ chồng.",
    "B": "Gia đạo: đã lập gia đình hoặc sống chung, chưa có con. Luận sự đồng thuận, mâu thuẫn trong nhà, kế hoạch mua nhà hoặc sinh con.",
    "C": "Gia đạo: đã có gia đình và đang nuôi con. Viết nuôi dạy con và áp lực chi phí chăm con.",
    "D": (
        "Gia đạo: độc thân nuôi con, là cha hoặc mẹ đơn thân. "
        "Viết sự vất vả và nỗi một mình gánh tiền bạc lẫn con cái. Giọng đồng cảm. "
        "Cấm khuyên bàn bạc với bạn đời. Khi lá số có Cô Thần hoặc Quả Tú, nói nỗi tự gánh, không viết như đang có người ở bên."
    ),
}

_NOI_TRUONG = {
    "A": (
        "Nỗi bận tâm hàng đầu là sự nghiệp, tài sản, khởi nghiệp hoặc trả nợ. "
        "Chương 3 dành phần lớn cho cung Quan Lộc và Tài Bạch, luận dòng tiền trong đúng kiểu công việc phía trên. "
        "Người làm thuê không bị viết thành người làm chủ. Người nội trợ không bị khuyên khai trương."
    ),
    "B": (
        "Nỗi bận tâm hàng đầu là tình yêu, hôn nhân, gia đình hoặc con cái. "
        "Lướt qua sự nghiệp, xoáy sâu cung Phu Thê và Tử Tức theo đúng gia đạo phía trên. "
        "Hóa kỵ và sát tinh, nếu có trong lá số, dịch thành mâu thuẫn, xa cách, hoặc tin vui con cái khi họ đang có con. "
        "Người độc thân không có mâu thuẫn vợ chồng. Người đơn thân không được khuyên bàn bạc với bạn đời."
    ),
    "C": (
        "Nỗi bận tâm hàng đầu là sức khỏe và sự bình yên. "
        "Giọng như người lắng nghe. Lấy cung Phúc Đức và Tật Ách làm trung tâm. Khuyên buông bớt và giữ sức."
    ),
    "D": (
        "Nỗi bận tâm hàng đầu là rắc rối pháp lý, kiện tụng, thị phi. "
        "Chỉ phân tích Cự Môn, Thiên Hình, Liêm Trinh, Hóa Kỵ, Thái Tuế khi sao đó có trong nguyên liệu. "
        "Cảnh báo giấy tờ và hợp đồng. Không bịa sao."
    ),
}


def _truong(dap: dict) -> tuple[str, str]:
    q1 = _chon(dap, "q1", set(_VIEC_TRUONG))
    q2 = _chon(dap, "q2", set(_NHA_TRUONG))
    q3 = _chon(dap, "q3", set(_NOI_TRUONG))
    van = " ".join((_VIEC_TRUONG[q1], _NHA_TRUONG[q2], _NOI_TRUONG[q3]))
    return van, f"{q1}|{q2}|{q3}"


_SUC_GIA = {
    "A": "Đã nghỉ hưu, chủ yếu nghỉ ngơi. Cấm khuyên khai trương và khởi nghiệp. Nhấn mạnh khám bệnh và đi lại nhẹ nhàng.",
    "B": "Vẫn điều hành công việc, kinh doanh hoặc làm nhẹ. Viết chuyển giao việc và làm cố vấn, không vắt kiệt sức. Không khuyên khởi nghiệp mới hay đầu tư mạo hiểm.",
    "C": "Sức khỏe kém, thường đau ốm hoặc cần người chăm. Cấm khuyên khai trương, khởi nghiệp và đi xa. Nhấn mạnh khám bệnh, ở nhà và người trông.",
}

_O_GIA = {
    "A": "Sống cùng con cháu.",
    "B": "Sống cùng bạn đời. Viết sự nương tựa tuổi già.",
    "C": "Sống một mình. Cảnh báo té ngã khi không có ai biết. Khuyên chỗ gặp người cùng tuổi. Không khuyên đi xa một mình.",
}

_NOI_GIA = {
    "A": "Điều trăn trở nhất là sức khỏe của mình hoặc của bạn đời. Xoáy sâu cung Tật Ách và Phúc Đức. Chương 4 chỉ luận ngày đi khám, điều trị hoặc nghỉ dưỡng.",
    "B": "Điều trăn trở nhất là việc làm, tiền bạc và hạnh phúc của con cháu. Lấy cung Tử Tức làm trọng tâm. Khuyên bớt kiểm soát, để con cháu tự lập, tránh lo quá mà sinh bệnh.",
    "C": "Điều trăn trở nhất là chia tài sản, đất đai và thừa kế. Phân tích cung Điền Trạch và Tài Bạch theo hướng giữ và trao lại. Chương 4 ưu tiên ngày lập di chúc, sang tên sổ và họp mặt gia tộc. Không khuyên đầu tư mạo hiểm.",
    "D": "Điều trăn trở nhất là tu tập, việc thiện và sự thanh thản. Chương 4 luận ngày đi lễ, phóng sinh hoặc dọn ban thờ.",
}


def _gia(dap: dict) -> tuple[str, str]:
    q1 = _chon(dap, "q1", set(_SUC_GIA))
    q2 = _chon(dap, "q2", set(_O_GIA))
    q3 = _chon(dap, "q3", set(_NOI_GIA))
    return " ".join((_SUC_GIA[q1], _O_GIA[q2], _NOI_GIA[q3])), f"{q1}|{q2}|{q3}"
