import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import os
import time
import threading
import webbrowser
import subprocess
from datetime import datetime
import schedule
from plyer import notification  # ← Додано

class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Нагадувач")
        self.reminders = []
        self.load_reminders()

        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10)

        self.listbox = tk.Listbox(self.frame, width=80)
        self.listbox.pack()

        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Додати", command=self.add_reminder).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Редагувати", command=self.edit_reminder).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Видалити", command=self.delete_reminder).grid(row=0, column=2, padx=5)

        self.update_listbox()
        self.setup_schedule()
        self.start_scheduler()

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def show_notification(self, title, message):
        notification.notify(
            title=title,
            message=message,
            timeout=10  # в секундах
        )

    def add_reminder(self):
        time_str = simpledialog.askstring("Час", "Введіть час у форматі ГГ:ХХ (24-год):")
        message = simpledialog.askstring("Повідомлення", "Введіть повідомлення:")
        repeat = messagebox.askyesno("Повторення", "Повторювати щодня?")
        action_type = simpledialog.askstring("Тип дії", "Введіть 'сайт' або 'програма':")
        action_value = simpledialog.askstring("Шлях/URL", "Введіть URL або шлях до програми:")

        if time_str and message:
            reminder = {
                "time": time_str,
                "message": message,
                "repeat": repeat,
                "action_type": action_type,
                "action_value": action_value
            }
            self.reminders.append(reminder)
            self.save_reminders()
            self.update_listbox()
            self.setup_schedule()

    def edit_reminder(self):
        index = self.listbox.curselection()
        if index:
            index = index[0]
            reminder = self.reminders[index]

            time_str = simpledialog.askstring("Час", "Редагуйте час:", initialvalue=reminder["time"])
            message = simpledialog.askstring("Повідомлення", "Редагуйте повідомлення:", initialvalue=reminder["message"])
            repeat = messagebox.askyesno("Повторення", "Повторювати щодня?")
            action_type = simpledialog.askstring("Тип дії", "Введіть 'сайт' або 'програма':", initialvalue=reminder["action_type"])
            action_value = simpledialog.askstring("Шлях/URL", "Введіть URL або шлях до програми:", initialvalue=reminder["action_value"])

            if time_str and message:
                self.reminders[index] = {
                    "time": time_str,
                    "message": message,
                    "repeat": repeat,
                    "action_type": action_type,
                    "action_value": action_value
                }
                self.save_reminders()
                self.update_listbox()
                self.setup_schedule()

    def delete_reminder(self):
        index = self.listbox.curselection()
        if index:
            del self.reminders[index[0]]
            self.save_reminders()
            self.update_listbox()
            self.setup_schedule()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for r in self.reminders:
            repeat_str = " (щодня)" if r["repeat"] else ""
            self.listbox.insert(tk.END, f'{r["time"]} - {r["message"]}{repeat_str} [{r["action_type"]}]')

    def load_reminders(self):
        if os.path.exists("reminders.json"):
            with open("reminders.json", "r", encoding="utf-8") as f:
                self.reminders = json.load(f)

    def save_reminders(self):
        with open("reminders.json", "w", encoding="utf-8") as f:
            json.dump(self.reminders, f, indent=4, ensure_ascii=False)

    def setup_schedule(self):
        schedule.clear()
        for r in self.reminders:
            h, m = map(int, r["time"].split(":"))
            if r["repeat"]:
                schedule.every().day.at(r["time"]).do(self.open_task, r)
            else:
                today = datetime.now()
                if today.hour == h and today.minute == m:
                    self.open_task(r)
                else:
                    schedule.every().day.at(r["time"]).do(self.one_time_task, r)

    def one_time_task(self, task):
        self.open_task(task)
        self.reminders.remove(task)
        self.save_reminders()
        self.update_listbox()

    def open_task(self, task):
        self.show_notification("Нагадування", task["message"])
        if task["action_type"] == "сайт":
            webbrowser.open(task["action_value"])
        elif task["action_type"] == "програма":
            subprocess.Popen(task["action_value"], shell=True)

    def check_reminders(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def start_scheduler(self):
        threading.Thread(target=self.check_reminders, daemon=True).start()

    def hide_window(self):
        self.root.withdraw()

if __name__ == "__main__":
    root = tk.Tk()
    app = ReminderApp(root)
    root.mainloop()
