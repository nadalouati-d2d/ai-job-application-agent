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
        # ---------------------------------------------------------
    # Cybersecurity experience requirements
    # ---------------------------------------------------------

    # Preferred experience:
    # "2 years of cybersecurity experience preferred"
    preferred_pattern = re.compile(
        r"\b(?P<years>\d+(?:\.\d+)?)\+?"
        r"\s+years?\s+of\s+"
        r"(?:professional\s+)?cybersecurity\s+experience"
        r"\s+(?:is\s+)?preferred\b",
        flags=re.IGNORECASE,
    )

    preferred_match = preferred_pattern.search(text)

    if preferred_match:
        years = float(preferred_match.group("years"))

        requirements.preferred_cybersecurity_years = years

        evidence.append(
            ExtractedEvidence(
                field="preferred_cybersecurity_years",
                value=f"{years:g}",
                quote=preferred_match.group(0),
            )
        )

    # Explicit required experience:
    #
    # "2 years of cybersecurity experience required"
    # "1 year of cybersecurity experience is required"
    required_suffix_pattern = re.compile(
        r"\b(?P<years>\d+(?:\.\d+)?)\+?"
        r"\s+years?\s+of\s+"
        r"(?:professional\s+)?cybersecurity\s+experience"
        r"\s+(?:is\s+)?(?:required|mandatory)\b",
        flags=re.IGNORECASE,
    )

    required_match = required_suffix_pattern.search(text)

    if required_match:
        years = float(required_match.group("years"))

        requirements.mandatory_cybersecurity_years = years

        evidence.append(
            ExtractedEvidence(
                field="mandatory_cybersecurity_years",
                value=f"{years:g}",
                quote=required_match.group(0),
            )
        )

    # "must have at least 2 years of cybersecurity experience"
    required_at_least_pattern = re.compile(
        r"\b(?:candidates?\s+)?must\s+have\s+"
        r"(?:at\s+least\s+)?"
        r"(?P<years>\d+(?:\.\d+)?)\+?"
        r"\s+years?\s+of\s+"
        r"(?:professional\s+)?cybersecurity\s+experience\b",
        flags=re.IGNORECASE,
    )

    required_at_least_match = required_at_least_pattern.search(text)

    if required_at_least_match:
        years = float(required_at_least_match.group("years"))

        requirements.mandatory_cybersecurity_years = years

        evidence.append(
            ExtractedEvidence(
                field="mandatory_cybersecurity_years",
                value=f"{years:g}",
                quote=required_at_least_match.group(0),
            )
        )

    # Required range:
    # "must have 1-2 years of cybersecurity experience"
    #
    # We use the lower bound because the posting explicitly accepts
    # candidates beginning at that experience level.
    required_range_pattern = re.compile(
        r"\b(?:candidates?\s+)?must\s+have\s+"
        r"(?P<minimum>\d+(?:\.\d+)?)\s*[-–]\s*"
        r"(?P<maximum>\d+(?:\.\d+)?)"
        r"\s+years?\s+of\s+"
        r"(?:professional\s+)?cybersecurity\s+experience\b",
        flags=re.IGNORECASE,
    )

    required_range_match = required_range_pattern.search(text)

    if required_range_match:
        minimum = float(required_range_match.group("minimum"))

        requirements.mandatory_cybersecurity_years = minimum

        evidence.append(
            ExtractedEvidence(
                field="mandatory_cybersecurity_years",
                value=f"{minimum:g}",
                quote=required_range_match.group(0),
            )
        )
        # ---------------------------------------------------------
    # Explicit experience alternatives
    # ---------------------------------------------------------

    alternative_detected = False

    # Education explicitly substitutes for experience.
    education_alternative_patterns = [
        r"\bor equivalent education(?: and training)?\b",
        r"\beducation may be considered in lieu of "
        r"(?:professional )?experience\b",
        r"\beducation may substitute for "
        r"(?:professional )?experience\b",
    ]

    for pattern in education_alternative_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            requirements.education_substitution = True
            alternative_detected = True

            evidence.append(
                ExtractedEvidence(
                    field="education_substitution",
                    value="true",
                    quote=match.group(0),
                )
            )
            break

    # Internships explicitly accepted as experience.
    internship_patterns = [
        r"\binternships?\s*,?\s*or equivalent "
        r"hands-on experience will be considered\b",
        r"\binternships? may be considered in lieu of "
        r"(?:professional )?experience\b",
        r"\binternships? may substitute for "
        r"(?:professional )?experience\b",
    ]

    for pattern in internship_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            requirements.accepts_internships = True
            alternative_detected = True

            evidence.append(
                ExtractedEvidence(
                    field="accepts_internships",
                    value="true",
                    quote=match.group(0),
                )
            )
            break

    # Relevant coursework explicitly substitutes for experience.
    coursework_patterns = [
        r"\brelevant coursework may be considered in lieu of "
        r"(?:professional )?experience\b",
        r"\brelevant coursework may substitute for "
        r"(?:professional )?experience\b",
    ]

    for pattern in coursework_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            requirements.accepts_coursework = True
            alternative_detected = True

            evidence.append(
                ExtractedEvidence(
                    field="accepts_coursework",
                    value="true",
                    quote=match.group(0),
                )
            )
            break

    # Projects explicitly substitute for experience.
    project_patterns = [
        r"\brelevant cybersecurity projects may substitute "
        r"for (?:professional )?experience\b",
        r"\brelevant cybersecurity projects may be considered "
        r"in lieu of (?:professional )?experience\b",
    ]

    for pattern in project_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            requirements.accepts_projects = True
            alternative_detected = True

            evidence.append(
                ExtractedEvidence(
                    field="accepts_projects",
                    value="true",
                    quote=match.group(0),
                )
            )
            break

    if alternative_detected:
        requirements.experience_alternatives_explicit = True

    # Recent-graduate language is useful independently of whether
    # the posting contains a numeric experience requirement.
    recent_graduate_patterns = [
        r"\brecent graduates? (?:are )?encouraged to apply\b",
        r"\brecent graduates? (?:are )?welcome to apply\b",
    ]

    for pattern in recent_graduate_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            requirements.accepts_recent_graduates = True

            evidence.append(
                ExtractedEvidence(
                    field="accepts_recent_graduates",
                    value="true",
                    quote=match.group(0),
                )
            )
            break

         # ---------------------------------------------------------
    # Current security-clearance requirements
    # ---------------------------------------------------------
    #
    # Only extract a clearance when the posting explicitly says
    # the candidate must already hold it.
    #
    # Do NOT treat "eligible to obtain" or "able to obtain" as
    # a current-clearance requirement.

    current_clearance_patterns = [
        (
            "Secret",
            r"\b(?:candidates?\s+)?must\s+currently\s+hold\s+"
            r"(?:a\s+)?(?:valid\s+)?secret\s+"
            r"(?:security\s+)?clearance\b",
        ),
        (
            "Secret",
            r"\b(?:applicants?\s+)?must\s+hold\s+"
            r"(?:a\s+)?(?:valid\s+)?secret\s+"
            r"(?:security\s+)?clearance\b",
        ),
        (
            "Reliability",
            r"\b(?:candidates?\s+|applicants?\s+)?must\s+"
            r"(?:currently\s+)?hold\s+"
            r"(?:a\s+)?(?:valid\s+)?reliability\s+status\b",
        ),
    ]

    for clearance_level, pattern in current_clearance_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            requirements.required_clearance = clearance_level

            evidence.append(
                ExtractedEvidence(
                    field="required_clearance",
                    value=clearance_level,
                    quote=match.group(0),
                )
            )
            break

        # ---------------------------------------------------------
    # Student-only eligibility requirements
    # ---------------------------------------------------------
    #
    # Only mark a posting as student-only when the description
    # explicitly requires current enrollment or returning to
    # school. An internship title alone is not sufficient.

    student_only_patterns = [
        r"\bapplicants? must be currently enrolled in "
        r"(?:a\s+)?college or university program\b",

        r"\bcandidates? must be currently enrolled in "
        r"(?:a\s+)?college or university program\b",

        r"\bmust be currently enrolled in "
        r"(?:a\s+)?college or university program\b",

        r"\bcandidates? must be returning to school "
        r"after completion of the internship\b",

        r"\bapplicants? must be returning to school "
        r"after completion of the internship\b",

        r"\bmust be returning to school "
        r"after completion of the internship\b",

                r"\bcandidates? must be currently enrolled in "
        r"(?:a\s+)?post-secondary program\b",

        r"\bapplicants? must be currently enrolled in "
        r"(?:a\s+)?post-secondary program\b",

        r"\bmust be currently enrolled in "
        r"(?:a\s+)?post-secondary program\b",

        r"\bapplicants? must return to studies following "
        r"the work term\b",

        r"\bcandidates? must return to studies following "
        r"the work term\b",

        r"\bmust return to studies following "
        r"the work term\b",
    ]

    for pattern in student_only_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            requirements.student_only = True

            evidence.append(
                ExtractedEvidence(
                    field="student_only",
                    value="true",
                    quote=match.group(0),
                )
            )
            break

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

