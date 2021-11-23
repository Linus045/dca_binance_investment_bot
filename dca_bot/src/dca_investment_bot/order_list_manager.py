import os
import json

from logger import LOG_DEBUG, LOG_INFO, LOG_WARNING_AND_NOTIFY, LOG_ERROR_AND_NOTIFY, LOG_CRITICAL_AND_NOTIFY
from binance_order import BinanceOrder

'''
Manages the fulfilled, unfufilled orders.
Reads them from a file, and writes them to a file.
'''
class OrderListManager:
    
    def __init__(self, order_filepath : str) -> None:
        self._debug_tag = '[OrderListManager]'
        self._unfulfilled_orders = []
        self._fulfilled_orders = []
        self._order_filepath = order_filepath
        self.__create_path()
            
    def load_fulfilled_from_file(self) -> None:
        '''
        Loads the orders from the file.
        '''
        if os.path.isfile(self._order_filepath):
            with open(self._order_filepath) as f:
                json_orders = json.load(f)
                self._fulfilled_orders = [BinanceOrder(o) for o in json_orders]
        else:
            self._fulfilled_orders = []

    def store_orders_to_file(self) -> None:
        '''
        Stores the orders to the file.
        '''
        with open(self._order_filepath, 'w') as f:
            json_orders = [o.asDict() for o in self._fulfilled_orders]
            json.dump(json_orders, f, indent=4, ensure_ascii=False)

    def __create_path(self):
        if not os.path.exists(self._order_filepath):
            os.makedirs(self._order_filepath)

    def unfulfilled_orders(self) -> list:
        return self._unfulfilled_orders

    def fulfilled_orders(self) -> list:
        return self._fulfilled_orders

    def add_new_order(self, new_order : BinanceOrder) -> None:
        '''
        Adds a new order to the list of unfulfilled orders.
        '''
        self._unfulfilled_orders.append(new_order)

    def print_orders(self, orders : list) -> None:
        '''
        Prints the orders.
        '''
        if len(orders) > 0:
            LOG_INFO("------------------------------------------------")
            for order in orders:
                LOG_INFO(order.to_info_string())
            LOG_INFO("------------------------------------------------")
        else:
            LOG_INFO("NO ORDERS")
