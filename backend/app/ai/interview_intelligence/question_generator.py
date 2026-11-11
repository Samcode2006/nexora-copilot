"""Role-specific question generation with profile-grounded offline templates."""

from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from app.ai.job_intelligence.schemas import JobListing
from app.ai.job_matching.evidence import is_supported_fact
from app.ai.job_matching.schemas import JobMatch
from app.ai.providers import LLMService, create_llm_service
from app.ai.resume_intelligence.profile_schemas import EvidenceValue, StudentProfile

from .prompts import build_question_prompt
from .rubrics import default_rubric
from .schemas import (
    Difficulty,
    InterviewQuestion,
    InterviewStartRequest,
    InterviewType,
    QuestionBatchDraft,
    QuestionDraft,
    QuestionEvidenceReference,
)

_QUESTION_NAMESPACE = uuid.UUID("8514384a-4517-44c7-8f79-7dc911e97e64")
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[+#.][a-z0-9+#.]*)?", re.IGNORECASE)
_PROJECT_QUESTION_WORDS = {
    "a", "about", "and", "approach", "architecture", "as", "at", "built", "can",
    "challenge", "challenges", "choice", "choices", "choose", "component", "consider",
    "considered", "decision", "decisions", "describe", "design", "did", "discuss",
    "do", "does", "explain", "for", "from", "how", "if", "improve", "improvements",
    "include", "including", "in", "it", "key", "made", "might", "off", "one", "or", "our",
    "personally", "project", "profile", "relevant", "role", "show", "shown", "specific",
    "step", "steps", "technology", "technologies", "tell", "the", "their", "this", "trade",
    "tradeoff", "tradeoffs", "tradeoffs", "up", "used", "using", "was", "were", "what",
    "when", "where", "which", "why", "with", "work", "worked", "would", "you", "your",
    "testing", "test", "tested", "result", "results", "purpose", "problem", "goal", "goals",
    "system", "data", "application", "feature", "features", "user", "users", "service", "api",
    "constraint", "constraints", "alternative", "alternatives", "failure", "failures", "case",
    "cases", "performance", "scaling", "scale", "implementation", "implemented", "learned",
}
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "by", "for", "from",
    "had", "has", "have", "he", "her", "how", "i", "if", "in", "into", "is", "it", "its",
    "me", "my", "of", "on", "or", "our", "she", "that", "the", "their", "them", "there",
    "these", "they", "this", "those", "to", "was", "we", "were", "what", "which", "who",
    "with", "would", "you", "your",
}


@dataclass(frozen=True)
class _ProfileFact:
    path: str
    evidence: EvidenceValue[Any]

    @property
    def value(self) -> str:
        return str(self.evidence.value)

    def reference(self) -> QuestionEvidenceReference:
        return QuestionEvidenceReference(
            profile_path=self.path,
            value=self.value,
            source_text=self.evidence.source_text or "",
            source_section=self.evidence.source_section,
            confidence=self.evidence.confidence,
            evidence_status=self.evidence.evidence_status,
            verification_status=self.evidence.verification_status,
        )


@dataclass(frozen=True)
class _Target:
    competency: str
    requirement: str | None
    evidence_paths: tuple[str, ...] = ()
    profile_values: tuple[str, ...] = ()


