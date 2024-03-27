from flask import Flask, json
from InstrumentService import InstrumentService
from TelegramBot import TelegramBot
from LiquidityEvaluator import LiquidityEvaluator
from AlertSender import AlertSender
from MessageProcessor import MessageProcessor
import asyncio
import websockets

app = Flask(__name__)

bot_token = "6494493719:AAH054SZmUbBAPzNjcIrQONhGXQVs3gUUAQ"
chat_id = "-4104771211"
spread_amount = 10
threshhold_percentage = 0.02
bot_service = TelegramBot(bot_token, chat_id)
liquidityEvaluator = LiquidityEvaluator(spread_amount)
alertSender = AlertSender(bot_service)
messageProcessor = MessageProcessor(liquidityEvaluator, alertSender, threshhold_percentage)

async def connect_and_subscribe(instrument_name, retry_count=3):
    uri = "wss://api.lyra.finance/ws"
    group = "1"
    depth = "20"
    while retry_count > 0:
        try:
            async with websockets.connect(uri) as websocket:
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
                    # print(message)
                    messageProcessor.process_message(message, instrument_name)
        except websockets.exceptions.ConnectionClosedError:
            print(f"Connection closed unexpectedly for {instrument_name}. Retrying...")
            retry_count -= 1
            await asyncio.sleep(15)
    print(f"Failed to connect to {instrument_name} after multiple retries.")


# async def main():
#     instruments_data = InstrumentService.get_instruments()
#     if instruments_data:
#         instrument_names = InstrumentService.extract_instrument_names(instruments_data)
#         if instrument_names:
#             min_key = min(instrument_names.keys())  # Find the minimum key
#             min_instrument_names = instrument_names[min_key]  # Get instrument names corresponding to the minimum key
#             tasks = [connect_and_subscribe(instrument_name) for instrument_name in min_instrument_names]
#             await asyncio.gather(*tasks)

async def main():
    # await asyncio.gather(
    #     connect_and_subscribe("ETH-20240328-3750-P"),
    #     connect_and_subscribe("ETH-20240328-4200-P"),
    #     connect_and_subscribe("ETH-20240328-3350-P")
    # )
    instruments_data = InstrumentService.get_instruments()
    if instruments_data:
        instrument_names = InstrumentService.extract_instrument_names(instruments_data)
        if instrument_names:
            sorted_keys = sorted(instrument_names.keys())
            if len(sorted_keys) >= 2:
                second_min_key = sorted_keys[1]  # Second minimum key
                min_instrument_names = instrument_names[second_min_key]
                tasks = [connect_and_subscribe(instrument_name) for instrument_name in min_instrument_names]
                await asyncio.gather(*tasks)
            else:
                print("There are not enough instruments to find the second minimum key.")

if __name__ == "__main__":
    asyncio.run(main())