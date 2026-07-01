import subprocess

from .base_fixer import BaseFixer, FixResult


class BuildTimeoutFixer(BaseFixer):
    PATTERNS = [
        r"Build timed out",
        r"Build aborted",
        r"context deadline exceeded",
        r"Build failed: context timeout",
    ]

    def can_fix(self, error: dict) -> bool:
        msg = error.get("content", "").lower()
        return any(p in msg.lower() for p in self.PATTERNS)

    def fix(self, error: dict) -> FixResult:
        railway_lua = self.repo_root / "railway.lua"
        railway_json = self.repo_root / "railway.json"

        if railway_lua.exists():
            content = railway_lua.read_text()
            if "timeout" not in content.lower():
                new_content = content.rstrip() + "\n    timeout = 300,\n"
                railway_lua.write_text(new_content)
                commit = self.commit_changes("fix: increase build timeout")
                if commit:
                    return FixResult(True, True, "Increased build timeout in railway.lua", files_changed=["railway.lua"], commit_sha=commit)
                return FixResult(True, True, "Increased build timeout but could not commit", files_changed=["railway.lua"])

        if railway_json.exists():
            import json
            try:
                cfg = json.loads(railway_json.read_text())
                if "build" not in cfg:
                    cfg["build"] = {}
                cfg["build"]["timeout"] = 300
                railway_json.write_text(json.dumps(cfg, indent=2))
                commit = self.commit_changes("fix: increase build timeout to 300s")
                if commit:
                    return FixResult(True, True, "Increased build timeout to 300s", files_changed=["railway.json"], commit_sha=commit)
                return FixResult(True, True, "Increased build timeout but could not commit", files_changed=["railway.json"])
            except json.JSONDecodeError:
                pass

        return FixResult(False, False, "No railway.lua or railway.json found to adjust timeout")
