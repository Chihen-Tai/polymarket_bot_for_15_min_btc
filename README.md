##Due to personal reasons, there will be no updates for a while, as I currently have no access to real market trading data. However, providing me with trading data is highly welcome.##
# Polymarket BTC 15-Minute Trading Bot

This bot is a production-oriented execution system for **Polymarket 15-minute BTC markets**. It is optimized for **maker-first** entry, **expiry-first** settlement, and **execution-truth** accounting.

## 🛡️ Core Philosophy
- **Execution Truth Over Signal Cleverness**: No trade is valid if its executable edge doesn't cover fees and spread.
- **Maker-First**: Default behavior is to provide liquidity (Limit Orders), not take it (Market Orders).
- **Expiry-First**: Most trades are held until market expiry to capture the full edge and avoid exit slippage.
- **Expectancy-Based Learning**: The bot ranks strategies based on real, fee-adjusted PnL, not just win rate.

## 🚀 Key Features
- **Default 15m Profile**: Optimized for `btc-updown-15m-` markets.
- **Executable Pricing**: Direct orderbook depth traversal to estimate real fill prices.
- **Dynamic Fee Model**: Automatically accounts for Polymarket's taker fees in every decision.
- **Shadow Journaling**: Tracks signals that were blocked by execution risk for later research.
- **E2E Latency Monitoring**: Automatically halts trading if network jitter exceeds safety thresholds.

## 📦 Getting Started
1. **Environment Setup**:
   ```bash
   conda env create -f environment.yml
   conda activate polymarket-bot
   ```
2. **Configuration**:
   Copy `.env.example` to `.env` and provide your `PRIVATE_KEY` and `FUNDER_ADDRESS`.
   Ensure `MARKET_PROFILE=btc_15m` (default).

3. **Running the Bot**:
   ```bash
   python main.py
   ```

## 📊 Performance Analysis
Run `python scripts/journal_analysis.py` to see your **Fee-Adjusted Actual PnL**. This report breaks down performance by:
- Timing Buckets (How early/late you entered)
- Execution Style (Maker vs Taker vs Expiry)
- Actual-vs-Observed Gap (How much you lost to execution drag)

---
*Note: This system is designed for professional use. Always verify your parameters in dry-run mode before trading live.*
