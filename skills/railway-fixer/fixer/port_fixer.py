import json
import re
import subprocess
from pathlib import Path

from .base_fixer import BaseFixer, FixResult


class PortFixer(BaseFixer):
    PATTERNS = [
        r"EADDRINUSE",
        r"Port \d+ already in use",
        r"address already in use",
        r"listen EACCES: permission denied.*:\d+",
    ]

    def can_fix(self, error: dict) -> bool:
        msg = error.get("content", "")
        return any(re.search(p, msg, re.IGNORECASE) for p in self.PATTERNS)

    def fix(self, error: dict) -> FixResult:
        railway_json = self.repo_root / "railway.json"
        railway_lua = self.repo_root / "railway.lua"
        dockerfile = self.repo_root / "Dockerfile"

        detected_port = self._extract_port(error.get("content", ""))

        changed = []

        if dockerfile.exists():
            content = dockerfile.read_text()
            new_content = re.sub(r"EXPOSE\s+\d+", f"EXPOSE {detected_port}", content)
            new_content = re.sub(r"ENV\s+PORT=?\d+", f"ENV PORT={detected_port}", new_content)
            if new_content != content:
                dockerfile.write_text(new_content)
                changed.append("Dockerfile")

        if railway_json.exists():
            try:
                cfg = json.loads(railway_json.read_text())
                if "deploy" in cfg and "healthcheckPort" in cfg["deploy"]:
                    cfg["deploy"]["healthcheckPort"] = detected_port
                if "deploy" in cfg and "startCommand" in cfg["deploy"]:
                    cfg["deploy"]["startCommand"] = re.sub(
                        r"--port\s+\$?PORT|\$PORT",
                        f"--port ${detected_port}",
                        cfg["deploy"]["startCommand"],
                    )
                railway_json.write_text(json.dumps(cfg, indent=2))
                changed.append("railway.json")
            except json.JSONDecodeError:
                pass

        if not changed:
            return FixResult(False, False, "Could not find port config file to fix")

        commit = self.commit_changes(f"fix: update port to {detected_port}")
        if not commit:
            return FixResult(True, True, f"Updated port to {detected_port} but could not commit", files_changed=changed)

        return FixResult(True, True, f"Updated port to {detected_port}", files_changed=changed, commit_sha=commit)

    def _extract_port(self, content: str) -> int:
        match = re.search(r"(\d+)", content)
        return int(match.group(1)) if match else 3000
