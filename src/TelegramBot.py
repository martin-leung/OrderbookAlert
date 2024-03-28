import telebot
import time
import threading

class RateLimiter:
    def __init__(self, max_messages_per_second):
        self.max_messages_per_second = max_messages_per_second
        self.lock = threading.Lock()
        self.last_message_time = 0

    def acquire(self):
        with self.lock:
            current_time = time.time()
            elapsed_time = current_time - self.last_message_time
            if elapsed_time < self.max_messages_per_second:
                time.sleep(self.max_messages_per_second)
            self.last_message_time = time.time()

class TelegramBot:
    def __init__(self, bot_token, chat_id):
        self.bot = telebot.TeleBot(bot_token)
        self.chat_id = chat_id
        self.rate_limiter = RateLimiter(5)

    def send_message(self, message):
        self.rate_limiter.acquire()
        self.bot.send_message(self.chat_id, message)