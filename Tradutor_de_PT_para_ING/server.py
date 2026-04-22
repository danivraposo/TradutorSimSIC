import os
import webbrowser
from pathlib import Path
import whisper
import pyaudio
import numpy as np
import torch
from deep_translator import GoogleTranslator
from flask import Flask, Response, render_template, request, jsonify
import threading
import time
import queue

app = Flask(__name__)

def configure_ffmpeg_path():
    ffmpeg_dir = os.getenv("FFMPEG_DIR")
    if not ffmpeg_dir:
        bundled_dir = Path(__file__).resolve().parent.parent / "ffmpeg" / "bin"
        if bundled_dir.exists():
            ffmpeg_dir = str(bundled_dir)

    if not ffmpeg_dir:
        default_windows_dir = Path(r"C:\ffmpeg\bin")
        if default_windows_dir.exists():
            ffmpeg_dir = str(default_windows_dir)

    if ffmpeg_dir and Path(ffmpeg_dir).exists():
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")


configure_ffmpeg_path()

WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto").lower()

if WHISPER_DEVICE == "auto":
    WHISPER_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

default_model = "small" if WHISPER_DEVICE == "cuda" else "base"
WHISPER_MODEL = os.getenv("WHISPER_MODEL", default_model)

def load_whisper_model():
    requested_device = WHISPER_DEVICE
    try:
        if requested_device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA indisponivel no ambiente atual.")

        loaded_model = whisper.load_model(WHISPER_MODEL).to(requested_device)
        print(f"Whisper carregado: modelo={WHISPER_MODEL}, device={requested_device}")
        return loaded_model, requested_device
    except Exception as e:
        if requested_device != "cpu":
            print(f"Falha ao iniciar em {requested_device}: {e}")
            print("A usar fallback para CPU.")
            loaded_model = whisper.load_model(WHISPER_MODEL).to("cpu")
            print(f"Whisper carregado: modelo={WHISPER_MODEL}, device=cpu")
            return loaded_model, "cpu"
        raise


model, ACTIVE_DEVICE = load_whisper_model()

translated_queue = queue.Queue(maxsize=100)
translation_history = []
pause_translations = False  # Controle de pausa

# Áudio config
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 300
SILENCE_SECONDS = 0.9
MAX_SEGMENT_SECONDS = 3.0

audio_frames_queue = queue.Queue(maxsize=8)

# Frases proibidas
banned_phrases = [
    "subtitles by the amara.org community",
    "amara.org community",
    "subtitles provided by",
    "this video was transcribed by"
]

def is_banned(text):
    lower = text.lower()
    return any(phrase in lower for phrase in banned_phrases)

def is_similar(a, b):
    return a.strip().lower() == b.strip().lower()


def queue_put_with_drop(q, item):
    try:
        q.put_nowait(item)
    except queue.Full:
        try:
            q.get_nowait()
        except queue.Empty:
            pass
        q.put_nowait(item)


def list_input_devices(audio):
    try:
        print("Dispositivos de input disponiveis:")
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if int(info.get("maxInputChannels", 0)) > 0:
                print(f"  [{i}] {info.get('name')} (in={int(info.get('maxInputChannels', 0))})")
    except Exception as e:
        print(f"Nao foi possivel listar dispositivos de audio: {e}")

def audio_capture_loop():
    while True:
        audio = None
        stream = None
        try:
            audio = pyaudio.PyAudio()
            list_input_devices(audio)
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
            )
            print("Captura iniciada. A ouvir em português...")

            frames = []
            silence_duration = 0

            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_np = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_np.astype(np.float64) ** 2))
                frames.append(data)

                if rms < SILENCE_THRESHOLD:
                    silence_duration += CHUNK / RATE
                else:
                    silence_duration = 0

                if silence_duration >= SILENCE_SECONDS:
                    if frames:
                        queue_put_with_drop(audio_frames_queue, frames.copy())
                        frames = []
                    silence_duration = 0

                if len(frames) >= int(RATE / CHUNK * MAX_SEGMENT_SECONDS):
                    queue_put_with_drop(audio_frames_queue, frames.copy())
                    frames = []
        except Exception as e:
            print(f"Erro na captura de audio: {e}")
            print("A tentar reiniciar captura em 2 segundos...")
            time.sleep(2)
        finally:
            try:
                if stream is not None:
                    stream.stop_stream()
                    stream.close()
            except Exception:
                pass
            try:
                if audio is not None:
                    audio.terminate()
            except Exception:
                pass

def audio_processing_loop():
    last_transcribed = ""
    last_translated = ""
    print("Processamento de audio iniciado.")

    while True:
        frames = audio_frames_queue.get()
        if not frames:
            continue

        try:
            print("A processar em português...")
            audio_int16 = np.frombuffer(b"".join(frames), dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0

            result = model.transcribe(
                audio_float32,
                language="pt",
                fp16=(ACTIVE_DEVICE == "cuda"),
                temperature=0.0,
                condition_on_previous_text=False,
            )
            text = result["text"].strip()

            if not text or is_similar(text, last_transcribed) or is_banned(text):
                continue

            last_transcribed = text
            translated = GoogleTranslator(source='pt', target='en').translate(text)

            if not is_similar(translated, last_translated):
                queue_put_with_drop(translated_queue, translated)
                last_translated = translated

        except Exception as e:
            print("Erro:", e)

def stream_translations():
    while True:
        if pause_translations:
            time.sleep(0.2)
            continue

        translated = translated_queue.get()
        translation_history.append(translated)
        full_text = "<br>".join(translation_history[-100:])
        yield f"data: {full_text}\n\n"
        time.sleep(0.1)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stream")
def stream():
    return Response(stream_translations(), mimetype='text/event-stream')

@app.route("/toggle_pause", methods=["POST"])
def toggle_pause():
    global pause_translations
    action = request.json.get("action", "")
    
    if action == "pause":
        pause_translations = True
        return jsonify({"status": "paused"})
    
    elif action == "resume":
        pause_translations = False
        return jsonify({"status": "resumed"})
    
    return jsonify({"status": "invalid action"}), 400

@app.route("/clear", methods=["POST"])
def clear_translations():
    global translation_history
    translation_history.clear()
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    threading.Thread(target=audio_capture_loop, daemon=True).start()
    threading.Thread(target=audio_processing_loop, daemon=True).start()

    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:5000")

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, threaded=True, host="0.0.0.0", port=5000)
