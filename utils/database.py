"""
database.py
- LOCAL: USE_LOCAL = "true" trong secrets.toml → SQLite
- DEPLOY: DATABASE_URL trong secrets → Supabase
- SQLite dùng Row factory → truy cập bằng tên cột (như dict), không bị lệch index
- Tự detect và recreate DB nếu schema cũ
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import shutil




# ================================================================
# BACKEND
# ================================================================


def _use_local():
    try:
        import streamlit as st
        val = st.secrets.get("USE_LOCAL", "false")
        return str(val).lower() in ("true", "1", "yes")
    except Exception:
        return True




def _path(username):
    os.makedirs("data", exist_ok=True)
    return f"data/{username}.db"




def _sq(username):
    """SQLite connection với row_factory → kết quả trả về như dict"""
    conn = sqlite3.connect(_path(username))
    conn.row_factory = sqlite3.Row   # ← KEY FIX: truy cập bằng tên cột
    return conn




def _pg():
    import streamlit as st
    import psycopg2, psycopg2.extras
    return psycopg2.connect(
        st.secrets["DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor
    )




# ================================================================
# SCHEMA
# ================================================================


_SQLITE_DDL = [
    """CREATE TABLE IF NOT EXISTS daily_checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        date TEXT NOT NULL,
        mental_load TEXT,
        energy_level INTEGER,
        pressure_source TEXT,
        sleep_quality INTEGER,
        tasks TEXT,
        task_feeling TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(username, date))""",
    """CREATE TABLE IF NOT EXISTS task_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        checkin_date TEXT,
        task_name TEXT,
        estimated_time INTEGER,
        priority TEXT,
        task_type TEXT)""",
    """CREATE TABLE IF NOT EXISTS fixed_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        checkin_date TEXT,
        schedule_name TEXT,
        start_time TEXT,
        end_time TEXT)""",
    """CREATE TABLE IF NOT EXISTS weekly_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        week_start TEXT,
        week_end TEXT,
        total_checkins INTEGER,
        avg_energy REAL,
        data_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS improvement_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        week_start TEXT,
        note_content TEXT,
        note_type TEXT,
        applied INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS playbook (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        rule_title TEXT,
        trigger TEXT,
        action TEXT,
        tested_week TEXT,
        result TEXT,
        status TEXT DEFAULT 'testing',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
]


_PG_DDL = [s.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
           for s in _SQLITE_DDL]


_REQUIRED_COLS = {
    "daily_checkins":    ["username", "date", "mental_load", "energy_level",
                          "pressure_source", "sleep_quality", "tasks", "task_feeling"],
    "task_metadata":     ["username", "checkin_date", "task_name", "estimated_time",
                          "priority", "task_type"],
    "fixed_schedules":   ["username", "checkin_date", "schedule_name", "start_time", "end_time"],
    "weekly_history":    ["username", "week_start", "week_end", "total_checkins",
                          "avg_energy", "data_json"],
    "improvement_notes": ["username", "week_start", "note_content", "note_type", "applied"],
    "playbook":          ["username", "rule_title", "trigger", "action",
                          "tested_week", "result", "status"],
}




def _schema_ok(username):
    try:
        path = _path(username)
        if not os.path.exists(path):
            return True
        conn = sqlite3.connect(path)
        for table, required in _REQUIRED_COLS.items():
            exists = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()[0]
            if not exists:
                conn.close(); return False
            existing = {row[1].lower() for row in conn.execute(f"PRAGMA table_info({table})")}
            for col in required:
                if col not in existing:
                    conn.close(); return False
        conn.close(); return True
    except Exception:
        return False




def _recreate_db(username):
    path = _path(username)
    if os.path.exists(path):
        backup = path.replace(".db", f"_bak_{datetime.now().strftime('%H%M%S')}.db")
        try:
            shutil.copy2(path, backup)
        except Exception:
            pass
        try:
            os.remove(path)
        except Exception:
            try:
                os.rename(path, path + ".old")
            except Exception:
                pass
    conn = sqlite3.connect(path)
    for s in _SQLITE_DDL:
        conn.execute(s)
    conn.commit(); conn.close()