def generate_interview_questions(
    student_profile: StudentProfile,
    job_listing: JobListing,
    interview_type: InterviewType,
    difficulty: Difficulty,
    question_count: int = 10,
    *,
    job_match: JobMatch | None = None,
    llm_service: LLMService | None = None,
    focus_competency: str | None = None,
    exclude_question_texts: tuple[str, ...] | list[str] = (),
    variant_offset: int = 0,
) -> list[InterviewQuestion]:
    """Generate distinct questions, hiding the answer key in normal serialization.

    The deterministic template path is offline and role-aware. Project-based
    questions always cite actual supported project facts or explicitly ask the
    student to supply an example when the profile contains none.
    """
    if isinstance(question_count, bool) or not isinstance(question_count, int):
        raise ValueError("question_count must be an integer")
    request = InterviewStartRequest(
        student_profile=student_profile,
        job_listing=job_listing,
        job_match=job_match,
        interview_type=interview_type,
        difficulty=difficulty,
        question_count=question_count,
    )
    facts = _collect_profile_facts(request.student_profile)
    allowed_paths = _question_profile_paths(facts, request.interview_type)
    references = [facts[path].reference() for path in allowed_paths]
    provider_result = _generate_question_batch(
        request.student_profile,
        request.job_listing,
        request.interview_type,
        request.difficulty,
        request.question_count,
        references,
        request.job_match,
        focus_competency,
        llm_service,
    )
    result, provider_warning = provider_result
    fallback_provider = result.is_fallback
    job_context = _job_context_tokens(request.job_listing)
    used_texts = {_normalize(text) for text in exclude_question_texts}
    output: list[InterviewQuestion] = []
    for draft in result.value.questions:
        if len(output) >= question_count:
            break
        question = _from_provider_draft(
            draft,
            request.interview_type,
            request.difficulty,
            request.student_profile,
            request.job_listing,
            facts,
            allowed_paths,
            job_context,
            result.provider,
            provider_warning,
        )
        if question is None:
            continue
        normalized = _normalize(question.question_text)
        if normalized in used_texts:
            continue
        used_texts.add(normalized)
        output.append(question)

    targets = _targets(
        request.student_profile,
        request.job_listing,
        request.interview_type,
        facts,
        request.job_match,
    )
    if focus_competency:
        focus_key = _canonical(focus_competency)
        focus_skill_key = _competency_name(focus_competency)
        focused = [
            target
            for target in targets
            if _canonical(target.competency) == focus_key
            or (
                target.requirement is not None
                and _competency_name(target.requirement) == focus_skill_key
            )
        ]
        targets = focused + [target for target in targets if target not in focused]
    offset = max(0, variant_offset)
    variant_index = 0
    while len(output) < question_count:
        target_index = (
            variant_index % len(targets)
            if focus_competency
            else (offset + variant_index) % len(targets)
        )
        target = targets[target_index]
        variant = (offset + variant_index) // len(targets)
        question = _fallback_question(
            request.interview_type,
            request.difficulty,
            request.job_listing,
            target,
            facts,
            variant,
            provider_warning,
        )
        normalized = _normalize(question.question_text)
        variant_index += 1
        if normalized in used_texts:
            if variant_index > question_count * max(3, len(targets)):
                break
            continue
        used_texts.add(normalized)
        output.append(question)

    if len(output) < question_count:
        # If only a single competency is available, explicit variant framing
        # keeps ids and exact text unique without asserting new student facts.
        while len(output) < question_count:
            target = targets[len(output) % len(targets)]
            variant = len(output) + offset + 100
            question = _fallback_question(
                request.interview_type,
                request.difficulty,
                request.job_listing,
                target,
                facts,
                variant,
                provider_warning,
            )
            if _normalize(question.question_text) in used_texts:
                break
            used_texts.add(_normalize(question.question_text))
            output.append(question)
    return output[:question_count]


def available_competencies(
    student_profile: StudentProfile,
    job_listing: JobListing,
    interview_type: InterviewType,
    *,
    job_match: JobMatch | None = None,
) -> list[str]:
    """Return deterministic competency targets available for an interview."""
    facts = _collect_profile_facts(student_profile)
    return [
        target.competency
        for target in _targets(student_profile, job_listing, interview_type, facts, job_match)
    ]


