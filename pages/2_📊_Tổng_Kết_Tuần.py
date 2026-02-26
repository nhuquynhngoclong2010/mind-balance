import streamlit as st
from datetime import datetime, timedelta
from utils.database import (get_week_data, init_database, get_current_week_range,
                           save_weekly_history, is_new_week, get_weekly_history, save_improvement_note)
from utils.auth import check_authentication
from utils.ui_components import apply_gradient_theme, show_fox_header
from utils.charts import create_energy_trend, create_task_energy_comparison, create_mood_matrix
import json
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Tổng kết tuần", page_icon="📊", layout="wide")
apply_gradient_theme()

if not check_authentication():
    st.warning("⚠️ Vui lòng đăng nhập trước!")
    st.stop()

username = st.session_state.username
init_database(username)
show_fox_header("📊 Tổng kết tuần")

week_start, week_end = get_current_week_range()
st.markdown(f"**Tuần:** {week_start} đến {week_end}")

# ================================================================
# BANNER LƯU TUẦN CŨ — chỉ hiện khi chưa lưu
# ================================================================
if is_new_week(username):
    last_monday = datetime.strptime(week_start, "%Y-%m-%d") - timedelta(days=7)
    last_sunday = last_monday + timedelta(days=6)

    history_check = get_weekly_history(username, 8)
    already_saved = (
        len(history_check) > 0 and
        last_monday.strftime('%Y-%m-%d') in history_check['week_start'].values
    )

    if not already_saved:
        st.warning("🎉 ĐÃ HẾT TUẦN! Hãy lưu tuần trước.")
        st.info(f"Tuần trước: {last_monday.strftime('%Y-%m-%d')} - {last_sunday.strftime('%Y-%m-%d')}")

        if st.button("📂 Lưu tuần cũ", type="primary", use_container_width=True):
            save_weekly_history(
                username,
                last_monday.strftime('%Y-%m-%d'),
                last_sunday.strftime('%Y-%m-%d'),
                pd.DataFrame()
            )
            st.success("✅ Đã lưu!")
            st.balloons()
            st.rerun()

        st.markdown("---")

# ================================================================
# DATA TUẦN HIỆN TẠI — get_week_data đã filter theo tuần rồi
# ================================================================
df = get_week_data(username)
days_tracked = len(df)

st.markdown(f"### Check-in: **{days_tracked}/7 ngày** {'✅' if days_tracked >= 6 else '💪'}")

if days_tracked < 3:
    st.warning(f"⚠️ Cần 3 ngày để phân tích. Hiện có {days_tracked}/3 ngày.")
    if st.button("📝 Check-in ngay", type="primary"):
        st.switch_page("pages/1_📝_Nhập_Liệu_Hàng_Ngày.py")

    st.markdown("---")
    st.subheader("📂 Lịch sử các tuần")
    history_df = get_weekly_history(username, 8)
    if len(history_df) > 0:
        for idx, row in history_df.iterrows():
            col_a, col_b, col_c = st.columns([2, 1, 1])
            with col_a:
                st.markdown(f"**{row['week_start']} - {row['week_end']}**")
            with col_b:
                st.metric("Check-in", f"{row['total_checkins']}/7")
            with col_c:
                st.metric("Năng lượng", f"{float(row['avg_energy']):.1f}/10")
            st.markdown("---")
    else:
        st.info("Chưa có lịch sử tuần nào được lưu.")
    st.stop()

st.success(f"✅ Đủ dữ liệu! ({days_tracked} ngày)")


# METRICS
df = df.reset_index(drop=True)
df['energy_level'] = pd.to_numeric(df['energy_level'], errors='coerce')
df['sleep_quality'] = pd.to_numeric(df['sleep_quality'], errors='coerce')
avg_energy = df['energy_level'].mean()  # mean() tự bỏ NaN

def _parse_tasks(x):
    if isinstance(x, list):
        return len(x)
    try:
        return len(json.loads(x))
    except Exception:
        return 0

df['task_count'] = df['tasks'].apply(_parse_tasks)
avg_tasks = df['task_count'].mean()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Năng lượng TB", f"{avg_energy:.1f}/10")
with col2:
    st.metric("Công việc TB", f"{avg_tasks:.1f} việc/ngày")
with col3:
    df_valid = df.dropna(subset=['energy_level'])
    if len(df_valid) > 0:
        best_day = df_valid.loc[df_valid['energy_level'].idxmax()]
        st.metric("Ngày tốt nhất", best_day['date'])
    else:
        st.metric("Ngày tốt nhất", "—")

st.markdown("---")

# BIỂU ĐỒ
st.subheader("📈 Biểu đồ phân tích tuần")
chart_tab1, chart_tab2, chart_tab3 = st.tabs([
    "⚡ Xu hướng năng lượng",
    "📋 Công việc vs Năng lượng",
    "🎯 Ma trận áp lực"
])
with chart_tab1:
    st.plotly_chart(create_energy_trend(df), use_container_width=True)
