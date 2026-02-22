import streamlit as st
from datetime import datetime
from utils.database import (init_database, save_checkin, get_checkin_today,
                           save_task_metadata, get_task_metadata,
                           save_fixed_schedule, get_fixed_schedule,
                           get_current_week_range, save_improvement_note)
from utils.auth import check_authentication
from utils.ui_components import apply_gradient_theme, show_fox_header
import json
import base64
import streamlit.components.v1 as components

st.set_page_config(page_title="Nhập liệu hàng ngày", page_icon="📝", layout="wide")
apply_gradient_theme()

if not check_authentication():
    st.warning("⚠️ Vui lòng đăng nhập trước!")
    st.stop()

username = st.session_state.username
init_database(username)

show_fox_header("📝 Nhập liệu hàng ngày")

weekday_emoji = {
    "Monday": "📅", "Tuesday": "📘", "Wednesday": "⚡", "Thursday": "🤝",
    "Friday": "🎯", "Saturday": "📋", "Sunday": "😴"
}
today_weekday = datetime.now().strftime("%A")
emoji = weekday_emoji.get(today_weekday, "📅")
st.markdown(f"**Hôm nay:** {emoji} {datetime.now().strftime('%A, %d/%m/%Y')}")

existing_checkin = get_checkin_today(username)  # Trả về dict hoặc None

# Session state
if 'num_fixed' not in st.session_state:
    st.session_state.num_fixed = 0
if 'num_tasks' not in st.session_state:
    st.session_state.num_tasks = 3
if 'editing_checkin' not in st.session_state:
    st.session_state.editing_checkin = False
if 'show_prompt' not in st.session_state:
    st.session_state.show_prompt = False


# ===== NÚT COPY AN TOÀN (base64) =====
def render_copy_button(prompt_text: str, button_id: str = "copybtn"):
    b64 = base64.b64encode(prompt_text.encode('utf-8')).decode('ascii')
    components.html(f"""
    <button id="{button_id}" onclick="
        try {{
            var b64 = '{b64}';
            var bin = atob(b64);
            var bytes = new Uint8Array(bin.length);
            for (var i = 0; i < bin.length; i++) {{ bytes[i] = bin.charCodeAt(i); }}
            var text = new TextDecoder('utf-8').decode(bytes);
            navigator.clipboard.writeText(text).then(function() {{
                document.getElementById('{button_id}').innerText = '✅ Đã copy!';
                setTimeout(function() {{
                    document.getElementById('{button_id}').innerText = '📋 Copy Prompt';
                }}, 2000);
            }}).catch(function() {{
                document.getElementById('{button_id}').innerText = '❌ Lỗi clipboard';
            }});
        }} catch(e) {{
            document.getElementById('{button_id}').innerText = '❌ ' + e.message;
        }}
    " style="
        width:100%; padding:0.6rem 1rem;
        background:linear-gradient(135deg,#667eea,#764ba2);
        color:white; border:none; border-radius:10px;
        font-size:1rem; font-weight:600; cursor:pointer;
        font-family:sans-serif;
    ">📋 Copy Prompt</button>
    """, height=50)


