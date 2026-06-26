from app.models.domain import SiteAssessment


def source_labels(assessment: SiteAssessment) -> list[str]:
    return [source.label for source in assessment.sources]
