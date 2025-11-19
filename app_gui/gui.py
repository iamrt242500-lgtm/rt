import os
# Ensure headless-friendly backend for matplotlib before importing qkdn_sim
os.environ.setdefault('MPLBACKEND', 'Agg')
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import sys
import shutil

from lib.auth_store import register_user, authenticate_user
from qkdn_sim import default_topology, baseline_route, crosslayer_route, rl_route, plot_network_path  # retained (not used now)
from app_gui.tetris import TetrisFrame

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def run_cmd(cmd, cwd=None):
    try:
        subprocess.check_call(cmd, cwd=cwd)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Command failed: {' '.join(cmd)}\nExit code: {e.returncode}")


class LoginFrame(ttk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.username = tk.StringVar()
        self.password = tk.StringVar()

        ttk.Label(self, text="Username").grid(row=0, column=0, sticky='w')
        ttk.Entry(self, textvariable=self.username).grid(row=0, column=1, sticky='ew')
        ttk.Label(self, text="Password").grid(row=1, column=0, sticky='w')
        ttk.Entry(self, textvariable=self.password, show='*').grid(row=1, column=1, sticky='ew')

        btns = ttk.Frame(self)
        btns.grid(row=2, column=0, columnspan=2, pady=6)
        ttk.Button(btns, text="Login", command=self.do_login).pack(side='left', padx=4)
        ttk.Button(btns, text="Register", command=self.do_register).pack(side='left', padx=4)

        self.columnconfigure(1, weight=1)

    def do_login(self):
        u = self.username.get().strip()
        p = self.password.get()
        if not u or not p:
            messagebox.showwarning("Login", "Enter username and password")
            return
        if authenticate_user(u, p):
            self.on_success(u)
        else:
            messagebox.showerror("Login", "Invalid credentials")

    def do_register(self):
        u = self.username.get().strip()
        p = self.password.get()
        if not u or not p:
            messagebox.showwarning("Register", "Enter username and password")
            return
        ok = register_user(u, p)
        if ok:
            messagebox.showinfo("Register", "Registration successful. You can login now.")
        else:
            messagebox.showerror("Register", "User already exists")


class MainFrame(ttk.Frame):
    def __init__(self, master, username):
        super().__init__(master)
        # Replaced content with embedded Tetris game
        ttk.Label(self, text=f"PQC Login OK - Tetris Mode (Player: {username})", font=(None, 14, 'bold')).pack(pady=8)
        # Mount Tetris
        tf = TetrisFrame(self, username=username)
        tf.pack()


def main():
    root = tk.Tk()
    root.title("PQC-QKD Suite")
    root.geometry('840x600')

    def on_success(user):
        for w in root.winfo_children():
            w.destroy()
        # Load Tetris-based main frame
        mf = MainFrame(root, user)
        mf.pack(fill='both', expand=True)

    lf = LoginFrame(root, on_success=on_success)
    lf.pack(fill='both', expand=True, padx=8, pady=8)

    root.mainloop()


if __name__ == '__main__':
    main()
