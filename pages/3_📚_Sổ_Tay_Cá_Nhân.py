import streamlit as st
from datetime import datetime, timedelta
from utils.database import (get_all_playbook_rules, save_playbook_rule, update_rule_status,
                           delete_playbook_rule, get_improvement_notes, mark_note_applied,
                           delete_improvement_note, get_current_week_range, init_database)
from utils.auth import check_authentication
from utils.ui_components import apply_gradient_theme, show_fox_header

st.set_page_config(
    page_title="Sổ tay cá nhân",
    page_icon="📚",
    layout="wide"
)

apply_gradient_theme()

if not check_authentication():
    st.warning("⚠️ Vui lòng đăng nhập trước!")
    st.stop()

username = st.session_state.username
init_database(username)

show_fox_header("📚 Sổ tay cá nhân")

st.markdown("Nơi lưu trữ **quy luật đã học** và **ghi chú cải thiện** từ AI")


# ===== HELPER FUNCTIONS — phải khai báo TRƯỚC khi dùng =====

def get_status_emoji(status):
    """Emoji theo trạng thái"""
    emoji_map = {
        'Đã xác nhận': '✅',
        'Đang thử': '🧪',
        'Thất bại': '❌'
    }
    return emoji_map.get(status, '📌')


def get_week_label(note_week_start, current_week_start, next_week_start):
    """Phân loại ghi chú theo tuần"""
    if note_week_start >= next_week_start:
        return 'Tuần tới'
    elif note_week_start >= current_week_start:
        return 'Tuần này'
    else:
        return 'Lịch sử'


# ===== 2 TABS =====
tab1, tab2 = st.tabs(["📖 Quy luật đã học", "📝 Ghi chú cải thiện tuần sau"])

