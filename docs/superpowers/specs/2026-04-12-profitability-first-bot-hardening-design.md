# Profitability-First Bot Hardening Design

## Goal

Move the Polymarket BTC 5-minute bot from "actively trading with uncertain real edge" to "trading less often, with more trustworthy execution and a better chance of positive post-cost expectancy."

This design does not promise guaranteed profit. Its purpose is to remove the current failure modes that make the bot look smarter than it really is: unsafe runtime behavior, weak execution truth, overly optimistic probability assumptions, and entry rules that still allow low-quality trades.

## Problem Statement

The current bot already contains many advanced components: signal generation, candidate ranking, edge thresholds, Kelly-style sizing, maker-first execution, hedge exits, and journal/report analysis. The problem is not that the bot lacks ideas. The problem is that too much of the stack still depends on assumptions that are not trustworthy enough to support real profitability.

The main issues fall into four groups:

1. **Truth problems**
   - Root `.env` is tracked and loaded directly.
   - TLS verification is globally disabled in `main.py`.
   - `verify=False` is used in `core/market_resolver.py`.
   - Some runtime paths are centralized in `core/runtime_paths.py`, but `core/state_store.py`, `core/journal.py`, and `core/run_journal.py` still freeze mode-specific paths at import time.

2. **Execution/accounting problems**
   - Live exposure and fill/accounting truth are not fully trustworthy.
   - Maker/taker state transitions are more heuristic than authoritative.
   - Reported `observed` profit can diverge from `actual` realized profit.

3. **Qualification problems**
   - The bot still enters too many mediocre setups near neutral pricing or thin execution conditions.
   - Maker-to-taker fallback can rescue trades that never had enough post-cost edge.
   - Deadline exits still carry too much of the loss burden.

4. **Calibration problems**
   - `core/decision_engine.py` contains multiple heuristic or fixed probability assignments.
   - Those values are later used by edge filters and Kelly sizing.
   - If the probability estimate is wrong, EV gating and Kelly logic become error amplifiers rather than advantages.

The design objective is therefore to **fix truth first, tighten qualification second, and only then improve edge estimation**.

## Non-Negotiable Design Principles

1. **Truth before alpha** — do not optimize a bot whose realized PnL accounting is still untrustworthy.
2. **Selectivity over activity** — fewer trades is acceptable if the bad trades disappear first.
3. **Execution-aware qualification** — if a trade only works before fees/slippage/fallback cost, it is not a valid trade.
4. **Probability skepticism** — heuristic probabilities may be useful as signals, but not as trustworthy EV inputs until calibrated.
5. **Incremental architecture change** — use the current bot structure where possible instead of rewriting everything into a new engine.

## Architecture Direction

The bot should be treated as a five-layer system.

### 1. Truth Layer

This layer ensures the bot's runtime and reports reflect reality.

**Responsibilities**
- Safe environment loading and secret hygiene.
- Safe HTTP/TLS behavior.
- Correct dry-run vs live path isolation.
- Trustworthy live position / exposure / fill state.
- Actual-cash-aware journal and report reconciliation.

**Primary files**
- `main.py`
- `core/config.py`
- `core/runtime_paths.py`
- `core/state_store.py`
- `core/journal.py`
- `core/run_journal.py`
- `core/exchange.py`
- `scripts/journal_analysis.py`

**Why it matters**

If this layer is wrong, nothing above it can be evaluated honestly.

### 2. Qualification Layer

This is the most important new emphasis. It should answer one question: **"Should this bot be allowed to trade this setup at all?"**

This layer should sit between signal generation and execution.

**Responsibilities**
- Neutral-zone no-trade blocks or steep edge penalties.
- Time-window gating.
- Volatility gating.
- Book-quality gating.
- Execution-cost buffer requirements.
- Maker fallback eligibility checks.
- Conservative-mode restrictions after bad recent execution quality.

**Primary files**
- `core/runner.py`
- `core/trade_manager.py`
- `core/config.py`

**Why it matters**

The repo already has many ways to generate a direction. What it lacks is a strong enough refusal mechanism.

### 3. Signal Layer

This layer generates possible directional candidates.

**Responsibilities**
- Order-flow imbalance, websocket velocity, liquidation fade, underdog, theta/strike-cross, and related signal generation.
- Candidate scoring inputs.
- Strategy-specific metadata for later qualification.

**Primary file**
- `core/decision_engine.py`

**Design rule**

Do not add more signals in the first hardening phase. First reduce false confidence in the existing ones.

### 4. Execution Layer

This layer should decide how a qualified trade is actually entered or exited.

**Responsibilities**
- Maker-first posting.
- Safe maker aging and cancellation.
- Strict maker-to-taker fallback discipline.
- Better fill confirmation and close-state reconciliation.
- Cleaner separation between routine execution and emergency forced exits.

**Primary files**
- `core/runner.py`
- `core/exchange.py`
- `core/trade_manager.py`

### 5. Reporting Layer

