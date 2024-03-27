import datetime
import time
from datetime import datetime
from flask import Flask, json
from InstrumentService import InstrumentService
from TelegramBot import TelegramBot
from LiquidityEvaluator import LiquidityEvaluator
from AlertSender import AlertSender
import asyncio
import websockets

app = Flask(__name__)

bot_token = "6494493719:AAH054SZmUbBAPzNjcIrQONhGXQVs3gUUAQ"
chat_id = "-4104771211"
bot_service = TelegramBot(bot_token, chat_id)
liquidityEvaluator = LiquidityEvaluator()
alertSender = AlertSender(bot_service)

THRESHOLD_PERCENTAGE = 0.02  #
DURATION_THRESHOLD_SECONDS = 60  # 60 seconds
ALERT_FREQUENCY_SECONDS = 300  # Frequency of subsequent alerts (every 5 minutes)

last_alert_time = {}
initial_alert_triggered = {}
initial_alert_time = {}

def process_message(message, instrument_name):
    data = json.loads(message)
    params = data.get("params")
    if params and "data" in params:
        data = params["data"]
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        eth_price = liquidityEvaluator.extract_eth_price(instrument_name)

        current_time = time.time()
        initial_alert_time_instrument = initial_alert_time.get(instrument_name, 0)
        last_alert = last_alert_time.get(instrument_name, 0)

        if not bids and not asks:
            handle_empty_bids_and_asks(instrument_name, current_time, initial_alert_time_instrument, last_alert)
            return

        if not bids:
            handle_empty_bids(instrument_name, current_time, initial_alert_time_instrument, last_alert)
            return

        if not asks:
            handle_empty_asks(instrument_name, current_time, initial_alert_time_instrument, last_alert)
            return

        if liquidityEvaluator.enough_bids_and_asks(bids, asks):
            handle_sufficient_liquidity(bids, asks, eth_price, instrument_name, current_time, initial_alert_time_instrument, last_alert)
        else:
            handle_insufficient_liquidity(bids, asks, instrument_name, current_time, initial_alert_time_instrument, last_alert)


def handle_empty_bids_and_asks(instrument_name, current_time, initial_alert_time_instrument, last_alert):
    if not initial_alert_triggered.get(instrument_name, False):
        print("Initial Alert for empty bid and asks " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        initial_alert_triggered[instrument_name] = True
        initial_alert_time[instrument_name] = current_time
    elif current_time - initial_alert_time_instrument >= DURATION_THRESHOLD_SECONDS:
        if current_time - last_alert >= ALERT_FREQUENCY_SECONDS:
            print("Alert for empty bid and asks " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # send_empty_alert(instrument_name)
            last_alert_time[instrument_name] = current_time


def handle_empty_bids(instrument_name, current_time, initial_alert_time_instrument, last_alert):
    if not initial_alert_triggered.get(instrument_name, False):
        print("Initial Alert for empty bid " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        initial_alert_triggered[instrument_name] = True
        initial_alert_time[instrument_name] = current_time
    elif current_time - initial_alert_time_instrument >= DURATION_THRESHOLD_SECONDS:
        if current_time - last_alert >= ALERT_FREQUENCY_SECONDS:
            print("Alert for empty bid " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # send_bids_empty_alert(instrument_name)
            last_alert_time[instrument_name] = current_time


def handle_empty_asks(instrument_name, current_time, initial_alert_time_instrument, last_alert):
    if not initial_alert_triggered.get(instrument_name, False):
        print("Initial Alert for empty ask " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        initial_alert_triggered[instrument_name] = True
        initial_alert_time[instrument_name] = current_time
    elif current_time - initial_alert_time_instrument >= DURATION_THRESHOLD_SECONDS:
        if current_time - last_alert >= ALERT_FREQUENCY_SECONDS:
            print("Alert for empty ask " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # send_asks_empty_alert(instrument_name)
            last_alert_time[instrument_name] = current_time

def handle_sufficient_liquidity(bids, asks, eth_price, instrument_name, current_time, initial_alert_time_instrument, last_alert):
    spread_percentage = liquidityEvaluator.calculate_spread_percentage(bids, asks, eth_price)
    if spread_percentage >= THRESHOLD_PERCENTAGE:
        if not initial_alert_triggered.get(instrument_name, False):
            # Initial alert, wait 60 seconds before sending
            print("Initial Alert for " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Spread: " + str(spread_percentage))
            initial_alert_triggered[instrument_name] = True
            initial_alert_time[instrument_name] = current_time
        elif current_time - initial_alert_time_instrument >= DURATION_THRESHOLD_SECONDS:
            if current_time - last_alert >= ALERT_FREQUENCY_SECONDS:
                # Trigger subsequent alert if 5 minutes have passed since last alert
                alertSender.send_normal_alert(instrument_name, spread_percentage, THRESHOLD_PERCENTAGE)
                last_alert_time[instrument_name] = current_time
    else:
        # Reset the alert if spread falls below threshold
        initial_alert_triggered[instrument_name] = False
        if instrument_name in initial_alert_time:
            print("Deleted: " + instrument_name + " Spread: " + str(spread_percentage))
            del initial_alert_time[instrument_name]
        if instrument_name in last_alert_time:
            print("Deleted: " + instrument_name + " Spread: " + str(spread_percentage))
            del last_alert_time[instrument_name]


def handle_insufficient_liquidity(bids, asks, instrument_name, current_time, initial_alert_time_instrument, last_alert):
    if not initial_alert_triggered.get(instrument_name, False):
        # Initial alert, wait 60 seconds before sending
        print(f"Initial Alert for {instrument_name}: Insufficient liquidity. Waiting for 60 seconds before sending." + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        initial_alert_triggered[instrument_name] = True
        initial_alert_time[instrument_name] = current_time
    elif current_time - initial_alert_time_instrument >= DURATION_THRESHOLD_SECONDS:
        if current_time - last_alert >= ALERT_FREQUENCY_SECONDS:
            if not bids:
                total_depth = sum(float(ask[1]) for ask in asks)
            elif not asks:
                total_depth = sum(float(bid[1]) for bid in bids)
            else:
                total_bid_depth = sum(float(bid[1]) for bid in bids)
                total_ask_depth = sum(float(ask[1]) for ask in asks)
                total_depth = min(total_bid_depth, total_ask_depth)
            alertSender.send_insufficient_liquidity_alert(instrument_name, total_depth)
            last_alert_time[instrument_name] = current_time

async def connect_and_subscribe(instrument_name):
    uri = "wss://api.lyra.finance/ws"
    group = "1"
    depth = "20"
    async with websockets.connect(uri) as websocket:
        # Construct the subscription request
        channel = f"orderbook.{instrument_name}.{group}.{depth}"
        subscription_request = {
            "method": "subscribe",
            "params": {
                "channels": [channel]
            }
        }
        print(subscription_request)
        await websocket.send(json.dumps(subscription_request))
        while True:
            message = await websocket.recv()
            # print("Received message:", message)
            process_message(message, instrument_name)


async def main():
    instruments_data = InstrumentService.get_instruments()
    if instruments_data:
        instrument_names = InstrumentService.extract_instrument_names(instruments_data)
        if instrument_names:
            min_key = min(instrument_names.keys())  # Find the minimum key
            min_instrument_names = instrument_names[min_key]  # Get instrument names corresponding to the minimum key
            tasks = [connect_and_subscribe(instrument_name) for instrument_name in min_instrument_names]
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())