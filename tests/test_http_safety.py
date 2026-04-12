import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.http import request_json, request_json_with_session


def test_request_json_defaults_to_tls_verification(monkeypatch):
    captured = {}

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        return DummyResponse()

    monkeypatch.setattr("requests.get", fake_get)

    payload = request_json("https://example.com/markets")

    assert payload == {"ok": True}
    assert captured["verify"] is True
    assert captured["timeout"] == 12


def test_request_json_with_session_uses_verify_true():
    captured = {}

    class DummySession:
        def get(self, url, **kwargs):
            captured.update(kwargs)

            class DummyResponse:
                def raise_for_status(self):
                    return None

                def json(self):
                    return []

            return DummyResponse()

    payload = request_json_with_session(DummySession(), "https://example.com/data")

    assert payload == []
    assert captured["verify"] is True
    assert captured["timeout"] == 12
