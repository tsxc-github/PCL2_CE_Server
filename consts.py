from pathlib import Path

DATA_FOLDER: Path = Path(".data").resolve()

OSS_UPLOAD_FOLDER_OLD: Path = Path(".data/uploads_old").resolve()
OSS_UPLOAD_FOLDER: Path = Path(".data/uploads").resolve()

RELEASE_CONFIG_PATH: Path = Path(".data/channel_rules.json").resolve()
RELEASE_FILE_FOLDER: Path = Path(".data/release").resolve()
RELEASE_ANNOUNCEMENT_PATH: Path = Path(".data/announcement.json").resolve()

CHECKER_FONFIG_PATH: Path = Path(".data/checker.json").resolve()

ARCHIVE_RELEASE_FOLDER: Path = Path(".data/release_archive").resolve()