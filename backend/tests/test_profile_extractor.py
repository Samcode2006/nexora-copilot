from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest
from pydantic import ValidationError

from app.ai.providers import LLMProviderError, LLMService, create_llm_service
from app.ai.resume_intelligence import (
    EducationProfile,
    EvidenceValue,
    PersonalInformation,
    StudentProfileFields,
    extract_student_profile,
)
from app.ai.resume_intelligence.profile_schemas import (
    ExperienceProfile,
    ProjectProfile,
    SkillProfile,
)


def _evidence(
    value: Any,
    quote: str,
    *,
    evidence_status: str = "explicit",
) -> EvidenceValue[Any]:
    # Deliberately overstate provider metadata; the service must recompute it.
    return EvidenceValue(
        value=value,
        source_text=quote,
        source_section="provider-invented-section",
        confidence="high",
        evidence_status=evidence_status,  # type: ignore[arg-type]
        verification_status="verified",
    )


class _SequenceProvider:
    name = "mock"
    model = "mock-profile-model"

    def __init__(self, responses: Iterable[Any]) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def generate_structured(self, *, prompt: str, response_model: type) -> Any:
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def complete_resume_and_draft() -> tuple[str, StudentProfileFields]:
    resume = """Name: Maya Patel
Email: maya.patel@example.test
Phone: +91 98765 43210
Location: Pune, India

Education
Institution: North Valley University
Degree: B.Tech
Branch: Computer Science
Graduation year: 2025
CGPA: 8.7

Skills
Programming Languages: Python, Java
Frameworks: FastAPI, React
Databases: PostgreSQL
Cloud Technologies: AWS
Tools: Docker, Git
Technical Domains: Machine Learning

Projects
Campus Planner
Description: Built a calendar app for student events.
Technologies: Python, FastAPI
Responsibilities: Designed API endpoints.
Achievements: Reduced manual scheduling tasks by 30%.
Study Notes Search
Description: Created searchable notes for classmates.

Experience
Company: Example Labs
Position: Software Intern
Duration: June 2024 - August 2024
Responsibilities: Built internal dashboards.
Achievements: Improved report generation time by 20%.

Internships
Company: Northwind Research
Position: Research Intern
Duration: Summer 2023
Responsibilities: Cleaned survey data.

Certifications
AWS Certified Cloud Practitioner

Awards
Award: Dean's list 2024

Achievements
Published a poster at the student research symposium."""
    draft = StudentProfileFields(
        personal_information=PersonalInformation(
            name=_evidence("Maya Patel", "Name: Maya Patel"),
            email=_evidence("maya.patel@example.test", "maya.patel@example.test"),
            phone=_evidence("+91 98765 43210", "Phone: +91 98765 43210"),
            location=_evidence("Pune, India", "Location: Pune, India"),
        ),
        education=[
            EducationProfile(
                institution=_evidence(
                    "North Valley University", "Institution: North Valley University"
                ),
                degree=_evidence("B.Tech", "Degree: B.Tech"),
                branch=_evidence("Computer Science", "Branch: Computer Science"),
                graduation_year=_evidence(2025, "Graduation year: 2025"),
                cgpa=_evidence(8.7, "CGPA: 8.7"),
            )
        ],
        skills=SkillProfile(
            programming_languages=[
                _evidence("Python", "Programming Languages: Python, Java"),
                _evidence("Java", "Programming Languages: Python, Java"),
            ],
            frameworks=[
                _evidence("FastAPI", "Frameworks: FastAPI, React"),
                _evidence("React", "Frameworks: FastAPI, React"),
            ],
            databases=[_evidence("PostgreSQL", "Databases: PostgreSQL")],
            cloud_technologies=[_evidence("AWS", "Cloud Technologies: AWS")],
            tools=[
                _evidence("Docker", "Tools: Docker, Git"),
                _evidence("Git", "Tools: Docker, Git"),
            ],
            technical_domains=[
                _evidence("Machine Learning", "Technical Domains: Machine Learning")
            ],
        ),
        projects=[
            ProjectProfile(
                name=_evidence("Campus Planner", "Campus Planner"),
                description=_evidence(
                    "Built a calendar app for student events.",
                    "Description: Built a calendar app for student events.",
                ),
                technologies=[
                    _evidence("Python", "Technologies: Python, FastAPI"),
                    _evidence("FastAPI", "Technologies: Python, FastAPI"),
                ],
                responsibilities=[
                    _evidence("Designed API endpoints.", "Responsibilities: Designed API endpoints.")
                ],
                achievements=[
                    _evidence(
                        "Reduced manual scheduling tasks by 30%.",
                        "Achievements: Reduced manual scheduling tasks by 30%.",
                    )
                ],
            ),
            ProjectProfile(
                name=_evidence("Study Notes Search", "Study Notes Search"),
                description=_evidence(
                    "Created searchable notes for classmates.",
                    "Description: Created searchable notes for classmates.",
                ),
            ),
        ],
        experience=[
            ExperienceProfile(
                company=_evidence("Example Labs", "Company: Example Labs"),
                position=_evidence("Software Intern", "Position: Software Intern"),
                duration=_evidence("June 2024 - August 2024", "Duration: June 2024 - August 2024"),
                responsibilities=[
                    _evidence("Built internal dashboards.", "Responsibilities: Built internal dashboards.")
                ],
                achievements=[
                    _evidence(
                        "Improved report generation time by 20%.",
                        "Achievements: Improved report generation time by 20%.",
                    )
                ],
            )
        ],
        internships=[
            ExperienceProfile(
                company=_evidence("Northwind Research", "Company: Northwind Research"),
                position=_evidence("Research Intern", "Position: Research Intern"),
                duration=_evidence("Summer 2023", "Duration: Summer 2023"),
                responsibilities=[
                    _evidence("Cleaned survey data.", "Responsibilities: Cleaned survey data.")
                ],
            )
        ],
        certifications=[
            _evidence("AWS Certified Cloud Practitioner", "AWS Certified Cloud Practitioner")
        ],
        awards=[_evidence("Dean's list 2024", "Award: Dean's list 2024")],
        achievements=[
            _evidence(
                "Published a poster at the student research symposium.",
                "Published a poster at the student research symposium.",
            )
        ],
    )
    return resume, draft


