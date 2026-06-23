from app.core.config import Settings
from app.services.ai.base import AIProvider
from app.services.ai.real import RealAIProvider
from app.services.ai.stub import StubAIProvider


def build_ai_provider(settings: Settings) -> AIProvider:
    if settings.llm_api_key:
        return RealAIProvider(settings=settings)
    return StubAIProvider()
