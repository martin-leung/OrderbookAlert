import requests

class InstrumentService:
    @staticmethod
    def get_instruments():
        url = "https://api.lyra.finance/public/get_instruments"
        params = {
            "expired": "false",
            "instrument_type": "option",
            "currency": "ETH"
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print("Error making request:", e)
            return None

    @staticmethod
    def extract_instrument_names(response):
        try:
            instrument_map = {}
            for item in response["result"]:
                instrument_name = item["instrument_name"]
                key = instrument_name.split("-")[1]
                if key not in instrument_map:
                    instrument_map[key] = []
                instrument_map[key].append(instrument_name)
            print(instrument_map)
            return instrument_map
        except KeyError as e:
            print("KeyError:", e)
            return None