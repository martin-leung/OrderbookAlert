class LiquidityEvaluator:
    def calculate_effective_price(self, orderbook, spread_amount):
        total_amount = 0
        weighted_price = 0
        for price, amount in orderbook:
            price = float(price)
            amount = min(float(amount), spread_amount - total_amount)
            total_amount += amount
            weighted_price += price * amount
            if total_amount >= spread_amount:
                break
        return weighted_price / spread_amount if spread_amount != 0 else 0

    def calculate_spread_percentage(self, bids, asks, eth_price):
        spread_amount = 10
        effective_bid_price = self.calculate_effective_price(bids, spread_amount)
        effective_ask_price = self.calculate_effective_price(asks, spread_amount)
        spread = effective_ask_price - effective_bid_price
        spread_percentage = abs(spread / eth_price)
        return spread_percentage

    def extract_eth_price(self, instrument_name):
        parts = instrument_name.split("-")
        if len(parts) >= 3:
            return int(parts[2])
        else:
            return None

    def enough_bids_and_asks(self, bids, asks):
        min_spread_amount = 10  # Minimum spread amount required for calculation
        total_bids = sum(float(amount) for _, amount in bids)
        total_asks = sum(float(amount) for _, amount in asks)
        return total_bids >= min_spread_amount and total_asks >= min_spread_amount