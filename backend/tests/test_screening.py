from __future__ import annotations

from uuid import uuid4

import pytest

from app.agents.graph import PIPELINE, PipelineError, replace_node, run_pipeline
from app.agents.state import ScreeningState
from app.services.ats_engine import (
    EXPECTED_SECTION_COUNT,
    REVIEW_THRESHOLD,
    STRONG_MATCH_THRESHOLD,
    WEIGHT_COMPLETENESS,
    WEIGHT_EXPERIENCE,
    WEIGHT_KEYWORD,
    WEIGHT_SEMANTIC,
    _contains_skill as contains_skill,
    calculate_ats,
    extract_experience_years,
    recommend,
)
from app.services.bias_check import assess, detect_protected_attributes
from app.services.pii_redaction import extract_sections, redact_resume

# Synthetic throughout. Real candidate data has no place in a test fixture.
RESUME = """Priya Raghavan
priya.raghavan@example.com | +91 98765 43210
github.com/priya-raghavan/redis-cache-layer
14 Brigade Road, Bengaluru

Professional Summary
Backend engineer with 7 years of professional experience.

Skills
Python, FastAPI, PostgreSQL, Redis, Docker

Experience
Senior Backend Engineer, Acme Logistics
Built event-driven services handling 40k requests per second.

Projects
Redis-backed Caching layer

Education
B.Tech, Computer Science
"""

JOB_DESCRIPTION = """Hiring a senior backend engineer to build high-throughput
Python services using FastAPI, PostgreSQL and Redis, deployed with Docker.
"""


def build_state(**overrides: object) -> ScreeningState:
    defaults: dict[str, object] = {
        "application_id": uuid4(),
        "organization_id": uuid4(),
        "job_id": uuid4(),
        "candidate_id": uuid4(),
        "raw_resume_text": RESUME,
        "job_description": JOB_DESCRIPTION,
        "job_title": "Senior Backend Engineer",
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "preferred_skills": ["Redis", "Docker"],
        "min_experience_years": 5,
        "known_names": ("Priya Raghavan",),
    }
    defaults.update(overrides)
    return ScreeningState(**defaults)  # type: ignore[arg-type]


# ------------------------------------------------------------------
# Skill matching
# ------------------------------------------------------------------


class TestSkillMatching:
    @pytest.mark.parametrize(
        ("text", "skill"),
        [
            ("Built dashboards in React", "React"),
            ("Statistical modelling in R, plus Python", "R"),
            ("Core services in C++", "C++"),
            ("Backend in C# with .NET 8", "C#"),
            ("Node.js microservices", "NodeJS"),
            ("Deep experience with Postgres", "PostgreSQL"),  # alias
            ("Shipped k8s operators", "Kubernetes"),  # alias
        ],
    )
    def test_genuine_matches(self, text: str, skill: str) -> None:
        assert contains_skill(text, skill) is True

    # The regression: a single letter matching inside a longer word.
    @pytest.mark.parametrize(
        ("text", "skill"),
        [
            ("Built dashboards in React and Redux", "R"),
            ("Deployed on Google Cloud Platform", "Go"),
            ("Wrote Java services", "Javascript"),
            ("Experience with Postgres", "Mongo"),
        ],
    )
    def test_substring_false_positives_rejected(self, text: str, skill: str) -> None:
        assert contains_skill(text, skill) is False

    def test_blank_inputs_never_match(self) -> None:
        assert contains_skill("Python developer", "") is False
        assert contains_skill("", "Python") is False


# ------------------------------------------------------------------
# Experience extraction
# ------------------------------------------------------------------


class TestExperienceExtraction:
    def test_explicit_self_description(self) -> None:
        assert (
            extract_experience_years("7 years of professional experience") == 7.0
        )

    def test_plus_notation(self) -> None:
        assert (
            extract_experience_years("8+ years in experience in backend") == 8.0
        )

    def test_company_history_is_not_candidate_experience(self) -> None:
        """The regression years belong to an employer, not the person."""
        assert (
            extract_experience_years(
                "Joined a company with 20 years of history in logistics."
            )
            == 0.0
        )

    def test_candidate_years_win_over_company_years(self) -> None:
        text = """
        The organization has 40 years of history.
        I bring 8 years of professional experience in data engineering.
        """
        assert extract_experience_years(text) == 8.0

    def test_bare_years_only_inside_experience_section(self) -> None:
        assert (
            extract_experience_years(
                "4 years building APIs", {"experience": "4 years building APIs"}
            )
            == 4.0
        )
        assert (
            extract_experience_years("Studied over 3 years", {"education": ""})
            == 0.0
        )

    def test_implausible_values_rejected(self) -> None:
        """Mangled PDF text yields things like "2015 years"."""
        assert (
            extract_experience_years("2015 of 2015 years of experience") == 0.0
        )


