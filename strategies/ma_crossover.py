"""Simple Moving Average Crossover Strategy."""

import pandas as pd
from . import BaseStrategy


class MATimeframes:
    """Moving Average Crossover strategy with fast and slow timeframes."""

    def __init__(self, fast_period: int = 8, slow_period: int = 24):
        """
        Initialize MA Crossover strategy.

        Args:
            fast_period: Period for fast moving average (default 8 hours)
            slow_period: Period for slow moving average (default 24 hours)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.name = f"MA_Crossover_{fast_period}_{slow_period}"
        self.description = f"Moving Average Crossover ({fast_period}h fast, {slow_period}h slow)"

    def generate_signals(
        self, close: pd.DataFrame, bullish: pd.DataFrame = None, bearish: pd.DataFrame = None, **kwargs
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate entry and exit signals based on MA crossover.

        Entry: Fast MA crosses above Slow MA
        Exit: Fast MA crosses below Slow MA
        """
        # Calculate moving averages for each coin
        fast_ma = close.rolling(window=self.fast_period).mean()
        slow_ma = close.rolling(window=self.slow_period).mean()

        # Generate entry signals (fast MA > slow MA and was not before)
        entries = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))

        # Generate exit signals (fast MA < slow MA and was not before)
        exits = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))

        return entries.fillna(False), exits.fillna(False)


class MAOnlyFast(BaseStrategy):
    """Simple strategy: only use fast MA as signal."""

    def __init__(self, fast_period: int = 12):
        super().__init__(
            name=f"MA_Fast_{fast_period}",
            description=f"Buy when price > {fast_period}h MA, sell when below"
        )
        self.fast_period = fast_period

    def generate_signals(
        self, close: pd.DataFrame, bullish: pd.DataFrame = None, bearish: pd.DataFrame = None, **kwargs
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Simple strategy: buy when above MA, sell when below.
        """
        fast_ma = close.rolling(window=self.fast_period).mean()

        entries = (close > fast_ma) & (close.shift(1) <= fast_ma.shift(1))
        exits = (close < fast_ma) & (close.shift(1) >= fast_ma.shift(1))

        return entries.fillna(False), exits.fillna(False)