# ================================================================
# INIT
# ================================================================


def init_database(username):
    if _use_local():
        if not _schema_ok(username):
            _recreate_db(username)
        conn = _sq(username)
        for s in _SQLITE_DDL:
            conn.execute(s)
        conn.commit(); conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        for s in _PG_DDL:
            cur.execute(s)
        conn.commit(); cur.close(); conn.close()




# ================================================================
# CHECK-IN
# ================================================================


def save_checkin(username, data):
    tj = json.dumps(data['tasks'], ensure_ascii=False)
    if _use_local():
        conn = _sq(username)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO daily_checkins
                  (username,date,mental_load,energy_level,pressure_source,
                   sleep_quality,tasks,task_feeling)
                VALUES (?,?,?,?,?,?,?,?)
            """, (username, data['date'], data['mental_load'], data['energy_level'],
                  data['pressure_source'], data['sleep_quality'], tj, data['task_feeling']))
            conn.commit(); return True
        except Exception as e:
            print(f"save_checkin: {e}"); return False
        finally:
            conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO daily_checkins
                  (username,date,mental_load,energy_level,pressure_source,
                   sleep_quality,tasks,task_feeling)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (username,date) DO UPDATE SET
                  mental_load=EXCLUDED.mental_load,
                  energy_level=EXCLUDED.energy_level,
                  pressure_source=EXCLUDED.pressure_source,
                  sleep_quality=EXCLUDED.sleep_quality,
                  tasks=EXCLUDED.tasks,
                  task_feeling=EXCLUDED.task_feeling
            """, (username, data['date'], data['mental_load'], data['energy_level'],
                  data['pressure_source'], data['sleep_quality'], tj, data['task_feeling']))
            conn.commit(); return True
        except Exception as e:
            print(f"save_checkin pg: {e}"); return False
        finally:
            cur.close(); conn.close()




def get_checkin_today(username):
    today = datetime.now().strftime("%Y-%m-%d")
    if _use_local():
        conn = _sq(username)
        r = conn.execute(
            "SELECT * FROM daily_checkins WHERE username=? AND date=?",
            (username, today)).fetchone()
        conn.close()
        return dict(r) if r else None
    else:
        conn = _pg(); cur = conn.cursor()
        cur.execute("SELECT * FROM daily_checkins WHERE username=%s AND date=%s", (username, today))
        r = cur.fetchone(); cur.close(); conn.close()
        return dict(r) if r else None




def get_checkin_by_date(username, date):
    if _use_local():
        conn = _sq(username)
        r = conn.execute(
            "SELECT * FROM daily_checkins WHERE username=? AND date=?",
            (username, date)).fetchone()
        conn.close()
        return dict(r) if r else None
    else:
        conn = _pg(); cur = conn.cursor()
        cur.execute("SELECT * FROM daily_checkins WHERE username=%s AND date=%s", (username, date))
        r = cur.fetchone(); cur.close(); conn.close()
        return dict(r) if r else None




def get_week_data(username):
    if _use_local():
        conn = sqlite3.connect(_path(username))  # pandas không cần row_factory
        df = pd.read_sql_query(
            "SELECT * FROM daily_checkins WHERE username=? ORDER BY date DESC LIMIT 7",
            conn, params=(username,))
        conn.close(); return df
    else:
        conn = _pg()
        df = pd.read_sql_query(
            "SELECT * FROM daily_checkins WHERE username=%s ORDER BY date DESC LIMIT 7",
            conn, params=(username,))
        conn.close(); return df




# ================================================================
# TASK METADATA
# ================================================================


