from agent.eligibility import (
    EligibilityStatus,
    JobRequirements,
    evaluate_eligibility,
)


def base_job(**overrides):
    data = {
        "title": "Junior Cybersecurity Analyst",
        "mandatory_cybersecurity_years": 0,
        "citizenship_required": False,
        "student_only": False,
        "senior_role": False,
        "location": "Ottawa, ON",
        "remote_eligible_canada": False,
        "expired": False,
    }

    data.update(overrides)
    return JobRequirements(**data)


def test_junior_job_is_suitable():
    result = evaluate_eligibility(base_job())

    assert result.status == EligibilityStatus.SUITABLE


def test_one_year_required_is_suitable():
    result = evaluate_eligibility(
        base_job(mandatory_cybersecurity_years=1)
    )

    assert result.status == EligibilityStatus.SUITABLE


def test_two_years_required_is_excluded():
    result = evaluate_eligibility(
        base_job(mandatory_cybersecurity_years=2)
    )

    assert result.status == EligibilityStatus.EXCLUDED


def test_three_years_required_is_excluded():
    result = evaluate_eligibility(
        base_job(mandatory_cybersecurity_years=3)
    )

    assert result.status == EligibilityStatus.EXCLUDED


def test_three_years_preferred_is_not_excluded():
    result = evaluate_eligibility(
        base_job(
            mandatory_cybersecurity_years=0,
            preferred_cybersecurity_years=3,
        )
    )

    assert result.status == EligibilityStatus.SUITABLE


def test_citizenship_requirement_is_excluded():
    result = evaluate_eligibility(
        base_job(citizenship_required=True)
    )

    assert result.status == EligibilityStatus.EXCLUDED


def test_senior_role_is_excluded():
    result = evaluate_eligibility(
        base_job(senior_role=True)
    )

    assert result.status == EligibilityStatus.EXCLUDED


def test_expired_job_is_excluded():
    result = evaluate_eligibility(
        base_job(expired=True)
    )

    assert result.status == EligibilityStatus.EXCLUDED


def test_student_only_requires_review():
    result = evaluate_eligibility(
        base_job(student_only=True)
    )

    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_unknown_experience_requires_review():
    result = evaluate_eligibility(
        base_job(mandatory_cybersecurity_years=None)
    )

    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_unknown_worksite_requires_review():
    result = evaluate_eligibility(
        base_job(
            location=None,
            remote_eligible_canada=None,
        )
    )

    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_canada_remote_job_can_be_suitable_without_location():
    result = evaluate_eligibility(
        base_job(
            location=None,
            remote_eligible_canada=True,
        )
    )

    assert result.status == EligibilityStatus.SUITABLE