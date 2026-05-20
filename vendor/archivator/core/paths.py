from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]

APP_DIR = Path.home() / ".archivator"
CONFIG_PATH = APP_DIR / "projects.json"
DATA_PATH = APP_DIR / "data"
THUMBNAILS_PATH = DATA_PATH / "thumbnails"

UI_PATH = PACKAGE_ROOT / "ui" / "view" / "interface.ui"
PLACEHOLDER_PATH = PACKAGE_ROOT / "ui" / "resources" / "placeholder.png"


def ensure_app_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    THUMBNAILS_PATH.mkdir(parents=True, exist_ok=True)