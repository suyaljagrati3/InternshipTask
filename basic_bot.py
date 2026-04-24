import pandas as pd
import numpy as np
import glob
import os

OSM = "ASH_COATED_OSMIUM"
PEP = "INTARIAN_PEPPER_ROOT"
LIMITS = {OSM: 20, PEP: 35}

# ── thresholds ──────────────────────────────────────────────────
BUY_THRESH  = 9998
SELL_THRESH = 10004
OSM_QTY     = 3
UNWIND_AT   = 15

ROLL        = 150
PEP_QTY     = 5
DIP_ENTRY   = 2.0
TAKE_PROFIT = 5.0      # original profit-take threshold
MIN_HOLD    = 20       # don't sell below this pos in normal ops
CLOSE_START = 950_000  # timestamp after which we start closing all positions


def run_strategy(csv_path: str) -> dict:
    """Run the full strategy on one CSV file and return a results dict."""

    df = pd.read_csv(csv_path, sep=";")
    label = os.path.basename(csv_path)

    osm_df = (
        df[df["product"] == OSM]
        .dropna(subset=["bid_price_1", "ask_price_1", "mid_price"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    pep_df = (
        df[df["product"] == PEP]
        .dropna(subset=["bid_price_1", "ask_price_1", "mid_price"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    position  = {OSM: 0, PEP: 0}
    cash      = 0.0
    trade_log = []

    # ── last timestamp in file ───
    max_ts = float(df["timestamp"].max())

    # OSMIUM
    for _, row in osm_df.iterrows():
        ts  = float(row["timestamp"])
        bid = float(row["bid_price_1"])
        ask = float(row["ask_price_1"])
        pos = position[OSM]
        lim = LIMITS[OSM]

        # ── UPGRADE 1: end-of-day position close ──
        if ts >= CLOSE_START:
            if pos > 0 and bid > 0:
                # Sell everything we own
                position[OSM] -= pos
                cash += bid * pos
                trade_log.append([ts, OSM, "SELL", bid, pos])
            elif pos < 0 and ask > 0:
                # Buy back short
                qty = -pos
                position[OSM] += qty
                cash -= ask * qty
                trade_log.append([ts, OSM, "BUY", ask, qty])
            continue

        # Forced unwind (still active before CLOSE_START)
        if pos >= UNWIND_AT:
            if bid >= 10001 and pos > 0:
                qty = min(OSM_QTY, pos)
                position[OSM] -= qty
                cash += bid * qty
                trade_log.append([ts, OSM, "SELL", bid, qty])
            continue

        if pos <= -UNWIND_AT:
            if ask <= 10003 and pos < lim:
                qty = min(OSM_QTY, -pos)
                position[OSM] += qty
                cash -= ask * qty
                trade_log.append([ts, OSM, "BUY", ask, qty])
            continue

        # Normal range: pure frequency-matched thresholds
        if ask <= BUY_THRESH and pos < lim:
            qty = min(OSM_QTY, lim - pos)
            position[OSM] += qty
            cash -= ask * qty
            trade_log.append([ts, OSM, "BUY", ask, qty])

        elif bid >= SELL_THRESH and pos > -lim:
            qty = min(OSM_QTY, lim + pos)
            position[OSM] -= qty
            cash += bid * qty
            trade_log.append([ts, OSM, "SELL", bid, qty])

    # PEPPER   UPGRADE 3: tiered profit-booking + end-of-day close
 
    pep_window_px = []
    pep_window_ts = []
    total_cost  = 0.0
    total_units = 0

    for _, row in pep_df.iterrows():
        ts  = float(row["timestamp"])
        bid = float(row["bid_price_1"])
        ask = float(row["ask_price_1"])
        mid = float(row["mid_price"])

        if mid < 5000:
            continue

        # ──  UPGRADE 1: end-of-day close for PEP ────
        if ts >= CLOSE_START:
            pos = position[PEP]
            if pos > 0 and bid > 0:
                # Unwind in chunks so we don't crash the book
                sell_qty = min(PEP_QTY * 2, pos)
                position[PEP]  -= sell_qty
                cash           += bid * sell_qty
                avg = total_cost / total_units if total_units > 0 else 0
                total_cost     -= avg * sell_qty
                total_units    -= sell_qty
                trade_log.append([ts, PEP, "SELL", bid, sell_qty])
            continue

        # Rolling fair-value estimate
        pep_window_px.append(mid)
        pep_window_ts.append(ts)
        if len(pep_window_px) > ROLL:
            pep_window_px.pop(0)
            pep_window_ts.pop(0)
        if len(pep_window_px) < 20:
            continue

        slope, intercept = np.polyfit(pep_window_ts, pep_window_px, 1)
        fair     = intercept + slope * ts
        lim      = LIMITS[PEP]
        pos      = position[PEP]
        avg_cost = total_cost / total_units if total_units > 0 else fair

        # ── BUY: price dips below fair value ────────────────────
        if ask <= fair - DIP_ENTRY and pos < lim:
            qty = min(PEP_QTY, lim - pos)
            position[PEP] += qty
            cash          -= ask * qty
            total_cost    += ask * qty
            total_units   += qty
            trade_log.append([ts, PEP, "BUY", ask, qty])

        # ──  UPGRADE 3: tiered profit-booking ───
        # Tier 1 — moderate gain: sell small chunk (no MIN_HOLD floor)
        elif (bid >= fair + TAKE_PROFIT
              and pos > 5
              and bid > avg_cost + 5):
            qty = min(PEP_QTY, pos - 5)          # keep at least 5 units
            if qty > 0:
                position[PEP] -= qty
                cash          += bid * qty
                total_cost    -= avg_cost * qty
                total_units   -= qty
                trade_log.append([ts, PEP, "SELL", bid, qty])

        # Tier 2 — big spike: sell aggressively
        elif (bid >= fair + TAKE_PROFIT * 3
              and pos > 0):
            qty = min(PEP_QTY * 2, pos)           # sell up to 10 units
            if qty > 0:
                position[PEP] -= qty
                cash          += bid * qty
                total_cost    -= avg_cost * qty
                total_units   -= qty
                trade_log.append([ts, PEP, "SELL", bid, qty])

    # MARK TO MARKET

    last_prices     = df.groupby("product")["mid_price"].last()
    portfolio_value = cash
    for p in position:
        portfolio_value += position[p] * last_prices.get(p, 0)

    trades = pd.DataFrame(
        trade_log,
        columns=["timestamp", "product", "side", "price", "qty"],
    )

    results = {
        "label"           : label,
        "position"        : dict(position),
        "cash"            : round(cash, 2),
        "portfolio_value" : round(portfolio_value, 2),
        "trades"          : trades,
        "last_prices"     : last_prices,
    }
    return results


def print_results(r: dict):
    trades      = r["trades"]
    last_prices = r["last_prices"]
    position    = r["position"]

    print("\n" + "=" * 60)
    print(f"  FILE : {r['label']}")
    print("=" * 60)
    print(f"  Final Positions : {position}")
    print(f"  Cash            : {r['cash']:>15,.2f}")
    print(f"  Portfolio Value : {r['portfolio_value']:>15,.2f}")
    print("-" * 60)

    total_pnl = 0
    for p in [OSM, PEP]:
        t      = trades[trades["product"] == p]
        bought = (t[t["side"] == "BUY"]["price"]  * t[t["side"] == "BUY"]["qty"]).sum()
        sold   = (t[t["side"] == "SELL"]["price"] * t[t["side"] == "SELL"]["qty"]).sum()
        resid  = position[p] * last_prices.get(p, 0)
        pnl    = sold - bought + resid
        total_pnl += pnl
        print(f"  {p:35s}  trades={len(t):4d}  PnL={round(pnl):>10,}")

    print(f"  {'TOTAL':35s}                PnL={round(total_pnl):>10,}")
    print(f"\n  Total trades : {len(trades)}")

    # OSM summary
    osm_t = trades[trades["product"] == OSM]
    buys  = osm_t[osm_t["side"] == "BUY"]["price"]
    sells = osm_t[osm_t["side"] == "SELL"]["price"]
    print(f"\n  --- OSMIUM SUMMARY ---")
    print(f"  Buys  : {len(buys):4d}" + (f"  avg = {buys.mean():.2f}"   if len(buys)  else ""))
    print(f"  Sells : {len(sells):4d}" + (f"  avg = {sells.mean():.2f}" if len(sells) else ""))
    if len(buys) and len(sells):
        edge = sells.mean() - buys.mean()
        print(f"  Edge  : {edge:.2f} ticks")
    print(f"  Final OSM pos : {position[OSM]}  (target: 0)")

    # PEP inventory log
    pep_t = trades[trades["product"] == PEP].copy()
    if len(pep_t):
        pep_t["pos"] = pep_t.apply(
            lambda r: r["qty"] if r["side"] == "BUY" else -r["qty"], axis=1
        ).cumsum()
        print(f"\n  --- PEPPER INVENTORY LOG ---")
        print(f"  {'Time':>10}  {'Side':>4}  {'Price':>8}  {'Qty':>3}  {'Pos':>4}")
        print("  " + "-" * 40)
        for _, row in pep_t.iterrows():
            print(f"  {int(row['timestamp']):>10}  {row['side']:>4}  "
                  f"{row['price']:>8.1f}  {int(row['qty']):>3}  {int(row['pos']):>4}")
    print(f"  Final PEP pos : {position[PEP]}  (target: ~0 after close)")


#  UPGRADE 2 — Multi-day test: auto-discover all CSV files

if __name__ == "__main__":
    # Adjust this glob to wherever your CSVs live
    search_dirs = [
        r"C:\Users\Jagrati suyal\Downloads\ROUND_1\ROUND1",
        ".",       # also check current directory
    ]

    csv_files = []
    for d in search_dirs:
        csv_files.extend(
            glob.glob(os.path.join(d, "prices_round_1_day_*.csv"))
        )

    # De-duplicate and sort (day -2, -1, 0 will sort correctly as strings)
    csv_files = sorted(set(csv_files))

    if not csv_files:
        print("No CSV files found — check search_dirs in the script.")
    else:
        all_pnl = []
        for path in csv_files:
            r = run_strategy(path)
            print_results(r)
            all_pnl.append(r["portfolio_value"])

        if len(all_pnl) > 1:
            print("\n" + "=" * 60)
            print("  MULTI-DAY SUMMARY")
            print("=" * 60)
            for path, pv in zip(csv_files, all_pnl):
                tag = os.path.basename(path)
                status = "PROFIT" if pv > 0 else "LOSS"
                print(f"  {tag:45s}  {pv:>12,.2f}  {status}")
            print(f"\n  Profitable on {sum(p > 0 for p in all_pnl)}/{len(all_pnl)} days")
            print(f"  Average PnL : {np.mean(all_pnl):,.2f}")
            print(f"  Min PnL     : {min(all_pnl):,.2f}")
            print(f"  Max PnL     : {max(all_pnl):,.2f}")
