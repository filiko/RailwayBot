# Agent Integration Guide

## Overview

RailwayBot provides an **agent-friendly API** that coding agents (like Claude, GitHub Copilot, or other AI assistants) can call programmatically to check Railway deployment status and get error details.

## Installation

**Required:** Install RailwayBot as a package first:

```bash
cd RailwayBot
pip install -e .
```

This enables the `python -m railwaybot.agent_api` command and creates the `railwaybot-agent` entry point.

## Why This Matters

When a coding agent is working on fixing Railway deployments, it can:
1. **Check deployment status** programmatically
2. **Get structured error data** in JSON format
3. **Parse specific errors** to make targeted fixes
4. **Continue autonomous work** based on deployment results

## Usage Modes

### 1. JSON Output (For Agent Parsing)

```bash
python -m railwaybot.agent_api

# Or using the entry point
railwaybot-agent
```

**Output:**
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

### 2. Brief Summary (For Quick Checks)

```bash
python -m railwaybot.agent_api --summary
```

**Output:**
```
❌ Deployment Failed - 3 build errors, 1 deploy errors
```

or

```
✓ Deployment SUCCESS
```

### 3. Human-Readable Text

```bash
python -m railwaybot.agent_api --format text
```

**Output:**
```
============================================================
=== Railway Deployment Failed ===
============================================================
Service: my-api
Environment: production

BUILD ERRORS:
------------------------------------------------------------
[Line 45] npm ERR! missing dependency: express@^4.0.0
...
```

## Integration Examples

### Example 1: Python Coding Agent

```python
import subprocess
import json

def check_railway_deployment():
    """Call RailwayBot agent API and parse results."""
    result = subprocess.run(
        ["python", "-m", "railwaybot.agent_api"],
        capture_output=True,
        text=True,
        cwd="/path/to/RailwayBot"
    )

    data = json.loads(result.stdout)

    if data["status"] == "failed":
        # Extract specific errors
        build_errors = data["errors"]["build"]

        for error in build_errors:
            print(f"Found error at line {error['line_number']}: {error['content']}")

            # Agent can now make targeted fixes based on error content
            if "missing dependency" in error["content"]:
                fix_missing_dependency(error)
            elif "MODULE_NOT_FOUND" in error["content"]:
                fix_missing_module(error)

    return data

def fix_missing_dependency(error):
    """Agent implements fix for missing dependency."""
    # Extract package name from error
    # Update package.json
    # Run npm install
    pass
```

### Example 2: Shell Script Integration

```bash
#!/bin/bash
# Agent workflow script

echo "Deploying to Railway..."
railway up

echo "Checking deployment status..."
STATUS=$(python -m railwaybot.agent_api --summary)

if [[ $STATUS == *"Failed"* ]]; then
    echo "Deployment failed! Getting error details..."

    # Get full error details
    python -m railwaybot.agent_api --format text > deployment_errors.txt

    # Send to AI assistant for analysis
    cat deployment_errors.txt | codex "Fix these Railway deployment errors"
else
    echo "Deployment successful!"
fi
```

### Example 3: DashBot Tool Integration

```dart
// Future DashBot integration
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
      workingDirectory: 'C:/path/to/RailwayBot',
    );

    final data = jsonDecode(result.stdout);

    if (data['status'] == 'failed') {
      // Return formatted errors to agent
      return data['formatted_report'];
    }

    return 'Deployment status: ${data['deployment']['status']}';
  }
}
```

### Example 4: Node.js Agent

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
            console.log('Deployment failed!');

            // Extract error patterns
            const buildErrors = result.errors.build;
            const errorTypes = buildErrors.map(e => detectErrorType(e.content));

            // Agent decides what to fix
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
    // ... more patterns
}
```

## JSON Response Structure

### Success Response

```json
{
  "status": "ok",
  "deployment": {
    "id": "deploy-123",
    "status": "SUCCESS",
    "service": "my-service",
    "environment": "production"
  },
  "errors": {
    "build": [],
    "deploy": []
  },
  "formatted_report": "",
  "message": "Deployment status: SUCCESS"
}
```

### Failure Response

```json
{
  "status": "failed",
  "deployment": {
    "id": "deploy-456",
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
        "context": [
          "npm install --production",
          "npm ERR! missing dependency: express@^4.0.0",
          "npm ERR! peer dep missing"
        ]
      }
    ],
    "deploy": [
      {
        "line_number": 12,
        "content": "Error: listen EADDRINUSE: address already in use :::3000",
        "type": "DEPLOYMENT",
        "timestamp": "14:23:40",
        "context": [
          "Starting server...",
          "Error: listen EADDRINUSE: address already in use :::3000",
          "at Server.setupListenHandle"
        ]
      }
    ]
  },
  "formatted_report": "=== Railway Deployment Failed ===\n...",
  "message": "Deployment FAILED"
}
```

### Error Response

```json
{
  "status": "error",
  "deployment": null,
  "errors": {
    "build": [],
    "deploy": []
  },
  "formatted_report": "",
  "message": "Not linked to a Railway project. Run 'railway link' in your project directory."
}
```

## Common Agent Workflows

### Workflow 1: Deploy → Check → Fix Loop

```python
def autonomous_deployment_fix():
    """Agent autonomously fixes deployment issues."""
    max_attempts = 5
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        print(f"Deployment attempt {attempt}/{max_attempts}")

        # Deploy
        subprocess.run(["railway", "up"])

        # Wait for deployment to complete
        time.sleep(10)

        # Check status
        result = get_railway_status()

        if result["status"] == "ok":
            print("✓ Deployment successful!")
            break

        if result["status"] == "failed":
            print(f"✗ Deployment failed with {len(result['errors']['build'])} errors")

            # Analyze errors and apply fixes
            fixes_applied = analyze_and_fix_errors(result["errors"])

            if not fixes_applied:
                print("No automatic fixes available")
                break

            print(f"Applied {fixes_applied} fixes, retrying...")
            continue

    return result

