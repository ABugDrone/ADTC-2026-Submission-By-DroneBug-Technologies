"""
Windows toast notifications — uses Windows 10+ native Action Center.
Falls back gracefully if notification fails.
"""

import logging
import platform

logger = logging.getLogger(__name__)


def trigger_windows_notification(title: str, message: str) -> None:
    """
    Show a Windows toast notification.

    Uses plyer which calls the native Windows 10+ notification API.
    Fully offline — no network calls.
    Silently handles errors without crashing the app.
    """
    if platform.system() != "Windows":
        return

    try:
        from plyer import notification

        notification.notify(
            title=title,
            message=message,
            app_name="BusinessPilot AI",
            app_icon=None,
            timeout=5,
        )
    except ImportError:
        # plyer not installed — skip notification
        pass
    except Exception as exc:
        # Notification failed (e.g., app not registered) — log but don't crash
        logger.debug("Notification failed: %s", exc)