# ===== TAB 1: QUY LUẬT ĐÃ HỌC =====
with tab1:
    st.subheader("📖 Quy luật đã học từ kinh nghiệm")
    
    st.info("💡 Đây là các quy luật bạn tự rút ra hoặc học được từ AI, đã được test và xác nhận hiệu quả!")
    
    # Nút thêm quy luật mới
    if st.button("➕ Thêm quy luật mới", type="primary"):
        st.session_state.show_add_rule = True
    
    # Form thêm quy luật
    if st.session_state.get('show_add_rule', False):
        with st.form("add_rule_form"):
            st.markdown("### Thêm quy luật mới")
            
            rule_title = st.text_input(
                "Tiêu đề quy luật:",
                placeholder="VD: Nếu ngủ >7 tiếng → Năng lượng +2"
            )
            
            trigger = st.text_area(
                "Điều kiện (Trigger):",
                placeholder="VD: Khi tôi ngủ đủ 7 tiếng trở lên",
                height=100
            )
            
            action = st.text_area(
                "Hành động (Action):",
                placeholder="VD: Năng lượng tăng thêm 2 điểm, công việc hoàn thành nhanh hơn",
                height=100
            )
            
            tested_week = st.text_input(
                "Tuần thử nghiệm:",
                placeholder="VD: 12-18/02/2026"
            )
            
            result = st.text_area(
                "Kết quả thử nghiệm:",
                placeholder="VD: Thử 4/7 ngày, năng lượng TB tăng từ 5.2 lên 7.0",
                height=100
            )
            
            status = st.selectbox(
                "Trạng thái:",
                ["Đang thử", "Đã xác nhận", "Thất bại"]
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit_rule = st.form_submit_button("💾 Lưu quy luật", use_container_width=True)
            
            with col2:
                cancel_rule = st.form_submit_button("❌ Hủy", use_container_width=True)
            
            if submit_rule:
                if rule_title and trigger and action:
                    rule_data = {
                        'rule_title': rule_title,
                        'trigger': trigger,
                        'action': action,
                        'tested_week': tested_week,
                        'result': result,
                        'status': status
                    }
                    
                    if save_playbook_rule(username, rule_data):
                        st.success("✅ Đã lưu quy luật!")
                        st.session_state.show_add_rule = False
                        st.rerun()
                    else:
                        st.error("❌ Có lỗi khi lưu!")
                else:
                    st.warning("⚠️ Vui lòng điền đầy đủ thông tin!")
            
            if cancel_rule:
                st.session_state.show_add_rule = False
                st.rerun()
    
    st.markdown("---")
    
    # Hiển thị danh sách quy luật
    df_playbook = get_all_playbook_rules(username)
    
    if len(df_playbook) == 0:
        st.info("Bạn chưa có quy luật nào. Hãy thêm quy luật đầu tiên!")
    else:
        # Filter theo status
        status_filter = st.selectbox(
            "Lọc theo trạng thái:",
            ["Tất cả", "Đã xác nhận", "Đang thử", "Thất bại"]
        )
        
        if status_filter != "Tất cả":
            df_filtered = df_playbook[df_playbook['status'] == status_filter]
        else:
            df_filtered = df_playbook
        
        st.markdown(f"**Tổng: {len(df_filtered)} quy luật**")
        
        for idx, row in df_filtered.iterrows():
            with st.expander(f"{get_status_emoji(row['status'])} {row['rule_title']}", expanded=False):
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    st.markdown(f"**📍 Điều kiện:** {row['trigger']}")
                    st.markdown(f"**✨ Hành động:** {row['action']}")
                    st.markdown(f"**📅 Tuần thử:** {row['tested_week']}")
                    st.markdown(f"**📊 Kết quả:** {row['result']}")
                    st.markdown(f"**🏷️ Trạng thái:** {row['status']}")
                
                with col_b:
                    if row['status'] == 'Đang thử':
                        if st.button("✅ Xác nhận", key=f"verify_{row['id']}", use_container_width=True):
                            update_rule_status(username, row['id'], 'Đã xác nhận')
                            st.rerun()
                        
                        if st.button("❌ Thất bại", key=f"fail_{row['id']}", use_container_width=True):
                            update_rule_status(username, row['id'], 'Thất bại')
                            st.rerun()
                    
                    if st.button("🗑️ Xóa", key=f"delete_{row['id']}", use_container_width=True):
                        delete_playbook_rule(username, row['id'])
                        st.success("✅ Đã xóa!")
                        st.rerun()

# ===== TAB 2: GHI CHÚ CẢI THIỆN =====
with tab2:
    st.subheader("📝 Ghi chú cải thiện tuần sau")
    
    st.info("💡 Những lời khuyên từ AI để áp dụng vào tuần tới!")
    
    # Lấy thông tin tuần
    week_start, week_end = get_current_week_range()
    next_week_start = (datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Nút thêm ghi chú thủ công
    if st.button("➕ Thêm ghi chú mới", key="btn_add_note"):
        st.session_state.show_add_note = True

    if st.session_state.get('show_add_note', False):
        with st.form("manual_note_form"):
            st.markdown("### Thêm ghi chú mới")
            manual_note = st.text_area("Nội dung ghi chú:", height=100,
                                       placeholder="VD: AI khuyên dời Ôn Anh sang Thứ 3...")
            manual_type = st.radio("Loại:", ["Hôm nay", "Tuần sau", "Quy luật"], horizontal=True)
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                submit_note = st.form_submit_button("💾 Lưu", use_container_width=True)
            with col_n2:
                cancel_note = st.form_submit_button("❌ Hủy", use_container_width=True)

            if submit_note and manual_note.strip():
                from utils.database import save_improvement_note
                if save_improvement_note(username, week_start, manual_note.strip(), manual_type):
                    st.success("✅ Đã lưu!")
                    st.session_state.show_add_note = False
                    st.rerun()
                else:
                    st.error("❌ Lỗi khi lưu!")
            if cancel_note:
                st.session_state.show_add_note = False
                st.rerun()

    st.markdown("---")

    # Lấy ghi chú
    df_notes = get_improvement_notes(username)
    
    if len(df_notes) == 0:
        st.info("Chưa có ghi chú nào. Hãy thêm ghi chú sau khi dùng AI prompt!")
    else:
        # Nhóm theo tuần
        df_notes['week_label'] = df_notes['week_start'].apply(
            lambda x: get_week_label(x, week_start, next_week_start)
        )
        
        # ── Ghi chú tuần tới ──
        notes_next_week = df_notes[df_notes['week_label'] == 'Tuần tới']
        
        if len(notes_next_week) > 0:
            st.markdown(f"### 💡 Ghi chú cho tuần tới")
            st.caption(f"Tuần từ {next_week_start} trở đi")
            
            for idx, note in notes_next_week.iterrows():
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        applied_icon = "✅" if note['applied'] == 1 else "⏳"
                        st.markdown(f"{applied_icon} **{note['note_content']}**")
                        st.caption(f"Ngày ghi: {note['created_at'][:10]} | Loại: {note['note_type']}")
                    
                    with col2:
                        if note['applied'] == 0:
                            if st.button("✅ Đã áp dụng", key=f"apply_{note['id']}", use_container_width=True):
                                mark_note_applied(username, note['id'])
                                st.rerun()
                        
                        if st.button("🗑️", key=f"del_{note['id']}", use_container_width=True):
                            delete_improvement_note(username, note['id'])
                            st.rerun()
                    
                    st.markdown("---")
        
        # ── Ghi chú tuần này ──
        notes_this_week = df_notes[df_notes['week_label'] == 'Tuần này']
        
        if len(notes_this_week) > 0:
            st.markdown(f"### 📋 Ghi chú tuần này")
            st.caption(f"Tuần {week_start} đến {week_end}")
            
            for idx, note in notes_this_week.iterrows():
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        applied_icon = "✅" if note['applied'] == 1 else "⏳"
                        st.markdown(f"{applied_icon} **{note['note_content']}**")
                        st.caption(f"Ngày ghi: {note['created_at'][:10]} | Loại: {note['note_type']}")
                        
                        if note['applied'] == 1:
                            st.success("✅ Hiệu quả! Có thể lưu thành quy luật")
                    
                    with col2:
                        if note['applied'] == 1:
                            if st.button("💾 Lưu thành Quy luật", key=f"save_rule_{note['id']}", use_container_width=True):
                                rule_data = {
                                    'rule_title': note['note_content'][:50] + ("..." if len(note['note_content']) > 50 else ""),
                                    'trigger': "Từ ghi chú AI",
                                    'action': note['note_content'],
                                    'tested_week': week_start,
                                    'result': "Đã áp dụng và hiệu quả",
                                    'status': 'Đã xác nhận'
                                }
                                save_playbook_rule(username, rule_data)
                                delete_improvement_note(username, note['id'])
                                st.success("✅ Đã chuyển thành quy luật!")
                                st.rerun()
                        else:
                            if st.button("✅ Đã áp dụng", key=f"apply2_{note['id']}", use_container_width=True):
                                mark_note_applied(username, note['id'])
                                st.rerun()
                        
                        if st.button("🗑️", key=f"del2_{note['id']}", use_container_width=True):
                            delete_improvement_note(username, note['id'])
                            st.rerun()
                    
                    st.markdown("---")
        
        # ── Lịch sử (tuần trước) ──
        notes_past = df_notes[df_notes['week_label'] == 'Lịch sử']
        
        if len(notes_past) > 0:
            with st.expander(f"📂 Lịch sử ghi chú ({len(notes_past)} ghi chú)"):
                for idx, note in notes_past.iterrows():
                    applied_icon = "✅" if note['applied'] == 1 else "⏳"
                    st.markdown(f"{applied_icon} {note['note_content']}")
                    st.caption(f"Tuần {note['week_start']} | {note['created_at'][:10]}")
                    st.markdown("---")

st.markdown("---")
st.caption("💡 Tip: Ghi chú những gì AI khuyên, áp dụng, và chuyển thành quy luật nếu hiệu quả!")