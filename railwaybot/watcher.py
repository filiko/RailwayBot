"""Railway deployment watcher."""

import time
import json
from typing import Optional, Dict, Any
from colorama import Fore, Style

from .railway_client import RailwayClient, RailwayClientError
from .log_parser import LogParser
from .clipboard import ClipboardManager


class DeploymentWatcher:
    """Monitor Railway deployments and extract errors on failure."""

    def __init__(
        self,
        client: RailwayClient,
        parser: LogParser,
        clipboard: ClipboardManager,
        poll_interval: int = 5,
        auto_copy: bool = True
    ):
        """
        Initialize deployment watcher.

        Args:
            client: Railway CLI client
            parser: Log parser
            clipboard: Clipboard manager
            poll_interval: Seconds between status checks
            auto_copy: Automatically copy errors to clipboard
        """
        self.client = client
        self.parser = parser
        self.clipboard = clipboard
        self.poll_interval = poll_interval
        self.auto_copy = auto_copy

        self.last_deployment_id: Optional[str] = None
        self.last_status: Optional[str] = None
        self.is_running = False

    def start(self) -> None:
        """Start watching deployments."""
        self.is_running = True

        print(f"{Fore.GREEN}RailwayBot started - monitoring deployments...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")

        # Verify Railway project is linked
        if not self.client.check_linked():
            print(f"{Fore.RED}Error: Not linked to a Railway project{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Run 'railway link' in your project directory{Style.RESET_ALL}")
            return

        try:
            self._watch_loop()
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}RailwayBot stopped by user{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}RailwayBot error: {e}{Style.RESET_ALL}")
        finally:
            self.is_running = False

    def _watch_loop(self) -> None:
        """Main watch loop."""
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.is_running:
            try:
                self._check_deployment()
                consecutive_errors = 0  # Reset on success

            except RailwayClientError as e:
                consecutive_errors += 1
                print(f"{Fore.RED}Railway CLI error: {e}{Style.RESET_ALL}")

                if consecutive_errors >= max_consecutive_errors:
                    print(f"{Fore.RED}Too many consecutive errors, stopping watcher{Style.RESET_ALL}")
                    break

                # Exponential backoff
                wait_time = min(30, self.poll_interval * (2 ** consecutive_errors))
                print(f"{Fore.YELLOW}Retrying in {wait_time}s...{Style.RESET_ALL}")
                time.sleep(wait_time)
                continue

            except Exception as e:
                print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
                time.sleep(self.poll_interval)
                continue

            time.sleep(self.poll_interval)

    def _check_deployment(self) -> None:
        """Check current deployment status."""
        status_data = self.client.get_status()

        # Extract relevant info from status
        # Note: Actual Railway CLI JSON structure may vary
        # This is a best-effort based on common patterns
        current_deployment = self._extract_deployment_info(status_data)

        if not current_deployment:
            # No active deployment
            return

        deployment_id = current_deployment.get('id')
        deployment_status = current_deployment.get('status', '').upper()

        # Check if this is a new deployment or status change
        is_new_deployment = deployment_id != self.last_deployment_id
        status_changed = deployment_status != self.last_status

        if is_new_deployment or status_changed:
            self._log_status_change(current_deployment, deployment_status)

        # Update tracking
        self.last_deployment_id = deployment_id
        self.last_status = deployment_status

        # Handle failure
        if deployment_status in ['FAILED', 'CRASHED', 'ERRORED']:
            self._handle_deployment_failure(current_deployment)

    def _extract_deployment_info(self, status_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract deployment info from status JSON."""
        # Railway CLI status output varies, adapt as needed
        # Common patterns:
        if isinstance(status_data, dict):
            # Look for deployment info in various possible keys
            deployment = (
                status_data.get('deployment') or
                status_data.get('latestDeployment') or
                status_data.get('currentDeployment')
            )

            if deployment:
                return deployment

            # Sometimes status_data itself is the deployment
            if 'id' in status_data and 'status' in status_data:
                return status_data

        return None

    def _log_status_change(self, deployment: Dict[str, Any], status: str) -> None:
        """Log deployment status changes."""
        service_name = deployment.get('serviceName', 'Unknown')
        environment = deployment.get('environment', 'production')

        status_color = {
            'BUILDING': Fore.BLUE,
            'DEPLOYING': Fore.CYAN,
            'SUCCESS': Fore.GREEN,
            'ACTIVE': Fore.GREEN,
            'FAILED': Fore.RED,
            'CRASHED': Fore.RED,
            'ERRORED': Fore.RED,
        }.get(status, Fore.YELLOW)

        print(f"{status_color}[{time.strftime('%H:%M:%S')}] "
              f"{service_name} ({environment}): {status}{Style.RESET_ALL}")

    def _handle_deployment_failure(self, deployment: Dict[str, Any]) -> None:
        """Handle deployment failure - extract and copy errors."""
        print(f"\n{Fore.RED}{'!' * 60}{Style.RESET_ALL}")
        print(f"{Fore.RED}Deployment failed - extracting errors...{Style.RESET_ALL}")
        print(f"{Fore.RED}{'!' * 60}{Style.RESET_ALL}\n")

        service_name = deployment.get('serviceName', 'Unknown')
        environment = deployment.get('environment', 'production')

        # Fetch logs
        try:
            print(f"{Fore.CYAN}Fetching build logs...{Style.RESET_ALL}")
            build_logs = self.client.get_logs(build=True, json_format=False)

            print(f"{Fore.CYAN}Fetching deployment logs...{Style.RESET_ALL}")
            deploy_logs = self.client.get_logs(deployment=False, json_format=False)

        except Exception as e:
            print(f"{Fore.RED}Failed to fetch logs: {e}{Style.RESET_ALL}")
            # Fallback to recent logs
            try:
                deploy_logs = self.client.get_recent_logs(lines=100)
                build_logs = ""
            except Exception:
                print(f"{Fore.RED}Could not retrieve any logs{Style.RESET_ALL}")
                return

        # Parse errors
        build_errors = self.parser.parse_logs(build_logs, "BUILD") if build_logs else []
        deploy_errors = self.parser.parse_logs(deploy_logs, "DEPLOYMENT") if deploy_logs else []

        # Format output
        formatted_errors = self.parser.format_errors(
            build_errors=build_errors,
            deploy_errors=deploy_errors,
            service_name=service_name,
            environment=environment
        )

        # Copy to clipboard
        if self.auto_copy:
            success = self.clipboard.copy(formatted_errors)
            if not success:
                print(f"\n{Fore.YELLOW}Error report:{Style.RESET_ALL}")
                print(formatted_errors)
        else:
            print(f"\n{Fore.YELLOW}Error report:{Style.RESET_ALL}")
            print(formatted_errors)

    def stop(self) -> None:
        """Stop the watcher."""
        self.is_running = False

    def check_once(self) -> Optional[str]:
        """
        Perform a single check (one-shot mode).

        Returns:
            Error report if deployment failed, None otherwise
        """
        if not self.client.check_linked():
            raise RailwayClientError("Not linked to a Railway project")

        status_data = self.client.get_status()
        deployment = self._extract_deployment_info(status_data)

        if not deployment:
            return None

        deployment_status = deployment.get('status', '').upper()

        if deployment_status in ['FAILED', 'CRASHED', 'ERRORED']:
            service_name = deployment.get('serviceName', 'Unknown')
            environment = deployment.get('environment', 'production')

            # Fetch and parse logs
            try:
                build_logs = self.client.get_logs(build=True, json_format=False)
                deploy_logs = self.client.get_logs(deployment=False, json_format=False)
            except Exception:
                deploy_logs = self.client.get_recent_logs(lines=100)
                build_logs = ""

            build_errors = self.parser.parse_logs(build_logs, "BUILD") if build_logs else []
            deploy_errors = self.parser.parse_logs(deploy_logs, "DEPLOYMENT") if deploy_logs else []

            formatted_errors = self.parser.format_errors(
                build_errors=build_errors,
                deploy_errors=deploy_errors,
                service_name=service_name,
                environment=environment
            )

            if self.auto_copy:
                self.clipboard.copy(formatted_errors)

            return formatted_errors

        return None
