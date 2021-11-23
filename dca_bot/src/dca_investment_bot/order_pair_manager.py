import os
import json

from binance_order import BinanceOrder

ORDER_PAIR_DIRECTORY = 'order_pairs'

'''NOT FUNCTIONAL YET! IDEA:Stores and Loads orders for a given pair'''
class OrderPairManager:
    def __init__(self):
        self.create_order_pair_directory_if_no_exist()
        
    def get_symbol_filename(self, symbol):
        return "pair_{0}.json".format(symbol)

    def get_symbol_filepath(self, symbol):
        return os.path.join(ORDER_PAIR_DIRECTORY, self.get_symbol_filename(symbol))

    def create_order_pair_directory_if_no_exist(self):
        if not os.path.exists(ORDER_PAIR_DIRECTORY):
            os.makedirs(ORDER_PAIR_DIRECTORY)

    def store_pair(self,symbol, limit_order, oco_order):
        self.create_order_pair_directory_if_no_exist()
        file_path = self.get_symbol_filepath(symbol)
        if os.path.exists(file_path):
            os.remove(file_path)

        with open(file_path,'w') as file:
            order_pair = {
                'symbol' : symbol,
                'limit_order' : limit_order,
                'oco_order' : oco_order
            }
            json.dump(order_pair, file, ensure_ascii=False, indent=4)

    def load_pair(self,symbol):
        file_path = self.get_symbol_filepath(symbol)
        if os.path.exists(file_path):
            if os.path.getsize(file_path) > 0:
                with open(file_path,'r') as file:
                    #TODO: Validate read json
                    order_pair = json.load(file)
                    return {
                        'symbol' : order_pair['symbol'],
                        'limit_order' : BinanceOrder(order_pair['limit_order']),
                        'oco_order' : BinanceOrder(order_pair['oco_order'])
                    }
            else:
                print("ORDER_PAIR_MANAGER::load_pair - file {0} is empty and gets removed".format(file_path))
                self.remove_pair(symbol)

    def remove_pair(self, symbol):
        file_path = self.get_symbol_filepath(symbol)
        if os.path.exists(file_path):
            os.remove(file_path)



                