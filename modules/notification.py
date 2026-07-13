from plyer import notification


def trigger_windows_notification(title, message):
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="BusinessPilot AI",
            timeout=5
        )
    except Exception:
        pass
