from app.services.ats_engine import calculate_ats

def test_required_skill_match():
    result = calculate_ats(
        "Python FastAPI PostgreSQL 3 years experience\nEducation",
        ["Python", "FastAPI"],
        ["React"],
        2,
        3,
    )
    assert result.keyword_score >= 80
    assert result.missing_required == []
    assert result.experience_score == 100

def test_missing_required_skill():
    result = calculate_ats(
        "Python developer with 1 years experience\nSkills\nEducation",
        ["Python", "Java"],
        [],
        2,
        2,
    )
    assert "Java" in result.missing_required
    assert result.recommendation in {"REVIEW", "LOW_MATCH"}
