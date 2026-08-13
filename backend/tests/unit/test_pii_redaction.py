from app.services.pii_redaction import redact_pii

def test_email_and_phone_are_redacted():
    text = "John Doe john@example.com +91 98765 43210"
    redacted = redact_pii(text)
    assert "john@example.com" not in redacted
    assert "98765 43210" not in redacted
    assert "[EMAIL_REDACTED]" in redacted
