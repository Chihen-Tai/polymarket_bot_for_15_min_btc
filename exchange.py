from dataclasses import dataclass
from random import uniform
from typing import Any
import time

import requests

from config import SETTINGS


@dataclass
class Account:
    equity: float
    cash: float
    open_exposure: float


@dataclass
class Position:
    token_id: str
    size: float
    avg_price: float
    initial_value: float
    current_value: float
    cash_pnl: float
    percent_pnl: float


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


class PolymarketExchange:
    """
    dry-run: 本地模擬
    real mode: 使用 py-clob-client
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._equity = 10.30
        self._cash = 9.23
        self._open_exposure = 0.0
        self._last_price = 73933.39

        self.client = None
        self._funder = SETTINGS.funder_address

        if not self.dry_run:
            self._init_real_client()

    def _init_real_client(self):
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds

        if not SETTINGS.private_key:
            raise ValueError("PRIVATE_KEY is required when DRY_RUN=false")

        if not self._funder:
            raise ValueError("FUNDER_ADDRESS is required when DRY_RUN=false")

        if SETTINGS.clob_api_key and SETTINGS.clob_api_secret and SETTINGS.clob_api_passphrase:
            creds = ApiCreds(
                api_key=SETTINGS.clob_api_key,
                api_secret=SETTINGS.clob_api_secret,
                api_passphrase=SETTINGS.clob_api_passphrase,
            )
            self.client = ClobClient(
                SETTINGS.clob_host,
                key=SETTINGS.private_key,
                chain_id=SETTINGS.chain_id,
                creds=creds,
                signature_type=SETTINGS.signature_type,
                funder=self._funder,
            )
            return

        temp_client = ClobClient(
            SETTINGS.clob_host,
            key=SETTINGS.private_key,
            chain_id=SETTINGS.chain_id,
            signature_type=SETTINGS.signature_type,
            funder=self._funder,
        )
        creds = temp_client.create_or_derive_api_creds()

        self.client = ClobClient(
            SETTINGS.clob_host,
            key=SETTINGS.private_key,
            chain_id=SETTINGS.chain_id,
            creds=creds,
            signature_type=SETTINGS.signature_type,
            funder=self._funder,
        )

    def _get_positions_value(self) -> float:
        # Data API: https://data-api.polymarket.com/value?user=0x...
        if not self._funder:
            return 0.0
        try:
            r = requests.get(
                f"{SETTINGS.data_api_host}/value",
                params={"user": self._funder},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list) and data:
                # 通常為 [{"user":..., "value": ...}]
                return _to_float(data[0].get("value", 0.0), 0.0)
            if isinstance(data, dict):
                return _to_float(data.get("value", 0.0), 0.0)
            return 0.0
        except Exception:
            return 0.0

    def _get_cash_balance(self) -> float:
        try:
            from py_clob_client.clob_types import BalanceAllowanceParams, AssetType

            # 先用設定值，再 fallback 掃 0/1/2（解決代理錢包 signature type 不一致）
            sig_candidates = [SETTINGS.signature_type, 0, 1, 2]
            best = 0.0
            for sig in dict.fromkeys(sig_candidates):
                try:
                    resp = self.client.get_balance_allowance(
                        BalanceAllowanceParams(
                            asset_type=AssetType.COLLATERAL,
                            token_id="",
                            signature_type=sig,
                        )
                    )
                    for k in ("balance", "available", "available_balance"):
                        if isinstance(resp, dict) and k in resp:
                            v = _to_float(resp.get(k), 0.0)
                            # USDC 常見為 6 decimals（回傳最小單位）
                            if v > 100000:
                                v = v / 1_000_000
                            if v > best:
                                best = v
                except Exception:
                    continue
            return best
        except Exception:
            return 0.0

    def _extract_close_response_value(self, payload: Any) -> tuple[float | None, str, dict[str, float | None]]:
        if not isinstance(payload, dict):
            return None, "close_response_unavailable", {}

        candidates = {
            "takingAmount": _to_float(payload.get("takingAmount"), -1.0),
            "makingAmount": _to_float(payload.get("makingAmount"), -1.0),
        }
        normalized = {k: (v if v >= 0 else None) for k, v in candidates.items()}

        taking = normalized["takingAmount"]
        if taking is not None and taking > 0:
            return taking, "close_response_takingAmount", normalized

        making = normalized["makingAmount"]
        if making is not None and making > 0:
            return making, "close_response_makingAmount", normalized

        return None, "close_response_missing_amount", normalized

    def get_account(self) -> Account:
        if self.dry_run:
            return Account(
                equity=self._equity,
                cash=self._cash,
                open_exposure=self._open_exposure,
            )

        cash = self._get_cash_balance()
        positions_value = self._get_positions_value()
        equity = cash + positions_value

        # open exposure 先用保守值 0（後續可擴充為掃 open orders）
        return Account(equity=equity, cash=cash, open_exposure=0.0)

    def get_positions(self) -> list[Position]:
        if self.dry_run or not self._funder:
            return []
        try:
            r = requests.get(
                f"{SETTINGS.data_api_host}/positions",
                params={"user": self._funder},
                timeout=10,
            )
            r.raise_for_status()
            arr = r.json() or []
            out: list[Position] = []
            for row in arr:
                size = _to_float(row.get("size", 0.0), 0.0)
                if size <= 0:
                    continue
                out.append(Position(
                    token_id=str(row.get("asset") or ""),
                    size=size,
                    avg_price=_to_float(row.get("avgPrice", 0.0), 0.0),
                    initial_value=_to_float(row.get("initialValue", 0.0), 0.0),
                    current_value=_to_float(row.get("currentValue", 0.0), 0.0),
                    cash_pnl=_to_float(row.get("cashPnl", 0.0), 0.0),
                    percent_pnl=_to_float(row.get("percentPnl", 0.0), 0.0),
                ))
            return out
        except Exception:
            return []

    def get_btc_price(self) -> float:
        if self.dry_run:
            self._last_price += uniform(-40, 40)
            return max(1000, self._last_price)

        # 實盤可改用市場 API；先沿用輕量 public endpoint（coingecko）
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin", "vs_currencies": "usd"},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            p = _to_float(data.get("bitcoin", {}).get("usd", 0), 0)
            if p > 0:
                return p
        except Exception:
            pass

        return self._last_price

    def place_order(self, side: str, amount_usd: float, token_id_override: str | None = None) -> dict:
        if self.dry_run:
            self._cash -= amount_usd
            self._open_exposure += amount_usd
            return {
                "ok": True,
                "mode": "dry-run",
                "side": side,
                "amount_usd": amount_usd,
                "order_id": "dryrun-order",
            }

        # side = UP / DOWN ; 對應 token id
        token_id = token_id_override or (SETTINGS.token_id_up if side == "UP" else SETTINGS.token_id_down)
        if not token_id:
            raise ValueError("TOKEN_ID_UP / TOKEN_ID_DOWN is required when DRY_RUN=false")

        from py_clob_client.clob_types import MarketOrderArgs, OrderType
        from py_clob_client.order_builder.constants import BUY

        order = self.client.create_market_order(
            MarketOrderArgs(
                token_id=token_id,
                amount=float(amount_usd),
                side=BUY,
                order_type=OrderType.FOK,
            )
        )
        resp = self.client.post_order(order, OrderType.FOK)

        return {
            "ok": True,
            "mode": "live",
            "side": side,
            "amount_usd": amount_usd,
            "response": resp,
        }

    def has_exit_liquidity(self, token_id: str, shares: float) -> bool:
        if self.dry_run:
            return True
        try:
            book = self.client.get_order_book(token_id)
            bids = book.get("bids") if isinstance(book, dict) else None
            if not isinstance(bids, list):
                return True
            total = 0.0
            for lv in bids:
                if isinstance(lv, dict):
                    sz = _to_float(lv.get("size", lv.get("amount", 0)), 0.0)
                elif isinstance(lv, (list, tuple)) and len(lv) >= 2:
                    sz = _to_float(lv[1], 0.0)
                else:
                    sz = 0.0
                total += max(0.0, sz)
                if total >= shares * 0.8:
                    return True
            return False
        except Exception:
            return True

    def close_position(self, token_id: str, shares: float) -> dict:
        if self.dry_run:
            return {"ok": True, "mode": "dry-run", "closed_shares": shares}

        from py_clob_client.clob_types import MarketOrderArgs, OrderType
        from py_clob_client.order_builder.constants import SELL

        cash_before = self._get_cash_balance()
        remaining = float(shares)
        attempts = 0
        last_resp = None
        last_error = None
        sold_total = 0.0
        response_amount_value = None
        response_amount_source = "close_response_unavailable"
        response_amount_fields: dict[str, float | None] = {}
        while remaining > 0.0001 and attempts < 5:
            attempts += 1
            # progressively smaller chunks on retries
            if attempts == 1:
                chunk = remaining
            elif attempts == 2:
                chunk = max(remaining * 0.7, 0.01)
            elif attempts == 3:
                chunk = max(remaining * 0.5, 0.01)
            else:
                chunk = max(remaining * 0.35, 0.01)

            try:
                order = self.client.create_market_order(
                    MarketOrderArgs(
                        token_id=token_id,
                        amount=float(chunk),
                        side=SELL,
                        order_type=OrderType.FOK,
                    )
                )
                last_resp = self.client.post_order(order, OrderType.FOK)
                amount_value, amount_source, amount_fields = self._extract_close_response_value(last_resp)
                if amount_value is not None and amount_value > 0:
                    response_amount_value = (response_amount_value or 0.0) + amount_value
                response_amount_source = amount_source
                response_amount_fields = amount_fields
                remaining -= chunk
                sold_total += chunk
            except Exception as e:
                last_error = str(e)
                # small delay then retry
                time.sleep(2)
                continue

            time.sleep(2)

        cash_after = None
        cash_delta = None
        cash_delta_source = "cash_balance_unavailable"
        if sold_total > 0:
            for _ in range(3):
                cash_after = self._get_cash_balance()
                if cash_after > 0 or cash_before > 0:
                    cash_delta = cash_after - cash_before
                    if cash_delta > 0:
                        cash_delta_source = "cash_balance_delta"
                        break
                    cash_delta_source = "cash_balance_non_positive"
                time.sleep(1)

        ok = sold_total > 0 and (last_resp is not None)
        return {
            "ok": ok,
            "mode": "live",
            "requested_shares": shares,
            "closed_shares": sold_total,
            "remaining_shares": max(0.0, float(shares) - sold_total),
            "attempts": attempts,
            "response": last_resp,
            "error": None if ok else (last_error or "no fill"),
            "cash_before": cash_before,
            "cash_after": cash_after,
            "actual_exit_value_usd": cash_delta,
            "actual_exit_value_source": cash_delta_source,
            "close_response_value": response_amount_value,
            "close_response_value_source": response_amount_source,
            "close_response_amount_fields": response_amount_fields,
        }

    def settle_mock(self, pnl: float):
        if not self.dry_run:
            return
        self._open_exposure = max(0.0, self._open_exposure - 1.0)
        self._cash += (1.0 + pnl)
        self._equity += pnl
