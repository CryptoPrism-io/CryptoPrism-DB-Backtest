"""Sentiment-based trading strategies with ratio filters (from socials.io logic)."""

import pandas as pd
from . import BaseStrategy


class SentimentLongStrategy(BaseStrategy):
    """
    Long-only strategy based on bullish sentiment and ratio filtering.

    Replicates the socials.io long strategy logic:
    - Entry: bullish >= threshold AND d_rat_beta > 1 AND m_rat_omega > 1
    - Exit: bullish drops below threshold OR ratio conditions violated
    """

    def __init__(
        self,
        bullish_threshold: int = 3,
        min_d_rat_beta: float = 1.0,
        min_m_rat_omega: float = 1.0,
        exit_buffer: float = 0.8,
    ):
        """
        Initialize Long sentiment strategy.

        Args:
            bullish_threshold: Bullish signal strength to enter (default 3)
            min_d_rat_beta: Minimum d_rat_beta for entering (default > 1)
            min_m_rat_omega: Minimum m_rat_omega for entering (default > 1)
            exit_buffer: Exit threshold = threshold * exit_buffer (default 0.8)
        """
        self.bullish_threshold = bullish_threshold
        self.min_d_rat_beta = min_d_rat_beta
        self.min_m_rat_omega = min_m_rat_omega
        self.exit_threshold = bullish_threshold * exit_buffer

        self.name = f"SentimentLong_{bullish_threshold}_{min_d_rat_beta}_{min_m_rat_omega}"
        self.description = (
            f"Long on bullish>={bullish_threshold} + beta>{min_d_rat_beta} + omega>{min_m_rat_omega}"
        )

    def generate_signals(self, close, bullish=None, bearish=None, **kwargs):
        """
        Generate long entry/exit signals based on bullish sentiment + ratio filters.

        Returns: (entries, exits) as 2-tuple for long-only strategy
        """
        ratios = kwargs.get('ratios')

        # Entry conditions
        bullish_condition = bullish >= self.bullish_threshold

        if ratios:
            beta_condition = ratios['beta'] > self.min_d_rat_beta
            omega_condition = ratios['omega'] > self.min_m_rat_omega
            long_entries = bullish_condition & beta_condition & omega_condition
        else:
            # If no ratios available, use only bullish signal
            long_entries = bullish_condition

        # Exit conditions
        exit_bullish = bullish < self.exit_threshold
        long_exits = exit_bullish

        if ratios:
            # Also exit if ratios drop below thresholds
            exit_beta = ratios['beta'] <= (self.min_d_rat_beta * 0.9)
            exit_omega = ratios['omega'] <= (self.min_m_rat_omega * 0.9)
            long_exits = long_exits | exit_beta | exit_omega

        return long_entries.fillna(False), long_exits.fillna(False)


class SentimentShortStrategy(BaseStrategy):
    """
    Short-only strategy based on bearish sentiment and ratio filtering.

    Replicates the socials.io short strategy logic:
    - Entry: bearish >= threshold AND d_rat_beta > 1 AND m_rat_omega < 2
    - Exit: bearish drops below threshold OR ratio conditions violated
    """

    def __init__(
        self,
        bearish_threshold: int = 3,
        min_d_rat_beta: float = 1.0,
        max_m_rat_omega: float = 2.0,
        exit_buffer: float = 0.8,
    ):
        """
        Initialize Short sentiment strategy.

        Args:
            bearish_threshold: Bearish signal strength to short (default 3)
            min_d_rat_beta: Minimum d_rat_beta for shorting (default > 1)
            max_m_rat_omega: Maximum m_rat_omega for shorting (default < 2)
            exit_buffer: Exit threshold = threshold * exit_buffer (default 0.8)
        """
        self.bearish_threshold = bearish_threshold
        self.min_d_rat_beta = min_d_rat_beta
        self.max_m_rat_omega = max_m_rat_omega
        self.exit_threshold = bearish_threshold * exit_buffer

        self.name = f"SentimentShort_{bearish_threshold}_{min_d_rat_beta}_{max_m_rat_omega}"
        self.description = (
            f"Short on bearish>={bearish_threshold} + beta>{min_d_rat_beta} + omega<{max_m_rat_omega}"
        )

    def generate_signals(self, close, bullish=None, bearish=None, **kwargs):
        """
        Generate short entry/exit signals based on bearish sentiment + ratio filters.

        Returns: (entries, exits) as 2-tuple for long-only (we'll convert to shorts in run_vbt)

        Note: For true short signals, this would return a 4-tuple.
        For now, return empty long signals to avoid long trades.
        """
        ratios = kwargs.get('ratios')

        # Entry conditions for shorting
        bearish_condition = bearish >= self.bearish_threshold

        if ratios:
            beta_condition = ratios['beta'] > self.min_d_rat_beta
            omega_condition = ratios['omega'] < self.max_m_rat_omega
            short_entries = bearish_condition & beta_condition & omega_condition
        else:
            # If no ratios available, use only bearish signal
            short_entries = bearish_condition

        # Exit conditions for shorts
        exit_bearish = bearish < self.exit_threshold
        short_exits = exit_bearish

        if ratios:
            # Also exit shorts if ratios conditions violated
            exit_beta = ratios['beta'] <= (self.min_d_rat_beta * 0.9)
            exit_omega = ratios['omega'] >= (self.max_m_rat_omega * 1.1)
            short_exits = short_exits | exit_beta | exit_omega

        # Return as 4-tuple for long/short: (long_entries, long_exits, short_entries, short_exits)
        # No long trades, only shorts
        long_entries = pd.DataFrame(False, index=close.index, columns=close.columns)
        long_exits = pd.DataFrame(False, index=close.index, columns=close.columns)

        return long_entries, long_exits, short_entries.fillna(False), short_exits.fillna(False)


