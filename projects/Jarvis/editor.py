import customtkinter as ctk
import json
import os
import subprocess
import sys
import psutil
from tkinter import filedialog, messagebox
PID_FILE = "jarvis.pid"
CONFIG_FILE = "config.json"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ================= CONFIG =================

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "activation_keywords": ["джарвис", "жарвис", "jarvis"],
        "commands": []
    }

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)

# ================= JARVIS =================

def jarvis_running():
    if not os.path.exists(PID_FILE):
        return False

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        return psutil.pid_exists(pid)
    except:
        return False


# ================= MAIN WINDOW =================

class JarvisEditor(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("J.A.R.V.I.S — Центр управления")
        self.geometry("1100x700")
        self.config_data = load_config()

        self.build_ui()
        self.load_commands()
        self.update_buttons()

    def build_ui(self):

        # HEADER
        header = ctk.CTkFrame(self, height=60)
        header.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(header, text="J.A.R.V.I.S", font=("Segoe UI", 28, "bold")).pack(side="left", padx=20)
        ctk.CTkLabel(header, text="Редактор команд", font=("Segoe UI", 16)).pack(side="left")

        # Activation
        act = ctk.CTkFrame(self)
        act.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(act, text="Ключевые слова активации (через запятую)").pack(anchor="w", padx=10)

        self.activation_entry = ctk.CTkEntry(act)
        self.activation_entry.pack(fill="x", padx=10)
        self.activation_entry.insert(0, ", ".join(self.config_data["activation_keywords"]))

        # MAIN
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=20, pady=10)

        # LEFT MENU
        left = ctk.CTkFrame(main, width=280)
        left.pack(side="left", fill="y", padx=10)

        self.btn_add = ctk.CTkButton(left, text="➕ Добавить команду", command=self.add_command)
        self.btn_add.pack(fill="x", pady=6)

        self.btn_del = ctk.CTkButton(left, text="🗑 Удалить последнюю", fg_color="#a83232", command=self.delete_command)
        self.btn_del.pack(fill="x", pady=6)

        self.btn_save = ctk.CTkButton(left, text="💾 Сохранить", command=self.save)
        self.btn_save.pack(fill="x", pady=6)

        self.btn_run = ctk.CTkButton(left, text="▶ Запустить JARVIS", fg_color="#0a84ff", command=self.run_jarvis)
        self.btn_run.pack(fill="x", pady=6)

        self.btn_stop = ctk.CTkButton(left, text="⏹ Остановить JARVIS", fg_color="#555", command=self.stop_jarvis)
        self.btn_stop.pack(fill="x", pady=6)

        # COMMAND LIST
        self.command_frame = ctk.CTkScrollableFrame(main)
        self.command_frame.pack(side="left", fill="both", expand=True, padx=10)

    # ================= SYSTEM =================

    def update_buttons(self):
        if jarvis_running():
            self.btn_stop.configure(state="normal")
            self.btn_run.configure(state="disabled")
        else:
            self.btn_stop.configure(state="disabled")
            self.btn_run.configure(state="normal")

        self.after(2000, self.update_buttons)

    # ================= COMMAND LIST =================

    def load_commands(self):
        for w in self.command_frame.winfo_children():
            w.destroy()

        for cmd in self.config_data["commands"]:
            card = ctk.CTkFrame(self.command_frame)
            card.pack(fill="x", padx=10, pady=6)

            title = " | ".join(cmd["keywords"])
            target = cmd.get("path") or cmd.get("url") or str(cmd.get("volume"))

            ctk.CTkLabel(card, text=title, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10)
            ctk.CTkLabel(card, text=f"{cmd['action']} → {target}", text_color="#aaa").pack(anchor="w", padx=10)

    # ================= BUTTONS =================

    def add_command(self):
        CommandWindow(self, self.config_data, self.load_commands)

    def delete_command(self):
        if not self.config_data["commands"]:
            messagebox.showinfo("Информация", "Нет команд для удаления")
            return
        self.config_data["commands"].pop()
        self.load_commands()

    def save(self):
        self.config_data["activation_keywords"] = [k.strip() for k in self.activation_entry.get().split(",") if k.strip()]
        save_config(self.config_data)
        messagebox.showinfo("Сохранено", "Настройки сохранены")

    def run_jarvis(self):
        exe = sys.executable.replace("python.exe", "pythonw.exe")
        p = subprocess.Popen([exe, "jarvis.py"])
        with open("jarvis.pid", "w") as f:
            f.write(str(p.pid))
        self.update_buttons()

    def stop_jarvis(self):
        if not jarvis_running():
            messagebox.showinfo("Информация", "JARVIS не запущен")
            return

        try:
            with open("jarvis.pid", "r") as f:
                pid = int(f.read())
            psutil.Process(pid).terminate()
            os.remove("jarvis.pid")
            messagebox.showinfo("Остановлен", "JARVIS остановлен")
        except:
            messagebox.showerror("Ошибка", "Не удалось остановить JARVIS")

        self.update_buttons()