def test_extracts_complete_resume_with_evidence(complete_resume_and_draft) -> None:
    resume, draft = complete_resume_and_draft
    profile = extract_student_profile(
        resume,
        llm_service=LLMService(_SequenceProvider([draft])),
    )

    assert profile.personal_information.name.value == "Maya Patel"
    assert profile.personal_information.email.source_text == "maya.patel@example.test"
    assert profile.personal_information.name.source_section == "header"
    assert profile.education[0].institution.value == "North Valley University"
    assert profile.education[0].institution.source_section == "education"
    assert profile.skills.programming_languages[0].value == "Python"
    assert len(profile.projects) == 2
    assert profile.experience[0].company.value == "Example Labs"
    assert profile.internships[0].company.value == "Northwind Research"
    assert profile.certifications[0].value == "AWS Certified Cloud Practitioner"
    assert profile.awards[0].value == "Dean's list 2024"
    assert profile.achievements[0].verification_status == "unverified"
    assert profile.extraction_provider == "mock"
    assert profile.is_fallback is False


def test_missing_education_details_remain_null() -> None:
    resume = "Education\nInstitution: Central College"
    draft = StudentProfileFields(
        education=[
            EducationProfile(
                institution=_evidence("Central College", "Institution: Central College")
            )
        ]
    )
    profile = extract_student_profile(
        resume,
        llm_service=LLMService(_SequenceProvider([draft])),
    )
    education = profile.education[0]
    assert education.institution.value == "Central College"
    assert education.degree is None
    assert education.branch is None
    assert education.graduation_year is None
    assert education.cgpa is None


def test_resume_without_experience_returns_empty_experience() -> None:
    resume = "Name: Jordan Lee\nSkills\nPython"
    draft = StudentProfileFields(
        personal_information=PersonalInformation(
            name=_evidence("Jordan Lee", "Name: Jordan Lee")
        )
    )
    profile = extract_student_profile(
        resume,
        llm_service=LLMService(_SequenceProvider([draft])),
    )
    assert profile.experience == []
    assert profile.internships == []


