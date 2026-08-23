#!/usr/bin/env python3
"""E2E de Resiliencia (M5): failover de backup + verificacao de integridade.

Usa fixtures em tmp (sem discos reais). Invoca os scripts PowerShell com
-Vault/-ConfigPath apontando para o fixture. Prova:
  - backup_vault.ps1 faz failover para 2o destino quando o primario e invalido
  - verify_integrity.ps1 detecta cofre integro (exit 0) e corrompido (exit 1)
Nao altera o vault real. Requer PowerShell 7 (pwsh).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

VAULT = r"D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"
# SCRIPTS deve ser relativo ao proprio teste (repo clonado), nao ao vault
# hardcoded — no CI o repo fica em D:\a\...\mega-brain, nao no vault real.
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS"))


def run_pwsh(script, *args):
    cmd = ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", os.path.join(SCRIPTS, script)] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        print(f"   [pwsh debug] {script} rc={p.returncode}")
        print("   STDOUT:", (p.stdout or "").strip()[:800])
        print("   STDERR:", (p.stderr or "").strip()[:800])
    return p.returncode, p.stdout, p.stderr


def make_vault_fixture(root):
    for d in ["10_MEGA_BRAIN", "70_MOCS", "80_SYSTEM", "80_SYSTEM/SCRIPTS", "80_SYSTEM/LOGS"]:
        os.makedirs(os.path.join(root, d), exist_ok=True)
    notes = {
        "10_MEGA_BRAIN/INDEX_GERAL.md": "# Index\n",
        "70_MOCS/MOC_TEST.md": "---\ntipo: moc\n---\n# Test\n",
        "80_SYSTEM/SCRIPTS/config.json": "{\"backup\":{\"root\":\"X:\\\\invalido\",\"secondary_root\":\"\"}}",
    }
    for rel, c in notes.items():
        with open(os.path.join(root, rel), "w", encoding="utf-8") as f:
            f.write(c)
    return os.path.join(root, "80_SYSTEM", "SCRIPTS", "config.json")


def main():
    print("=== E2E Resiliencia (M5) ===")
    tmp = tempfile.mkdtemp(prefix="mb_m5_")
    results = []
    try:
        vault_fx = os.path.join(tmp, "vault")
        os.makedirs(vault_fx, exist_ok=True)
        cfg = make_vault_fixture(vault_fx)

        # --- Failover: primario invalido (X:), secundario valido (tmp) ---
        sec = os.path.join(tmp, "backup2")
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump({"backup": {"root": "X:\\nao_existe", "secondary_root": sec}}, f)
        rc, out, err = run_pwsh("backup_vault.ps1", "-Vault", vault_fx, "-ConfigPath", cfg)
        # robocopy do primario falha (X: inexistente); failover deve copiar para sec
        backed_up = os.path.exists(os.path.join(sec, "full"))
        # conta notas copiadas no secundario
        copied = sum(len(fs) for _, _, fs in os.walk(sec)) if backed_up else 0
        results.append(("failover_backup", rc == 0 and backed_up and copied > 0))
        print(("PASS" if rc == 0 and backed_up else "FAIL"), "failover_backup",
              f"(rc={rc}, sec_criado={backed_up}, arquivos={copied})")

        # --- Integridade: cofre integro -> exit 0 ---
        rc2, out2, _ = run_pwsh("verify_integrity.ps1", "-Vault", vault_fx)
        results.append(("integrity_ok", rc2 == 0))
        print(("PASS" if rc2 == 0 else "FAIL"), "integrity_ok", f"(rc={rc2})")

        # --- Integridade: nota corrompida (0 bytes) -> exit 1 ---
        bad = os.path.join(vault_fx, "10_MEGA_BRAIN", "BROKEN.md")
        open(bad, "w", encoding="utf-8").close()  # 0 bytes
        rc3, _, _ = run_pwsh("verify_integrity.ps1", "-Vault", vault_fx)
        results.append(("integrity_detects_corrupt", rc3 == 1))
        print(("PASS" if rc3 == 1 else "FAIL"), "integrity_detects_corrupt", f"(rc={rc3})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ok = all(p for _, p in results)
    for name, p in results:
        if not p:
            print("FAIL", name)
    print("RESULTADO:", "TODOS PASSARAM" if ok else "FALHAS DETECTADAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