# ------------------------------------------------------------------
# Scoring
# ------------------------------------------------------------------


class TestScoring:
    def test_all_required_skills_matched(self) -> None:
        result = calculate_ats(
            "Python FastAPI PostgreSQL, 3 years of professional experience",
            ["Python", "FastAPI"],
            ["React"],
            min_experience_years=3,
            section_count=5,
        )
        assert result.missing_required == []
        assert result.keyword_score == 100
        assert result.detected_experience_years == 3.0

    def test_missing_required_skill_blocks_strong_match(self) -> None:
        """A perfect score elsewhere must not overcome a missing requirement."""
        result = calculate_ats(
            "Python expert, 20 years of professional experience",
            ["Python", "Haskell"],
            [],
            min_experience_years=3,
            section_count=5,
            semantic_score=100.0,
        )
        assert result.missing_required == ["Haskell"]
        assert result.recommendation != "STRONG_MATCH"

    def test_semantic_score_is_an_input_not_an_override(self) -> None:
        result = calculate_ats("Python", ["Python"], [], 3, 5, semantic_score=42.5)
        assert result.semantic_score == 42.5

    def test_missing_semantic_falls_back_to_keyword_scale(self) -> None:
        """A zero score must not silently depress the overall score."""
        result = calculate_ats("Python", ["Python"], [], 3, 5, semantic_score=0.0)
        assert result.semantic_score == result.keyword_score

    def test_duplicate_skills_counted_once(self) -> None:
        result = calculate_ats(
            "Python developer", ["Python", "Python", "PYTHON"], [], None, 5
        )
        assert result.matched_required == ["Python"]

    def test_scores_stay_within_bounds(self) -> None:
        result = calculate_ats(
            "Python, 20 years of professional experience",
            ["Python"],
            ["Redis"],
            min_experience_years=3,
            section_count=5,
            semantic_score=100.0,
        )
        for value in (
            result.keyword_score,
            result.semantic_score,
            result.experience_score,
            result.completeness_score,
            result.overall_score,
        ):
            assert 0.0 <= value <= 100.0

    def test_concerns_cite_their_evidence(self) -> None:
        result = calculate_ats("Python", ["Python", "Kafka"], [], None, 5)
        assert any("Kafka" in concern for concern in result.concerns)

    def test_weights_sum_to_one(self) -> None:
        total = (
            WEIGHT_KEYWORD + WEIGHT_SEMANTIC + WEIGHT_EXPERIENCE + WEIGHT_COMPLETENESS
        )
        assert total == pytest.approx(1.0)

    def test_recommendation_bands(self) -> None:
        assert recommend(85.0, []) == "STRONG_MATCH"
        assert recommend(85.0, ["missing"]) != "STRONG_MATCH"
        assert recommend(70.0, []) == "REVIEW"
        assert recommend(50.0, []) == "LOW_MATCH"

    def test_scorer_is_deterministic(self) -> None:
        """The scoring pass must not call an LLM or depend on anything stochastic."""
        args = ("Python 5 years of professional experience", ["Python"], ["Go"], 3, 4)
        a = calculate_ats(*args, semantic_score=0.0)
        b = calculate_ats(*args, semantic_score=0.0)
        assert a == b
        assert a.overall_score == b.overall_score


# ------------------------------------------------------------------
# PII redaction
# ------------------------------------------------------------------


