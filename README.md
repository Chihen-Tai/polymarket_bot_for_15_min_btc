# polymarket-bot-by_openclaw

A high-frequency, event-driven trading bot designed specifically for **Polymarket 5-minute BTC markets (btc-updown-5m)**. 

---

## 🇹🇼 中文說明 (Chinese Documentation)

這個機器人專注於高頻率的 5 分鐘二元期權市場，藉由同步與 **幣安 (Binance) WebSocket** 的訂單流數據，進行極短線的動能預測與套利。本版本已經過大幅度「正期望值 (EV) 最佳化」，以適應微型籌碼（每單 $1 USD）的暴力打法。

### 🚀 核心殺手鐧 (Core Strategies)

*   **WS Flash Snipe (常規動能狙擊)**：監控幣安的資金流與報價陡升，配合計分板 (Scoreboard) 動態評估勝率，自動進場勝率 > 60% 的標的。
*   **Early Underdog Sniper (開局逆勢樂透)**：專注於開局 4 分鐘內的市場，當 Polymarket 報價滯後且低於 $0.35 時，若幣安出現強烈反轉動能 (Velocity Spike)，直接買入便宜的「樂透單」並啟動 3 分鐘死區鎖定 (Lock Mode)，只接受 1.5 倍以上的暴利！

### 🛡️ 極致風控與結算 (Risk & Ev-Optimization)

為了避免在薄弱流動性中被造市商扒皮，我們的風控捨棄了傳統的「分批停損利」，改採**核彈級的一波流策略**：
1.  **100% 全壘打 (Force Full Exit)**：廢除提早賣一半保本的舊機制。一旦達到 40% 或 50% 獲利目標，機器人直接 100% 倉位套現，把手續費與滑價磨損降到最低。
2.  **大逃殺獲利線 (45s Profit Deadline)**：倒數 45 秒時，只要帳面獲利，無條件市價全砸，避免最後關頭的洗盤。
3.  **空城死守機制 (30s Ghost Town Lock)**：倒數 30 秒時如果帳面虧損或打平，強制裝死抱到結算，絕對不丟 FAK 單去撞無法成交的空城訂單簿，保留吃「死貓反彈」翻盤的機會。
4.  **65% 霸王停損 (Wide Stop Loss)**：容忍高達 65% 的洗盤震幅，只在方向完全死亡時才斷頭。

### 📦 安裝與啟動

建議使用 Conda 建立純淨環境：
```bash
git clone https://github.com/Chihen-Tai/polymarket_bot_for_5_min_btc.git
cd polymarket_bot_for_5_min_btc
conda env create -f environment.yml
conda activate polymarket-bot
```

**一鍵啟動（自動背景抓取市場快照資料 + 啟動交易機器人）**：
```bash
bash scripts/start_bot_with_market_data.sh
```
純啟動機器人：`python main.py`

### ⚙️ 設定檔與私鑰 (.env)

*   請複製 `.env.secrets.example` 命名為 `.env.local` 或 `.env.secrets` 來存放私鑰，**切勿將真實私鑰 commit 到 Git！**
*   實盤交易前，請確保：
    *   `DRY_RUN=false`
    *   `SIGNATURE_TYPE` 設定正確 (EOA 填 0，Smart Wallet 填 2)
    *   備有正確的 Polymarket `CLOB_API_KEY` 與 `FUNDER_ADDRESS`。

### 📊 產出與報表

每次執行後，所有日誌與自動生成的摘要報表會存在 `data/` 目錄：
*   最新報表：`data/latest_run_report.txt` (請隨時查看此檔以掌握 PNL)
*   完整交易對帳單：執行 `python scripts/trade_pair_ledger.py --limit 30 --summary`

---

## 🇬🇧 English Documentation

This bot specializes in high-frequency trading for Polymarket's 5-minute binary options, leveraging **Binance WebSocket** order flow data for ultra-short-term momentum prediction. This version has been heavily optimized for "Positive Expected Value (+EV)" with micro-bet sizing ($1 per trade).

### 🚀 Advanced Strategies

*   **WS Flash Snipe**: Monitors Binance order flow and velocity to execute dynamic entries on high-probability setups (>60% model confidence), guided by a real-time strategy scoreboard.
*   **Early Underdog Sniper**: Operates exclusively in the first minute of the market. It buys deeply underpriced options (<= $0.35) when Binance spikes aggressively. These "lottery tickets" are locked for 3 minutes to ride out volatility, targeting a strict 150% profit.

### 🛡️ EV-Optimized Risk Management

To prevent being bled dry by LP fees and slippage in low-liquidity 5-minute markets, we abandoned traditional scaling methods in favor of aggressive, all-or-nothing execution:
1.  **Force Full Exits**: Disables partial scaling. Once the 40% or 50% profit target is hit, the bot dumps 100% of the position via market taker orders to minimize fee drag and eliminate unfillable dust/residuals.
2.  **45s Profit Deadline**: Automatically market-sells any profitable position exactly at 45 seconds remaining to secure bags before market makers pull order book liquidity.
3.  **30s Ghost Town Lock**: Prevents the bot from attempting to panic-dump losing positions in the final 30 seconds when the order book is empty. Losing trades are forced to ride to expiration, preserving the chance of a massive last-second reversal win!
4.  **65% Wide Stop-Loss**: Ignores standard 10-20% volatility, only cutting losses during definitive market death spirals.

### 📦 Installation & Execution

Use Conda for a clean environment:
```bash
git clone https://github.com/Chihen-Tai/polymarket_bot_for_5_min_btc.git
cd polymarket_bot_for_5_min_btc
conda env create -f environment.yml
conda activate polymarket-bot
```

**Run everything (starts market data collector + bot):**
```bash
bash scripts/start_bot_with_market_data.sh
```

### ⚙️ Configuration & Secrets

*   Copy `.env.secrets.example` to `.env.local` to securely store your private keys. **Never commit your keys to Git.**
*   For live trading, ensure:
    *   `DRY_RUN=false`
    *   `SIGNATURE_TYPE` is correctly set (2 for Proxy/Smart Wallets, 0 for EOA).
    *   Valid Polymarket `CLOB_API_KEY` configurations.

### 📊 Reporting

All logs and auto-generated run reports are saved to the `data/` directory:
*   Quick summary: `data/latest_run_report.txt`
*   Full PNL & Ledger: Run `python scripts/trade_pair_ledger.py --summary`
