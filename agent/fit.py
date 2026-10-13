from enum import Enum

from pydantic import BaseModel, Field

from agent.candidate_profile import CandidateProfile
from agent.eligibility import JobRequirements


class EvidenceSourceType(str, Enum):
    PROFESSIONAL_EXPERIENCE = "professional_experience"
    ACADEMIC_EXPERIENCE = "academic_experience"
    PROJECT = "project"
    EDUCATION = "education"
    CERTIFICATION = "certification"
    SKILL = "skill"


class SkillMatchStatus(str, Enum):
    SUPPORTED = "supported"
    MISSING = "missing"


class CandidateEvidence(BaseModel):
    source_type: EvidenceSourceType
    source_id: str
    source_name: str
    evidence_level: str
    fact: str
    professional_cybersecurity_experience: bool


class SkillMatch(BaseModel):
    skill: str
    status: SkillMatchStatus
    evidence: list[CandidateEvidence] = Field(default_factory=list)

class ResumeEmphasis(BaseModel):
    skill: str
    requirement_type: str
    source_type: EvidenceSourceType
    source_id: str
    source_name: str
    evidence_level: str
    fact: str
    professional_cybersecurity_experience: bool

class FitResult(BaseModel):
    required_skill_matches: list[SkillMatch] = Field(
        default_factory=list
    )
    preferred_skill_matches: list[SkillMatch] = Field(
        default_factory=list
    )
    fit_score: float | None = None
    missing_required_skills: list[str] = Field(
        default_factory=list
    )
    missing_preferred_skills: list[str] = Field(
        default_factory=list
    )
    resume_emphasis: list[ResumeEmphasis] = Field(
        default_factory=list
    )


def _normalize(value: str) -> str:
    return " ".join(value.lower().split())


def _match_skill(
    skill: str,
    profile: CandidateProfile,
) -> SkillMatch:
    normalized_skill = _normalize(skill)
    evidence: list[CandidateEvidence] = []

    # Verified professional cybersecurity experience.
    for experience in profile.professional_experience:
        if not experience.verified:
            continue

        searchable_values = [
            *experience.categories,
            *experience.facts,
        ]

        if any(
            normalized_skill in _normalize(value)
            for value in searchable_values
        ):
            evidence.append(
                CandidateEvidence(
                    source_type=(
                        EvidenceSourceType.PROFESSIONAL_EXPERIENCE
                    ),
                    source_id=experience.id,
                    source_name=experience.title,
                    evidence_level=experience.evidence_level,
                    fact=next(
                        value
                        for value in searchable_values
                        if normalized_skill in _normalize(value)
                    ),
                    professional_cybersecurity_experience=True,
                )
            )

    # Verified projects and coursework.
    for project in profile.projects:
        if not project.verified:
            continue

        searchable_values = [
            *project.technologies,
            *project.categories,
            *project.facts,
        ]

        if any(
            normalized_skill in _normalize(value)
            for value in searchable_values
        ):
            evidence.append(
                CandidateEvidence(
                    source_type=EvidenceSourceType.PROJECT,
                    source_id=project.id,
                    source_name=project.name,
                    evidence_level=project.evidence_level,
                    fact=next(
                        value
                        for value in searchable_values
                        if normalized_skill in _normalize(value)
                    ),
                    professional_cybersecurity_experience=False,
                )
            )

    status = (
        SkillMatchStatus.SUPPORTED
        if evidence
        else SkillMatchStatus.MISSING
    )

    return SkillMatch(
        skill=skill,
        status=status,
        evidence=evidence,
    )
def _build_resume_emphasis(
    matches: list[SkillMatch],
    requirement_type: str,
) -> list[ResumeEmphasis]:
    emphasis: list[ResumeEmphasis] = []

    for match in matches:
        if match.status != SkillMatchStatus.SUPPORTED:
            continue

        for evidence in match.evidence:
            emphasis.append(
                ResumeEmphasis(
                    skill=match.skill,
                    requirement_type=requirement_type,
                    source_type=evidence.source_type,
                    source_id=evidence.source_id,
                    source_name=evidence.source_name,
                    evidence_level=evidence.evidence_level,
                    fact=evidence.fact,
                    professional_cybersecurity_experience=(
                        evidence.professional_cybersecurity_experience
                    ),
                )
            )

    return emphasis

def analyze_fit(
    job: JobRequirements,
    profile: CandidateProfile,
) -> FitResult:
    required_matches = [
        _match_skill(skill, profile)
        for skill in job.required_skills
    ]

    preferred_matches = [
        _match_skill(skill, profile)
        for skill in job.preferred_skills
    ]

    missing_required_skills = [
        match.skill
        for match in required_matches
        if match.status == SkillMatchStatus.MISSING
    ]

    missing_preferred_skills = [
        match.skill
        for match in preferred_matches
        if match.status == SkillMatchStatus.MISSING
    ]

    required_weight = 2
    preferred_weight = 1

    total_weight = (
        len(required_matches) * required_weight
        + len(preferred_matches) * preferred_weight
    )

    if total_weight == 0:
        fit_score = None
    else:
        supported_weight = (
            sum(
                required_weight
                for match in required_matches
                if match.status == SkillMatchStatus.SUPPORTED
            )
            + sum(
                preferred_weight
                for match in preferred_matches
                if match.status == SkillMatchStatus.SUPPORTED
            )
        )

        fit_score = round(
            supported_weight / total_weight * 100,
            2,
        )

    resume_emphasis = (
        _build_resume_emphasis(
            required_matches,
            "required",
        )
        + _build_resume_emphasis(
            preferred_matches,
            "preferred",
        )
    )

    return FitResult(
        required_skill_matches=required_matches,
        preferred_skill_matches=preferred_matches,
        fit_score=fit_score,
        missing_required_skills=missing_required_skills,
        missing_preferred_skills=missing_preferred_skills,
        resume_emphasis=resume_emphasis,
    )