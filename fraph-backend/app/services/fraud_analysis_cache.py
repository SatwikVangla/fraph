import json
from pathlib import Path

FRAUD_ANALYSIS_CACHE_VERSION = 2


def build_fraud_analysis_cache_path(dataset_path: str | Path) -> Path:
    path = Path(dataset_path)
    return path.with_suffix(f"{path.suffix}.fraud.cache.json")


def _cache_key(*, threshold: float, limit: int) -> str:
    return f"threshold={threshold:.4f}|limit={limit}"


def get_cached_fraud_analysis(
    dataset_path: str | Path,
    *,
    threshold: float,
    limit: int,
) -> dict[str, object] | None:
    path = Path(dataset_path)
    cache_path = build_fraud_analysis_cache_path(path)
    if not cache_path.exists():
        return None

    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    if payload.get("cache_version") != FRAUD_ANALYSIS_CACHE_VERSION:
        return None

    dataset_stat = path.stat()
    cache_mtime = payload.get("dataset_mtime_ns")
    cache_size = payload.get("dataset_size")
    if cache_mtime != dataset_stat.st_mtime_ns or cache_size != dataset_stat.st_size:
        return None

    entries = payload.get("entries")
    if not isinstance(entries, dict):
        return None

    result = entries.get(_cache_key(threshold=threshold, limit=limit))
    return result if isinstance(result, dict) else None


def set_cached_fraud_analysis(
    dataset_path: str | Path,
    *,
    threshold: float,
    limit: int,
    result: dict[str, object],
) -> None:
    path = Path(dataset_path)
    cache_path = build_fraud_analysis_cache_path(path)
    dataset_stat = path.stat()

    payload = {
        "cache_version": FRAUD_ANALYSIS_CACHE_VERSION,
        "dataset_mtime_ns": dataset_stat.st_mtime_ns,
        "dataset_size": dataset_stat.st_size,
        "entries": {
            _cache_key(threshold=threshold, limit=limit): result,
        },
    }

    if cache_path.exists():
        try:
            existing = json.loads(cache_path.read_text(encoding="utf-8"))
            if (
                isinstance(existing, dict)
                and existing.get("cache_version") == FRAUD_ANALYSIS_CACHE_VERSION
                and existing.get("dataset_mtime_ns") == dataset_stat.st_mtime_ns
                and existing.get("dataset_size") == dataset_stat.st_size
                and isinstance(existing.get("entries"), dict)
            ):
                payload["entries"] = {
                    **existing["entries"],
                    _cache_key(threshold=threshold, limit=limit): result,
                }
        except (OSError, json.JSONDecodeError):
            pass

    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
