def calculate_position(entry_price: float, leverage: float, balance: float):
    position_size = balance * leverage
    liquidation_price = entry_price - (entry_price * (1 / leverage)) if leverage != 0 else 0
    return {
        "position_size": position_size,
        "liquidation_price": liquidation_price
    }