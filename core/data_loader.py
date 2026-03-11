from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import pandas as pd
from core.config import settings

@dataclass
class GraphData:
    entities: pd.DataFrame
    relationships: pd.DataFrame
    communities: pd.DataFrame
    community_reports: pd.DataFrame
    text_units: pd.DataFrame
    documents: pd.DataFrame | None = None


def _resolve_parquet(out: Path, name: str) -> Path:
    """Resolve a parquet path, checking without prefix first, then with 'create_final_'."""
    plain = out / f"{name}.parquet"
    if plain.exists():
        return plain
    prefixed = out / f"create_final_{name}.parquet"
    if prefixed.exists():
        return prefixed
    raise FileNotFoundError(
        f"Cannot find '{name}.parquet' or 'create_final_{name}.parquet' in {out}"
    )


def _optional_parquet(out: Path, name: str) -> Path | None:
    """Like _resolve_parquet but returns None instead of raising if neither file exists."""
    plain = out / f"{name}.parquet"
    if plain.exists():
        return plain
    prefixed = out / f"create_final_{name}.parquet"
    if prefixed.exists():
        return prefixed
    return None


@lru_cache(maxsize=1)
def load_all() -> GraphData:
    out = Path(settings.graphrag_output_dir)
    docs_path = _optional_parquet(out, "documents")
    return GraphData(
        entities=pd.read_parquet(_resolve_parquet(out, "entities")),
        relationships=pd.read_parquet(_resolve_parquet(out, "relationships")),
        communities=pd.read_parquet(_resolve_parquet(out, "communities")),
        community_reports=pd.read_parquet(_resolve_parquet(out, "community_reports")),
        text_units=pd.read_parquet(_resolve_parquet(out, "text_units")),
        documents=pd.read_parquet(docs_path) if docs_path else None,
    )
