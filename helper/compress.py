import zipfile
from pathlib import Path
from typing import Optional

def compress_target_file(input_file_path: str, in_zip_file_name: str, output_path: str):
    with zipfile.ZipFile(output_path, mode="w",compression=zipfile.ZIP_DEFLATED) as compressed_file:
        compressed_file.write(
                filename=input_file_path,
                arcname=in_zip_file_name
            )
    