"""Agent-friendly API for RailwayBot - callable by coding agents."""

import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from .railway_client import RailwayClient, RailwayClientError
from .log_parser import LogParser


class AgentAPI:
    """
    Simplified API for coding agents to check Railway deployments.

    Returns JSON output for easy parsing by AI agents.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize agent API."""
        if config_path is None:
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Initialize components
        railway_token = self._get_railway_token()
        self.client = RailwayClient(token=railway_token)
        self.parser = LogParser(
            max_lines=self.config.get('formatting', {}).get('max_lines_per_error', 50),
            include_timestamps=True
        )

    def _load_config(self) -> dict:
        """Load configuration or return defaults."""
        if not self.config_path.exists():
            return {
                "railway": {"token_env_var": "RAILWAY_TOKEN"},
                "formatting": {"max_lines_per_error": 50}
            }

        with open(self.config_path, 'r') as f:
            return json.load(f)

    def _get_railway_token(self) -> Optional[str]:
        """Get Railway token from environment."""
        import os
        token_env_var = self.config.get('railway', {}).get('token_env_var', 'RAILWAY_TOKEN')
        return os.environ.get(token_env_var)

    def check_deployment(self) -> Dict[str, Any]:
        """
        Check current Railway deployment status.

        Returns JSON-serializable dict with structure:
        {
            "status": "ok" | "failed" | "error",
            "deployment": {
                "id": "...",
                "status": "...",
                "service": "...",
                "environment": "..."
            },
            "errors": {
                "build": [...],
                "deploy": [...]
            },
            "formatted_report": "...",  # Human-readable error report
            "message": "..."  # Status message
        }
        """
        result = {
            "status": "ok",
            "deployment": None,
            "errors": {
                "build": [],
                "deploy": []
            },
            "formatted_report": "",
            "message": ""
        }

        try:
            # Check if linked to Railway project
            if not self.client.check_linked():
                result["status"] = "error"
                result["message"] = "Not linked to a Railway project. Run 'railway link' in your project directory."
                return result

            # Get deployment status
            status_data = self.client.get_status()
            deployment = self._extract_deployment_info(status_data)

            if not deployment:
                result["message"] = "No active deployment found"
                return result

            # Extract deployment info
            deployment_status = deployment.get('status', '').upper()
            result["deployment"] = {
                "id": deployment.get('id', ''),
                "status": deployment_status,
                "service": deployment.get('serviceName', 'Unknown'),
                "environment": deployment.get('environment', 'production')
            }

            # Check if deployment failed
            if deployment_status in ['FAILED', 'CRASHED', 'ERRORED']:
                result["status"] = "failed"
                result["message"] = f"Deployment {deployment_status}"

                # Fetch logs
                try:
                    build_logs = self.client.get_logs(build=True, json_format=False)
                    deploy_logs = self.client.get_logs(deployment=False, json_format=False)
                except Exception:
                    deploy_logs = self.client.get_recent_logs(lines=100)
                    build_logs = ""

                # Parse errors
                build_errors = self.parser.parse_logs(build_logs, "BUILD") if build_logs else []
                deploy_errors = self.parser.parse_logs(deploy_logs, "DEPLOYMENT") if deploy_logs else []

                # Store structured errors
                result["errors"]["build"] = build_errors
                result["errors"]["deploy"] = deploy_errors

                # Generate formatted report
                result["formatted_report"] = self.parser.format_errors(
                    build_errors=build_errors,
                    deploy_errors=deploy_errors,
                    service_name=result["deployment"]["service"],
                    environment=result["deployment"]["environment"]
                )
            else:
                result["message"] = f"Deployment status: {deployment_status}"

        except RailwayClientError as e:
            result["status"] = "error"
            result["message"] = str(e)

        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Unexpected error: {str(e)}"

        return result

    def _extract_deployment_info(self, status_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract deployment info from status JSON."""
        if isinstance(status_data, dict):
            deployment = (
                status_data.get('deployment') or
                status_data.get('latestDeployment') or
                status_data.get('currentDeployment')
            )

            if deployment:
                return deployment

            if 'id' in status_data and 'status' in status_data:
                return status_data

            # Railway CLI v4 status returns deployments nested under:
            # environments.edges[].node.serviceInstances.edges[].node.latestDeployment
            environments = status_data.get('environments', {}).get('edges', [])
            newest_deployment = None
            newest_created_at = ''

            for env_edge in environments:
                env_node = env_edge.get('node', {}) if isinstance(env_edge, dict) else {}
                environment_name = env_node.get('name', 'production')
                service_edges = (
                    env_node
                    .get('serviceInstances', {})
                    .get('edges', [])
                )

                for service_edge in service_edges:
                    service_node = service_edge.get('node', {}) if isinstance(service_edge, dict) else {}
                    candidates = []

                    latest = service_node.get('latestDeployment')
                    if latest:
                        candidates.append(latest)

                    active = service_node.get('activeDeployments') or []
                    candidates.extend(active)

                    for candidate in candidates:
                        if not isinstance(candidate, dict):
                            continue

                        created_at = candidate.get('createdAt', '')
                        enriched = {
                            **candidate,
                            'serviceName': service_node.get('serviceName', 'Unknown'),
                            'environment': environment_name,
                        }

                        domains = service_node.get('domains', {})
                        service_domains = domains.get('serviceDomains') or []
                        if service_domains:
                            domain = service_domains[0].get('domain')
                            if domain:
                                enriched['url'] = f'https://{domain}'

                        if newest_deployment is None or created_at > newest_created_at:
                            newest_deployment = enriched
                            newest_created_at = created_at

            if newest_deployment:
                return newest_deployment

        return None

    def get_error_summary(self) -> str:
        """
        Get a brief error summary suitable for agent decision-making.

        Returns: Brief string summary of deployment status
        """
        result = self.check_deployment()

        if result["status"] == "error":
            return f"ERROR: {result['message']}"

        if result["status"] == "failed":
            build_count = len(result["errors"]["build"])
            deploy_count = len(result["errors"]["deploy"])
            return f"FAILED: Deployment Failed - {build_count} build errors, {deploy_count} deploy errors"

        if result["deployment"]:
            status = result["deployment"]["status"]
            return f"OK: Deployment {status}"

        return "OK: No active deployment"


def main():
    """
    CLI entry point for agent API.

    Usage:
        python -m railwaybot.agent_api            # Returns JSON
        python -m railwaybot.agent_api --summary  # Returns brief summary
    """
    import argparse

    parser = argparse.ArgumentParser(description="Agent-friendly Railway deployment checker")
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Return brief summary instead of full JSON'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'text'],
        default='json',
        help='Output format (default: json)'
    )

    args = parser.parse_args()

    api = AgentAPI()

    if args.summary:
        # Brief summary mode
        print(api.get_error_summary())
    else:
        # Full JSON mode
        result = api.check_deployment()

        if args.format == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Text format
            if result["status"] == "failed" and result["formatted_report"]:
                print(result["formatted_report"])
            else:
                print(result["message"])


if __name__ == '__main__':
    main()
