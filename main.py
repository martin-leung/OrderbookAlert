import datetime
import time
from datetime import datetime
from flask import Flask, json
from TelegramBot import TelegramBotService
import asyncio
import websockets
import requests

app = Flask(__name__)

bot_token = "6494493719:AAH054SZmUbBAPzNjcIrQONhGXQVs3gUUAQ"
chat_id = "-4104771211"
bot_service = TelegramBotService(bot_token, chat_id)

THRESHOLD_PERCENTAGE = 0.0002  # 30
DURATION_THRESHOLD_SECONDS = 60  # 60 seconds

ALERT_FREQUENCY_SECONDS = 300  # Frequency of subsequent alerts (every 5 minutes)

# Store last alert time for each instrument to avoid sending repeated alerts
last_alert_time = {}

ETH_PRICE = 3500  # Sample ETH price
initial_alert_triggered = {}
initial_alert_time = {}

initial_alert_lock = asyncio.Lock()
last_alert_lock = asyncio.Lock()

@app.route('/')
def send_test_message():
    bot_service.send_message("Test message from main.py")
    return "Message sent successfully from main.py"


def get_instruments():
    url = "https://api.lyra.finance/public/get_instruments"
    params = {
        "expired": "false",
        "instrument_type": "option",
        "currency": "ETH"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()  # Parse response as JSON
        return data
    except requests.exceptions.RequestException as e:
        print("Error making request:", e)
        return None

def extract_instrument_names(response):
    try:
        instrument_map = {}
        for item in response["result"]:
            instrument_name = item["instrument_name"]
            key = instrument_name.split("-")[1]  # Extract the substring "20240531" from the instrument name
            if key not in instrument_map:
                instrument_map[key] = []
            instrument_map[key].append(instrument_name)
        print(instrument_map)
        return instrument_map
    except KeyError as e:
        print("KeyError:", e)
        return None


def calculate_effective_price(orderbook, spread_amount):
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

def calculate_spread_percentage(bids, asks):
    # Assuming spread amount of 25
    spread_amount = 25
    effective_bid_price = calculate_effective_price(bids, spread_amount)
    effective_ask_price = calculate_effective_price(asks, spread_amount)
    spread = effective_ask_price - effective_bid_price
    spread_percentage = spread / ETH_PRICE
    return spread_percentage

def process_message(message, instrument_name):
    data = json.loads(message)
    params = data.get("params")
    if params and "data" in params:
        data = params["data"]
        bids = data.get("bids", [])
        asks = data.get("asks", [])

        if bids and asks:
            spread_percentage = calculate_spread_percentage(bids, asks)
            current_time = time.time()
            initial_alert_time_instrument = initial_alert_time.get(instrument_name, 0)
            last_alert = last_alert_time.get(instrument_name, 0)
            if spread_percentage >= THRESHOLD_PERCENTAGE:
                if not initial_alert_triggered.get(instrument_name, False):
                    # Initial alert, wait 60 seconds before sending
                    initial_alert_triggered[instrument_name] = True
                    initial_alert_time[instrument_name] = current_time
                    print("Initial Alert for " + instrument_name + " found at time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print(bids)
                    print(asks)
                elif current_time - initial_alert_time_instrument >= DURATION_THRESHOLD_SECONDS:
                    if current_time - last_alert >= ALERT_FREQUENCY_SECONDS:
                        # Trigger subsequent alert if 5 minutes have passed since last alert
                        send_alert(instrument_name, spread_percentage)
                        print(bids)
                        print(asks)
                        last_alert_time[instrument_name] = current_time
            else:
                # Reset the alert if spread falls below threshold
                initial_alert_triggered[instrument_name] = False
                if instrument_name in initial_alert_time:
                    del initial_alert_time[instrument_name]
                if instrument_name in last_alert_time:
                    del last_alert_time[instrument_name]

def send_alert(instrument_name, spread_percentage):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] Spread of {instrument_name} is wider than {THRESHOLD_PERCENTAGE}% ( {spread_percentage} % spread)")
    bot_service.send_message(f"[{current_time}] Spread of {instrument_name} is wider than {THRESHOLD_PERCENTAGE}% ( {spread_percentage} % spread)")


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

        # Send the subscription request
        await websocket.send(json.dumps(subscription_request))

        # Continuously receive and process messages from the WebSocket server
        while True:
            message = await websocket.recv()
            # print("Received message:", message)
            process_message(message, instrument_name)


async def main():
    instruments_data = get_instruments()
    if instruments_data:
        instrument_names = extract_instrument_names(instruments_data)
        if instrument_names:
            min_key = min(instrument_names.keys())  # Find the minimum key
            min_instrument_names = instrument_names[min_key]  # Get instrument names corresponding to the minimum key
            tasks = [connect_and_subscribe(instrument_name) for instrument_name in min_instrument_names]
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("start")
    asyncio.run(main())