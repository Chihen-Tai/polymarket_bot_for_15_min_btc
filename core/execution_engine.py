from __future__ import annotations
from typing import List, Dict, Any

def get_vwap_from_ladder(ladder: List[Dict[str, Any]], size_usd: float) -> float:
    """
    模擬在訂單簿梯次中成交特定金額的 VWAP。
    如果深度不足以支撐該金額，回傳 999.0 (代表成本無窮大)。
    """
    if not ladder:
        return 999.0
        
    cumulative_usd = 0.0
    cumulative_shares = 0.0
    
    for level in ladder:
        price = float(level['price'])
        shares = float(level['size'])
        level_usd = price * shares
        
        if cumulative_usd + level_usd >= size_usd:
            needed_usd = size_usd - cumulative_usd
            cumulative_shares += (needed_usd / price)
            return size_usd / cumulative_shares
            
        cumulative_usd += level_usd
        cumulative_shares += shares
        
    return 999.0

def calculate_polymarket_fee(price: float, size_usd: float) -> float:
    """
    官方費率公式: Fee = Amount * feeRate * p * (1-p)
    feeRate 固定為 0.0156 (156 bps)。
    """
    fee_rate = 0.0156
    # p * (1-p) 在 0.5 時達到最大值 0.25
    return float(size_usd * fee_rate * price * (1.0 - price))

def calculate_committed_edge(
    fair_value: float, 
    ob_up: Dict[str, Any], 
    ob_down: Dict[str, Any], 
    order_size_usd: float, 
    side: str
) -> float:
    """
    計算「承諾邊際」。
    邊際 = 期望價值 - 入場成本 - (進場費 + 出場費) - 延遲緩衝
    """
    safety_buffer = 0.01 # 1% 靜態緩衝
    
    if side == "UP":
        entry_price = get_vwap_from_ladder(ob_up.get('asks', []), order_size_usd)
        if entry_price > 1.0: return -1.0
        
        # 官方費率計算 (進場與預期出場)
        entry_fee = calculate_polymarket_fee(entry_price, order_size_usd) / order_size_usd
        # 出場假設到期 (費率為 0)，若非到期則需額外計算
        total_fees = entry_fee 
        
        ev_expiry = fair_value
        edge = ev_expiry - entry_price - total_fees - safety_buffer
    else:
        entry_price = get_vwap_from_ladder(ob_down.get('asks', []), order_size_usd)
        if entry_price > 1.0: return -1.0
        
        entry_fee = calculate_polymarket_fee(entry_price, order_size_usd) / order_size_usd
        total_fees = entry_fee
        
        ev_expiry = 1.0 - fair_value
        edge = ev_expiry - entry_price - total_fees - safety_buffer
        
    return float(edge)
