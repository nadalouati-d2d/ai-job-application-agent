import re

from pydantic import BaseModel, Field

from agent.eligibility import JobRequirements


class ExtractedEvidence(BaseModel):
    field: str
    value: str
    quote: str


class JobAnalysis(BaseModel):
    requirements: JobRequirements
    evidence: list[ExtractedEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _normalize_text(text: str) -> str:
    """Normalize whitespace while preserving the posting's wording."""
    return re.sub(r"\s+", " ", text).strip()


def analyze_job_description(
    title: str,
    description: str,
) -> JobAnalysis:
    """
    Convert raw job-posting text into structured requirements.

    This first version deliberately extracts only high-confidence facts.
    Unknown or ambiguous information remains unknown rather than being
    guessed.
    """

    text = _normalize_text(description)

    requirements = JobRequirements(title=title)
    evidence: list[ExtractedEvidence] = []
    warnings: list[str] = []

    # Citizenship requirement
    citizenship_patterns = [
    r"\bmust be (?:a )?canadian citizens?\b",
    r"\bmust be canadian citizens?\b",
    r"\bcanadian citizenship (?:is )?required\b",
    r"\bmust hold canadian citizenship\b",
    r"\bapplicants must be canadian citizens?\b",
]

    for pattern in citizenship_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            requirements.citizenship_required = True

            evidence.append(
                ExtractedEvidence(
                    field="citizenship_required",
                    value="true",
                    quote=match.group(0),
                )
            )
            break

    # Explicit remote eligibility
    remote_canada_patterns = [
        r"\bremote (?:within|in|across) canada\b",
        r"\bremote[- ]canada\b",
        r"\bwork remotely (?:within|from) canada\b",
    ]

    for pattern in remote_canada_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            requirements.work_arrangement = "remote"
            requirements.remote_eligible_canada = True

            evidence.append(
                ExtractedEvidence(
                    field="remote_eligible_canada",
                    value="true",
                    quote=match.group(0),
                )
            )
            break

    # Explicit seniority signals
    senior_title_pattern = (
        r"\b(?:senior|sr\.?|lead|principal|manager|director)\b"
    )

    if re.search(senior_title_pattern, title, flags=re.IGNORECASE):
        requirements.senior_role = True

        evidence.append(
            ExtractedEvidence(
                field="senior_role",
                value="true",
                quote=title,
            )
        )

    # Preserve unknown information instead of guessing.
    if requirements.citizenship_required is None:
        warnings.append(
            "Citizenship requirement was not explicitly identified."
        )

    if requirements.work_arrangement is None:
        warnings.append(
            "Work arrangement was not explicitly identified."
        )

    return JobAnalysis(
        requirements=requirements,
        evidence=evidence,
        warnings=warnings,
    )


if __name__ == "__main__":
    sample_description = """
    We are hiring a Junior Cybersecurity Analyst.
    This position is remote within Canada.
    Applicants must be Canadian citizens.
    """

    analysis = analyze_job_description(
        title="Junior Cybersecurity Analyst",
        description=sample_description,
    )

    print(analysis.model_dump_json(indent=2))