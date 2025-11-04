# Trading Strategies

This folder contains reusable trading strategies for vectorbt backtesting. Each strategy implements the `BaseStrategy` interface and can be loaded dynamically by the backtest runner.

## Strategy Structure

Each strategy file should export strategy classes that inherit from `BaseStrategy`:

```python
from strategies import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(name="MyStrategy", description="Description here")

    def generate_signals(self, close, bullish=None, bearish=None):
        # Return (entries, exits) as boolean DataFrames
        return entries, exits
```

## Available Strategies

### MA_Crossover (ma_crossover.py)

Moving Average Crossover strategies with configurable fast and slow periods.

**Variants:**

1. **MATimeframes** - Classic dual MA crossover
   - Fast MA (default 8 hours) vs Slow MA (default 24 hours)
   - Entry: Fast MA crosses above Slow MA
   - Exit: Fast MA crosses below Slow MA
   - Usage: `MATimeframes(fast_period=8, slow_period=24)`

2. **MAOnlyFast** - Simple MA price crossover
   - Entry: Price crosses above MA
   - Exit: Price crosses below MA
   - Default MA period: 12 hours
   - Usage: `MAOnlyFast(fast_period=12)`

**Performance Notes:**
- Works best with trending markets
- Prone to whipsaws in sideways markets
- Can be tuned by adjusting fast/slow periods

## Running Backtests with Strategies

```bash
# List available strategies
python src/backtest.py --list-strategies

# Run backtest with specific strategy
python src/backtest.py --strategy MA_Crossover_8_24 --days 30

# Run backtest with strategy variant
python src/backtest.py --strategy MAOnlyFast_12 --days 30

# Default: uses original DMV signal strategy if no strategy specified
python src/backtest.py --days 30
```

## Creating New Strategies

1. Create a new Python file in the `strategies/` folder
2. Import `BaseStrategy` from `strategies`
3. Implement your strategy class:
   ```python
   from strategies import BaseStrategy
   import pandas as pd

   class MyNewStrategy(BaseStrategy):
       def __init__(self):
           super().__init__(
               name="MyNewStrategy",
               description="Brief description of the strategy"
           )

       def generate_signals(self, close, bullish=None, bearish=None):
           # close: DataFrame (index=timestamp, columns=coin slugs)
           # bullish/bearish: Optional DataFrames with signal strengths

           # Generate boolean entry and exit signals
           entries = ...  # Boolean DataFrame
           exits = ...    # Boolean DataFrame

           return entries, exits
   ```

4. Test with: `python src/backtest.py --strategy MyNewStrategy --days 7`

## Strategy Design Tips

- **Input Data**: `close` is always provided; `bullish`/`bearish` are optional
- **Output Format**: Return boolean DataFrames (True = signal, False = no signal)
- **Handle NaN**: Use `.fillna(False)` to handle edge cases in rolling windows
- **Multi-coin**: Strategies receive data for all coins; return signals for all
- **Avoid Look-ahead Bias**: Don't use future data in signal generation (use `.shift()` if needed)
- **Performance**: Vectorize operations; avoid loops over timestamps/coins

## Backtesting Parameters

All strategies use the same portfolio parameters from `src/backtest.py`:
- Initial cash: $100,000
- Fees: 0.1% per trade
- Slippage: 0.05%
- Cash sharing: True (single pool across all assets)
- Frequency: 1 hour
- Asset filter: Only coins with ≥20 data points in backtest window

## Tips for Strategy Selection

- **Trend Following**: MA Crossover, MACD, ADX-based strategies
- **Mean Reversion**: RSI overbought/oversold, Bollinger Bands
- **Volatility**: ATR-based position sizing, Keltner Channels
- **Signal Integration**: Leverage existing `bullish`/`bearish` columns from database

## Performance Benchmarking

To compare multiple strategies on the same data:

```bash
python src/backtest.py --strategy MATimeframes_8_24 --start "2025-01-01" --end "2025-11-04"
python src/backtest.py --strategy MAOnlyFast_12 --start "2025-01-01" --end "2025-11-04"
```

Compare the output stats (total return, sharpe ratio, max drawdown, etc.)
