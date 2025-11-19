import sysimport argparse

import subprocess

USAGE = """PQC-QKD Suite CLI (stub)import sys

import os

현재 GUI 테트리스 모드 중심입니다. 기본 명령:import shutil

  help            도움말 출력import getpass

  exit            종료import binascii

import hashlib

추후: pqc build/run, qkd simulate 등 복구 예정.from qkdn_sim import default_topology, baseline_route, crosslayer_route, rl_route, plot_network_path

"""

# Determine project root. When frozen via PyInstaller, prefer current working directory.

def main():if getattr(sys, 'frozen', False):

    if len(sys.argv) > 1 and sys.argv[1] in ('help','-h','--help'):    ROOT = os.getcwd()

        print(USAGE)else:

        return    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    print(USAGE)

    # 간단 인터랙티브 루프 (옵션)

    try:def run(cmd, cwd=None):

        while True:    print("$", " ".join(cmd))

            cmd = input('cli> ').strip().lower()    r = subprocess.run(cmd, cwd=cwd)

            if cmd in ('exit','quit'): break    if r.returncode != 0:

            elif cmd in ('help',''): print(USAGE)        sys.exit(r.returncode)

            else: print('알 수 없는 명령:', cmd)

    except (EOFError, KeyboardInterrupt):

        passdef cmd_pqc(args):

    if args.action == 'build':

if __name__ == '__main__':        # try cmake first, fallback to make

    main()        build_dir = os.path.join(ROOT, 'pqc_core', 'build')

        os.makedirs(build_dir, exist_ok=True)
        cmake = shutil.which('cmake')
        if cmake:
            run(['cmake', '..'], cwd=build_dir)
            run(['make'], cwd=build_dir)
        else:
            # explicit directory to avoid cwd ambiguity in frozen apps
            run(['make', '-C', os.path.join(ROOT, 'pqc_core')])
    elif args.action == 'run':
        # prefer fallback make target for portability
        run(['make', 'core-make-example'], cwd=ROOT)
    else:
        print('Unknown pqc action')


def cmd_embedded(args):
    notes = os.path.join(ROOT, 'pqc_embedded', 'OPTIMIZATION_NOTES.md')
    with open(notes, 'r', encoding='utf-8') as f:
        print(f.read())


def cmd_qkd(args):
    # Run scenario directly (avoid relying on python -m when frozen)
    net = default_topology()
    net.step(args.steps)
    if args.policy == 'baseline':
        path = baseline_route(net, args.src, args.dst)
    elif args.policy == 'cross':
        path = crosslayer_route(net, args.src, args.dst)
    else:
        path = rl_route(net, args.src, args.dst)
    print(f"Chosen path: {path}")
    plot_network_path(net, path, out=args.plot)


def cmd_auth(args):
    # Secure password entry demo (no storage). Derive an ephemeral key.
    if args.env:
        pw = os.environ.get(args.env, "")
        if not pw:
            print(f"Environment variable {args.env} is empty or not set.")
            return
    else:
        pw = getpass.getpass("Password: ")
        if args.confirm:
            pw2 = getpass.getpass("Confirm: ")
            if pw != pw2:
                print("Passwords do not match.")
                return

    if len(pw) < 8:
        print("Warning: short password (recommend >= 8 characters)")

    if args.salt:
        try:
            salt = binascii.unhexlify(args.salt)
        except binascii.Error:
            print("Invalid --salt hex string")
            return
    else:
        salt = os.urandom(16)

    rounds = max(1, int(args.rounds))
    key = hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), salt, rounds, dklen=32)
    print("PBKDF2-HMAC-SHA256 derived key (hex):", binascii.hexlify(key).decode())
    print("Salt (hex):", binascii.hexlify(salt).decode())
    print(f"Rounds: {rounds}")
    print("Note: Password and key are NOT stored. This is a local, ephemeral demo.")


