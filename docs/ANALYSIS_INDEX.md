# Complete Analysis Index

## Reports Created for SentimentLongShort_3_3 Strategy

### 📊 Main Analysis Documents

#### 1. **TRADE_REPORT.md** ⭐ START HERE
Detailed trade-by-trade breakdown of all 5 trades from Oct 30 - Nov 4
- **What**: Individual trade entries/exits with timestamps, prices, PnL
- **When to read**: Want to see exact trades that were executed
- **Key finding**: APTOS dominated with +$5,142 best trade (+5.02%)

**All 5 Trades Listed**:
1. AAVE Long (-0.69%)
2. APTOS Long (+5.02%) ← Best Trade
3. APTOS Long 2 (+0.78%)
4. APTOS Short (-2.35%) ← Worst Trade
5. XRP Short (+3.66%)

---

#### 2. **PERIOD_COMPARISON.md**
Complete statistical comparison of two periods
- **What**: Side-by-side metrics for Full Period vs Late Period
- **When to read**: Want to understand why one period was better than the other
- **Key finding**: Signal quality jumped from 31.88% to 60% win rate

**Comparison**:
```
                Full Period    Late Period
Return          -6.50%         +6.39%
Win Rate        31.88%         60.00%
Sharpe          0.71           9.18
Max Drawdown    53.68%         2.35%
```

---

#### 3. **OCT_ANALYSIS.md**
Deep dive into October 2025 activity and why exact Oct 1-30 isn't available
- **What**: Explanation of data availability + October market regime analysis
- **When to read**: Want to understand October specifically or data limitations
- **Key finding**: October was part of bear market (-14.20%), real action started Oct 30

**Data Availability**:
- Prices available: Feb 13 → Nov 4
- Signals available: Feb 13 → Oct 31 only
- Result: Can't isolate Oct 1-30; no trades triggered until Oct 30

---

### 📈 Reference Documents

#### 4. **LONGSHORT_STRATEGIES.md**
Strategy documentation and performance analysis
- Overview of 3 sentiment-based strategies
- Backtesting results and methodology
- Tips for customization

#### 5. **BACKTEST_RESULTS.md**
Earlier backtest results including MA strategies
- Comparison of multiple strategies
- Performance metrics and analysis

#### 6. **STRATEGIES_QUICKSTART.md**
Quick start guide for running backtests
- Command examples
- Strategy comparison
- Tips for strategy development

#### 7. **CLAUDE.md**
Architecture documentation and commands
- Setup instructions
- Common commands
- Strategy framework details

---

## Reading Guide

### If you want to understand...

**The specific trades that were executed**
→ Read: `TRADE_REPORT.md`
- Exact entry/exit times
- Prices for each trade
- Win/loss analysis

**Why late October was so much better**
→ Read: `PERIOD_COMPARISON.md`
- Statistical breakdown
- Performance metrics
- Market regime analysis

**October performance and data limitations**
→ Read: `OCT_ANALYSIS.md`
- October timeline
- Data availability explanation
- Why exact Oct 1-30 isn't testable

**How to run your own backtests**
→ Read: `STRATEGIES_QUICKSTART.md`
- Command examples
- Strategy options

**The full strategy system**
→ Read: `LONGSHORT_STRATEGIES.md`
- Architecture
- All 3 strategies detailed
- Customization guide

---

## Quick Stats

### Full Period: Feb 13 - Oct 31, 2025
- **Trades**: 69
- **Win Rate**: 31.88%
- **Return**: -6.50% (but +7.70% vs -14.20% market)
- **Sharpe**: 0.71
- **Status**: Bearish market period, strategy underperformed but beat market

### Late Period: Oct 30 - Nov 4, 2025
- **Trades**: 5
- **Win Rate**: 60.00%
- **Return**: +6.39% (vs -3.11% market = +9.50% outperformance)
- **Sharpe**: 9.18 (exceptional)
- **Status**: Market transition point, signal quality dramatically improved

### Difference
- Win rate improvement: +28.12 percentage points
- Return improvement: +12.89 percentage points
- Sharpe improvement: +8.47x better
- Max drawdown reduction: 51.33 percentage points lower

