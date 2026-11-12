import json
from io import BytesIO
from urllib.error import HTTPError
from types import SimpleNamespace

from devops_lab.analyze_failure import (
    _ask_model,
    _filter_lab_diff,
    _http_error_details,
    _read_pull_request,
    _redact_secrets,
)


def test_read_pull_request_number_from_workflow_run_event(tmp_path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps({"workflow_run": {"pull_requests": [{"number": 17}]}}),
        encoding="utf-8",
    )

    assert _read_pull_request(str(event_path)) == ("17", None)


def test_read_pull_request_returns_none_for_manual_run(tmp_path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"workflow_run": {"pull_requests": []}}), encoding="utf-8")

    assert _read_pull_request(str(event_path)) == (None, None)


def test_redact_secrets_masks_common_assignments() -> None:
    log = "api_key=example-secret token:example-token sk-abcdefghijklmnopqrstuvwxyz12345 gsk_abcdefghijklmnopqrstuvwxyz12345"

    assert _redact_secrets(log) == "api_key=[REDACTED] token:[REDACTED] [REDACTED] [REDACTED]"


def test_http_error_details_reports_status_and_redacts_groq_key() -> None:
    error = HTTPError(
        url="https://example.invalid",
        code=429,
        msg="Too Many Requests",
        hdrs=None,
        fp=BytesIO(b'{"error":"gsk_abcdefghijklmnopqrstuvwxyz12345 rate limit"}'),
    )

    details = _http_error_details(error)

    assert details.startswith("HTTP 429:")
    assert "gsk_abcdefghijklmnopqrstuvwxyz12345" not in details
    assert "[REDACTED]" in details


def test_http_error_details_reports_status_and_redacts_key() -> None:
    error = HTTPError(
        url="https://example.invalid",
        code=403,
        msg="Forbidden",
        hdrs=None,
        fp=BytesIO(b'{"error":"API key AIzaabcdefghijklmnopqrstuvwxyz123456 is invalid"}'),
    )

    details = _http_error_details(error)

    assert details.startswith("HTTP 403:")
    assert "AIzaabcdefghijklmnopqrstuvwxyz123456" not in details
    assert "[REDACTED]" in details


def test_filter_lab_diff_excludes_other_project_files() -> None:
    diff = (
        "diff --git a/app/main.py b/app/main.py\n+change outside lab\n"
        "diff --git a/devops_lab/shipping_service.py b/devops_lab/shipping_service.py\n"
        "+intentional change\n"
    )

    assert _filter_lab_diff(diff) == (
        "diff --git a/devops_lab/shipping_service.py b/devops_lab/shipping_service.py\n"
        "+intentional change\n"
    )


def test_ask_model_uses_groq_responses_api(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured["request"] = kwargs
            return SimpleNamespace(output_text="Diagnóstico.")

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.responses = FakeResponses()

    monkeypatch.setattr("devops_lab.analyze_failure.OpenAI", FakeClient)

    result = _ask_model("falha de teste", "diff fictício", "gsk_FAKE_KEY", "openai/gpt-oss-20b")

    assert result == "Diagnóstico."
    assert captured["client"] == {
        "api_key": "gsk_FAKE_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "timeout": 45,
    }
    request = captured["request"]
    assert request["model"] == "openai/gpt-oss-20b"
    assert request["instructions"].startswith("Analise falhas de CI")
    assert request["input"].startswith("Log de testes:")
