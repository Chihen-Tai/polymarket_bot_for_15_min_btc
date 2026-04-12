from __future__ import annotations

from typing import Any

import requests


DEFAULT_TIMEOUT = 12


def request_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
):
    response = requests.get(url, params=params, timeout=timeout, verify=True)
    response.raise_for_status()
    return response.json()


def request_json_with_session(
    session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
):
    response = session.get(url, params=params, timeout=timeout, verify=True)
    response.raise_for_status()
    return response.json()
