from __future__ import annotations
from core.data_loader import GraphData


def graph_expand(data: GraphData, entity_titles: list[str], hops: int = 2) -> list[dict]:
    """Expand N hops from seed entities using the relationships DataFrame (pure Pandas)."""
    if not entity_titles:
        return []

    rels = data.relationships
    entities = data.entities

    visited_lower: set[str] = {t.lower() for t in entity_titles}
    frontier_lower: set[str] = set(visited_lower)

    for _ in range(hops):
        mask = (
            rels["source"].str.lower().isin(frontier_lower)
            | rels["target"].str.lower().isin(frontier_lower)
        )
        connected = (
            set(rels[mask]["source"].str.lower())
            | set(rels[mask]["target"].str.lower())
        )
        new = connected - visited_lower
        if not new:
            break
        visited_lower |= new
        frontier_lower = new

    result_titles = visited_lower - {t.lower() for t in entity_titles}
    mask = entities["title"].str.lower().isin(result_titles)
    return entities[mask][["title", "description", "type"]].to_dict("records")
