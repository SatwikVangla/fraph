from pathlib import Path


def build_file_path(directory: str, filename: str) -> Path:
    return Path(directory) / filename
