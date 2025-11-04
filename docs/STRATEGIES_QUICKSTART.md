# Strategies Quick Start Guide

## What's New?

A modular **strategies framework** has been added to the backtest repo. You can now define custom trading strategies, store them in the `strategies/` folder, and test them with vectorbt.

## Quick Example: Test Bitcoin with MA Crossover Strategy

```bash
# List available strategies
python src/backtest.py --list-strategies

# Run Bitcoin backtest (last 30 days) with MA Crossover strategy
python src/backtest.py --strategy MA_Crossover_8_24 --coin bitcoin --days 30

# Run Bitcoin backtest with longer history (60 days)
python src/backtest.py --strategy MA_Crossover_8_24 --coin bitcoin --days 60

# Compare different strategies on same data
python src/backtest.py --strategy MA_Fast_12 --coin bitcoin --days 30
python src/backtest.py --strategy MA_Crossover_8_24 --coin bitcoin --days 30
python src/backtest.py --coin bitcoin --days 30  # Default: DMV Signals
```

## File Structure

```
strategies/
├── __init__.py              # BaseStrategy class
├── ma_crossover.py          # MA-based strategies
└── README.md                # Full strategy documentation
```

## Available Strategies

### 1. MA_Crossover_8_24
**Dual Moving Average Crossover**
- Entry: 8h MA crosses above 24h MA
- Exit: 8h MA crosses below 24h MA
- Best for: Trending markets
- Command: `--strategy MA_Crossover_8_24`

### 2. MA_Fast_12
**Price vs Moving Average**
- Entry: Price crosses above 12h MA
- Exit: Price crosses below 12h MA
- Best for: Sensitive to fast price moves
- Command: `--strategy MA_Fast_12`

### 3. DMV_Signals (Default)
**Database-Driven Signals**
- Uses pre-computed `FE_DMV_ALL` signals from database
- No `--strategy` flag needed
- Conservative, fewer trades

## Create Your Own Strategy (3 Steps)

### Step 1: Create `strategies/your_strategy.py`
```python
from strategies import BaseStrategy
import pandas as pd

class RSI_Strategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="RSI_Strategy",
            description="Buy on RSI oversold, sell on overbought"
        )

    def generate_signals(self, close, bullish=None, bearish=None):
        # Calculate RSI (you'll need talib or implement your own)
        rsi = close.rolling(14).apply(lambda x: your_rsi_function(x))

        # Generate signals
        entries = rsi < 30      # Oversold
        exits = rsi > 70        # Overbought

        return entries, exits
```

### Step 2: Run Backtest
```bash
python src/backtest.py --strategy RSI_Strategy --coin bitcoin --days 30
```

### Step 3: Check Results
The backtest output will show performance metrics (return, Sharpe ratio, max drawdown, etc.)

## Testing Strategy Formula

The backtest framework provides all strategies with:
- Historical OHLCV prices from `ohlcv_1h_250_coins` table
- Historical signals from `FE_DMV_ALL` table (if needed)
- Portfolio simulation with fixed parameters:
  - Initial capital: $100,000
  - Fees: 0.1% per trade
  - Slippage: 0.05%
  - Hourly bars
  - Cash sharing across all assets

## Strategy Ideas to Try

### Trend-Following
- MACD crossover
- Bollinger Bands breakout
- ADX-based entries
- EMA/SMA crossovers with different periods

### Mean Reversion
- RSI overbought/oversold
- Keltner Channel bands
- Stochastic oscillator
- Z-score reversions

### Volatility-Based
- ATR stops and sizing
- Bollinger Band width
- VIX-like indicators
- Gap-based entries/exits

### Multi-Indicator
- Combine multiple indicators with AND/OR logic
- Require confirmation from multiple signals
- Weight signals by strength (from `bullish`/`bearish` columns)

## Backtest Results (Reference)

See `BACKTEST_RESULTS.md` for detailed results from testing three strategies on Bitcoin over 60 days.

**Key Finding**: MA_Crossover_8_24 outperformed both MA_Fast_12 and DMV_Signals in this declining market:
- MA_Crossover_8_24: -1.24% (best)
- DMV_Signals: -6.60%
- MA_Fast_12: -15.51% (worst)

## Common Commands

```bash
# List all strategies
python src/backtest.py --list-strategies

# List available data
python src/backtest.py --list-ranges

# Backtest with strategy and coin
python src/backtest.py --strategy MA_Crossover_8_24 --coin bitcoin --days 30

# Backtest specific date range
python src/backtest.py --strategy MA_Fast_12 --start "2025-09-01 00:00:00" --end "2025-10-01 00:00:00"

# Backtest all coins with strategy
python src/backtest.py --strategy MA_Crossover_8_24 --days 60
```

## Tips for Writing Good Strategies

1. **Avoid Look-Ahead Bias**: Don't use future data in signals
   ```python
   # ❌ Wrong - uses tomorrow's price
   entries = close.shift(-1) > close

   # ✅ Correct - uses only past data
   entries = close > close.shift(1)
   ```

2. **Handle NaN Values**: Indicators produce NaN at the start
   ```python
   entries, exits = strategy.generate_signals(...)
   return entries.fillna(False), exits.fillna(False)
   ```

3. **Return Boolean DataFrames**: Entries/exits must be True/False
   ```python
   # ✅ Correct
   return entries.astype(bool), exits.astype(bool)

   # ❌ Wrong - numeric values instead of bool
   return rsi_values, macd_values
   ```

4. **Vectorize Operations**: Use pandas/numpy, avoid loops
   ```python
   # ✅ Fast - vectorized
   entries = (ma_fast > ma_slow) & (ma_fast.shift(1) <= ma_slow.shift(1))

   # ❌ Slow - loops over each row
   entries = pd.DataFrame(index=close.index)
   for t in range(len(close)):
       entries.iloc[t] = ...
   ```

5. **Test Multiple Timeframes**: Try different MA periods, thresholds, etc.
   ```bash
   python src/backtest.py --strategy MA_Crossover_5_15 --coin bitcoin --days 30
   python src/backtest.py --strategy MA_Crossover_12_24 --coin bitcoin --days 30
   python src/backtest.py --strategy MA_Crossover_20_50 --coin bitcoin --days 30
   ```

## Debugging Strategies

If your strategy produces no signals:
```bash
# Check if data loaded correctly
python src/backtest.py --list-ranges

# Check if coin exists
python src/backtest.py --coin nonexistent_coin --days 30
# Will show available coins

# Add print statements in your strategy
class DebugStrategy(BaseStrategy):
    def generate_signals(self, close, bullish=None, bearish=None):
        print(f"Close shape: {close.shape}")
        print(f"Close values (first 5): {close.iloc[:5, 0]}")
        entries = ...
        print(f"Entries shape: {entries.shape}")
        print(f"Total entries: {entries.sum().sum()}")
        return entries, exits
```

## Next Steps

1. **Read full documentation**: See `strategies/README.md` for detailed info
2. **Run example strategies**: Test MA_Crossover_8_24 and MA_Fast_12 on different coins
3. **Create your own**: Pick a simple indicator and implement it
4. **Optimize parameters**: Try different periods and thresholds
5. **Backtest longer**: Test on multiple months/years of data
6. **Walk-forward analysis**: Reserve recent data for validation

## More Info

- **Strategies README**: `strategies/README.md`
- **Backtest Results**: `BACKTEST_RESULTS.md`
- **Full Documentation**: `CLAUDE.md`
- **Source Code**: `src/backtest.py`, `strategies/`
