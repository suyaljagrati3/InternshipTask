# InternshipTask
This repository contains the internship task that i was asssigned for data science

# IMC Prosperity Round 1 — Trading Bot

## What I Did

### Data Analysis
- Loaded and analysed price data for both products across 3 days
- Plotted price charts for ASH_COATED_OSMIUM and INTARIAN_PEPPER_ROOT
- Identified ASH_COATED_OSMIUM as mean-reverting (flat at ~10,001)
- Identified INTARIAN_PEPPER_ROOT as upward trending (~12,000 to 13,000)
- Analysed bid/ask distribution to find optimal entry/exit thresholds

### Strategy Design
- Designed mean reversion strategy for OSMIUM using fixed price thresholds
- Designed buy-and-hold trend following strategy for PEPPER
- Decided on position limits (OSMIUM: 20, PEPPER: 35)
- Chose trade quantity and inventory management rules

### Backtesting
- Built a row-by-row backtester in Python using pandas
- Tested 3 strategy levels (simple to complex) as advised by mentor
- Built a local runner to validate Trader class before submission
- Tested all strategies across Day -1, Day 0, Day -2

### ML Experiment
- Implemented Linear Regression price predictor for OSMIUM
- Implemented Polynomial Regression trend model for PEPPER
- Compared ML vs baseline across all 3 days
- Concluded baseline outperforms ML for this dataset

### Results
| Day    | Baseline PnL | ML PnL |
|--------|-------------|--------|
| Day -1 | +35,720     | +16,396|
| Day 0  | +35,868     | +16,622|
| Day -2 | +35,293     | +16,726|
| Avg    | +35,627     | +16,581|

Baseline wins by ~19,000 PnL on every day.

---

## What Was Done by AI (Claude)

- Suggested the overall architecture (mean reversion + trend following)
- Provided initial code structure for the backtester
- Helped debug position imbalance issues in OSMIUM strategy
- Ran frequency analysis on bid/ask data to find threshold values
- Suggested the ML approach (Linear Regression + Polynomial Regression)
- Helped fix sklearn feature size mismatch error
- Provided the datamodel.py file and local_runner.py structure
- Suggested the inventory skew concept for position management

---

## My Contributions

- Analysed the price charts and identified product regimes myself
- Communicated findings to mentor and received strategic guidance
- Decided which strategy level to use based on backtest results
- Ran all experiments and compared outputs across all 3 days
- Drew conclusions from ML experiment independently
- Structured and documented the work

---


## Key Learnings

1. Simpler strategies outperform complex ones on stable products
2. ML adds noise on near-random-walk products like OSMIUM
3. Position limit management is critical — runaway inventory kills PnL
4. Always test across multiple days before submitting
5. Buy-and-hold is optimal for strongly trending products
