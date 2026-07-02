# RailwayBot Quick Start Guide

## 5-Minute Setup

### Step 1: Install RailwayBot

**Recommended Method:**
```bash
cd RailwayBot
pip install -e .
```

This installs RailwayBot as a package and adds the `railwaybot` command to your PATH.

**No-install alternative (good for coding agents):**
```bash
python /path/to/RailwayBot/railwaybot-check.py --summary
```
Works from any directory, no `pip install` needed. If `pip install -e .` fails on your
Python setup (some 3.10 configs hit setuptools/distutils issues), use this instead.

**Manual dependencies only:**
```bash
pip install -r requirements.txt
# Note: This doesn't add commands to PATH
```

### Step 2: Verify Railway CLI

Make sure Railway CLI is installed and authenticated:

```bash
railway --version
railway whoami
```

If not installed:
```bash
npm i -g @railway/cli
railway login
```

### Step 3: Link Your Project

Navigate to your Railway project and link it:

```bash
cd /path/to/your/railway-project
railway link
```

### Step 4: Start Monitoring

```bash
# From your Railway project directory
cd /path/to/your/railway-project

# Start RailwayBot (after pip install -e .)
railwaybot watch

# Or use Python module
python -m railwaybot.cli watch
```

## Daily Workflow

### Setup (Once per session)

**Terminal 1 - RailwayBot:**
```bash
cd /path/to/your/railway-project
railwaybot watch
```

**Terminal 2 - Coding Assistant:**
```bash
codex chat
# or whatever coding assistant you use
```

### When Deployment Fails

1. **RailwayBot automatically:**
   - Detects the failure
   - Extracts errors from logs
   - Copies formatted errors to clipboard
   - Shows notification

2. **You:**
   - Switch to coding assistant terminal
   - Press `Ctrl+V` to paste errors
   - Get AI suggestions
   - Implement fixes
   - Redeploy

3. **Repeat until successful!**

## Commands

**After installation with `pip install -e .`:**

| Command | Description |
|---------|-------------|
| `railwaybot watch` | Start monitoring (keeps running) |
| `railwaybot check` | One-time check for errors |
| `railwaybot config` | Show current configuration |
| `railwaybot test` | Test Railway CLI connection |

**Or use Python module form:**
```bash
python -m railwaybot.cli watch
python -m railwaybot.cli check
python -m railwaybot.cli config
python -m railwaybot.cli test
```

**For agent integration:**
```bash
python -m railwaybot.agent_api          # JSON output
python -m railwaybot.agent_api --summary  # Brief summary
railwaybot-agent --summary              # Using entry point
```

## Configuration

Config file: `RailwayBot/config.json` (auto-created on first run)

**Common Settings:**

```json
{
  "railway": {
    "poll_interval_seconds": 5,    // How often to check (seconds)
    "auto_copy": true               // Auto-copy to clipboard
  },
  "formatting": {
    "max_lines_per_error": 50      // Max lines per error section
  },
  "notifications": {
    "enabled": true,                // Show notifications
    "sound": false                  // Play beep sound
  }
}
```

## Troubleshooting

### "Railway CLI not found"
```bash
npm i -g @railway/cli
```

### "Not linked to a Railway project"
```bash
cd /path/to/project
railway link
```

### "No errors detected"
The deployment failed but RailwayBot couldn't find specific error patterns. The tool will still copy the last portion of logs.

### Want to customize error patterns?
Edit `railwaybot/log_parser.py` -> `ERROR_PATTERNS` list

## Tips

- **Keep RailwayBot running** in the background while developing
- **Multiple projects?** Start a separate RailwayBot instance for each (different terminals)
- **Sound notifications** can be helpful if you context-switch a lot (enable in config.json)
- **Poll interval**: Lower = faster detection but more API calls. 5 seconds is a good balance.

## What Gets Copied?

Example clipboard content:

```
============================================================
=== Railway Deployment Failed ===
============================================================
Service: my-api
Environment: production
Time: 2026-02-26 14:23:45

BUILD ERRORS:
------------------------------------------------------------
[14:20:15] Line 45
  npm ERR! missing dependency: express@^4.0.0
  Context:
    npm install --production
    npm ERR! missing dependency: express@^4.0.0
    npm ERR! peer dep missing: express@^4.0.0

DEPLOYMENT ERRORS:
------------------------------------------------------------
[14:23:40] Line 12
  Error: listen EADDRINUSE: address already in use :::3000
  Context:
    Starting server...
    Error: listen EADDRINUSE: address already in use :::3000

============================================================
```

This format is optimized for coding assistants to understand and provide relevant fixes!

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [docs/AGENT_INTEGRATION.md](docs/AGENT_INTEGRATION.md) for architecture and agent integration details
- Customize `config.json` to your preferences
- Consider adding RailwayBot to your startup scripts for automatic launching

## Support

For issues or feature requests, open an issue on the RailwayBot repository.
