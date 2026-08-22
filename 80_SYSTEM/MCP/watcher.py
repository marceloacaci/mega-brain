"""Watcher do cofre Obsidian (Mega Brain).

Monitora mudanças em .md e registra em 80_SYSTEM/LOGS/watcher.log.
Usa watchdog se disponível; senão cai num polling simples (compatível com qq Python).

Uso:
  python watcher.py            # roda até Ctrl+C
  python watcher.py --once 5   # roda 5s e sai (útil p/ teste)
"""
import os
import sys
import time
from config import load_config

_CFG = load_config()
_VAULT = _CFG.get("vault_path", "")
_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "LOGS", "watcher.log")


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def handle(path):
    if not path.endswith(".md"):
        return
    rel = os.path.relpath(path, _VAULT).replace("\\", "/") if _VAULT else path
    log(f"change: {rel}")


try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    class _H(FileSystemEventHandler):
        def on_modified(self, e):
            if not e.is_directory:
                handle(e.src_path)

        def on_created(self, e):
            if not e.is_directory:
                handle(e.src_path)

    def run(seconds=0):
        obs = Observer()
        obs.schedule(_H(), _VAULT, recursive=True)
        obs.start()
        log(f"watcher ativo (watchdog) em {_VAULT}")
        try:
            if seconds > 0:
                time.sleep(seconds)
                obs.stop()
            else:
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            obs.stop()
            obs.join()

except ImportError:
    def run(seconds=0):
        log(f"watcher ativo (polling) em {_VAULT}")
        seen = {}
        for root, _, files in os.walk(_VAULT):
            if ".obsidian" in root:
                continue
            for fn in files:
                if fn.endswith(".md"):
                    p = os.path.join(root, fn)
                    try:
                        seen[p] = os.path.getmtime(p)
                    except OSError:
                        pass
        deadline = time.time() + seconds if seconds > 0 else 0
        try:
            while True:
                for root, _, files in os.walk(_VAULT):
                    if ".obsidian" in root:
                        continue
                    for fn in files:
                        if fn.endswith(".md"):
                            p = os.path.join(root, fn)
                            try:
                                m = os.path.getmtime(p)
                            except OSError:
                                continue
                            if p not in seen or m != seen[p]:
                                seen[p] = m
                                handle(p)
                if seconds > 0 and time.time() >= deadline:
                    return
                time.sleep(2)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    once = 0
    if "--once" in sys.argv:
        i = sys.argv.index("--once")
        once = int(sys.argv[i + 1]) if i + 1 < len(sys.argv) else 5
    run(seconds=once)
