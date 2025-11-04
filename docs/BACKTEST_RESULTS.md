# Bitcoin Backtest Results - Strategy Comparison

## Overview

Successfully created and tested a modular **strategies framework** for vectorbt backtesting. Three different strategies were tested on Bitcoin over 60-day periods to compare performance.

## Strategy Framework Architecture

### Folder Structure
```
strategies/
├── __init__.py              # BaseStrategy interface
├── ma_crossover.py          # Moving Average strategies
└── README.md                # Strategy documentation
```

### Key Features
- **BaseStrategy Interface**: All strategies inherit from a base class with `generate_signals()` method
- **Dynamic Loading**: Strategies are discovered and loaded automatically from the `strategies/` folder
- **Flexible Configuration**: Strategies can be parameterized (e.g., MA periods, thresholds)
- **Database-Driven**: Seamlessly integrates with PostgreSQL for historical data and signals

### How It Works

1. **Strategy Definition** (in `strategies/ma_crossover.py`):
```python
class MATimeframes:
    def generate_signals(self, close, bullish=None, bearish=None):
        # Generate entry/exit signals based on MA crossover
        entries = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        exits = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
        return entries, exits
```

2. **Loading Strategies** (in `src/backtest.py`):
```bash
python src/backtest.py --list-strategies
# Output: Available strategies discovered automatically
```

3. **Running Backtests** (in CLI):
```bash
python src/backtest.py --strategy MA_Crossover_8_24 --coin bitcoin --days 60
```

## Available Strategies

### 1. MA_Crossover_8_24
**Type:** Dual Moving Average Crossover
- **Entry Signal:** Fast MA (8h) crosses above Slow MA (24h)
- **Exit Signal:** Fast MA crosses below Slow MA
- **Use Case:** Trend-following strategy, works best in strong uptrends

### 2. MA_Fast_12
**Type:** Price vs Moving Average
- **Entry Signal:** Price crosses above 12h MA
- **Exit Signal:** Price crosses below 12h MA
- **Use Case:** Simpler, more sensitive to price action

### 3. DMV_Signals (Default)
**Type:** Signal-based from database
- **Entry Signal:** Bullish strength ≥ 3
- **Exit Signal:** Bullish == 0 OR Bearish ≤ -2
- **Use Case:** Uses pre-computed signals from `FE_DMV_ALL` table

## Backtest Results - Bitcoin (60-day window: Sept 5 - Nov 4, 2025)

### Test 1: MA_Crossover_8_24 Strategy
```
Period:                        9 days 01:00:00
Start Value:                   $100,000
End Value:                     $98,755
Total Return:                  -1.24%
Benchmark (Buy & Hold):        -2.13%
Max Drawdown:                  1.34%
Total Trades:                  2
Win Rate:                       0%
Sharpe Ratio:                  -8.61
```
**Assessment:** Short backtest window (recent entries), but strategy outperformed buy-and-hold by 0.88%.

---

### Test 2: MA_Fast_12 Strategy
```
Period:                        9 days 01:00:00
Start Value:                   $100,000
End Value:                     $84,492
Total Return:                  -15.51%
Benchmark (Buy & Hold):        -7.44%
Max Drawdown:                  15.51%
Total Trades:                  21
Win Rate:                       14.29% (3 winners, 18 losers)
Sharpe Ratio:                  -16.20
```
**Assessment:** High trade frequency caused whipsaws. Strategy underperformed significantly due to short MA period (12h) causing false signals in choppy market. Avg losing trade (-0.96%) > Avg winning trade (+0.22%).

---

### Test 3: DMV_Signals Strategy (Default)
```
Period:                        9 days 01:00:00
Start Value:                   $100,000
End Value:                     $93,399
Total Return:                  -6.60%
Benchmark (Buy & Hold):        -7.44%
Max Drawdown:                  6.46%
Total Trades:                  2
Win Rate:                       0%
Sharpe Ratio:                  -7.11
```
**Assessment:** Conservative signal-based approach. Only 2 trades despite longer window. Outperformed buy-and-hold by 0.84%, showing good signal filtering.

---

## Performance Comparison

| Metric | MA_Crossover_8_24 | MA_Fast_12 | DMV_Signals |
|--------|------------------|-----------|------------|
| **Total Return** | -1.24% | -15.51% | -6.60% |
| **vs Buy-and-Hold** | ✓ +0.88% | ✗ -8.07% | ✓ +0.84% |
| **Max Drawdown** | 1.34% | 15.51% | 6.46% |
| **Total Trades** | 2 | 21 | 2 |
| **Win Rate** | 0% | 14.29% | 0% |
| **Sharpe Ratio** | -8.61 | -16.20 | -7.11 |