# ===== FORM CHECK-IN =====
def show_checkin_form():
    st.info("💡 Hãy dành 2-3 phút để check-in hôm nay")

    with st.form("daily_checkin_form"):
        st.subheader("🧠 Bạn cảm thấy thế nào hôm nay?")

        col1, col2 = st.columns(2)
        with col1:
            mental_load = st.radio("Mức độ áp lực tinh thần:",
                ["Nhẹ nhàng", "Bình thường", "Nặng", "Cực nặng"], horizontal=True)
            energy_level = st.slider("Mức năng lượng:", 1, 10, 5)
        with col2:
            pressure_source = st.radio("Nguồn áp lực chính:",
                ["Deadline bên ngoài", "Tự đặt ra", "Cả hai"], horizontal=True)
            sleep_quality = st.select_slider("Chất lượng giấc ngủ:",
                options=[1,2,3,4,5], value=3, format_func=lambda x: "⭐"*x)

        st.markdown("---")
        st.subheader("📅 Lịch cố định hôm nay")
        st.caption("Nhập các lịch KHÔNG THỂ THAY ĐỔI (học trên lớp, học kèm...)")

        fixed_schedule = []
        for i in range(st.session_state.num_fixed):
            st.markdown(f"**Lịch {i+1}:**")
            ca, cb, cc = st.columns([2,1,1])
            with ca:
                fn = st.text_input("Tên:", key=f"fixed_name_{i}", placeholder="VD: Học trên lớp")
            with cb:
                fs = st.time_input("Từ:", datetime.strptime("07:00","%H:%M").time(), key=f"fixed_start_{i}")
            with cc:
                fe = st.time_input("Đến:", datetime.strptime("11:30","%H:%M").time(), key=f"fixed_end_{i}")
            if fn:
                fixed_schedule.append({'name': fn, 'start': fs.strftime("%H:%M"), 'end': fe.strftime("%H:%M")})

        st.markdown("---")
        st.subheader("📋 Công việc cần làm")
        st.caption("Các công việc trong khoảng thời gian rảnh")

        tasks_with_meta = []
        for i in range(st.session_state.num_tasks):
            st.markdown(f"**Công việc {i+1}:**")
            c1, c2, c3, c4 = st.columns([3,2,2,2])
            with c1:
                tn = st.text_input("Tên:", key=f"task_{i}", placeholder="VD: Làm bài Sinh học")
            with c2:
                tt = st.selectbox("Thời gian:", [15,30,45,60,90,120,180,240],
                    format_func=lambda x: f"{x//60}h{x%60}'" if x>=60 else f"{x}'", key=f"time_{i}")
            with c3:
                tp = st.selectbox("Ưu tiên:", ["Cao","Trung bình","Thấp"], key=f"priority_{i}")
            with c4:
                ttype = st.selectbox("Loại:", ["Học sâu","Công việc nhẹ","Họp/Gặp mặt"], key=f"type_{i}")
            if tn:
                tasks_with_meta.append({'name': tn, 'estimated_time': tt, 'priority': tp, 'task_type': ttype})

        st.markdown("---")
        task_feeling = st.radio("Nhìn vào danh sách, bạn cảm thấy:",
            ["Hoàn toàn làm được","Hơi căng nhưng OK","Nặng","Không thể nào"], horizontal=True)

        submitted = st.form_submit_button("💾 Lưu check-in", type="primary", use_container_width=True)

        if submitted:
            if len(tasks_with_meta) == 0:
                st.error("❌ Vui lòng nhập ít nhất 1 công việc!")
            else:
                data = {
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'mental_load': mental_load,
                    'energy_level': energy_level,
                    'pressure_source': pressure_source,
                    'sleep_quality': sleep_quality,
                    'tasks': [t['name'] for t in tasks_with_meta],
                    'task_feeling': task_feeling
                }
                if save_checkin(username, data):
                    save_task_metadata(username, data['date'], tasks_with_meta)
                    if fixed_schedule:
                        save_fixed_schedule(username, data['date'], fixed_schedule)
                    st.session_state.editing_checkin = False
                    st.session_state.show_prompt = False
                    st.success("✅ Đã lưu!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Có lỗi xảy ra!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Thêm lịch cố định", use_container_width=True):
            st.session_state.num_fixed += 1
            st.rerun()
    with col2:
        if st.button("➕ Thêm công việc", use_container_width=True):
            st.session_state.num_tasks += 1
            st.rerun()

    if st.session_state.editing_checkin:
        st.markdown("---")
        if st.button("❌ Hủy cập nhật", use_container_width=True):
            st.session_state.editing_checkin = False
            st.session_state.num_fixed = 0
            st.session_state.num_tasks = 3
            st.rerun()


# ===== HIỂN THỊ CHÍNH =====

if not existing_checkin:
    show_checkin_form()

elif existing_checkin and st.session_state.editing_checkin:
    st.warning("🔄 Đang cập nhật check-in hôm nay:")
    show_checkin_form()

