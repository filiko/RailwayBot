import json
import re
import subprocess
from pathlib import Path
from typing import Optional, Set

from .base_fixer import BaseFixer, FixResult


class EnvFixer(BaseFixer):
    PATTERNS = [
        r"Environment variable .* not set",
        r"process\.env\.\w+ is undefined",
        r"KeyError: ['\"]?(\w+)['\"]?",
        r"\$(\w+) is not defined",
        r"is not defined as an environment variable",
    ]

    STDLIB = {
        "os", "sys", "re", "json", "time", "datetime", "pathlib", "typing",
        "collections", "itertools", "functools", "math", "random", "uuid",
        "hashlib", "hmac", "base64", "binascii", "struct", "copy", "pprint",
        "io", "warnings", "abc", "ast", "argparse", "csv", "configparser",
        "ctypes", "errno", "gc", "inspect", "logging", "marshal", "pickle",
        " shelve", "socket", "sqlite3", "ssl", "threading", "tokenize",
        "traceback", "types", "unittest", "weakref", "webbrowser", "zipfile",
        "zlib", "platform", "subprocess", "sysconfig", "webbrowser",
    }

    NODE_STDLIB = {
        "fs", "path", "os", "http", "https", "url", "querystring", "util",
        "events", "stream", "buffer", "crypto", "tls", "ssl", "net", "dgram",
        "dns", "domain", "readline", "repl", "child_process", "cluster",
        "zlib", "querystring", "path", "string_decoder", "sys", "timers",
        "tty", "vm", "assert", "constants", "events", "fs", "http", "https",
        "net", "os", "path", "process", "punycode", "querystring", "url",
    }

    def can_fix(self, error: dict) -> bool:
        msg = error.get("content", "")
        return any(re.search(p, msg, re.IGNORECASE) for p in self.PATTERNS)

    def fix(self, error: dict) -> FixResult:
        env_key = self._extract_env_key(error.get("content", ""))
        if not env_key:
            return FixResult(False, False, f"Could not extract env var name from: {error.get('content')}")

        code_ref = self._find_env_usage(env_key)
        if not code_ref:
            return FixResult(False, False, f"Cannot find usage of {env_key} in code — may be a real secret")

        return FixResult(False, False, f"Env var {env_key} appears to be a user secret — requires user input")

    def _extract_env_key(self, content: str) -> Optional[str]:
        patterns = [
            r"Environment variable ['\"]?(\w+)['\"]? not set",
            r"KeyError: ['\"]?(\w+)['\"]?",
            r"\$(\w+) is not defined",
            r"process\.env\.(\w+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _find_env_usage(self, key: str) -> Optional[dict]:
        for py_file in self.repo_root.rglob("*.py"):
            content = py_file.read_text()
            if f"os.environ['{key}']" in content or f"os.environ[\"{key}\"]" in content:
                return {"file": str(py_file), "type": "python"}
            if f"os.getenv('{key}')" in content or f"os.getenv(\"{key}\")" in content:
                return {"file": str(py_file), "type": "python"}

        for js_file in list(self.repo_root.rglob("*.js")) + list(self.repo_root.rglob("*.ts")):
            content = js_file.read_text()
            if f"process.env.{key}" in content:
                return {"file": str(js_file), "type": "node"}

        return None