def test_multiple_projects_are_preserved() -> None:
    resume = "Projects\nAlpha Tool\nBuilt a planner.\nBeta Tool\nBuilt a tracker."
    draft = StudentProfileFields(
        projects=[
            ProjectProfile(
                name=_evidence("Alpha Tool", "Alpha Tool"),
                description=_evidence("Built a planner.", "Built a planner."),
            ),
            ProjectProfile(
                name=_evidence("Beta Tool", "Beta Tool"),
                description=_evidence("Built a tracker.", "Built a tracker."),
            ),
        ]
    )
    profile = extract_student_profile(
        resume,
        llm_service=LLMService(_SequenceProvider([draft])),
    )
    assert [project.name.value for project in profile.projects] == ["Alpha Tool", "Beta Tool"]


def test_duplicate_skills_are_removed_case_insensitively() -> None:
    resume = "Skills\nPython, python"
    draft = StudentProfileFields(
        skills=SkillProfile(
            programming_languages=[
                _evidence("Python", "Python, python"),
                _evidence("python", "Python, python"),
            ]
        )
    )
    profile = extract_student_profile(
        resume,
        llm_service=LLMService(_SequenceProvider([draft])),
    )
    assert [skill.value for skill in profile.skills.programming_languages] == ["Python"]


def test_ambiguous_information_is_low_confidence_and_needs_review() -> None:
    resume = "Education\nExpected graduation: 2026"
    draft = StudentProfileFields(
        education=[
            EducationProfile(
                graduation_year=_evidence(
                    2026,
                    "Expected graduation: 2026",
                    evidence_status="uncertain",
                )
            )
        ]
    )
    profile = extract_student_profile(
        resume,
        llm_service=LLMService(_SequenceProvider([draft])),
    )
    year = profile.education[0].graduation_year
    assert year.value == 2026
    assert year.confidence == "low"
    assert year.evidence_status == "uncertain"
    assert year.verification_status == "needs_review"


def test_invalid_llm_response_is_retried_and_recovered(complete_resume_and_draft) -> None:
    resume, draft = complete_resume_and_draft
    provider = _SequenceProvider(["{invalid json", draft])
    profile = extract_student_profile(resume, llm_service=LLMService(provider))
    assert profile.personal_information.name.value == "Maya Patel"
    assert profile.is_fallback is False
    assert len(provider.prompts) == 2
    assert "previous response failed validation" in provider.prompts[1].lower()


def test_missing_credentials_use_deterministic_fallback(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    service = create_llm_service()
    assert service.provider is None

    profile = extract_student_profile(
        "Name: Sam Rivera\nEmail: sam@example.test\nSkills\nPython\n"
        "Internships\nCompany: River Labs\nPosition: Student Intern\n"
        "Duration: May 2025 - June 2025",
        llm_service=service,
    )
    assert profile.is_fallback is True
    assert profile.extraction_provider == "deterministic_fallback"
    assert profile.personal_information.name.value == "Sam Rivera"
    assert profile.personal_information.email.value == "sam@example.test"
    assert profile.skills.programming_languages[0].value == "Python"
    assert profile.internships[0].company.value == "River Labs"


def test_unsupported_factual_claim_is_omitted(complete_resume_and_draft) -> None:
    resume, _ = complete_resume_and_draft
    unsupported = StudentProfileFields(
        personal_information=PersonalInformation(
            name=_evidence("Maya Patel", "Name: Maya Patel"),
        ),
        projects=[
            ProjectProfile(
                achievements=[
                    _evidence(
                        "Made the product 10x faster.",
                        "Achievements: Reduced manual scheduling tasks by 30%.",
                    )
                ]
            )
        ],
    )
    profile = extract_student_profile(
        resume,
        llm_service=LLMService(_SequenceProvider([unsupported])),
    )
    assert profile.personal_information.name.value == "Maya Patel"
    assert profile.projects == []
    assert any("unsupported" in warning for warning in profile.warnings)


def test_provider_failures_fall_back_after_retry() -> None:
    provider = _SequenceProvider(
        [LLMProviderError("temporary provider failure"), LLMProviderError("still offline")]
    )
    profile = extract_student_profile(
        "Name: Nina Das",
        llm_service=LLMService(provider),
    )
    assert profile.is_fallback is True
    assert len(provider.prompts) == 2
    assert profile.personal_information.name.value == "Nina Das"


def test_profile_schemas_validate_email_and_score_ranges() -> None:
    with pytest.raises(ValidationError):
        PersonalInformation(email=EvidenceValue(value="not-an-email", source_text="not-an-email"))
    with pytest.raises(ValidationError):
        EducationProfile(cgpa=EvidenceValue(value=125.0, source_text="CGPA: 125"))
