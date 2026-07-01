"""Parse and extract errors from Railway logs."""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class LogParser:
    """Extract and format errors from Railway deployment logs."""

    ERROR_PATTERNS = [
        r'(?i)error:?\s+(.+)',
        r'(?i)exception:?\s+(.+)',
        r'(?i)failed:?\s+(.+)',
        r'(?i)ERR!\s+(.+)',
        r'(?i)fatal:?\s+(.+)',
        r'(?i)cannot\s+(.+)',
        r'exit code:\s*(\d+)',
        r'EADDRINUSE',
        r'ECONNREFUSED',
        r'MODULE_NOT_FOUND',
    ]

    def __init__(self, max_lines: int = 50, include_timestamps: bool = True):
        """
        Initialize log parser.

        Args:
            max_lines: Maximum lines to include per error section
            include_timestamps: Whether to include timestamps in output
        """
        self.max_lines = max_lines
        self.include_timestamps = include_timestamps

    def parse_logs(self, logs: str, log_type: str = "DEPLOYMENT") -> List[Dict[str, Any]]:
        """
        Parse logs and extract error information.

        Args:
            logs: Raw log content
            log_type: Type of logs (BUILD, DEPLOYMENT, etc.)

        Returns:
            List of error entries with metadata
        """
        errors = []
        lines = logs.split('\n')

        for i, line in enumerate(lines):
            if self._is_error_line(line):
                error_entry = {
                    'line_number': i + 1,
                    'content': line.strip(),
                    'type': log_type,
                    'timestamp': self._extract_timestamp(line)
                }

                # Get surrounding context (2 lines before and after)
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                error_entry['context'] = lines[context_start:context_end]

                errors.append(error_entry)

        return errors

    def _is_error_line(self, line: str) -> bool:
        """Check if line contains an error pattern."""
        for pattern in self.ERROR_PATTERNS:
            if re.search(pattern, line):
                return True
        return False

    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Try to extract timestamp from log line."""
        # Common Railway log timestamp patterns
        timestamp_patterns = [
            r'\[(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})',  # ISO format
            r'(\d{2}:\d{2}:\d{2})',  # Time only
        ]

        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)

        return None

    def format_errors(
        self,
        build_errors: List[Dict[str, Any]],
        deploy_errors: List[Dict[str, Any]],
        service_name: Optional[str] = None,
        environment: Optional[str] = None
    ) -> str:
        """
        Format errors for clipboard output.

        Args:
            build_errors: Errors from build logs
            deploy_errors: Errors from deployment logs
            service_name: Name of the service
            environment: Deployment environment

        Returns:
            Formatted error report
        """
        output_lines = [
            "=" * 60,
            "=== Railway Deployment Failed ===",
            "=" * 60,
        ]

        if service_name:
            output_lines.append(f"Service: {service_name}")
        if environment:
            output_lines.append(f"Environment: {environment}")

        output_lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append("")

        # Build errors section
        if build_errors:
            output_lines.append("BUILD ERRORS:")
            output_lines.append("-" * 60)

            for error in build_errors[:self.max_lines]:
                if self.include_timestamps and error.get('timestamp'):
                    output_lines.append(f"[{error['timestamp']}] Line {error['line_number']}")
                else:
                    output_lines.append(f"[Line {error['line_number']}]")

                output_lines.append(f"  {error['content']}")

                # Add context
                if error.get('context'):
                    output_lines.append("  Context:")
                    for ctx_line in error['context']:
                        if ctx_line.strip():
                            output_lines.append(f"    {ctx_line.strip()}")

                output_lines.append("")

        # Deploy errors section
        if deploy_errors:
            output_lines.append("DEPLOYMENT ERRORS:")
            output_lines.append("-" * 60)

            for error in deploy_errors[:self.max_lines]:
                if self.include_timestamps and error.get('timestamp'):
                    output_lines.append(f"[{error['timestamp']}] Line {error['line_number']}")
                else:
                    output_lines.append(f"[Line {error['line_number']}]")

                output_lines.append(f"  {error['content']}")

                # Add context
                if error.get('context'):
                    output_lines.append("  Context:")
                    for ctx_line in error['context']:
                        if ctx_line.strip():
                            output_lines.append(f"    {ctx_line.strip()}")

                output_lines.append("")

        if not build_errors and not deploy_errors:
            output_lines.append("No specific error patterns detected in logs.")
            output_lines.append("The deployment failed but error details are unclear.")
            output_lines.append("")

        output_lines.append("=" * 60)
        output_lines.append("=== End Error Report ===")
        output_lines.append("=" * 60)

        return '\n'.join(output_lines)

    def extract_from_plain_logs(self, logs: str) -> str:
        """
        Quick extraction from plain text logs.

        Args:
            logs: Plain text log content

        Returns:
            Formatted error lines
        """
        error_lines = []

        for line in logs.split('\n'):
            if self._is_error_line(line):
                error_lines.append(line.strip())

        if error_lines:
            return '\n'.join(error_lines[:self.max_lines])
        else:
            # Return last N lines if no specific errors found
            all_lines = [l.strip() for l in logs.split('\n') if l.strip()]
            return '\n'.join(all_lines[-20:])
