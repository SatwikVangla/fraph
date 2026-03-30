import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_DIR = PROJECT_ROOT / "datasets"
TRAINED_MODELS_DIR = PROJECT_ROOT / "trained_models"


def build_file_path(directory: str, filename: str) -> Path:
    return Path(directory) / filename


def ensure_runtime_directories() -> None:
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)


def slugify_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned or "dataset"


def build_dataset_storage_path(filename: str) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    original = Path(filename or "dataset.csv")
    safe_stem = slugify_name(original.stem)
    safe_suffix = original.suffix.lower() or ".csv"
    return DATASETS_DIR / f"{timestamp}-{safe_stem}{safe_suffix}"


def build_model_storage_path(
    dataset_name: str,
    model_name: str,
    extension: str,
) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    dataset_directory = TRAINED_MODELS_DIR / slugify_name(dataset_name)
    dataset_directory.mkdir(parents=True, exist_ok=True)
    safe_model_name = slugify_name(model_name)
    safe_extension = extension if extension.startswith(".") else f".{extension}"
    return dataset_directory / f"{timestamp}-{safe_model_name}{safe_extension}"
