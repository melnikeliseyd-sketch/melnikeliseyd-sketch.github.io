import os
import json
import queue
import webbrowser
import pyautogui
import sounddevice as sd
import soundfile as sf
import vosk
import subprocess
import urllib.parse
from dotenv import load_dotenv
import requests

load_dotenv()

# ================== НАСТРОЙКИ ==================
MODEL_PATH = "model"
SAMPLE_RATE = 16000

# ================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==================
def set_volume(percent):
    for _ in range(50):
        pyautogui.press("volumedown")
    for _ in range(percent // 2):
        pyautogui.press("volumeup")
    return "Громкость установлена", "phrases/Громкость установлена.wav"

def open_url(url, message):
    webbrowser.open(url.strip())
    return message, "phrases/Запрос выполнен сэр.wav"

def launch_app(path, app_name):
    try:
        subprocess.Popen(path, shell=True)
        return f"Запускаю {app_name}", "phrases/Запрос выполнен сэр.wav"
    except Exception as e:
        return "Не удалось запустить", "phrases/Ошибка.wav"

def search_web(query):
    if not query.strip():
        return "Что именно искать, сэр?", "phrases/Ошибка.wav"
    encoded_query = urllib.parse.quote_plus(query.strip())
    url = f"https://www.google.com/search?q=  {encoded_query}"
    webbrowser.open(url)
    return f"Ищу: {query.strip()}", "phrases/Запрос выполнен сэр.wav"

def play_wav(file_path):
    """Воспроизводит .wav файл"""
    try:
        data, sr = sf.read(file_path, dtype='float32')
        sd.play(data, sr)
        sd.wait()
    except Exception as e:
        print(f"Ошибка воспроизведения {file_path}: {e}")
        # Fallback: если файла нет, говорим через pyttsx3
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say("Готово.")
            engine.runAndWait()
        except:
            pass

# ================== КОМАНДЫ ==================
ACTIONS = {
    ("джарвис", "здесь", "живой", "ты тут", "жарвис", "дарвис", "джаз"): lambda: (
        "Всегда к вашим услугам, сэр.", "phrases/К вашим услугам сэр.wav"
    ),
    ("максимум", "макс", "100", "звук_макс", "громкость_макс"): lambda: set_volume(100),
    ("половина", "50", "средний", "громкость_50"): lambda: set_volume(50),
    ("минимум", "0", "тихо", "без_звука"): lambda: set_volume(0),
    ("аниме", "анимешка"): lambda: open_url("https://animego.org  ", "Да сэр.wav"),
    ("музыка", "музон", "фон", "включи музыку"): lambda: open_url(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ  ", "Загружаю сэр.wav"
    ),
    ("ютуб", "youtube"): lambda: open_url("https://youtube.com  ", "Загружаю сэр.wav"),
    ("гугл", "google"): lambda: open_url("https://google.com  ", "Загружаю сэр.wav"),
    ("найди", "поищи", "загугли", "search"): lambda cmd: search_web(
        " ".join(cmd.split()[1:]) if len(cmd.split()) > 1 else ""
    ),
    ("телеграм", "telegram", "тг"): lambda: launch_app(
        r"C:\Users\111\AppData\Roaming\Telegram Desktop\Telegram.exe", "Telegram"
    ),
    ("опера", "opera", "браузер опера," "оперу",): lambda: launch_app(
        r"C:\Users\111\AppData\Local\Programs\Opera GX\opera.exe", "браузер Opera"
    ),
    ('тим', 'стим', "steam"): lambda: launch_app(
        r"K:\steam\steam.exe", "Steam"
    ),
    ("кс", "кэс", "кесс", "кэсс", "кс2", "кэс2", "кесс2", "кэсс2", "каэс", "кас", "counter-strike", "cs2", "контра", "контр"): lambda: launch_app(
        r'"K:\Game\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\cs2.exe"', "Counter-Strike 2"
    ),
    ("дота", "dota", "dota2"): lambda: launch_app(
        r"steam://rungameid/570", "Dota 2"
    ),
    ("майнкрафт", "minecraft", "майн", "ll"): lambda: launch_app(
        r"C:\Users\111\Desktop\LL.exe", "Minecraft"
    ),
    ("закрой", "закрыть", "крест", "выход_окно"): lambda: (
        (pyautogui.hotkey("alt", "f4"), "Окно закрыто."), "phrases/Запрос выполнен сэр.wav"
    ),
    ("блокировка", "заблокируй", "спящий"): lambda: (
        (subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True), "Система заблокирована."), "phrases/Запрос выполнен сэр.wav"
    ),
    ("перезагрузка", "рестарт"): lambda: (
        (subprocess.run("shutdown /r /t 5", shell=True), "Перезагрузка через 5 секунд."), "phrases/Запрос выполнен сэр.wav"
    ),
    ("выключение", "выключи_пк"): lambda: (
        (subprocess.run("shutdown /s /t 5", shell=True), "Выключение через 5 секунд."), "phrases/Запрос выполнен сэр.wav"
    ),
    ("пока", "выход", "стоп", "молчать", "отключись"): lambda: ("exit", None),
}

# ================== РАСПОЗНАВАНИЕ РЕЧИ ==================
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
    # Приветствие при старте
    play_wav("phrases/Джарвис - приветствие.wav")

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

                # Активация только после "джарвис"
                JARVIS_KEYWORDS = ("джарвис", "жарвис", "дарвис", "джаз", "джой", "джордж", "джа")
                if not any(kw in text for kw in JARVIS_KEYWORDS):
                    continue
                command_text = text.replace("джарвис", "", 1).strip()
                if not command_text:
                    play_wav("phrases/Джарвис - приветствие.wav")
                    continue

                handled = False
                for keys, action in ACTIONS.items():
                    if any(k in command_text for k in keys):
                        response_text, wav_path = action()
                        if response_text == "exit":
                            play_wav("phrases/Поздралвяю сэр.wav")  # или любой другой прощальный файл
                            return
                        print(f"J.A.R.V.I.S.: {response_text}")
                        if wav_path:
                            play_wav(wav_path)
                        handled = True
                        break

                if not handled:
                    play_wav("phrases/Ошибка.wav")

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    main()
