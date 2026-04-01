import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'workout_log.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workout_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,             -- ISO format: YYYY-MM-DD
            mode_id     TEXT NOT NULL,
            sets_done   INTEGER NOT NULL,
            reps_done   INTEGER NOT NULL,          -- total reps this session
            duration_s  INTEGER NOT NULL,          -- total workout seconds
            completed   INTEGER NOT NULL DEFAULT 0 -- 1 if finished all sets
        )
    ''')

    # Create view for daily totals
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS daily_totals AS
        SELECT date,
               SUM(reps_done)  AS total_reps,
               COUNT(*)        AS session_count,
               MAX(completed)  AS any_completed
        FROM workout_sessions
        GROUP BY date
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == '__main__':
    init_db()
