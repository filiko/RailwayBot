# Agent Integration & Architecture

## Overview

RailwayBot is an automated monitoring tool for Railway deployments. It watches for
deployment failures, extracts and formats error messages, and exposes both a human
CLI and an **agent-friendly API** that coding agents (Claude, GitHub Copilot, or other
AI assistants) can call programmatically to check deployment status and get error
details.

## Architecture

### Component Structure

```
RailwayBot/
├── railwaybot/
│   ├── cli.py               # Main CLI entry point
│   ├── agent_api.py         # Agent-facing API
│   ├── railway_client.py    # Railway CLI wrapper
│   ├── log_parser.py        # Error extraction and formatting
│   ├── clipboard.py         # Clipboard operations
│   └── watcher.py           # Deployment monitoring
├── config.json               # User settings (auto-generated)
└── requirements.txt          # Dependencies
```

### Key Components

#### 1. RailwayClient (`railway_client.py`)
- **Purpose**: Wrapper around Railway CLI commands
- **Key Methods**: `get_status()`, `get_logs()`, `check_linked()`
- **Error Handling**: Wraps CLI errors in `RailwayClientError`

#### 2. LogParser (`log_parser.py`)
- **Purpose**: Extract and format error messages
- **Features**: Pattern matching for common error types, context extraction (lines before/after errors), configurable output formatting
- **Error Patterns**: npm errors, Python exceptions, port conflicts, module not found

#### 3. ClipboardManager (`clipboard.py`)
- **Purpose**: Handle clipboard operations and notifications
- **Features**: Cross-platform clipboard support via pyperclip, console notifications with colorama, optional sound notifications (Windows only)

#### 4. DeploymentWatcher (`watcher.py`)
- **Purpose**: Monitor Railway deployments
- **Modes**: Watch mode (continuous polling), one-shot (single status check)
- **Features**: Automatic error extraction on failure, exponential backoff on errors, graceful shutdown handling

#### 5. CLI Interface (`cli.py`)
- **Commands**: `watch`, `check`, `config`, `test`

### Error Flow

1. **Detection**: Watcher polls Railway status every N seconds
2. **Trigger**: Status changes to FAILED/CRASHED/ERRORED
3. **Extraction**: Fetch build logs (`railway logs --build`) and deploy logs (`railway logs`)
4. **Parsing**: Apply regex patterns to identify errors, extract surrounding context
5. **Formatting**: Format with headers, timestamps, service info; limit to `max_lines_per_error`
6. **Output**: Copy to clipboard (if `auto_copy` enabled), show notification

### Extension Points

**Adding error patterns** — edit `railwaybot/log_parser.py` → `LogParser.ERROR_PATTERNS`:
```python
ERROR_PATTERNS = [
    r'(?i)error:?\s+(.+)',
    r'your-custom-pattern',
]
```

**Custom notifications** — extend `railwaybot/clipboard.py` → `ClipboardManager`:
```python
def _show_notification(self, text: str) -> None:
    # e.g. Windows toast, desktop notification, etc.
    pass
```

**Additional Railway commands** — extend `railwaybot/railway_client.py` → `RailwayClient`:
```python
def redeploy(self) -> None:
    """Trigger a redeployment."""
    self._run_command(["redeploy", "-y"])
```

## Configuration

Stored in `config.json`:

```json
{
  "railway": {
    "token_env_var": "RAILWAY_TOKEN",
    "poll_interval_seconds": 5,
    "auto_copy": true
  },
  "formatting": {
    "include_timestamps": true,
    "max_lines_per_error": 50,
    "highlight_keywords": ["error", "failed", "exception"]
  },
  "notifications": {
    "enabled": true,
    "sound": false
  }
}
```

## Skills

Three skills are scaffolded under `skills/` for full Railway lifecycle automation. They
are registered as:
- Claude Code slash commands: `~/.claude/commands/railway-*.md`
- Opencode agents: `.opencode/agents/railway-*.md`

### `/railway-deploy` — Deploy a repo to Railway

**Trigger:** "deploy my repo to Railway", "setup railway for <repo>", "railway deploy"

Full first-time deployment workflow:
1. `python skills/railway-deploy/detect_stack.py <repo-path>` — detect runtime/framework/DB
2. `python skills/railway-deploy/config_generator.py <repo-path> <template>` — generate configs
3. `python skills/railway-deploy/service_setup.py <repo-path>` — provision PostgreSQL/Redis
4. `railway variables set PORT=<port>`
5. `git add railway.json railway.lua Dockerfile && railway up`
6. Auto-chains → `railway-fixer`

**Templates available:** `django-postgres`, `fastapi-postgres`, `go-gin-postgres`, `node-express-postgres`, `node-nextjs`

### `/railway-fixer` — Autonomous deployment fixer

**Trigger:** "fix my railway deploy", "railway is failing", "railway-fixer"

Background sub-agent. Runs the diagnose → fix → commit → redeploy loop until success or escalation.

