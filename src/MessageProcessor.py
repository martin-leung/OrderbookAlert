import json
import time
from datetime import datetime

class MessageProcessor:
    def __init__(self, liquidity_evaluator, alert_sender, threshold_percentage):
        self.liquidityEvaluator = liquidity_evaluator
        self.alertSender = alert_sender
        self.initial_alert_triggered = {}
        self.initial_alert_time = {}
        self.last_alert_time = {}
        self.DURATION_THRESHOLD_SECONDS = 60
        self.ALERT_FREQUENCY_SECONDS = 300
        self.THRESHOLD_PERCENTAGE = threshold_percentage

    def process_message(self, message, instrument_name, ):
        data = json.loads(message)
        params = data.get("params")
        if params and "data" in params:
            data = params["data"]
            bids = data.get("bids", [])
            asks = data.get("asks", [])
            eth_price = self.liquidityEvaluator.extract_eth_price(instrument_name)

            current_time = time.time()
            initial_alert_time_instrument = self.initial_alert_time.get(instrument_name, 0)
            last_alert = self.last_alert_time.get(instrument_name, 0)

            if not bids and not asks:
                self.handle_empty_bids_and_asks(instrument_name, current_time, initial_alert_time_instrument, last_alert)
                return

            if not bids:
                self.handle_empty_bids(instrument_name, current_time, initial_alert_time_instrument, last_alert)
                return

            if not asks:
                self.handle_empty_asks(instrument_name, current_time, initial_alert_time_instrument, last_alert)
                return

            if self.liquidityEvaluator.enough_bids_and_asks(bids, asks):
                self.handle_sufficient_liquidity(bids, asks, eth_price, instrument_name, current_time, initial_alert_time_instrument, last_alert)
            else:
                self.handle_insufficient_liquidity(bids, asks, instrument_name, current_time, initial_alert_time_instrument, last_alert)

    def handle_empty_bids_and_asks(self, instrument_name, current_time, initial_alert_time_instrument, last_alert):
        if not self.initial_alert_triggered.get(instrument_name, False):
            print("Initial Alert for empty bid and asks " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.initial_alert_triggered[instrument_name] = True
            self.initial_alert_time[instrument_name] = current_time
        elif current_time - initial_alert_time_instrument >= self.DURATION_THRESHOLD_SECONDS:
            if current_time - last_alert >= self.ALERT_FREQUENCY_SECONDS:
                self.alertSender.send_empty_alert(instrument_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.last_alert_time[instrument_name] = current_time

    def handle_empty_bids(self, instrument_name, current_time, initial_alert_time_instrument, last_alert):
        if not self.initial_alert_triggered.get(instrument_name, False):
            print("Initial Alert for empty bid " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.initial_alert_triggered[instrument_name] = True
            self.initial_alert_time[instrument_name] = current_time
        elif current_time - initial_alert_time_instrument >= self.DURATION_THRESHOLD_SECONDS:
            if current_time - last_alert >= self.ALERT_FREQUENCY_SECONDS:
                self.alertSender.send_bids_empty_alert(instrument_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.last_alert_time[instrument_name] = current_time

    def handle_empty_asks(self, instrument_name, current_time, initial_alert_time_instrument, last_alert):
        if not self.initial_alert_triggered.get(instrument_name, False):
            print("Initial Alert for empty ask " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.initial_alert_triggered[instrument_name] = True
            self.initial_alert_time[instrument_name] = current_time
        elif current_time - initial_alert_time_instrument >= self.DURATION_THRESHOLD_SECONDS:
            if current_time - last_alert >= self.ALERT_FREQUENCY_SECONDS:
                self.alertSender.send_asks_empty_alert(instrument_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.last_alert_time[instrument_name] = current_time

    def handle_sufficient_liquidity(self, bids, asks, eth_price, instrument_name, current_time, initial_alert_time_instrument, last_alert):
        spread_percentage = self.liquidityEvaluator.calculate_spread_percentage(bids, asks, eth_price)
        if spread_percentage >= self.THRESHOLD_PERCENTAGE:
            if not self.initial_alert_triggered.get(instrument_name, False):
                print("Initial Alert for " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Spread: " + str(spread_percentage))
                self.initial_alert_triggered[instrument_name] = True
                self.initial_alert_time[instrument_name] = current_time
            elif current_time - initial_alert_time_instrument >= self.DURATION_THRESHOLD_SECONDS:
                if current_time - last_alert >= self.ALERT_FREQUENCY_SECONDS:
                    self.alertSender.send_normal_alert(instrument_name, spread_percentage * 100, self.THRESHOLD_PERCENTAGE * 100, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    self.last_alert_time[instrument_name] = current_time
        else:
            self.initial_alert_triggered[instrument_name] = False
            if instrument_name in self.initial_alert_time:
                print("Reset: " + instrument_name + " Spread: " + str(spread_percentage))
                del self.initial_alert_time[instrument_name]
            if instrument_name in self.last_alert_time:
                print("Reset: " + instrument_name + " Spread: " + str(spread_percentage))
                del self.last_alert_time[instrument_name]

    def handle_insufficient_liquidity(self, bids, asks, instrument_name, current_time, initial_alert_time_instrument, last_alert):
        if not self.initial_alert_triggered.get(instrument_name, False):
            print(f"Initial Alert for {instrument_name}: Insufficient liquidity " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.initial_alert_triggered[instrument_name] = True
            self.initial_alert_time[instrument_name] = current_time
        elif current_time - initial_alert_time_instrument >= self.DURATION_THRESHOLD_SECONDS:
            if current_time - last_alert >= self.ALERT_FREQUENCY_SECONDS:
                if not bids:
                    total_depth = sum(float(ask[1]) for ask in asks)
                elif not asks:
                    total_depth = sum(float(bid[1]) for bid in bids)
                else:
                    total_bid_depth = sum(float(bid[1]) for bid in bids)
                    total_ask_depth = sum(float(ask[1]) for ask in asks)
                    total_depth = min(total_bid_depth, total_ask_depth)
                self.alertSender.send_insufficient_liquidity_alert(instrument_name, total_depth, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.last_alert_time[instrument_name] = current_time