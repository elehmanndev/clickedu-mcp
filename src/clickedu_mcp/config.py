"""Per-user config: where credentials live and the one-time interactive setup.

A teacher runs `clickedu-mcp setup` once. It writes everything to
``~/.clickedu-mcp/`` so the MCP server (launched later with no terminal) can read
it. Environment variables still take precedence over this file.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from dotenv import load_dotenv


def config_dir() -> Path:
    override = os.environ.get("CLICKEDU_CONFIG_DIR", "").strip()
    return Path(override).expanduser() if override else Path.home() / ".clickedu-mcp"


def config_env_path() -> Path:
    return config_dir() / "config.env"


def load_env() -> None:
    """Load credentials. Precedence: real env vars > ~/.clickedu-mcp/config.env > ./.env."""
    # load_dotenv never overrides an already-set variable, so load the
    # highest-precedence file first.
    load_dotenv(config_env_path())
    load_dotenv()  # ./.env for local development


def _prompt(label: str, default: str = "", secret: bool = False) -> str:
    import getpass

    suffix = f" [{default}]" if default else ""
    if secret:
        val = getpass.getpass(f"{label}{suffix}: ").strip()
    else:
        val = input(f"{label}{suffix}: ").strip()
    return val or default


def setup() -> int:
    """Interactive first-run setup. Returns a process exit code."""
    print("\nClickedu MCP setup\n" + "-" * 18)
    print("This is stored only on this computer, under", config_dir(), "\n")

    load_env()  # prefill from any existing config

    base = _prompt(
        "Your school's Clickedu URL (e.g. https://yourschool.clickedu.eu)",
        os.environ.get("CLICKEDU_BASE_URL", ""),
    ).rstrip("/")
    if not base.startswith("http"):
        print("  URL must start with https://")
        return 1
    user = _prompt("Clickedu username", os.environ.get("CLICKEDU_USERNAME", ""))
    pw = _prompt("Clickedu password", secret=True)
    if not pw and os.environ.get("CLICKEDU_PASSWORD"):
        pw = os.environ["CLICKEDU_PASSWORD"]  # keep existing if left blank
    passfile_src = _prompt(
        "Path to your pass file (the 'arxiu de pas' file)",
        os.environ.get("CLICKEDU_PASSFILE", ""),
    )
    src = Path(passfile_src).expanduser()
    if not src.is_file():
        print(f"  Pass file not found at {src}")
        return 1
    if not (base and user and pw):
        print("  URL, username and password are all required.")
        return 1

    cfg = config_dir()
    cfg.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(cfg, 0o700)
    except OSError:
        pass

    # Copy the pass file in so it is self-contained and survives the original moving.
    passfile_dst = cfg / "passfile"
    if src.resolve() != passfile_dst.resolve():
        shutil.copyfile(src, passfile_dst)
    os.chmod(passfile_dst, 0o600)

    env_path = config_env_path()
    lines = [
        f"CLICKEDU_BASE_URL={base}",
        f"CLICKEDU_USERNAME={user}",
        f"CLICKEDU_PASSWORD={pw}",
        f"CLICKEDU_PASSFILE={passfile_dst}",
        f"CLICKEDU_COOKIE_PATH={cfg / 'cookies.jar'}",
    ]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(env_path, 0o600)
    print(f"\nSaved to {env_path} (permissions 600).")

    # Verify login so the teacher knows it works before wiring it into Codex.
    print("Testing login...")
    for k in ("CLICKEDU_BASE_URL", "CLICKEDU_USERNAME", "CLICKEDU_PASSWORD",
              "CLICKEDU_PASSFILE", "CLICKEDU_COOKIE_PATH"):
        os.environ.pop(k, None)
    load_env()
    try:
        from .session import ClickeduSession

        ClickeduSession().login()
    except Exception as e:  # noqa: BLE001 - surface any login failure plainly
        print(f"  Login FAILED: {e}")
        print("  Check your details and run setup again.")
        return 1
    print("  Login OK.\n")
    print("Now add it to Codex (one line):")
    print("  codex mcp add clickedu -- uvx --from "
          "git+https://github.com/elehmanndev/clickedu-mcp clickedu-mcp\n")
    return 0