class TestPiiRedaction:
    def test_contact_details_removed_from_both_views(self) -> None:
        result = redact_resume(RESUME, known_names=("Priya Raghavan",))
        for view in (result.scoring_text, result.llm_text):
            assert "priya.raghavan@example.com" not in view
            assert "98765 43210" not in view

    def test_name_removed_from_llm_view(self) -> None:
        """The most serious original defect: names reached the LLM verbatim."""
        result = redact_resume(RESUME, known_names=("Priya Raghavan",))
        assert "Priya" not in result.llm_text
        assert "Raghavan" not in result.llm_text
        assert "[NAME_REDACTED]" in result.llm_text

    def test_name_tokens_removed_throughout_the_document(self) -> None:
        text = "Priya Raghavan<priya@example.com>\nPriya led the migration."
        result = redact_resume(text, known_names=("Priya Raghavan",))
        assert "Priya" not in result.llm_text

    def test_bare_url_path_removed_but_host_kept(self) -> None:
        """github.com/user/repo has no scheme, so the old pattern missed it and
        the username survived redaction entirely."""
        result = redact_resume(RESUME, known_names=("Priya Raghavan",))
        assert "github.com/" in result.llm_text
        assert "redis-cache-layer" not in result.llm_text

    def test_scoring_view_keeps_urls_and_name(self) -> None:
        """Scoring in local: stripping URLs would discard real skill evidence,
        and keeping the name is what makes the fairness check measurable."""
        result = redact_resume(RESUME, known_names=("Priya Raghavan",))
        assert "github.com/priya-raghavan/redis-cache-layer" in result.scoring_text
        assert "redis-cache-layer" in result.scoring_text
        assert "Priya" in result.scoring_text

    def test_address_removed_from_llm_view(self) -> None:
        result = redact_resume(RESUME, known_names=("Priya Raghavan",))
        assert "Brigade Road" not in result.llm_text

    def test_counterfactual_view_differs_only_by_name(self) -> None:
        result = redact_resume(RESUME, known_names=("Priya Raghavan",))
        assert "Priya" in result.scoring_text
        assert "Priya" not in result.name_redacted_scoring_text
        assert "Python" in result.name_redacted_scoring_text

    def test_report_counts_only_no_values(self) -> None:
        """The audit record must not recreate the exposure it documents."""
        report = redact_resume(RESUME, known_names=("Priya Raghavan",)).report
        assert report.total > 0
        assert all(isinstance(v, int) for v in report.as_dict().values())
        assert "priya" not in str(report.as_dict())

    def test_short_tokens_are_not_redacted(self) -> None:
        """Redacting "of" or "Dr" would shred the document."""
        result = redact_resume("Dr. Priya Raghavan, Head of Engineering", known_names=("Priya Raghavan",))
        assert "of" in result.llm_text

    def test_sections_detected(self) -> None:
        sections = extract_sections(RESUME)
        assert {"summary", "skills", "experience", "education"} <= set(sections)
        assert "WORK EXPERIENCE" not in sections  # normalized

    def test_empty_inputs(self) -> None:
        result = redact_resume("", known_names=())
        assert result.scoring_text == ""
        assert result.llm_text == ""


# ------------------------------------------------------------------
# Fairness
# ------------------------------------------------------------------


class TestFairness:
    def test_protected_attributes_detected_by_category(self) -> None:
        assert "gender" in detect_protected_attributes("Gender: Female")
        assert "age" in detect_protected_attributes("Date of Birth: 1990-01-01")

    def test_word_boundaries_respected(self) -> None:
        """'manage' contains 'age' but discloses nothing."""
        assert "age" not in detect_protected_attributes("managed a team")

    def test_name_sensitivity_scorer_is_caught(self) -> None:
        """The check that must be able to fail."""

        def biased_scorer(text: str) -> float:
            # Score depends on whether name is present.
            return 85.0 if "Priya" in text else 70.0

        assessment = assess(
            scoring_text="Priya\nPython",
            name_redacted_text="Python",
            score_fn=biased_scorer,
        )
        assert assessment.name_signal_detected is True
        assert assessment.review_required is True
        assert any("name" in flag.lower() for flag in assessment.flags)

    def test_insensitive_scorer_passes(self) -> None:
        result = assess(
            scoring_text="Priya\nPython",
            name_redacted_text="Python",
            score_fn=lambda text: 75.0,
            explanation="Strong Python evidence.",
        )
        assert result.name_sensitivity_delta == 0.0
        assert result.review_required is False
        assert result.flags == []

    def test_disclosure_alone_flags_but_does_not_escalate(self) -> None:
        """Resumes in many regions routinely disclose these; that is not
        misconduct by the system, so it is recorded rather than escalated."""
        result = assess(
            scoring_text="Gender: Female\nPython",
            name_redacted_text="Gender: Female\nPython",
            score_fn=lambda text: 80.0,
        )
        assert result.protected_attributes_present == ["gender"]
        assert result.flags != []
        assert result.review_required is False

    def test_protected_reference_in_explanation_escalates(self) -> None:
        result = assess(
            scoring_text="Python",
            name_redacted_text="Python",
            score_fn=lambda text: 80.0,
            explanation="Her age makes her a good fit.",
        )
        assert result.review_required is True

    def test_scorer_failure_does_not_break_the_audit(self) -> None:
        def failing_scorer(text: str) -> float:
            raise RuntimeError("boom")

        result = assess(
            scoring_text="Python",
            name_redacted_text="Python",
            score_fn=failing_scorer,
        )
        assert result.name_sensitivity_delta == 0.0


