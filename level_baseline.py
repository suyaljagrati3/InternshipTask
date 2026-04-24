import pandas as pd

df = pd.read_csv(
    r"C:\Users\Jagrati suyal\Downloads\ROUND_1\ROUND1\prices_round_1_day_0.csv",
    sep=";"
)

OSM = "ASH_COATED_OSMIUM"
PEP = "INTARIAN_PEPPER_ROOT"

osm_df = df[df["product"] == OSM].dropna(
    subset=["bid_price_1","ask_price_1"]
).sort_values("timestamp").reset_index(drop=True)

pep_df = df[df["product"] == PEP].dropna(
    subset=["bid_price_1","ask_price_1"]
).sort_values("timestamp").reset_index(drop=True)

position = {OSM: 0, PEP: 0}
cash      = 0.0
trade_log = []

# ── OSMIUM: fixed fair value, buy below, sell above ──────────────
for _, row in osm_df.iterrows():
    ts  = row["timestamp"]
    bid = float(row["bid_price_1"])
    ask = float(row["ask_price_1"])
    pos = position[OSM]

    if ask <= 9999 and pos < 20:
        position[OSM] += 1
        cash -= ask
        trade_log.append([ts, OSM, "BUY", ask, 1])

    elif bid >= 10004 and pos > -5:
        position[OSM] -= 1
        cash += bid
        trade_log.append([ts, OSM, "SELL", bid, 1])

# ── PEPPER: just buy and hold ─────
for _, row in pep_df.iterrows():
    ts  = row["timestamp"]
    ask = float(row["ask_price_1"])
    pos = position[PEP]

    if pos < 35:
        position[PEP] += 1
        cash -= ask
        trade_log.append([ts, PEP, "BUY", ask, 1])

# ── Results ──────
last_prices = df.groupby("product")["mid_price"].last()
portfolio_value = cash
for p in position:
    portfolio_value += position[p] * last_prices.get(p, 0)

trades = pd.DataFrame(trade_log,
    columns=["timestamp","product","side","price","qty"])

print("=" * 45)
print("LEVEL 1 — BASELINE")
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
