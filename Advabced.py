import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import webbrowser
import subprocess
import threading
import time
from datetime import datetime, timedelta
import json
import os
import pystray
from PIL import Image
from plyer import notification  # Додано для системного сповіщення

REMINDER_FILE = "reminders.json"

class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Розумний Нагадувач")
        self.root.geometry("500x550")

        self.tasks = []
        self.selected_index = None

        self.create_widgets()
        self.load_tasks()
        self.refresh_task_list()

        threading.Thread(target=self.check_tasks, daemon=True).start()
        threading.Thread(target=self.setup_tray, daemon=True).start()

    def create_widgets(self):
        tk.Label(self.root, text="Час (YYYY-MM-DD HH:MM):").pack()
        self.entry_time = tk.Entry(self.root)
        self.entry_time.pack()

        tk.Label(self.root, text="Повідомлення:").pack()
        self.entry_message = tk.Entry(self.root)
        self.entry_message.pack()

        tk.Label(self.root, text="Посилання або програма:").pack()
        self.entry_target = tk.Entry(self.root)
        self.entry_target.pack()

        self.browse_button = tk.Button(self.root, text="Огляд...", command=self.browse_file)
        self.browse_button.pack(pady=2)

        self.var_type = tk.StringVar(value="url")
        tk.Radiobutton(self.root, text="Відкрити сайт", variable=self.var_type, value="url").pack()
        tk.Radiobutton(self.root, text="Запустити програму", variable=self.var_type, value="program").pack()

        tk.Label(self.root, text="Тип повторення:").pack()
        self.combo_repeat = ttk.Combobox(self.root, values=["одноразове", "щодня", "щотижня"])
        self.combo_repeat.set("одноразове")
        self.combo_repeat.pack()

        tk.Button(self.root, text="Зберегти / Оновити", command=self.add_task).pack(pady=5)
        tk.Button(self.root, text="Видалити вибране", command=self.delete_task).pack(pady=2)

        tk.Label(self.root, text="Нагадування:").pack()
        self.listbox_tasks = tk.Listbox(self.root, height=10, width=70)
        self.listbox_tasks.pack(pady=5)
        self.listbox_tasks.bind("<<ListboxSelect>>", self.on_task_select)

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.entry_target.delete(0, tk.END)
            self.entry_target.insert(0, file_path)
            self.var_type.set("program")

    def add_task(self):
        time_str = self.entry_time.get()
        message = self.entry_message.get()
        target = self.entry_target.get()
        task_type = self.var_type.get()
        repeat = self.combo_repeat.get()

        if not time_str or not message or not target:
            messagebox.showwarning("Увага", "Будь ласка, заповніть всі поля!")
            return

        try:
            datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Помилка", "Формат дати: YYYY-MM-DD HH:MM")
            return

        new_task = {
            "time": time_str,
            "type": task_type,
            "value": target,
            "message": message,
            "repeat": repeat
        }

        if self.selected_index is not None:
            self.tasks[self.selected_index] = new_task
            self.selected_index = None
        else:
            self.tasks.append(new_task)

        self.save_tasks()
        self.refresh_task_list()
        self.clear_inputs()
        messagebox.showinfo("OK", "Нагадування збережено!")

    def on_task_select(self, event):
        selected = self.listbox_tasks.curselection()
        if selected:
            idx = selected[0]
            self.selected_index = idx
            task = self.tasks[idx]
            self.entry_time.delete(0, tk.END)
            self.entry_time.insert(0, task["time"])
            self.entry_message.delete(0, tk.END)
            self.entry_message.insert(0, task["message"])
            self.entry_target.delete(0, tk.END)
            self.entry_target.insert(0, task["value"])
            self.var_type.set(task["type"])
            self.combo_repeat.set(task.get("repeat", "одноразове"))

    def delete_task(self):
        selected = self.listbox_tasks.curselection()
        if selected:
            idx = selected[0]
            confirm = messagebox.askyesno("Підтвердження", "Видалити це нагадування?")
            if confirm:
                del self.tasks[idx]
                self.save_tasks()
                self.refresh_task_list()
                self.clear_inputs()
                self.selected_index = None

    def refresh_task_list(self):
        self.listbox_tasks.delete(0, tk.END)
        for idx, task in enumerate(self.tasks):
            self.listbox_tasks.insert(tk.END, f"{idx+1}. {task['time']} | {task['message']}")

    def clear_inputs(self):
        self.entry_time.delete(0, tk.END)
        self.entry_message.delete(0, tk.END)
        self.entry_target.delete(0, tk.END)
        self.var_type.set("url")
        self.combo_repeat.set("одноразове")

    def check_tasks(self):
        while True:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            for task in self.tasks[:]:
                if task["time"] == now:
                    self.open_task(task)
                    if task["repeat"] == "одноразове":
                        self.tasks.remove(task)
                    else:
                        dt = datetime.strptime(task["time"], "%Y-%m-%d %H:%M")
                        if task["repeat"] == "щодня":
                            dt += timedelta(days=1)
                        elif task["repeat"] == "щотижня":
                            dt += timedelta(weeks=1)
                        task["time"] = dt.strftime("%Y-%m-%d %H:%M")
            self.save_tasks()
            self.refresh_task_list()
            time.sleep(30)

    def open_task(self, task):
        if task["type"] == "url":
            webbrowser.open(task["value"])
        elif task["type"] == "program":
            try:
                subprocess.Popen(task["value"])
            except Exception as e:
                print("Помилка запуску програми:", e)

        # Використання plyer для системного сповіщення
        notification.notify(
            title="Нагадування",
            message=task["message"],
            timeout=10
        )

    def save_tasks(self):
        with open(REMINDER_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=4)

    def load_tasks(self):
        if os.path.exists(REMINDER_FILE):
            with open(REMINDER_FILE, "r", encoding="utf-8") as f:
                self.tasks = json.load(f)

    def setup_tray(self):
        def on_show():
            self.root.after(0, self.root.deiconify)

        def on_quit():
            self.icon.stop()
            self.root.quit()

        image = Image.open("reminder_icon.png")
        self.icon = pystray.Icon("reminder", image, "Нагадувач", menu=pystray.Menu(
            pystray.MenuItem("Відкрити", on_show),
            pystray.MenuItem("Вийти", on_quit)
        ))
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.icon.run()

    def hide_window(self):
        self.root.withdraw()

if __name__ == "__main__":
    root = tk.Tk()
    app = ReminderApp(root)
    root.mainloop()
