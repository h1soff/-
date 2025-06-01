import telebot
import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import time
import os
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np

# ==== НАСТРОЙКИ ====
TOKEN = 'токен дота'
AUTHORIZED_USER_ID = твой айди тг
bot = telebot.TeleBot(TOKEN)
selected_camera_index = 0

# Создаём папки для фото, видео и аудио, если их нет
os.makedirs("photos", exist_ok=True)
os.makedirs("videos", exist_ok=True)
os.makedirs("audio", exist_ok=True)

# ==== GUI ====
def update_camera_list():
    """Updates the list of available cameras in the combobox."""
    update_btn.config(state=tk.DISABLED, text="Обновление...")
    root.update_idletasks() # Force GUI update to show disabled state

    available = []
    for i in range(5): # Check up to 5 camera indices
        cap = cv2.VideoCapture(i)
        if cap.read()[0]:
            available.append(i)
        cap.release()
    
    combo['values'] = available
    if available:
        combo.current(0)
        global selected_camera_index
        selected_camera_index = available[0]
        status_label.config(text=f"Выбрана камера: {selected_camera_index}")
    else:
        combo.set("Камеры не найдены")
        status_label.config(text="Камеры не найдены")
    
    update_btn.config(state=tk.NORMAL, text="Обновить камеры")

def on_select(event):
    """Handles camera selection from the combobox."""
    global selected_camera_index
    try:
        selected_camera_index = int(combo.get())
        status_label.config(text=f"Выбрана камера: {selected_camera_index}")
    except ValueError:
        status_label.config(text="Неверный выбор камеры")

def show_instructions():
    """Displays a message box with bot instructions."""
    instructions = (
        "Этот бот позволяет вам удаленно делать фото, записывать видео и аудио.\n\n"
        "**Доступные команды:**\n"
        "  - `/photo`: Сделать снимок.\n"
        "  - `/video <секунды>`: Записать видео указанной длительности (например, `/video 10`). Максимум 300 секунд.\n"
        "  - `/audio <секунды>`: Записать аудио указанной длительности (например, `/audio 15`). Максимум 300 секунд.\n\n"
        f"**Ваш ID пользователя:** {AUTHORIZED_USER_ID}\n"
        "Только этот пользователь может управлять ботом."
    )
    messagebox.showinfo("Инструкции по боту", instructions)

# Main window setup
root = tk.Tk()
root.title("Управление удаленной камерой/аудио")
root.geometry("400x250")
root.resizable(False, False) # Prevent resizing for a cleaner look

# Style configuration
style = ttk.Style()
style.theme_use('clam') # 'clam', 'alt', 'default', 'classic'

# Main Frame
main_frame = ttk.Frame(root, padding="20")
main_frame.pack(fill=tk.BOTH, expand=True)

# Camera Selection Section
camera_frame = ttk.LabelFrame(main_frame, text="Настройки камеры", padding="10")
camera_frame.pack(pady=10, padx=10, fill=tk.X)

label = ttk.Label(camera_frame, text="Выберите веб-камеру:")
label.pack(pady=5)

combo = ttk.Combobox(camera_frame, state="readonly")
combo.pack(pady=5, fill=tk.X)
combo.bind("<<ComboboxSelected>>", on_select)

update_btn = ttk.Button(camera_frame, text="Обновить список камер", command=update_camera_list)
update_btn.pack(pady=5)

status_label = ttk.Label(camera_frame, text="Ожидание выбора камеры...", foreground="blue")
status_label.pack(pady=5)

# Instructions Button
instructions_btn = ttk.Button(main_frame, text="Инструкции по боту", command=show_instructions)
instructions_btn.pack(pady=10)

# Initial camera list update
update_camera_list()

# ==== Камера ====
def capture_photo():
    cap = cv2.VideoCapture(selected_camera_index)
    ret, frame = cap.read()
    photo_path = None
    if ret:
        photo_path = os.path.join("photos", "photo.jpg")
        cv2.imwrite(photo_path, frame)
    cap.release()
    return photo_path

