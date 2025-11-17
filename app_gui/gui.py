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
from qkdn_sim import default_topology, baseline_route, crosslayer_route, rl_route, plot_network_path

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
        self.username = username
        ttk.Label(self, text=f"Welcome, {username}", font=(None, 12, 'bold')).grid(row=0, column=0, sticky='w')

        # PQC
        lf_pqc = ttk.LabelFrame(self, text="PQC Core")
        lf_pqc.grid(row=1, column=0, sticky='ew', padx=4, pady=4)
        ttk.Button(lf_pqc, text="Build (make/cmake)", command=self.pqc_build).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(lf_pqc, text="Run example", command=self.pqc_run_example).grid(row=0, column=1, padx=4, pady=4)

        # Embedded
        lf_emb = ttk.LabelFrame(self, text="Embedded Notes")
        lf_emb.grid(row=2, column=0, sticky='nsew', padx=4, pady=4)
        self.emb_text = tk.Text(lf_emb, height=12, wrap='word')
        self.emb_text.grid(row=0, column=0, sticky='nsew')
        ttk.Button(lf_emb, text="Load notes", command=self.load_embedded_notes).grid(row=1, column=0, sticky='w', padx=4, pady=4)
        lf_emb.rowconfigure(0, weight=1)
        lf_emb.columnconfigure(0, weight=1)

        # QKD
        lf_qkd = ttk.LabelFrame(self, text="QKD Simulation")
        lf_qkd.grid(row=3, column=0, sticky='ew', padx=4, pady=4)
        self.src = tk.IntVar(value=1)
        self.dst = tk.IntVar(value=6)
        self.steps = tk.IntVar(value=50)
        self.policy = tk.StringVar(value='baseline')
        ttk.Label(lf_qkd, text="Src").grid(row=0, column=0)
        ttk.Entry(lf_qkd, textvariable=self.src, width=5).grid(row=0, column=1)
        ttk.Label(lf_qkd, text="Dst").grid(row=0, column=2)
        ttk.Entry(lf_qkd, textvariable=self.dst, width=5).grid(row=0, column=3)
        ttk.Label(lf_qkd, text="Steps").grid(row=0, column=4)
        ttk.Entry(lf_qkd, textvariable=self.steps, width=7).grid(row=0, column=5)
        ttk.Label(lf_qkd, text="Policy").grid(row=0, column=6)
        ttk.Combobox(lf_qkd, textvariable=self.policy, values=['baseline','cross','rl'], width=10, state='readonly').grid(row=0, column=7)
        ttk.Button(lf_qkd, text="Run & Save Plot", command=self.qkd_run).grid(row=0, column=8, padx=6)

        self.columnconfigure(0, weight=1)

    def pqc_build(self):
        def task():
            build_dir = os.path.join(ROOT, 'pqc_core', 'build')
            os.makedirs(build_dir, exist_ok=True)
            cmake = shutil.which('cmake') if 'shutil' in sys.modules else None
            if cmake:
                run_cmd(['cmake', '..'], cwd=build_dir)
                run_cmd(['make'], cwd=build_dir)
            else:
                run_cmd(['make', '-C', os.path.join(ROOT, 'pqc_core')])
        threading.Thread(target=task, daemon=True).start()

    def pqc_run_example(self):
        def task():
            run_cmd(['make', 'core-make-example'], cwd=ROOT)
        threading.Thread(target=task, daemon=True).start()

    def load_embedded_notes(self):
        path = os.path.join(ROOT, 'pqc_embedded', 'OPTIMIZATION_NOTES.md')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.emb_text.delete('1.0', 'end')
                self.emb_text.insert('end', f.read())
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def qkd_run(self):
        out_path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG','*.png')], initialfile='qkd_path.png')
        if not out_path:
            return
        def task():
            net = default_topology()
            net.step(int(self.steps.get()))
            src = int(self.src.get()); dst = int(self.dst.get())
            pol = self.policy.get()
            if pol == 'baseline':
                path = baseline_route(net, src, dst)
            elif pol == 'cross':
                path = crosslayer_route(net, src, dst)
            else:
                path = rl_route(net, src, dst)
            plot_network_path(net, path, out=out_path)
            messagebox.showinfo("QKD", f"Chosen path: {path}\nSaved: {out_path}")
        threading.Thread(target=task, daemon=True).start()


def main():
    root = tk.Tk()
    root.title("PQC-QKD Suite")
    root.geometry('840x600')

    def on_success(user):
        for w in root.winfo_children():
            w.destroy()
        mf = MainFrame(root, user)
        mf.pack(fill='both', expand=True)

    lf = LoginFrame(root, on_success=on_success)
    lf.pack(fill='both', expand=True, padx=8, pady=8)

    root.mainloop()


if __name__ == '__main__':
    main()
