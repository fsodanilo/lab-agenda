import json

from devops_lab.analyze_failure import (
    _ask_model,
    _extract_gemini_text,
    _filter_lab_diff,
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
    log = "api_key=example-secret token:example-token sk-abcdefghijklmnopqrstuvwxyz12345"

    assert _redact_secrets(log) == "api_key=[REDACTED] token:[REDACTED] [REDACTED]"


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


def test_extract_gemini_text_from_generate_content_response() -> None:
    response = {
        "candidates": [
            {"content": {"parts": [{"text": "Diagnóstico preliminar."}]}}
        ]
    }

    assert _extract_gemini_text(response) == "Diagnóstico preliminar."


def test_ask_model_sends_key_in_header_and_uses_gemini_payload(monkeypatch) -> None:
    captured_request = None

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self) -> bytes:
            return json.dumps(
                {"candidates": [{"content": {"parts": [{"text": "Diagnóstico."}]}}]}
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        nonlocal captured_request
        captured_request = request
        assert timeout == 45
        return FakeResponse()

    monkeypatch.setattr("devops_lab.analyze_failure.urlopen", fake_urlopen)

    result = _ask_model("falha de teste", "diff fictício", "AIzaFAKE_KEY", "gemini-2.5-flash-lite")

    assert result == "Diagnóstico."
    assert captured_request is not None
    assert "AIzaFAKE_KEY" not in captured_request.full_url
    assert captured_request.get_header("X-goog-api-key") == "AIzaFAKE_KEY"
    payload = json.loads(captured_request.data)
    assert payload["contents"][0]["parts"][0]["text"].startswith("Log de testes:")