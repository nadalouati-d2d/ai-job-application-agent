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
    required_clearance: str | None = None
    student_only: bool | None = None
    senior_role: bool | None = None

    location: str | None = None
    location_country: str | None = None

    work_arrangement: str | None = None
    worksite_verified: bool | None = None
    commute_minutes: int | None = None

    remote_eligible_canada: bool | None = None  

    expired: bool | None = None

    accepts_internships: bool | None = None
    accepts_projects: bool | None = None
    accepts_coursework: bool | None = None
    accepts_recent_graduates: bool | None = None
    education_substitution: bool | None = None
    experience_alternatives_explicit: bool | None = None


class EligibilityResult(BaseModel):
    status: EligibilityStatus
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def evaluate_eligibility(
    job: JobRequirements,
    max_professional_cybersecurity_years: float = 1,
    candidate_clearance: str | None = "Reliability",
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
    
        # Clearance requirement
    clearance_levels = {
        "reliability": 1,
        "secret": 2,
        "top secret": 3,
    }

    if job.required_clearance is not None:
        required = clearance_levels.get(
            job.required_clearance.strip().lower()
        )

        candidate = (
            clearance_levels.get(candidate_clearance.strip().lower())
            if candidate_clearance
            else None
        )

        if required is None:
            review_reasons.append(
                f"Unknown clearance requirement: "
                f"{job.required_clearance}."
            )
        elif candidate is None:
            review_reasons.append(
                "Job requires security clearance, but the candidate "
                "clearance could not be verified."
            )
        elif candidate < required:
            review_reasons.append(
                f"Job requires {job.required_clearance} clearance, "
                f"but candidate has {candidate_clearance}."
            )

    # Hard exclusion: senior role
    if job.senior_role is True:
        exclusion_reasons.append(
            "Job is classified as a senior role."
        )

    # Hard exclusion: mandatory professional cybersecurity experience
        # Hard exclusion: mandatory professional cybersecurity experience
    if (
        job.mandatory_cybersecurity_years is not None
        and job.mandatory_cybersecurity_years
        > max_professional_cybersecurity_years
    ):
        has_explicit_alternative = (
            job.experience_alternatives_explicit is True
            and (
                job.education_substitution is True
                or job.accepts_internships is True
                or job.accepts_projects is True
                or job.accepts_coursework is True
                or job.accepts_recent_graduates is True
            )
        )

        if has_explicit_alternative:
            review_reasons.append(
                "Experience requirement exceeds the normal junior limit, "
                "but the posting explicitly allows an alternative such as "
                "education, internship, projects, coursework, or "
                "recent-graduate experience."
            )
        else:
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

        # Location and work-arrangement eligibility
    arrangement = (
        job.work_arrangement.lower()
        if job.work_arrangement
        else None
    )

    if arrangement == "remote":
        # Remote work must explicitly permit working from Canada.
        if job.remote_eligible_canada is not True:
            review_reasons.append(
                "Remote eligibility for Canada is unknown."
            )

    elif arrangement in {"onsite", "hybrid"}:
        # Candidate is open to onsite/hybrid work anywhere in Canada.
        # Commute distance and exact worksite verification do not
        # determine eligibility.
        if job.location_country is None:
            review_reasons.append(
                "Country for onsite/hybrid work is unknown."
            )
        elif job.location_country.strip().lower() != "canada":
            review_reasons.append(
                f"Onsite/hybrid work location is outside Canada: "
                f"{job.location_country}."
            )

    else:
        review_reasons.append(
            "Work arrangement is unknown."
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