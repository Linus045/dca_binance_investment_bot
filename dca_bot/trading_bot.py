import time
import os
import datetime
import requests
from decimal import Decimal
from threading import Thread, Event
from dotenv import load_dotenv

from binance import Client
from binance.enums import *

from binance_order import BinanceOrder
from logger import LOG_DEBUG, LOG_ERROR, LOG_INFO, LOG_WARNING
import global_vars

# currently not used
from binance import ThreadedWebsocketManager
from order_pair_manager import OrderPairManager

    
# class OrderCheckerEventThread(Thread):
#     """
#     Constantly checks if an order has been filled and notifies listeners
#     Thread class with a stop() method. The thread itself has to check
#     regularly for the stopped() condition.
#     """

#     def __init__(self,  *args, **kwargs):
#         super(OrderCheckerEventThread, self).__init__(*args, **kwargs)
#         self._stop_event = Event()
#         self.orders = []
#         self.bot = None

#     def close_thread(self):
#         self._stop_event.set()

#     def stopped(self):
#         return self._stop_event.is_set()

#     def init_trading_bot(self, traiding_bot):
#         self.bot = traiding_bot
    
#     def run(self):
#         while not self.stopped():
#             if self.bot == None:
#                 LOG_ERROR("NO BOT SET!!!")
            
#             new_orders = self.bot.get_orders()
#             #self.bot.print_orders(new_orders)

#             for new_order in new_orders:
#                 order_exists = False
#                 for old_order in self.orders:
#                     if new_order == old_order:
#                         order_exists = True
#                         break

#                 if not order_exists:
#                     self.orders.append(new_order)
#                     LOG_INFO("New Order found",new_order.orderId, new_order.status)                   
#                     self.bot.notify_order(new_order)

#                 elif not order_exists:
#                     LOG_INFO("Order Update:", old_order.status, new_order.status)
#                     if order_status == ORDER_STATUS_FILLED or order_status == ORDER_STATUS_PARTIALLY_FILLED:
#                         self.bot.notify_order(new_order)
#                     else:
#                         LOG_ERROR("ORDER UPDATE:UNKNOWN STATUS UPDATE:  ", order_status)
                
#             time.sleep(5)


