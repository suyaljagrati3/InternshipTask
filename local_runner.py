# local_runner.py
# Running  this to test submit.py locally against  CSV data

import pandas as pd
from datamodel import TradingState, OrderDepth, Trade, Observation
from submit import Trader

df = pd.read_csv(
   r"C:\Users\Jagrati suyal\Downloads\ROUND_1\ROUND1\prices_round_1_day_-2.csv",
    sep=";"
)

products = df["product"].unique()
timestamps = sorted(df["timestamp"].unique())

trader      = Trader()
trader_data = ""
position    = {}
cash        = 0.0
trade_log   = []

for ts in timestamps:
    tick = df[df["timestamp"] == ts]

    # Build order depths for this tick
    order_depths = {}
    for _, row in tick.iterrows():
        p  = row["product"]
        od = OrderDepth()

        for i in [1, 2, 3]:
            bp = row.get(f"bid_price_{i}")
            bv = row.get(f"bid_volume_{i}")
            ap = row.get(f"ask_price_{i}")
            av = row.get(f"ask_volume_{i}")

            if pd.notna(bp) and pd.notna(bv):
                od.buy_orders[int(bp)]  = int(bv)
            if pd.notna(ap) and pd.notna(av):
                od.sell_orders[int(ap)] = int(av)

        order_depths[p] = od

    # Build state
    state = TradingState(
        traderData    = trader_data,
        timestamp     = ts,
        listings      = {},
        order_depths  = order_depths,
        own_trades    = {},
        market_trades = {},
        position      = position.copy(),
        observations  = Observation({}, {}),
    )

    # Run trader
    orders, conversions, trader_data = trader.run(state)

    # Simulate fills
    for product, order_list in orders.items():
        od  = order_depths.get(product, OrderDepth())
        pos = position.get(product, 0)

        for order in order_list:
            if order.quantity > 0:   # buying
                for px in sorted(od.sell_orders):
                    if px <= order.price:
                        fill = min(order.quantity, od.sell_orders[px])
                        position[product] = pos + fill
                        cash -= px * fill
                        trade_log.append([ts, product, "BUY", px, fill])
                        break
            else:                    # selling
                for px in sorted(od.buy_orders, reverse=True):
                    if px >= order.price:
                        fill = min(abs(order.quantity), od.buy_orders[px])
                        position[product] = pos - fill
                        cash += px * fill
                        trade_log.append([ts, product, "SELL", px, fill])
                        break

# Results
last_prices = df.groupby("product")["mid_price"].last()
portfolio_value = cash
for p in position:
    portfolio_value += position[p] * last_prices.get(p, 0)

print("=" * 50)
print("LOCAL RUNNER RESULTS")
print("=" * 50)
print(f"Final Positions : {position}")
print(f"Cash            : {round(cash,2):>15,}")
print(f"Portfolio Value : {round(portfolio_value,2):>15,}")

import pandas as pd
trades = pd.DataFrame(trade_log,
    columns=["timestamp","product","side","price","qty"])

OSM = "ASH_COATED_OSMIUM"
PEP = "INTARIAN_PEPPER_ROOT"
for p in [OSM, PEP]:
    t      = trades[trades["product"] == p]
    bought = (t[t["side"]=="BUY"]["price"]  * t[t["side"]=="BUY"]["qty"]).sum()
    sold   = (t[t["side"]=="SELL"]["price"] * t[t["side"]=="SELL"]["qty"]).sum()
    resid  = position.get(p, 0) * last_prices.get(p, 0)
    pnl    = sold - bought + resid
    print(f"{p:35s}  trades={len(t):4d}  PnL={round(pnl):>8,}")
