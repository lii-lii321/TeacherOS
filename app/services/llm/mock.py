class MockProvider:
    """Deterministic offline provider.

    TeacherOS core flows (note parsing, homework drafts, parent messages) are
    rule-based by design so the product works with zero API keys. When a real
    provider is configured, `copilot_service.enrich_with_llm` upgrades the
    structured extraction; everything still degrades gracefully to rules.
    """

    name = "mock"

    async def complete(self, system: str, user: str) -> str:
        return ""
