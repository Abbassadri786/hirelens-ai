from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.agents.llm_router import (
    AllProvidersFailed,
    LLMConfigurationError,
    LLMProvider,
    LLMResponse,
    LLMRouter,
    LLMTransientError,
)
from app.core.config import PLACEHOLDER_JWT_SECRET, Settings
from app.core.rate_limit import RateLimiter
from app.core.security import (
    TokenError,
    constant_time_compare,
    create_access_token,
    create_refresh_token,
    create_token,
    decode_token,
    dummy_password_hash,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.main import app

API = "/api/v1"


@pytest.fixture
def client() -> TestClient:
    """Surfaces server errors as 500 responses instead of re-raising them.

    Handlers that reach the database will fail here; these tests assert on
    middleware and dependencies that run before the handler.
    """
    return TestClient(app, raise_server_exceptions=False)


def client_with(**cookies: str) -> TestClient:
    """Client with cookies set on the instance (https deprecates per-request)."""
    instance = TestClient(app, raise_server_exceptions=False)
    for name, value in cookies.items():
        instance.cookies.set(name, value)
    return instance


# ------------------------------------------------------------------
# Passwords and tokens
# ------------------------------------------------------------------


class TestPasswords:
    def test_hash_then_verify(self) -> None:
        hashed = hash_password("correct horse battery staple")
        assert verify_password("correct horse battery staple", hashed) is True
        assert verify_password("wrong password entirely", hashed) is False

    def test_hash_is_salted_and_opaque(self) -> None:
        assert hash_password("same input") != hash_password("same input")
        assert "battery staple" not in hash_password("battery staple")

    def test_malformed_stored_hash_is_a_failure_not_a_crash(self) -> None:
        assert verify_password("anything", "not-a-valid-hash") is False

    def test_dummy_hash_is_cached_and_unmatched(self) -> None:
        """Used to equalize login timing on the "no such user" branch."""
        assert dummy_password_hash() == dummy_password_hash()
        assert verify_password("some guess", dummy_password_hash()) is False


class TestTokens:
    def test_access_token_round_trip(self) -> None:
        user_id, org_id = uuid4(), uuid4()
        claims = decode_token(
            create_access_token(
                user_id=user_id, organization_id=org_id, role="RECRUITER"
            ),
            expected_type="access",
        )
        assert claims.user_id == user_id
        assert claims.organization_id == org_id
        assert claims.role == "RECRUITER"

    def test_refresh_token_rejected_where_access_expected(self) -> None:
        """Token-type confusion must not grant API access."""
        with pytest.raises(TokenError):
            decode_token(
                create_refresh_token(user_id=uuid4()), expected_type="access"
            )

    def test_expired_token_rejected(self) -> None:
        expired = create_token(
            user_id=uuid4(),
            token_type="access",
            expires_delta=timedelta(seconds=-30),
            organization_id=uuid4(),
            role="RECRUITER",
        )
        with pytest.raises(TokenError):
            decode_token(expired, expected_type="access")

    def test_tampered_and_garbage_tokens_rejected(self) -> None:
        token = create_access_token(
            user_id=uuid4(), organization_id=uuid4(), role="RECRUITER"
        )
        header, payload, _sig = token.split(".")
        for bad in ("not.a.jwt", f"{header}.{payload}.deadbeef"):
            with pytest.raises(TokenError):
                decode_token(bad, expected_type="access")

    def test_token_signed_with_another_secret_rejected(self) -> None:
        import jwt

        forged = jwt.encode(
            {
                "sub": str(uuid4()),
                "type": "access",
                "aud": "hirelens:access",
                "iss": "hirelens",
                "iat": 1_700_000_000,
                "nbf": 1_700_000_000,
                "exp": 1_800_000_000,
                "jti": "abc",
            },
            "an-entirely-different-secret-key-value",
            algorithm="HS256",
        )
        with pytest.raises(TokenError):
            decode_token(forged, expected_type="access")

    def test_refresh_tokens_are_stored_only_as_hashes(self) -> None:
        token = create_refresh_token(user_id=uuid4())
        digest = hash_refresh_token(token)
        assert digest != token
        assert len(digest) == 64
        assert digest == hash_refresh_token(token)


class TestConstantTimeCompare:
    def test_equal_and_unequal(self) -> None:
        assert constant_time_compare("token", "token") is True
        assert constant_time_compare("token", "other") is False

    @pytest.mark.parametrize(
        ("left", "right"), [("a", None), (None, "b"), (None, None), ("", "")]
    )
    def test_missing_values_never_equal(
        self, left: str | None, right: str | None
    ) -> None:
        """A missing CSRF cookie and missing header must not compare equal."""
        assert constant_time_compare(left, right) is False


# ------------------------------------------------------------------
# HTTP surface
# ------------------------------------------------------------------


class TestHealthAndHeaders:
    def test_health_is_public(self, client: TestClient) -> None:
        response = client.get(f"{API}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_security_headers_present(self, client: TestClient) -> None:
        headers = client.get(f"{API}/health").headers
        assert headers["Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_api_responses_are_not_cacheable(self, client: TestClient) -> None:
        """Screening results are candidate data; intermediaries must not store it."""
        assert client.get(f"{API}/health").headers["Cache-Control"] == "no-store"

    def test_hsts_absent_outside_production(self, client: TestClient) -> None:
        assert "Strict-Transport-Security" not in client.get(f"{API}/health").headers


class TestAuthenticationBoundary:
    @pytest.mark.parametrize(
        "path",
        [
            f"{API}/auth/me",
            f"{API}/organizations/me",
            f"{API}/jobs",
            f"{API}/applications",
            f"{API}/screening",
            f"{API}/screening/pipeline-status",
            f"{API}/analytics/fairness",
            f"{API}/audit",
        ],
    )
    def test_unauthenticated_requests_rejected(
        self, client: TestClient, path: str
    ) -> None:
        assert client.get(path).status_code == 401

    def test_invalid_token_rejected(self) -> None:
        client = client_with(hirelens_access="not-a-jwt")
        assert client.get(f"{API}/auth/me").status_code == 401

    def test_refresh_token_rejected_as_access_token(self) -> None:
        client = client_with(
            hirelens_access=create_refresh_token(user_id=uuid4())
        )
        assert client.get(f"{API}/auth/me").status_code == 401


class TestCsrf:
    def test_csrf_endpoint_issues_a_readable_cookie(self, client: TestClient) -> None:
        response = client.get(f"{API}/auth/csrf")
        assert response.status_code == 200
        assert "hirelens_csrf" in response.cookies

    def test_mismatched_token_rejected(self) -> None:
        client = client_with(hirelens_csrf="cookie-value")
        response = client.post(
            f"{API}/auth/refresh", headers={"X-CSRF-Token": "different-value"}
        )
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]

    def test_missing_header_rejected(self) -> None:
        client = client_with(hirelens_csrf="cookie-value")
        response = client.post(f"{API}/auth/refresh")
        assert response.status_code == 403

    def test_matching_token_passes_the_check(self) -> None:
        """Passes CSRF, then fails on the missing refresh cookie -- 401 not 403."""
        client = client_with(hirelens_csrf="cookie-value")
        response = client.post(
            f"{API}/auth/refresh", headers={"X-CSRF-Token": "cookie-value"}
        )
        assert response.status_code == 401


class TestRateLimiting:
    def test_login_becomes_rate_limited(self, client: TestClient) -> None:
        """The original code had no rate limiting at all on this endpoint."""
        from app.core.config import settings

        statuses = [
            client.post(
                f"{API}/auth/login",
                json={"email": "nobody@example.com", "password": "guess-attempt"},
            ).status_code
            for _ in range(settings.RATE_LIMIT_AUTH_PER_MINUTE + 3)
        ]
        assert 429 in statuses

    def test_limiter_window_and_key_isolation(self) -> None:
        limiter = RateLimiter(limit=2, window_seconds=60)
        assert limiter.allow("a") is True
        assert limiter.allow("a") is True
        assert limiter.allow("a") is False
        # One caller exhausting its allowance must not affect another.
        assert limiter.allow("b") is True

    def test_limiter_window_expiry(self) -> None:
        limiter = RateLimiter(limit=1, window_seconds=0)
        assert limiter.allow("a") is True
        # Age the recorded hit past the window rather than sleeping.
        limiter._hits["a"][0] -= 1
        assert limiter.allow("a") is True


class TestValidation:
    def test_error_prose_does_not_echo_the_submitted_value(
        self, client: TestClient
    ) -> None:
        """FastAPI's default handler reflects input, which could be a password."""
        secret = "SuperSecretPassword1!"
        response = client.post(
            f"{API}/auth/register",
            json={
                "email": "not-an-email",
                "full_name": "A",
                "password": secret,
                "organization_name": "B",
            },
        )
        assert response.status_code == 422
        assert secret not in response.text

    def test_error_shape_is_structured(self, client: TestClient) -> None:
        response = client.post(f"{API}/auth/login", json={"email": "bad"})
        assert response.status_code == 422
        body = response.json()
        assert {"field", "message"} <= set(body.get("detail", [{}])[0])

    def test_weak_password_rejected(self, client: TestClient) -> None:
        response = client.post(
            f"{API}/auth/register",
            json={
                "email": "user@example.com",
                "full_name": "Valid Name",
                "password": "1" * 16,
                "organization_name": "Acme",
            },
        )
        assert response.status_code == 422

    def test_malformed_uuid_rejected(self, client: TestClient) -> None:
        assert client.get(f"{API}/jobs/public/not-a-uuid").status_code == 422


class TestOpenApiContract:
    def test_public_job_analytics_route_exists(self) -> None:
        """The frontend called this and it did not exist, so it 404'd."""
        assert f"{API}/jobs/public/analytics" in app.openapi()["paths"]

    def test_literal_route_declared_before_the_parameterized_one(self) -> None:
        """FastAPI matches in declaration order, so ordering is load-bearing."""
        paths = list(app.openapi()["paths"].keys())
        assert paths.index(f"{API}/jobs/public/analytics") < paths.index(
            f"{API}/jobs/public/{{job_id}}"
        )

    def test_raw_resume_text_is_never_served(self) -> None:
        schemas = app.openapi()["components"]["schemas"]
        assert "extracted_text" not in schemas["ScreeningResultResponse"]["properties"]
        assert "extracted_text" not in schemas["ResumeResponse"]["properties"]

    def test_screening_result_exposes_provenance_and_fairness(self) -> None:
        properties = app.openapi()["components"]["schemas"][
            "ScreeningResultResponse"
        ]["properties"]
        for field in ("provider", "semantic_backend", "bias_flags"):
            assert field in properties


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------


def build_settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "ENVIRONMENT": "development",
        "DATABASE_URL": "postgresql+psycopg://org:local@localhost:5432/db",
        "JWT_SECRET_KEY": "a-perfectly-adequate-secret-key-of-length",
        "_env_file": None,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


class TestConfiguration:
    def test_short_secret_rejected(self) -> None:
        with pytest.raises(ValidationError, match="at least 32"):
            build_settings(JWT_SECRET_KEY="too-short")

    def test_secret_not_exposed_by_repr(self) -> None:
        settings = build_settings()
        assert "a-perfectly-adequate-secret-key-of-length" not in repr(settings)

    def test_blank_api_key_becomes_none(self) -> None:
        """Blank must mean 'not configured', or the chain attempts a doomed call."""
        settings = build_settings(GEMINI_API_KEY="", GROQ_API_KEY="  ")
        assert settings.GEMINI_API_KEY is None
        assert settings.GROQ_API_KEY is None

    def test_provider_chain_parsed_and_deduplicated(self) -> None:
        settings = build_settings(AI_PROVIDER_ORDER="gemini, groq, ,gemini,ollama")
        assert settings.provider_chain == ("gemini", "groq", "ollama")

    @pytest.mark.parametrize(
        ("overrides", "match"),
        [
            ({"DEBUG": True}, "DEBUG"), 
            ({"COOKIE_SECURE": False}, "COOKIE_SECURE"),
            ({"JWT_SECRET_KEY": PLACEHOLDER_JWT_SECRET}, "placeholder"),
            ({"FRONTEND_ORIGIN": "http://app.example.com"}, "https"),
        ],
    )
    def test_unsafe_production_config_refuses_to_boot(
        self, overrides: dict[str, object], match: str
    ) -> None:
        base = {
            "ENVIRONMENT": "production",
            "COOKIE_SECURE": True,
            "FRONTEND_ORIGIN": "https://app.example.com",
            **overrides,
        }
        with pytest.raises(ValidationError, match=match):
            build_settings(**{**base, **overrides})

    def test_valid_production_config_accepted(self) -> None:
        settings = build_settings(
            ENVIRONMENT="production",
            COOKIE_SECURE=True,
            FRONTEND_ORIGIN="https://app.example.com",
        )
        assert settings.is_production is True

    def test_development_tolerates_insecure_defaults(self) -> None:
        assert build_settings(DEBUG=True, COOKIE_SECURE=False).is_production is False


# ------------------------------------------------------------------
# LLM fallback chain
# ------------------------------------------------------------------


class StubProvider(LLMProvider):
    """Scripted provider. Each call pops the next outcome from 'script'."""

    def __init__(
        self,
        name: str,
        *,
        configured: bool = True,
        script: list[str | Exception] | None = None,
    ) -> None:
        self.name = name
        self._configured = configured
        self.script: list[str | Exception] = script or ['{"ok": true}']
        self.calls = 0

    def is_configured(self) -> bool:
        return self._configured

    @property
    def model_name(self) -> str:
        return f"{self.name}-model"

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        outcome = self.script[min(self.calls - 1, len(self.script) - 1)]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def generate(**providers: StubProvider) -> LLMResponse:
    return LLMRouter(provider_dict=providers).generate_json(
        system_prompt="sys", user_prompt="user"
    )


class TestLlmFallbackChain:
    def test_first_configured_provider_wins(self) -> None:
        gemini = StubProvider("gemini")
        groq = StubProvider("groq")
        response = generate(gemini=gemini, groq=groq, provider_chain=("gemini", "groq"))
        assert response.provider == "gemini"
        assert groq.calls == 0, "later providers must not be called on success"

    def test_falls_through_to_the_next_provider(self) -> None:
        response = generate(
            gemini=StubProvider("gemini", script=[LLMConfigurationError("bad key")]),
            groq=StubProvider("groq"),
            provider_chain=("gemini", "groq"),
        )
        assert response.provider == "groq"

    def test_unconfigured_providers_are_skipped(self) -> None:
        gemini = StubProvider("gemini", configured=False)
        groq = StubProvider("groq")
        response = generate(gemini=gemini, groq=groq, provider_chain=("gemini", "groq"))
        assert gemini.calls == 0
        assert response.provider == "groq"

    def test_falls_through_the_whole_chain_to_ollama(self) -> None:
        response = generate(
            gemini=StubProvider("gemini", script=[LLMConfigurationError("no key")]),
            groq=StubProvider("groq", script=[LLMRouter("timeout")]),
            ollama=StubProvider("ollama"),
            provider_chain=("gemini", "groq", "ollama"),
        )
        assert response.provider == "ollama"

    def test_transient_error_retried_but_config_error_is_not(self) -> None:
        retried = StubProvider(
            "gemini", script=[LLMTransientError("temporary"), '{"ok": true}']
        )
        assert generate(gemini=retried).provider == "gemini"
        assert retried.calls == 2

        # A bad API key will never succeed, so retrying only wastes time.
        misconfigured = StubProvider(
            "gemini", script=[LLMConfigurationError("invalid api key")]
        )
        assert generate(gemini=misconfigured, groq=StubProvider("groq"))
        assert misconfigured.calls == 1

    def test_empty_response_treated_as_failure(self) -> None:
        response = generate(
            gemini=StubProvider("gemini", script=["", "   "]),
            groq=StubProvider("groq"),
        )
        assert response.provider == "groq"

    def test_exhausted_chain_raises_with_detail(self) -> None:
        with pytest.raises(AllProvidersFailed) as exc_info:
            generate(
                gemini=StubProvider("gemini", script=[LLMConfigurationError("no key")]),
                groq=StubProvider("groq", script=[LLMTransientError("timeout")]),
            )
        reasons = {a.provider: a.reason for a in exc_info.value.attempts}
        assert "misconfigured" in reasons["gemini"]

    def test_no_providers_configured_raises(self) -> None:
        with pytest.raises(AllProvidersFailed) as exc_info:
            generate(gemini=StubProvider("gemini", configured=False))

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ('{"a": 1}', {"a": 1}),
            ('```json\n{"a": 1}\n```', {"a": 1}),
            ("Here you go:\n\n```json\n{'a': 1}\n```\nHope that helps.", {"a": 1}),
            ("{'a': 1} Hope that helps.", {"a": 1}),
            ("Not json at all.", {}),
            ("", {}),
            ("[1, 2, 3]", {}),
        ],
    )
    def test_json_extraction(self, text: str, expected: dict) -> None:
        """Handles well-fenced or prose-wrapped JSON even when told not to."""
        assert LLMResponse(text=text, provider="x", model="m").as_json == expected

    def test_only_the_local_provider_is_trusted_with_pii(self) -> None:
        """Free-hosted tiers commonly train on submitted data; local does not."""
        from app.agents.llm_router import (
            GeminiProvider,
            GroqProvider,
            OllamaProvider,
        )

        assert GeminiProvider().trusted_with_pii is False
        assert GroqProvider().trusted_with_pii is False
        assert OllamaProvider().trusted_with_pii is True