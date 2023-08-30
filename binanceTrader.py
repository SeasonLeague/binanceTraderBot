import pyttsx3 
import time
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
from awesome_progress_bar import ProgressBar


engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
engine.setProperty('rate', 150)

print("INITIATING THE BINANCE TRADE BOT...")
engine.say("INITIATING THE BINANCE TRADE BOT...")

# engine.stop()

total = 10
bar = ProgressBar(total, bar_length=10, fill='*', suffix=' Appended', prefix='Progress', time_format='mm:ss')
for x in range(total):
    time.sleep(.2)
    bar.iter()

print(F"\nBOT Started at {time.ctime()}...\n")
time.sleep(.2)

class TradingBot:
    def __init__(self, api_key, api_secret, symbol, budget, leverage):
        self.client = Client(api_key=api_key, api_secret=api_secret)
        self.symbol = symbol
        self.budget = budget
        self.leverage = leverage
        self.profit = 0
        self.starting_balance = 0
        self.current_balance = 0
        self.days_trading = 0
        self.start_time = time.time()
        self.is_in_position = False

    def get_current_price(self):
        ticker = self.client.futures_mark_price(symbol=self.symbol)
        return float(ticker['markPrice'])

    def calculate_quantity_to_buy(self):
        account_balance = self.client.futures_account_balance()
        balances = float(next((item['balance']) for item in account_balance if item['asset'] == 'USDT'))
        available_budget = min(self.budget, balances)
        if available_budget > 0:
            price = self.get_current_price()
            notional_value = 0.02 * available_budget  # Allocate 2% of the available budget for buying
            quantity = notional_value / price
            symbol_info = self.client.futures_exchange_info()
            symbol_precision = next(
                (symbol['quantityPrecision'] for symbol in symbol_info['symbols'] if symbol['symbol'] == self.symbol),
                0
            )
            if symbol_precision is not None:
                quantity = round(quantity, symbol_precision)
                return quantity
        return 0

    def market_buy(self, quantity):
        try:
            order = self.client.futures_create_order(
                symbol=self.symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantity,
                newOrderRespType=ORDER_RESP_TYPE_FULL
            )
            return float(order['price'])
        except BinanceAPIException as e:
            print(f"An error occurred while placing the buy order: {e}")
            return None

    def market_sell(self, quantity, take_profit_price):
        try:
            order = self.client.futures_create_order(
                symbol=self.symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_LIMIT,
                quantity=quantity,
                timeInForce=TIME_IN_FORCE_GTC,
                price=take_profit_price,
                newOrderRespType=ORDER_RESP_TYPE_FULL
            )
            return order
        except BinanceAPIException as e:
            print(f"An error occurred while placing the sell order: {e}")
            return None

    def calculate_take_profit_price(self, buy_price):
        take_profit_price = buy_price * 1.03  # Set take-profit at 3% above the buy price
        return take_profit_price

    def update_profit(self, order):
        executed_qty = float(order['executedQty'])
        sell_price = float(order['price'])
        buy_price = sell_price / 1.02  # Assuming 2% profit target
        trade_profit = (sell_price - buy_price) * executed_qty
        self.profit += trade_profit
        self.current_balance += trade_profit
        self.days_trading = (time.time() - self.start_time) / (24 * 60 * 60)  # Calculate number of days trading
        print(f"Trade Profit: {trade_profit}")
        print(f"Total Profit: {self.profit}")
        print(f"Profit per Day: {self.profit / self.days_trading:.2f}")


    def get_account_balance(self):
        account_info = self.client.futures_account()
        balance = account_info['assets']
        balance = next((item['availableBalance']) for item in balance if item['asset'] == 'USDT')
        return float(balance)


    def run(self):
        self.starting_balance = self.get_account_balance()
        self.current_balance = self.starting_balance

        while True:
            current_price = self.get_current_price()
            moving_average = self.calculate_moving_average()

            if current_price > moving_average and not self.is_in_position:
                quantity = self.calculate_quantity_to_buy()
                if quantity > 0:
                    buy_price = self.market_buy(quantity)
                    if buy_price:
                        take_profit_price = self.calculate_take_profit_price(buy_price)
                        sell_order = self.market_sell(quantity, take_profit_price)
                        if sell_order:
                            self.update_profit(sell_order)
                            self.is_in_position = False

            print("Waiting for the next iteration...")
            time.sleep(900)  # Sleep for 900 seconds (15 minutes) which you can adjust to fit your own taste
    
    def calculate_moving_average(self):
        kline = self.client.futures_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=1)
        close_prices = [float(kline[4]) for kline in kline]
        return sum(close_prices) / len(close_prices)

    # Other methods (get_account_balance, calculate_moving_average, etc.) go here...

# Main entry point

# Main entry point
if __name__ == "__main__":
    api_key = 'Add Binance API Key here'
    api_secret = 'Add Binance API Secret Here'
    
    client = Client(api_key=api_key, api_secret=api_secret)
    server_time = client.futures_time()['serverTime']
    client.timestamp = server_time  

    # symbol = 'XRPUSDT'
    # budget = 20

    bot = TradingBot(api_key=api_key, api_secret=api_secret, symbol='BTCUSDT', budget=10, leverage=1)
    engine.runAndWait()
    bot.run()