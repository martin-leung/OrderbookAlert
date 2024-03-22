from flask import Flask, json
from TelegramBot import TelegramBotService
import asyncio
import websockets
import requests

app = Flask(__name__)

bot_token = "6494493719:AAH054SZmUbBAPzNjcIrQONhGXQVs3gUUAQ"
chat_id = "-4104771211"
bot_service = TelegramBotService(bot_token, chat_id)


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

async def connect_and_subscribe():
    uri = "wss://api.lyra.finance/ws"
    instrument_name = "ETH-PERP"

    group = "1"
    depth = "10"

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
            # bot_service.send_message(message)
            print("Received message:", message)

async def main():
    await connect_and_subscribe()

if __name__ == "__main__":
    asyncio.run(main())
