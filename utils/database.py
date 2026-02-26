import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime, timedelta
import json

# ===== KẾT NỐI DATABASE =====

def get_connection():
    """Kết nối tới Supabase PostgreSQL"""
    return psycopg2.connect(
        st.secrets["DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor
    )

def _query_to_df(conn, query, params=()):
    """Helper: chạy query và trả về DataFrame đúng cách với psycopg2"""
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    if rows:
        return pd.DataFrame(rows, columns=cols)
    return pd.DataFrame(columns=cols)


def init_database(username):
    """Khởi tạo database với tất cả bảng cần thiết"""
    conn = get_connection()
    cur = conn.cursor()

    # Bảng check-in hàng ngày
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_checkins (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            date TEXT NOT NULL,
            mental_load TEXT,
            energy_level INTEGER,
            pressure_source TEXT,
            sleep_quality INTEGER,
            tasks TEXT,
            task_feeling TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, date)
        )
    """)

    # Bảng metadata tasks
    cur.execute("""
        CREATE TABLE IF NOT EXISTS task_metadata (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            checkin_date TEXT,
            task_name TEXT,
            estimated_time INTEGER,
            priority TEXT,
            task_type TEXT
        )
    """)

    # Bảng lịch cố định
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fixed_schedules (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            checkin_date TEXT,
            schedule_name TEXT,
            start_time TEXT,
            end_time TEXT
        )
    """)

    # Bảng lịch sử tuần
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weekly_history (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            week_start TEXT,
            week_end TEXT,
            total_checkins INTEGER,
            avg_energy REAL,
            data_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bảng ghi chú cải thiện
    cur.execute("""
        CREATE TABLE IF NOT EXISTS improvement_notes (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            week_start TEXT,
            note_content TEXT,
            note_type TEXT,
            applied INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bảng playbook
    cur.execute("""
        CREATE TABLE IF NOT EXISTS playbook (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            rule_title TEXT,
            trigger TEXT,
            action TEXT,
            tested_week TEXT,
            result TEXT,
            status TEXT DEFAULT 'testing',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

# ===== CHECK-IN FUNCTIONS =====

def save_checkin(username, data):
    """Lưu check-in hàng ngày"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO daily_checkins 
            (username, date, mental_load, energy_level, pressure_source, 
             sleep_quality, tasks, task_feeling)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (username, date) DO UPDATE SET
                mental_load = EXCLUDED.mental_load,
                energy_level = EXCLUDED.energy_level,
                pressure_source = EXCLUDED.pressure_source,
                sleep_quality = EXCLUDED.sleep_quality,
                tasks = EXCLUDED.tasks,
                task_feeling = EXCLUDED.task_feeling
        """, (
            username,
            data['date'],
            data['mental_load'],
            data['energy_level'],
            data['pressure_source'],
            data['sleep_quality'],
            json.dumps(data['tasks'], ensure_ascii=False),
            data['task_feeling']
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi save_checkin: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_checkin_today(username):
    """Lấy check-in hôm nay"""
    conn = get_connection()
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute(
        "SELECT * FROM daily_checkins WHERE username = %s AND date = %s",
        (username, today)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def get_checkin_by_date(username, date):
    """Lấy check-in theo ngày cụ thể"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM daily_checkins WHERE username = %s AND date = %s",
        (username, date)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def get_week_data(username):
    """Lấy data tuần hiện tại theo đúng khoảng ngày thứ 2 - chủ nhật"""
    week_start, week_end = get_current_week_range()
    conn = get_connection()
    query = """
        SELECT * FROM daily_checkins 
        WHERE username = %s
        AND date >= %s
        AND date <= %s
        ORDER BY date ASC
    """
    df = _query_to_df(conn, query, (username, week_start, week_end))
    conn.close()
    return df

# ===== TASK METADATA FUNCTIONS =====

def save_task_metadata(username, date, tasks_meta):
    """Lưu metadata của tasks"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM task_metadata WHERE username = %s AND checkin_date = %s",
            (username, date)
        )
        for task in tasks_meta:
            cur.execute("""
                INSERT INTO task_metadata 
                (username, checkin_date, task_name, estimated_time, priority, task_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                username, date,
                task['name'], task['estimated_time'],
                task['priority'], task['task_type']
            ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi save_task_metadata: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_task_metadata(username, date):
    """Lấy metadata tasks của 1 ngày"""
    conn = get_connection()
    query = """
        SELECT * FROM task_metadata 
        WHERE username = %s AND checkin_date = %s
        ORDER BY id
    """
    df = _query_to_df(conn, query, (username, date))
    conn.close()
    return df

# ===== FIXED SCHEDULE FUNCTIONS =====

def save_fixed_schedule(username, date, schedules):
    """Lưu lịch cố định"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM fixed_schedules WHERE username = %s AND checkin_date = %s",
            (username, date)
        )
        for schedule in schedules:
            cur.execute("""
                INSERT INTO fixed_schedules 
                (username, checkin_date, schedule_name, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                username, date,
                schedule['name'], schedule['start'], schedule['end']
            ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi save_fixed_schedule: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_fixed_schedule(username, date):
    """Lấy lịch cố định của 1 ngày"""
    conn = get_connection()
    query = """
        SELECT * FROM fixed_schedules 
        WHERE username = %s AND checkin_date = %s
        ORDER BY start_time
    """
    df = _query_to_df(conn, query, (username, date))
    conn.close()
    return df

# ===== WEEKLY HISTORY FUNCTIONS =====

def save_weekly_history(username, week_start, week_end, df):
    """Lưu lịch sử tuần (chỉ giữ 8 tuần gần nhất)"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        total_checkins = len(df)
        avg_energy = df['energy_level'].mean() if total_checkins > 0 else 0

        cur.execute("""
            INSERT INTO weekly_history 
            (username, week_start, week_end, total_checkins, avg_energy, data_json)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            username, week_start, week_end,
            total_checkins, avg_energy,
            df.to_json(orient='records', force_ascii=False)
        ))

        # Xóa tuần cũ nếu > 8 tuần
        cur.execute(
            "SELECT COUNT(*) FROM weekly_history WHERE username = %s",
            (username,)
        )
        count = cur.fetchone()['count']
        if count > 8:
            cur.execute("""
                DELETE FROM weekly_history 
                WHERE username = %s AND id IN (
                    SELECT id FROM weekly_history 
                    WHERE username = %s
                    ORDER BY created_at ASC 
                    LIMIT %s
                )
            """, (username, username, count - 8))

        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi save_weekly_history: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_weekly_history(username, limit=8):
    """Lấy lịch sử các tuần"""
    conn = get_connection()
    query = """
        SELECT * FROM weekly_history 
        WHERE username = %s
        ORDER BY created_at DESC 
        LIMIT %s
    """
    df = _query_to_df(conn, query, (username, limit))
    conn.close()
    return df

def get_current_week_range():
    """Lấy ngày đầu và cuối tuần hiện tại"""
    today = datetime.now()
    weekday = today.weekday()
    week_start = today - timedelta(days=weekday)
    week_end = week_start + timedelta(days=6)
    return week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")

def is_new_week(username):
    """Kiểm tra xem đã sang tuần mới chưa"""
    week_start, _ = get_current_week_range()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM weekly_history 
        WHERE username = %s AND week_start = %s
    """, (username, week_start))
    count = cur.fetchone()['count']
    cur.close()
    conn.close()
    return count == 0 and datetime.now().weekday() == 0

# ===== IMPROVEMENT NOTES FUNCTIONS =====

def save_improvement_note(username, week_start, note_content, note_type="tuần_sau"):
    """Lưu ghi chú cải thiện"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO improvement_notes 
            (username, week_start, note_content, note_type, applied)
            VALUES (%s, %s, %s, %s, 0)
        """, (username, week_start, note_content, note_type))
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi save_improvement_note: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_improvement_notes(username, week_start=None):
    """Lấy ghi chú cải thiện"""
    conn = get_connection()
    if week_start:
        query = """
            SELECT * FROM improvement_notes 
            WHERE username = %s AND week_start = %s
            ORDER BY created_at DESC
        """
        df = _query_to_df(conn, query, (username, week_start))
    else:
        query = """
            SELECT * FROM improvement_notes 
            WHERE username = %s
            ORDER BY created_at DESC
        """
        df = _query_to_df(conn, query, (username,))
    conn.close()
    return df

def mark_note_applied(username, note_id):
    """Đánh dấu ghi chú đã áp dụng"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE improvement_notes SET applied = 1 WHERE id = %s AND username = %s",
            (note_id, username)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi mark_note_applied: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def delete_improvement_note(username, note_id):
    """Xóa ghi chú"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM improvement_notes WHERE id = %s AND username = %s",
            (note_id, username)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi delete_improvement_note: {e}")
        return False
    finally:
        cur.close()
        conn.close()

# ===== PLAYBOOK FUNCTIONS =====

def save_playbook_rule(username, rule_data):
    """Lưu quy luật vào playbook"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO playbook 
            (username, rule_title, trigger, action, tested_week, result, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            username,
            rule_data['rule_title'],
            rule_data['trigger'],
            rule_data['action'],
            rule_data['tested_week'],
            rule_data['result'],
            rule_data['status']
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi save_playbook_rule: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_all_playbook_rules(username):
    """Lấy tất cả quy luật"""
    conn = get_connection()
    query = """
        SELECT * FROM playbook 
        WHERE username = %s
        ORDER BY created_at DESC
    """
    df = _query_to_df(conn, query, (username,))
    conn.close()
    return df

def update_rule_status(username, rule_id, new_status, new_result=None):
    """Cập nhật trạng thái quy luật"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if new_result:
            cur.execute("""
                UPDATE playbook SET status = %s, result = %s
                WHERE id = %s AND username = %s
            """, (new_status, new_result, rule_id, username))
        else:
            cur.execute("""
                UPDATE playbook SET status = %s
                WHERE id = %s AND username = %s
            """, (new_status, rule_id, username))
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi update_rule_status: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def delete_playbook_rule(username, rule_id):
    """Xóa quy luật"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM playbook WHERE id = %s AND username = %s",
            (rule_id, username)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi delete_playbook_rule: {e}")
        return False
    finally:
        cur.close()
        conn.close()