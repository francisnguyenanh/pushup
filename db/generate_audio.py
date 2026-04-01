"""
Motivational audio generator for PushUp Trainer.
Creates synthesized sounds with ADSR envelopes, harmonics, and musical sequences.
Output: WAV-format data saved as .mp3 (browsers detect format from content).
"""
import wave, struct, math, os

SAMPLE_RATE = 44100

def clamp(v, lo=-32767, hi=32767):
    return int(max(lo, min(hi, v)))

def sine(freq, t):
    return math.sin(2 * math.pi * freq * t)

def adsr(i, total, attack_r=0.05, decay_r=0.1, sustain_level=0.75, release_r=0.2):
    """Return amplitude multiplier 0‥1 for sample i out of total."""
    a = int(total * attack_r)
    d = int(total * decay_r)
    r = int(total * release_r)
    s = total - a - d - r
    if i < a:
        return i / a if a else 1.0
    elif i < a + d:
        return 1.0 - (1.0 - sustain_level) * (i - a) / d
    elif i < a + d + s:
        return sustain_level
    else:
        rem = total - i
        return sustain_level * rem / r if r else 0.0

def write_wav(filename, frames):
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframesraw(bytes(frames))
    print(f"  → {filename}")

def note_frames(freq, duration_s, volume=0.7, harmonics=None,
                attack_r=0.05, decay_r=0.10, sustain=0.75, release_r=0.25):
    """Generate samples for one note."""
    harmonics = harmonics or [(1, 1.0), (2, 0.4), (3, 0.2)]
    n = int(SAMPLE_RATE * duration_s)
    frames = []
    for i in range(n):
        t = i / SAMPLE_RATE
        amp = adsr(i, n, attack_r, decay_r, sustain, release_r)
        val = sum(amplitude * sine(freq * h, t) for h, amplitude in harmonics)
        frames += struct.pack('<h', clamp(val * amp * volume * 32767))
    return frames

def sweep_frames(f0, f1, duration_s, volume=0.8,
                 attack_r=0.02, decay_r=0.08, sustain=0.65, release_r=0.3):
    """Frequency sweep from f0 to f1."""
    n = int(SAMPLE_RATE * duration_s)
    phase = 0.0
    frames = []
    for i in range(n):
        t = i / n                               # 0‥1
        freq = f0 + (f1 - f0) * t              # linear sweep
        phase += 2 * math.pi * freq / SAMPLE_RATE
        amp = adsr(i, n, attack_r, decay_r, sustain, release_r)
        # Rich harmonics: fundamental + 2nd + 3rd
        val = (math.sin(phase)
               + 0.35 * math.sin(2 * phase)
               + 0.15 * math.sin(3 * phase))
        frames += struct.pack('<h', clamp(val * amp * volume * 32767))
    return frames


def silence(duration_s):
    n = int(SAMPLE_RATE * duration_s)
    return [0] * (n * 2)   # 2 bytes per sample


out_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'audio')
os.makedirs(out_dir, exist_ok=True)

print("Generating motivational audio…")

# ── up.mp3 ───────────────────────────────────────────────────────────────────
# Single HIGH note: C6 (1046 Hz) — bright, sharp, victory punch
# Short attack, quick decay into sustain, clean release
frames_up = note_frames(
    1046.50, 0.35, volume=0.90,
    harmonics=[(1, 1.0), (2, 0.30), (3, 0.08)],   # bright but not harsh
    attack_r=0.01, decay_r=0.12, sustain=0.65, release_r=0.40
)
write_wav(os.path.join(out_dir, 'up.mp3'), frames_up)

# ── down.mp3 ─────────────────────────────────────────────────────────────────
# Single LOW note: C3 (130 Hz) — deep, heavy, "grind through it" feel
# Slower attack for weight, rich low harmonics for rumble
frames_down = note_frames(
    130.81, 0.45, volume=0.92,
    harmonics=[(1, 1.0), (2, 0.55), (3, 0.28), (4, 0.12)],  # thick, bassy
    attack_r=0.04, decay_r=0.10, sustain=0.70, release_r=0.35
)
write_wav(os.path.join(out_dir, 'down.mp3'), frames_down)

# ── rest.mp3 ─────────────────────────────────────────────────────────────────
# Victory chime: C5–E5–G5 arpeggio with slight reverb-tail
C5, E5, G5 = 523.25, 659.25, 783.99
frames_rest = (
    note_frames(C5, 0.18, volume=0.75, attack_r=0.01, release_r=0.40)
  + silence(0.04)
  + note_frames(E5, 0.18, volume=0.75, attack_r=0.01, release_r=0.40)
  + silence(0.04)
  + note_frames(G5, 0.35, volume=0.80, attack_r=0.01, decay_r=0.12,
                sustain=0.65, release_r=0.40)
)
write_wav(os.path.join(out_dir, 'rest.mp3'), frames_rest)

# ── done.mp3 ─────────────────────────────────────────────────────────────────
# Triumphant fanfare: G4 → C5 → E5 → G5 → C6 ascending with rich overtones
notes_fanfare = [
    (392.00, 0.15),   # G4
    (523.25, 0.15),   # C5
    (659.25, 0.15),   # E5
    (783.99, 0.15),   # G5
    (1046.50, 0.55),  # C6 — hold the top note
]
frames_done = []
for freq, dur in notes_fanfare:
    frames_done += note_frames(
        freq, dur, volume=0.82,
        harmonics=[(1, 1.0), (2, 0.45), (3, 0.22), (4, 0.10)],
        attack_r=0.02, decay_r=0.08, sustain=0.70, release_r=0.25
    )
    frames_done += silence(0.02)

write_wav(os.path.join(out_dir, 'done.mp3'), frames_done)

print("Done! ✅")