```bash
python skills/railway-fixer/fixer_orchestrator.py <repo-path>
```

Exit signals: `SUCCESS` (2 consecutive clean deploys) | `ESCALATE` (3 failed fixes per error type)

Fixer modules: `npm_fixer`, `pip_fixer`, `go_fixer`, `env_fixer`, `port_fixer`, `prisma_fixer`, `lock_fixer`, `build_timeout_fixer`

### `/railway-manage` — Post-deploy ops

**Trigger:** "railway logs", "rollback railway", "railway env", "railway scale", "railway migrate"

Day-2 operations after a successful deploy:
```bash
railway logs [--build] [--service <name>]
railway variables set|list|delete
railway rollback --deployment-id <id>
railway scale --replicas <n>
railway run <migration-command>
```

### Skills file layout

```
skills/
├── railway-deploy/
│   ├── skill.yaml
│   ├── detect_stack.py
│   ├── config_generator.py
│   ├── service_setup.py
│   ├── workflow.md
│   └── templates/
│       ├── django-postgres/    {Dockerfile, railway.json, railway.lua}
│       ├── fastapi-postgres/   {Dockerfile, railway.json, railway.lua}
│       ├── go-gin-postgres/    {Dockerfile, railway.json, railway.lua}
│       ├── node-express-postgres/ {Dockerfile, railway.json, railway.lua}
│       └── node-nextjs/        {railway.json, railway.lua}
├── railway-fixer/
│   ├── skill.yaml
│   ├── fixer_orchestrator.py
│   ├── fixer/
│   │   ├── base_fixer.py
│   │   ├── npm_fixer.py, pip_fixer.py, go_fixer.py
│   │   ├── env_fixer.py, port_fixer.py, prisma_fixer.py
│   │   └── lock_fixer.py, build_timeout_fixer.py
│   └── workflows/
│       └── diagnose.md, node-fix.md, python-fix.md, go-fix.md
└── railway-manage/
    ├── skill.yaml
    └── workflow.md
```

## Agent API (Programmatic Access)

### Installation

```bash
cd RailwayBot
pip install -e .
```

This enables `python -m railwaybot.agent_api` and creates the `railwaybot-agent` entry point.

### Usage Modes

**JSON output (for agent parsing):**
```bash
python -m railwaybot.agent_api
# or: railwaybot-agent
```
```json
{
  "status": "failed",
  "deployment": {
    "id": "abc123",
    "status": "FAILED",
    "service": "my-api",
    "environment": "production"
  },
  "errors": {
    "build": [
      {
        "line_number": 45,
        "content": "npm ERR! missing dependency: express@^4.0.0",
        "type": "BUILD",
        "timestamp": "14:20:15",
        "context": ["...", "...", "..."]
      }
    ],
    "deploy": [...]
  },
  "formatted_report": "=== Railway Deployment Failed ===\n...",
  "message": "Deployment FAILED"
}
```

**Brief summary (for quick checks):**
```bash
python -m railwaybot.agent_api --summary
```
```
❌ Deployment Failed - 3 build errors, 1 deploy errors
```

**Human-readable text:**
```bash
python -m railwaybot.agent_api --format text
```

### Integration Examples

**Python coding agent:**
```python
import subprocess
import json

def check_railway_deployment():
    result = subprocess.run(
        ["python", "-m", "railwaybot.agent_api"],
        capture_output=True,
        text=True,
        cwd="/path/to/RailwayBot"
    )
    data = json.loads(result.stdout)

    if data["status"] == "failed":
        for error in data["errors"]["build"]:
            print(f"Found error at line {error['line_number']}: {error['content']}")
            if "missing dependency" in error["content"]:
                fix_missing_dependency(error)
            elif "MODULE_NOT_FOUND" in error["content"]:
                fix_missing_module(error)

    return data
```

**Shell script integration:**
```bash
#!/bin/bash
echo "Deploying to Railway..."
railway up

echo "Checking deployment status..."
STATUS=$(python -m railwaybot.agent_api --summary)

if [[ $STATUS == *"Failed"* ]]; then
    python -m railwaybot.agent_api --format text > deployment_errors.txt
    cat deployment_errors.txt | codex "Fix these Railway deployment errors"
else
    echo "Deployment successful!"
fi
```

**Custom tool wrapper (any agent framework, e.g. a Dart/Flutter tool registry):**
```dart
class RailwayTool extends Tool {
  @override
  String get name => 'check_railway';

  @override
  String get description => 'Check Railway deployment status and get errors';

  @override
  Future<String> execute(Map<String, dynamic> args) async {
    final result = await Process.run(
      'python',
      ['-m', 'railwaybot.agent_api'],
      workingDirectory: '/path/to/RailwayBot',
    );

    final data = jsonDecode(result.stdout);

    if (data['status'] == 'failed') {
      return data['formatted_report'];
    }
    return 'Deployment status: ${data['deployment']['status']}';
  }
}
```

