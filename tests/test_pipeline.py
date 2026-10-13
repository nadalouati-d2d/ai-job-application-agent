from agent.eligibility import EligibilityStatus
from agent.pipeline import JobPipelineResult, analyze_job


def test_pipeline_returns_analysis_and_eligibility():
    result = analyze_job(
        title="Junior Cybersecurity Analyst",
        description=(
            "This is a hybrid role. "
            "Location: Ottawa, ON. "
            "1 year of cybersecurity experience is required."
        ),
    )

    assert isinstance(result, JobPipelineResult)

    assert result.analysis.requirements.title == (
        "Junior Cybersecurity Analyst"
    )
    assert result.analysis.requirements.mandatory_cybersecurity_years == 1
    assert result.analysis.requirements.work_arrangement == "hybrid"
    assert result.analysis.requirements.location == "Ottawa, ON"
    assert result.analysis.requirements.location_country == "Canada"

    assert result.eligibility.status == EligibilityStatus.SUITABLE


def test_pipeline_preserves_analyzer_evidence():
    result = analyze_job(
        title="Junior Cybersecurity Analyst",
        description=(
            "This is a hybrid role. "
            "Location: Toronto, ON. "
            "1 year of cybersecurity experience is required."
        ),
    )

    fields = {item.field for item in result.analysis.evidence}

    assert "mandatory_cybersecurity_years" in fields
    assert "work_arrangement" in fields
    assert "location" in fields


def test_pipeline_returns_excluded_for_senior_role():
    result = analyze_job(
        title="Senior Cybersecurity Analyst",
        description=(
            "This is a hybrid role. "
            "Location: Calgary, AB. "
            "1 year of cybersecurity experience is required."
        ),
    )

    assert result.eligibility.status == EligibilityStatus.EXCLUDED
    assert "Job is classified as a senior role." in (
        result.eligibility.reasons
    )


def test_pipeline_returns_needs_review_for_unknown_experience():
    result = analyze_job(
        title="Cybersecurity Analyst",
        description=(
            "This is a hybrid role. "
            "Location: Vancouver, BC."
        ),
    )

    assert result.eligibility.status == EligibilityStatus.NEEDS_REVIEW
    assert (
        "Mandatory professional cybersecurity experience "
        "requirement is unknown."
        in result.eligibility.reasons
    )


def test_pipeline_passes_candidate_clearance_to_eligibility():
    result = analyze_job(
        title="Junior Cybersecurity Analyst",
        description=(
            "This is a hybrid role. "
            "Location: Ottawa, ON. "
            "1 year of cybersecurity experience is required. "
            "Candidates must currently hold Secret clearance."
        ),
        candidate_clearance="Reliability",
    )

    assert result.eligibility.status == EligibilityStatus.NEEDS_REVIEW
    assert any(
        "Secret clearance" in reason
        for reason in result.eligibility.reasons
    )