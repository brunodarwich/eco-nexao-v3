"""Unit tests for ContentService (ECO-0607)."""

import pytest

from app.schemas.envelopes import SupportContentEnvelope
from app.services.content_service import ContentService


@pytest.mark.asyncio
async def test_content_service_get_support_content() -> None:
    service = ContentService()
    result = await service.get_support_content()
    assert isinstance(result, SupportContentEnvelope)
    assert len(result.data.faq) >= 3
    assert result.data.contacts.email == "suporte@econexao.org"
    assert len(result.data.help_links) >= 3
    assert result.data.editorial_info.version == "1.0.0"
