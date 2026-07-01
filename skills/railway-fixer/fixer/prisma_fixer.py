import subprocess

from .base_fixer import BaseFixer, FixResult


class PrismaFixer(BaseFixer):
    PATTERNS = [
        r"prisma generate",
        r"prisma migrate",
        r"Schema not found",
        r"Cannot find Prisma Client",
        r"PrismaClient is not defined",
        r"Error loading schema",
    ]

    def can_fix(self, error: dict) -> bool:
        msg = error.get("content", "").lower()
        return any(p in msg for p in self.PATTERNS)

    def fix(self, error: dict) -> FixResult:
        prisma_dir = self.repo_root / "prisma"
        if not prisma_dir.exists():
            return FixResult(False, False, "No prisma directory found")

        schema = prisma_dir / "schema.prisma"
        if not schema.exists():
            return FixResult(False, False, "No schema.prisma found")

        result = subprocess.run(
            ["prisma", "generate"],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return FixResult(False, False, f"prisma generate failed: {result.stderr}")

        result = subprocess.run(
            ["prisma", "db", "push"],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return FixResult(False, False, f"prisma db push failed: {result.stderr}")

        commit = self.commit_changes("fix: regenerate Prisma client")
        if not commit:
            return FixResult(True, True, "Prisma client regenerated but could not commit")

        return FixResult(True, True, "Prisma client regenerated and committed", files_changed=["prisma/", "node_modules/.prisma"], commit_sha=commit)
