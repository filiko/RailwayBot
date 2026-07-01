# Railway Fixer — Diagnosis Workflow

## Purpose
Diagnose Railway deployment failures and categorize errors to route to the appropriate fixer.

## Input
Deployment status from `railway status` + build/deploy logs from `railway logs`.

## Diagnosis Steps

### Step 1: Get Deployment Status
```bash
railway status
```
Parse the status — look for `FAILED`, `CRASHED`, `ERRORED`, `SUCCESS`.

### Step 2: Get Build Logs
```bash
railway logs --build
```
Parse for error patterns in build output.

### Step 3: Get Deploy Logs
```bash
railway logs
```
Parse for error patterns in deployment/runtime output.

### Step 4: Categorize Errors

Use the following error type taxonomy:

| Category | Error Patterns | Fixer |
|---|---|---|
| MISSING_DEP | `npm ERR! missing`, `Cannot find module`, `MODULE_NOT_FOUND`, `package not found` | npm_fixer / pip_fixer / go_fixer |
| ENV_VAR | `Environment variable .* not set`, `process.env.* undefined`, `KeyError:.*` | env_fixer |
| PORT_CONFLICT | `EADDRINUSE`, `Port already in use`, `address already in use` | port_fixer |
| BUILD_TIMEOUT | `Build timed out`, `Build aborted`, `context deadline exceeded` | build_timeout_fixer |
| DOCKER_BUILD | `Dockerfile error`, `failed to build`, `FROM image not found` | docker_fixer |
| LOCK_FILE | `package-lock.json`, `yarn.lock`, `Pipfile.lock`, `go.sum` mismatch | lock_fixer |
| PRISMA | `prisma generate`, `prisma migrate`, `Schema not found` | prisma_fixer |
| DRIZZLE | `drizzle-kit`, `drizzle generate` | drizzle_fixer |
| GO_MOD | `go: module not found`, `go mod tidy`, `cannot find package` | go_fixer |
| PYTHON_DEP | `pip install failed`, `PythonRequires-PythonVersion`, `SysRequirement` | pip_fixer |
| UNKNOWN | anything else | report to user |

### Step 5: Extract Error Context

For each error, extract:
- **File**: which file the error references
- **Line**: approximate line number
- **Error message**: the full error text
- **Context lines**: 5 lines before and after for stack traces

### Step 6: Route to Fixer

Pass categorized errors to the appropriate fixer module. Multiple errors may require multiple fixers in sequence.

## Error Output Schema

```json
{
  "deployment_id": "abc123",
  "status": "FAILED",
  "errors": [
    {
      "id": "err-1",
      "type": "MISSING_DEP",
      "message": "Cannot find module 'express'",
      "file": "package.json",
      "line": null,
      "context": ["...", "Cannot find module 'express'", "..."],
      "fixer": "npm_fixer",
      "fixable": true
    }
  ],
  "summary": "1 MISSING_DEP error — fixable by npm_fixer"
}
```

## Decision Rules

1. **If any error is unfixable** (syntax error in user code, API key missing, etc.) → flag for user escalation
2. **If all errors are fixable** → proceed to apply fixes
3. **If no errors detected but deployment failed** → check Railway status for runtime crashes
4. **If deployment succeeded** → exit with success
