"""
Builds LLM and text embedder instances via GraphRAG's ModelFactory.
Compatible with graphrag >=2.7.
"""
from functools import lru_cache
from core.config import settings


def _chat_config():
    from graphrag.config.models.language_model_config import LanguageModelConfig
    from graphrag.config.enums import ModelType
    return LanguageModelConfig(
        type=ModelType.OpenAIChat,
        model="gpt-4o",
        api_key=settings.openai_api_key,
    )


def _embedding_config():
    from graphrag.config.models.language_model_config import LanguageModelConfig
    from graphrag.config.enums import ModelType
    return LanguageModelConfig(
        type=ModelType.OpenAIEmbedding,
        model="text-embedding-3-small",
        api_key=settings.openai_api_key,
    )


@lru_cache(maxsize=1)
def get_llm():
    from graphrag.language_model.factory import ModelFactory
    from graphrag.config.enums import ModelType
    return ModelFactory.create_chat_model(
        ModelType.OpenAIChat.value,
        name="mcp_chat",
        config=_chat_config(),
    )


@lru_cache(maxsize=1)
def get_text_embedder():
    from graphrag.language_model.factory import ModelFactory
    from graphrag.config.enums import ModelType
    return ModelFactory.create_embedding_model(
        ModelType.OpenAIEmbedding.value,
        name="mcp_embedding",
        config=_embedding_config(),
    )
