# RailwayBot Installation Guide

## Quick Start (No Installation Needed!)

The easiest way to use RailwayBot, especially for coding agents, is the **standalone wrapper**:

```bash
python /path/to/RailwayBot/railwaybot-check.py --summary
```

This works from any directory and requires no installation!

---

## Installation Methods

### Method 1: No Installation (Recommended for Agents)

**Just use the standalone wrapper:**

```bash
# Check deployment status
python /path/to/RailwayBot/railwaybot-check.py --summary

# Get JSON output
python /path/to/RailwayBot/railwaybot-check.py

# Get formatted text
python /path/to/RailwayBot/railwaybot-check.py --format text
```

**Advantages:**
- ✅ Works from any directory
- ✅ No installation required
- ✅ No dependency conflicts
- ✅ Perfect for coding agents
- ✅ Cross-platform compatible

---

### Method 2: Package Installation (Optional)

If you want the `railwaybot` command in your PATH:

```bash
cd RailwayBot
pip install -e .
```

This installs:
- `railwaybot` command for interactive use
- `railwaybot-agent` command for agent integration
- Python module `railwaybot` for imports

**After installation:**
```bash
# From anywhere
railwaybot watch
railwaybot check
railwaybot-agent --summary
python -m railwaybot.agent_api --summary
```

**Note:** Installation may fail on some Python 3.10 configurations due to setuptools/distutils issues. Use Method 1 if installation fails.

---

### Method 3: Manual Dependencies Only

If you only need the dependencies:

```bash
cd RailwayBot
pip install -r requirements.txt
```

Then use the standalone wrapper or module invocation.

---

## Prerequisites

### 1. Python 3.7+
```bash
python --version
```

### 2. Railway CLI (Required)
```bash
# Install
npm i -g @railway/cli

# Login
railway login

# Verify
railway --version
railway whoami
```

### 3. Link Your Project
```bash
cd /path/to/your/railway/project
railway link
```

---

## Usage After Installation

### For Human Developers

```bash
# Watch mode - continuous monitoring
cd /path/to/railway/project
railwaybot watch

# One-shot check
railwaybot check

# View configuration
railwaybot config

# Test connection
railwaybot test
```

### For Coding Agents

**Recommended (no installation needed):**

```bash
python /path/to/RailwayBot/railwaybot-check.py --summary
```

**From Python code:**

```python
import subprocess
import json

result = subprocess.run(
    [
        "python",
        "/path/to/RailwayBot/railwaybot-check.py"
    ],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
print(f"Status: {data['status']}")
```

---

## Troubleshooting Installation

### "pip install -e ." fails with setuptools error

**Solution:** Use the standalone wrapper instead (Method 1). No installation needed!

```bash
python /path/to/RailwayBot/railwaybot-check.py
```

### "Railway CLI not found"

**Solution:** Install Railway CLI:
```bash
npm i -g @railway/cli
```

Verify it's in PATH:
```bash
railway --version
```

### "Not linked to a Railway project"

**Solution:** Run from your Railway project directory:
```bash
cd /path/to/railway/project
railway link
python /path/to/RailwayBot/railwaybot-check.py --summary
```

### "ModuleNotFoundError: No module named 'railwaybot'"

**Solution:** Either:
1. Use the standalone wrapper (recommended):
   ```bash
   python /path/to/RailwayBot/railwaybot-check.py --summary
   ```

2. Or run from RailwayBot directory:
   ```bash
   cd RailwayBot
   python -m railwaybot.agent_api --summary
   ```

---

## Verification

Test that everything works:

```bash
# Test 1: Standalone wrapper
python /path/to/RailwayBot/railwaybot-check.py --summary

# Expected output (if not in Railway project):
# ERROR: Not linked to a Railway project. Run 'railway link' in your project directory.

# Test 2: From Railway project
cd /path/to/railway/project
python /path/to/RailwayBot/railwaybot-check.py --summary

# Expected output:
# OK: No active deployment
# (or deployment status if active)
```

---

## What Gets Installed (Method 2)

When you run `pip install -e .`:

1. **Dependencies:**
   - pyperclip (clipboard access)
   - colorama (terminal colors)
   - python-dotenv (environment variables)

2. **Entry Points (commands):**
   - `railwaybot` → `railwaybot.cli:main`
   - `railwaybot-agent` → `railwaybot.agent_api:main`

3. **Python Package:**
   - `railwaybot` module available for import

4. **Location:**
   - Editable install - changes to source code take effect immediately

---

## Uninstallation

If you installed with `pip install -e .`:

```bash
pip uninstall railwaybot
```

The standalone wrapper doesn't need uninstallation - just delete the file if you don't want it.

---

## Summary

**For most users (especially coding agents):**
```bash
# Just use this - no installation needed!
python /path/to/RailwayBot/railwaybot-check.py --summary
```

**For power users who want PATH commands:**
```bash
# Install once
pip install -e .

# Then use
railwaybot watch
railwaybot-agent --summary
```

**That's it!** 🚀
