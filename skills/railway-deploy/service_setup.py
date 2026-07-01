import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def check_railway_cli() -> bool:
    try:
        result = subprocess.run(
            ["railway", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_railway_cli() -> None:
    print("Installing Railway CLI...")
    subprocess.run(["npm", "i", "-g", "@railway/cli"], check=True)
    print("Railway CLI installed.")


def check_authenticated() -> bool:
    try:
        result = subprocess.run(
            ["railway", "whoami"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def create_services(repo_root: str, stack: dict) -> dict:
    repo_path = Path(repo_root)
    created = []

    if not check_railway_cli():
        install_railway_cli()

    if not check_authenticated():
        print("Not authenticated with Railway. Run 'railway login' first.")
        sys.exit(1)

    if "postgresql" in stack.get("database", []):
        print("Creating PostgreSQL service...")
        result = subprocess.run(
            ["railway", "add", "--database", "postgresql"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            created.append("postgresql")
            print("PostgreSQL service created.")
        else:
            print(f"PostgreSQL creation failed (may already exist): {result.stderr}")

    if "redis" in stack.get("cache", []):
        print("Creating Redis service...")
        result = subprocess.run(
            ["railway", "add", "--cache", "redis"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            created.append("redis")
            print("Redis service created.")
        else:
            print(f"Redis creation failed (may already exist): {result.stderr}")

    env_vars = fetch_railway_env(repo_path)

    return {
        "created": created,
        "env_vars": env_vars,
    }


def fetch_railway_env(repo_path: Path) -> dict:
    result = subprocess.run(
        ["railway", "environment", "list"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )
    env = {}
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def inject_env_vars(repo_root: str, env_vars: dict, stack: dict) -> None:
    repo_path = Path(repo_root)
    env_file = repo_path / ".env.railway"

    lines = ["# Railway Environment Variables", ""]
    for key, value in env_vars.items():
        if key in ("DATABASE_URL", "REDABASE_URL"):
            lines.append(f"{key}={value}")

    if "REDIS_URL" not in env_vars:
        env_vars.get("REDIS_URL", "")

    if env_file.exists():
        existing = env_file.read_text()
        lines = [existing.rstrip()] + lines

    env_file.write_text("\n".join(lines) + "\n")
    print(f"Environment variables written to {env_file}")


if __name__ == "__main__":
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    import subprocess
    result = subprocess.run(
        ["python", str(Path(__file__).parent / "detect_stack.py"), repo_root],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    stack = json.loads(result.stdout)
    result = create_services(repo_root, stack)
    print(json.dumps(result, indent=2))