def record_video(seconds=5):
    cap = cv2.VideoCapture(selected_camera_index)
    if not cap.isOpened():
        print(f"Error: Could not open video stream for camera index {selected_camera_index}")
        return None

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_path = os.path.join("videos", "video.avi")
    # Check if a valid resolution can be obtained, default to 640x480
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if cap.get(cv2.CAP_PROP_FRAME_WIDTH) > 0 else 640
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if cap.get(cv2.CAP_PROP_FRAME_HEIGHT) > 0 else 480

    out = cv2.VideoWriter(video_path, fourcc, 20.0, (width, height))
    
    start = time.time()
    while time.time() - start < seconds:
        ret, frame = cap.read()
        if ret:
            out.write(frame)
        else:
            print("Warning: Could not read frame from camera.")
            break # Exit loop if frames cannot be read
    cap.release()
    out.release()
    return video_path

# ==== Аудиозапись ====
def record_audio(seconds=5, fs=44100):
    print(f"Recording audio for {seconds} seconds...")
    audio_path = os.path.join("audio", "audio.wav")
    try:
        recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # ждём окончания записи
        write(audio_path, fs, recording)
        print(f"Audio saved to {audio_path}")
        return audio_path
    except Exception as e:
        print(f"Error recording audio: {e}")
        return None

# ==== Бот ====
@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    if message.from_user.id != AUTHORIZED_USER_ID:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return
    bot.send_message(message.chat.id,
                     "Привет! Я бот для управления камерой и аудио.\n"
                     "Напиши /photo чтобы получить фото.\n"
                     "Напиши /video <секунды> чтобы записать видео.\n"
                     "Например: /video 10 — записать видео 10 секунд.\n"
                     "Максимум 300 секунд (5 минут).\n"
                     "Команда /audio <секунды> — записать аудио.\n"
                     "Максимум 300 секунд.")

@bot.message_handler(commands=['photo'])
def handle_photo(message):
    if message.from_user.id != AUTHORIZED_USER_ID:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return
    bot.send_message(message.chat.id, "Делаю фото...")
    photo_path = capture_photo()
    if photo_path and os.path.exists(photo_path):
        with open(photo_path, "rb") as f:
            bot.send_photo(message.chat.id, f)
        os.remove(photo_path) # Clean up the photo file
    else:
        bot.send_message(message.chat.id, "Не удалось сделать фото. Проверьте подключение камеры.")

@bot.message_handler(commands=['video'])
def handle_video(message):
    if message.from_user.id != AUTHORIZED_USER_ID:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return
    parts = message.text.split()
    seconds = 5
    if len(parts) > 1:
        try:
            sec = int(parts[1])
            if sec < 1:
                bot.send_message(message.chat.id, "Время должно быть не меньше 1 секунды.")
                return
            if sec > 300:
                bot.send_message(message.chat.id, "Максимальное время записи — 300 секунд (5 минут).")
                return
            seconds = sec
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат времени. Укажите число секунд.")
            return
    bot.send_message(message.chat.id, f"Записываю видео {seconds} секунд...")
    video_path = record_video(seconds)
    if video_path and os.path.exists(video_path):
        with open(video_path, "rb") as f:
            bot.send_video(message.chat.id, f)
        os.remove(video_path) # Clean up the video file
    else:
        bot.send_message(message.chat.id, "Не удалось записать видео. Проверьте подключение камеры.")

@bot.message_handler(commands=['audio'])
def handle_audio(message):
    if message.from_user.id != AUTHORIZED_USER_ID:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return
    parts = message.text.split()
    seconds = 5
    if len(parts) > 1:
        try:
            sec = int(parts[1])
            if sec < 1:
                bot.send_message(message.chat.id, "Время должно быть не меньше 1 секунды.")
                return
            if sec > 300:
                bot.send_message(message.chat.id, "Максимальное время записи — 300 секунд (5 минут).")
                return
            seconds = sec
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат времени. Укажите число секунд.")
            return
    bot.send_message(message.chat.id, f"Записываю аудио {seconds} секунд...")
    audio_path = record_audio(seconds)
    if audio_path and os.path.exists(audio_path):
        with open(audio_path, "rb") as f:
            bot.send_audio(message.chat.id, f)
        os.remove(audio_path) # Clean up the audio file
    else:
        bot.send_message(message.chat.id, "Не удалось записать аудио. Проверьте микрофон.")

def run_bot():
    bot.infinity_polling()

# Start the bot in a separate thread
Thread(target=run_bot, daemon=True).start()

# Start the Tkinter GUI
root.mainloop()