class SentimentLongShortStrategy(BaseStrategy):
    """
    Combined long/short strategy based on sentiment and ratio filtering.

    Combines both:
    - Longs: bullish >= threshold AND d_rat_beta > 1 AND m_rat_omega > 1
    - Shorts: bearish >= threshold AND d_rat_beta > 1 AND m_rat_omega < 2

    Prevents simultaneous long+short on same asset.
    """

    def __init__(
        self,
        bullish_threshold: int = 3,
        bearish_threshold: int = 3,
        min_d_rat_beta: float = 1.0,
        min_m_rat_omega_long: float = 1.0,
        max_m_rat_omega_short: float = 2.0,
        exit_buffer: float = 0.8,
    ):
        """
        Initialize LongShort sentiment strategy.

        Args:
            bullish_threshold: Bullish signal strength to enter long (default 3)
            bearish_threshold: Bearish signal strength to enter short (default 3)
            min_d_rat_beta: Minimum d_rat_beta for both long and short (default > 1)
            min_m_rat_omega_long: Minimum m_rat_omega for longs (default > 1)
            max_m_rat_omega_short: Maximum m_rat_omega for shorts (default < 2)
            exit_buffer: Exit threshold = threshold * exit_buffer (default 0.8)
        """
        self.bullish_threshold = bullish_threshold
        self.bearish_threshold = bearish_threshold
        self.min_d_rat_beta = min_d_rat_beta
        self.min_m_rat_omega_long = min_m_rat_omega_long
        self.max_m_rat_omega_short = max_m_rat_omega_short
        self.exit_buffer = exit_buffer

        self.bullish_exit = bullish_threshold * exit_buffer
        self.bearish_exit = bearish_threshold * exit_buffer

        self.name = f"SentimentLongShort_{bullish_threshold}_{bearish_threshold}"
        self.description = f"Long/Short on bullish/bearish signals with ratio filters"

    def generate_signals(self, close, bullish=None, bearish=None, **kwargs):
        """
        Generate combined long/short entry/exit signals.

        Returns: (long_entries, long_exits, short_entries, short_exits) as 4-tuple
        """
        ratios = kwargs.get('ratios')

        # ===== LONG SIGNALS =====
        bullish_cond = bullish >= self.bullish_threshold
        if ratios:
            beta_cond = ratios['beta'] > self.min_d_rat_beta
            omega_long_cond = ratios['omega'] > self.min_m_rat_omega_long
            long_entries = bullish_cond & beta_cond & omega_long_cond
        else:
            long_entries = bullish_cond

        # Exit longs
        exit_bullish = bullish < self.bullish_exit
        long_exits = exit_bullish
        if ratios:
            exit_beta = ratios['beta'] <= (self.min_d_rat_beta * 0.9)
            exit_omega_long = ratios['omega'] <= (self.min_m_rat_omega_long * 0.9)
            long_exits = long_exits | exit_beta | exit_omega_long

        # ===== SHORT SIGNALS =====
        bearish_cond = bearish >= self.bearish_threshold
        if ratios:
            beta_cond = ratios['beta'] > self.min_d_rat_beta
            omega_short_cond = ratios['omega'] < self.max_m_rat_omega_short
            short_entries = bearish_cond & beta_cond & omega_short_cond
        else:
            short_entries = bearish_cond

        # Exit shorts
        exit_bearish = bearish < self.bearish_exit
        short_exits = exit_bearish
        if ratios:
            exit_beta = ratios['beta'] <= (self.min_d_rat_beta * 0.9)
            exit_omega_short = ratios['omega'] >= (self.max_m_rat_omega_short * 1.1)
            short_exits = short_exits | exit_beta | exit_omega_short

        # ===== PREVENT SIMULTANEOUS LONG+SHORT =====
        # If both long and short conditions are true, prioritize long (preference can be changed)
        simultaneous = long_entries & short_entries
        short_entries = short_entries & ~simultaneous

        return (
            long_entries.fillna(False),
            long_exits.fillna(False),
            short_entries.fillna(False),
            short_exits.fillna(False),
        )
