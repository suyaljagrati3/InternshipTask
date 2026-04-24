import pandas as pd
import numpy as np

df = pd.read_csv(
    r"C:\Users\Jagrati suyal\Downloads\ROUND_1\ROUND1\prices_round_1_day_0.csv",
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

# ── OSMIUM: z-score + inventory skew ─────────────────────────────
osm_mids = []

for _, row in osm_df.iterrows():
    ts  = row["timestamp"]
    bid = float(row["bid_price_1"])
    ask = float(row["ask_price_1"])
    mid = float(row["mid_price"])
    pos = position[OSM]
    lim = 20

    osm_mids.append(mid)
    if len(osm_mids) > 50:
        osm_mids.pop(0)
    if len(osm_mids) < 10:
        continue

    fair  = np.median(osm_mids)
    sigma = np.std(osm_mids)
    if sigma < 0.1:
        continue

    z = (mid - fair) / sigma

    # Inventory skew shifts both thresholds
    inv = pos / lim             # -1 to +1
    skew = inv * 0.5            # small skew

    buy_z  = -1.0 - skew       # when long, need bigger dip to buy
    sell_z =  1.0 - skew       # when long, sell more easily

    if z < buy_z and pos < lim:
        qty = min(3, lim - pos)
        position[OSM] += qty
        cash -= ask * qty
        trade_log.append([ts, OSM, "BUY", ask, qty])

    elif z > sell_z and pos > -lim:
        qty = min(3, lim + pos)
        position[OSM] -= qty
        cash += bid * qty
        trade_log.append([ts, OSM, "SELL", bid, qty])

# ── PEPPER: OLS trend + dip entry + spike exit ───────────────────
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

    slope, intercept = np.polyfit(pep_ts, pep_px, 1)
    fair     = intercept + slope * ts
    avg_cost = tot_cost / tot_qty if tot_qty > 0 else fair

    # Buy dips below trend
    if ask <= fair - 2 and pos < lim:
        qty = min(5, lim - pos)
        position[PEP] += qty
        cash -= ask * qty
        tot_cost += ask * qty
        tot_qty  += qty
        trade_log.append([ts, PEP, "BUY", ask, qty])

    # Sell spikes — keep minimum 15 units always
    elif bid >= fair + 8 and pos > 15 and bid > avg_cost + 5:
        qty = min(5, pos - 15)
        if qty > 0:
            position[PEP] -= qty
            cash += bid * qty
            tot_cost -= avg_cost * qty
            tot_qty  -= qty
            trade_log.append([ts, PEP, "SELL", bid, qty])

# ── Results ───────────────────────────────────────────────────────
last_prices = df.groupby("product")["mid_price"].last()
portfolio_value = cash
for p in position:
    portfolio_value += position[p] * last_prices.get(p, 0)

trades = pd.DataFrame(trade_log,
    columns=["timestamp","product","side","price","qty"])

print("=" * 45)
print("LEVEL 3 — Z-SCORE + OLS TREND")
print("=" * 45)
print(f"Final Positions : {position}")
print(f"Portfolio Value : {round(portfolio_value,2):>12,}")
for p in [OSM, PEP]:
    t = trades[trades["product"] == p]
    bought = (t[t["side"]=="BUY"]["price"] * t[t["side"]=="BUY"]["qty"]).sum()
    sold   = (t[t["side"]=="SELL"]["price"] * t[t["side"]=="SELL"]["qty"]).sum()
    resid  = position[p] * last_prices.get(p, 0)
    pnl    = sold - bought + resid
    print(f"{p:35s}  trades={len(t):4d}  PnL={round(pnl):>8,}")