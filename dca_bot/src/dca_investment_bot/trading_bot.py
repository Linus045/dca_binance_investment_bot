import time
import os
import requests
import datetime
from decimal import Decimal

from binance import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException

from binance_order import BinanceOrder

#TODO: Remove LOG_INFO calls from this file or convert to LOG_DEBUG.
from logger import LOG_DEBUG, LOG_ERROR_AND_NOTIFY, LOG_INFO, LOG_WARNING
from order_validator import OrderValidator
import global_vars

class TradingBot:
    def __init__(self, use_testnet=True):
        self.debug_tag = "[TradingBot]"
        self.connected = False
        self.use_testnet = use_testnet

        self.symbol_info_dict = {}
        self.sockets = []
        self.order_listeners = []

    def connect(self):
        # load key and secret from env and throw error if they are empty
        key = os.environ.get('BINANCE_KEY')
        secret = os.environ.get('BINANCE_SECRET')

        if key == None or secret == None:
            raise Exception('Binance key or secret is not set')

        if self.use_testnet:
            LOG_INFO(self.debug_tag, 'Using testnet to connect to binance')
        else:
            LOG_INFO(self.debug_tag, '!!!Using MAINNET!!!')

        self.connected = False
        while not self.connected:
            try: 
                self.client = Client(key, secret, testnet=self.use_testnet)
                self.connected = True
            except requests.exceptions.ConnectionError:
                LOG_WARNING("No internet connection... retrying in 10sec..")
                time.sleep(10)
    
    def check_connected(self):
        if not self.connected:
            LOG_ERROR_AND_NOTIFY(self.debug_tag,"Client not connected to Binance", 'Please call TradingBot::connect()')
            raise Exception('Binance client is not connected')

    def get_symbol_info(self, symbol):
        self.check_connected()
        if symbol in self.symbol_info_dict:
            return self.symbol_info_dict[symbol]
        else:
            symbol_info = self.client.get_symbol_info(symbol)
            self.symbol_info_dict[symbol] = symbol_info
            return symbol_info

    def close_all(self):
        pass

    def get_order_status(self, symbol, order_id):
        self.check_connected()
        return BinanceOrder(self.client.get_order(symbol=symbol, orderId=order_id))

    def create_limit_buy_order(self, symbol, limit, quantity) -> BinanceOrder:
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

    def invest_at_current_price(self, symbol: str, quote_amount: Decimal) -> BinanceOrder:
        price = self.get_avg_price(symbol)
        amount = quote_amount / price
        symbol_info = self.get_symbol_info(symbol)

        # round amount to match step size
        # get filter for LOT_SIZE
        filters = symbol_info['filters']
        lot_filter = [f for f in filters if f['filterType'] == 'LOT_SIZE'][0]
        if lot_filter is None:
            LOG_ERROR_AND_NOTIFY(self.debug_tag, 'No lot filter found for symbol {}'.format(symbol))
        else:
            lot_step_size = Decimal(lot_filter['stepSize'])
            amount = round(amount / lot_step_size) * lot_step_size

        price = round(round(price / 10) * 10)
        LOG_INFO('Investing {} at price {} for {}'.format(amount, price, symbol))
        try:
            quote_balance = self.get_asset_balance(symbol_info['quoteAsset'])
            if OrderValidator.check_order_possible(symbol_info, quote_balance, symbol, amount, price):
                return self.create_limit_buy_order(symbol, price, amount)
            else:
                LOG_ERROR_AND_NOTIFY(self.debug_tag, 'Investment not possible')
        except BinanceAPIException as e:
            LOG_ERROR_AND_NOTIFY(self.debug_tag, 'Failed to create investment order:', e)

            message_body = 'Failed to create investment order:\n' + \
                            'Symbol: {}\n'.format(symbol) + \
                            'Amount: {}\n'.format(amount) + \
                            'Price: {}\n'.format(price) + \
                            'Error: {}\n'.format(e)
            LOG_DEBUG(self.debug_tag, 'Sending push notification failed order:', message_body)

            # TODO: Move this to a separate function (event handler)
            if global_vars.firebaseMessager is not None:
                LOG_DEBUG(self.debug_tag, 'Sending push notification failed order:', message_body)
                global_vars.firebaseMessager.push_notification(title="Failed to create investment order", body=message_body)
        
        return None