def save_task_metadata(username, date, tasks_meta):
    if _use_local():
        conn = _sq(username)
        try:
            conn.execute("DELETE FROM task_metadata WHERE username=? AND checkin_date=?", (username, date))
            for t in tasks_meta:
                conn.execute("""
                    INSERT INTO task_metadata
                      (username,checkin_date,task_name,estimated_time,priority,task_type)
                    VALUES (?,?,?,?,?,?)
                """, (username, date, t['name'], t['estimated_time'], t['priority'], t['task_type']))
            conn.commit(); return True
        except Exception as e:
            print(f"save_task_metadata: {e}"); return False
        finally:
            conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        try:
            cur.execute("DELETE FROM task_metadata WHERE username=%s AND checkin_date=%s", (username, date))
            for t in tasks_meta:
                cur.execute("""
                    INSERT INTO task_metadata
                      (username,checkin_date,task_name,estimated_time,priority,task_type)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (username, date, t['name'], t['estimated_time'], t['priority'], t['task_type']))
            conn.commit(); return True
        except Exception as e:
            print(f"save_task_metadata pg: {e}"); return False
        finally:
            cur.close(); conn.close()




def get_task_metadata(username, date):
    if _use_local():
        conn = sqlite3.connect(_path(username))
        df = pd.read_sql_query(
            "SELECT * FROM task_metadata WHERE username=? AND checkin_date=? ORDER BY id",
            conn, params=(username, date))
        conn.close(); return df
    else:
        conn = _pg()
        df = pd.read_sql_query(
            "SELECT * FROM task_metadata WHERE username=%s AND checkin_date=%s ORDER BY id",
            conn, params=(username, date))
        conn.close(); return df




# ================================================================
# FIXED SCHEDULE
# ================================================================


def save_fixed_schedule(username, date, schedules):
    if _use_local():
        conn = _sq(username)
        try:
            conn.execute("DELETE FROM fixed_schedules WHERE username=? AND checkin_date=?", (username, date))
            for s in schedules:
                conn.execute("""
                    INSERT INTO fixed_schedules
                      (username,checkin_date,schedule_name,start_time,end_time)
                    VALUES (?,?,?,?,?)
                """, (username, date, s['name'], s['start'], s['end']))
            conn.commit(); return True
        except Exception as e:
            print(f"save_fixed_schedule: {e}"); return False
        finally:
            conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        try:
            cur.execute("DELETE FROM fixed_schedules WHERE username=%s AND checkin_date=%s", (username, date))
            for s in schedules:
                cur.execute("""
                    INSERT INTO fixed_schedules
                      (username,checkin_date,schedule_name,start_time,end_time)
                    VALUES (%s,%s,%s,%s,%s)
                """, (username, date, s['name'], s['start'], s['end']))
            conn.commit(); return True
        except Exception as e:
            print(f"save_fixed_schedule pg: {e}"); return False
        finally:
            cur.close(); conn.close()




def get_fixed_schedule(username, date):
    if _use_local():
        conn = sqlite3.connect(_path(username))
        df = pd.read_sql_query(
            "SELECT * FROM fixed_schedules WHERE username=? AND checkin_date=? ORDER BY start_time",
            conn, params=(username, date))
        conn.close(); return df
    else:
        conn = _pg()
        df = pd.read_sql_query(
            "SELECT * FROM fixed_schedules WHERE username=%s AND checkin_date=%s ORDER BY start_time",
            conn, params=(username, date))
        conn.close(); return df




# ================================================================
# WEEKLY HISTORY
# ================================================================


def get_current_week_range():
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")




def save_weekly_history(username, week_start, week_end, df):
    total = len(df)
    avg_e = df['energy_level'].mean() if total > 0 else 0
    dj = df.to_json(orient='records', force_ascii=False)
    if _use_local():
        conn = _sq(username)
        try:
            conn.execute("""
                INSERT INTO weekly_history
                  (username,week_start,week_end,total_checkins,avg_energy,data_json)
                VALUES (?,?,?,?,?,?)
            """, (username, week_start, week_end, total, avg_e, dj))
            count = conn.execute(
                "SELECT COUNT(*) FROM weekly_history WHERE username=?", (username,)
            ).fetchone()[0]
            if count > 8:
                conn.execute("""
                    DELETE FROM weekly_history WHERE username=? AND id IN (
                        SELECT id FROM weekly_history WHERE username=?
                        ORDER BY created_at ASC LIMIT ?)
                """, (username, username, count - 8))
            conn.commit(); return True
        except Exception as e:
            print(f"save_weekly_history: {e}"); return False
        finally:
            conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO weekly_history
                  (username,week_start,week_end,total_checkins,avg_energy,data_json)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (username, week_start, week_end, total, avg_e, dj))
            cur.execute("SELECT COUNT(*) as c FROM weekly_history WHERE username=%s", (username,))
            count = cur.fetchone()['c']
            if count > 8:
                cur.execute("""
                    DELETE FROM weekly_history WHERE username=%s AND id IN (
                        SELECT id FROM weekly_history WHERE username=%s
                        ORDER BY created_at ASC LIMIT %s)
                """, (username, username, count - 8))
            conn.commit(); return True
        except Exception as e:
            print(f"save_weekly_history pg: {e}"); return False
        finally:
            cur.close(); conn.close()




def get_weekly_history(username, limit=8):
    if _use_local():
        conn = sqlite3.connect(_path(username))
        df = pd.read_sql_query(
            "SELECT * FROM weekly_history WHERE username=? ORDER BY created_at DESC LIMIT ?",
            conn, params=(username, limit))
        conn.close(); return df
    else:
        conn = _pg()
        df = pd.read_sql_query(
            "SELECT * FROM weekly_history WHERE username=%s ORDER BY created_at DESC LIMIT %s",
            conn, params=(username, limit))
        conn.close(); return df




def is_new_week(username):
    week_start, _ = get_current_week_range()
    if _use_local():
        conn = _sq(username)
        count = conn.execute(
            "SELECT COUNT(*) FROM weekly_history WHERE username=? AND week_start=?",
            (username, week_start)).fetchone()[0]
        conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as c FROM weekly_history WHERE username=%s AND week_start=%s",
            (username, week_start))
        count = cur.fetchone()['c']; cur.close(); conn.close()
    return count == 0 and datetime.now().weekday() == 0




# ================================================================
# IMPROVEMENT NOTES
# ================================================================


def save_improvement_note(username, week_start, note_content, note_type="tuần_sau"):
    if _use_local():
        conn = _sq(username)
        try:
            conn.execute("""
                INSERT INTO improvement_notes
                  (username,week_start,note_content,note_type,applied)
                VALUES (?,?,?,?,0)
            """, (username, week_start, note_content, note_type))
            conn.commit(); return True
        except Exception as e:
            print(f"save_improvement_note: {e}"); return False
        finally:
            conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO improvement_notes
                  (username,week_start,note_content,note_type,applied)
                VALUES (%s,%s,%s,%s,0)
            """, (username, week_start, note_content, note_type))
            conn.commit(); return True
        except Exception as e:
            print(f"save_improvement_note pg: {e}"); return False
        finally:
            cur.close(); conn.close()




