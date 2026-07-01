# Go Fix Workflow

## Handles
- Missing Go modules
- go mod tidy failures
- Build failures
- Import path issues

## Fix Sequence

### 1. Module Not Found

**Pattern:** `go: module not found`, `cannot find package`, `go get.*failed`

**Diagnosis:**
```bash
# From error: "cannot find package github.com/gin-gonic/gin in import path"
# → package = 'github.com/gin-gonic/gin'
```

**Fix Steps:**
1. Run `go mod tidy` to resolve dependencies
2. If that fails, manually `go get` the missing package
3. Commit `go.mod` and `go.sum` changes

**Example fix:**
```bash
go mod tidy
git add go.mod go.sum
git commit -m "fix: resolve go module dependencies"
```

### 2. Build Failure — Missing Dependencies

**Pattern:** `go build.*failed`, `go: go.mod file not found`

**Fix:**
```bash
# If no go.mod exists
go mod init <module-name>
go mod tidy
```

### 3. CGO Issues

**Pattern:** `go: CGO_ENABLED=0`, `gcc failed`, `could not find gcc`

**Fix for Railway (which doesn't support CGO by default):**
```bash
CGO_ENABLED=0 go build -o server .
```

Update `railway.json` or `railway.lua` to set `CGO_ENABLED=0` in the build environment.

### 4. Import Path Mismatch

**Pattern:** `import path.*does not match`, `package.*was changed`

**Fix:**
```bash
go mod tidy
```

## Pre-flight Checks

1. Verify `go.mod` exists and is valid
2. Check `go version` matches what the project expects
3. For Railway deployments, ensure `CGO_ENABLED=0`

## Railway-Specific Go Configuration

In `railway.json`:
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "CGO_ENABLED=0 go build -o server ."
  }
}
```

Or in `railway.lua`:
```lua
return railway {
    build = {
        builder = "NIXPACKS",
        buildCommand = "CGO_ENABLED=0 go build -o server .",
    },
}
```

## Rollback

```bash
git stash
git checkout HEAD~1 -- go.mod go.sum
go mod tidy
```