# ------------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------------


def explode_state(state: ScreeningState) -> ScreeningState:
    raise RuntimeError("Node exploded")


class TestPipeline:
    def test_produces_a_complete_result(self) -> None:
        state = run_pipeline(build_state())

        assert state.ats is not None
        assert 0.0 <= state.ats.overall_score <= 100.0
        assert state.ats.missing_required == []
        assert state.explanation, "every result must carry an explanation"
        assert state.improvement_suggestions
        assert state.provider == "deterministic"

    def test_every_node_runs_and_none_fails(self) -> None:
        state = run_pipeline(build_state())
        assert [n.name for n in state.nodes_executed] == [n.name for n in PIPELINE]
        assert state.errors == []

    def test_falls_back_to_deterministic_without_a_provider(self) -> None:
        state = run_pipeline(build_state())
        assert state.ats is not None
        assert state.provider == "deterministic"
        assert state.explanation

    def test_pii_never_reaches_the_llm_view(self) -> None:
        """The structural guarantee of the node ordering."""
        state = run_pipeline(build_state())
        assert "priya.raghavan@example.com" not in state.llm_text
        assert "https" not in state.llm_text
        assert "98765 43210" not in state.llm_text

    def test_deterministic_scorer_shows_no_name_sensitivity(self) -> None:
        state = run_pipeline(build_state())
        assert state.bias is not None
        assert state.bias.name_sensitivity_delta == 0.0
        assert state.bias.review_required is False

    def test_protected_attribute_disclosure_surfaces_as_a_concern(self) -> None:
        state = run_pipeline(
            build_state(raw_resume_text=RESUME + "\nGender: Female\n")
        )
        assert state.bias is not None
        assert "gender" in state.bias.protected_attributes_present
        assert any("protected attribute" in c.lower() for c in state.concerns)

    def test_empty_resume_still_scores_and_explains(self) -> None:
        """An unparseable resume must not 500."""
        state = run_pipeline(build_state(raw_resume_text=""))
        assert state.ats is not None
        assert state.ats.missing_required == ["Python", "FastAPI", "PostgreSQL"]
        assert state.explanation

    def test_advisory_node_failure_does_not_abort(self) -> None:
        """An LLM outage must degrade the result, not fail it."""
        with pytest.raises(PipelineError, match="scorer"):
            run_pipeline(build_state(), replace_node("scorer", explode_state))

    def test_critical_node_failure_aborts(self) -> None:
        """An unparseable resume must not 500."""
        with pytest.raises(PipelineError, match="redactor"):
            run_pipeline(build_state(), replace_node("redactor", explode_state))

    def test_redaction_precedes_every_text_consumer(self) -> None:
        order = [node.name for node in PIPELINE]
        for consumer in ("matcher", "scorer", "feedback", "bias_check"):
            assert order.index(consumer) > order.index("redaction")

    def test_feedback_precedes_bias_check(self) -> None:
        """The fairness pass must be able to inspect the generated explanation."""
        order = [node.name for node in PIPELINE]
        assert order.index("bias_check") > order.index("feedback")

    def test_audit_payload_contains_no_raw_resume_text(self) -> None:
        """Writing an audit row must never itself become a disclosure."""
        payload = run_pipeline(build_state()).audit_payload()
        assert "raw_resume_text" not in payload
        assert "priya.raghavan@example.com" not in payload
        assert "Acme" not in payload

    def test_audit_payload_records_scores_and_provenance(self) -> None:
        payload = run_pipeline(build_state()).audit_payload()
        assert "scores" in payload
        assert "fairness" in payload
        assert "redactions" in payload
        assert payload["provider"] == "deterministic"