def _generate_question_batch(
    profile: StudentProfile,
    job: JobListing,
    interview_type: InterviewType,
    difficulty: Difficulty,
    question_count: int,
    evidence: list[QuestionEvidenceReference],
    job_match: JobMatch | None,
    focus_competency: str | None,
    llm_service: LLMService | None,
):
    prompt = build_question_prompt(
        student_profile=profile,
        job_listing=job,
        interview_type=interview_type,
        difficulty=difficulty,
        question_count=question_count,
        evidence=evidence,
        job_match=job_match,
        focus_competency=focus_competency,
    )
    service = llm_service if llm_service is not None else create_llm_service()
    warning = None
    try:
        result = service.generate_structured(
            prompt=prompt,
            response_model=QuestionBatchDraft,
            fallback=QuestionBatchDraft,
            max_attempts=2,
        )
    except Exception as exc:
        warning = f"Question provider failed ({type(exc).__name__}); deterministic templates were used."
        result = LLMService().generate_structured(
            prompt="",
            response_model=QuestionBatchDraft,
            fallback=QuestionBatchDraft,
        )
    if result.is_fallback and warning is None:
        warning = result.fallback_reason or "No structured question provider was available."
    return result, warning


def _from_provider_draft(
    draft: QuestionDraft,
    requested_type: InterviewType,
    requested_difficulty: Difficulty,
    profile: StudentProfile,
    job: JobListing,
    facts: dict[str, _ProfileFact],
    allowed_paths: set[str],
    job_tokens: set[str],
    provider: str,
    warning: str | None,
) -> InterviewQuestion | None:
    if draft.interview_type != requested_type or draft.difficulty != requested_difficulty:
        return None
    if draft.relevant_job_requirement and not _is_job_requirement(draft.relevant_job_requirement, job):
        return None
    if any(path not in facts or path not in allowed_paths for path in draft.profile_evidence_paths):
        return None
    if requested_type == "project_based":
        if not any(path.startswith("projects[") for path in facts):
            # Keep missing-profile project prompts in the deterministic path,
            # which explicitly allows the student to have no project example.
            return None
        if profile.projects:
            if not draft.profile_evidence_paths or not all(
                path.startswith("projects[") for path in draft.profile_evidence_paths
            ):
                return None
            project_values = " ".join(facts[path].value for path in draft.profile_evidence_paths)
            allowed = set(_tokens(project_values)) | job_tokens | _PROJECT_QUESTION_WORDS | set(_tokens(draft.competency))
            if not _tokens_supported(draft.question_text, allowed):
                return None
            if any(not _tokens_supported(point, allowed) for point in draft.expected_answer_points):
                return None

    profile_refs = [facts[path].reference() for path in dict.fromkeys(draft.profile_evidence_paths)]
    target = _Target(
        competency=draft.competency,
        requirement=draft.relevant_job_requirement,
        evidence_paths=tuple(draft.profile_evidence_paths),
        profile_values=tuple(facts[path].value for path in draft.profile_evidence_paths),
    )
    rubric = default_rubric(requested_type)
    expected_points = list(dict.fromkeys(draft.expected_answer_points))
    if not expected_points:
        expected_points = _fallback_points(requested_type, target, requested_difficulty)

    return _make_question(
        question_text=draft.question_text,
        interview_type=requested_type,
        difficulty=requested_difficulty,
        competency=draft.competency,
        requirement=draft.relevant_job_requirement,
        profile_refs=profile_refs,
        expected_points=expected_points,
        follow_up=draft.follow_up_guidance,
        rubric=rubric,
        keywords=_evaluation_keywords(expected_points, target),
        provider=provider,
        method="llm_structured",
        warning=warning,
        job_id=job.job_id,
    )