else:
    st.success("✅ Bạn đã check-in hôm nay!")

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("🔄 Cập nhật lại", use_container_width=True):
            st.session_state.editing_checkin = True
            st.session_state.num_fixed = 0
            st.session_state.num_tasks = 3
            st.session_state.show_prompt = False
            st.rerun()

    st.markdown("---")
    st.subheader("📸 Tổng quan hôm nay")

    # ← TRUY CẬP BẰNG TÊN CỘT (dict), không dùng index số
    tasks   = json.loads(existing_checkin['tasks'])
    date    = existing_checkin['date']
    energy  = existing_checkin['energy_level']

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tinh thần", existing_checkin['mental_load'])
        st.metric("Năng lượng", f"{energy}/10")
    with col2:
        st.metric("Áp lực", existing_checkin['pressure_source'])
        st.metric("Giấc ngủ", "⭐" * existing_checkin['sleep_quality'])
    with col3:
        st.metric("Công việc", len(tasks))
        st.metric("Cảm giác", existing_checkin['task_feeling'])

    fixed_df      = get_fixed_schedule(username, date)
    tasks_meta_df = get_task_metadata(username, date)

    with st.expander("📋 Chi tiết"):
        if len(fixed_df) > 0:
            st.markdown("**Lịch cố định:**")
            for _, row in fixed_df.iterrows():
                st.write(f"• {row['schedule_name']}: {row['start_time']} - {row['end_time']}")
        st.markdown("**Công việc:**")
        for i, task in enumerate(tasks, 1):
            st.write(f"{i}. {task}")

    st.markdown("---")
    st.subheader("🤖 Prompt AI")

    weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
    framework_names = {
        "Monday":    "Thứ 2 - Xem lại tổng thể",
        "Tuesday":   "Thứ 3 - Ma trận ưu tiên",
        "Wednesday": "Thứ 4 - Chu kỳ năng lượng",
        "Thursday":  "Thứ 5 - Bớt tải công việc",
        "Friday":    "Thứ 6 - Nhìn lại để học hỏi",
        "Saturday":  "Thứ 7 - Kế hoạch dự phòng",
        "Sunday":    "Chủ nhật - Phục hồi chủ động"
    }
    framework_name = framework_names.get(weekday, "Thứ 2 - Xem lại tổng thể")

    col_fw1, col_fw2 = st.columns([3, 1])
    with col_fw1:
        st.info(f"**Phương pháp hôm nay:** {framework_name}")
    with col_fw2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔬 Tại sao dùng phương pháp này?", use_container_width=True, key="btn_why_fw"):
            st.session_state.show_science = True
            st.switch_page("app.py")

    from utils.prompt_builder import build_daily_framework_prompt_with_schedule

    data_for_prompt = {
        'mental_load': existing_checkin['mental_load'],
        'energy_level': energy,
        'tasks': tasks,
        'tasks_meta': tasks_meta_df.to_dict('records') if len(tasks_meta_df) > 0 else [],
        'fixed_schedule': fixed_df.to_dict('records') if len(fixed_df) > 0 else []
    }
    prompt = build_daily_framework_prompt_with_schedule(date, data_for_prompt, framework_name)

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        btn_label = "🙈 Ẩn Prompt" if st.session_state.show_prompt else "👁️ Xem Prompt"
        if st.button(btn_label, use_container_width=True, type="primary", key="btn_toggle"):
            st.session_state.show_prompt = not st.session_state.show_prompt
            st.rerun()
    with col_p2:
        render_copy_button(prompt, "copydailybtn")

    if st.session_state.show_prompt:
        st.code(prompt, language="markdown")

    st.markdown("---")
    st.subheader("📝 Ghi chú từ AI")
    with st.expander("Lưu lời khuyên"):
        with st.form("save_note"):
            note = st.text_area("AI khuyên gì?", height=100)
            note_type = st.radio("Loại:", ["Hôm nay","Tuần sau","Quy luật"], horizontal=True)
            if st.form_submit_button("💾 Lưu"):
                if note.strip():
                    week_start, _ = get_current_week_range()
                    if save_improvement_note(username, week_start, note, note_type):
                        st.success("✅ Đã lưu!")
                    else:
                        st.error("❌ Lỗi!")