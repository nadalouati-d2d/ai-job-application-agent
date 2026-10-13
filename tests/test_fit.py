from agent.eligibility import JobRequirements
from agent.fit import (
    EvidenceSourceType,
    SkillMatchStatus,
    analyze_fit,
)
from agent.candidate_profile import (
    ProfessionalExperience,
    load_candidate_profile,
)


def load_example_profile():
    return load_candidate_profile(
        "profile/candidate.example.json"
    )


def test_matches_skill_to_verified_project_evidence():
    profile = load_example_profile()

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=["Example SIEM"],
    )

    result = analyze_fit(job, profile)

    match = result.required_skill_matches[0]

    assert match.skill == "Example SIEM"
    assert match.status == SkillMatchStatus.SUPPORTED
    assert len(match.evidence) == 1

    evidence = match.evidence[0]

    assert evidence.source_type == EvidenceSourceType.PROJECT
    assert evidence.source_id == "example-soc-project"
    assert evidence.evidence_level == "hands_on_project"
    assert evidence.professional_cybersecurity_experience is False


def test_missing_skill_remains_missing():
    profile = load_example_profile()

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=["CrowdStrike"],
    )

    result = analyze_fit(job, profile)

    match = result.required_skill_matches[0]

    assert match.skill == "CrowdStrike"
    assert match.status == SkillMatchStatus.MISSING
    assert match.evidence == []


def test_project_evidence_is_never_professional_experience():
    profile = load_example_profile()

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=["Example SIEM"],
    )

    result = analyze_fit(job, profile)

    evidence = result.required_skill_matches[0].evidence[0]

    assert evidence.evidence_level == "hands_on_project"
    assert evidence.professional_cybersecurity_experience is False


def test_preserves_required_and_preferred_skill_groups():
    profile = load_example_profile()

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=["Example SIEM"],
        preferred_skills=["CrowdStrike"],
    )

    result = analyze_fit(job, profile)

    assert len(result.required_skill_matches) == 1
    assert len(result.preferred_skill_matches) == 1

    assert (
        result.required_skill_matches[0].skill
        == "Example SIEM"
    )
    assert (
        result.preferred_skill_matches[0].skill
        == "CrowdStrike"
    )

def test_matches_skill_to_verified_professional_evidence():
    profile = load_example_profile()

    profile.professional_experience.append(
        ProfessionalExperience(
            id="professional-terraform",
            title="DevSecOps Intern",
            employer="Example Company",
            location="Example City, ON",
            start="2026-01",
            end=None,
            current=True,
            employment_type="internship",
            evidence_level="professional",
            categories=["devsecops"],
            verified=True,
            facts=[
                "Reviewed Terraform infrastructure "
                "configurations for security issues."
            ],
        )
    )

    job = JobRequirements(
        title="Junior DevSecOps Analyst",
        required_skills=["Terraform"],
    )

    result = analyze_fit(job, profile)

    match = result.required_skill_matches[0]

    assert match.status == SkillMatchStatus.SUPPORTED
    assert len(match.evidence) == 1

    evidence = match.evidence[0]

    assert (
        evidence.source_type
        == EvidenceSourceType.PROFESSIONAL_EXPERIENCE
    )
    assert evidence.source_id == "professional-terraform"
    assert evidence.evidence_level == "professional"
    assert evidence.professional_cybersecurity_experience is True
    assert "Terraform" in evidence.fact

def test_does_not_use_unverified_project_evidence():
    profile = load_example_profile()

    profile.projects[0].verified = False

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=["Example SIEM"],
    )

    result = analyze_fit(job, profile)

    match = result.required_skill_matches[0]

    assert match.status == SkillMatchStatus.MISSING
    assert match.evidence == []

def test_fit_score_is_100_when_all_skills_are_supported():
    profile = load_example_profile()

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=["Example SIEM"],
    )

    result = analyze_fit(job, profile)

    assert result.fit_score == 100.0
    assert result.missing_required_skills == []
    assert result.missing_preferred_skills == []


def test_missing_required_skill_reduces_score_more_than_preferred():
    profile = load_example_profile()

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=[
            "Example SIEM",
            "CrowdStrike",
        ],
        preferred_skills=["Unknown Tool"],
    )

    result = analyze_fit(job, profile)

    # Required skills have weight 2 each.
    # Preferred skills have weight 1 each.
    #
    # Supported weight = 2
    # Total weight = 2 + 2 + 1 = 5
    # Score = 2 / 5 * 100 = 40
    assert result.fit_score == 40.0

    assert result.missing_required_skills == [
        "CrowdStrike"
    ]
    assert result.missing_preferred_skills == [
        "Unknown Tool"
    ]


def test_project_supported_skill_receives_skill_match_credit():
    profile = load_example_profile()

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=["Example SIEM"],
        preferred_skills=["CrowdStrike"],
    )

    result = analyze_fit(job, profile)

    # Project evidence supports the skill requirement,
    # but remains non-professional evidence.
    assert result.fit_score == 66.67

    evidence = result.required_skill_matches[0].evidence[0]

    assert evidence.evidence_level == "hands_on_project"
    assert evidence.professional_cybersecurity_experience is False


def test_fit_score_is_unknown_when_job_has_no_extracted_skills():
    profile = load_example_profile()

    job = JobRequirements(
        title="SOC Analyst",
    )

    result = analyze_fit(job, profile)

    assert result.fit_score is None
    assert result.missing_required_skills == []
    assert result.missing_preferred_skills == []

def test_multiple_evidence_sources_do_not_double_count_skill():
    profile = load_example_profile()

    profile.professional_experience.append(
        ProfessionalExperience(
            id="professional-example-siem",
            title="Cybersecurity Intern",
            employer="Example Company",
            location="Example City, ON",
            start="2026-01",
            end=None,
            current=True,
            employment_type="internship",
            evidence_level="professional",
            categories=["security_operations"],
            verified=True,
            facts=[
                "Reviewed Example SIEM security configurations."
            ],
        )
    )

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=["Example SIEM"],
    )

    result = analyze_fit(job, profile)

    match = result.required_skill_matches[0]

    assert match.status == SkillMatchStatus.SUPPORTED
    assert len(match.evidence) == 2
    assert result.fit_score == 100.0

def test_resume_emphasis_prioritizes_supported_required_skill():
    profile = load_example_profile()

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=["Example SIEM"],
    )

    result = analyze_fit(job, profile)

    assert len(result.resume_emphasis) == 1

    emphasis = result.resume_emphasis[0]

    assert emphasis.skill == "Example SIEM"
    assert emphasis.requirement_type == "required"
    assert emphasis.source_id == "example-soc-project"
    assert emphasis.evidence_level == "hands_on_project"
    assert emphasis.professional_cybersecurity_experience is False


def test_missing_skill_is_not_added_to_resume_emphasis():
    profile = load_example_profile()

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=["CrowdStrike"],
    )

    result = analyze_fit(job, profile)

    assert result.resume_emphasis == []


def test_required_emphasis_comes_before_preferred_emphasis():
    profile = load_example_profile()

    job = JobRequirements(
        title="SOC Analyst",
        required_skills=["Example SIEM"],
        preferred_skills=["Example SIEM"],
    )

    result = analyze_fit(job, profile)

    assert len(result.resume_emphasis) == 2

    assert result.resume_emphasis[0].requirement_type == "required"
    assert result.resume_emphasis[1].requirement_type == "preferred"