/**
 * WorkoutController — pure JS state machine
 * States: IDLE → COUNTDOWN → REP_UP → REP_DOWN → REST → DONE
 */
class WorkoutController {
    constructor(config, callbacks) {
        this.config = {
            id: config.id,
            sets: parseInt(config.sets),
            reps_per_set: parseInt(config.reps_per_set),
            rest_seconds: parseInt(config.rest_seconds)
        };

        this.callbacks = {
            onStateChange:  callbacks.onStateChange  || (() => {}),
            onRepComplete:  callbacks.onRepComplete  || (() => {}),
            onSetComplete:  callbacks.onSetComplete  || (() => {}),
            onCountdown:    callbacks.onCountdown    || (() => {}),
            onRestTick:     callbacks.onRestTick     || (() => {}),
            onDone:         callbacks.onDone         || (() => {})
        };

        this.state        = 'IDLE';
        this.currentSet   = 1;
        this.currentRep   = 0;
        this.totalReps    = 0;
        this.startTime    = null;
        this.duration     = 0;

        // Pause support
        this.isPaused       = false;
        this.timerId        = null;
        this.remainingMs    = 0;
        this.phaseStartTime = null;

        // Countdown state
        this._countdownValue = 3;

        // REST tick state
        this._restRemaining = 0;
        this._restTickTimer = null;

        // Preload audio
        this.sounds = {
            up:   new Audio('/static/audio/up.mp3'),
            down: new Audio('/static/audio/down.mp3'),
            rest: new Audio('/static/audio/rest.mp3'),
            done: new Audio('/static/audio/done.mp3'),
        };
    }

    // ─── Public API ───────────────────────────────────────────────────────────

    start() {
        this.startTime = Date.now();
        this._startCountdown(3);
    }

    pause() {
        if (this.isPaused || this.state === 'DONE' || this.state === 'IDLE') return;

        this.isPaused = true;
        clearTimeout(this.timerId);
        clearTimeout(this._restTickTimer);

        const elapsed   = Date.now() - this.phaseStartTime;
        this.remainingMs = Math.max(0, this.remainingMs - elapsed);

        this.callbacks.onStateChange('PAUSED', {
            originalState: this.state,
            remainingMs:   this.remainingMs
        });
    }

    resume() {
        if (!this.isPaused) return;
        this.isPaused = false;
        this.phaseStartTime = Date.now();

        // Restart the main phase timer
        this.timerId = setTimeout(() => this.nextPhase(), this.remainingMs);

        // If we were in REST, restart the per-second tick too
        if (this.state === 'REST') {
            this._scheduleRestTick(Math.ceil(this.remainingMs / 1000));
        }

        this.callbacks.onStateChange(this.state, {
            remainingMs: this.remainingMs,
            isResume:    true,
            set:         this.currentSet,
            rep:         this.currentRep,
            totalReps:   this.totalReps,
            durationMs:  this.remainingMs
        });
    }

    abort() {
        clearTimeout(this.timerId);
        clearTimeout(this._restTickTimer);
        this.state = 'IDLE';
    }

    // ─── Internal ─────────────────────────────────────────────────────────────

    _startCountdown(value) {
        this._countdownValue = value;
        this.state           = 'COUNTDOWN';
        this.remainingMs     = 1000;
        this.phaseStartTime  = Date.now();

        this.callbacks.onStateChange('COUNTDOWN', {
            countdown:  value,
            durationMs: 1000
        });

        this.timerId = setTimeout(() => {
            if (this.isPaused) return;
            if (this._countdownValue > 1) {
                this._startCountdown(this._countdownValue - 1);
            } else {
                this.transitionTo('REP_UP', 1250);
            }
        }, 1000);
    }

    transitionTo(newState, durationMs) {
        this.state          = newState;
        this.remainingMs    = durationMs;
        this.phaseStartTime = Date.now();

        // Sounds
        if (newState === 'REP_UP')   this.playSound('up');
        if (newState === 'REP_DOWN') this.playSound('down');
        if (newState === 'REST')     { this.playSound('rest'); this._scheduleRestTick(this.config.rest_seconds); }
        if (newState === 'DONE')     this.playSound('done');

        this.callbacks.onStateChange(newState, {
            durationMs,
            set:       this.currentSet,
            rep:       this.currentRep,
            totalReps: this.totalReps
        });

        this.timerId = setTimeout(() => this.nextPhase(), durationMs);
    }

    _scheduleRestTick(secondsLeft) {
        clearTimeout(this._restTickTimer);
        if (secondsLeft <= 0) return;
        this._restRemaining = secondsLeft;
        this.callbacks.onRestTick(secondsLeft);
        if (secondsLeft > 1) {
            this._restTickTimer = setTimeout(() => {
                if (!this.isPaused) this._scheduleRestTick(secondsLeft - 1);
            }, 1000);
        }
    }

    nextPhase() {
        if (this.isPaused) return;
        clearTimeout(this._restTickTimer);

        switch (this.state) {
            case 'COUNTDOWN':
                // handled inside _startCountdown
                break;

            case 'REP_UP':
                this.transitionTo('REP_DOWN', 1250);
                break;

            case 'REP_DOWN': {
                this.currentRep++;
                this.totalReps++;
                this.callbacks.onRepComplete(this.currentRep, this.currentSet, this.totalReps);

                if (this.currentRep < this.config.reps_per_set) {
                    // More reps in this set
                    this.transitionTo('REP_UP', 1250);
                } else if (this.currentSet < this.config.sets) {
                    // Set completed, move to REST
                    this.callbacks.onSetComplete(this.currentSet, this.config.rest_seconds);
                    this.transitionTo('REST', this.config.rest_seconds * 1000);
                } else {
                    // All sets done
                    this.finish();
                }
                break;
            }

            case 'REST':
                this.currentSet++;
                this.currentRep = 0;
                this.transitionTo('REP_UP', 1250);
                break;
        }
    }

    finish() {
        this.state    = 'DONE';
        this.duration = Math.floor((Date.now() - this.startTime) / 1000);

        this.callbacks.onStateChange('DONE', {
            totalReps:  this.totalReps,
            duration:   this.duration,
            setsDone:   this.currentSet   // ← send accurate sets done
        });

        this.callbacks.onDone(this.totalReps, this.duration, this.currentSet);
    }

    playSound(key) {
        const snd = this.sounds[key];
        if (!snd) return;
        snd.currentTime = 0;
        snd.play().catch(e => console.warn('Audio blocked:', e));
    }
}

window.WorkoutController = WorkoutController;
