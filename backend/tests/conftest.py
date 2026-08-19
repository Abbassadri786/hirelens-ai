"""Global test configuration and fixtures.

Importing 'app.core.config' builds 'Settings' at module scope and
'app.db.session' builds the engine from it, so setting any envlet arrives too
late.

SQLite is used for the engine URL purely so the engine can be constructed
without a PostgreSQL driver. No test issues SQL - the models use JSONB and
native enums that SQLite cannot represent faithfully, so the suite covers logic
and HTTP behaviour rather than persistence.
"""

from __future__ import annotations

import os

for key, value in {
    "ENVIRONMENT": "test",
    "DEBUG": "false",
    "LOG_LEVEL": "WARNING",
    "DATABASE_URL": "sqlite+pysqlite:///:memory:",
    "JWT_SECRET_KEY": "replace_with_at_least_32_random_characters-32-chars",
    "FRONTEND_ORIGIN": "http://localhost:3000",
    # Deterministic AI behaviour: nothing configured, so the pipeline exercises
    # its fallback path instead of making network calls.
    "GEMINI_API_KEY": "",
    "GROQ_API_KEY": "",
    "OLLAMA_ENABLED": "false",
    "EMBEDDINGS_ENABLED": "false",
    "RATE_LIMIT_ENABLED": "true",
    "PII_REDACT_NAMES": "true",
}.items():
    os.environ[key] = value

import pytest # noqa: E402 - must follow the environment setup above

from app.core.rate_limit import ALL_LIMITERS # noqa: E402


@pytest.fixture(autouse=True)
def _reset_rate_limiters() -> None:
    """Clear rate-limit buckets between tests.

    The limiters are module-level singletons, so without this a test that
    exhausts a limit would leak 429s into every test after it.
    """
    for limiter in ALL_LIMITERS:
        limiter.reset()