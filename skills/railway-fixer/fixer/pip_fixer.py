import re
import subprocess
from pathlib import Path
from typing import Optional

from .base_fixer import BaseFixer, FixResult


class PipFixer(BaseFixer):
    PATTERNS = [
        r"No module named ['\"]?(\w+)['\"]?",
        r"ModuleNotFoundError",
        r"ImportError",
        r"pip install.*failed",
        r"PythonRequires-PythonVersion",
        r"Could not find a version that satisfies the requirement",
    ]

    def can_fix(self, error: dict) -> bool:
        msg = error.get("content", "").lower()
        return any(re.search(p, msg, re.IGNORECASE) for p in self.PATTERNS)

    def fix(self, error: dict) -> FixResult:
        req_file = self._find_requirements_file()
        if not req_file:
            return FixResult(False, False, "No requirements.txt found")

        package = self._extract_package(error.get("content", ""))
        if not package:
            return FixResult(False, False, f"Could not extract package from: {error.get('content')}")

        content = req_file.read_text()
        if package.lower() in content.lower():
            return FixResult(True, False, f"{package} already in requirements.txt")

        lines = content.rstrip().splitlines()
        lines.append(f"{package}>=1.0.0")
        req_file.write_text("\n".join(lines) + "\n")

        install_result = subprocess.run(
            ["pip", "install", "-r", str(req_file)],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )

        if install_result.returncode != 0:
            req_file.write_text(content)
            return FixResult(False, False, f"pip install failed: {install_result.stderr}")

        commit = self.commit_changes(f"fix: add missing dependency {package}")
        if not commit:
            return FixResult(True, True, f"Added {package} but could not commit")

        return FixResult(True, True, f"Added {package} and committed", files_changed=[str(req_file)], commit_sha=commit)

    def _find_requirements_file(self) -> Optional[Path]:
        for name in ["requirements.txt", "requirements-prod.txt", "requirements/prod.txt"]:
            path = self.repo_root / name
            if path.exists():
                return path
        return None

    def _extract_package(self, error_content: str) -> Optional[str]:
        patterns = [
            r"No module named ['\"]?(\w+)['\"]?",
            r"ModuleNotFoundError: No module named ['\"]?(\w+)['\"]?",
        ]
        for pattern in patterns:
            match = re.search(pattern, error_content, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
