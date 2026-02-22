import streamlit as st
from utils.auth import login_form, check_authentication, logout
from utils.database import init_database, get_week_data, get_all_playbook_rules
from datetime import datetime
import pandas as pd

st.set_page_config(
    page_title="Mind Balance",
    page_icon="🧠",
    layout="wide"
)

# CSS SIÊU ĐẸP - FOX MASCOT + GRADIENT TRENDY
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&family=Poppins:wght@400;600;700&display=swap');
    
    * { font-family: 'Quicksand', sans-serif; }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #667eea 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
    }
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .main .block-container {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20px);
        border-radius: 30px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        padding: 3rem 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    .big-title {
        font-family: 'Poppins', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0;
        color: white;
    }
    .subtitle {
        font-size: 1.3rem;
        text-align: center;
        color: rgba(255, 255, 255, 0.95);
        margin-bottom: 2rem;
        font-weight: 500;
    }
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.25) 0%, rgba(255, 255, 255, 0.15) 100%);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem !important;
        border: 2px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        border-color: rgba(255, 255, 255, 0.5);
    }
    [data-testid="metric-container"] label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.5);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
        box-shadow: 0 6px 20px rgba(240, 147, 251, 0.7);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%);
        backdrop-filter: blur(10px);
    }
    [data-testid="stSidebar"] * { color: white !important; }
    .element-container .stAlert {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.1) 100%);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        color: white !important;
    }
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.1) 100%);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        color: white !important;
        font-weight: 600;
    }
    .streamlit-expanderContent {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
        backdrop-filter: blur(10px);
        border-radius: 0 0 12px 12px;
        color: white !important;
    }
    h1, h2, h3, p, span, div, li { color: white !important; }
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.1) 100%);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] { color: rgba(255, 255, 255, 0.8) !important; font-weight: 600; }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 8px;
    }
    .stMarkdown { color: white !important; }

    /* ── FRAMEWORK SCIENCE SECTION ── */
    .fw-science-header { text-align: center; padding: 10px 0 20px 0; }
    .fw-science-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.5);
        border-radius: 100px;
        padding: 6px 20px;
        font-size: 12px;
        font-weight: 700;
        color: white;
        letter-spacing: 1px;
        margin-bottom: 14px;
    }
    .fw-science-title {
        font-family: 'Poppins', sans-serif;
        font-size: 2rem;
        font-weight: 900;
        color: white;
        margin: 0 0 8px 0;
        line-height: 1.2;
    }
    .fw-science-sub {
        color: rgba(255,255,255,0.8);
        font-size: 14px;
        max-width: 520px;
        margin: 0 auto;
        line-height: 1.7;
    }
    .fw-science-card {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 18px;
        padding: 18px 16px;
        transition: all 0.25s ease;
        cursor: default;
    }
    .fw-science-card:hover {
        background: rgba(255,255,255,0.2);
        border-color: rgba(255,255,255,0.45);
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    .fw-day-pill {
        display: inline-block;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
        background: rgba(255,255,255,0.25);
        color: white;
        border: 1px solid rgba(255,255,255,0.35);
    }
    .fw-card-name { font-size: 16px; font-weight: 800; color: white; margin: 2px 0 3px 0; }
    .fw-card-eng { font-size: 11px; color: rgba(255,255,255,0.55); margin-bottom: 10px; font-style: italic; }
    .fw-card-tagline { font-size: 13px; color: rgba(255,255,255,0.85); line-height: 1.5; font-weight: 600; margin-bottom: 10px; }
    .fw-card-body { font-size: 12.5px; color: rgba(255,255,255,0.7); line-height: 1.6; margin-bottom: 8px; }
    .fw-card-proof {
        font-size: 11px;
        color: rgba(255,255,255,0.5);
        font-style: italic;
        border-top: 1px solid rgba(255,255,255,0.15);
        padding-top: 8px;
        margin-top: 4px;
    }
    .fw-bottom-cta {
        text-align: center;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 20px;
        padding: 24px 20px;
        margin-top: 10px;
    }
    .fw-cta-title { font-size: 18px; font-weight: 900; color: white; margin: 8px 0 6px 0; }
    .fw-cta-sub { font-size: 13px; color: rgba(255,255,255,0.65); max-width: 400px; margin: 0 auto; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# HÀM HIỂN THỊ 7 FRAMEWORKS KHOA HỌC
# ═══════════════════════════════════════════════════════════
def render_framework_science():
    FRAMEWORKS = [
        {
            "day": "Thứ 2", "emoji": "🗂️",
            "name": "GTD Review", "eng": "Getting Things Done",
            "tagline": "Xếp việc đúng thứ tự, không bỏ sót gì cả",
            "body": "Não bạn không phải cái tủ nhớ. Cố nhớ 10 việc cùng lúc làm não quá tải, hiệu quả giảm 40%. Mind Balance giúp bạn đổ hết việc ra ngoài rồi sắp xếp theo deadline và độ ưu tiên thật sự.",
            "proof": "📖 David Allen (2001) — NASA, IBM và hàng triệu học sinh đang dùng",
        },
        {
            "day": "Thứ 3", "emoji": "🎯",
            "name": "Ma Trận Eisenhower", "eng": "Eisenhower Matrix",
            "tagline": "Việc QUAN TRỌNG ≠ việc KHẨN CẤP",
            "body": "Bận rộn cả ngày mà chẳng làm được gì — vì bạn ưu tiên việc 'kêu to' thay vì việc 'ảnh hưởng thật'. App tự chia công việc vào 4 ô, đặt việc quan trọng vào buổi sáng khi não còn tỉnh.",
            "proof": "📖 Tổng thống Eisenhower phát minh — Stephen Covey phổ biến trong '7 Habits'",
        },
        {
            "day": "Thứ 4", "emoji": "⚡",
            "name": "Chu Kỳ Năng Lượng", "eng": "Ultradian Rhythm",
            "tagline": "Não bạn có 'giờ vàng' và 'giờ xỉu' mỗi ngày",
            "body": "Não hoạt động theo chu kỳ 90 phút tập trung cao → 20 phút cần nghỉ. Học lúc não đang 'xỉu' thì hiệu quả giảm 60% dù cố gắng tới đâu. App theo dõi và đặt lịch theo đúng chu kỳ của bạn.",
            "proof": "📖 Peretz Lavie & Nathaniel Kleitman — Nghiên cứu Harvard, 200+ công trình xác nhận",
        },
        {
            "day": "Thứ 5", "emoji": "🤝",
            "name": "Nghệ Thuật Bỏ Bớt", "eng": "Delegation & Focus",
            "tagline": "Học sinh giỏi không làm nhiều nhất — biết việc gì KHÔNG cần làm",
            "body": "Làm quá nhiều = não kiệt sức = kết quả tệ hơn dù bỏ nhiều giờ hơn. App xác định 'core tasks' thật sự quan trọng, giúp bạn tập trung tối đa vào thứ thật sự có giá trị.",
            "proof": "📖 Warren Buffett: 'Người thành công nói KHÔNG với gần như mọi thứ' — Stanford xác nhận",
        },
        {
            "day": "Thứ 6", "emoji": "🔍",
            "name": "Nhìn Lại Để Tiến", "eng": "Reflection Framework",
            "tagline": "Làm mà không nhìn lại = tuần sau y chang tuần này",
            "body": "Não học qua phản tư, không phải qua trải nghiệm đơn thuần. Học 10 tiếng/ngày mà không nhìn lại, tuần sau vẫn mắc y chang lỗi cũ. App tóm tắt pattern và chỉ cho bạn đúng chỗ cần thay đổi.",
            "proof": "📖 John Dewey — Lý thuyết học tập phản chiếu, ứng dụng tại Harvard Business School",
        },
        {
            "day": "Thứ 7", "emoji": "🛡️",
            "name": "Kế Hoạch Dự Phòng", "eng": "If-Then Planning",
            "tagline": "Biết mình nên làm nhưng vẫn không làm được? Đây là lý do",
            "body": "Não thiếu 'kịch bản dự phòng' khi gặp trở ngại nên mặc định chọn việc dễ hơn. App giúp bạn đặt trước quy tắc tự động: 'Nếu mệt → làm việc nhẹ', 'Nếu hết giờ → cắt việc ít quan trọng'.",
            "proof": "📖 Peter Gollwitzer (NYU) — 94 nghiên cứu xác nhận: tăng hoàn thành mục tiêu 300%",
        },
        {
            "day": "Chủ Nhật", "emoji": "🌿",
            "name": "Phục Hồi Chủ Động", "eng": "Active Recovery",
            "tagline": "Nằm coi TikTok KHÔNG phải nghỉ ngơi — não vẫn đang tiêu hao",
            "body": "Passive rest (xem điện thoại, TV) không tái tạo năng lượng não — bạn vẫn mệt dù 'nghỉ' cả ngày. App gợi ý active rest phù hợp mức năng lượng còn lại để não thật sự nạp lại pin.",
            "proof": "📖 Matthew Walker — 'Why We Sleep' (2017), giải thích cơ chế phục hồi não bộ",
        },
    ]

    st.markdown("""
    <div class="fw-science-header">
        <div class="fw-science-badge">🔬 DỰA TRÊN 7 NGHIÊN CỨU KHOA HỌC</div>
        <div class="fw-science-title">Tại sao Mind Balance thật sự hiệu quả?</div>
        <div class="fw-science-sub">
            Không phải app xếp lịch thông thường. Mỗi ngày trong tuần,
            Mind Balance áp dụng một framework tâm lý học được kiểm chứng
            để tối ưu não bộ của bạn.
        </div>
    </div>
    """, unsafe_allow_html=True)

    pairs = [FRAMEWORKS[i:i+2] for i in range(0, len(FRAMEWORKS), 2)]
    for pair in pairs:
        cols = st.columns(len(pair))
        for col, fw in zip(cols, pair):
            with col:
                st.markdown(f"""
                <div class="fw-science-card">
                    <div class="fw-day-pill">{fw['day']}</div>
                    <div style="font-size:28px; margin-bottom:6px;">{fw['emoji']}</div>
                    <div class="fw-card-name">{fw['name']}</div>
                    <div class="fw-card-eng">{fw['eng']}</div>
                    <div class="fw-card-tagline">"{fw['tagline']}"</div>
                    <div class="fw-card-body">{fw['body']}</div>
                    <div class="fw-card-proof">{fw['proof']}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("""
    <div class="fw-bottom-cta">
        <div style="font-size:36px;">🦊</div>
        <div class="fw-cta-title">Mỗi ngày một framework. Mỗi tuần một phiên bản tốt hơn.</div>
        <div class="fw-cta-sub">
            Mind Balance không chỉ nhắc việc — nó học cách bạn hoạt động
            và điều chỉnh lịch theo đúng khoa học, riêng cho bạn.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════

if not check_authentication():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem; animation: fadeInDown 0.8s ease;">
        <div style="font-size: 8rem; display: inline-block; animation: bounce 2s ease-in-out infinite; filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.2));">🦊</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="big-title">🧠 Mind Balance</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Hệ thống tư duy có cấu trúc</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        login_form()
        st.markdown("---")
        with st.expander("ℹ️ Mind Balance là gì?"):
            st.markdown("""
            **Mind Balance KHÔNG phải:**
            - ❌ App tạo prompt
            - ❌ Chatbot therapy
            - ❌ Mood tracker thông thường
            
            **Mind Balance LÀ:**
            - ✅ Hệ thống thu thập data có cấu trúc
            - ✅ Phát hiện patterns tự động
            - ✅ **7 frameworks tư duy** dựa trên nghiên cứu tâm lý học
            - ✅ Xây dựng playbook cá nhân
            - ✅ Tạo AI prompt context-rich (optional)
            
            **Kết quả:** Bạn tự học cách xử lý stress thông minh hơn!
            
            👉 Mỗi ngày = 1 framework khác nhau từ GTD, Eisenhower, Ultradian Rhythm...
            """)

else:
    init_database(st.session_state.username)
    
    with st.sidebar:
        st.success(f"👋 Xin chào **{st.session_state.name}**")
        
        if st.button("🚪 Đăng xuất", use_container_width=True):
            logout()
        
        st.markdown("---")
        st.caption("📍 Điều hướng nhanh")
        st.page_link("pages/1_📝_Nhập_Liệu_Hàng_Ngày.py", label="📝 Check-in hôm nay")
        st.page_link("pages/2_📊_Tổng_Kết_Tuần.py", label="📊 Xem phân tích")
        st.page_link("pages/3_📚_Sổ_Tay_Cá_Nhân.py", label="📚 Playbook của tôi")
        
        st.markdown("---")
        if st.button("🧠 Tại sao app hiệu quả?", use_container_width=True):
            st.session_state.show_science = True
    
    # Header
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem; animation: fadeInDown 0.8s ease;">
        <div style="font-size: 6rem; display: inline-block; animation: bounce 2s ease-in-out infinite; filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));">🦊</div>
        <h1 style="margin: 0.5rem 0 0 0; font-family: 'Poppins', sans-serif; font-size: 2.5rem; font-weight: 700; color: white;">🧠 Mind Balance Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9; color: white;">Hôm nay: {datetime.now().strftime('%A, %d/%m/%Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    df_week = get_week_data(st.session_state.username)
    df_playbook = get_all_playbook_rules(st.session_state.username)

    if st.session_state.get('show_science', False):
        render_framework_science()
        if st.button("✖️ Đóng", key="close_science"):
            st.session_state.show_science = False
            st.rerun()
        st.markdown("---")

    st.markdown("---")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        days_tracked = len(df_week)
        st.metric("📅 Ngày đã theo dõi", f"{days_tracked}/7")
    with col2:
        if days_tracked > 0:
            import pandas as pd_local
            avg_energy = pd_local.to_numeric(df_week['energy_level'], errors='coerce').mean()
            st.metric("⚡ Năng lượng TB", f"{avg_energy:.1f}/10")
        else:
            st.metric("⚡ Năng lượng TB", "—")
    with col3:
        playbook_count = len(df_playbook)
        verified_count = len(df_playbook[df_playbook['status'] == 'verified']) if playbook_count > 0 else 0
        st.metric("📚 Playbook Rules", f"{verified_count} verified")
    with col4:
        if days_tracked > 0:
            import json as _json
            def _count_tasks(x):
                if isinstance(x, list):
                    return len(x)
                try:
                    return len(_json.loads(x))
                except Exception:
                    return 0
            total_tasks = sum(df_week['tasks'].apply(_count_tasks))
            st.metric("📋 Tổng công việc", total_tasks)
        else:
            st.metric("📋 Tổng công việc", "—")
    
    st.markdown("---")
    
    st.subheader("🚀 Hành động nhanh")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 Check-in hôm nay", use_container_width=True, type="primary"):
            st.switch_page("pages/1_📝_Nhập_Liệu_Hàng_Ngày.py")
    with col2:
        if st.button("📊 Xem phân tích tuần", use_container_width=True):
            st.switch_page("pages/2_📊_Tổng_Kết_Tuần.py")
    with col3:
        if st.button("📚 Mở Playbook", use_container_width=True):
            st.switch_page("pages/3_📚_Sổ_Tay_Cá_Nhân.py")
    
    st.markdown("---")
    
    if days_tracked == 0:
        st.info("👋 Chào mừng đến Mind Balance! Hãy bắt đầu với check-in đầu tiên.")
        st.markdown("### 🎯 Cách sử dụng:")
        st.markdown("""
        1. **📝 Check-in hàng ngày** (1-2 phút)
           - Ghi lại trạng thái tinh thần, năng lượng
           - Liệt kê công việc hôm nay
           - Xem framework tư duy theo ngày
        
        2. **📊 Xem phân tích sau 3+ ngày**
           - 3 biểu đồ tự động
           - Phát hiện patterns
           - Tạo AI prompt context-rich
        
        3. **📚 Xây dựng Playbook**
           - Ghi lại quy luật từ kinh nghiệm
           - Test và verify
           - Tạo "sách hướng dẫn" cho chính mình
        """)
        if st.button("🚀 Bắt đầu check-in đầu tiên", type="primary", use_container_width=True):
            st.switch_page("pages/1_📝_Nhập_Liệu_Hàng_Ngày.py")
    else:
        tab1, tab2 = st.tabs(["📈 Xu hướng tuần này", "📚 Playbook gần đây"])
        
        with tab1:
            if days_tracked >= 3:
                from utils.charts import create_energy_trend
                fig = create_energy_trend(df_week)
                st.plotly_chart(fig, use_container_width=True)
                st.info(f"Bạn đã check-in {days_tracked} ngày tuần này. {'✅ Tuyệt vời!' if days_tracked >= 6 else '💪 Hãy tiếp tục!'}")
            else:
                st.warning(f"Cần ít nhất 3 ngày để hiển thị biểu đồ. Bạn đang có {days_tracked}/3 ngày.")
        
        with tab2:
            if playbook_count == 0:
                st.info("Bạn chưa có rule nào trong playbook. Hãy thêm rule đầu tiên sau khi phân tích tuần!")
            else:
                recent_rules = df_playbook.head(3)
                for idx, row in recent_rules.iterrows():
                    status_emoji = {'verified': '✅', 'testing': '🧪', 'failed': '❌'}
                    st.markdown(f"**{status_emoji.get(row['status'], '📌')} {row['rule_title']}**")
                    st.caption(f"Action: {row['action'][:100]}...")
                    st.markdown("---")
                if st.button("Xem tất cả rules →"):
                    st.switch_page("pages/3_📚_Sổ_Tay_Cá_Nhân.py")
    
    # Section 7 Frameworks
    st.markdown("---")
    render_framework_science()

    st.markdown("---")
    st.caption("💡 Tip: Check-in đều đặn mỗi ngày để phát hiện patterns chính xác hơn!")