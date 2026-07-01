"""RailwayBot - Automated Railway deployment error monitoring and extraction."""

__version__ = "0.1.0"

# Main exports for programmatic use
from .railway_client import RailwayClient, RailwayClientError
from .log_parser import LogParser
from .clipboard import ClipboardManager
from .watcher import DeploymentWatcher
from .agent_api import AgentAPI

__all__ = [
    "RailwayClient",
    "RailwayClientError",
    "LogParser",
    "ClipboardManager",
    "DeploymentWatcher",
    "AgentAPI",
]
