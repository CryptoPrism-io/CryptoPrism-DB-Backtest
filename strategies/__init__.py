"""Strategy package for backtesting."""

from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    """Base class for trading strategies."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def generate_signals(
        self, close: pd.DataFrame, bullish: pd.DataFrame = None, bearish: pd.DataFrame = None, **kwargs
    ) -> tuple:
        """
        Generate entry and exit signals.

        Args:
            close: DataFrame with close prices (index=timestamp, columns=slug)
            bullish: Optional DataFrame with bullish signals
            bearish: Optional DataFrame with bearish signals
            **kwargs: Optional additional data (e.g., ratios dict with 'alpha', 'beta', 'omega')

        Returns:
            Tuple of (entries, exits) for long-only strategies (2-tuple)
            or (long_entries, long_exits, short_entries, short_exits) for long/short strategies (4-tuple)
            All as boolean DataFrames
        """
        pass

    def __repr__(self) -> str:
        return f"{self.name}: {self.description}"
