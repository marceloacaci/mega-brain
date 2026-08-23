#!/usr/bin/env python3
"""Teste de debounce do watcher MEGA BRAIN (stdlib, sem dependencias).

Importa watcher.py como modulo e valida que eventos repetidos da MESMA nota
numa janela de 2s sao ignorados (debounce), mas notas diferentes disparam.

Uso:
  python tests/test_watcher_debounce.py
"""
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WATCHER = os.path.join(HERE, "..", "80_SYSTEM", "MCP", "watcher.py")

# Stub de config para o watcher importar sem o vault real
sys.modules["config"] = type(sys)("config")
sys.modules["config"].load_config = lambda: {"vault_path": "C:/fake", "watcher_debounce_ms": 2000}


def load_watcher():
    spec = importlib.util.spec_from_file_location("watcher_test", WATCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    w = load_watcher()
    results = []

    # 1. Primeiro evento de uma nota processa
    w._LAST_SEEN.clear()
    w.handle("C:/fake/10_MEGA_BRAIN/NOTA.md")
    results.append(("first_event_processed", "change: 10_MEGA_BRAIN/NOTA.md" in open(w._LOG, encoding="utf-8").read() if os.path.exists(w._LOG) else False))

    # 2. Evento repetido na mesma nota < 2s é ignorado (nao gera nova linha)
    before = os.path.getsize(w._LOG) if os.path.exists(w._LOG) else 0
    w.handle("C:/fake/10_MEGA_BRAIN/NOTA.md")
    after = os.path.getsize(w._LOG) if os.path.exists(w._LOG) else 0
    results.append(("same_note_within_debounce_ignored", before == after))

    # 3. Nota diferente processa mesmo em janela curta
    w.handle("C:/fake/20_DAILY_NOTES/OUTRA.md")
    after2 = os.path.getsize(w._LOG) if os.path.exists(w._LOG) else 0
    results.append(("different_note_processed", after2 > after))

    # 4. Apos > 2s a mesma nota processa de novo
    time.sleep(2.1)
    w.handle("C:/fake/10_MEGA_BRAIN/NOTA.md")
    after3 = os.path.getsize(w._LOG) if os.path.exists(w._LOG) else 0
    results.append(("same_note_after_debounce_processed", after3 > after2))

    ok_all = True
    for name, passed in results:
        print("%s %s" % ("PASS" if passed else "FAIL", name))
        ok_all = ok_all and passed
    print("RESULTADO:", "TODOS PASSARAM" if ok_all else "FALHAS DETECTADAS")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
