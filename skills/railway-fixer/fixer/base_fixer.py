from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import subprocess


@dataclass
class FixResult:
    success: bool
    applied_fix: bool
    message: str
    files_changed: List[str] = field(default_factory=list)
    commit_sha: Optional[str] = None


class BaseFixer(ABC):
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)

    @abstractmethod
    def can_fix(self, error: dict) -> bool:
        raise NotImplementedError

    @abstractmethod
    def fix(self, error: dict) -> FixResult:
        raise NotImplementedError

    def run_git(self, *args, **kwargs) -> subprocess.CompletedProcess:
        kwargs.setdefault("cwd", str(self.repo_root))
        kwargs.setdefault("capture_output", True)
        kwargs.setdefault("text", True)
        return subprocess.run(["git"] + list(args), **kwargs)

    def has_uncommitted_changes(self) -> bool:
        result = self.run_git("status", "--porcelain")
        return bool(result.stdout.strip())

    def commit_changes(self, message: str) -> Optional[str]:
        result = self.run_git("add", "-A")
        if result.returncode != 0:
            return None

        result = self.run_git("commit", "-m", message)
        if result.returncode != 0:
            return None

        return result.stdout.strip()

    def push_changes(self) -> bool:
        result = self.run_git("push")
        return result.returncode == 0
