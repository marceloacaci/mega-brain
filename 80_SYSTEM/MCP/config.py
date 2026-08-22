"""Lê o config.json do Mega Brain (80_SYSTEM/SCRIPTS/config.json)."""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.abspath(os.path.join(_HERE, "..", "SCRIPTS", "config.json"))


def load_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "mcp_server_url": "http://localhost:8770",
            "vault_path": r"D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills",
        }


if __name__ == "__main__":
    import pprint
    pprint.pprint(load_config())
