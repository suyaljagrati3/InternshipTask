import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

df = pd.read_csv(
    r"C:\Users\Jagrati suyal\Downloads\ROUND_1\ROUND1\prices_round_1_day_-1.csv",
    sep=";"
)

OSM = "ASH_COATED_OSMIUM"
PEP = "INTARIAN_PEPPER_ROOT"

osm_df = df[df["product"] == OSM].dropna(
    subset=["bid_price_1","ask_price_1","mid_price"]
).sort_values("timestamp").reset_index(drop=True)

pep_df = df[df["product"] == PEP].dropna(
    subset=["bid_price_1","ask_price_1","mid_price"]
).sort_values("timestamp").reset_index(drop=True)

position = {OSM: 0, PEP: 0}
cash      = 0.0
trade_log = []

# ================================================================
# OSMIUM — ML: Linear Regression price predictor
#
# Features: last 5 mid prices + spread + OBI
# Target:   next mid price
# Signal:   if predicted_next > current + threshold → buy
#           if predicted_next < current - threshold → sell
# ================================================================

# ================================================================
# OSMIUM — ML: Linear Regression price predictor
# ================================================================

LOOKBACK    = 10
osm_mids    = []
osm_bids    = []
osm_asks    = []
X_train     = []
y_train     = []
model_osm   = LinearRegression()
model_ready = False

def make_features(mids, bid, ask):
    """Always returns exactly 13 features — consistent size."""
    recent   = mids[-LOOKBACK:]          # 10 features
    spread   = ask - bid                 # 1 feature
    momentum = recent[-1] - recent[0]   # 1 feature
    mean_r   = np.mean(recent)          # 1 feature
    # Total: 13 features always
    return recent + [spread, momentum, mean_r]

for idx, row in osm_df.iterrows():
    ts  = row["timestamp"]
    bid = float(row["bid_price_1"])
    ask = float(row["ask_price_1"])
    mid = float(row["mid_price"])
    pos = position[OSM]
    lim = 20

    osm_mids.append(mid)
    osm_bids.append(bid)
    osm_asks.append(ask)

    # Need at least LOOKBACK + 1 prices
    if len(osm_mids) < LOOKBACK + 1:
        continue

    features = make_features(osm_mids[:-1], osm_bids[-1], osm_asks[-1])
    target   = mid   # what we're trying to predict

    X_train.append(features)
    y_train.append(target)

    # Retrain every 20 ticks once we have 50 samples
    if len(X_train) >= 50 and idx % 20 == 0:
        model_osm.fit(X_train[-200:], y_train[-200:])
        model_ready = True

    if not model_ready:
        # Baseline while model warms up
        if ask <= 9999 and pos < lim:
            qty = min(3, lim - pos)
            position[OSM] += qty
            cash -= ask * qty
            trade_log.append([ts, OSM, "BUY", ask, qty])
        elif bid >= 10004 and pos > -5:
            qty = min(3, pos + 5)
            if qty > 0:
                position[OSM] -= qty
                cash += bid * qty
                trade_log.append([ts, OSM, "SELL", bid, qty])
        continue

    # ML prediction using same feature function
    feat_vec  = [make_features(osm_mids, bid, ask)]
    pred_next = model_osm.predict(feat_vec)[0]
    pred_delta = pred_next - mid

    THRESH = 1.5

    if pred_delta > THRESH and pos < lim:
        qty = min(3, lim - pos)
        position[OSM] += qty
        cash -= ask * qty
        trade_log.append([ts, OSM, "BUY", ask, qty])

    elif pred_delta < -THRESH and pos > -5:
        qty = min(3, pos + 5)
        if qty > 0:
            position[OSM] -= qty
            cash += bid * qty
            trade_log.append([ts, OSM, "SELL", bid, qty])
 
     
        
# ================================================================
# PEPPER — ML: Polynomial regression for trend
#
# Instead of simple OLS line, fit a degree-2 polynomial
# This captures the slight acceleration seen in the chart
# ================================================================

pep_px   = []
pep_ts   = []
tot_cost = 0.0
tot_qty  = 0

for _, row in pep_df.iterrows():
    ts  = row["timestamp"]
    bid = float(row["bid_price_1"])
    ask = float(row["ask_price_1"])
    mid = float(row["mid_price"])
    pos = position[PEP]
    lim = 35

    if mid < 5000:
        continue

    pep_px.append(mid)
    pep_ts.append(float(ts))
    if len(pep_px) > 150:
        pep_px.pop(0)
        pep_ts.pop(0)
    if len(pep_px) < 20:
        continue

    # Degree-2 polynomial fit instead of linear OLS
    ts_arr  = np.array(pep_ts)
    px_arr  = np.array(pep_px)
    ts_norm = (ts_arr - ts_arr.mean()) / (ts_arr.std() + 1e-6)

    coeffs = np.polyfit(ts_norm, px_arr, deg=2)
    ts_now = (ts - ts_arr.mean()) / (ts_arr.std() + 1e-6)
    fair   = np.polyval(coeffs, ts_now)

    avg_cost = tot_cost / tot_qty if tot_qty > 0 else fair

    # Buy dips below polynomial trend
    if ask <= fair - 2 and pos < lim:
        qty = min(5, lim - pos)
        position[PEP] += qty
        cash -= ask * qty
        tot_cost += ask * qty
        tot_qty  += qty
        trade_log.append([ts, PEP, "BUY", ask, qty])

    elif bid >= fair + 5 and pos > 15 and bid > avg_cost + 5:
        qty = min(5, pos - 15)
        if qty > 0:
            position[PEP] -= qty
            cash += bid * qty
            tot_cost -= avg_cost * qty
            tot_qty  -= qty
            trade_log.append([ts, PEP, "SELL", bid, qty])

# ================================================================
# RESULTS
# ================================================================
last_prices = df.groupby("product")["mid_price"].last()
portfolio_value = cash
for p in position:
    portfolio_value += position[p] * last_prices.get(p, 0)

print("=" * 50)
print("ML-BASED APPROACH")
print("=" * 50)
print(f"Final Positions : {position}")
print(f"Portfolio Value : {round(portfolio_value,2):>12,}")

trades = pd.DataFrame(trade_log,
    columns=["timestamp","product","side","price","qty"])

for p in [OSM, PEP]:
    t      = trades[trades["product"] == p]
    bought = (t[t["side"]=="BUY"]["price"]  * t[t["side"]=="BUY"]["qty"]).sum()
    sold   = (t[t["side"]=="SELL"]["price"] * t[t["side"]=="SELL"]["qty"]).sum()
    resid  = position[p] * last_prices.get(p, 0)
    pnl    = sold - bought + resid
    print(f"{p:35s}  trades={len(t):4d}  PnL={round(pnl):>8,}")

print(f"\nTotal trades : {len(trades)}")