from app.services.assessment import assess_site


def test_assessment_computes_expected_sections(test_engine):
    result = assess_site(test_engine, "site-bishan-001")
    assessment = result.assessment
    assert result.cache_meta.hit is False
    assert assessment.site.id == "site-bishan-001"
    assert assessment.comparableSummary.selectedCount >= 5
    assert assessment.locationScore.overall > 0
    assert assessment.demographicContext is None
    assert assessment.planningContext is None
    assert assessment.riskAssessment.items
    assert assessment.confidence.level in {"high", "medium", "low"}
    assert {source.reliability for source in assessment.sources} == {"official"}
    assert any(limitation.id == "limitation-demographics" for limitation in assessment.limitations)
    assert any(limitation.id == "limitation-planning" for limitation in assessment.limitations)


def test_assessment_cache_miss_then_hit(test_engine):
    first = assess_site(test_engine, "site-tampines-001")
    second = assess_site(test_engine, "site-tampines-001")
    assert first.cache_meta.hit is False
    assert second.cache_meta.hit is True
    assert first.assessment.assessmentId == second.assessment.assessmentId
