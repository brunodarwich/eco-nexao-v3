"""Unified safe environment verification for ECOnexão (ECO-1301).

This script:
1. Checks local tool availability and versions (Python, Node, npm, pytest, Ruff, mypy, tsc, Jest, Supabase CLI).
2. Validates local environment configuration (.env and .env.test).
3. Detects environment isolation issues (e.g. .env and .env.test pointing to the same DB/URL).
4. NEVER logs or prints secret keys, passwords, DSNs, or API keys.
5. NEVER makes external network calls or remote database modifications.
6. Works across Windows and Linux platforms.
7. Exits with non-zero code if tools are missing or environment is insecure/colliding.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Paths
BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
APP_DIR = ROOT_DIR / "econexao-app"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


import re

# Sensitive patterns for output sanitization
_URL_PASSWORD_REGEX = re.compile(r"://([^:@\s]+):([^@\s]+)@")
_SECRET_KEY_REGEX = re.compile(r"(sb_secret_[a-zA-Z0-9_-]+|sb_publishable_[a-zA-Z0-9_-]+|eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)")
_ENV_PAIR_SECRET_REGEX = re.compile(r"(?i)(password|secret|key|token|dsn|url)\s*=\s*['\"]?([^\s'\"]+)['\"]?")


def sanitize_text(text: str) -> str:
    """Redact sensitive info (DSNs, passwords, URLs with auth, secret keys, JWTs) from text."""
    if not text:
        return ""
    # Redact credentials in URLs: postgres://user:password@host -> postgres://user:[REDACTED]@host
    redacted = _URL_PASSWORD_REGEX.sub(r"://\1:[REDACTED]@", text)
    # Redact secret tokens and keys
    redacted = _SECRET_KEY_REGEX.sub("[REDACTED_TOKEN]", redacted)
    # Redact key=value secret assignments when printed
    redacted = _ENV_PAIR_SECRET_REGEX.sub(r"\1=[REDACTED]", redacted)
    return redacted


def check_tool(command: str, args: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    """Check if a CLI tool is installed and retrieve its version string safely."""
    cmd_name = f"{command}.cmd" if sys.platform == "win32" and not command.endswith(".cmd") else command
    executable = shutil.which(cmd_name) or shutil.which(command)
    if not executable:
        return False, "NÃO INSTALADO"
    try:
        res = subprocess.run(
            [executable] + args,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            cwd=cwd,
        )
        out = (res.stdout or res.stderr or "").strip().splitlines()
        version_line = out[0] if out else "OK"
        return True, sanitize_text(version_line)
    except Exception as err:
        return False, f"ERRO AO EXECUTAR: {sanitize_text(str(err))}"


def run_checks() -> int:
    print("==================================================")
    print("ECOnexão — Verificação Sanitizada de Baseline (ECO-1301)")
    print("==================================================")

    failures: list[str] = []

    # 1. Platform & Tool versions
    print("\n[1] Ferramentas e Runtime:")
    print(f"  - Sistema Operacional: {sys.platform} ({os.name})")

    tools = [
        ("python", [sys.executable, "--version"], None),
        ("node", ["node", "--version"], None),
        ("npm", ["npm", "--version"], None),
        ("ruff", [sys.executable, "-m", "ruff", "--version"], None),
        ("mypy", [sys.executable, "-m", "mypy", "--version"], None),
        ("pytest", [sys.executable, "-m", "pytest", "--version"], None),
        ("tsc", ["node", "node_modules/typescript/bin/tsc", "--version"], APP_DIR),
        ("jest", ["node", "node_modules/jest/bin/jest.js", "--version"], APP_DIR),
        ("supabase", ["npx", "--no-install", "supabase", "--version"], ROOT_DIR),
    ]

    for tool_name, cmd, tool_cwd in tools:
        ok, ver = check_tool(cmd[0], cmd[1:], cwd=tool_cwd)
        status = "OK" if ok else "FALHA/AUSENTE"
        print(f"  - {tool_name:12s}: [{status}] {ver}")
        if not ok and tool_name in ("python", "node", "npm", "ruff", "mypy", "pytest"):
            failures.append(f"Ferramenta essencial ausente ou inacessível: {tool_name}")

    # 2. Environment files validation (Safe, no secrets printed)
    print("\n[2] Arquivos de Configuração Local:")

    dev_env_path = BACKEND_DIR / ".env"
    test_env_path = BACKEND_DIR / ".env.test"
    app_env_path = APP_DIR / ".env.local"

    print(f"  - backend/.env         : {'Presente' if dev_env_path.is_file() else 'AUSENTE'}")
    print(f"  - backend/.env.test    : {'Presente' if test_env_path.is_file() else 'AUSENTE'}")
    print(f"  - econexao-app/.env.local: {'Presente' if app_env_path.is_file() else 'AUSENTE'}")

    if not dev_env_path.is_file():
        failures.append("backend/.env não encontrado")
    if not test_env_path.is_file():
        failures.append("backend/.env.test não encontrado")

    # 3. Isolation & Collision check (Safe, comparing parsed keys without printing)
    print("\n[3] Isolamento e Segurança de Ambientes:")
    try:
        import scripts.check_env as check_env

        env_failures = check_env.validate()
        if env_failures:
            for f in env_failures:
                sanitized_f = sanitize_text(f)
                print(f"  [AVISO/ERRO ENV] {sanitized_f}")
                failures.append(f"Validação de .env falhou: {sanitized_f}")
        else:
            print("  - Validação de .env: OK")

        # Run test isolation check with PYTHONPATH set
        sub_env = os.environ.copy()
        sub_env["PYTHONPATH"] = str(BACKEND_DIR) + os.pathsep + sub_env.get("PYTHONPATH", "")
        iso_res = subprocess.run(
            [sys.executable, str(BACKEND_DIR / "scripts" / "check_test_isolation.py")],
            capture_output=True,
            text=True,
            check=False,
            env=sub_env,
        )
        if iso_res.returncode != 0:
            print("  - Isolamento dev/test: COLISÃO / CONFIGURAÇÃO INSEGURA DETECTADA")
            for line in iso_res.stdout.strip().splitlines():
                print(f"    {sanitize_text(line)}")
            failures.append("Ambiente de teste e desenvolvimento colidem (.env e .env.test)")
        else:
            print("  - Isolamento dev/test: OK (projetos e bancos isolados)")

    except Exception as err:
        err_msg = sanitize_text(str(err))
        print(f"  - Erro ao validar isolamento: {err_msg}")
        failures.append(f"Erro na execução da checagem de isolamento: {err_msg}")

    # Summary
    print("\n==================================================")
    if failures:
        print("STATUS FINAL: ERRO — Falhas de baseline detectadas:")
        for failure in failures:
            print(f"  - {sanitize_text(failure)}")
        print("==================================================")
        return 1

    print("STATUS FINAL: OK — Baseline verificado com sucesso.")
    print("==================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_checks())

