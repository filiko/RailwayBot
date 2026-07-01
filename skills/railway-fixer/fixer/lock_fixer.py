import re
import subprocess

from .base_fixer import BaseFixer, FixResult


class LockFixer(BaseFixer):
    PATTERNS = [
        r"package-lock\.json.*changed",
        r"yarn\.lock.*changed",
        r"go\.sum.*changed",
        r"Pipfile\.lock.*changed",
        r"requirements\.txt.*changed",
        r"lock file.*mismatch",
    ]

    def can_fix(self, error: dict) -> bool:
        msg = error.get("content", "").lower()
        return any(p in msg.lower() for p in self.PATTERNS)

    def fix(self, error: dict) -> FixResult:
        changed_files = self._detect_changed_lock_files()
        if not changed_files:
            return FixResult(False, False, "No lock files detected as changed")

        if (self.repo_root / "package-lock.json").exists():
            subprocess.run(["npm", "install"], cwd=str(self.repo_root), capture_output=True)
        elif (self.repo_root / "yarn.lock").exists():
            subprocess.run(["yarn", "install"], cwd=str(self.repo_root), capture_output=True)
        elif (self.repo_root / "go.sum").exists():
            subprocess.run(["go", "mod", "tidy"], cwd=str(self.repo_root), capture_output=True)

        commit = self.commit_changes(f"fix: update lock files")
        if not commit:
            return FixResult(True, True, "Lock files updated but could not commit", files_changed=changed_files)

        return FixResult(True, True, "Lock files updated and committed", files_changed=changed_files, commit_sha=commit)

    def _detect_changed_lock_files(self) -> list[str]:
        result = self.run_git("status", "--porcelain")
        lock_files = ["package-lock.json", "yarn.lock", "go.sum", "Pipfile.lock"]
        return [f for f in lock_files if f in result.stdout]
