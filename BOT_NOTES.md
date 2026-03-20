# BOT_NOTES

## Position sync policy

The bot syncs positions from the Polymarket Data API, but **only for token ids already tracked by this bot** (runtime state or reconstructed journal lots).

Reason:
- the wallet contains historical / unrelated legacy positions
- importing all wallet positions would pollute stop-loss / take-profit logic
- current behavior is conservative: reconcile bot-tracked lots only

## Observation vs execution

The bot now separates **observed marks** from **execution results** more explicitly:
- floating exit decisions still use current observed market prices
- `observed_*` fields are mark-based estimates only (`observed_exit_value_source=observed_mark_price`)
- `actual_*` exit fields prefer close-time cash balance delta (`actual_exit_value_source=cash_balance_delta`)
- if no reliable balance delta is available, the bot keeps `actual_*` as unavailable and stores the raw close response amount separately under `actual_close_response_*`
- journaled `pnl_source` shows whether realized PnL came from actual recovered cash or from observed mark estimate fallback

This avoids presenting a response amount or mark estimate as if both were the same accounting truth.

## Journal recovery

The bot journal now supports partial-close reconstruction:
- `entry` creates a tracked lot
- `exit` reduces remaining shares/cost instead of always assuming a full close
- `reconcile_journal.py` emits notes for unmatched exits, invalid rows, and still-open / unreconciled lots

If runtime state is empty, the bot can rebuild tracked positions from the journal before syncing with live wallet positions.

## Restart / stale protection

On startup, stale protection flags are sanitized:
- if there is no active tracked position, `panic_exit_mode` and `close_fail_streak` are reset
- if the previous panic market is no longer active, protection is cleared instead of locking the bot forever

## Event labels

The journal can now record clearer cycle labels / intent labels such as:
- `good-entry`
- `bad-entry` (recorded on exit outcome)
- `no-signal`
- `signal-but-no-fill`
- `signal-blocked`

This is meant to make post-mortem review easier without changing the confirmed trading style.