with chart_tab2:
    st.plotly_chart(create_task_energy_comparison(df), use_container_width=True)
with chart_tab3:
    st.plotly_chart(create_mood_matrix(df), use_container_width=True)

st.markdown("---")

# PATTERNS
st.subheader("⚠️ Quy luật phát hiện")
patterns = []
df_valid2 = df.dropna(subset=['energy_level'])
if len(df_valid2) > 0:
    worst_day = df_valid2.loc[df_valid2['energy_level'].idxmin()]
    if worst_day['energy_level'] < 5:
        patterns.append(f"⚠️ {worst_day['date']} là ngày thấp nhất ({worst_day['energy_level']}/10)")
low_sleep = df[df['sleep_quality'] <= 2]
if len(low_sleep) > 0:
    patterns.append(f"😴 {len(low_sleep)} ngày ngủ kém → Ảnh hưởng năng lượng")
high_tasks = df[df['task_count'] >= 8]
if len(high_tasks) > 0:
    patterns.append(f"📋 {len(high_tasks)} ngày quá nhiều việc (≥8 việc)")

if patterns:
    for p in patterns:
        st.markdown(f"- {p}")
else:
    st.info("✅ Không có quy luật tiêu cực!")

st.markdown("---")

# PROMPT TUẦN
st.subheader("🤖 Prompt AI tuần")
st.info(f"💡 Prompt tuần MẠNH HƠN prompt ngày vì có {days_tracked} ngày dữ liệu!")

from utils.prompt_builder import build_weekly_prompt
weekly_prompt = build_weekly_prompt(df, patterns)

if 'show_weekly_prompt' not in st.session_state:
    st.session_state.show_weekly_prompt = False

col_p1, col_p2 = st.columns(2)
with col_p1:
    btn_label = "🙈 Ẩn Prompt" if st.session_state.show_weekly_prompt else "👁️ Xem Prompt tuần"
    if st.button(btn_label, use_container_width=True, type="primary", key="btn_weekly_toggle"):
        st.session_state.show_weekly_prompt = not st.session_state.show_weekly_prompt
        st.rerun()
with col_p2:
    prompt_json = json.dumps(weekly_prompt)
    components.html(f"""
    <button id="copyweeklybtn" onclick="
        var text = {prompt_json};
        navigator.clipboard.writeText(text).then(function() {{
            document.getElementById('copyweeklybtn').innerText = '✅ Đã copy!';
            setTimeout(function() {{
                document.getElementById('copyweeklybtn').innerText = '📋 Copy Prompt tuần';
            }}, 2000);
        }}).catch(function() {{
            document.getElementById('copyweeklybtn').innerText = '❌ Lỗi, thử lại';
        }});
    " style="
        width:100%; padding:0.6rem 1rem;
        background:linear-gradient(135deg,#667eea,#764ba2);
        color:white; border:none; border-radius:10px;
        font-size:1rem; font-weight:600; cursor:pointer;
        font-family:sans-serif; line-height:1.6;
    ">📋 Copy Prompt tuần</button>
    """, height=50)

if st.session_state.show_weekly_prompt:
    st.code(weekly_prompt, language="markdown")

st.markdown("---")

# GHI CHÚ
st.subheader("📝 Ghi chú cải thiện")
with st.expander("Lưu lời khuyên cho tuần sau"):
    with st.form("weekly_note"):
        note_content = st.text_area(
            "AI khuyên gì cho tuần sau?",
            height=150,
            placeholder="VD: Nên ngủ đủ 7 tiếng, giảm công việc xuống 5-6 việc/ngày..."
        )
        note_type = st.radio("Áp dụng:", ["Tuần sau", "Dài hạn", "Quy luật"], horizontal=True)
        if st.form_submit_button("💾 Lưu", use_container_width=True):
            if note_content.strip():
                next_week = (datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
                if save_improvement_note(username, next_week, note_content, note_type):
                    st.success("✅ Đã lưu!")
                    st.balloons()
                else:
                    st.error("❌ Lỗi!")
            else:
                st.warning("⚠️ Nhập nội dung!")

st.markdown("---")

# LỊCH SỬ — CUỐI TRANG
st.subheader("📂 Lịch sử các tuần")
history_df = get_weekly_history(username, 8)
if len(history_df) > 0:
    for idx, row in history_df.iterrows():
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            st.markdown(f"**{row['week_start']} - {row['week_end']}**")
        with col_b:
            st.metric("Check-in", f"{row['total_checkins']}/7")
        with col_c:
            st.metric("Năng lượng", f"{float(row['avg_energy']):.1f}/10")
        st.markdown("---")
else:
    st.info("Chưa có lịch sử tuần nào được lưu.")

st.caption("💡 Hãy áp dụng lời khuyên tuần sau để cải thiện!")