def _fallback_question(
    interview_type: InterviewType,
    difficulty: Difficulty,
    job: JobListing,
    target: _Target,
    facts: dict[str, _ProfileFact],
    variant: int,
    warning: str | None,
) -> InterviewQuestion:
    role = job.title or "this role"
    points = _fallback_points(interview_type, target, difficulty)
    references = [facts[path].reference() for path in target.evidence_paths if path in facts]
    if interview_type == "technical":
        if target.competency == "education_fundamentals" and target.profile_values:
            field = ", ".join(target.profile_values)
            question = (
                f"Which concept from your {field} education is useful for a {role} role, "
                "and how would you apply or validate it?"
            )
        else:
            subject = target.requirement or target.competency.replace("_", " ")
            variants = [
                f"What does {subject} do, and where might it be useful in a {role} role?",
                f"Explain one core concept in {subject} and give an example relevant to {role}.",
                f"A task in a {role} role involves {subject}. How would you approach it and check your result?",
            ]
            question = variants[variant % len(variants)]
        suffix = _difficulty_suffix(difficulty, variant)
        if suffix:
            question += " " + suffix
        follow_up = "Ask the student to clarify a concept, justify an approach, or consider a trade-off."
    elif interview_type == "project_based":
        if target.profile_values:
            project_name = next(
                (facts[path].value for path in target.evidence_paths if path.endswith(".name") and path in facts),
                None,
            )
            description = next(
                (facts[path].value for path in target.evidence_paths if path.endswith(".description") and path in facts),
                None,
            )
            technology_values = [
                facts[path].value
                for path in target.evidence_paths
                if ".technologies[" in path and path in facts
            ]
            subject = project_name or description or "the profile-listed project"
            variants = [
                f"Your profile lists the project {subject}. What problem or goal was it intended to address, and what did you personally contribute?",
                f"For the project {subject}, did you encounter a challenge? If not, describe one you would anticipate and how you would investigate it.",
                f"For the project {subject}, explain one design decision and any trade-off you considered, if applicable.",
                f"For the project {subject}, what guided your implementation choices? Discuss a listed technology or an alternative you would consider.",
                f"For the project {subject}, how did you check that the work met its intended goal? If this was not documented, describe how you would test it.",
            ]
            question = variants[variant % len(variants)]
            if technology_values:
                points.append("Technologies listed: " + ", ".join(technology_values))
            if description:
                points.append("Profile description: " + description)
        else:
            question = (
                "The profile does not include project details. Is there an academic, personal, or practice project you would like to discuss? If not, you may skip this question."
            )
            points = [
                "If applicable, state the project goal.",
                "If applicable, explain the student's own contribution.",
                "Do not assume a project exists when the student says there is none.",
            ]
        suffix = _difficulty_suffix(difficulty, variant)
        if suffix:
            question += " " + suffix
        follow_up = "Invite a specific example or decision; do not assume undocumented project features."
    elif interview_type == "hr_behavioral":
        question, competency, points, follow_up = _behavioral_question(difficulty, variant)
        target = _Target(competency=competency, requirement=None)
    else:
        subject = target.requirement or job.title or "the role's core responsibilities"
        variants = [
            f"The selected role lists {subject}. How would you approach a task requiring this competency, including how you would check your work?",
            f"For a {role} position involving {subject}, what trade-offs or constraints would you consider before choosing an approach?",
            f"Describe how you would apply {subject} to a realistic task in a {role} role. If you have not used it, explain how you would learn and validate an approach.",
        ]
        question = variants[variant % len(variants)]
        suffix = _difficulty_suffix(difficulty, variant)
        if suffix:
            question += " " + suffix
        follow_up = "Ask for assumptions, validation steps, and an alternative approach where relevant."

    if variant >= 6:
        question += " For this variation, focus especially on " + _variation_focus(variant - 6) + "."

    return _make_question(
        question_text=question,
        interview_type=interview_type,
        difficulty=difficulty,
        competency=target.competency,
        requirement=target.requirement,
        profile_refs=references,
        expected_points=points,
        follow_up=follow_up,
        rubric=default_rubric(interview_type),
        keywords=_evaluation_keywords(points, target),
        provider="deterministic_fallback",
        method="deterministic_templates",
        warning=warning,
        job_id=job.job_id,
    )