# ================= KEYWORD LIST =================

class KeywordList(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent, height=180)
        self.pack(fill="x", padx=20, pady=5)

        self.entries = []
        self.add_entry()

    def add_entry(self):
        e = ctk.CTkEntry(self, placeholder_text="Фраза активации")
        e.pack(fill="x", pady=4)
        e.bind("<KeyRelease>", lambda ev: self.check_last())
        self.entries.append(e)

    def check_last(self):
        if self.entries[-1].get().strip():
            self.add_entry()

    def get_keywords(self):
        return [e.get().strip() for e in self.entries if e.get().strip()]

# ================= ADD COMMAND WINDOW =================

class CommandWindow(ctk.CTkToplevel):

    def __init__(self, parent, config, refresh):
        super().__init__(parent)

        self.geometry("500x600")
        self.title("Новая команда")
        self.config_data = config
        self.refresh = refresh

        self.grab_set()
        self.focus_force()

        ctk.CTkLabel(self, text="Новая команда", font=("Segoe UI", 20, "bold")).pack(pady=10)
        ctk.CTkLabel(self, text="Фразы активации").pack()

        self.keyword_list = KeywordList(self)

        # Тип действия
        self.action = ctk.CTkComboBox(self, values=["launch_app", "open_url", "set_volume"])
        self.action.pack(fill="x", padx=20, pady=10)

        # ---- ПУТЬ / URL / ГРОМКОСТЬ ----
        target_frame = ctk.CTkFrame(self)
        target_frame.pack(fill="x", padx=20, pady=5)

        self.target = ctk.CTkEntry(target_frame, placeholder_text="Путь / URL / громкость")
        self.target.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_browse_target = ctk.CTkButton(
            target_frame, text="Обзор", width=80, command=self.browse_target
        )
        self.btn_browse_target.pack(side="right")

        # ---- WAV ----
        wav_frame = ctk.CTkFrame(self)
        wav_frame.pack(fill="x", padx=20, pady=5)

        self.wav = ctk.CTkEntry(wav_frame, placeholder_text="Файл подтверждения (.wav)")
        self.wav.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_browse_wav = ctk.CTkButton(
            wav_frame, text="Обзор", width=80, command=self.browse_wav
        )
        self.btn_browse_wav.pack(side="right")

        # Сохранить
        ctk.CTkButton(self, text="СОХРАНИТЬ", fg_color="#0a84ff", command=self.save).pack(pady=25)

    # ---------- FILE PICKERS ----------

    def browse_target(self):
        if self.action.get() == "open_url":
            messagebox.showinfo("Информация", "Для URL просто вставь ссылку")
            return

        path = filedialog.askopenfilename(filetypes=[("Программы", "*.exe"), ("Все файлы", "*.*")])
        if path:
            self.target.delete(0, "end")
            self.target.insert(0, path)

    def browse_wav(self):
        path = filedialog.askopenfilename(filetypes=[("WAV файлы", "*.wav")])
        if path:
            self.wav.delete(0, "end")
            self.wav.insert(0, path)

    # ---------- SAVE ----------

    def save(self):
        try:
            keywords = self.keyword_list.get_keywords()
            if not keywords:
                raise Exception()

            cmd = {
                "keywords": keywords,
                "action": self.action.get(),
                "response_wav": self.wav.get()
            }

            t = self.target.get()

            if cmd["action"] == "launch_app":
                cmd["path"] = t
            elif cmd["action"] == "open_url":
                cmd["url"] = t
            else:
                cmd["volume"] = int(t)

            self.config_data["commands"].append(cmd)
            self.refresh()
            self.destroy()

        except:
            messagebox.showerror("Ошибка", "Заполни все поля корректно")

# ================= RUN =================

if __name__ == "__main__":
    app = JarvisEditor()
    app.mainloop()
