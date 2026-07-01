import json
import re
import subprocess
from pathlib import Path
from typing import Optional

from .base_fixer import BaseFixer, FixResult


class NpmFixer(BaseFixer):
    PATTERNS = [
        r"Cannot find module ['\"]([^'\"]+)['\"]",
        r"npm ERR! missing (?:package )?['\"]?([^'\"\s]+)['\"]?",
        r"MODULE_NOT_FOUND",
        r"package ['\"]([^'\"]+)['\"] not found",
    ]

    def can_fix(self, error: dict) -> bool:
        msg = error.get("content", "").lower()
        return any(
            re.search(p, msg, re.IGNORECASE)
            for p in self.PATTERNS
        )

    def fix(self, error: dict) -> FixResult:
        pkg_json = self.repo_root / "package.json"
        if not pkg_json.exists():
            return FixResult(False, False, "No package.json found")

        pkg = json.loads(pkg_json.read_text())

        package = self._extract_package(error.get("content", ""))
        if not package:
            return FixResult(False, False, f"Could not extract package name from: {error.get('content')}")

        if package in pkg.get("dependencies", {}) or package in pkg.get("devDependencies", {}):
            return FixResult(True, False, f"Package {package} already in package.json — lock file issue")

        pkg.setdefault("dependencies", {})[package] = self._guess_version(package)
        pkg_json.write_text(json.dumps(pkg, indent=2))

        install_result = subprocess.run(
            ["npm", "install"],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )

        if install_result.returncode != 0:
            pkg_json.write_text(json.dumps(pkg, indent=2))
            return FixResult(False, False, f"npm install failed: {install_result.stderr}")

        commit = self.commit_changes(f"fix: add missing dependency {package}")
        if not commit:
            return FixResult(True, True, f"Added {package} but could not commit")

        return FixResult(True, True, f"Added {package} and committed", files_changed=["package.json"], commit_sha=commit)

    def _extract_package(self, error_content: str) -> Optional[str]:
        for pattern in self.PATTERNS:
            match = re.search(pattern, error_content, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else None
        return None

    def _guess_version(self, package: str) -> str:
        known = {
            "express": "^4.18.0",
            "cors": "^2.8.5",
            "dotenv": "^16.0.0",
            "helmet": "^7.0.0",
            "jsonwebtoken": "^9.0.0",
            "bcrypt": "^5.1.0",
            "pg": "^8.11.0",
            "redis": "^4.6.0",
            "ioredis": "^5.3.0",
            "zod": "^3.22.0",
            "axios": "^1.6.0",
        }
        return known.get(package, "^1.0.0")
