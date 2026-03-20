import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _f(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


def _i(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def _b(key: str, default: bool) -> bool:
    return os.getenv(key, str(default)).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    dry_run: bool = _b("DRY_RUN", True)

    min_equity: float = _f("MIN_EQUITY", 5.0)
    max_order_usd: float = _f("MAX_ORDER_USD", 1.0)
    max_exposure_usd: float = _f("MAX_EXPOSURE_USD", 3.0)
    max_orders_per_5min: int = _i("MAX_ORDERS_PER_5MIN", 1)
    max_consec_loss: int = _i("MAX_CONSEC_LOSS", 3)
    daily_max_loss: float = _f("DAILY_MAX_LOSS", 2.0)

    poll_seconds: int = _i("POLL_SECONDS", 15)

    discord_webhook_url: str = os.getenv("DISCORD_WEBHOOK_URL", "")

    # CLOB runtime settings
    clob_host: str = os.getenv("CLOB_HOST", "https://clob.polymarket.com")
    data_api_host: str = os.getenv("DATA_API_HOST", "https://data-api.polymarket.com")
    chain_id: int = _i("CHAIN_ID", 137)
    signature_type: int = _i("SIGNATURE_TYPE", 1)

    # Trading identity
    private_key: str = os.getenv("PRIVATE_KEY", "")
    funder_address: str = os.getenv("FUNDER_ADDRESS", "")

    # Optional fixed CLOB API creds
    clob_api_key: str = os.getenv("CLOB_API_KEY", "")
    clob_api_secret: str = os.getenv("CLOB_API_SECRET", "")
    clob_api_passphrase: str = os.getenv("CLOB_API_PASSPHRASE", "")

    # Target market token ids (optional static)
    token_id_up: str = os.getenv("TOKEN_ID_UP", "")
    token_id_down: str = os.getenv("TOKEN_ID_DOWN", "")

    # Auto market selection
    auto_market_selection: bool = _b("AUTO_MARKET_SELECTION", True)
    market_slug_prefix: str = os.getenv("MARKET_SLUG_PREFIX", "btc-updown-5m-")

    # Integrated decision rules (from prior paper simulations)
    edge_threshold: float = _f("EDGE_THRESHOLD", 0.02)
    fee_buffer: float = _f("FEE_BUFFER", 0.01)
    zscore_window: int = _i("ZSCORE_WINDOW", 10)
    zscore_threshold: float = _f("ZSCORE_THRESHOLD", 2.2)
    entry_window_min_sec: float = _f("ENTRY_WINDOW_MIN_SEC", 40.0)
    entry_window_max_sec: float = _f("ENTRY_WINDOW_MAX_SEC", 95.0)
    min_entry_price: float = _f("MIN_ENTRY_PRICE", 0.2)
    max_entry_price: float = _f("MAX_ENTRY_PRICE", 0.8)

    # Cadence guard: avoid long no-trade stretches
    max_idle_minutes: int = _i("MAX_IDLE_MINUTES", 120)

    # Dump+hedge integration
    dump_move_threshold: float = _f("DUMP_MOVE_THRESHOLD", 0.08)
    hedge_sum_target: float = _f("HEDGE_SUM_TARGET", 0.95)
    hedge_max_wait_sec: int = _i("HEDGE_MAX_WAIT_SEC", 90)
    stop_loss_pct: float = _f("STOP_LOSS_PCT", 0.20)
    max_hold_seconds: int = _i("MAX_HOLD_SECONDS", 90)
    take_profit_soft_pct: float = _f("TAKE_PROFIT_SOFT_PCT", 0.50)
    take_profit_hard_pct: float = _f("TAKE_PROFIT_HARD_PCT", 1.00)
    momentum_ticks: int = _i("MOMENTUM_TICKS", 3)
    momentum_min_move: float = _f("MOMENTUM_MIN_MOVE", 0.01)
    exit_deadline_sec: int = _i("EXIT_DEADLINE_SEC", 20)
    stop_loss_warn_pct: float = _f("STOP_LOSS_WARN_PCT", 0.12)


SETTINGS = Settings()
