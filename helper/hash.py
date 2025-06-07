import hashlib
from pathlib import Path

def get_file_sha256(file_path: str) -> str:
    if not Path(file_path).exists():
        return ""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
    
def get_file_md5(file_path: str) -> str:
    if not Path(file_path).exists():
        return ""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()
