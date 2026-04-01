import json
import os
from flask import Flask, render_template, request, jsonify
from models.workout import save_session, get_history, get_recent_sessions, get_stats, WorkoutSession
from db.init_db import init_db

app = Flask(__name__)

# Auto-create DB if it doesn't exist yet
DB_PATH = os.path.join(os.path.dirname(__file__), 'workout_log.db')
if not os.path.exists(DB_PATH):
    init_db()

# Load workout modes
MODES_PATH = os.path.join(os.path.dirname(__file__), 'config', 'modes.json')
with open(MODES_PATH, 'r', encoding='utf-8') as f:
    WORKOUT_MODES = json.load(f)['modes']

@app.route('/')
def index():
    return render_template('index.html', modes=WORKOUT_MODES)

@app.route('/workout')
def workout():
    mode_id = request.args.get('mode_id')
    mode = next((m for m in WORKOUT_MODES if m['id'] == mode_id), None)
    if not mode:
        return "Mode not found", 404
        
    # Always work on a shallow copy so we never mutate the shared WORKOUT_MODES list
    mode = mode.copy()

    # Handle custom mode field overrides
    if mode_id == 'custom':
        try:
            mode['sets']         = int(request.args.get('sets', 3))
            mode['reps_per_set'] = int(request.args.get('reps_per_set', 10))
            mode['rest_seconds'] = int(request.args.get('rest_seconds', 60))
        except (ValueError, TypeError):
            return "Invalid custom parameters", 400

    # rep_pace_s can be overridden by query param for ALL modes
    if 'rep_pace_s' in request.args:
        try:
            pace = float(request.args.get('rep_pace_s'))
            mode['rep_pace_s'] = max(1.0, min(6.0, pace))   # clamp 1–6 s/rep
        except (ValueError, TypeError):
            return "Invalid rep_pace_s", 400

    # Ensure a safe default if still None (shouldn't normally happen)
    if not mode.get('rep_pace_s'):
        mode['rep_pace_s'] = 2.5

    return render_template('workout.html', config=mode)

@app.route('/api/session/save', methods=['POST'])
def api_save_session():
    data = request.json
    if not data:
        return jsonify({'ok': False, 'error': 'No JSON body'}), 400
    required = ('mode_id', 'sets_done', 'reps_done', 'duration_s', 'completed')
    missing  = [k for k in required if k not in data]
    if missing:
        return jsonify({'ok': False, 'error': f'Missing fields: {missing}'}), 400
    session = WorkoutSession(
        mode_id=data['mode_id'],
        sets_done=int(data['sets_done']),
        reps_done=int(data['reps_done']),
        duration_s=int(data['duration_s']),
        completed=bool(data['completed'])
    )
    session_id = save_session(session)
    return jsonify({'ok': True, 'session_id': session_id})

@app.route('/history')
def history():
    stats = get_stats()
    recent = get_recent_sessions()
    return render_template('history.html', stats=stats, recent=recent)

@app.route('/api/history')
def api_history():
    history_data = get_history(30)
    return jsonify(history_data)

if __name__ == '__main__':
    app.run(debug=True, port=5020)
