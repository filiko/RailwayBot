# Node.js Fix Workflow

## Handles
- Missing npm dependencies
- Lock file mismatches
- npm install failures
- Module resolution errors

## Fix Sequence

### 1. Missing Dependency (npm ERR! missing)

**Pattern:** `Cannot find module`, `npm ERR! missing`, `MODULE_NOT_FOUND`

**Diagnosis:**
```bash
# Get the package name from the error
# Error: Cannot find module 'express' → package = 'express'
```

**Fix Steps:**
1. Read `package.json`
2. Add the missing package with a compatible version range
3. Run `npm install` locally to verify
4. Update lock file
5. Commit

**Example fix:**
```python
# Read package.json
with open("package.json") as f:
    pkg = json.load(f)

# Add missing package (use semver compatible range)
if "express" not in pkg.get("dependencies", {}):
    pkg.setdefault("dependencies", {})["express"] = "^4.18.0"

# Write and install
with open("package.json", "w") as f:
    json.dump(pkg, f, indent=2)

subprocess.run(["npm", "install"], check=True)
```

### 2. npm Install Failure

**Pattern:** `npm install failed`, `npm ERR!`, `peer dep missing`

**Fix Steps:**
1. Clear npm cache: `npm cache clean --force`
2. Delete `package-lock.json` (if exists)
3. Run `npm install`
4. If private registry issue, check `.npmrc`
5. Commit lock file changes

### 3. Lock File Mismatch

**Pattern:** `package-lock.json changed`, `yarn.lock changed`

**Fix:**
```bash
npm install
git add package-lock.json
git commit -m "fix: update lock file"
```

### 4. Peer Dependency Warning

**Pattern:** `WARN unmet peer dependency`

**Fix:**
```bash
npm install --legacy-peer-deps
git add package-lock.json
git commit
```

## Pre-flight Checks

Before applying any fix, verify:
1. The repo is a git repo
2. There are no uncommitted changes (or stash them)
3. The fix doesn't break other packages

## Rollback

If a fix introduces new errors:
```bash
git stash
git checkout HEAD~1 -- package.json package-lock.json
npm install
```
