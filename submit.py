import json
import numpy as np
from datamodel import OrderDepth, TradingState, Order
from typing import List

class Trader:

    OSM = "ASH_COATED_OSMIUM"
    PEP = "INTARIAN_PEPPER_ROOT"

    def run(self, state: TradingState):
        # Load persisted state
        data = json.loads(state.traderData) if state.traderData else {}
        pep_bought = data.get("pep_bought", False)

        result = {}

        for product, order_depth in state.order_depths.items():
            orders: List[Order] = []
            pos = state.position.get(product, 0)

            if not order_depth.buy_orders or not order_depth.sell_orders:
                continue

            best_bid = max(order_depth.buy_orders)
            best_ask = min(order_depth.sell_orders)

            # ── OSMIUM: fixed threshold mean reversion ──────────
            if product == self.OSM:
                LIMIT = 20

                # BUY when ask is cheap
                if best_ask <= 9999 and pos < LIMIT:
                    qty = min(3, LIMIT - pos)
                    orders.append(Order(product, best_ask, qty))

                # SELL when bid is rich, but don't go too short
                elif best_bid >= 10004 and pos > -5:
                    qty = min(3, pos + 5)
                    if qty > 0:
                        orders.append(Order(product, best_bid, -qty))

            # ── PEPPER: buy dips, hold inventory ───────────────
            elif product == self.PEP:
                LIMIT = 35

                # Always accumulate up to limit
                if pos < LIMIT:
                    qty = min(5, LIMIT - pos)
                    orders.append(Order(product, best_ask, qty))

            result[product] = orders

        # Persist state
        trader_data = json.dumps({"pep_bought": True})
        return result, 0, trader_data