def _targets(
    profile: StudentProfile,
    job: JobListing,
    interview_type: InterviewType,
    facts: dict[str, _ProfileFact],
    job_match: JobMatch | None,
) -> list[_Target]:
    if interview_type == "hr_behavioral":
        return [
            _Target(item, None)
            for item in (
                "teamwork",
                "problem_solving",
                "communication",
                "adaptability",
                "conflict_resolution",
                "learning_ability",
                "career_goals",
                "leadership_approach",
            )
        ]
    if interview_type == "project_based":
        targets: list[_Target] = []
        for index, project in enumerate(profile.projects):
            paths = tuple(path for path in facts if path.startswith(f"projects[{index}]."))
            if paths:
                name_path = f"projects[{index}].name"
                label = facts[name_path].value if name_path in facts else f"project_{index + 1}"
                targets.append(
                    _Target(
                        competency="project_architecture",
                        requirement=_best_job_skill(job, facts, paths),
                        evidence_paths=paths,
                        profile_values=tuple(facts[path].value for path in paths),
                    )
                )
                # Preserve the human-readable project identifier for focus matching.
                targets[-1] = _Target(
                    competency=f"project_architecture:{label}",
                    requirement=targets[-1].requirement,
                    evidence_paths=paths,
                    profile_values=targets[-1].profile_values,
                )
        return targets or [_Target("project_reflection", job.title)]

    requested = [*job.required_skills, *job.preferred_skills]
    if job_match:
        matched = [item.job_skill for item in job_match.matched_skills]
        requested = list(dict.fromkeys([
            *job_match.missing_required_skills,
            *job.required_skills,
            *matched,
            *job.preferred_skills,
        ]))
    skill_targets: list[_Target] = []
    for skill in requested:
        related = tuple(
            path for path, fact in facts.items()
            if (
                path.startswith("skills.") and _canonical(fact.value) == _canonical(skill)
            ) or (
                path.startswith(("projects[", "experience[", "internships["))
                and _contains_phrase(fact.value, skill)
            )
        )
        skill_targets.append(
            _Target(
                competency=_competency_name(skill),
                requirement=skill,
                evidence_paths=related,
                profile_values=tuple(facts[path].value for path in related),
            )
        )
    if not skill_targets:
        for path, fact in facts.items():
            if path.startswith("skills."):
                skill_targets.append(
                    _Target(
                        competency=_competency_name(fact.value),
                        requirement=fact.value,
                        evidence_paths=(path,),
                        profile_values=(fact.value,),
                    )
                )
    education_target = None
    if _is_technical_role(job):
        education_paths = tuple(
            path for path in facts
            if path.startswith("education[") and path.rsplit(".", 1)[-1] in {"degree", "branch"}
        )
        education_values = tuple(facts[path].value for path in education_paths)
        if education_values:
            education_target = _Target(
                competency="education_fundamentals",
                requirement=None,
                evidence_paths=education_paths,
                profile_values=education_values,
            )
    if skill_targets:
        targets = _unique_targets(skill_targets)
        if education_target:
            targets.append(education_target)
        return targets
    if education_target:
        return [education_target]

    # Stay role-specific even when the listing lacks a structured skill array.
    description_subject = (job.description or "").strip()
    fallback = job.title or (description_subject[:100] if description_subject else "role fundamentals")
    return [_Target("role_fundamentals", fallback)]


def _best_job_skill(job: JobListing, facts: dict[str, _ProfileFact], paths: tuple[str, ...]) -> str | None:
    values = " ".join(facts[path].value.casefold() for path in paths if path in facts)
    for skill in [*job.required_skills, *job.preferred_skills]:
        if skill.casefold() in values:
            return skill
    return None


def _unique_targets(targets: list[_Target]) -> list[_Target]:
    output: list[_Target] = []
    seen: set[str] = set()
    for target in targets:
        key = _canonical(target.competency)
        if key not in seen:
            seen.add(key)
            output.append(target)
    return output


def _fallback_points(
    interview_type: InterviewType,
    target: _Target,
    difficulty: Difficulty,
) -> list[str]:
    subject = target.requirement or target.competency.replace("_", " ")
    if interview_type == "hr_behavioral":
        return [
            "State the situation or context, if using a past example.",
            "Explain the student's own action or intended approach.",
            "Describe the outcome or what the student would learn.",
        ]
    base = [f"Address the question's focus on {subject}."]
    if difficulty == "beginner":
        return [*base, "Explain one relevant concept or goal.", "Give a simple example or application."]
    if difficulty == "intermediate":
        return [*base, "Describe a reasoned approach.", "Discuss a trade-off or validation step."]
    return [*base, "Justify a design or solution choice.", "Discuss constraints, failure cases, or alternatives."]


