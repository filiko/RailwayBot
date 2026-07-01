"""Wrapper for Railway CLI commands."""

import json
import os
import shutil
import subprocess
from typing import Optional, Dict, Any, List


class RailwayClientError(Exception):
    """Raised when Railway CLI operations fail."""
    pass


class RailwayClient:
    """Interface to Railway CLI."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize Railway client.

        Args:
            token: Railway API token (will be set in RAILWAY_TOKEN env var)
        """
        self.token = token
        self.railway_exe = self._find_railway_cli()

    def _find_railway_cli(self) -> str:
        """
        Find Railway CLI executable path.

        Returns:
            Full path to Railway CLI executable

        Raises:
            RailwayClientError: If Railway CLI is not found
        """
        railway_exe = shutil.which("railway")

        if not railway_exe:
            raise RailwayClientError(
                "Railway CLI not found in PATH. Install from: https://docs.railway.app/develop/cli"
            )

        return railway_exe

    def _check_cli_installed(self) -> None:
        """Verify Railway CLI is installed and working."""
        try:
            result = subprocess.run(
                [self.railway_exe, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RailwayClientError("Railway CLI found but returned error")
        except FileNotFoundError:
            raise RailwayClientError(
                "Railway CLI not found. Install from: https://docs.railway.app/develop/cli"
            )
        except subprocess.TimeoutExpired:
            raise RailwayClientError("Railway CLI command timed out")

    def _run_command(
        self,
        args: List[str],
        check: bool = True,
        timeout: int = 30
    ) -> subprocess.CompletedProcess:
        """
        Run a Railway CLI command.

        Args:
            args: Command arguments (excluding 'railway')
            check: Whether to raise on non-zero exit
            timeout: Command timeout in seconds

        Returns:
            CompletedProcess instance
        """
        # Use full path to Railway CLI for Windows compatibility
        cmd = [self.railway_exe] + args

        env = None
        if self.token:
            env = os.environ.copy()
            env["RAILWAY_TOKEN"] = self.token

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            raise RailwayClientError(f"Railway command failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RailwayClientError(f"Command timed out after {timeout}s")
        except FileNotFoundError:
            raise RailwayClientError(
                f"Railway CLI not found at {self.railway_exe}. Please reinstall."
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get current project status.

        Returns:
            Status information as dict
        """
        result = self._run_command(["status", "--json"])
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            raise RailwayClientError("Failed to parse status JSON")

    def get_logs(
        self,
        build: bool = False,
        deployment: bool = False,
        json_format: bool = True,
        limit: int = 100
    ) -> str:
        """
        Fetch logs from Railway.

        Args:
            build: Get build logs only
            deployment: Get deployment logs only
            json_format: Return JSON format
            limit: Maximum number of log lines

        Returns:
            Log output as string (JSON or plain text)
        """
        args = ["logs"]

        if build:
            args.append("--build")
        elif deployment:
            args.append("--deployment")

        if json_format:
            args.append("--json")

        # Railway CLI doesn't have a direct limit flag, but we can use shell features
        # For now, fetch all and truncate in parsing

        result = self._run_command(args, timeout=60)
        return result.stdout

    def get_recent_logs(self, lines: int = 100) -> str:
        """
        Get most recent logs.

        Args:
            lines: Number of recent lines to fetch

        Returns:
            Log output
        """
        # Railway CLI streams logs, so we'll fetch and take last N lines
        result = self._run_command(["logs"], timeout=30)
        log_lines = result.stdout.strip().split('\n')
        return '\n'.join(log_lines[-lines:])

    def check_linked(self) -> bool:
        """
        Check if current directory is linked to a Railway project.

        Returns:
            True if linked, False otherwise
        """
        try:
            self.get_status()
            return True
        except RailwayClientError:
            return False

    def whoami(self) -> Dict[str, Any]:
        """
        Get authenticated user information.

        Returns:
            User info dict
        """
        result = self._run_command(["whoami", "--json"])
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            raise RailwayClientError("Failed to parse whoami JSON")
