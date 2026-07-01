#!/usr/bin/env python
"""
Standalone wrapper for RailwayBot agent API.
This can be called from any directory without installation.

Usage:
    python path/to/railwaybot-check.py --summary
    python path/to/railwaybot-check.py           # JSON output
    python path/to/railwaybot-check.py --format text
"""

import sys
import os
from pathlib import Path

# Add RailwayBot to path
railwaybot_dir = Path(__file__).parent
sys.path.insert(0, str(railwaybot_dir))

# Import and run the agent API
from railwaybot.agent_api import main

if __name__ == '__main__':
    main()
