# RailwayBot

Automated Railway deployment error monitoring and extraction tool. Watches Railway deployments and automatically copies errors to clipboard for pasting into your coding assistant.

## Features

- 🔍 **Automatic Error Detection**: Monitors Railway deployments and detects failures
- 📋 **Clipboard Integration**: Automatically copies formatted errors to clipboard
- ⚙️ **Configurable**: Editable settings via `config.json`
- 🎯 **Smart Parsing**: Extracts relevant error patterns from build and deployment logs
- 🔄 **Watch Mode**: Continuously monitor deployments in the background
- 🚀 **One-Shot Mode**: Quick check for current deployment status

## Prerequisites

1. **Railway CLI** - Must be installed and authenticated
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli

   # Login to Railway
   railway login
   ```

2. **Python 3.7+**

## Installation

1. Clone and navigate to the RailwayBot directory:
   ```bash
   git clone https://github.com/filiko/RailwayBot.git
   cd RailwayBot
   ```

2. **Install RailwayBot as a package** (recommended):
   ```bash
   pip install -e .
   ```

   This will:
   - Install all Python dependencies automatically
   - Add `railwaybot` and `railwaybot-agent` commands to your PATH
   - Enable `python -m railwaybot.agent_api` for agent integration

   **Alternative (manual dependencies):**
   ```bash
   pip install -r requirements.txt
   # Note: This doesn't add commands to PATH
   ```

3. (Optional) Set Railway token environment variable:
   ```bash
   # Windows PowerShell
   $env:RAILWAY_TOKEN = "your-token-here"

   # Windows CMD
   set RAILWAY_TOKEN=your-token-here

   # Or add to system environment variables for persistence
   ```

## Usage

### Watch Mode (Recommended)

Start monitoring Railway deployments in the background:

```bash
# Navigate to your Railway project directory
cd C:\path\to\your\railway-project

# Start RailwayBot (after pip install -e .)
railwaybot watch

# Or using Python module
python -m railwaybot.cli watch
```

RailwayBot will:
- Monitor deployment status every 5 seconds (configurable)
- Detect when deployments fail
- Extract build and deployment errors
- Copy formatted errors to clipboard
- Show notification when errors are copied

You can then paste directly into your coding assistant (Ctrl+V).

### One-Shot Check

Check current deployment status once:

```bash
railwaybot check

# Or using Python module
python -m railwaybot.cli check
```

### Agent API (For Coding Agents)

For programmatic access by coding agents:

```bash
# Get JSON output
python -m railwaybot.agent_api

# Get brief summary
python -m railwaybot.agent_api --summary

# Or use the entry point
railwaybot-agent --summary
```

See [docs/AGENT_INTEGRATION.md](docs/AGENT_INTEGRATION.md) for detailed agent integration examples.

### Configuration

View current configuration:

```bash
railwaybot config

# Or using Python module
python -m railwaybot.cli config
```

Edit `config.json` to customize settings:

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

### Test Connection

Verify Railway CLI is working:

```bash
python -m railwaybot test
```

## Workflow

### Typical Development Workflow

1. **Terminal 1** - Start RailwayBot in your project directory:
   ```bash
   cd /path/to/my-railway-project
   railwaybot watch
   ```

2. **Terminal 2** - Your coding assistant (e.g., codex):
   ```bash
   codex chat
   ```

3. **Make changes** and deploy:
   ```bash
   git push  # or railway up
   ```

4. **If deployment fails**:
   - RailwayBot automatically detects the failure
   - Errors are copied to clipboard
   - You get a notification
   - Switch to your coding assistant and paste (Ctrl+V)
   - Get AI suggestions for fixes
   - Apply fixes and redeploy

## Error Report Format

RailwayBot formats errors for easy consumption by coding assistants:

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
    npm ERR! peer dep missing: express@^4.0.0, required by...

DEPLOYMENT ERRORS:
------------------------------------------------------------
[14:23:40] Line 12
  Error: listen EADDRINUSE: address already in use :::3000
  Context:
    Starting server...
    Error: listen EADDRINUSE: address already in use :::3000
    at Server.setupListenHandle [as _listen2]

============================================================
=== End Error Report ===
============================================================
```

## Troubleshooting

### "Railway CLI not found"

Install Railway CLI:
```bash
npm i -g @railway/cli
```

### "Not linked to a Railway project"

Link your project:
```bash
cd /path/to/project
railway link
```

### "Too many consecutive errors"

Check your Railway authentication:
```bash
railway whoami
```

If not logged in:
```bash
railway login
```

## Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `poll_interval_seconds` | Seconds between status checks | 5 |
| `auto_copy` | Automatically copy errors to clipboard | true |
| `include_timestamps` | Include timestamps in error reports | true |
| `max_lines_per_error` | Max lines to show per error | 50 |
| `notifications.enabled` | Show console notifications | true |
| `notifications.sound` | Play sound on error | false |

## Project Structure

```
RailwayBot/
├── railwaybot/
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Python -m entry point
│   ├── cli.py               # CLI interface
│   ├── agent_api.py         # Agent-facing API
│   ├── railway_client.py    # Railway CLI wrapper
│   ├── log_parser.py        # Error extraction
│   ├── clipboard.py         # Clipboard operations
│   └── watcher.py           # Deployment monitoring
├── config.json              # User configuration (auto-created)
├── config.example.json      # Example configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Future Enhancements

- Web dashboard for error history
- Email/Slack notifications
- Custom error pattern matching
- Multiple project monitoring
- Error trending and analytics

## License

MIT — see [LICENSE](LICENSE).
