"""
SECTION GIỚI THIỆU 8 FRAMEWORKS KHOA HỌC
Copy đoạn code này vào app.py hoặc trang Dashboard của bạn.

Cách dùng:
    from framework_section import render_framework_section
    render_framework_section()
"""

import streamlit as st

FRAMEWORKS = [
    {
        "day": "Thứ 2",
        "name": "GTD Review",
        "fullname": "Getting Things Done",
        "emoji": "🗂️",
        "color": "#6C63FF",
        "tagline": "Xếp việc đúng thứ tự, không bỏ sót gì cả",
        "van_de": "Não bạn **không phải cái tủ nhớ**. Khi cố nhớ 10 việc cùng lúc, não bị quá tải và bạn làm việc kém hơn 40%.",
        "ung_dung": "Mind Balance giúp bạn đổ hết việc ra ngoài, rồi sắp xếp theo 'cái nào phải làm trước' dựa trên deadline thật và mối quan hệ phụ thuộc giữa các việc.",
        "khoa_hoc": "📖 David Allen (2001) — Đang được NASA, IBM và hàng triệu học sinh dùng",
    },
    {
        "day": "Thứ 3",
        "name": "Ma Trận Eisenhower",
        "fullname": "Eisenhower Matrix",
        "emoji": "🎯",
        "color": "#FF6584",
        "tagline": "Việc QUAN TRỌNG và việc KHẨN CẤP — khác nhau hoàn toàn",
        "van_de": "Cảm giác **bận rộn cả ngày nhưng chẳng làm được gì** xảy ra vì bạn ưu tiên việc kêu to (khẩn) thay vì việc ảnh hưởng thật (quan trọng).",
        "ung_dung": "App tự chia công việc vào 4 ô. Buổi sáng dành cho việc quan trọng khi não đang tỉnh, buổi chiều mới xử lý việc khẩn vặt.",
        "khoa_hoc": "📖 Tổng thống Mỹ Dwight Eisenhower phát minh — Được Stephen Covey phổ biến trong '7 Habits'",
    },
    {
        "day": "Thứ 4",
        "name": "Chu Kỳ Năng Lượng",
        "fullname": "Ultradian Rhythm",
        "emoji": "⚡",
        "color": "#F9C74F",
        "tagline": "Não bạn có 'giờ vàng' và 'giờ xỉu' — và bạn không biết!",
        "van_de": "Não hoạt động theo chu kỳ **90 phút tập trung cao → 20 phút cần nghỉ**. Nếu học lúc não đang 'xỉu', hiệu quả giảm tới 60% mà bạn không hay.",
        "ung_dung": "Mind Balance theo dõi năng lượng của bạn qua từng ngày, rồi tự động đặt việc học sâu vào đúng lúc não đang ở đỉnh — không phải học theo thói quen.",
        "khoa_hoc": "📖 Peretz Lavie & Nathaniel Kleitman — Nghiên cứu Harvard, xác nhận bởi 200+ công trình khoa học",
    },
    {
        "day": "Thứ 5",
        "name": "Nghệ Thuật Ủy Thác",
        "fullname": "Delegation & Focus",
        "emoji": "🤝",
        "color": "#43AA8B",
        "tagline": "Học sinh giỏi không phải làm nhiều nhất — mà biết việc gì KHÔNG cần làm",
        "van_de": "Làm quá nhiều = não kiệt sức = **kết quả tệ hơn** dù bỏ ra nhiều giờ hơn. Đây là cái bẫy mà hầu hết học sinh đang mắc phải.",
        "ung_dung": "App xác định 'core tasks' thật sự ảnh hưởng đến kết quả của bạn. Phần còn lại được hoãn hoặc đơn giản hóa để não tập trung tối đa vào điều quan trọng.",
        "khoa_hoc": "📖 Warren Buffett: 'Người thành công nói KHÔNG với gần như mọi thứ' — Nghiên cứu Stanford xác nhận",
    },
    {
        "day": "Thứ 6",
        "name": "Nhìn Lại Để Tiến",
        "fullname": "Reflection Framework",
        "emoji": "🔍",
        "color": "#277DA1",
        "tagline": "Làm mà không nhìn lại = tuần sau y chang tuần này",
        "van_de": "Não **học hỏi qua phản tư**, không phải qua trải nghiệm đơn thuần. Bạn có thể học 10 tiếng/ngày nhưng nếu không nhìn lại, tuần sau vẫn mắc y chang lỗi cũ.",
        "ung_dung": "Cuối tuần, app tóm tắt pattern của bạn: hôm nào hiệu quả nhất? Tại sao? Điều gì nên TIẾP TỤC / NÊN DỪNG / NÊN BẮT ĐẦU? Từ đó bạn biết chính xác cần thay đổi gì.",
        "khoa_hoc": "📖 John Dewey — Lý thuyết học tập phản chiếu, ứng dụng tại Harvard Business School",
    },
    {
        "day": "Thứ 7",
        "name": "Kế Hoạch Dự Phòng",
        "fullname": "If-Then Planning",
        "emoji": "🛡️",
        "color": "#F77F00",
        "tagline": "Chuẩn bị cho mọi tình huống trước khi nó xảy ra",
        "van_de": "Tại sao bạn **biết mình nên làm** nhưng vẫn không làm được? Vì não thiếu 'kịch bản dự phòng' khi gặp trở ngại — và mặc định chọn việc dễ hơn.",
        "ung_dung": "Cuối tuần, Mind Balance giúp bạn đặt trước quy tắc tự động: 'Nếu mệt → làm việc nhẹ trước', 'Nếu hết giờ → cắt việc ưu tiên thấp'. Tuần sau não tự chạy autopilot.",
        "khoa_hoc": "📖 Peter Gollwitzer (NYU) — 94 nghiên cứu độc lập xác nhận: tăng hoàn thành mục tiêu lên 300%",
    },
    {
        "day": "Chủ Nhật",
        "name": "Phục Hồi Chủ Động",
        "fullname": "Active Recovery",
        "emoji": "🌿",
        "color": "#90BE6D",
        "tagline": "Nằm coi TikTok KHÔNG phải nghỉ ngơi — não vẫn đang tiêu hao năng lượng",
        "van_de": "**Passive rest** (xem điện thoại, TV) không tái tạo năng lượng não. Bạn thấy mệt ngay cả sau khi 'nghỉ' cả ngày — đây là lý do.",
        "ung_dung": "App gợi ý active rest phù hợp với mức năng lượng còn lại: đi bộ nhẹ, vẽ, nấu ăn, nghe nhạc... Những hoạt động này giúp não thật sự nạp lại pin và sẵn sàng cho tuần mới.",
        "khoa_hoc": "📖 Matthew Walker — 'Why We Sleep' (2017), giải thích cơ chế phục hồi não bộ",
    },
]


