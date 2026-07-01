"""
Example: How a coding agent would use RailwayBot programmatically.

This demonstrates an autonomous agent that:
1. Checks Railway deployment status
2. Analyzes errors
3. Applies automated fixes
4. Retries deployment
"""

import subprocess
import json
import time
import re
from pathlib import Path


class AutonomousDeploymentAgent:
    """Example coding agent that autonomously fixes Railway deployments."""

    def __init__(self, railwaybot_path: str, project_path: str):
        """
        Initialize agent.

        Args:
            railwaybot_path: Path to RailwayBot installation
            project_path: Path to the Railway project to monitor
        """
        self.railwaybot_path = Path(railwaybot_path)
        self.project_path = Path(project_path)
        self.max_attempts = 5

    def check_deployment(self) -> dict:
        """
        Call RailwayBot agent API to check deployment status.

        Returns:
            Dict with deployment status and errors
        """
        result = subprocess.run(
            ["python", "-m", "railwaybot.agent_api"],
            capture_output=True,
            text=True,
            cwd=str(self.railwaybot_path)
        )

        if result.returncode != 0:
            return {"status": "error", "message": result.stderr}

        return json.loads(result.stdout)

    def deploy(self) -> bool:
        """Trigger Railway deployment."""
        print("🚀 Deploying to Railway...")

        result = subprocess.run(
            ["railway", "up"],
            cwd=str(self.project_path),
            capture_output=True,
            text=True
        )

        return result.returncode == 0

    def analyze_errors(self, errors: dict) -> list:
        """
        Analyze errors and determine fixes.

        Args:
            errors: Dict with 'build' and 'deploy' error lists

        Returns:
            List of fix actions to apply
        """
        fixes = []

        # Analyze build errors
        for error in errors.get("build", []):
            content = error["content"]

            # Missing npm dependency
            if "missing dependency" in content.lower() or "npm ERR!" in content:
                package = self._extract_package_name(content)
                if package:
                    fixes.append({
                        "type": "install_npm_package",
                        "package": package,
                        "reason": f"Missing dependency: {package}"
                    })

            # Missing Python package
            elif "ModuleNotFoundError" in content or "No module named" in content:
                module = self._extract_python_module(content)
                if module:
                    fixes.append({
                        "type": "install_python_package",
                        "package": module,
                        "reason": f"Missing Python module: {module}"
                    })

            # TypeScript/JavaScript syntax error
            elif "SyntaxError" in content or "error TS" in content:
                fixes.append({
                    "type": "syntax_error",
                    "line": error.get("line_number"),
                    "content": content,
                    "reason": "Syntax error detected"
                })

        # Analyze deployment errors
        for error in errors.get("deploy", []):
            content = error["content"]

            # Port already in use
            if "EADDRINUSE" in content:
                port = self._extract_port_number(content)
                fixes.append({
                    "type": "port_conflict",
                    "port": port,
                    "reason": f"Port {port} already in use"
                })

            # Environment variable missing
            elif "environment variable" in content.lower() or "env" in content.lower():
                var_name = self._extract_env_var_name(content)
                fixes.append({
                    "type": "missing_env_var",
                    "variable": var_name,
                    "reason": f"Missing environment variable: {var_name}"
                })

        return fixes

    def apply_fixes(self, fixes: list) -> int:
        """
        Apply automated fixes.

        Args:
            fixes: List of fix actions from analyze_errors

        Returns:
            Number of fixes successfully applied
        """
        applied_count = 0

        for fix in fixes:
            print(f"🔧 Applying fix: {fix['reason']}")

            try:
                if fix["type"] == "install_npm_package":
                    self._install_npm_package(fix["package"])
                    applied_count += 1

                elif fix["type"] == "install_python_package":
                    self._install_python_package(fix["package"])
                    applied_count += 1

                elif fix["type"] == "port_conflict":
                    self._fix_port_conflict(fix["port"])
                    applied_count += 1

                elif fix["type"] == "missing_env_var":
                    print(f"⚠️  Cannot auto-fix: Missing environment variable '{fix['variable']}'")
                    print(f"   Please set this variable manually in Railway dashboard")

                elif fix["type"] == "syntax_error":
                    print(f"⚠️  Cannot auto-fix: Syntax error at line {fix.get('line')}")
                    print(f"   Manual code review required")

            except Exception as e:
                print(f"❌ Fix failed: {e}")

        return applied_count

    def autonomous_deploy_loop(self) -> dict:
        """
        Autonomous deployment loop: deploy → check → fix → repeat.

        Returns:
            Final deployment result
        """
        attempt = 0

        while attempt < self.max_attempts:
            attempt += 1
            print(f"\n{'='*60}")
            print(f"Deployment Attempt {attempt}/{self.max_attempts}")
            print(f"{'='*60}\n")

            # Deploy
            self.deploy()

            # Wait for deployment to process
            print("⏳ Waiting for deployment to complete...")
            time.sleep(15)  # Give Railway time to process

            # Check status
            result = self.check_deployment()

            if result["status"] == "ok":
                print(f"\n{'='*60}")
                print("✅ DEPLOYMENT SUCCESSFUL!")
                print(f"{'='*60}")
                return result

            elif result["status"] == "failed":
                print(f"\n❌ Deployment failed")

                # Show errors
                build_error_count = len(result["errors"]["build"])
                deploy_error_count = len(result["errors"]["deploy"])
                print(f"   Build errors: {build_error_count}")
                print(f"   Deploy errors: {deploy_error_count}")

                # Analyze and fix
                fixes = self.analyze_errors(result["errors"])

                if not fixes:
                    print("\n⚠️  No automatic fixes available for these errors")
                    print("\n📋 Error details:")
                    print(result["formatted_report"])
                    return result

                print(f"\n🤔 Identified {len(fixes)} potential fixes:")
                for fix in fixes:
                    print(f"   - {fix['reason']}")

                # Apply fixes
                applied = self.apply_fixes(fixes)

                if applied == 0:
                    print("\n⚠️  Could not apply any automatic fixes")
                    return result

                print(f"\n✓ Applied {applied} fixes, retrying deployment...")
                continue

            elif result["status"] == "error":
                print(f"\n❌ Error checking deployment: {result['message']}")
                return result

        print(f"\n{'='*60}")
        print(f"❌ Max attempts ({self.max_attempts}) reached")
        print(f"{'='*60}")
        return result

    # Helper methods for fix application

    def _install_npm_package(self, package: str) -> None:
        """Install npm package."""
        print(f"   Installing npm package: {package}")
        subprocess.run(
            ["npm", "install", package],
            cwd=str(self.project_path),
            check=True
        )

    def _install_python_package(self, package: str) -> None:
        """Install Python package."""
        print(f"   Installing Python package: {package}")

        # Update requirements.txt
        req_file = self.project_path / "requirements.txt"
        with open(req_file, "a") as f:
            f.write(f"\n{package}\n")

        print(f"   Added {package} to requirements.txt")

    def _fix_port_conflict(self, port: int) -> None:
        """Fix port conflict by updating to dynamic port."""
        print(f"   Fixing port conflict (port {port})")

        # Common port configuration files
        config_files = [
            "server.js",
            "index.js",
            "app.js",
            "main.py",
            "app.py"
        ]

        for filename in config_files:
            filepath = self.project_path / filename

            if filepath.exists():
                content = filepath.read_text()

                # Replace hardcoded port with environment variable
                if f":{port}" in content or f"= {port}" in content:
                    updated = content.replace(
                        f"const PORT = {port}",
                        "const PORT = process.env.PORT || 3000"
                    )
                    updated = updated.replace(
                        f"PORT = {port}",
                        "PORT = int(os.environ.get('PORT', 3000))"
                    )

                    filepath.write_text(updated)
                    print(f"   Updated {filename} to use dynamic port")
                    return

    # Helper methods for pattern extraction

    def _extract_package_name(self, error_content: str) -> str:
        """Extract npm package name from error message."""
        patterns = [
            r"missing dependency: ([a-z0-9@/_-]+)",
            r"npm ERR! ([a-z0-9@/_-]+)",
            r"Cannot find module ['\"]([a-z0-9@/_-]+)['\"]",
        ]

        for pattern in patterns:
            match = re.search(pattern, error_content, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_python_module(self, error_content: str) -> str:
        """Extract Python module name from error message."""
        patterns = [
            r"No module named ['\"]([a-z0-9_]+)['\"]",
            r"ModuleNotFoundError: No module named ['\"]([a-z0-9_]+)['\"]",
        ]

        for pattern in patterns:
            match = re.search(pattern, error_content)
            if match:
                return match.group(1)

        return None

    def _extract_port_number(self, error_content: str) -> int:
        """Extract port number from error message."""
        match = re.search(r":(\d+)", error_content)
        return int(match.group(1)) if match else 3000

    def _extract_env_var_name(self, error_content: str) -> str:
        """Extract environment variable name from error message."""
        patterns = [
            r"environment variable ['\"]([A-Z_]+)['\"]",
            r"env\[['\""]([A-Z_]+)['\"]\]",
        ]

        for pattern in patterns:
            match = re.search(pattern, error_content, re.IGNORECASE)
            if match:
                return match.group(1)

        return "UNKNOWN"


def main():
    """Example usage."""

    # Configure paths
    RAILWAYBOT_PATH = "/path/to/RailwayBot"
    PROJECT_PATH = "/path/to/your/railway-project"

    # Create agent
    agent = AutonomousDeploymentAgent(
        railwaybot_path=RAILWAYBOT_PATH,
        project_path=PROJECT_PATH
    )

    # Run autonomous deployment loop
    result = agent.autonomous_deploy_loop()

    # Final report
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(f"Status: {result['status']}")

    if result.get("deployment"):
        print(f"Service: {result['deployment']['service']}")
        print(f"Environment: {result['deployment']['environment']}")
        print(f"Deployment Status: {result['deployment']['status']}")


if __name__ == "__main__":
    main()
