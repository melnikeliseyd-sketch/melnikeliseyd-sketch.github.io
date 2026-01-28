import os
import asyncio
import json
import queue
import time
import webbrowser
import pyautogui
import requests
import sounddevice as sd
import soundfile as sf
import io
import vosk
from dotenv import load_dotenv
load_dotenv()

# ================== НАСТРОЙКИ ==================
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise RuntimeError("Ошибка: установите переменную окружения ELEVENLABS_API_KEY")

VOICE_ID = "EXAVITQu4vr4xnSDxMaL"      # Dmitri — отлично читает по-русски
MODEL_ID = "eleven_multilingual_v2"   # Поддерживает русский

MODEL_PATH = "model"                  # Путь к модели Vosk (должна быть скачана)
SAMPLE_RATE = 16000
OLLAMA_MODEL = "phi3"

# ================== КОМАНДЫ ==================
def set_volume(percent):
    for _ in range(50):
        pyautogui.press("volumedown")
    for _ in range(percent // 2):
        pyautogui.press("volumeup")
    return f"Громкость установлена на {percent} процентов."

def open_url(url, message):
    webbrowser.open(url)
    return message

COMMANDS = {
    ("джарвис", "ты здесь", "живой"): lambda: "Всегда к вашим услугам, сэр.",
    ("звук на 100", "громкость максимум"): lambda: set_volume(100),
    ("звук на 50", "громкость 50"): lambda: set_volume(50),
    ("аниме", "включи аниме"): lambda: open_url("https://animego.org", "Открываю AnimeGO."),
    ("музыка", "фоновая музыка"): lambda: open_url(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "Запускаю фоновую музыку."
    ),
    ("закрой окно", "закрой"): lambda: (pyautogui.hotkey("alt", "f4"), "Окно закрыто.")[1],
    ("пока", "выход", "стоп"): lambda: "exit",
}

# ================== ОЗВУЧКА ЧЕРЕЗ ELEVENLABS ==================
def speak(text: str):
    print(f"J.A.R.V.I.S.: {text}")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.85
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        # Воспроизведение без сохранения файла
        audio_stream = io.BytesIO(response.content)
        data, sr = sf.read(audio_stream, dtype='float32')
        sd.play(data, sr)
        sd.wait()
    except Exception as e:
        print("Ошибка ElevenLabs:", e)
        # Fallback через pyttsx3
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say("Голосовой движок недоступен.")
            engine.runAndWait()
        except:
            pass

# ================== ЗАПРОС К OLLAMA ==================
def ask_ollama(prompt):
    try:
        import ollama
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — J.A.R.V.I.S., умный, краткий и вежливый голосовой помощник на русском языке. "
                        "Отвечай коротко, по делу, без лишних объяснений."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            timeout=120
        )
        return response['message']['content'].strip()
    except Exception as e:
        return "Извините, ИИ временно недоступен."

# ================== РАСПОЗНАВАНИЕ РЕЧИ (VOSK) ==================
def create_listener():
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError("Модель Vosk не найдена! Скачайте её в папку 'model'.")
    model = vosk.Model(MODEL_PATH)
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        q.put(bytes(indata))

    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=callback
    )
    return stream, recognizer, q

# ================== ОСНОВНОЙ ЦИКЛ ==================
def main():
    speak("Джарвис активирован.")

    stream, recognizer, q = create_listener()

    with stream:
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower().strip()
                if not text:
                    continue

                print("Вы сказали:", text)

                # === 1. Проверка встроенных команд ===
                handled = False
                for keys, action in COMMANDS.items():
                    if any(k in text for k in keys):
                        response = action()
                        if response == "exit":
                            speak("До свидания, сэр.")
                            return
                        speak(response)
                        handled = True
                        break

                # === 2. Если команда не найдена — спрашиваем Ollama ===
                if not handled:
                    speak("Обращаюсь к ИИ...")
                    ai_response = ask_ollama(text)
                    speak(ai_response)

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    main()