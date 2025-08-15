import tkinter as tk
import sys
from tkinter import messagebox
from GUI import MainUI
from callbacks import AppCallbacks
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def hide_console():
    if sys.platform.startswith('win'):
        try:
            import ctypes
            console_window = ctypes.windll.kernel32.GetConsoleWindow()
            if console_window != 0:
                ctypes.windll.user32.ShowWindow(console_window, 0)
        except Exception:
            messagebox.showwarning("界面提示", "无法隐藏控制台窗口")

def main():
    hide_console()

    root = tk.Tk()
    root.title("Oblivionis")
    root.geometry("800x800")
    root.minsize(800, 600)

    try:
        root.iconbitmap("assets/icon.ico")
    except tk.TclError:
        pass

    # draw UI -> bind callbacks -> start loop
    ui = MainUI(root)

    callbacks = AppCallbacks(root, ui)
    callbacks.bind_callbacks()

    callbacks.process_queue()
    root.mainloop()


if __name__ == "__main__":
    main()