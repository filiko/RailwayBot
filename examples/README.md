# RailwayBot Examples

## agent_example.py

Complete example of an **autonomous coding agent** that uses RailwayBot to:

1. ✅ Check Railway deployment status
2. 🔍 Analyze errors automatically
3. 🔧 Apply automated fixes (install packages, fix ports, etc.)
4. 🔄 Retry deployment until success
5. 📊 Report final results

### How It Works

The `AutonomousDeploymentAgent` class demonstrates:

```python
# 1. Check deployment using RailwayBot agent API
result = subprocess.run(
    ["python", "-m", "railwaybot.agent_api"],
    capture_output=True,
    text=True
)
data = json.loads(result.stdout)

# 2. Analyze structured errors
if data["status"] == "failed":
    for error in data["errors"]["build"]:
        if "missing dependency" in error["content"]:
            # Apply fix
            install_package(extract_package_name(error))

# 3. Redeploy and repeat
railway_up()
```

### Run the Example

```bash
# Edit paths in agent_example.py first!
cd RailwayBot/examples
python agent_example.py
```

### What Gets Automated

| Error Type | Detection | Automatic Fix |
|------------|-----------|---------------|
| Missing npm dependency | ✅ | ✅ Install package |
| Missing Python module | ✅ | ✅ Add to requirements.txt |
| Port conflict | ✅ | ✅ Switch to dynamic port |
| Syntax errors | ✅ | ⚠️ Report only |
| Missing env vars | ✅ | ⚠️ Report only |

## Use Cases

### Use Case 1: Human Developer
**Original workflow** (manual, ~5 minutes per error):
1. Deploy fails
2. Open Railway dashboard
3. Find logs
4. Copy errors
5. Paste into coding assistant
6. Read suggestions
7. Implement fixes
8. Redeploy

**With RailwayBot** (~30 seconds):
1. RailwayBot auto-detects failure
2. Errors auto-copied to clipboard
3. Paste into coding assistant (Ctrl+V)
4. Implement fixes
5. Redeploy

**Time saved:** ~80% per deployment cycle

### Use Case 2: Autonomous Agent
**With agent_example.py** (~automated~):
1. Agent triggers deployment
2. RailwayBot checks status via API
3. Agent analyzes structured errors
4. Agent applies automatic fixes
5. Agent retries deployment
6. Repeats until success or max attempts

**Human involvement:** None (until complex errors)

### Use Case 3: CI/CD Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy with Auto-Fix
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to Railway
        run: |
          railway up

      - name: Check Deployment
        run: |
          python railwaybot.agent_api --summary
          if [[ $? -ne 0 ]]; then
            python railwaybot.agent_api --format text | \
              gh issue create --title "Deployment Failed" --body-file -
          fi
```

## More Examples Coming Soon

- **Multi-service monitoring** - Track multiple Railway services
- **Slack integration** - Post errors to Slack channels
- **Error trend analysis** - Identify recurring issues
- **LLM-powered fixes** - Use GPT/Claude for complex errors

## Contributing

Have a cool use case? Add your example here!
