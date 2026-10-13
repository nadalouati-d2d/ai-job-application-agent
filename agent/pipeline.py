from pydantic import BaseModel

from agent.analyzer import JobAnalysis, analyze_job_description
from agent.candidate_profile import CandidateProfile
from agent.eligibility import EligibilityResult, evaluate_eligibility
from agent.fit import FitResult, analyze_fit


class JobPipelineResult(BaseModel):
    """Combined result of job analysis, eligibility, and candidate fit."""

    analysis: JobAnalysis
    eligibility: EligibilityResult
    fit: FitResult | None = None


def analyze_job(
    title: str,
    description: str,
    *,
    max_professional_cybersecurity_years: float = 1,
    candidate_clearance: str | None = "Reliability",
    candidate_profile: CandidateProfile | None = None,
) -> JobPipelineResult:
    """
    Analyze a raw job posting, evaluate eligibility, and optionally
    evaluate candidate fit.

    Fit analysis is performed only when a validated candidate profile
    is explicitly provided.
    """

    analysis = analyze_job_description(
        title=title,
        description=description,
    )

    eligibility = evaluate_eligibility(
        analysis.requirements,
        max_professional_cybersecurity_years=(
            max_professional_cybersecurity_years
        ),
        candidate_clearance=candidate_clearance,
    )

    fit = (
        analyze_fit(
            analysis.requirements,
            candidate_profile,
        )
        if candidate_profile is not None
        else None
    )

    return JobPipelineResult(
        analysis=analysis,
        eligibility=eligibility,
        fit=fit,
    )