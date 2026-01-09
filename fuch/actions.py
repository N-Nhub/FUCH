# fuch/actions.py
import subprocess

APP_COMMANDS = {
    "spotify": ["flatpak", "run", "com.spotify.Client"],
    "firefox": ["firefox"],
    "browser": ["firefox"],
    "terminal": ["kitty"],  # change if needed
}

def open_app(app: str) -> bool:
    if app not in APP_COMMANDS:
        return False

    try:
        subprocess.Popen(
            APP_COMMANDS[app],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return True
    except Exception:
        return False

