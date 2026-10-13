from pydantic import BaseModel

from agent.analyzer import JobAnalysis, analyze_job_description
from agent.eligibility import EligibilityResult, evaluate_eligibility


class JobPipelineResult(BaseModel):
    """Combined result of job analysis and eligibility evaluation."""

    analysis: JobAnalysis
    eligibility: EligibilityResult


def analyze_job(
    title: str,
    description: str,
    *,
    max_professional_cybersecurity_years: float = 1,
    candidate_clearance: str | None = "Reliability",
) -> JobPipelineResult:
    """
    Analyze a raw job posting and evaluate candidate eligibility.

    This function only orchestrates the existing deterministic analyzer
    and eligibility engine. It does not duplicate extraction or
    eligibility logic.
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

    return JobPipelineResult(
        analysis=analysis,
        eligibility=eligibility,
    )