def _behavioral_question(
    difficulty: Difficulty, variant: int
) -> tuple[str, str, list[str], str]:
    prompts: list[tuple[str, str]] = [
        ("teamwork", "Describe a time you worked with others toward a shared goal. If you do not have a past example, explain how you would approach it."),
        ("problem_solving", "Tell me about a difficult problem you worked through, or describe the steps you would take in a similar situation."),
        ("communication", "How would you explain a complex technical idea to someone with a different background? You may use a real or hypothetical example."),
        ("adaptability", "Describe a time plans changed unexpectedly, or explain how you would adapt when a project requirement changes."),
        ("conflict_resolution", "If a teammate disagreed with your technical approach, how would you work toward a resolution? Use a past example only if you have one."),
        ("learning_ability", "How do you approach learning a new tool or concept when a task requires it? Give an example if available."),
        ("career_goals", "What skills or responsibilities would you like to develop in your next role, and why?"),
        ("leadership_approach", "How would you help a group make progress when responsibilities are unclear? Use a real example only if one is available."),
    ]
    competency, question = prompts[variant % len(prompts)]
    if difficulty == "beginner":
        question += " Keep your answer focused on the situation and your next step."
    elif difficulty == "advanced":
        question += " Include constraints, stakeholders, alternatives, and how you would assess the outcome."
    points = [
        "State the situation or context, if using a past example.",
        "Explain the student's own action or intended approach.",
        "Describe the outcome or what the student would learn.",
    ]
    follow_up = "Use STAR (Situation, Task, Action, Result) for a past example; a hypothetical answer is acceptable when experience is absent."
    return question, competency, points, follow_up


def _make_question(
    *,
    question_text: str,
    interview_type: InterviewType,
    difficulty: Difficulty,
    competency: str,
    requirement: str | None,
    profile_refs: list[QuestionEvidenceReference],
    expected_points: list[str],
    follow_up: str,
    rubric,
    keywords: list[str],
    provider: str,
    method: str,
    warning: str | None,
    job_id: str,
) -> InterviewQuestion:
    normalized = _normalize(question_text)
    question_id = str(
        uuid.uuid5(
            _QUESTION_NAMESPACE,
            "|".join((job_id, interview_type, difficulty, competency, normalized)),
        )
    )
    return InterviewQuestion(
        question_id=question_id,
        question_text=question_text,
        interview_type=interview_type,
        difficulty=difficulty,
        competency=competency,
        relevant_job_requirement=requirement,
        profile_evidence_references=profile_refs,
        follow_up_guidance=follow_up,
        generation_provider=provider,
        generation_method=method,  # type: ignore[arg-type]
        generation_warning=warning,
        expected_answer_points=list(dict.fromkeys(expected_points)),
        evaluation_rubric=rubric,
        evaluation_keywords=list(dict.fromkeys(keyword for keyword in keywords if keyword)),
    )


