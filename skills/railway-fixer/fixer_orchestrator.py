import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

FIXER_DIR = Path(__file__).parent
FIXER_MODULE_DIR = FIXER_DIR / "fixer"

sys.path.insert(0, str(FIXER_DIR))

MAX_RETRIES_PER_ERROR = 3
POLL_INTERVAL = 10
SUCCESS_THRESHOLD = 2


@dataclass
class ErrorEntry:
    id: str
    type: str
    message: str
    fixer_name: str
    fixable: bool
    attempts: int = 0


def check_railway_status() -> dict:
    result = subprocess.run(
        ["railwaybot-agent"],
        capture_output=True,
        text=True,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "error", "message": result.stdout + result.stderr}


def get_logs() -> dict:
    build_result = subprocess.run(
        ["railway", "logs", "--build"],
        capture_output=True,
        text=True,
    )
    deploy_result = subprocess.run(
        ["railway", "logs"],
        capture_output=True,
        text=True,
    )
    return {
        "build": build_result.stdout,
        "deploy": deploy_result.stdout,
    }


def diagnose(errors: List[dict]) -> List[ErrorEntry]:
    from fixer.npm_fixer import NpmFixer
    from fixer.pip_fixer import PipFixer
    from fixer.go_fixer import GoFixer
    from fixer.env_fixer import EnvFixer
    from fixer.port_fixer import PortFixer
    from fixer.prisma_fixer import PrismaFixer
    from fixer.lock_fixer import LockFixer
    from fixer.build_timeout_fixer import BuildTimeoutFixer

    fixers = [
        ("npm_fixer", NpmFixer(".")),
        ("pip_fixer", PipFixer(".")),
        ("go_fixer", GoFixer(".")),
        ("env_fixer", EnvFixer(".")),
        ("port_fixer", PortFixer(".")),
        ("prisma_fixer", PrismaFixer(".")),
        ("lock_fixer", LockFixer(".")),
        ("build_timeout_fixer", BuildTimeoutFixer(".")),
    ]

    entries = []
    for i, error in enumerate(errors):
        entry = ErrorEntry(
            id=f"err-{i}",
            type="UNKNOWN",
            message=error.get("content", ""),
            fixer_name="",
            fixable=False,
        )

        for fixer_name, fixer in fixers:
            if fixer.can_fix(error):
                entry.type = fixer_name.upper().replace("_FIXER", "")
                entry.fixer_name = fixer_name
                entry.fixable = True
                break

        entries.append(entry)

    return entries


def apply_fix(error_entry: ErrorEntry, error: dict, repo_root: str) -> dict:
    from fixer.npm_fixer import NpmFixer
    from fixer.pip_fixer import PipFixer
    from fixer.go_fixer import GoFixer
    from fixer.env_fixer import EnvFixer
    from fixer.port_fixer import PortFixer
    from fixer.prisma_fixer import PrismaFixer
    from fixer.lock_fixer import LockFixer
    from fixer.build_timeout_fixer import BuildTimeoutFixer

    fixer_map = {
        "npm_fixer": NpmFixer(repo_root),
        "pip_fixer": PipFixer(repo_root),
        "go_fixer": GoFixer(repo_root),
        "env_fixer": EnvFixer(repo_root),
        "port_fixer": PortFixer(repo_root),
        "prisma_fixer": PrismaFixer(repo_root),
        "lock_fixer": LockFixer(repo_root),
        "build_timeout_fixer": BuildTimeoutFixer(repo_root),
    }

    fixer = fixer_map.get(error_entry.fixer_name)
    if not fixer:
        return {"success": False, "message": f"No fixer for {error_entry.fixer_name}"}

    return asdict(fixer.fix(error))


def trigger_redeploy() -> bool:
    result = subprocess.run(
        ["railway", "up"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def wait_for_deploy() -> str:
    for _ in range(60):
        status_data = check_railway_status()
        deployment_status = status_data.get("deployment", {}).get("status", "").upper()
        if deployment_status in ("SUCCESS", "FAILED", "CRASHED", "ERRORED"):
            return deployment_status
        time.sleep(POLL_INTERVAL)
    return "TIMEOUT"


def run_fix_loop(repo_root: str) -> str:
    consecutive_success = 0

    print(f"[railway-fixer] Starting autonomous fix loop in {repo_root}")
    print(f"[railway-fixer] Max retries per error: {MAX_RETRIES_PER_ERROR}")

    while True:
        status_data = check_railway_status()
        deployment_status = status_data.get("deployment", {}).get("status", "").upper()

        print(f"[railway-fixer] Current status: {deployment_status}")

        if deployment_status == "SUCCESS":
            consecutive_success += 1
            print(f"[railway-fixer] Success count: {consecutive_success}/{SUCCESS_THRESHOLD}")
            if consecutive_success >= SUCCESS_THRESHOLD:
                print("[railway-fixer] Deployment stable. Exiting.")
                return "SUCCESS"
        else:
            consecutive_success = 0

        if deployment_status in ("FAILED", "CRASHED", "ERRORED"):
            print("[railway-fixer] Deployment failed. Diagnosing...")
            logs = get_logs()
            all_errors = status_data.get("errors", {}).get("build", []) + status_data.get("errors", {}).get("deploy", [])

            if not all_errors:
                print("[railway-fixer] No structured errors found. Checking raw logs...")
                print(logs.get("build", "")[:500])
                print(logs.get("deploy", "")[:500])

            error_entries = diagnose(all_errors)

            for entry in error_entries:
                print(f"[railway-fixer] Error: {entry.type} — {entry.message[:100]}")

            fixed_any = False
            for entry, error in zip(error_entries, all_errors):
                if not entry.fixable:
                    print(f"[railway-fixer] Unfixable error: {entry.message[:100]}")
                    continue

                if entry.attempts >= MAX_RETRIES_PER_ERROR:
                    print(f"[railway-fixer] Max retries reached for {entry.type}. Escalating.")
                    return f"ESCALATE: {entry.message}"

                print(f"[railway-fixer] Applying {entry.fixer_name}...")
                result = apply_fix(entry, error, repo_root)
                entry.attempts += 1

                if result.get("success") and result.get("applied_fix"):
                    print(f"[railway-fixer] Fix applied: {result.get('message')}")
                    fixed_any = True

                    print("[railway-fixer] Triggering redeploy...")
                    if trigger_redeploy():
                        final_status = wait_for_deploy()
                        if final_status == "SUCCESS":
                            consecutive_success += 1
                            if consecutive_success >= SUCCESS_THRESHOLD:
                                return "SUCCESS"
                        elif final_status != "TIMEOUT":
                            print(f"[railway-fixer] Redeploy resulted in: {final_status}")
                    else:
                        print("[railway-fixer] Failed to trigger redeploy")
                else:
                    print(f"[railway-fixer] Fix not applied: {result.get('message')}")

            if not fixed_any and error_entries:
                all_maxed = all(e.attempts >= MAX_RETRIES_PER_ERROR for e in error_entries if e.fixable)
                if all_maxed:
                    print("[railway-fixer] All fixable errors exhausted. Escalating.")
                    return "ESCALATE: all fix attempts exhausted"

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    result = run_fix_loop(repo_root)
    print(json.dumps({"result": result}))
    sys.exit(0 if result == "SUCCESS" else 1)
