import wave
import struct
import math
import os

def generate_beep(filename, frequency=440, duration=0.5, volume=0.5):
    sample_rate = 44100
    num_samples = int(duration * sample_rate)
    
    # Create the wave file
    wav_file = wave.open(filename, 'w')
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 2 bytes per sample
    wav_file.setframerate(sample_rate)
    
    for i in range(num_samples):
        # Generate a sine wave sample
        value = int(volume * 32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
        # Pack into binary format
        data = struct.pack('<h', value)
        wav_file.writeframesraw(data)
    
    wav_file.close()

audio_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'audio')
os.makedirs(audio_dir, exist_ok=True)

# Generate four different beeps
generate_beep(os.path.join(audio_dir, 'up.mp3'), frequency=880)   # Higher pitch for UP
generate_beep(os.path.join(audio_dir, 'down.mp3'), frequency=440) # Lower pitch for DOWN
generate_beep(os.path.join(audio_dir, 'rest.mp3'), frequency=660) # Mid pitch for REST
generate_beep(os.path.join(audio_dir, 'done.mp3'), frequency=1100, duration=1.0) # Long high pitch for DONE

print(f"Generated placeholder audio in {audio_dir}")
