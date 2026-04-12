from datetime import datetime, timezone
import json
import time

from core.config import SETTINGS
from core.http import request_json


class MarketResolutionError(Exception):
    pass


def _coerce_ids(v):
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except Exception:
            return []
    return v if isinstance(v, list) else []


def _extract_token_pair(m: dict) -> tuple[str, str] | tuple[None, None]:
    ids = _coerce_ids(m.get("clobTokenIds"))
    if len(ids) < 2:
        return None, None

    outcomes = _coerce_ids(m.get("outcomes"))
    mapped: dict[str, str] = {}
    for idx, outcome in enumerate(outcomes):
        if idx >= len(ids):
            break
        label = str(outcome or "").strip().lower()
        if label == "up":
            mapped["up"] = str(ids[idx])
        elif label == "down":
            mapped["down"] = str(ids[idx])

    if mapped.get("up") and mapped.get("down"):
        return mapped["up"], mapped["down"]
    return str(ids[0]), str(ids[1])


def _fetch_by_slug(slug: str):
    arr = (
        request_json(
            "https://gamma-api.polymarket.com/markets",
            params={"slug": slug},
            timeout=12,
        )
        or []
    )
    if not arr:
        return None
    m = arr[0]
    token_up, token_down = _extract_token_pair(m)
    if not token_up or not token_down:
        return None
    strike_price = None
    events = m.get("events", [])
    if events and isinstance(events, list) and len(events) > 0:
        event_metadata = events[0].get("eventMetadata", {})
        strike_price = event_metadata.get("priceToBeat")

    return {
        "question": m.get("question"),
        "slug": m.get("slug") or slug,
        "condition_id": m.get("conditionId"),
        "token_up": token_up,
        "token_down": token_down,
        "outcomes": m.get("outcomes"),
        "outcomePrices": m.get("outcomePrices"),
        "endDate": m.get("endDate") or m.get("end_date_iso"),
        "strike_price": strike_price,
    }


def _candidate_slugs_from_epoch(prefix: str):
    # 使用者觀察：每 5 分鐘 +300
    now = int(time.time())
    base = (now // 300) * 300
    # 依序嘗試當前區間與前後幾檔
    for d in [0, 300, -300, 600, -600, 900, -900]:
        yield f"{prefix}{base + d}"


def resolve_latest_btc_5m_token_ids() -> dict:
    prefix = SETTINGS.market_slug_prefix

    # 先走「5 分鐘 +300」規律（最穩）
    for slug in _candidate_slugs_from_epoch(prefix):
        got = _fetch_by_slug(slug)
        if got:
            return got

    # 後備：掃 active markets 用 prefix contains
    data = request_json(
        "https://gamma-api.polymarket.com/markets",
        params={"active": "true", "closed": "false", "limit": 500},
        timeout=12,
    )

    candidates = []
    for m in data:
        slug = m.get("slug") or ""
        if prefix.lower() not in slug.lower():
            continue
        token_up, token_down = _extract_token_pair(m)
        if not token_up or not token_down:
            continue
        # 優先取 slug 最後的 epoch 數字
        try:
            tail = int(slug.split("-")[-1])
        except Exception:
            tail = 0
        candidates.append((tail, m, token_up, token_down))

    if not candidates:
        raise MarketResolutionError(f"no active markets with slug prefix: {prefix}")

    candidates.sort(key=lambda x: x[0], reverse=True)
    _, m, token_up, token_down = candidates[0]
    return {
        "question": m.get("question"),
        "slug": m.get("slug"),
        "condition_id": m.get("conditionId"),
        "token_up": token_up,
        "token_down": token_down,
        "outcomes": m.get("outcomes"),
        "outcomePrices": m.get("outcomePrices"),
        "endDate": m.get("endDate") or m.get("end_date_iso"),
    }
