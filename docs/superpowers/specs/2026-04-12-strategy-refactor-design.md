# Strategy Layer Refactor & Research Framework Design

## 1. 概述 (Overview)
本文件詳細說明 Polymarket 交易機器人策略層的重構方案。目標是將現有的單體式 `decision_engine.py` 拆解為獨立、可測試、可量化的策略模塊，並建立嚴謹的研究歸因管道，以識別具備真實正期望值 (Positive Expectancy) 的組件。

## 2. 核心架構 (Core Architecture)

### 2.1 策略模塊化 (Strategy Modularization)
所有策略將遷移至 `core/strategies/` 目錄。每個策略家族 (Family) 必須繼承或符合統一的接口。

**標準輸出 Schema (`StrategyResult`):**
```python
{
    "strategy_name": str,           # 例如 "ws_order_flow"
    "side": str,                    # "UP" | "DOWN"
    "trigger_reason": str,          # 詳細觸發原因
    "entry_price": float,           # 觸發時的價格
    "model_probability": float,     # 原始模型勝率 (0.0-1.0)，嚴禁人工膨脹
    "confidence": float,            # 信號置信度 (0.0-1.0)
    "required_edge": float,         # 該策略要求的最低 Edge (考慮滑點/風險)
    "raw_edge": float,              # model_probability - entry_price
    "execution_preference": str,    # "maker" | "taker" | "hybrid"
    "metadata": dict                # 策略特有的原始數據 (如 OFI ratio)
}
```

### 2.2 去中心化決策 (Decoupled Decision Engine)
`decision_engine.py` 將轉變為「協調器 (Orchestrator)」，負責：
1. 調用已啟用的策略模塊。
2. 收集所有 `StrategyResult`。
3. 根據 `raw_edge` 與 `confidence` 進行排序與過濾。
4. **移除所有硬編碼的概率膨脹邏輯**（如 `_MOMENTUM_EXEMPT` 中的加成）。

## 3. 退出狀態機 (Exit State Machine)
簡化 `trade_manager.py`，將 30+ 條重疊規則歸納為以下狀態遷移：

- **FRESH_ENTRY**: 進場前 10 秒，觀察滑點與初始動量。
- **SOFT_PROFIT**: 盈利達到門檻（如 20%），啟動移動止盈或本金回收邏輯。
- **PRINCIPAL_EXTRACTED**: 已賣出足夠份額收回本金，剩餘部分為 Moonbag，僅受劇烈回撤 (Drawdown) 控制。
- **EMERGENCY_LOSS**: 觸發硬止損或信號反轉。
- **EXPIRY_HOLD**: 距離到期極近，根據邊際成本決定是否持有至結算。

## 4. 研究與歸因 (Research & Attribution)

### 4.1 歸因日誌 (Attribution Logging)
擴展 `core/journal.py`，每筆交易必須記錄：
- `signal_price`: 觸發信號時的報價。
- `fill_price`: 實際成交均價。
- `slippage`: (fill_price - signal_price) / signal_price。
- `hedging_cost`: 相關聯的對沖成本。
- `exit_reason`: 精確的狀態機退出原因。

### 4.2 績效報告 (`scripts/research_report.py`)
產出按以下維度桶化的報告：
- **Strategy**: 每個策略的勝率、平均滑點、費後 PnL。
- **Seconds-to-Expiry**: 距離到期時間（如 <60s, 60-120s, >120s）。
- **Price Bucket**: 進入價格（如 <0.2, 0.2-0.5, >0.5）。
- **Taker vs Maker**: 執行質量對比。

## 5. 實施優先級 (Priority)
1. **[High]** 建立 `core/strategies/` 基礎結構與標準 Schema。
2. **[High]** 提取 `ws_order_flow` 與 `ws_flash_snipe` (核心潛力策略)。
3. **[Medium]** 重構 `trade_manager.py` 狀態機。
4. **[Medium]** 移除所有 `decision_engine.py` 中的概率補償。
5. **[Low]** 建立歸因報告工具。

## 6. 驗證標準 (Success Criteria)
- 能夠在不修改主邏輯的情況下，通過單元測試驗證 `ws_order_flow` 的觸發邏輯。
- 系統日誌中不再出現「為了過濾而手動調整概率」的記錄。
- 報告能清晰顯示：在考慮滑點後，`early_underdog` 是否真正盈利。
