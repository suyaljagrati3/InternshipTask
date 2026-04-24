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

# ── OSMIUM: rolling median fair value + fixed thresholds ─────────
osm_mids = []

for _, row in osm_df.iterrows():
    ts  = row["timestamp"]
    bid = float(row["bid_price_1"])
    ask = float(row["ask_price_1"])
    mid = float(row["mid_price"])
    pos = position[OSM]

    osm_mids.append(mid)
    if len(osm_mids) > 50:
        osm_mids.pop(0)

    fair = np.median(osm_mids)

    # Buy 3 ticks below fair, sell 3 ticks above fair
    if ask <= fair - 3 and pos < 20:
        qty = min(3, 20 - pos)
        position[OSM] += qty
        cash -= ask * qty
        trade_log.append([ts, OSM, "BUY", ask, qty])

    elif bid >= fair + 3 and pos > -20:
        qty = min(3, 20 + pos)
        position[OSM] -= qty
        cash += bid * qty
        trade_log.append([ts, OSM, "SELL", bid, qty])

# ── PEPPER: buy dips below rolling trend ─────────────────────────
pep_px = []
pep_ts = []

for _, row in pep_df.iterrows():
    ts  = row["timestamp"]
    bid = float(row["bid_price_1"])
    ask = float(row["ask_price_1"])
    mid = float(row["mid_price"])
    pos = position[PEP]

    if mid < 5000:
        continue

    pep_px.append(mid)
    pep_ts.append(float(ts))
    if len(pep_px) > 100:
        pep_px.pop(0)
        pep_ts.pop(0)
    if len(pep_px) < 20:
        continue

    slope, intercept = np.polyfit(pep_ts, pep_px, 1)
    fair = intercept + slope * ts

    # Buy dips, hold — only sell if well above trend
    if ask <= fair - 2 and pos < 35:
        qty = min(5, 35 - pos)
        position[PEP] += qty
        cash -= ask * qty
        trade_log.append([ts, PEP, "BUY", ask, qty])

    elif bid >= fair + 10 and pos > 10:
        qty = min(5, pos - 10)
        position[PEP] -= qty
        cash += bid * qty
        trade_log.append([ts, PEP, "SELL", bid, qty])

# ── Results ────
last_prices = df.groupby("product")["mid_price"].last()
portfolio_value = cash
for p in position:
    portfolio_value += position[p] * last_prices.get(p, 0)

trades = pd.DataFrame(trade_log,
    columns=["timestamp","product","side","price","qty"])

print("=" * 45)
print("LEVEL 2 — ROLLING FAIR VALUE")
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
