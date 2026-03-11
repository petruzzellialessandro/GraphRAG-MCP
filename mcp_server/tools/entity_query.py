from core.data_loader import load_all

async def list_entities_tool(entity_type: str | None = None) -> dict:
    data = load_all()
    # GraphRAG 3.x uses "title" column, not "name"
    df = data.entities
    if entity_type:
        df = df[df["type"].str.lower() == entity_type.lower()]
    entities = df[["title", "type", "description"]].head(100).to_dict("records")
    return {"entities": entities, "total": len(entities)}

async def get_entity_tool(name: str) -> dict:
    data = load_all()
    match = data.entities[data.entities["title"].str.lower() == name.lower()]
    if match.empty:
        return {"error": f"Entity '{name}' not found"}
    entity = match.iloc[0].to_dict()
    # Find direct relationships
    rels = data.relationships[
        (data.relationships["source"].str.lower() == name.lower()) |
        (data.relationships["target"].str.lower() == name.lower())
    ][["source", "target", "description", "weight"]].head(20).to_dict("records")
    return {"entity": entity, "relationships": rels}