def get_improvement_notes(username, week_start=None):
    if _use_local():
        conn = sqlite3.connect(_path(username))
        if week_start:
            df = pd.read_sql_query(
                "SELECT * FROM improvement_notes WHERE username=? AND week_start=? ORDER BY created_at DESC",
                conn, params=(username, week_start))
        else:
            df = pd.read_sql_query(
                "SELECT * FROM improvement_notes WHERE username=? ORDER BY created_at DESC",
                conn, params=(username,))
        conn.close(); return df
    else:
        conn = _pg()
        if week_start:
            df = pd.read_sql_query(
                "SELECT * FROM improvement_notes WHERE username=%s AND week_start=%s ORDER BY created_at DESC",
                conn, params=(username, week_start))
        else:
            df = pd.read_sql_query(
                "SELECT * FROM improvement_notes WHERE username=%s ORDER BY created_at DESC",
                conn, params=(username,))
        conn.close(); return df




def mark_note_applied(username, note_id):
    if _use_local():
        conn = _sq(username)
        try:
            conn.execute("UPDATE improvement_notes SET applied=1 WHERE id=? AND username=?", (note_id, username))
            conn.commit(); return True
        except Exception as e:
            print(f"mark_note_applied: {e}"); return False
        finally:
            conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        try:
            cur.execute("UPDATE improvement_notes SET applied=1 WHERE id=%s AND username=%s", (note_id, username))
            conn.commit(); return True
        except Exception as e:
            print(f"mark_note_applied pg: {e}"); return False
        finally:
            cur.close(); conn.close()




