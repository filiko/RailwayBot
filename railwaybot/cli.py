"""Command-line interface for RailwayBot."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional
from colorama import Fore, Style, init

from .railway_client import RailwayClient, RailwayClientError
from .log_parser import LogParser
from .clipboard import ClipboardManager
from .watcher import DeploymentWatcher

# Initialize colorama
init(autoreset=True)


class RailwayBot:
    """Main RailwayBot application."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize RailwayBot.

        Args:
            config_path: Path to config.json (defaults to project root)
        """
        if config_path is None:
            # Default to config.json in RailwayBot directory
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Initialize components
        railway_token = self._get_railway_token()
        self.client = RailwayClient(token=railway_token)

        self.parser = LogParser(
            max_lines=self.config['formatting']['max_lines_per_error'],
            include_timestamps=self.config['formatting']['include_timestamps']
        )

        self.clipboard = ClipboardManager(
            notify_enabled=self.config['notifications']['enabled'],
            sound_enabled=self.config['notifications']['sound']
        )

        self.watcher = DeploymentWatcher(
            client=self.client,
            parser=self.parser,
            clipboard=self.clipboard,
            poll_interval=self.config['railway']['poll_interval_seconds'],
            auto_copy=self.config['railway']['auto_copy']
        )

    def _load_config(self) -> dict:
        """Load configuration from file."""
        if not self.config_path.exists():
            # Create default config
            print(f"{Fore.YELLOW}Config file not found at {self.config_path}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Creating default configuration...{Style.RESET_ALL}")

            default_config = {
                "railway": {
                    "token_env_var": "RAILWAY_TOKEN",
                    "poll_interval_seconds": 5,
                    "auto_copy": True
                },
                "formatting": {
                    "include_timestamps": True,
                    "max_lines_per_error": 50,
                    "highlight_keywords": ["error", "failed", "exception", "Error:", "ERR!"]
                },
                "notifications": {
                    "enabled": True,
                    "sound": False
                }
            }

            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)

            return default_config

        with open(self.config_path, 'r') as f:
            return json.load(f)

    def _get_railway_token(self) -> Optional[str]:
        """Get Railway token from environment variable."""
        token_env_var = self.config['railway'].get('token_env_var', 'RAILWAY_TOKEN')
        token = os.environ.get(token_env_var)

        if not token:
            print(f"{Fore.YELLOW}Warning: {token_env_var} not set{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Railway CLI will use default authentication{Style.RESET_ALL}")

        return token

    def watch(self) -> None:
        """Start watching deployments."""
        self.watcher.start()

    def check(self) -> None:
        """Perform one-shot check."""
        print(f"{Fore.CYAN}Checking Railway deployment status...{Style.RESET_ALL}")

        try:
            result = self.watcher.check_once()

            if result:
                print(f"\n{Fore.RED}Deployment has failed!{Style.RESET_ALL}")
                if self.config['railway']['auto_copy']:
                    print(f"{Fore.GREEN}Errors copied to clipboard{Style.RESET_ALL}")
                else:
                    print(result)
            else:
                print(f"{Fore.GREEN}No deployment failures detected{Style.RESET_ALL}")

        except RailwayClientError as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            sys.exit(1)

    def show_config(self) -> None:
        """Display current configuration."""
        print(f"{Fore.CYAN}Current configuration:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Config file: {self.config_path}{Style.RESET_ALL}\n")

        print(json.dumps(self.config, indent=2))

        print(f"\n{Fore.YELLOW}To edit configuration:{Style.RESET_ALL}")
        print(f"  Edit {self.config_path}")
        print(f"  Or set RAILWAY_TOKEN environment variable")

    def test_connection(self) -> None:
        """Test Railway CLI connection."""
        print(f"{Fore.CYAN}Testing Railway CLI connection...{Style.RESET_ALL}\n")

        try:
            # Test whoami
            user_info = self.client.whoami()
            print(f"{Fore.GREEN}✓ Railway CLI authenticated{Style.RESET_ALL}")
            print(f"  User: {user_info.get('name', 'Unknown')}")
            print(f"  Email: {user_info.get('email', 'Unknown')}")

            # Test project link
            if self.client.check_linked():
                status = self.client.get_status()
                print(f"\n{Fore.GREEN}✓ Project linked{Style.RESET_ALL}")
                # Print project details based on status structure
                print(f"  Status: {json.dumps(status, indent=2)}")
            else:
                print(f"\n{Fore.YELLOW}⚠ Not linked to a Railway project{Style.RESET_ALL}")
                print(f"  Run 'railway link' in your project directory")

        except RailwayClientError as e:
            print(f"{Fore.RED}✗ Connection failed: {e}{Style.RESET_ALL}")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RailwayBot - Automated Railway deployment error monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m railwaybot watch              Start monitoring deployments
  python -m railwaybot check              One-shot check for errors
  python -m railwaybot config             Show configuration
  python -m railwaybot test               Test Railway CLI connection
        """
    )

    parser.add_argument(
        'command',
        choices=['watch', 'check', 'config', 'test'],
        help='Command to execute'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to config.json (default: RailwayBot/config.json)'
    )

    args = parser.parse_args()

    try:
        bot = RailwayBot(config_path=args.config)

        if args.command == 'watch':
            bot.watch()
        elif args.command == 'check':
            bot.check()
        elif args.command == 'config':
            bot.show_config()
        elif args.command == 'test':
            bot.test_connection()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == '__main__':
    main()
