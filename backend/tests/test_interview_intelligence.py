"""Offline tests for Phase 6 interview generation, evaluation, and adaptation."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from app.ai.interview_intelligence import (
    AnswerEvaluation,
    InterviewSession,
    RubricWeights,
    default_rubric_weights,
    end_interview,
    evaluate_interview_answer,
    generate_interview_questions,
    get_interview_report,
    get_question_evaluation_material,
    select_next_question,
    serialize_interview_session,
    start_interview,
    submit_interview_answer,
)
from app.ai.interview_intelligence.schemas import AnswerEvaluationDraft
from app.ai.job_intelligence.schemas import JobListing
from app.ai.providers import LLMProviderError, LLMService
from app.ai.resume_intelligence.profile_schemas import (
    EducationProfile,
    EvidenceValue,
    PersonalInformation,
    ProjectProfile,
    SkillProfile,
    StudentProfile,
)


def _fact(value: Any, source: str | None = None) -> EvidenceValue[Any]:
    source_text = source or str(value)
    return EvidenceValue(
        value=value,
        source_text=source_text,
        source_section="resume",
        confidence="medium",
        evidence_status="explicit",
        verification_status="unverified",
    )


@pytest.fixture
def profile() -> StudentProfile:
    return StudentProfile(
        personal_information=PersonalInformation(
            name=_fact("Maya Patel", "Name: Maya Patel"),
            email=_fact("maya.patel@example.test", "Email: maya.patel@example.test"),
        ),
        education=[
            EducationProfile(
                degree=_fact("B.Tech", "Degree: B.Tech"),
                branch=_fact("Computer Science", "Branch: Computer Science"),
            )
        ],
        skills=SkillProfile(
            programming_languages=[_fact("Python", "Programming Languages: Python")],
            frameworks=[_fact("FastAPI", "Frameworks: FastAPI")],
            databases=[_fact("PostgreSQL", "Databases: PostgreSQL")],
        ),
        projects=[
            ProjectProfile(
                name=_fact("Campus Planner", "Project: Campus Planner"),
                description=_fact(
                    "Built a campus events calendar API using Python and FastAPI.",
                    "Description: Built a campus events calendar API using Python and FastAPI.",
                ),
                technologies=[_fact("Python", "Technologies: Python, FastAPI")],
            )
        ],
        extraction_provider="test_fixture",
        is_fallback=False,
    )


@pytest.fixture
def job() -> JobListing:
    return JobListing(
        job_id="fixture:python-backend",
        title="Python Backend Intern",
        company="Example Co",
        description="Build APIs and data services with Python and FastAPI.",
        required_skills=["Python", "FastAPI", "SQL"],
        preferred_skills=["Docker"],
        source_provider="test_fixture",
        source_job_id="python-backend",
    )


class QueueProvider:
    name = "mock_interview"
    model = "offline-fixture"

    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses)
        self.calls = 0
        self.prompts: list[str] = []

    def generate_structured(self, *, prompt: str, response_model: type) -> Any:
        self.calls += 1
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class RubricProvider:
    name = "mock_rubric"
    model = "offline-fixture"

    def __init__(self, score: float = 80.0) -> None:
        self.score = score

    def generate_structured(self, *, prompt: str, response_model: type) -> Any:
        if response_model.__name__ == "QuestionBatchDraft":
            return {"questions": []}
        names = (
            "technical_correctness",
            "conceptual_understanding",
            "depth_of_explanation",
            "relevance",
            "problem_solving",
            "communication_clarity",
            "practical_application",
        )
        return {
            "dimension_scores": {name: self.score for name in names},
            "explanations": {name: f"Assessed {name.replace('_', ' ')}." for name in names},
            "strengths": ["The answer gives a relevant explanation."],
            "weaknesses": [],
            "missing_concepts": [],
            "improvement_suggestions": ["Add a concrete example."],
            "example_areas_to_improve": [],
            "answer_evidence_quotes": {"communication_clarity": ["Python uses indentation"]},
        }


def _question_draft(interview_type: str = "technical", difficulty: str = "intermediate") -> dict[str, Any]:
    return {
        "question_text": "How would you use Python to build a reliable API endpoint?",
        "interview_type": interview_type,
        "difficulty": difficulty,
        "competency": "python_fundamentals",
        "relevant_job_requirement": "Python",
        "expected_answer_points": ["Explain Python concepts", "Describe validation and testing"],
        "profile_evidence_paths": ["skills.programming_languages[0]"],
        "follow_up_guidance": "Ask about validation and error handling.",
    }


def _evaluation_draft(score: float = 75) -> dict[str, Any]:
    names = (
        "technical_correctness",
        "conceptual_understanding",
        "depth_of_explanation",
        "relevance",
        "problem_solving",
        "communication_clarity",
        "practical_application",
    )
    return {
        "dimension_scores": {name: score for name in names},
        "explanations": {name: f"Evaluation for {name}." for name in names},
        "strengths": ["The response addresses the asked concept."],
        "weaknesses": ["More detail could improve the answer."],
        "missing_concepts": ["error handling"],
        "improvement_suggestions": ["Explain how you would test the approach."],
        "example_areas_to_improve": ["Include a worked example."],
        "answer_evidence_quotes": {"communication_clarity": ["Python uses indentation"]},
    }


@pytest.mark.parametrize("category", ["technical", "project_based", "hr_behavioral", "role_specific"])
def test_generates_all_interview_categories(category, profile, job):
    questions = generate_interview_questions(profile, job, category, "intermediate", 2, llm_service=LLMService())
    assert len(questions) == 2
    assert all(question.interview_type == category for question in questions)
    if category == "project_based":
        assert all(any(ref.profile_path.startswith("projects[") for ref in question.profile_evidence_references) for question in questions)
    elif category == "role_specific":
        assert all(question.relevant_job_requirement in job.required_skills for question in questions)
    elif category == "technical":
        assert all(question.relevant_job_requirement in job.required_skills for question in questions)


@pytest.mark.parametrize("difficulty", ["beginner", "intermediate", "advanced"])
def test_question_generation_supports_each_difficulty(difficulty, profile, job):
    questions = generate_interview_questions(profile, job, "technical", difficulty, 1, llm_service=LLMService())
    assert questions[0].difficulty == difficulty
    assert questions[0].relevant_job_requirement in job.required_skills


def test_project_question_references_only_supported_project_facts(profile, job):
    question = generate_interview_questions(profile, job, "project_based", "beginner", 1, llm_service=LLMService())[0]
    assert question.profile_evidence_references
    assert all(reference.profile_path.startswith("projects[") for reference in question.profile_evidence_references)
    assert "Campus Planner" in question.question_text


def test_project_question_does_not_assume_missing_project(profile, job):
    profile.projects = []
    question = generate_interview_questions(profile, job, "project_based", "intermediate", 1, llm_service=LLMService())[0]
    assert "profile does not include project details" in question.question_text.casefold()
    assert question.profile_evidence_references == []


def test_unsupported_project_claim_from_provider_is_rejected(profile, job):
    draft = _question_draft(interview_type="project_based")
    draft.update(
        question_text="Tell me about the blockchain payment gateway you built.",
        competency="project_architecture",
        relevant_job_requirement=None,
        expected_answer_points=["Explain the blockchain payment gateway architecture"],
        profile_evidence_paths=["projects[0].name"],
    )
    provider = QueueProvider({"questions": [draft]})
    question = generate_interview_questions(
        profile, job, "project_based", "intermediate", 1, llm_service=LLMService(provider)
    )[0]
    assert "blockchain" not in question.question_text.casefold()
    assert "gateway" not in question.question_text.casefold()
    assert question.generation_method == "deterministic_templates"


def test_grounded_project_provider_question_is_accepted(profile, job):
    draft = _question_draft(interview_type="project_based")
    draft.update(
        question_text="For Campus Planner, explain one design decision for the calendar API and a trade-off.",
        competency="project_architecture",
        relevant_job_requirement=None,
        expected_answer_points=["Explain the calendar API goal", "Discuss a design trade-off"],
        profile_evidence_paths=["projects[0].name", "projects[0].description"],
    )
    provider = QueueProvider({"questions": [draft]})
    question = generate_interview_questions(
        profile, job, "project_based", "intermediate", 1, llm_service=LLMService(provider)
    )[0]
    assert question.generation_method == "llm_structured"
    assert question.generation_provider == "mock_interview"
    assert question.profile_evidence_references


def test_relevant_education_can_inform_technical_question(profile, job):
    questions = generate_interview_questions(profile, job, "technical", "beginner", 10, llm_service=LLMService())
    education_question = next(question for question in questions if question.competency == "education_fundamentals")
    assert "Computer Science" in education_question.question_text
    assert any(ref.profile_path == "education[0].branch" for ref in education_question.profile_evidence_references)


def test_llm_question_prompt_excludes_personal_contact_information(profile, job):
    provider = QueueProvider({"questions": [_question_draft()]})
    generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService(provider))
    assert "maya.patel@example.test" not in provider.prompts[0]
    assert "Maya Patel" not in provider.prompts[0]


def test_answer_evaluation_uses_only_relevant_supported_profile_context(profile, job):
    question = generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService())[0]
    provider = QueueProvider(_evaluation_draft())
    evaluate_interview_answer(
        question,
        "Python uses indentation to define blocks.",
        profile,
        job,
        llm_service=LLMService(provider),
    )
    assert "Programming Languages: Python" in provider.prompts[0]
    assert "maya.patel@example.test" not in provider.prompts[0]


def test_question_count_limits_and_unique_variations(profile, job):
    questions = generate_interview_questions(profile, job, "technical", "beginner", 15, llm_service=LLMService())
    assert len(questions) == 15
    assert len({question.question_text.casefold() for question in questions}) == 15
    with pytest.raises(ValidationError):
        generate_interview_questions(profile, job, "technical", "beginner", 0, llm_service=LLMService())
    with pytest.raises(ValidationError):
        generate_interview_questions(profile, job, "technical", "beginner", 31, llm_service=LLMService())


def test_maximum_question_count_remains_distinct(profile, job):
    questions = generate_interview_questions(profile, job, "project_based", "advanced", 30, llm_service=LLMService())
    assert len(questions) == 30
    assert len({question.question_id for question in questions}) == 30


def test_duplicate_provider_questions_are_discarded(profile, job):
    duplicate = _question_draft()
    provider = QueueProvider({"questions": [duplicate, duplicate]})
    questions = generate_interview_questions(profile, job, "technical", "intermediate", 2, llm_service=LLMService(provider))
    assert len({question.question_text for question in questions}) == 2


def test_structured_provider_question_is_used_when_valid(profile, job):
    provider = QueueProvider({"questions": [_question_draft()]})
    question = generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService(provider))[0]
    assert question.generation_method == "llm_structured"
    assert question.generation_provider == "mock_interview"


def test_invalid_question_provider_response_uses_labelled_fallback(profile, job):
    provider = QueueProvider({"questions": [{"unexpected": "shape"}]}, {"questions": [{"unexpected": "shape"}]})
    question = generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService(provider))[0]
    assert question.generation_method == "deterministic_templates"
    assert question.generation_provider == "deterministic_fallback"
    assert provider.calls == 2


def test_answer_key_is_not_in_public_question_json(profile, job):
    question = generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService())[0]
    public_json = question.model_dump_json()
    assert "expected_answer_points" not in public_json
    assert "evaluation_keywords" not in public_json
    with pytest.raises(PermissionError):
        get_question_evaluation_material(question)
    assert get_question_evaluation_material(question, explicitly_requested=True).expected_answer_points


def test_evaluation_uses_mocked_structured_rubric(profile, job):
    question = generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService())[0]
    result = evaluate_interview_answer(question, "Python uses indentation to define blocks.", profile, job, llm_service=LLMService(QueueProvider(_evaluation_draft())))
    assert result.evaluation_method == "llm_rubric"
    assert result.generation_provider == "mock_interview"
    assert result.overall_score == pytest.approx(75)
    assert result.dimension_scores["technical_correctness"].score == 75


def test_fluent_communication_does_not_override_technical_correctness(profile, job):
    question = generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService())[0]
    scores = _evaluation_draft(60)
    scores["dimension_scores"]["technical_correctness"] = 10
    scores["dimension_scores"]["communication_clarity"] = 95
    result = evaluate_interview_answer(question, "Python uses indentation", profile, job, llm_service=LLMService(QueueProvider(scores)))
    assert result.dimension_scores["technical_correctness"].score == 10
    assert result.dimension_scores["communication_clarity"].score == 95
    assert result.overall_score < 70


def test_invalid_llm_evaluation_retries_then_uses_explicit_fallback(profile, job):
    question = generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService())[0]
    provider = QueueProvider({"dimension_scores": {}}, {"dimension_scores": {}})
    result = evaluate_interview_answer(question, "I would start by checking the input and then run a test.", profile, job, llm_service=LLMService(provider))
    assert result.is_fallback
    assert result.evaluation_method == "deterministic_heuristic"
    assert result.generation_provider == "deterministic_fallback"
    assert provider.calls == 2


def test_provider_failure_falls_back_without_claiming_llm(profile, job):
    question = generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService())[0]
    provider = QueueProvider(LLMProviderError("offline"), LLMProviderError("offline"))
    result = evaluate_interview_answer(question, "I would inspect the input, then test the endpoint.", profile, job, llm_service=LLMService(provider))
    assert result.is_fallback
    assert result.dimension_scores["technical_correctness"].status == "not_assessed"


def test_missing_api_credentials_use_deterministic_evaluation(profile, job, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    question = generate_interview_questions(profile, job, "technical", "beginner", 1, llm_service=LLMService())[0]
    result = evaluate_interview_answer(question, "A brief answer with one example.", profile, job)
    assert result.is_fallback
    assert result.confidence == "low"
    assert result.score_coverage < 1


def test_empty_answer_is_unscored_and_graceful(profile, job):
    question = generate_interview_questions(profile, job, "technical", "beginner", 1, llm_service=LLMService())[0]
    result = evaluate_interview_answer(question, "  ", profile, job, llm_service=LLMService())
    assert result.overall_score is None
    assert result.score_coverage == 0
    assert all(item.status == "not_assessed" for item in result.dimension_scores.values())


def test_dimension_and_total_scores_are_validated(profile, job):
    question = generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService())[0]
    result = evaluate_interview_answer(question, "Python uses indentation to define code blocks.", profile, job, llm_service=LLMService(QueueProvider(_evaluation_draft(70))))
    assert 0 <= result.overall_score <= 100
    invalid = result.model_dump()
    invalid["overall_score"] = 2
    with pytest.raises(ValidationError):
        AnswerEvaluation.model_validate(invalid)


def test_rubric_weights_are_configurable_and_validated():
    weights = default_rubric_weights("technical").model_dump()
    weights["communication_clarity"] += 0.05
    with pytest.raises(ValidationError):
        RubricWeights.model_validate(weights)
    weights = default_rubric_weights("technical").model_dump()
    weights["communication_clarity"] += 0.05
    weights["technical_correctness"] -= 0.05
    validated = RubricWeights.model_validate(weights)
    assert sum(validated.model_dump().values()) == pytest.approx(1)


def test_llm_evidence_quotes_must_be_exact_answer_substrings(profile, job):
    question = generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService())[0]
    draft = _evaluation_draft()
    draft["answer_evidence_quotes"] = {"communication_clarity": ["invented quote"]}
    result = evaluate_interview_answer(question, "The actual response gives a clear concept.", profile, job, llm_service=LLMService(QueueProvider(draft)))
    assert result.dimension_scores["communication_clarity"].answer_evidence == []


def test_deterministic_evaluator_is_low_confidence_and_discloses_limits(profile, job):
    question = generate_interview_questions(profile, job, "technical", "intermediate", 1, llm_service=LLMService())[0]
    result = evaluate_interview_answer(question, "I would first inspect the input and then test it.", profile, job, llm_service=LLMService())
    assert result.confidence == "low"
    assert any("not assessed" in item.casefold() for item in result.limitations)


def test_adaptive_follow_up_reinforces_one_weak_competency(profile, job):
    session = start_interview(profile, job, "technical", "intermediate", 4, llm_service=LLMService())
    first_competency = session.question_history[-1].competency
    session = submit_interview_answer(session, "I don't know.", llm_service=LLMService())
    assert session.question_history[-1].competency == first_competency
    assert session.current_difficulty == "beginner"
    assert session.focus_reinforcement_used is True


def test_engine_moves_on_after_one_repeated_weak_answer(profile, job):
    session = start_interview(profile, job, "technical", "intermediate", 4, llm_service=LLMService())
    first_competency = session.question_history[-1].competency
    session = submit_interview_answer(session, "I don't know.", llm_service=LLMService())
    session = submit_interview_answer(session, "I still do not know.", llm_service=LLMService())
    assert session.question_history[-1].competency != first_competency
    assert first_competency in session.repeated_weaknesses


def test_adaptive_selection_exposes_reason_and_reinforcement_flag(profile, job):
    session = start_interview(profile, job, "technical", "intermediate", 3, llm_service=LLMService())
    session = submit_interview_answer(session, "I don't know.", llm_service=LLMService())
    selection = select_next_question(session, llm_service=LLMService())
    assert selection is not None
    assert selection.selection_reason
    assert selection.reinforcement is False  # the session already contains the pending follow-up


def test_strong_answer_increases_difficulty(profile, job):
    provider = LLMService(RubricProvider(90))
    session = start_interview(profile, job, "technical", "beginner", 2, llm_service=provider)
    session = submit_interview_answer(session, "Python uses indentation to define blocks and I would test the API.", llm_service=provider)
    assert session.current_difficulty == "intermediate"


def test_competency_metrics_track_attempts_scores_and_trend(profile, job):
    provider = LLMService(RubricProvider(90))
    session = start_interview(profile, job, "technical", "intermediate", 1, llm_service=provider)
    competency = session.question_history[-1].competency
    session = submit_interview_answer(session, "Python uses indentation to define blocks.", llm_service=provider)
    metric = session.competency_performance[competency]
    assert metric.questions_attempted == 1
    assert metric.average_score == 90
    assert metric.confidence == "low"  # one answer is not enough to raise assessment confidence


def test_empty_answer_records_unscored_competency_attempt(profile, job):
    session = start_interview(profile, job, "technical", "beginner", 2, llm_service=LLMService())
    competency = session.question_history[-1].competency
    session = submit_interview_answer(session, "", llm_service=LLMService())
    metric = session.competency_performance[competency]
    assert metric.questions_attempted == 1
    assert metric.unscored_attempts == 1
    assert metric.average_score is None


def test_session_creation_has_first_question_and_pending_state(profile, job):
    session = start_interview(profile, job, "role_specific", "advanced", 2, llm_service=LLMService())
    assert session.status == "in_progress"
    assert session.current_question_index == 0
    assert len(session.question_history) == 1
    assert session.turn_history == []


def test_answer_submission_creates_turn_and_selects_next(profile, job):
    session = start_interview(profile, job, "technical", "intermediate", 2, llm_service=LLMService())
    session = submit_interview_answer(session, "Python uses indentation and I would validate the input.", llm_service=LLMService())
    assert len(session.turn_history) == len(session.answer_history) == len(session.evaluation_history) == 1
    assert len(session.question_history) == 2
    assert session.turn_history[0].selection_reason


def test_interview_completes_after_planned_answer_count(profile, job):
    session = start_interview(profile, job, "technical", "intermediate", 1, llm_service=LLMService())
    session = submit_interview_answer(session, "A complete answer with reasoning and testing.", llm_service=LLMService())
    assert session.status == "completed"
    assert len(session.question_history) == len(session.turn_history) == 1
    with pytest.raises(ValueError):
        submit_interview_answer(session, "late answer", llm_service=LLMService())


def test_report_summarizes_completed_interview_without_hiring_claim(profile, job):
    provider = LLMService(RubricProvider(82))
    session = start_interview(profile, job, "technical", "intermediate", 1, llm_service=provider)
    session = submit_interview_answer(session, "Python uses indentation to define blocks.", llm_service=provider)
    report = get_interview_report(session)
    assert report.session_status == "completed"
    assert report.overall_score == pytest.approx(82)
    assert report.questions_completed == 1
    assert any("not a hiring decision" in item for item in report.readiness_observations)


def test_report_for_incomplete_session_notes_incompleteness(profile, job):
    session = start_interview(profile, job, "hr_behavioral", "beginner", 3, llm_service=LLMService())
    report = get_interview_report(session)
    assert report.session_status == "in_progress"
    assert report.overall_score is None
    assert any("incomplete" in item.casefold() for item in report.readiness_observations)


def test_provider_failure_generation_falls_back_without_fake_llm_claim(profile, job):
    provider = QueueProvider(LLMProviderError("offline"), LLMProviderError("offline"))
    question = generate_interview_questions(profile, job, "technical", "beginner", 1, llm_service=LLMService(provider))[0]
    assert question.generation_method == "deterministic_templates"
    assert question.generation_provider == "deterministic_fallback"


def test_session_serialization_hides_and_optionally_preserves_internal_material(profile, job):
    session = start_interview(profile, job, "technical", "intermediate", 1, llm_service=LLMService())
    public_payload = json.loads(serialize_interview_session(session))
    assert "expected_answer_points" not in public_payload["question_history"][0]
    internal_payload = serialize_interview_session(session, include_evaluation_material=True)
    restored = InterviewSession.model_validate_json(internal_payload)
    assert restored.question_history[0].expected_answer_points
    assert restored.question_history[0].evaluation_rubric.weights.technical_correctness > 0


def test_no_experience_does_not_turn_hr_questions_into_claims(profile, job):
    profile.experience = []
    question = generate_interview_questions(profile, job, "hr_behavioral", "intermediate", 1, llm_service=LLMService())[0]
    assert "if you" in question.question_text.casefold() or "how would" in question.question_text.casefold()


def test_missing_profile_evidence_does_not_block_interview(profile, job):
    profile.skills = SkillProfile()
    profile.projects = []
    session = start_interview(profile, job, "technical", "beginner", 1, llm_service=LLMService())
    assert session.question_history[0].profile_evidence_references == []
    assert "Python" in session.question_history[0].question_text


def test_early_termination_keeps_completed_turns(profile, job):
    session = start_interview(profile, job, "technical", "intermediate", 4, llm_service=LLMService())
    session = submit_interview_answer(session, "A short explanation.", llm_service=LLMService())
    terminated = end_interview(session, "student ended early")
    assert terminated.status == "terminated"
    assert terminated.termination_reason == "student ended early"
    assert len(terminated.turn_history) == 1
    assert get_interview_report(terminated).session_status == "terminated"


def test_invalid_answer_type_and_length_are_rejected(profile, job):
    session = start_interview(profile, job, "technical", "beginner", 1, llm_service=LLMService())
    with pytest.raises(ValidationError):
        submit_interview_answer(session, "x" * 12001, llm_service=LLMService())
    with pytest.raises(ValidationError):
        submit_interview_answer(session, None, llm_service=LLMService())  # type: ignore[arg-type]


def test_session_validation_catches_mismatched_job_match(profile, job):
    from app.ai.job_matching.schemas import EligibilityAssessment, JobMatch

    wrong_match = JobMatch(
        job_id="another-job",
        rank=1,
        score_coverage=0,
        dimension_scores={},
        eligibility_assessment=EligibilityAssessment(status="unknown"),
        explanation="fixture",
        matching_method="keyword_fallback",
        confidence="low",
    )
    with pytest.raises(ValidationError):
        start_interview(profile, job, "technical", "beginner", 1, job_match=wrong_match, llm_service=LLMService())