def interactive_menu():
    print("\nPQC-QKD Suite — Interactive Mode")
    print("Select an option:")
    print("  1) PQC build")
    print("  2) PQC run example")
    print("  3) Show embedded optimization notes")
    print("  4) Run QKD simulation")
    print("  5) Secure password input (PBKDF2 demo)")
    print("  0) Exit")
    try:
        choice = input("> ").strip()
    except EOFError:
        choice = "0"

    if choice == "1":
        class A: pass
        a = A(); a.action = 'build'
        cmd_pqc(a)
    elif choice == "2":
        class A: pass
        a = A(); a.action = 'run'
        cmd_pqc(a)
    elif choice == "3":
        class A: pass
        cmd_embedded(A())
    elif choice == "4":
        # collect simple parameters
        def ask_int(prompt, default):
            s = input(f"{prompt} [{default}]: ").strip()
            try:
                return int(s) if s else default
            except ValueError:
                return default
        def ask_str(prompt, default=None):
            s = input(f"{prompt}{f' [{default}]' if default is not None else ''}: ").strip()
            return s if s else default

        policy = ask_str("Policy (baseline/cross/rl)", "baseline")
        if policy not in {"baseline","cross","rl"}:
            policy = "baseline"
        steps = ask_int("Steps", 50)
        src = ask_int("Source node id", 1)
        dst = ask_int("Destination node id", 6)
        plot = ask_str("Save plot to file (optional)", None)

        class A:
            pass
        a = A()
        a.action = 'run'
        a.src = src
        a.dst = dst
        a.steps = steps
        a.policy = policy
        a.plot = plot
        cmd_qkd(a)
    elif choice == "5":
        class A:
            pass
        a = A()
        a.env = None
        a.salt = None
        a.rounds = 200000
        a.confirm = True
        cmd_auth(a)
    else:
        print("Bye.")


def main():
    # If launched without arguments (e.g., double-clicked or run directly), open interactive menu
    if len(sys.argv) == 1:
        interactive_menu()
        return

    ap = argparse.ArgumentParser(prog='cli')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p_pqc = sub.add_parser('pqc', help='Build/Run pqc_core example')
    p_pqc.add_argument('action', choices=['build','run'])
    p_pqc.set_defaults(func=cmd_pqc)

    p_emb = sub.add_parser('embedded', help='Show embedded optimization notes')
    p_emb.set_defaults(func=cmd_embedded)

    p_qkd = sub.add_parser('qkd', help='Run QKD simulation')
    p_qkd.add_argument('action', choices=['run'])
    p_qkd.add_argument('--src', type=int, default=1)
    p_qkd.add_argument('--dst', type=int, default=6)
    p_qkd.add_argument('--steps', type=int, default=50)
    p_qkd.add_argument('--policy', choices=['baseline','cross','rl'], default='baseline')
    p_qkd.add_argument('--plot', type=str, default=None)
    p_qkd.set_defaults(func=cmd_qkd)

    p_auth = sub.add_parser('auth', help='Secure password prompt and key-derivation demo')
    p_auth.add_argument('--env', type=str, default=None, help='Read password from environment variable (for automation)')
    p_auth.add_argument('--salt', type=str, default=None, help='Hex-encoded salt (16 bytes recommended). If omitted, random salt is generated.')
    p_auth.add_argument('--rounds', type=int, default=200000, help='PBKDF2 iterations (default: 200000)')
    p_auth.add_argument('--no-confirm', dest='confirm', action='store_false', help='Skip confirm prompt')
    p_auth.set_defaults(func=cmd_auth, confirm=True)

    args = ap.parse_args()
    if args.cmd == 'qkd':
        args.func(args)
    elif args.cmd == 'embedded':
        args.func(args)
    elif args.cmd == 'pqc':
        args.func(args)
    elif args.cmd == 'auth':
        args.func(args)

if __name__ == '__main__':
    main()
