import sqlite3
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'workout_log.db')

@dataclass
class WorkoutSession:
    mode_id: str
    sets_done: int
    reps_done: int
    duration_s: int
    completed: bool
    date: str = None
    id: int = None

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def save_session(session: WorkoutSession):
    date_str = session.date or datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO workout_sessions (date, mode_id, sets_done, reps_done, duration_s, completed)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (date_str, session.mode_id, session.sets_done, session.reps_done, session.duration_s, 1 if session.completed else 0))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_history(days=30):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get last 30 days of daily totals
    cursor.execute('''
        SELECT date, total_reps, session_count 
        FROM daily_totals 
        ORDER BY date DESC 
        LIMIT ?
    ''', (days,))
    rows = cursor.fetchall()
    conn.close()
    # reversed() needs a sequence; cursor.fetchall() returns list so this is fine,
    # but wrap explicitly to be safe.
    return [dict(row) for row in reversed(list(rows))]

def get_recent_sessions(limit=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM workout_sessions 
        ORDER BY id DESC 
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total reps all-time
    cursor.execute('SELECT SUM(reps_done) FROM workout_sessions')
    stats['total_reps'] = cursor.fetchone()[0] or 0
    
    # Total sessions
    cursor.execute('SELECT COUNT(*) FROM workout_sessions')
    stats['total_sessions'] = cursor.fetchone()[0] or 0
    
    # Best day (most reps)
    cursor.execute('SELECT MAX(total_reps) FROM daily_totals')
    row = cursor.fetchone()
    stats['best_day_reps'] = row[0] if row and row[0] is not None else 0
    
    # Current streak
    cursor.execute('SELECT date FROM daily_totals WHERE any_completed = 1 ORDER BY date DESC')
    dates = [row[0] for row in cursor.fetchall()]
    
    streak = 0
    if dates:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        last_date = datetime.strptime(dates[0], '%Y-%m-%d').date()
        
        if last_date == today or last_date == yesterday:
            streak = 1
            for i in range(len(dates) - 1):
                curr = datetime.strptime(dates[i], '%Y-%m-%d').date()
                prev = datetime.strptime(dates[i+1], '%Y-%m-%d').date()
                if (curr - prev).days == 1:
                    streak += 1
                else:
                    break
    
    stats['streak'] = streak
    conn.close()
    return stats