def analyze_and_fix_errors(errors):
    """Agent analyzes errors and applies fixes."""
    fixes_count = 0

    for error in errors["build"]:
        content = error["content"]

        if "missing dependency" in content:
            package = extract_package_name(content)
            install_package(package)
            fixes_count += 1

        elif "MODULE_NOT_FOUND" in content:
            module = extract_module_name(content)
            add_missing_import(module)
            fixes_count += 1

        # ... more fix patterns

    return fixes_count
```

### Workflow 2: Continuous Monitoring

```python
def continuous_monitor():
    """Agent continuously monitors deployments."""
    last_status = None

    while True:
        result = get_railway_status()
        current_status = result.get("deployment", {}).get("status")

        # Status changed
        if current_status != last_status:
            print(f"Status changed: {last_status} → {current_status}")

            if result["status"] == "failed":
                # Automatically attempt fix
                auto_fix_deployment(result)

        last_status = current_status
        time.sleep(5)
```

## Python API Direct Import

For Python-based agents, you can import directly:

```python
from railwaybot.agent_api import AgentAPI

# Initialize
api = AgentAPI()

# Check deployment
result = api.check_deployment()

if result["status"] == "failed":
    print("Deployment failed!")
    print(result["formatted_report"])

    # Get structured errors
    for error in result["errors"]["build"]:
        print(f"Line {error['line_number']}: {error['content']}")

# Get brief summary
summary = api.get_error_summary()
print(summary)  # "❌ Deployment Failed - 3 build errors, 1 deploy errors"
```

## Best Practices

1. **Check Before Acting**: Always check deployment status before attempting fixes
2. **Parse Structured Errors**: Use the JSON output for precise error identification
3. **Implement Retry Logic**: Deployments can have transient failures
4. **Limit Attempts**: Prevent infinite loops with max retry count
5. **Log Actions**: Keep track of what fixes were attempted
6. **Validate Fixes**: Ensure fixes don't introduce new issues

## Error Pattern Detection

Common error patterns agents should handle:

| Pattern | Description | Typical Fix |
|---------|-------------|-------------|
| `npm ERR! missing dependency` | Missing npm package | Add to package.json |
| `MODULE_NOT_FOUND` | Missing Node module | Add import statement |
| `EADDRINUSE` | Port already in use | Change port or kill process |
| `pip install failed` | Python dependency issue | Update requirements.txt |
| `build failed` | Compilation error | Fix syntax/type errors |
| `cannot find module` | Missing file | Create missing file |

## Advanced: Custom Error Handlers

```python
class ErrorHandler:
    """Custom error handler for specific error types."""

    def __init__(self):
        self.handlers = {
            'missing_dependency': self.fix_missing_dependency,
            'port_conflict': self.fix_port_conflict,
            'module_not_found': self.fix_module_not_found,
        }

    def handle(self, error):
        """Route error to appropriate handler."""
        error_type = self.detect_type(error['content'])

        if error_type in self.handlers:
            return self.handlers[error_type](error)

        return False

    def detect_type(self, content):
        """Detect error type from content."""
        if 'missing dependency' in content:
            return 'missing_dependency'
        if 'EADDRINUSE' in content:
            return 'port_conflict'
        if 'MODULE_NOT_FOUND' in content:
            return 'module_not_found'
        return 'unknown'

    def fix_missing_dependency(self, error):
        """Fix missing dependency error."""
        # Implementation
        pass
```

## Future Enhancements

- **Real-time WebSocket API** for live deployment monitoring
- **Error prediction** based on code changes
- **Auto-fix suggestions** with confidence scores
- **Integration with LLM APIs** for natural language error analysis
- **Multi-project support** for monorepo deployments

---

**Ready to use!** Your coding agents can now autonomously monitor and respond to Railway deployment errors.
