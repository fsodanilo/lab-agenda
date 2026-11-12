import json
from io import BytesIO
from urllib.error import HTTPError

from devops_lab.analyze_failure import (
    _ask_model,
    _extract_groq_text,
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


def test_extract_groq_text_from_chat_completion_response() -> None:
    response = {
        "choices": [
            {"message": {"content": "Diagnóstico preliminar."}}
        ]
    }

    assert _extract_groq_text(response) == "Diagnóstico preliminar."


def test_ask_model_sends_key_in_header_and_uses_groq_payload(monkeypatch) -> None:
    captured_request = None

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self) -> bytes:
            return json.dumps(
                {"choices": [{"message": {"content": "Diagnóstico."}}]}
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        nonlocal captured_request
        captured_request = request
        assert timeout == 45
        return FakeResponse()

    monkeypatch.setattr("devops_lab.analyze_failure.urlopen", fake_urlopen)

    result = _ask_model("falha de teste", "diff fictício", "gsk_FAKE_KEY", "qwen/qwen3.8-27b")

    assert result == "Diagnóstico."
    assert captured_request is not None
    assert captured_request.full_url == "https://api.groq.com/openai/v1/chat/completions"
    assert captured_request.get_header("Authorization") == "Bearer gsk_FAKE_KEY"
    payload = json.loads(captured_request.data)
    assert payload["model"] == "qwen/qwen3.8-27b"
    assert payload["messages"][1]["content"].startswith("Log de testes:")
