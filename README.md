# OrderbookAlert

Spread Percentage is set to 5% (0.05)
Depth is set to 50 (25 bids/25 asks)

For all alerts, initial alert is sent after 1 minute of consistent status (spread percentage, empty bids/asks, etc). Every subsequent alert is 5 minutes unless the status is reset. 

TG messages are currently limited to 1 message per ~5 seconds to avoid TG bot API limit errors. 

It's set to monitor the second lowest day. If March 28, 29 and Apr 5, 12 it will monitor March 29. 

Docker commands:
docker build -t my-python-app .
docker run -it my-python-app

Can also directly run main.py. 

TG channel bot sends alert to:
https://t.me/+PKaHTTGxOu42NTRh


To add:
Customizable spread percentage, depth, chat id, day to monitor, etc. 
