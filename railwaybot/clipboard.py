"""Clipboard operations and notifications."""

import pyperclip
from colorama import Fore, Style, init

# Initialize colorama for Windows color support
init(autoreset=True)


class ClipboardManager:
    """Handle clipboard operations and user notifications."""

    def __init__(self, notify_enabled: bool = True, sound_enabled: bool = False):
        """
        Initialize clipboard manager.

        Args:
            notify_enabled: Show console notifications
            sound_enabled: Play sound on clipboard copy
        """
        self.notify_enabled = notify_enabled
        self.sound_enabled = sound_enabled

    def copy(self, text: str, notify: bool = True) -> bool:
        """
        Copy text to clipboard.

        Args:
            text: Text to copy
            notify: Show notification

        Returns:
            True if successful, False otherwise
        """
        try:
            pyperclip.copy(text)

            if notify and self.notify_enabled:
                self._show_notification(text)

            if self.sound_enabled:
                self._play_sound()

            return True

        except Exception as e:
            print(f"{Fore.RED}Failed to copy to clipboard: {e}{Style.RESET_ALL}")
            return False

    def _show_notification(self, text: str) -> None:
        """Show console notification about clipboard copy."""
        print(f"\n{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Errors copied to clipboard!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Paste into your coding assistant (Ctrl+V){Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}\n")

        # Show preview of first few lines
        preview_lines = text.split('\n')[:5]
        print(f"{Fore.CYAN}Preview:{Style.RESET_ALL}")
        for line in preview_lines:
            print(f"{Fore.CYAN}{line}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}...{Style.RESET_ALL}\n")

    def _play_sound(self) -> None:
        """Play notification sound (Windows beep)."""
        try:
            import winsound
            winsound.Beep(1000, 200)  # 1000 Hz for 200ms
        except ImportError:
            # Not on Windows or winsound not available
            pass
        except Exception:
            # Sound failed, ignore
            pass

    def get_clipboard(self) -> str:
        """
        Get current clipboard content.

        Returns:
            Clipboard text content
        """
        try:
            return pyperclip.paste()
        except Exception:
            return ""
