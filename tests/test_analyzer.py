from agent.analyzer import analyze_job_description
from agent.eligibility import EligibilityStatus, evaluate_eligibility

def test_experience_alternative_prevents_automatic_exclusion():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "Candidates must have 2 years of cybersecurity experience required, "
            "or equivalent education and training."
        ),
    )

    result = evaluate_eligibility(
        analysis.requirements,
        max_professional_cybersecurity_years=1,
        candidate_clearance="Reliability",
    )

    assert analysis.requirements.mandatory_cybersecurity_years == 2
    assert analysis.requirements.education_substitution is True
    assert analysis.requirements.experience_alternatives_explicit is True

    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_extracts_canadian_citizenship_requirement():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="Applicants must be Canadian citizens.",
    )

    assert analysis.requirements.citizenship_required is True

    assert any(
        item.field == "citizenship_required"
        for item in analysis.evidence
    )


def test_extracts_remote_within_canada():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="This position is remote within Canada.",
    )

    assert analysis.requirements.work_arrangement == "remote"
    assert analysis.requirements.remote_eligible_canada is True


def test_detects_senior_title():
    analysis = analyze_job_description(
        title="Senior Cybersecurity Analyst",
        description="Security operations position.",
    )

    assert analysis.requirements.senior_role is True


def test_junior_title_is_not_marked_senior():
    analysis = analyze_job_description(
        title="Junior Cybersecurity Analyst",
        description="Security operations position.",
    )

    assert analysis.requirements.senior_role is not True


def test_unknown_citizenship_remains_unknown():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="We are looking for a security professional.",
    )

    assert analysis.requirements.citizenship_required is None


def test_unknown_remote_eligibility_remains_unknown():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="The successful candidate will join our security team.",
    )

    assert analysis.requirements.remote_eligible_canada is None
    assert analysis.requirements.work_arrangement is None

def test_extracts_required_experience():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "Candidates must have at least 2 years of "
            "cybersecurity experience."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years == 2
    assert analysis.requirements.preferred_cybersecurity_years is None


def test_extracts_preferred_experience():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "2 years of cybersecurity experience preferred."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years is None
    assert analysis.requirements.preferred_cybersecurity_years == 2


def test_required_and_preferred_are_not_confused():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "1 year of cybersecurity experience required. "
            "3 years of cybersecurity experience preferred."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years == 1
    assert analysis.requirements.preferred_cybersecurity_years == 3


def test_extracts_minimum_from_required_range():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "Candidates must have 1-2 years of cybersecurity experience."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years == 1


def test_unknown_experience_remains_unknown():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "Cybersecurity experience is an asset."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years is None
    assert analysis.requirements.preferred_cybersecurity_years is None

def test_extracts_plus_years_as_preferred():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="2+ years of cybersecurity experience preferred.",
    )

    assert analysis.requirements.mandatory_cybersecurity_years is None
    assert analysis.requirements.preferred_cybersecurity_years == 2


def test_does_not_treat_asset_as_required():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="2 years of cybersecurity experience is an asset.",
    )

    assert analysis.requirements.mandatory_cybersecurity_years is None
    assert analysis.requirements.preferred_cybersecurity_years is None


def test_does_not_extract_unrelated_experience():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="Candidates must have 5 years of customer service experience.",
    )

    assert analysis.requirements.mandatory_cybersecurity_years is None
    assert analysis.requirements.preferred_cybersecurity_years is None


def test_preserves_exact_experience_evidence():
    description = "Candidates must have at least 2 years of cybersecurity experience."

    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=description,
    )

    evidence = [
        item
        for item in analysis.evidence
        if item.field == "mandatory_cybersecurity_years"
    ]

    assert len(evidence) == 1
    assert evidence[0].quote == (
        "Candidates must have at least 2 years of cybersecurity experience"
    )

def test_detects_education_as_experience_alternative():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "2 years of cybersecurity experience required, "
            "or equivalent education and training."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years == 2
    assert analysis.requirements.education_substitution is True
    assert analysis.requirements.experience_alternatives_explicit is True


def test_detects_internship_as_accepted_experience():
    analysis = analyze_job_description(
        title="Junior Security Analyst",
        description=(
            "Professional experience, internships, or equivalent "
            "hands-on experience will be considered."
        ),
    )

    assert analysis.requirements.accepts_internships is True
    assert analysis.requirements.experience_alternatives_explicit is True


def test_detects_coursework_as_accepted_alternative():
    analysis = analyze_job_description(
        title="Junior SOC Analyst",
        description=(
            "Relevant coursework may be considered in lieu of "
            "professional experience."
        ),
    )

    assert analysis.requirements.accepts_coursework is True
    assert analysis.requirements.experience_alternatives_explicit is True


def test_detects_projects_as_accepted_alternative():
    analysis = analyze_job_description(
        title="Junior Cybersecurity Analyst",
        description=(
            "Relevant cybersecurity projects may substitute "
            "for professional experience."
        ),
    )

    assert analysis.requirements.accepts_projects is True
    assert analysis.requirements.experience_alternatives_explicit is True


def test_detects_recent_graduates():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="Recent graduates are encouraged to apply.",
    )

    assert analysis.requirements.accepts_recent_graduates is True


def test_does_not_infer_alternative_from_education_requirement():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "Bachelor's degree in Computer Science required. "
            "2 years of cybersecurity experience required."
        ),
    )

    assert analysis.requirements.education_substitution is not True
    assert analysis.requirements.experience_alternatives_explicit is not True