# type: ignore
import pandas as pd


def load_price_data(symbols_config):
    """
    Load OHLCV CSVs and align on common timestamps.
    Returns:
        data: dict[symbol -> DataFrame indexed by timestamp]
        common_index: sorted list of timestamps
    """
    data = {}

    for symbol, cfg in symbols_config.items():
        df = (
            pd.read_csv(cfg["file"], parse_dates=["timestamp"])
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
        data[symbol] = df.set_index("timestamp")

    common_index = sorted(set.intersection(*[set(df.index) for df in data.values()]))

    return data, common_index