def _collect_profile_facts(profile: StudentProfile) -> dict[str, _ProfileFact]:
    facts: dict[str, _ProfileFact] = {}

    def visit(value: Any, path: str) -> None:
        if isinstance(value, EvidenceValue):
            if is_supported_fact(value):
                facts[path] = _ProfileFact(path=path, evidence=value)
        elif isinstance(value, BaseModel):
            for name in type(value).model_fields:
                child_path = f"{path}.{name}" if path else name
                visit(getattr(value, name), child_path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")

    visit(profile, "")
    return facts


def _evaluation_keywords(points: list[str], target: _Target) -> list[str]:
    text = " ".join([*points, *target.profile_values, target.requirement or ""])
    return [
        token
        for token in dict.fromkeys(_tokens(text))
        if token not in _STOP_WORDS and len(token) > 1
    ]


def _is_job_requirement(value: str, job: JobListing) -> bool:
    allowed = [*job.required_skills, *job.preferred_skills, *job.eligibility_criteria]
    if job.title:
        allowed.append(job.title)
    return any(_normalize(value) == _normalize(item) for item in allowed)


def _job_context_tokens(job: JobListing) -> set[str]:
    text = " ".join(
        item
        for item in [job.title, job.description, *job.required_skills, *job.preferred_skills]
        if item
    )
    return set(_tokens(text))


def _question_profile_paths(
    facts: dict[str, _ProfileFact], interview_type: InterviewType
) -> set[str]:
    if interview_type == "hr_behavioral":
        return set()
    if interview_type == "project_based":
        return {path for path in facts if path.startswith("projects[")}
    prefixes = ("skills.", "education[", "projects[", "experience[", "internships[")
    return {path for path in facts if path.startswith(prefixes)}


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z0-9+#]){re.escape(phrase.casefold())}(?![a-z0-9+#])", text.casefold()) is not None


def _is_technical_role(job: JobListing) -> bool:
    role_text = " ".join([job.title or "", job.description or ""]).casefold()
    return any(term in role_text for term in ("software", "developer", "engineer", "technical", "backend", "frontend", "data science"))


def _tokens_supported(text: str, allowed: set[str]) -> bool:
    tokens = set(_tokens(text))
    return tokens <= allowed


def _tokens(text: str) -> list[str]:
    return [
        token
        for match in _TOKEN_RE.findall(unicodedata.normalize("NFKC", text))
        if (token := match.casefold().rstrip("."))
    ]


def _normalize(text: str) -> str:
    return " ".join(_tokens(text))


def _canonical(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9+#. ]", "", text.casefold())
    return re.sub(r"\s+", " ", cleaned).strip()


def _competency_name(skill: str) -> str:
    aliases = {
        "python": "python_fundamentals",
        "sql": "sql",
        "postgres": "sql_databases",
        "postgresql": "sql_databases",
        "mysql": "sql_databases",
        "mongodb": "nosql_databases",
        "rest api": "api_design",
        "apis": "api_design",
        "fastapi": "api_development",
        "django": "api_development",
        "flask": "api_development",
        "aws": "cloud_fundamentals",
        "azure": "cloud_fundamentals",
        "gcp": "cloud_fundamentals",
        "data structures": "data_structures",
        "algorithms": "algorithms",
    }
    normalized = _canonical(skill)
    if normalized in aliases:
        return aliases[normalized]
    slug = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return slug[:80] or "role_fundamentals"


def _difficulty_suffix(difficulty: Difficulty, variant: int) -> str:
    if difficulty == "beginner":
        return "Start with the key idea and one straightforward example." if variant % 2 == 0 else "Keep the explanation focused on fundamentals."
    if difficulty == "intermediate":
        return "Include one practical trade-off or validation step." if variant % 2 == 0 else "Explain your reasoning, not only the outcome."
    return "Discuss constraints, failure cases, and alternatives where relevant." if variant % 2 == 0 else "Explain how you would validate the approach under realistic constraints."


def _variation_focus(index: int) -> str:
    focus_areas = (
        "assumptions",
        "testing and validation",
        "edge cases",
        "maintainability",
        "constraints",
        "alternatives",
        "failure handling",
        "communication of trade-offs",
        "how you would measure success",
        "what you would learn next",
        "risks and mitigations",
        "how you would explain the decision",
        "the order of implementation steps",
        "an alternative design",
        "what could go wrong in production",
        "input validation and boundary cases",
        "how you would debug a failure",
        "data privacy considerations",
        "reliability and recovery",
        "how you would test the behavior",
        "how you would keep the solution simple",
        "the expected impact on users",
        "what information you would clarify first",
        "how you would review the result",
        "performance constraints",
        "how you would collaborate with a teammate",
        "how you would document the approach",
        "how you would monitor the result",
        "the most important trade-off",
        "how you would handle incomplete information",
        "how you would prioritize the work",
        "how the approach could be extended later",
        "the evidence you would use to validate success",
        "how you would communicate uncertainty",
        "accessibility and usability considerations",
        "how you would roll back a failure",
        "how you would identify hidden assumptions",
        "what you would check before delivery",
    )
    return focus_areas[index % len(focus_areas)]
