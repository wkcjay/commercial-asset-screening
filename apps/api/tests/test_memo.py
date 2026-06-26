import json

from app.config import Settings
from app.services.assessment import assess_site
from app.services import memo as memo_service
from app.services.memo import generate_memo


def test_fallback_memo_generation(test_engine):
    assessment = assess_site(test_engine, "site-queenstown-001").assessment
    result = generate_memo(test_engine, assessment, "investment-committee")
    assert result.cache_meta.hit is False
    assert result.data.generation.provider == "fallback"
    assert result.data.memo.confidenceLevel == assessment.confidence.level
    assert result.data.memo.recommendation.nextDiligenceSteps


def test_memo_cache_miss_then_hit(test_engine):
    assessment = assess_site(test_engine, "site-queenstown-001").assessment
    first = generate_memo(test_engine, assessment, "investment-committee")
    second = generate_memo(test_engine, assessment, "investment-committee")
    assert first.cache_meta.hit is False
    assert second.cache_meta.hit is True
    assert first.data.assessmentId == second.data.assessmentId


def test_ai_memo_generation_uses_openai_compatible_provider(test_engine, monkeypatch):
    assessment = assess_site(test_engine, "site-queenstown-001").assessment
    settings = Settings(
        enable_ai_memo=True,
        ai_api_key="test-key",
        ai_model="test-model",
        ai_base_url="https://example.test/v1",
    )

    def fake_request(settings, messages):
        assert settings.ai_model == "test-model"
        assert messages[0]["role"] == "system"
        return json.dumps(
            {
                "executiveSummary": "AI generated summary.",
                "siteContext": "AI site context.",
                "comparableTransactionView": "AI comparable view.",
                "accessibilityAndAmenities": "AI amenities view.",
                "demographicContext": "AI demographic view.",
                "planningContext": "AI planning view.",
                "risksAndAssumptions": "AI risk view.",
                "recommendation": {
                    "stance": "hold",
                    "rationale": "AI rationale.",
                    "nextDiligenceSteps": ["Verify source evidence."],
                },
                "confidenceLevel": assessment.confidence.level,
                "confidenceRationale": "AI confidence rationale.",
                "sourceUsageNote": "AI used only supplied sources.",
            }
        )

    monkeypatch.setattr(memo_service, "_request_chat_completion", fake_request)

    result = generate_memo(test_engine, assessment, "investment-committee", settings)

    assert result.data.generation.provider == "openai-compatible"
    assert result.data.generation.model == "test-model"
    assert result.data.generation.usedFallback is False
    assert result.data.memo.executiveSummary == "AI generated summary."
