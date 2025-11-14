import os
import sys
import time
import wave
import pyaudio
import whisper
import numpy as np
import torch

# -------------------------------
# 0. Base directory (safe for .exe and .py)
# -------------------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS  # PyInstaller temp folder
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# Use absolute paths for consistency
RECORD_DIR = os.path.join(BASE_DIR, "Recorded_Audio")
TRANSCRIPT_DIR = os.path.join(BASE_DIR, "Transcriptions")
os.makedirs(RECORD_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

# -------------------------------
# PyAudio config
# -------------------------------
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024



SILENCE_THRESHOLD = 0.01  # audio level considered as silence
SILENCE_MAX_DURATION = 6.0  # seconds



# -------------------------------
# Load Whisper model
# -------------------------------
print("🔊 Loading Whisper model...")
model = whisper.load_model("base")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"✅ Whisper model ready on {device.upper()}")

# -------------------------------
# 1. Dynamic Recording (Press & Hold)
# -------------------------------
def record_audio():
    """Record audio dynamically until key release, save WAV in RECORD_DIR and return path."""
    import keyboard
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("🎙️ Recording... release 'T' to stop.")
    frames = []

    while keyboard.is_pressed('t'):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    timestamp = int(time.time())
    filename = os.path.join(RECORD_DIR, f"audio_{timestamp}.wav")
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print(f"💾 Saved audio to {filename}")
    return filename


# -------------------------------
# 2. Normal transcription (batch)
# -------------------------------
def transcribe_audio(file_path, language=None):
    """Transcribe an audio file using Whisper."""
    kwargs = {"fp16": False}
    if language:
        kwargs["language"] = language

    file_path = os.path.abspath(file_path)
    result = model.transcribe(file_path, **kwargs)
    text = result.get("text", "").strip()

    # Safe deletion with retries
    try:
        abs_record_dir = os.path.abspath(RECORD_DIR)
        if file_path.startswith(abs_record_dir + os.sep):
            for _ in range(5):
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"🗑️ Deleted temporary file: {file_path}")
                    break
                except PermissionError:
                    time.sleep(0.2)
            else:
                print(f"⚠️ Could not delete (still in use): {file_path}")
    except Exception as e:
        print(f"⚠️ Warning: could not delete {file_path}: {e}")

    return text


# -------------------------------
# 3. Realtime transcription (near-live) — with stop flag
# -------------------------------
_realtime_active = False  # <-- flag to control background execution

def realtime_transcription(update_callback=None,
                           chunk_duration=2.0,
                           rolling_duration=5.0,
                           language=None,
                           silence_timeout=6.0,
                           silence_threshold=0.01):
    import queue
    import sounddevice as sd
    import time
    global _realtime_active

    _realtime_active = True  # start realtime session
    q = queue.Queue()
    RATE_LOCAL = RATE
    CHUNK_SIZE = int(RATE_LOCAL * chunk_duration)
    MAX_BUFFER = int(RATE_LOCAL * rolling_duration)
    last_speech_time = time.time()

    def audio_callback(indata, frames, time_info, status):
        if _realtime_active:
            q.put(indata.copy())

    kwargs = {"fp16": False}
    if language:
        kwargs["language"] = language

    with sd.InputStream(samplerate=RATE_LOCAL, channels=1, dtype="int16", callback=audio_callback):
        audio_buffer = np.zeros(0, dtype=np.int16)
        try:
            while _realtime_active:
                try:
                    data = q.get(timeout=0.5)
                    audio_buffer = np.concatenate((audio_buffer, data.flatten()))
                except queue.Empty:
                    continue

                # keep only last rolling_duration seconds
                if len(audio_buffer) > MAX_BUFFER:
                    audio_buffer = audio_buffer[-MAX_BUFFER:]

                # silence detection
                rms = np.sqrt(np.mean(audio_buffer.astype(np.float32)**2)) / 32768.0
                if rms > silence_threshold:
                    last_speech_time = time.time()
                elif time.time() - last_speech_time > silence_timeout:
                    print("\n🛑 Auto-stopping due to silence.")
                    _realtime_active = False
                    break

                # process in chunk_duration increments
                while len(audio_buffer) >= CHUNK_SIZE and _realtime_active:
                    chunk = audio_buffer[:CHUNK_SIZE]
                    audio_buffer = audio_buffer[CHUNK_SIZE:]
                    audio_np = chunk.astype(np.float32)/32768.0
                    result = model.transcribe(audio_np, **kwargs)
                    new_text = result.get("text","").strip()
                    if new_text and update_callback:
                        update_callback(new_text+" ")

        finally:
            _realtime_active = False
            print("\n🛑 Realtime transcription ended.")

def stop_realtime_transcription():
    """Stops realtime transcription safely."""
    global _realtime_active
    if _realtime_active:
        _realtime_active = False
        print("🛑 Stopping realtime transcription...")
    else:
        print("⚠️ Realtime transcription not running.")


# -------------------------------
# 4. Save Transcription
# -------------------------------
def save_transcription(text):
    timestamp = int(time.time())
    filename = os.path.join(TRANSCRIPT_DIR, f"transcription_{timestamp}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"💾 Saved transcription: {filename}")
    return filename