def delete_improvement_note(username, note_id):
    if _use_local():
        conn = _sq(username)
        try:
            conn.execute("DELETE FROM improvement_notes WHERE id=? AND username=?", (note_id, username))
            conn.commit(); return True
        except Exception as e:
            print(f"delete_improvement_note: {e}"); return False
        finally:
            conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        try:
            cur.execute("DELETE FROM improvement_notes WHERE id=%s AND username=%s", (note_id, username))
            conn.commit(); return True
        except Exception as e:
            print(f"delete_improvement_note pg: {e}"); return False
        finally:
            cur.close(); conn.close()




# ================================================================
# PLAYBOOK
# ================================================================


def save_playbook_rule(username, rule_data):
    if _use_local():
        conn = _sq(username)
        try:
            conn.execute("""
                INSERT INTO playbook
                  (username,rule_title,trigger,action,tested_week,result,status)
                VALUES (?,?,?,?,?,?,?)
            """, (username, rule_data['rule_title'], rule_data['trigger'],
                  rule_data['action'], rule_data['tested_week'],
                  rule_data['result'], rule_data['status']))
            conn.commit(); return True
        except Exception as e:
            print(f"save_playbook_rule: {e}"); return False
        finally:
            conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO playbook
                  (username,rule_title,trigger,action,tested_week,result,status)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (username, rule_data['rule_title'], rule_data['trigger'],
                  rule_data['action'], rule_data['tested_week'],
                  rule_data['result'], rule_data['status']))
            conn.commit(); return True
        except Exception as e:
            print(f"save_playbook_rule pg: {e}"); return False
        finally:
            cur.close(); conn.close()




def get_all_playbook_rules(username):
    if _use_local():
        conn = sqlite3.connect(_path(username))
        df = pd.read_sql_query(
            "SELECT * FROM playbook WHERE username=? ORDER BY created_at DESC",
            conn, params=(username,))
        conn.close(); return df
    else:
        conn = _pg()
        df = pd.read_sql_query(
            "SELECT * FROM playbook WHERE username=%s ORDER BY created_at DESC",
            conn, params=(username,))
        conn.close(); return df




def update_rule_status(username, rule_id, new_status, new_result=None):
    if _use_local():
        conn = _sq(username)
        try:
            if new_result:
                conn.execute("UPDATE playbook SET status=?,result=? WHERE id=? AND username=?",
                             (new_status, new_result, rule_id, username))
            else:
                conn.execute("UPDATE playbook SET status=? WHERE id=? AND username=?",
                             (new_status, rule_id, username))
            conn.commit(); return True
        except Exception as e:
            print(f"update_rule_status: {e}"); return False
        finally:
            conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        try:
            if new_result:
                cur.execute("UPDATE playbook SET status=%s,result=%s WHERE id=%s AND username=%s",
                            (new_status, new_result, rule_id, username))
            else:
                cur.execute("UPDATE playbook SET status=%s WHERE id=%s AND username=%s",
                            (new_status, rule_id, username))
            conn.commit(); return True
        except Exception as e:
            print(f"update_rule_status pg: {e}"); return False
        finally:
            cur.close(); conn.close()




def delete_playbook_rule(username, rule_id):
    if _use_local():
        conn = _sq(username)
        try:
            conn.execute("DELETE FROM playbook WHERE id=? AND username=?", (rule_id, username))
            conn.commit(); return True
        except Exception as e:
            print(f"delete_playbook_rule: {e}"); return False
        finally:
            conn.close()
    else:
        conn = _pg(); cur = conn.cursor()
        try:
            cur.execute("DELETE FROM playbook WHERE id=%s AND username=%s", (rule_id, username))
            conn.commit(); return True
        except Exception as e:
            print(f"delete_playbook_rule pg: {e}"); return False
        finally:
            cur.close(); conn.close()
