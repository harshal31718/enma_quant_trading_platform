# type: ignore
def open_position(
    cash,
    equity,
    price,
    candle_range,
    risk_pct,
    fee_rate,
    slippage_pct,
):
    entry_price = price + candle_range * slippage_pct
    position_value = equity * risk_pct
    fee = position_value * fee_rate
    qty = position_value / entry_price

    if cash < position_value + fee:
        return None

    cash -= position_value + fee

    return {
        "cash": cash,
        "qty": qty,
        "entry_price": entry_price,
        "risk_pct": risk_pct,
    }


def close_position(
    cash,
    qty,
    price,
    candle_range,
    fee_rate,
    slippage_pct,
):
    exit_price = price - candle_range * slippage_pct
    value = qty * exit_price
    fee = value * fee_rate
    cash += value - fee
    return cash
