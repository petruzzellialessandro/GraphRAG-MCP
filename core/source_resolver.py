import pandas as pd
from core.data_loader import GraphData

# ID column names tried in order of preference
_SOURCE_ID_CANDIDATES = ("human_readable_id", "id", "chunk_id")
_TU_ID_CANDIDATES = ("human_readable_id", "id")


def resolve_sources(sources, data: GraphData) -> list[dict]:
    """Map GraphRAG context sources (DataFrame, list, or dict) to document-traceable records."""
    if sources is None or data.text_units is None:
        return []

    # Normalise to DataFrame — GraphRAG may return a list[dict] or a DataFrame
    if not isinstance(sources, pd.DataFrame):
        try:
            sources = pd.DataFrame(sources)
        except Exception:
            return []

    if sources.empty:
        return []

    src_id_col = next((c for c in _SOURCE_ID_CANDIDATES if c in sources.columns), None)
    if src_id_col is None:
        return []

    tu_id_col = next((c for c in _TU_ID_CANDIDATES if c in data.text_units.columns), None)
    if tu_id_col is None:
        return []

    keep_cols = [c for c in [tu_id_col, "document_ids", "text"] if c in data.text_units.columns]

    try:
        merged = sources[[src_id_col]].merge(
            data.text_units[keep_cols],
            left_on=src_id_col,
            right_on=tu_id_col,
            how="left",
        )
    except Exception:
        return []

    results = []
    for _, row in merged.iterrows():
        doc_title = _resolve_doc_title(row.get("document_ids"), data.documents)
        results.append({
            "text_unit_id": str(row.get(src_id_col, "")),
            "document": doc_title,
            "text_preview": str(row.get("text", ""))[:300],
        })
    return results


def _resolve_doc_title(doc_ids, documents_df: pd.DataFrame | None) -> str:
    if not doc_ids or documents_df is None:
        return "unknown"
    doc_id = doc_ids[0] if isinstance(doc_ids, list) else doc_ids
    match = documents_df[documents_df["id"] == doc_id]
    return match["title"].iloc[0] if not match.empty else "unknown"
