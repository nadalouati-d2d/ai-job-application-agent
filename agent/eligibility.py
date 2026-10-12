from enum import Enum

from pydantic import BaseModel, Field


class EligibilityStatus(str, Enum):
    SUITABLE = "Suitable"
    NEEDS_REVIEW = "Needs Review"
    EXCLUDED = "Excluded"


class JobRequirements(BaseModel):
    """
    Structured requirements extracted from a job posting.

    None means the posting did not provide enough information
    to determine the value reliably.
    """

    title: str

    mandatory_cybersecurity_years: float | None = None
    preferred_cybersecurity_years: float | None = None

    citizenship_required: bool | None = None
    student_only: bool | None = None
    senior_role: bool | None = None

    location: str | None = None
    remote_eligible_canada: bool | None = None
    commute_minutes: int | None = None

    expired: bool | None = None

    accepts_internships: bool | None = None
    accepts_projects: bool | None = None
    accepts_coursework: bool | None = None
    accepts_recent_graduates: bool | None = None
    education_substitution: bool | None = None


class EligibilityResult(BaseModel):
    status: EligibilityStatus
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def evaluate_eligibility(
    job: JobRequirements,
    max_professional_cybersecurity_years: float = 1,
) -> EligibilityResult:
    """
    Evaluate whether a job should proceed to deeper AI analysis.

    Hard exclusions take priority over review conditions.
    """

    exclusion_reasons: list[str] = []
    review_reasons: list[str] = []

    # Hard exclusion: expired posting
    if job.expired is True:
        exclusion_reasons.append("Job posting is expired.")

    # Hard exclusion: citizenship requirement
    if job.citizenship_required is True:
        exclusion_reasons.append(
            "Job requires citizenship."
        )

    # Hard exclusion: senior role
    if job.senior_role is True:
        exclusion_reasons.append(
            "Job is classified as a senior role."
        )

    # Hard exclusion: mandatory professional cybersecurity experience
    if (
        job.mandatory_cybersecurity_years is not None
        and job.mandatory_cybersecurity_years
        > max_professional_cybersecurity_years
    ):
        exclusion_reasons.append(
            "Mandatory professional cybersecurity experience "
            f"({job.mandatory_cybersecurity_years:g} years) "
            f"exceeds the allowed maximum "
            f"({max_professional_cybersecurity_years:g} year)."
        )

    # Needs review: student-only role
    if job.student_only is True:
        review_reasons.append(
            "Role is restricted to students; eligibility must be verified."
        )

    # Needs review: unknown experience requirement
    if job.mandatory_cybersecurity_years is None:
        review_reasons.append(
            "Mandatory professional cybersecurity experience "
            "requirement is unknown."
        )

    # Needs review: workplace cannot yet be evaluated
    if (
        job.location is None
        and job.remote_eligible_canada is not True
    ):
        review_reasons.append(
            "Worksite or remote eligibility is unknown."
        )

    # Hard exclusions always win.
    if exclusion_reasons:
        return EligibilityResult(
            status=EligibilityStatus.EXCLUDED,
            reasons=exclusion_reasons,
            warnings=review_reasons,
        )

    # Ambiguous jobs require human review.
    if review_reasons:
        return EligibilityResult(
            status=EligibilityStatus.NEEDS_REVIEW,
            reasons=review_reasons,
        )

    return EligibilityResult(
        status=EligibilityStatus.SUITABLE,
        reasons=[
            "No mandatory exclusion condition was detected."
        ],
    )


if __name__ == "__main__":
    example_job = JobRequirements(
        title="Junior Cybersecurity Analyst",
        mandatory_cybersecurity_years=1,
        citizenship_required=False,
        student_only=False,
        senior_role=False,
        location="Ottawa, ON",
        remote_eligible_canada=False,
        commute_minutes=20,
        expired=False,
    )

    result = evaluate_eligibility(example_job)

    print("Job:", example_job.title)
    print("Status:", result.status.value)
    print("Reasons:", result.reasons)
    print("Warnings:", result.warnings)