This layer determines whether changes actually improved the bot.

**Responsibilities**
- Compare observed vs actual outcomes.
- Track fee-adjusted active-close quality.
- Distinguish reported edge from realized edge.
- Provide enough evidence to judge whether tighter gating is working.

**Primary file**
- `scripts/journal_analysis.py`

## Proposed Strategy Direction

### A. Stop optimizing for trade count

The first target is not more trades or faster trades. The first target is to stop entering weak setups that only look attractive before real execution cost.

This means:
- wider refusal zones around neutral pricing,
- stricter late-entry penalties,
- explicit execution-cost buffers,
- more willingness to skip a market entirely.

### B. Treat probability as a ranking input, not a truth source

Until probability estimates are calibrated from realized outcomes, they should be treated as **relative ranking hints**, not as trustworthy post-cost win probabilities.

This means:
- keep candidate ranking,
- keep scoreboarding,
- keep strategy history,
- but reduce how aggressively heuristic probabilities drive EV-style math and Kelly-style sizing.

### C. Use conservative mode as regime defense

Recent bad active-close quality should trigger a temporary defensive regime.

In conservative mode the bot should:
- widen the no-trade zone,
- require more edge,
- reduce or disable routine taker fallback,
- optionally skip the next N windows,
- optionally size down.

This is not meant to predict the market. It is meant to stop the bot from repeatedly paying for a hostile microstructure regime.

### D. Favor early cleanup over expensive deadline failure

Existing history suggests the bot often loses by carrying weak trades too long and then paying for late cleanup.

The design should therefore:
- preserve strong principal extraction behavior,
- recycle weak pre-principal positions earlier,
- reduce the share of exits that happen in the most expensive endgame window,
- use realized execution quality, not just mark value, to judge whether a position is genuinely healthy.

## What From the Pasted Strategy Spec Should Be Adopted

### Adopt now

1. **Volatility filtering**
   - Reason: compatible with current design and useful for avoiding dead/noisy regimes.
2. **Tighter decision windows**
   - Reason: already conceptually supported by the runner structure; this is mostly a qualification change.
3. **Stronger risk shutdown rules**
   - Reason: practical and directly protective.
4. **Order-flow + orderbook confirmation**
   - Reason: the repo already has versions of this idea; hardening it is easier than introducing a whole new data model.

### Defer until later

1. **Formal Kelly-heavy sizing logic**
   - Reason: too dependent on probability calibration.
2. **Hedging as a primary edge engine**
   - Reason: useful conceptually, but adds execution complexity before the truth layer is stable.
3. **Sentiment/social feed integration**
   - Reason: high complexity, unclear short-horizon value for this repo's current maturity.

### Reject as first-phase priorities

1. **Per-order gas gating as a core entry rule**
   - Polymarket CLOB order submission is off-chain signed and submitted via API; gas is not the main per-trade gating problem here.
2. **Flashbots/MEV as a first-phase hardening requirement**
   - Not the dominant bottleneck for the current bot architecture and loss profile.
3. **Adding many more new alpha modules**
   - Current evidence points to qualification and execution realism problems more than signal scarcity.

## Scope

### In scope

- Runtime truth hardening.
- Execution/accounting truth hardening.
- Profitability-first qualification rules.
- Conservative mode based on recent realized execution quality.
- Reduction of heuristic overconfidence in strategy qualification.
- Updated tests and report-based validation.

### Out of scope

- Guaranteed profitability claims.
- Full market-making engine rewrite.
- Full external data platform build-out.
- Low-latency infrastructure redesign.
- Copy-trading / wallet-cloning strategy rewrite.

## Success Metrics

The first successful version of this design should improve **quality of trading**, not just code cleanliness.

### Code-level success

- Safety and path-handling regressions are covered by targeted tests.
- Entry-qualification and execution-discipline changes are covered by targeted tests.
- Focused verification passes for the touched modules.

### Trading-quality success

Compared with the current baseline, recent run reports should show some combination of:

- lower ratio of trades opened in neutral-price zones,
- lower share of `deadline-*` and expensive weak active-close exits,
- smaller gap between `observed` and `actual` PnL,
- improved fee-adjusted `active-close` average,
- fewer large realized losses caused by late cleanup,
- lower total trade count with better per-trade quality.

### Failure signals

This design should be considered insufficient if:

- `actual` and `observed` converge but fee-adjusted active-close PnL remains negative,
- trade count collapses but realized quality does not improve,
- maker-first discipline still leaves stale or ambiguous fill state,
- heuristic probabilities still dominate EV-like logic without calibration.

## Recommendation

Proceed in this order:

1. **Repair truth and safety.**
2. **Repair execution and reporting realism.**
3. **Tighten qualification rules.**
4. **Reduce heuristic overconfidence.**
5. **Only then evaluate whether a more formal EV evaluator is justified.**

The right near-term strategy is not "teach the bot more patterns." It is **make the bot much harder to convince**.