class TradingBot:

    def __init__(self):
        self.debug_tag = "TradingBot"
        self.connected = False

        # load environment variables
        dotEnvPath = os.path.join('configs', '.env')
        if os.path.exists(dotEnvPath):
            load_dotenv(dotEnvPath)
        else:
            LOG_WARNING(self.debug_tag, "No .env file found at {}", dotEnvPath)

        self.symbol_info_dict = {}
        self.sockets = []
        self.order_listeners = []

        # self.order_pair_manager = OrderPairManager()

    def connect(self):
        # load key and secret from env and throw error if they are empty
        key = os.environ.get('BINANCE_KEY')
        secret = os.environ.get('BINANCE_SECRET')

        if key == None or secret == None:
            raise Exception('Binance key or secret is not set')

        self.connected = False
        while not self.connected:
            try: 
                self.client = Client(key, secret, testnet=True)
                self.connected = True

                # self.threadedWebsocketManager = ThreadedWebsocketManager(api_key=key, api_secret=secret, testnet=True)
                # self.threadedWebsocketManager.start()
            except requests.exceptions.ConnectionError:
                LOG_WARNING("No internet connection... retrying in 10sec..")
                connected = False
                time.sleep(10)
    
    def check_connected(self):
        if not self.connected:
            LOG_ERROR(self.debug_tag,"Client not connected to Binance", 'Please call TradingBot::connect()')
            raise Exception('Binance client is not connected')

    def get_symbol_info(self, symbol):
        self.check_connected()
        if symbol in self.symbol_info_dict:
            return self.symbol_info_dict[symbol]
        else:
            symbol_info = self.client.get_symbol_info(symbol)
            self.symbol_info_dict[symbol] = symbol_info
            return symbol_info

    # def start_order_listener(self):
    #     self.check_connected()
    #     self.order_change_checker = OrderCheckerEventThread()
    #     self.order_change_checker.init_trading_bot(self)
    #     self.order_change_checker.start()

    # def get_fullfilled_orders(self):
    #     self.check_connected()
    #     #starttime is 12 weeks ago
    #     start_time = int(time.time() - 12*7*24*60*60)
    #     end_time = int(time.time())
        
    #     #print start and end time as date
    #     start_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    #     end_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
    #     LOG_INFO("Start Date:", start_date)
    #     LOG_INFO("End Date:", end_date)
    #     #return self.client.get_all_orders(symbol=self.symbol, start_time=start_time, end_time=end_time)
    #     raise Exception("Not implemented")

    # def register_mark_price_listener(self, callback):
    #     socket = self.threadedWebsocketManager.start_symbol_mark_price_socket(callback=callback, symbol=self.symbol)
    #     self.sockets.append(socket)

    def close_all(self):
        # if self.order_change_checker.is_alive():
        #     self.order_change_checker.close_thread()
        #     self.order_change_checker.join()

        # for socket in self.sockets:
        #     self.threadedWebsocketManager.stop_socket(socket)
        # self.threadedWebsocketManager.stop()
        pass

    def get_order_status(self, symbol, order_id):
        self.check_connected()
        return BinanceOrder(self.client.get_order(symbol=symbol, orderId=order_id))

    # def notify_order(self,order_info):
    #     for listener_callback in self.order_listeners:
    #         listener_callback(order_info)

    # def register_order_listener_callback(self, listener_callback):
    #     self.order_listeners.append(listener_callback)

    # def create_oco_sell_order(self,symbol, price, quantity, stop_price):
    #     self.check_connected()
    #     return BinanceOrder(self.client.create_oco_order(
    #         symbol=symbol,
    #         side=SIDE_SELL,
    #         quantity=quantity,
    #         price=price,
    #         stopPrice=stop_price))

    # def create_market_sell_order(self, symbol, price, quantity, stop_price):
    #     self.check_connected()
    #     return BinanceOrder(self.client.create_order(
    #         symbol=symbol,
    #         side=SIDE_SELL,
    #         type=ORDER_TYPE_LIMIT,
    #         timeInForce=TIME_IN_FORCE_GTC,
    #         quantity=quantity,
    #         price=price))

    def create_limit_buy_order(self, symbol, limit, quantity):
        self.check_connected()
        return  BinanceOrder(self.client.create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=str(limit)))
    
    def cancel_order(self, symbol, order_id):
        self.check_connected()
        LOG_INFO(self.client.cancel_order(symbol=symbol, orderId=order_id))

    def print_order(self, order_type, order_id, date, status, side, symbol, price, quantity):
        price = Decimal(price)
        quantity = Decimal(quantity)
        if date != None:
            date = datetime.datetime.fromtimestamp(date/1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            date = "N/A"

        LOG_INFO("| {}-Order | {} | {} | {} | {} | {} | Price: {} | Quantity: {} | Calculated value in quote (price*quantity): {}".format(order_type, order_id, date, status, side, symbol, price, quantity, price*quantity))

    def print_orders(self,orders):
        if len(orders) > 0:
            LOG_INFO("------------------------------------------------")
            for order in orders:
                status = order.status
                order_id = order.orderId
                type = order.type
                side = order.side
                symbol = order.symbol
                price = order.price
                quantity = order.origQty
                date = order.time
                self.print_order(type, order_id, date, status, side, symbol, price, quantity)
            LOG_INFO("------------------------------------------------")
        else:
            LOG_INFO("NO ORDERS")
        
    def print_orders_object(self,orders):
        if len(orders) > 0:
            LOG_INFO("------------------------------------------------")
            for order in orders:
                status = order['status']
                order_id = order['orderId']
                type = order['type']
                side = order['side']
                symbol = order['symbol']
                price = order['price']
                quantity = order['origQty']
                date = order['time']
                self.print_order(type, order_id, date, status, side, symbol, price, quantity)
                LOG_INFO("------------------------------------------------")
        else:
            LOG_INFO("NO ORDERS")

    def get_asset_balance(self, asset : str):
        self.check_connected()
        return Decimal(self.client.get_asset_balance(asset)['free'])
   
    def get_orders(self, symbol : str):
        self.check_connected()
        orders = []
        for order in self.client.get_open_orders(symbol=symbol):
            orders.append(BinanceOrder(order))
        return orders

    def get_avg_price(self, symbol : str):
        self.check_connected()
        return Decimal(self.client.get_avg_price(symbol=symbol)['price'])

    def cancel_all_orders_for_symbol(self, symbol : str):
        for order in self.get_orders(symbol):
            self.cancel_order(symbol, order.orderId)
        # self.order_change_checker.orders.clear()


