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


class FitResult(BaseModel):
    required_skill_matches: list[SkillMatch] = Field(
        default_factory=list
    )
    preferred_skill_matches: list[SkillMatch] = Field(
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

    return FitResult(
        required_skill_matches=required_matches,
        preferred_skill_matches=preferred_matches,
    )