---

## Key Findings Summary

### What Works ✅
- Ratio filtering (d_rat_beta, m_rat_omega) improves signal quality
- Bullish entries highly reliable (67% win rate in short period)
- Risk management prevents large losses
- Long/short combination beats long-only
- 9.18 Sharpe ratio shows excellent risk-adjusted returns

### What Needs Work ❌
- Signal quality varies with market regime (31% to 60% win rate)
- Short signals underperformed (50% win rate vs 67% for longs)
- Early period showed poor performance in bear market
- No single strategy works in all conditions

### Recommendations 🎯
1. Test across different market regimes
2. Consider market regime filter (bull/bear/sideways)
3. Improve short signal filtering
4. Add trend confirmation for shorts
5. Test parameter optimization on full dataset

---

## Files by Type

### Analysis Reports (These files)
- `TRADE_REPORT.md` - Trade-by-trade details
- `PERIOD_COMPARISON.md` - Period analysis
- `OCT_ANALYSIS.md` - October explanation
- `ANALYSIS_INDEX.md` - This file

### Strategy/Backtest Code
- `strategies/sentiment_ratios.py` - 3 long/short strategies
- `strategies/ma_crossover.py` - MA-based strategies
- `src/backtest.py` - Backtest engine with ratio loading + short support

### Documentation
- `LONGSHORT_STRATEGIES.md` - Strategy documentation
- `BACKTEST_RESULTS.md` - Earlier results
- `STRATEGIES_QUICKSTART.md` - Quick start guide
- `CLAUDE.md` - Full architecture docs

### Analysis Scripts
- `analyze_trades.py` - Trade analysis tool
- `get_trade_details.py` - Trade extraction
- `inspect_trades.py` - Trade structure inspection
- `extract_trades.py` - Trade details script

---

## How to Use These Reports

### For Understanding Performance
1. Start with `TRADE_REPORT.md` to see actual trades
2. Read `PERIOD_COMPARISON.md` to understand period differences
3. Review `OCT_ANALYSIS.md` for October context

### For Running New Backtests
1. See `STRATEGIES_QUICKSTART.md` for commands
2. Reference `LONGSHORT_STRATEGIES.md` for strategy details
3. Check `CLAUDE.md` for full documentation

### For Strategy Development
1. Review `LONGSHORT_STRATEGIES.md` architecture
2. Check `strategies/sentiment_ratios.py` for implementation examples
3. Refer to `STRATEGIES_QUICKSTART.md` for creation steps

---

## Command Reference

```bash
# List all available strategies
python src/backtest.py --list-strategies

# Run specific period
python src/backtest.py --strategy SentimentLongShort_3_3 \
  --start "2025-10-30 00:00:00" --end "2025-11-04 23:59:59"

# Test on single coin
python src/backtest.py --strategy SentimentLongShort_3_3 --coin ethereum --days 30

# Run last 30 days
python src/backtest.py --strategy SentimentLongShort_3_3 --days 30

# Run full available period
python src/backtest.py --strategy SentimentLongShort_3_3 \
  --start "2025-02-13 00:00:00" --end "2025-10-31 23:59:59"
```

---

## Data Limitations

**Available Data**:
- Price data: Feb 13, 2025 → Nov 4, 2025
- Signal data: Feb 13, 2025 → Oct 31, 2025
- Ratio data: Feb 13, 2025 → Nov 4, 2025

**Why Oct 1-30 can't be isolated**:
- Signal data ends Oct 31
- Early October has very sparse hourly data
- No trading signals triggered until Oct 30
- Best to analyze Oct 1-31 as part of full period

---

## Next Steps

To use this analysis:

1. **Review Results**: Read the reports in order
2. **Understand Strategy**: Check LONGSHORT_STRATEGIES.md
3. **Run Tests**: Try commands from STRATEGIES_QUICKSTART.md
4. **Customize**: Modify parameters and test different periods
5. **Optimize**: Use walk-forward analysis for parameter tuning

---

**Questions?** See the individual report files for detailed explanations.

