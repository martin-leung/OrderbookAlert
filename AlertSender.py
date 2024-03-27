from datetime import datetime

class AlertSender:
    def __init__(self, bot_service):
        self.bot_service = bot_service

    def send_empty_alert(self, instrument_name):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Alert for {instrument_name}: Bids and Asks are empty.")
        self.bot_service.send_message(f"[{current_time}] Alert for {instrument_name}: Bids and Asks are empty.")

    def send_bids_empty_alert(self, instrument_name):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Alert for {instrument_name}: Bids are empty.")
        self.bot_service.send_message(f"[{current_time}] Alert for {instrument_name}: Bids are empty.")

    def send_asks_empty_alert(self, instrument_name):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Alert for {instrument_name}: Asks are empty.")
        self.bot_service.send_message(f"[{current_time}] Alert for {instrument_name}: Asks are empty.")

    def send_normal_alert(self, instrument_name, spread_percentage, threshold_percentage):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rounded_spread_percentage = round(spread_percentage, 4)
        print(f"[{current_time}] Spread of {instrument_name} is wider than {threshold_percentage}% ({rounded_spread_percentage} % spread)")
        self.bot_service.send_message(f"[{current_time}] Spread of {instrument_name} is wider than {threshold_percentage}% ({rounded_spread_percentage}% spread)")

    def send_insufficient_liquidity_alert(self, instrument_name, total_depth):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] BID/ASK for {instrument_name} only has {total_depth} depth")
        self.bot_service.send_message(f"[{current_time}] Spread of {instrument_name} is insufficient, BID / ASK only has {total_depth} depth")