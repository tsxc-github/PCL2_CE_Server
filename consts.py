from pathlib import Path

DATA_FOLDER: Path = Path(".data").resolve()

OSS_UPLOAD_FOLDER: Path = Path(".data/uploads").resolve()

RELEASE_CONFIG_PATH: Path = Path(".data/channel_rules.json").resolve()
RELEASE_FILE_FOLDER: Path = Path(".data/release").resolve()
RELEASE_ANNOUNCEMENT_PATH: Path = Path(".data/announcement.json").resolve()

RELEASE_ARCHIVE_INNER_FILE_NAME: str = "Plain Craft Launcher Community Edition.exe"