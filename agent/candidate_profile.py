import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


EvidenceLevel = Literal[
    "professional",
    "professional_non_cybersecurity",
    "hands_on_project",
    "coursework",
    "knowledge_only",
]

ProjectType = Literal[
    "hands_on_project",
    "hands_on_lab",
    "capstone_team_project",
    "course_lab",
    "documentation_project",
]


class ProfessionalExperience(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    employer: str
    location: str
    start: str
    end: str | None = None
    current: bool
    employment_type: str
    evidence_level: Literal["professional"]
    categories: list[str]
    verified: bool
    facts: list[str]


class AcademicExperience(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    employer: str
    location: str
    start: str
    end: str
    evidence_level: Literal["professional_non_cybersecurity"]
    verified: bool
    facts: list[str]


class Project(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    type: ProjectType
    evidence_level: Literal["hands_on_project", "coursework"]
    professional_experience: Literal[False]
    verified: bool
    categories: list[str]
    technologies: list[str]
    facts: list[str]


class Education(BaseModel):
    model_config = ConfigDict(extra="allow")

    credential: str
    field: str
    institution: str
    location: str
    year: int
    gpa: str | None = None


class Certification(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    date: str


class Language(BaseModel):
    language: str
    level: str


class CandidateProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    profile_version: str

    identity: dict[str, Any]
    work_authorization: dict[str, Any]
    career: dict[str, Any]

    professional_experience: list[ProfessionalExperience]
    academic_experience: list[AcademicExperience]
    projects: list[Project]

    education: list[Education]
    certifications: dict[str, Any]
    skills: dict[str, list[str]]
    languages: list[Language]

    job_search_constraints: dict[str, Any]
    truth_policy: dict[str, Any]

    @model_validator(mode="after")
    def enforce_truth_boundaries(self):
        # Projects must never masquerade as employment.
        for project in self.projects:
            if project.professional_experience is not False:
                raise ValueError(
                    f"Project '{project.name}' cannot be classified "
                    "as professional experience."
                )

        # Professional cybersecurity experience must use the
        # professional evidence level.
        for experience in self.professional_experience:
            if experience.evidence_level != "professional":
                raise ValueError(
                    f"Professional experience '{experience.title}' "
                    "must have evidence_level='professional'."
                )

        return self


def load_candidate_profile(
    path: str | Path = "profile/candidate.json",
) -> CandidateProfile:
    """Load and validate a candidate profile from JSON."""

    profile_path = Path(path)

    if not profile_path.exists():
        raise FileNotFoundError(
            f"Candidate profile not found: {profile_path}"
        )

    with profile_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return CandidateProfile.model_validate(data)


if __name__ == "__main__":
    profile = load_candidate_profile()

    print("Candidate profile loaded successfully")
    print(f"Name: {profile.identity.get('name')}")
    print(
        "Professional cybersecurity experiences:",
        len(profile.professional_experience),
    )
    print("Projects:", len(profile.projects))