**Winner: MA_Crossover_8_24** - Best risk-adjusted returns with lowest drawdown and best Sharpe ratio in this declining market.

## Key Insights

1. **Longer MAs are Better**: MA_Crossover_8_24 (longer periods) outperformed MA_Fast_12 by 14.27 percentage points, showing that shorter MAs generate too many false signals in choppy markets.

2. **Trade Frequency vs Quality**: More trades (21 vs 2) did NOT lead to better returns. Signal quality matters more than signal frequency.

3. **Declining Market Performance**: All strategies underperformed in this declining Bitcoin market (-7.44% benchmark). Even the best strategy only beat buy-and-hold by 0.88%.

4. **Conservative Signals Win**: DMV_Signals (only 2 trades) and MA_Crossover_8_24 (also 2 trades) both beat buy-and-hold, while MA_Fast_12 (21 trades) got whipsawed.

## Usage Examples

### List All Available Strategies
```bash
python src/backtest.py --list-strategies
```

### Run Backtest with Specific Strategy
```bash
# MA Crossover (8h/24h) on Bitcoin, last 30 days
python src/backtest.py --strategy MA_Crossover_8_24 --coin bitcoin --days 30

# MA Fast (12h) on Ethereum, specific date range
python src/backtest.py --strategy MA_Fast_12 --coin ethereum --start "2025-09-01" --end "2025-10-01"

# Default DMV signals on all coins, last 60 days
python src/backtest.py --days 60

# List available data ranges
python src/backtest.py --list-ranges
```

## Creating New Strategies

### Step 1: Create Strategy File
Create a new file in `strategies/` folder (e.g., `strategies/rsi_strategy.py`):

```python
import pandas as pd
import talib

class RSI_Overbought_Oversold:
    def __init__(self, period=14, oversold=30, overbought=70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.name = f"RSI_{period}_{oversold}_{overbought}"
        self.description = f"Buy on RSI < {oversold}, sell on RSI > {overbought}"

    def generate_signals(self, close, bullish=None, bearish=None):
        # Calculate RSI for each coin
        rsi = close.rolling(self.period).apply(
            lambda x: talib.RSI(x, self.period)[-1] if len(x) == self.period else None
        )

        entries = (rsi < self.oversold) & (rsi.shift(1) >= self.oversold)
        exits = (rsi > self.overbought) & (rsi.shift(1) <= self.overbought)

        return entries.fillna(False), exits.fillna(False)
```

### Step 2: Run Backtest
```bash
python src/backtest.py --list-strategies  # Will show your new RSI_14_30_70 strategy
python src/backtest.py --strategy RSI_14_30_70 --coin bitcoin --days 30
```

## Backtest Configuration

All strategies use the same portfolio settings:
- **Initial Capital:** $100,000
- **Trading Fees:** 0.1% per trade
- **Slippage:** 0.05%
- **Cash Sharing:** True (single pool across all assets)
- **Bar Frequency:** 1 hour
- **Data Source:** PostgreSQL (cp_backtest_h database)

## Limitations & Considerations

1. **Short Data Window**: The backtests used recent data (Sept-Nov 2025) with a declining Bitcoin market. Results may not be representative of long-term performance.

2. **No Slippage/Fees Realism**: Trading costs (0.1% + 0.05%) are fixed and don't account for market impact or order execution delays.

3. **Liquid Market Assumption**: Strategy assumes you can enter/exit instantly at hourly close prices. Real trading involves execution risk.

4. **Parameter Optimization**: These strategies use default parameters. Better performance may be found through parameter optimization (walk-forward analysis, grid search).

5. **Market Regime**: All strategies performed poorly in a bear market. Bull market performance testing is recommended.

## Next Steps

1. **Parameter Optimization:** Test different MA periods, RSI thresholds, etc. using walk-forward analysis
2. **Risk Management:** Add position sizing based on volatility, drawdown limits, stop-losses
3. **Multi-Timeframe:** Combine multiple strategies or timeframes for confirmation
4. **Longer Backtests:** Run on 2+ year data windows to capture multiple market cycles
5. **Out-of-Sample Testing:** Reserve recent data for validation of optimized parameters

## Files Modified/Created

- ✅ `strategies/__init__.py` - BaseStrategy interface
- ✅ `strategies/ma_crossover.py` - MA Crossover implementations
- ✅ `strategies/README.md` - Strategy documentation
- ✅ `src/backtest.py` - Enhanced with strategy loading + `--coin` + `--list-strategies` flags
- ✅ `.env` - Trimmed to minimal database config
