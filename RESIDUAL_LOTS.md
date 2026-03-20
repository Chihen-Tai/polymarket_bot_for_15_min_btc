# Residual Lots

Known residual / worthless lots that should not be treated as active bot positions unless manually verified.

## 2026-03-19

- token_id: `38490959023900375505459861064041510453855924207378335177538302161737266403566`
- market: `btc-updown-5m-1773893100`
- side: `UP`
- bot-tracked shares: `99.99755`
- initial value: `$0.9999755`
- observed live API status during cleanup:
  - `current_value = 0`
  - `cash_pnl = -0.9999755`
  - `percent_pnl = -100%`
- cleanup action:
  - removed from `.runtime_state.json` active `open_positions`
  - treat as worthless residual / legacy bad lot for future manual reconciliation

Reason:
This lot was no longer a meaningful recoverable active position for bot execution, but it polluted runtime recovery and could block future trading logic.
