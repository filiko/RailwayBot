# Python Fix Workflow

## Handles
- Missing pip packages
- Python version mismatches
- pip install failures
- requirements.txt issues

## Fix Sequence

### 1. Missing Package (pip install failed)

**Pattern:** `ModuleNotFoundError`, `ImportError`, `No module named`, `pip install.*failed`

**Diagnosis:**
```python
# Error: No module named 'fastapi' → package = 'fastapi'
# Error: ModuleNotFoundError: No module named 'pydantic' → package = 'pydantic'
```

**Fix Steps:**
1. Try to infer package name from error (`fastapi` from `No module named 'fastapi'`)
2. Add to `requirements.txt` with compatible version
3. Verify: `pip install -r requirements.txt`
4. Commit

**Example fix:**
```python
import re

def fix_missing_package(error_message: str):
    match = re.search(r"No module named '(\w+)'", error_message)
    if not match:
        match = re.search(r"ModuleNotFoundError: No module named '(\w+)'", error_message)
    if not match:
        return None

    package = match.group(1)
    req_file = Path("requirements.txt")

    if req_file.exists():
        content = req_file.read_text()
        if package not in content:
            content += f"\n{package}>=1.0.0"
            req_file.write_text(content)

    return package
```

### 2. Python Version Mismatch

**Pattern:** `PythonRequires-PythonVersion`, `requires Python X.Y but found X.Z`

**Fix:**
```toml
# pyproject.toml or setup.py
python_requires='>=3.8'
```

### 3. pip Install Failure — Build Errors

**Pattern:** `error: Microsoft Visual C++ required`, `error: gcc failed`, `wheel`

**Fix:**
```bash
# Try installing with pre-built wheels
pip install --only-binary :all: -r requirements.txt

# If that fails, try:
pip install --no-cache-dir -r requirements.txt
```

### 4. requirements.txt Issues

**Common issues:**
- Extra whitespace / empty lines
- Incompatible version specifiers
- Missing version for a package that requires compilation

**Fix:**
```python
# Clean requirements.txt
cleaned = []
for line in requirements_content.splitlines():
    line = line.strip()
    if line and not line.startswith("#"):
        clean_line = line.split(";")[0].strip()
        cleaned.append(clean_line)

cleaned_requirements = "\n".join(cleaned) + "\n"
```

### 5. Missing Dependency in Code (Import Detection)

**Pattern:** The error references a module import in source code

**Fix:**
```python
# Find all import statements in the repo
# Detect which packages are imported but not in requirements.txt
import re

IMPORT_PATTERN = re.compile(r'^(?:from|import)\s+(\w+)', re.MULTILINE)

def find_missing_packages(repo_path: str) -> list[str]:
    req_path = Path(repo_path) / "requirements.txt"
    if req_path.exists():
        reqs = req_path.read_text().lower()
    else:
        reqs = ""

    imported = set()
    for py_file in Path(repo_path).rglob("*.py"):
        for match in IMPORT_PATTERN.finditer(py_file.read_text()):
            imported.add(match.group(1))

    stdlib = {"os", "sys", "re", "json", "time", "datetime", "pathlib", "typing", ...}
    return [pkg for pkg in imported if pkg.lower() not in reqs and pkg not in stdlib]
```

## Pre-flight Checks

1. Verify Python version compatibility
2. Check for `pyproject.toml`, `setup.py`, `Pipfile` — may override requirements.txt
3. Always pin versions to avoid supply chain issues

## Rollback

```bash
git stash
git checkout HEAD~1 -- requirements.txt
pip install -r requirements.txt
```