**Node.js agent:**
```javascript
const { execSync } = require('child_process');

async function checkRailwayDeployment() {
    try {
        const output = execSync(
            'python -m railwaybot.agent_api',
            { cwd: '/path/to/RailwayBot', encoding: 'utf8' }
        );
        const result = JSON.parse(output);

        if (result.status === 'failed') {
            const buildErrors = result.errors.build;
            const errorTypes = buildErrors.map(e => detectErrorType(e.content));
            for (const errorType of errorTypes) {
                await applyFix(errorType);
            }
        }
        return result;
    } catch (error) {
        console.error('Failed to check deployment:', error);
    }
}

function detectErrorType(errorContent) {
    if (errorContent.includes('missing dependency')) return 'missing_dep';
    if (errorContent.includes('MODULE_NOT_FOUND')) return 'missing_module';
    if (errorContent.includes('EADDRINUSE')) return 'port_conflict';
}
```

### JSON Response Structure

**Success:**
```json
{
  "status": "ok",
  "deployment": {"id": "deploy-123", "status": "SUCCESS", "service": "my-service", "environment": "production"},
  "errors": {"build": [], "deploy": []},
  "formatted_report": "",
  "message": "Deployment status: SUCCESS"
}
```

**Error (not linked / no project):**
```json
{
  "status": "error",
  "deployment": null,
  "errors": {"build": [], "deploy": []},
  "formatted_report": "",
  "message": "Not linked to a Railway project. Run 'railway link' in your project directory."
}
```

### Common Agent Workflows

**Deploy → Check → Fix loop:**
```python
def autonomous_deployment_fix():
    max_attempts = 5
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        subprocess.run(["railway", "up"])
        time.sleep(10)

        result = get_railway_status()
        if result["status"] == "ok":
            break
        if result["status"] == "failed":
            fixes_applied = analyze_and_fix_errors(result["errors"])
            if not fixes_applied:
                break
            continue

    return result
```

**Continuous monitoring:**
```python
def continuous_monitor():
    last_status = None
    while True:
        result = get_railway_status()
        current_status = result.get("deployment", {}).get("status")
        if current_status != last_status:
            if result["status"] == "failed":
                auto_fix_deployment(result)
        last_status = current_status
        time.sleep(5)
```

### Python API Direct Import

```python
from railwaybot.agent_api import AgentAPI

api = AgentAPI()
result = api.check_deployment()

if result["status"] == "failed":
    for error in result["errors"]["build"]:
        print(f"Line {error['line_number']}: {error['content']}")

summary = api.get_error_summary()
print(summary)  # "❌ Deployment Failed - 3 build errors, 1 deploy errors"
```

### Best Practices

1. **Check before acting** — always check deployment status before attempting fixes
2. **Parse structured errors** — use the JSON output for precise error identification
3. **Implement retry logic** — deployments can have transient failures
4. **Limit attempts** — prevent infinite loops with a max retry count
5. **Log actions** — keep track of what fixes were attempted
6. **Validate fixes** — ensure fixes don't introduce new issues

### Error Pattern Detection

| Pattern | Description | Typical Fix |
|---------|-------------|-------------|
| `npm ERR! missing dependency` | Missing npm package | Add to package.json |
| `MODULE_NOT_FOUND` | Missing Node module | Add import statement |
| `EADDRINUSE` | Port already in use | Change port or kill process |
| `pip install failed` | Python dependency issue | Update requirements.txt |
| `build failed` | Compilation error | Fix syntax/type errors |
| `cannot find module` | Missing file | Create missing file |

## Testing Checklist

- [ ] Railway CLI installed and authenticated
- [ ] Project linked via `railway link`
- [ ] Config file created (auto-generated on first run)
- [ ] Watch mode detects deployment changes
- [ ] Errors copied to clipboard on failure
- [ ] One-shot check works
- [ ] Configuration changes respected
- [ ] Graceful shutdown (Ctrl+C)

## Troubleshooting

**"Railway CLI not found"** — Install: `npm i -g @railway/cli`; verify: `railway --version`

**"Not linked to a Railway project"** — Run `railway link` in the project directory

**"Too many consecutive errors"** — Check `railway whoami`, check network connection, verify `RAILWAY_TOKEN` if using token auth

## Development Notes

- Type hints for all function parameters and returns
- Docstrings for all public methods
- Error handling via custom exceptions
- Configuration-driven behavior
- Manual testing against real Railway deployments; test build/deploy/runtime failure modes

## Future Enhancements

- Web dashboard for error history
- Real-time WebSocket API for live deployment monitoring
- Error prediction based on code changes, auto-fix suggestions with confidence scores
- Email/Slack notifications
- Multi-project / monorepo support

## Version History

- **v0.1.0** (2026-02-26): Initial implementation — watch mode monitoring, error extraction and formatting, clipboard integration, configurable settings
- **v0.2.0** (2026-04-18): Skills added — `railway-deploy` (full first-time deploy workflow), `railway-fixer` (autonomous self-healing sub-agent), `railway-manage` (post-deploy ops: logs, env, rollback, scale, migrate)
