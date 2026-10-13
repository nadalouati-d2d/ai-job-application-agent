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
	"location_country":"Canada",
        "work_arrangement": "hybrid",
        "worksite_verified": True,
        "commute_minutes": 20,
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
            work_arrangement=None,
            worksite_verified=None,
            commute_minutes=None,
            remote_eligible_canada=None,
        )
    )

    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_canada_remote_job_can_be_suitable_without_location():
    result = evaluate_eligibility(
        base_job(
            location=None,
            work_arrangement="remote",
            worksite_verified=None,
            commute_minutes=None,
            remote_eligible_canada=True,
        )
    )

    assert result.status == EligibilityStatus.SUITABLE

def test_verified_onsite_job_within_commute_is_suitable():
    result = evaluate_eligibility(
        base_job(
            work_arrangement="onsite",
            worksite_verified=True,
            commute_minutes=25,
        )
    )

    assert result.status == EligibilityStatus.SUITABLE


def test_canadian_onsite_job_is_not_excluded_by_commute_distance():
    result = evaluate_eligibility(
        base_job(
            location="Toronto, ON",
            location_country="Canada",
            work_arrangement="onsite",
            worksite_verified=True,
            commute_minutes=300,
        )
    )

    assert result.status == EligibilityStatus.SUITABLE


def test_canadian_hybrid_job_does_not_require_commute_calculation():
    result = evaluate_eligibility(
        base_job(
            location="Calgary, AB",
            location_country="Canada",
            work_arrangement="hybrid",
            worksite_verified=False,
            commute_minutes=None,
        )
    )

    assert result.status == EligibilityStatus.SUITABLE


def test_onsite_job_with_unknown_country_requires_review():
    result = evaluate_eligibility(
        base_job(
            location="Unknown City",
            location_country=None,
            work_arrangement="onsite",
            worksite_verified=False,
            commute_minutes=None,
        )
    )

    assert result.status == EligibilityStatus.NEEDS_REVIEW

def test_canadian_hybrid_job_with_unverified_worksite_is_suitable():
    result = evaluate_eligibility(
        base_job(
            location="Vancouver, BC",
            location_country="Canada",
            work_arrangement="hybrid",
            worksite_verified=False,
            commute_minutes=None,
        )
    )

    assert result.status == EligibilityStatus.SUITABLE


def test_remote_job_with_unknown_canada_eligibility_requires_review():
    result = evaluate_eligibility(
        base_job(
            location=None,
            work_arrangement="remote",
            worksite_verified=None,
            commute_minutes=None,
            remote_eligible_canada=None,
        )
    )

    assert result.status == EligibilityStatus.NEEDS_REVIEW

def test_two_years_with_explicit_education_alternative_requires_review():
    result = evaluate_eligibility(
        base_job(
            mandatory_cybersecurity_years=2,
            experience_alternatives_explicit=True,
            education_substitution=True,
        )
    )

    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_two_years_with_explicit_internship_alternative_requires_review():
    result = evaluate_eligibility(
        base_job(
            mandatory_cybersecurity_years=2,
            experience_alternatives_explicit=True,
            accepts_internships=True,
        )
    )

    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_two_years_without_explicit_alternative_is_excluded():
    result = evaluate_eligibility(
        base_job(
            mandatory_cybersecurity_years=2,
            experience_alternatives_explicit=False,
            education_substitution=True,
        )
    )

    assert result.status == EligibilityStatus.EXCLUDED


def test_three_years_preferred_remains_suitable():
    result = evaluate_eligibility(
        base_job(
            mandatory_cybersecurity_years=0,
            preferred_cybersecurity_years=3,
            experience_alternatives_explicit=False,
        )
    )

    assert result.status == EligibilityStatus.SUITABLE

def test_reliability_clearance_is_suitable():
    result = evaluate_eligibility(
        base_job(required_clearance="Reliability"),
        candidate_clearance="Reliability",
    )

    assert result.status == EligibilityStatus.SUITABLE


def test_secret_clearance_requires_review():
    result = evaluate_eligibility(
        base_job(required_clearance="Secret"),
        candidate_clearance="Reliability",
    )

    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_top_secret_clearance_requires_review():
    result = evaluate_eligibility(
        base_job(required_clearance="Top Secret"),
        candidate_clearance="Reliability",
    )

    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_unknown_clearance_requires_review():
    result = evaluate_eligibility(
        base_job(required_clearance="Enhanced Security Clearance"),
        candidate_clearance="Reliability",
    )

    assert result.status == EligibilityStatus.NEEDS_REVIEW
