from flask import json
from InstrumentService import InstrumentService
from TelegramBot import TelegramBot
from LiquidityEvaluator import LiquidityEvaluator
from AlertSender import AlertSender
from MessageProcessor import MessageProcessor
import threading
import asyncio
import websockets

bot_token = "6494493719:AAH054SZmUbBAPzNjcIrQONhGXQVs3gUUAQ"
chat_id = "-1001994721570"
spread_amount = 25
threshold_percentage = 0.05
bot_service = TelegramBot(bot_token, chat_id)
liquidityEvaluator = LiquidityEvaluator(spread_amount)
alertSender = AlertSender(bot_service)
messageProcessor = MessageProcessor(liquidityEvaluator, alertSender, threshold_percentage)

def connect_and_subscribe(instrument_name):
    async def subscribe():
        uri = "wss://api.lyra.finance/ws"
        group = "10"
        depth = "20"
        while True:
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
                        messageProcessor.process_message(message, instrument_name)
                        await asyncio.sleep(2)
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Connection closed unexpectedly for {instrument_name}. Retrying...")
                await asyncio.sleep(10)
    asyncio.run(subscribe())

def main():
    instruments_data = InstrumentService.get_instruments()
    if instruments_data:
        instrument_names = InstrumentService.extract_instrument_names(instruments_data)
        if instrument_names:
            sorted_dates = sorted(instrument_names.keys())
            if len(sorted_dates) > 1:
                second_lowest_date = sorted_dates[1]
                min_instrument_names = instrument_names[second_lowest_date]
                threads = []
                for instrument_name in min_instrument_names:
                    thread = threading.Thread(target=connect_and_subscribe, args=(instrument_name,))
                    threads.append(thread)
                    thread.start()
                for thread in threads:
                    thread.join()

if __name__ == "__main__":
    main()