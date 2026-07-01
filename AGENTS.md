# RailwayBot Agent Documentation

## Overview

RailwayBot is an automated monitoring tool for Railway deployments. It watches for deployment failures and automatically extracts and formats error messages for easy pasting into coding assistants.

## Architecture

### Component Structure

```
RailwayBot/
├── src/
│   ├── cli.py              # Main CLI entry point
│   ├── railway_client.py   # Railway CLI wrapper
│   ├── log_parser.py       # Error extraction and formatting
│   ├── clipboard.py        # Clipboard operations
│   └── watcher.py          # Deployment monitoring
├── config.json             # User settings (auto-generated)
└── requirements.txt        # Dependencies
```

### Key Components

#### 1. RailwayClient (railway_client.py)
- **Purpose**: Wrapper around Railway CLI commands
- **Key Methods**:
  - `get_status()` - Fetch deployment status
  - `get_logs()` - Retrieve build/deploy logs
  - `check_linked()` - Verify project link
- **Error Handling**: Wraps CLI errors in `RailwayClientError`

#### 2. LogParser (log_parser.py)
- **Purpose**: Extract and format error messages
- **Features**:
  - Pattern matching for common error types
  - Context extraction (lines before/after errors)
  - Configurable output formatting
- **Error Patterns**: npm errors, Python exceptions, port conflicts, module not found

#### 3. ClipboardManager (clipboard.py)
- **Purpose**: Handle clipboard operations and notifications
- **Features**:
  - Cross-platform clipboard support via pyperclip
  - Console notifications with colorama
  - Optional sound notifications (Windows only)

#### 4. DeploymentWatcher (watcher.py)
- **Purpose**: Monitor Railway deployments
- **Modes**:
  - Watch mode: Continuous monitoring with polling
  - One-shot: Single status check
- **Features**:
  - Automatic error extraction on failure
  - Exponential backoff on errors
  - Graceful shutdown handling

#### 5. CLI Interface (cli.py)
- **Purpose**: Main entry point and configuration
- **Commands**:
  - `watch` - Start monitoring
  - `check` - One-shot check
  - `config` - Show configuration
  - `test` - Test Railway connection

## Configuration

Configuration is stored in `config.json`:

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

## Usage Patterns

### Basic Watch Mode
```bash
cd /path/to/railway/project
python C:\...\RailwayBot\src\cli.py watch
```

### Integration with Coding Assistants
1. Terminal 1: Run RailwayBot watch mode
2. Terminal 2: Run coding assistant (e.g., codex)
3. On deployment failure:
   - RailwayBot detects failure
   - Errors copied to clipboard
   - Paste into coding assistant (Ctrl+V)

### One-Shot Check
```bash
python -m railwaybot check
```

## Error Flow

1. **Detection**: Watcher polls Railway status every N seconds
2. **Trigger**: Status changes to FAILED/CRASHED/ERRORED
3. **Extraction**:
   - Fetch build logs via `railway logs --build`
   - Fetch deploy logs via `railway logs`
4. **Parsing**:
   - Apply regex patterns to identify errors
   - Extract context (surrounding lines)
5. **Formatting**:
   - Format with headers, timestamps, service info
   - Limit to max_lines_per_error
6. **Output**:
   - Copy to clipboard (if auto_copy enabled)
   - Show notification

## Extension Points

### Adding Error Patterns

Edit `log_parser.py` -> `LogParser.ERROR_PATTERNS`:

```python
ERROR_PATTERNS = [
    r'(?i)error:?\s+(.+)',
    r'your-custom-pattern',
    # ...
]
```

### Custom Notifications

Extend `clipboard.py` -> `ClipboardManager`:

```python
def _show_notification(self, text: str) -> None:
    # Add custom notification logic
    # e.g., Windows toast, desktop notification, etc.
    pass
```

### Additional Railway Commands

Extend `railway_client.py` -> `RailwayClient`:

```python
def redeploy(self) -> None:
    """Trigger a redeployment."""
    self._run_command(["redeploy", "-y"])
```

## Future Phase 2: DashBot Integration

### Option A: Tool Wrapper
Create `dashbot/lib/tools/railway_tool.dart`:

```dart
class RailwayTool extends Tool {
  Future<String> checkDeployment() async {
    // Call RailwayBot via ShellTool
    final result = await ShellTool.execute([
      'python',
      'C:/path/to/RailwayBot/src/cli.py',
      'check'
    ]);
    return result.stdout;
  }
}
```

### Option B: Native Dart Implementation
Port Python logic to Dart:
- `lib/services/railway_service.dart`
- `lib/tools/railway_tool.dart`
- Integrate with DashBot tool registry

## Dependencies

- **pyperclip**: Cross-platform clipboard access
- **colorama**: Terminal colors (Windows compatibility)
- **python-dotenv**: Environment variable loading
- **Railway CLI**: Must be installed separately (npm i -g @railway/cli)

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

### "Railway CLI not found"
- Install: `npm i -g @railway/cli`
- Verify: `railway --version`

### "Not linked to a Railway project"
- Run: `railway link` in project directory

### "Too many consecutive errors"
- Check Railway authentication: `railway whoami`
- Check network connection
- Verify RAILWAY_TOKEN if using token auth

## Development Notes

### Code Style
- Type hints for all function parameters and returns
- Docstrings for all public methods
- Error handling via custom exceptions
- Configuration-driven behavior

### Testing Strategy
- Manual testing with real Railway deployments
- Test various failure modes (build, deploy, runtime)
- Verify clipboard operations
- Test configuration changes

---

## Skills

Three skills are scaffolded under `skills/` for full Railway lifecycle automation. They are registered as:
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

---

### `/railway-fixer` — Autonomous deployment fixer

**Trigger:** "fix my railway deploy", "railway is failing", "railway-fixer"

Background sub-agent. Runs the diagnose → fix → commit → redeploy loop until success or escalation.

```bash
python skills/railway-fixer/fixer_orchestrator.py <repo-path>
```

Exit signals: `SUCCESS` (2 consecutive clean deploys) | `ESCALATE` (3 failed fixes per error type)

Fixer modules: `npm_fixer`, `pip_fixer`, `go_fixer`, `env_fixer`, `port_fixer`, `prisma_fixer`, `lock_fixer`, `build_timeout_fixer`

---

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

---

### Skills file layout
```
skills/
├── railway-deploy/
│   ├── skill.yaml          # skill metadata
│   ├── detect_stack.py     # stack detection
│   ├── config_generator.py # Railway config generation from templates
│   ├── service_setup.py    # PostgreSQL/Redis provisioning
│   ├── workflow.md         # step-by-step workflow doc
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
│   │   ├── lock_fixer.py, build_timeout_fixer.py
│   └── workflows/
│       └── diagnose.md, node-fix.md, python-fix.md, go-fix.md
└── railway-manage/
    ├── skill.yaml
    └── workflow.md
```

---

## Version History

- **v0.1.0** (2026-02-26): Initial implementation
  - Watch mode monitoring
  - Error extraction and formatting
  - Clipboard integration
  - Configurable settings
- **v0.2.0** (2026-04-18): Skills added
  - `railway-deploy` — full first-time deploy workflow
  - `railway-fixer` — autonomous self-healing sub-agent
  - `railway-manage` — post-deploy ops (logs, env, rollback, scale, migrate)
