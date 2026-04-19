# Live Startup CLOB Credentials Guard

Generated: 2026-04-19

## Confirmed Root Cause

The diagnosis is correct.

In live mode, if `CLOB_API_KEY`, `CLOB_API_SECRET`, and `CLOB_API_PASSPHRASE` are blank, startup used to reach:

- `core/exchange.py:591`

and call:

- `temp_client.create_or_derive_api_creds()`

That hits `clob.polymarket.com` during `PolymarketExchange.__init__`, which happens at the start of `main()`. If the Linux server is behind a VPN path that blocks or degrades the CLOB call, the bot can fail before any normal trading loop work begins.

## Repo Change Applied

I changed the repo so this no longer happens by default.

### New behavior

- `core/runner.py` preflight now fails fast if live mode is enabled and `CLOB_API_*` is missing.
- `core/runner.py` also fails fast on partial `CLOB_API_*` values.
- `core/exchange.py` now refuses to eager-derive creds in live mode unless `ALLOW_CLOB_CRED_DERIVATION=true`.

### Default stance

- `ALLOW_CLOB_CRED_DERIVATION` defaults to `false`.

That means the operationally safe path is now explicit:

- put `CLOB_API_KEY`
- `CLOB_API_SECRET`
- `CLOB_API_PASSPHRASE`

into `.env.local` or `.env.secrets`

## Verification

Passed:

- `python3 tests/test_runtime_paths.py`
- `python3 -m unittest tests.test_phase_live_clob_creds`

## Linux Checks To Run

On Allen's Linux host, run:

1. Confirm the server actually has the new code:

```bash
cd /home/allen/Desktop/bot/polymarket_bot_for_5_min_btc
git pull
```

2. Confirm whether CLOB creds are present:

```bash
grep CLOB /home/allen/Desktop/bot/polymarket_bot_for_5_min_btc/.env
grep CLOB /home/allen/Desktop/bot/polymarket_bot_for_5_min_btc/.env.local
```

## Fastest Operational Fix

If the three CLOB fields are blank on Linux, add them to `.env.local`:

```bash
cat >> .env.local << 'EOF'
CLOB_API_KEY=your_key
CLOB_API_SECRET=your_secret
CLOB_API_PASSPHRASE=your_passphrase
EOF
```

Then restart the bot.

## Optional Escape Hatch

If someone intentionally wants wallet-based credential derivation on startup anyway, they can set:

```bash
ALLOW_CLOB_CRED_DERIVATION=true
```

That restores the old behavior deliberately, instead of relying on it accidentally.
