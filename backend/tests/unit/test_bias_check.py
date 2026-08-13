from app.services.bias_check import inspect_text

def test_bias_checker_does_not_block_screening():
    result = inspect_text("Skills: Python\nAge: 24")
    assert result.safe_for_screening is True
    assert result.flags
