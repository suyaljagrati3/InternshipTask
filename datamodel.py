from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class TradingState:
    def __init__(
        self,
        traderData: str,
        timestamp: int,
        listings: dict,
        order_depths: dict,
        own_trades: dict,
        market_trades: dict,
        position: dict,
        observations: dict,
    ):
        self.traderData    = traderData
        self.timestamp     = timestamp
        self.listings      = listings
        self.order_depths  = order_depths
        self.own_trades    = own_trades
        self.market_trades = market_trades
        self.position      = position
        self.observations  = observations

    def toJSON(self):
        import json
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)


class Order:
    def __init__(self, symbol: str, price: int, quantity: int):
        self.symbol   = symbol
        self.price    = price
        self.quantity = quantity

    def __repr__(self):
        return f"Order({self.symbol}, {self.price}, {self.quantity})"


class OrderDepth:
    def __init__(self):
        self.buy_orders:  Dict[int, int] = {}   # price → quantity
        self.sell_orders: Dict[int, int] = {}   # price → quantity


class Trade:
    def __init__(
        self,
        symbol: str,
        price: int,
        quantity: int,
        buyer:  Optional[str] = None,
        seller: Optional[str] = None,
        timestamp: int = 0,
    ):
        self.symbol    = symbol
        self.price     = price
        self.quantity  = quantity
        self.buyer     = buyer
        self.seller    = seller
        self.timestamp = timestamp

    def __repr__(self):
        return (
            f"Trade({self.symbol}, {self.price}, {self.quantity}, "
            f"{self.buyer}, {self.seller}, {self.timestamp})"
        )


class Listing:
    def __init__(self, symbol: str, product: str, denomination: str):
        self.symbol       = symbol
        self.product      = product
        self.denomination = denomination


class Observation:
    def __init__(
        self,
        plainValueObservations: Dict[str, int],
        conversionObservations: Dict[str, any],
    ):
        self.plainValueObservations = plainValueObservations
        self.conversionObservations = conversionObservations


class ConversionObservation:
    def __init__(
        self,
        bidPrice:       float,
        askPrice:       float,
        transportFees:  float,
        exportTariff:   float,
        importTariff:   float,
        sugarPrice:     float,
        sunlightIndex:  float,
    ):
        self.bidPrice      = bidPrice
        self.askPrice      = askPrice
        self.transportFees = transportFees
        self.exportTariff  = exportTariff
        self.importTariff  = importTariff
        self.sugarPrice    = sugarPrice
        self.sunlightIndex = sunlightIndex