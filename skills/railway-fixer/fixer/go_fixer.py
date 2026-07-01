import subprocess

from .base_fixer import BaseFixer, FixResult


class GoFixer(BaseFixer):
    PATTERNS = [
        r"go: module not found",
        r"cannot find package",
        r"go mod tidy",
        r"go get.*failed",
        r"could not find go.mod",
    ]

    def can_fix(self, error: dict) -> bool:
        msg = error.get("content", "").lower()
        return any(p in msg for p in self.PATTERNS)

    def fix(self, error: dict) -> FixResult:
        go_mod = self.repo_root / "go.mod"
        if not go_mod.exists():
            return FixResult(False, False, "No go.mod found — cannot auto-fix")

        result = subprocess.run(
            ["go", "mod", "tidy"],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return FixResult(False, False, f"go mod tidy failed: {result.stderr}")

        commit = self.commit_changes("fix: resolve go module dependencies")
        if not commit:
            return FixResult(True, True, "go mod tidy succeeded but could not commit", files_changed=["go.mod", "go.sum"])

        return FixResult(True, True, "Resolved go module dependencies", files_changed=["go.mod", "go.sum"], commit_sha=commit)