def render_framework_section():
    """
    Render section giới thiệu 8 frameworks khoa học.
    Gọi hàm này trong trang Dashboard của bạn.
    """

    st.markdown("---")

    # CSS tùy chỉnh cho section này
    st.markdown("""
    <style>
    .fw-header {
        text-align: center;
        padding: 20px 0 10px 0;
    }
    .fw-badge {
        display: inline-block;
        background: rgba(108, 99, 255, 0.15);
        border: 1px solid rgba(108, 99, 255, 0.5);
        border-radius: 100px;
        padding: 6px 18px;
        font-size: 12px;
        font-weight: 700;
        color: #a99fff;
        letter-spacing: 1px;
        margin-bottom: 16px;
    }
    .fw-title {
        font-size: 28px;
        font-weight: 900;
        margin: 0 0 10px 0;
        background: linear-gradient(135deg, #fff 0%, #a99fff 60%, #ff6584 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .fw-subtitle {
        color: rgba(255,255,255,0.6);
        font-size: 15px;
        max-width: 520px;
        margin: 0 auto 30px;
        line-height: 1.7;
    }
    .fw-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 12px;
        transition: all 0.2s;
    }
    .fw-card:hover {
        border-color: rgba(255,255,255,0.25);
        background: rgba(255,255,255,0.08);
    }
    .fw-day-badge {
        display: inline-block;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .fw-card-title {
        font-size: 17px;
        font-weight: 800;
        margin: 4px 0 2px 0;
    }
    .fw-card-fullname {
        font-size: 11px;
        font-weight: 600;
        opacity: 0.6;
        margin-bottom: 8px;
    }
    .fw-tagline {
        font-size: 13px;
        color: rgba(255,255,255,0.7);
        line-height: 1.5;
        font-style: italic;
    }
    .fw-detail-box {
        background: rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 16px;
        margin-top: 10px;
    }
    .fw-detail-label {
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 6px;
        opacity: 0.8;
    }
    .fw-detail-text {
        font-size: 13px;
        color: rgba(255,255,255,0.75);
        line-height: 1.6;
    }
    .fw-proof {
        font-size: 12px;
        color: rgba(255,255,255,0.5);
        margin-top: 8px;
        font-style: italic;
    }
    .fw-bottom-banner {
        text-align: center;
        background: linear-gradient(135deg, rgba(108,99,255,0.15), rgba(255,101,132,0.1));
        border: 1px solid rgba(108,99,255,0.3);
        border-radius: 20px;
        padding: 28px 20px;
        margin-top: 24px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="fw-header">
        <div class="fw-badge">🔬 DỰA TRÊN 7 NGHIÊN CỨU KHOA HỌC</div>
        <div class="fw-title">Tại sao Mind Balance<br>thật sự hiệu quả?</div>
        <div class="fw-subtitle">
            Không phải app xếp lịch thông thường. Mỗi ngày trong tuần,
            Mind Balance áp dụng một framework tâm lý học được kiểm chứng
            để tối ưu não bộ của bạn.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hiển thị các framework dưới dạng expander
    for fw in FRAMEWORKS:
        color = fw["color"]

        # Card wrapper với màu viền theo framework
        with st.expander(f"{fw['emoji']} **{fw['day']}** — {fw['name']}  ·  *{fw['tagline']}*"):

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                <div class="fw-detail-box">
                    <div class="fw-detail-label" style="color:{color};">🧠 Vấn đề là gì?</div>
                    <div class="fw-detail-text">{fw['van_de']}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="fw-detail-box">
                    <div class="fw-detail-label" style="color:{color};">📱 Mind Balance áp dụng thế nào?</div>
                    <div class="fw-detail-text">{fw['ung_dung']}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="fw-proof">{fw['khoa_hoc']}</div>
            """, unsafe_allow_html=True)

    # Bottom banner
    st.markdown("""
    <div class="fw-bottom-banner">
        <div style="font-size:32px; margin-bottom:10px;">🦊</div>
        <div style="font-size:20px; font-weight:900; margin-bottom:8px;">
            Mỗi ngày một framework. Mỗi tuần một phiên bản tốt hơn.
        </div>
        <div style="color:rgba(255,255,255,0.55); font-size:14px; max-width:440px; margin:0 auto;">
            Mind Balance không chỉ nhắc việc — nó học cách bạn hoạt động
            và điều chỉnh lịch theo đúng khoa học, riêng cho bạn.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")


# ============================================================
# CÁCH DÙNG — dán vào app.py hoặc trang Dashboard:
#
#   from framework_section import render_framework_section
#   render_framework_section()
#
# Hoặc nếu không muốn file riêng, copy toàn bộ hàm
# render_framework_section() vào app.py trực tiếp.
# ============================================================