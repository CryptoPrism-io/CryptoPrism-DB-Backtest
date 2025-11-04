# CryptoPrism-DB-Backtest

<div align="center">

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Vectorbt](https://img.shields.io/badge/Vectorbt-Latest-green?style=for-the-badge)](https://github.com/polapy/vectorbt)
[![PostgreSQL 12+](https://img.shields.io/badge/PostgreSQL-12%2B-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red?style=for-the-badge)](https://www.sqlalchemy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Latest-150458?style=for-the-badge&logo=pandas)](https://pandas.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**Sentiment-Based Long/Short Cryptocurrency Backtesting Framework**

Vectorized backtesting engine with modular trading strategies, ratio filtering, and comprehensive analysis tools.

[Quick Start](#quick-start) • [Features](#key-features) • [Strategies](#sentiment-based-strategies) • [Docs](docs/ANALYSIS_INDEX.md) • [Results](#performance-results)

</div>

---

## 📋 Table of Contents

- [What's New](#whats-new)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Technology Stack](#technology-stack)
- [Sentiment-Based Strategies](#sentiment-based-strategies)
- [System Architecture](#system-architecture)
- [Performance Results](#performance-results)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

---

## 🎯 What's New

**v1.0.0** - Production Release: Sentiment-Based Long/Short Framework
- ✅ 3 sentiment-based long/short strategies with ratio filtering
- ✅ Extended vectorbt engine supporting 4-tuple (long/short) signals
- ✅ Ratio-based entry validation using FE_RATIOS data
- ✅ Comprehensive trade analysis framework with 4 utility scripts
- ✅ Full documentation suite with analysis guides and trade reports
- ✅ Repository organization with docs/, analysis/, and strategies/ folders
- ✅ Production-ready with clean git history and GitHub integration

**Previous Release** - Initial Scaffold:
- Vectorbt backtest runner with PostgreSQL integration
- QA and maintenance scripts
- GitHub Actions CI/CD workflows

---

## 🚀 Key Features

### 1. **Sentiment-Based Strategies with Ratio Filtering**
- **SentimentLongStrategy**: Bullish signals with beta/omega validation
- **SentimentShortStrategy**: Bearish signals with refined ratio thresholds
- **SentimentLongShortStrategy**: Combined long/short with mutual exclusion
- Customizable entry/exit thresholds and ratio parameters
- Real-time ratio data from FE_RATIOS table with forward-fill support

### 2. **Extended Vectorbt Engine**
- Support for 2-tuple (long-only) and 4-tuple (long/short) signal formats
- Automatic strategy discovery and dynamic loading from `strategies/` folder
- CLI arguments for strategy selection, coin filtering, and ratio tables
- Ratio data loading with missing value handling
- Backward compatible with existing strategies

### 3. **Multi-Strategy Framework**
- **Moving Average Strategies**: MATimeframes (8h/24h dual crossover), MAOnlyFast
- **Sentiment Strategies**: 3 long/short combinations with ratio filters
- **Extensible Architecture**: Create custom strategies by extending BaseStrategy
- Clean interface with flexible **kwargs support

### 4. **Comprehensive Analysis Tools**
- Trade extraction and detailed analysis scripts
- Trade-by-trade breakdown with timestamps, prices, and PnL
- Period comparison framework for regime analysis
- Portfolio performance metrics (Sharpe, Profit Factor, Win Rate, Drawdown)
- CSV export functionality for further analysis

### 5. **Production-Ready Pipeline**
- Strict DB-only validation with clear error messages
- PostgreSQL integration (cp_ai → cp_backtest_h)
- Automated data alignment and filtering
- Uniqueness enforcement and duplicate handling
- QA checks for data consistency

### 6. **Comprehensive Documentation**
- Full architecture guide (CLAUDE.md)
- Strategy documentation with examples
- Detailed trade reports with performance analysis
- Period comparison studies
- Quick start guide for users
- Master navigation index

---

## ⚡ Quick Start

### Prerequisites
```bash
# System Requirements
- Python 3.12+
- PostgreSQL 12+
- Git

# Environment Variables (.env)
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=cp_ai
DB_NAME_BT=cp_backtest_h
```

### Installation

**1. Clone and Setup Environment**
```bash
git clone https://github.com/CryptoPrism-io/CryptoPrism-DB-Backtest.git
cd CryptoPrism-DB-Backtest

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -U pip
pip install -r requirements.txt
```

**2. Configure Database**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your PostgreSQL credentials
# Required: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_NAME_BT
```

**3. Verify Data Availability**
```bash
# Check available date ranges
python src/backtest.py --list-ranges

# Run QA checks
python scripts/qa/check_sync_last3days.py
```

**4. Run Backtest**
```bash
# List available strategies
python src/backtest.py --list-strategies

# Run full period backtest
python src/backtest.py --strategy SentimentLongShort_3_3 \
  --start "2025-02-13 00:00:00" --end "2025-10-31 23:59:59"

# Test on single coin
python src/backtest.py --strategy SentimentLongShort_3_3 --coin bitcoin --days 30

# Run last 30 days
python src/backtest.py --strategy SentimentLongShort_3_3 --days 30
```

---

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Language** | Python | 3.12+ |
| **Backtesting** | Vectorbt | Latest |
| **Database** | PostgreSQL | 12+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **Data Processing** | Pandas | Latest |
| **Numerical** | NumPy | Latest |
| **Async** | Python-dotenv | Latest |

---

## 📊 Sentiment-Based Strategies

### Strategy Architecture

```
Market Data (OHLCV)
       ↓
┌──────────────────────────────┐
│  Sentiment Signals (DMV)     │
│  - Bullish Signal (0-5)      │
│  - Bearish Signal (0-5)      │
└──────────┬───────────────────┘
           ↓
┌──────────────────────────────┐
│  Ratio Data (FE_RATIOS)      │
│  - d_rat_beta                │
│  - m_rat_omega               │
│  - m_rat_alpha               │
└──────────┬───────────────────┘
           ↓
┌──────────────────────────────┐
│  Strategy Filter             │
│  - Threshold validation      │
│  - Ratio filtering           │
│  - Position management       │
└──────────┬───────────────────┘
           ↓
      4-Tuple Signals
  (long_entries, long_exits,
   short_entries, short_exits)
           ↓
┌──────────────────────────────┐
│  Vectorbt Portfolio          │
│  - Position sizing           │
│  - PnL calculation           │
│  - Performance metrics       │
└──────────┬───────────────────┘
           ↓
      Performance Report
```

### Available Strategies

#### 1. SentimentLongStrategy
- **Entry**: `bullish_signal ≥ 3` AND `d_rat_beta > 1.0` AND `m_rat_omega > 1.0`
- **Exit**: 24 hours (default)
- **Best For**: Bullish momentum trading with volatility confirmation
- **2025 Results**: 67% long trade win rate (Oct 30-Nov 4)

#### 2. SentimentShortStrategy
- **Entry**: `bearish_signal ≥ 3` AND `d_rat_beta > 1.0` AND `m_rat_omega < 2.0`
- **Exit**: 24 hours (default)
- **Best For**: Bearish reversal trading with refined ratio thresholds
- **2025 Results**: 50% short trade win rate (Oct 30-Nov 4)

#### 3. SentimentLongShortStrategy ⭐ Recommended
- **Long Entry**: `bullish_signal ≥ 3` AND `d_rat_beta > 1.0` AND `m_rat_omega > 1.0`
- **Short Entry**: `bearish_signal ≥ 3` AND `d_rat_beta > 1.0` AND `m_rat_omega < 2.0`
- **Exit**: 24 hours (configurable)
- **Mutual Exclusion**: Prevents simultaneous long/short on same asset
- **Best For**: Comprehensive market participation in both directions

#### Customization Example
```python
from strategies.sentiment_ratios import SentimentLongShortStrategy

strategy = SentimentLongShortStrategy(
    bullish_threshold=3,      # Min bullish signal strength
    bearish_threshold=3,      # Min bearish signal strength
    exit_bars=24,             # Hold duration in hours
    beta_threshold=1.0,       # Min volatility (beta)
    omega_long_max=2.0,       # Max omega for long entries
    omega_short_max=2.0       # Max omega for short entries
)
```

---

## 🏗️ System Architecture

### Data Pipeline

```
PostgreSQL (cp_ai)
    ↓ [Price Data]
cp_backtest_h
    ↓ [OHLCV Sync]
Load Data Module
    ├─ Prices (close, high, low, open, volume)
    ├─ Signals (bullish, bearish from FE_DMV_ALL)
    ├─ Ratios (beta, omega, alpha from FE_RATIOS)
    └─ Forward-fill missing values
    ↓
DataFrame Intersection
    └─ Filter to 194 cryptocurrencies with complete data
    ↓
Strategy Module
    ├─ Generate 4-tuple signals
    └─ Apply ratio filters
    ↓
Vectorbt Portfolio
    ├─ Long positions
    ├─ Short positions
    └─ Calculate metrics
    ↓
Analysis Framework
    ├─ Trade extraction
    ├─ Performance metrics
    └─ CSV export
```

### Module Structure

```
backtest-repo/
├── src/
│   ├── backtest.py          # Main vectorbt runner
│   └── db.py                # PostgreSQL connection factory
├── strategies/
│   ├── __init__.py          # BaseStrategy ABC
│   ├── ma_crossover.py      # MA-based strategies
│   └── sentiment_ratios.py  # Sentiment long/short strategies
├── analysis/
│   ├── scripts/             # Trade analysis utilities
│   └── outputs/             # CSV exports & results
├── docs/                    # All documentation
├── scripts/
│   ├── run_backtest.py
│   ├── qa/
│   └── maintenance/
└── CHANGELOG.md             # Project evolution log
```

---

## 📈 Performance Results

### Full Period Backtest (Feb 13 - Oct 31, 2025)
Tested SentimentLongShort_3_3 strategy on 194 cryptocurrencies

| Metric | Value | Assessment |
|--------|-------|------------|
| **Trades** | 69 | Statistically significant |
| **Total Return** | -6.50% | Underperformance |
| **Market Return** | -14.20% | Bear market |
| **Outperformance** | +7.70% | ✅ Beat market |
| **Win Rate** | 31.88% | Low signal reliability |
| **Sharpe Ratio** | 0.71 | Poor risk-adjusted |
| **Max Drawdown** | 53.68% | High risk |
| **Best Trade** | +114.15% | Strong signal examples exist |

**Key Finding**: Strategy underperformed in bear market but outperformed market decline by 7.70%

---

### Late Period Backtest (Oct 30 - Nov 4, 2025)
Same strategy in improved market conditions

| Metric | Value | Assessment |
|--------|-------|------------|
| **Trades** | 5 | Small sample |
| **Total Return** | +6.39% | Profitable |
| **Market Return** | -3.11% | Mixed market |
| **Outperformance** | +9.50% | ✅ Beat market |
| **Win Rate** | 60.00% | Excellent |
| **Sharpe Ratio** | 9.18 | Exceptional |
| **Max Drawdown** | 2.35% | Tight control |
| **Profit Factor** | 2.97x | Excellent |

**Top Trade**: APTOS Long +5.02% (+$5,142 profit)

---

### Trade Breakdown

| Asset | Trades | Wins | Win % | Total PnL | Avg Return |
|-------|--------|------|-------|-----------|------------|
| **APTOS** | 3 | 2 | 67% | +$3,643 | +1.49% |
| **XRP** | 1 | 1 | 100% | +$526 | +3.66% |
| **AAVE** | 1 | 0 | 0% | -$688 | -0.69% |
| **TOTAL** | 5 | 3 | 60% | +$3,481 | +0.69% |

---

### Long vs Short Performance

```
LONG TRADES (3 total)              SHORT TRADES (2 total)
├─ Wins: 2                         ├─ Wins: 1
├─ Losses: 1                       ├─ Losses: 1
├─ Win Rate: 67% ✅                ├─ Win Rate: 50% ⚠️
├─ Total PnL: +$5,240              ├─ Total PnL: -$1,819
└─ Avg Return: +1.74%              └─ Avg Return: -0.92%

Insight: Bullish market bias during Oct 30-Nov 4
Action: Short signal filtering needs improvement
```

---

## 📚 Documentation

### For Quick Understanding
- **[docs/ANALYSIS_INDEX.md](docs/ANALYSIS_INDEX.md)** - Start here! Master navigation guide
- **[docs/CLAUDE.md](docs/CLAUDE.md)** - Architecture & setup guide
- **[docs/STRATEGIES_QUICKSTART.md](docs/STRATEGIES_QUICKSTART.md)** - Quick examples

### For Detailed Analysis
- **[docs/TRADE_REPORT.md](docs/TRADE_REPORT.md)** - All 5 trades with timestamps & prices
- **[docs/PERIOD_COMPARISON.md](docs/PERIOD_COMPARISON.md)** - Full vs late period analysis
- **[docs/OCT_ANALYSIS.md](docs/OCT_ANALYSIS.md)** - October data limitations & timeline

### For Strategy Development
- **[docs/LONGSHORT_STRATEGIES.md](docs/LONGSHORT_STRATEGIES.md)** - Complete strategy documentation
- **[strategies/README.md](strategies/README.md)** - How to write custom strategies
- **[CHANGELOG.md](CHANGELOG.md)** - Full project evolution & implementation details

### For Analysis Tools
- **[analysis/scripts/](analysis/scripts/)** - 4 trade analysis utilities
- **[analysis/outputs/](analysis/outputs/)** - CSV exports & results

---

## 🔄 Project Structure

```
CryptoPrism-DB-Backtest/
│
├── 📄 README.md                    # This file
├── 📄 CHANGELOG.md                 # Complete project evolution (6 phases)
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.example                 # Environment template
│
├── 📁 docs/                        # All documentation
│   ├── ANALYSIS_INDEX.md           # Master guide (START HERE)
│   ├── CLAUDE.md                   # Architecture
│   ├── LONGSHORT_STRATEGIES.md     # Strategy docs
│   ├── TRADE_REPORT.md             # Detailed trade analysis
│   ├── PERIOD_COMPARISON.md        # Period comparison
│   ├── OCT_ANALYSIS.md             # October analysis
│   ├── STRATEGIES_QUICKSTART.md    # Quick start
│   └── BACKTEST_RESULTS.md         # Historical results
│
├── 📁 src/                         # Core engine
│   ├── backtest.py                 # Main vectorbt runner
│   │   ├─ load_data() - Data loading with ratios
│   │   ├─ run_vbt() - Vectorbt portfolio runner
│   │   ├─ get_available_strategies() - Strategy discovery
│   │   └─ main() - CLI entry point
│   └── db.py                       # PostgreSQL factory
│
├── 📁 strategies/                  # Trading strategies
│   ├── __init__.py                 # BaseStrategy ABC
│   │   └─ Define signal interface (2-tuple, 4-tuple)
│   ├── ma_crossover.py             # Moving average strategies
│   │   ├─ MATimeframes (8h/24h dual crossover)
│   │   └─ MAOnlyFast (price vs 12h MA)
│   ├── sentiment_ratios.py         # Sentiment strategies (270+ lines)
│   │   ├─ SentimentLongStrategy
│   │   ├─ SentimentShortStrategy
│   │   └─ SentimentLongShortStrategy ⭐
│   └── README.md                   # Strategy development guide
│
├── 📁 analysis/                    # Analysis tools
│   ├── scripts/                    # 4 analysis utilities
│   │   ├── analyze_trades.py       # Comprehensive breakdown
│   │   ├── extract_trades.py       # CSV export
│   │   ├── get_trade_details.py    # Detailed extraction
│   │   └── inspect_trades.py       # Structure inspection
│   └── outputs/                    # Results
│       └── trades_SentimentLongShort_3_3_30d.csv
│
├── 📁 scripts/                     # Utilities
│   ├── run_backtest.py             # Helper launcher
│   ├── qa/
│   │   └── check_sync_last3days.py # Data validation
│   └── maintenance/
│       ├── enforce_unique_ohlcv_slug_ts.py
│       └── sync_ohlcv_from_cp_ai_to_backtest.py
│
├── 📁 .github/
│   └── workflows/
│       └── backtest.yml            # CI/CD pipeline
│
├── 📁 reports/                     # Backtest output
├── 📁 data/                        # Data files
└── 📁 .git/                        # Version control
```

---

## 🔧 Common Commands

### Discovery
```bash
# List available strategies
python src/backtest.py --list-strategies

# Check data availability
python src/backtest.py --list-ranges

# Run QA checks
python scripts/qa/check_sync_last3days.py
```

### Backtesting
```bash
# Run specific period
python src/backtest.py --strategy SentimentLongShort_3_3 \
  --start "2025-02-13 00:00:00" --end "2025-10-31 23:59:59"

# Test on single coin
python src/backtest.py --strategy SentimentLongShort_3_3 --coin bitcoin

# Run last 30 days
python src/backtest.py --strategy SentimentLongShort_3_3 --days 30

# Use different ratio table
python src/backtest.py --strategy SentimentLongShort_3_3 \
  --days 30 --ratios-table FE_RATIOS_CUSTOM
```

### Analysis
```bash
# Analyze trades
python analysis/scripts/analyze_trades.py

# Extract to CSV
python analysis/scripts/extract_trades.py

# Get detailed trade info
python analysis/scripts/get_trade_details.py
```

---

## 🎓 Learning Path

1. **Start**: Read [docs/ANALYSIS_INDEX.md](docs/ANALYSIS_INDEX.md)
2. **Understand**: Review [docs/CLAUDE.md](docs/CLAUDE.md) architecture
3. **See Results**: Check [docs/TRADE_REPORT.md](docs/TRADE_REPORT.md)
4. **Learn Strategy**: Study [docs/LONGSHORT_STRATEGIES.md](docs/LONGSHORT_STRATEGIES.md)
5. **Write Custom**: Follow [strategies/README.md](strategies/README.md)
6. **Run Tests**: Use [docs/STRATEGIES_QUICKSTART.md](docs/STRATEGIES_QUICKSTART.md)
7. **Deep Dive**: Review [CHANGELOG.md](CHANGELOG.md) for implementation details

---

## 🤝 Contributing

### Adding New Strategies
1. Create new file in `strategies/` folder
2. Extend `BaseStrategy` class
3. Implement `generate_signals()` method
4. Return 2-tuple (long-only) or 4-tuple (long/short)
5. Add documentation to strategy README

### Reporting Issues
- Use GitHub Issues for bugs and feature requests
- Include backtest parameters and date range
- Attach relevant data files or CSV exports

### Code Standards
- Python 3.12+ compatible
- Type hints for function signatures
- Docstrings for public methods
- Test on small period before full run

---

## 📋 Data Availability

| Data Source | Table | Available Range | Status |
|-------------|-------|-----------------|--------|
| **Prices** | ohlcv_1h_250_coins | Feb 13 - Nov 4, 2025 | ✅ Complete |
| **Signals** | FE_DMV_ALL | Feb 13 - Oct 31, 2025 | ⚠️ Cutoff |
| **Ratios** | FE_RATIOS | Feb 13 - Nov 4, 2025 | ✅ Complete |
| **Assets Tested** | 194 cryptocurrencies | Full range | ✅ Verified |

**Note**: Signal data available through Oct 31, 2025. See [docs/OCT_ANALYSIS.md](docs/OCT_ANALYSIS.md) for details.

---

## 🔐 Environment Variables

```bash
# PostgreSQL Connection
DB_HOST=localhost           # Database host
DB_PORT=5432               # Database port (default)
DB_USER=postgres           # Database user
DB_PASSWORD=yourpass       # Database password

# Database Names
DB_NAME=cp_ai              # Source database (signals, prices)
DB_NAME_BT=cp_backtest_h   # Backtest database (output)

# Optional
BACKTEST_STATS_FILE=backtest_stats.txt
```

---

## 📜 License

This project is licensed under the MIT License. See LICENSE file for details.

---

## 🙏 Acknowledgments

- **Vectorbt**: Efficient portfolio backtesting library
- **PostgreSQL**: Reliable database backend
- **Pandas**: Data manipulation and analysis
- **CryptoPrism**: Data pipeline and infrastructure

---

## 📞 Support

For questions or issues:
1. Check [docs/ANALYSIS_INDEX.md](docs/ANALYSIS_INDEX.md) for navigation
2. Review [docs/CLAUDE.md](docs/CLAUDE.md) for architecture questions
3. See [docs/STRATEGIES_QUICKSTART.md](docs/STRATEGIES_QUICKSTART.md) for usage
4. Open GitHub Issue for bugs

---

<div align="center">

**Built with 🚀 by CryptoPrism Team**

[GitHub](https://github.com/CryptoPrism-io/CryptoPrism-DB-Backtest) • [Docs](docs/ANALYSIS_INDEX.md) • [Changelog](CHANGELOG.md)

</div>
