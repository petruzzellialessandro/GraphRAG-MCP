from functools import lru_cache
import importlib.metadata

@lru_cache(maxsize=1)
def graphrag_version() -> tuple[int, int, int]:
    """Return GraphRAG version as (major, minor, patch) tuple."""
    try:
        raw = importlib.metadata.version("graphrag")
        parts = raw.split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2].split("a")[0].split("b")[0].split("rc")[0]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except Exception:
        return (0, 0, 0)

def is_v3_or_above() -> bool:
    return graphrag_version()[0] >= 3
