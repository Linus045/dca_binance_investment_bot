from logging import debug
import requests
import time
import os
import threading
import datetime
import json
import time
import traceback
import signal
from decimal import Decimal, getcontext

from binance.enums import *
from binance.enums import ORDER_TYPE_LIMIT
from binance.exceptions import BinanceAPIException

from firebase.firebase_storage import FirebaseStorage
from firebase.firebase_messager import FirebaseMessager

import global_vars
from dotenv import load_dotenv
from trading_bot import TradingBot
from dca_investment_parameter import *
from binance_order import BinanceOrder
from logger import init_logger, LOG_INFO, LOG_ERROR, LOG_DEBUG, LOG_WARNING, LOG_CRITICAL

def load_last_orders(filepath : str):
    if os.path.isfile(filepath):
        with open(filepath) as f:
            json_orders = json.load(f)
            orders = [BinanceOrder(o) for o in json_orders]
            return orders
    else:
        return []

unfullfilled_orders = []
# set precision for Decimal to 8 since most numbers in binance use max 8 digits
getcontext().prec = 8


def check_order_possible(bot : TradingBot, amount : Decimal, price : Decimal, symbol : str):
    symbol_info = bot.get_symbol_info(symbol)
    filter_info = symbol_info['filters']

    debug_tag = '[Order Validation]'
    LOG_DEBUG(debug_tag, symbol, 'Filter Info: \n', filter_info)

    # check if price is in filter
    price_filter = [f for f in filter_info if f['filterType'] == 'PRICE_FILTER'][0]
    if price_filter is None:
        LOG_ERROR(debug_tag, 'No price filter found for symbol {}'.format(symbol))
        return False
    else:
        if price < Decimal(price_filter['minPrice']) or price > Decimal(price_filter['maxPrice']):
            LOG_ERROR(debug_tag, 'Price {} is not in price filter for symbol {} [{}-{}]'.format(price, symbol, price_filter['minPrice'], price_filter['maxPrice']))
            return False
        
        # check if price matches step size
        price_step_size = Decimal(price_filter['tickSize'])
        if price_step_size != 0:
            correct_price = round(price / price_step_size) * price_step_size
            LOG_DEBUG(debug_tag, 'Rounded price {} with step size {} to: {}'.format(price, price_step_size, correct_price))
            if price != correct_price:
                LOG_ERROR(debug_tag, 'Price {} does not match price filters step size for symbol {} of {}'.format(price, symbol, price_step_size))
                return False
            else:
                LOG_DEBUG(debug_tag, 'Requested order price {} matches rounded price {} with stepsize of {} for symbol {}'.format(price, correct_price, price_step_size, symbol))

    # check if amount/quantity is in filter
    lot_filter = [f for f in filter_info if f['filterType'] == 'LOT_SIZE'][0]
    if lot_filter is None:
        LOG_ERROR(debug_tag, 'No lot filter found for symbol {}'.format(symbol))
        return False
    else:
        if amount < Decimal(lot_filter['minQty']) or amount > Decimal(lot_filter['maxQty']):
            LOG_ERROR(debug_tag, 'Amount {} is not in amount filter for symbol {} [{}-{}]'.format(amount, symbol, lot_filter['minQty'], lot_filter['maxQty']))
            return False
        
        # check if amount matches lot step size
        lot_step_size = Decimal(lot_filter['stepSize'])
        if lot_step_size != 0:
            correct_amount = round(amount / lot_step_size) * lot_step_size
            LOG_DEBUG(debug_tag, 'Rounded amount {} with lot step size {} to: {}'.format(amount, lot_step_size, correct_amount))
            if amount != correct_amount:
                LOG_ERROR(debug_tag, 'Amount {} does not match amount filters step size for symbol {} of {}'.format(amount, symbol, lot_step_size))
                return False
            else:
                LOG_DEBUG(debug_tag, 'Requested amount {} matches rounded amount {} with step size of {} for symbol {}'.format(amount, correct_amount, lot_step_size, symbol))
        notion_filter = [f for f in filter_info if f['filterType'] == 'MIN_NOTIONAL'][0]
        if notion_filter is None:
            LOG_ERROR(debug_tag, 'No notion filter found for symbol {}'.format(symbol))
            return False
        else:
            # check if notional is bigger or equal to min notional
            notion = amount * price
            min_notional = Decimal(notion_filter['minNotional'])
            if notion < min_notional:
                LOG_ERROR(debug_tag, 'Notion {} is smaller than min notional {} for symbol {}'.format(notion, min_notional, symbol))
                return False
    
    # check if account has enough balance
    quote_asset = symbol_info['quoteAsset']
    quote_balance = bot.get_asset_balance(quote_asset)
    if quote_balance is None:
        LOG_ERROR(debug_tag, 'No balance found for {}'.format(quote_asset))
        return False
    else:
        if quote_balance < amount:
            LOG_ERROR(debug_tag, 'Not enough {} in account to complete order'.format(quote_asset))
            return False
    
    return True
    

def invest_at_current_price(bot : TradingBot, investment_strategy : DCAInvestmentParameter):
    price = bot.get_avg_price(investment_strategy.symbol)
    
    investment_amount = investment_strategy.investment_amount_quoteasset
    amount = investment_amount / price
    debug_tag = '[Order Creation]'
    # round amount to match step size
    symbol_info = bot.get_symbol_info(investment_strategy.symbol)
    # get filter for LOT_SIZE
    filters = symbol_info['filters']
    lot_filter = [f for f in filters if f['filterType'] == 'LOT_SIZE'][0]
    if lot_filter is None:
        LOG_ERROR(debug_tag, 'No lot filter found for symbol {}'.format(investment_strategy.symbol))
    else:
        lot_step_size = Decimal(lot_filter['stepSize'])
        amount = round(amount / lot_step_size) * lot_step_size

    # buy a bit below the current price
    price = round(round(price / 10) * 10)
    LOG_INFO('Defined Investment per interval ({}): {}'.format(str(datetime.timedelta(seconds=investment_strategy.interval)), investment_amount))
    LOG_INFO('Investing {} at price {} for {}'.format(amount, price, investment_strategy.symbol))
    try:
        if check_order_possible(bot, amount, price, investment_strategy.symbol):
            new_order = bot.create_limit_buy_order(investment_strategy.symbol, price, amount)
            unfullfilled_orders.append(new_order)
            LOG_INFO('New Investment order created:', new_order)

            # TODO: Move this to a separate function (event handler)
            message_body = 'New Investment order created:\n' +  new_order.to_info_string()
            global_vars.firebaseMessager.push_notification(title="New order created", body=message_body)
    except BinanceAPIException as e:
        LOG_ERROR(debug_tag, 'Failed to create investment order:', e)
        # TODO: Move this to a separate function (event handler)
        message_body = 'Failed to create investment order:\n' + \
                        'Symbol: {}\n'.format(investment_strategy.symbol) + \
                        'Amount: {}\n'.format(amount) + \
                        'Price: {}\n'.format(price) + \
                        'Error: {}\n'.format(e)
        global_vars.firebaseMessager.push_notification(title="Failed to create investment order", body=message_body)

def log_and_raise_exeption(e : Exception, debug_tag : str = '[Exception]', raise_exception : bool = True):
    # try logging but if that doesnt work, try printing the exception
    exception = e
    excepton_info = traceback.format_exc()
    try:
        LOG_ERROR(debug_tag, e)
        LOG_ERROR(debug_tag, traceback.format_exc())
    except Exception as ex:
        print(debug_tag, "Initial exception that was raised:")
        print(debug_tag, e)
        print(debug_tag, excepton_info)

        print(debug_tag, "Another exception was raised during logging of the first exception:")
        print(debug_tag, ex)
        print(debug_tag, traceback.format_exc())
    if raise_exception:
        raise exception

class KillProcessException(Exception):
    pass

def signal_handler(signal, frame):
    raise KillProcessException('Process killed by signal {}'.format(signal))

def load_config(config_filepath : str):
    if os.path.exists(config_filepath):
        with open(config_filepath, 'r') as config_file:
            return json.load(config_file)
    else:
        raise Exception('Config file {} does not exist'.format(config_filepath))

def main():
    global unfullfilled_orders
    order_dirpath = 'orders'
    order_filepath = os.path.join(order_dirpath, 'orders.json')
    if not os.path.exists(order_dirpath):
        os.makedirs(order_dirpath)

    debug_tag = '[Startup]'
    dca_file_name = 'dca_investment_parameter.json'
    dca_file_path = os.path.join('configs', dca_file_name)

    # load config file
    config_file = os.path.join('configs', 'config.json')
    config = load_config(config_file)

    # init logger
    if 'LOGGING' in config:
        log_options = config['LOGGING']
        init_logger(log_options)
    else:
        print(debug_tag, 'No logging options found in config file')
        raise Exception('No logging options found in config file')

    # load environment variables
    dotEnvPath = os.path.join('configs', '.env')
    if os.path.exists(dotEnvPath):
        load_dotenv(dotEnvPath)
    else:
        LOG_WARNING(debug_tag, "No .env file found at {}", dotEnvPath)

    ids = []
    if 'firebase_project_id' in config:
        firebase_project_id = config['firebase_project_id']
        firebaseStorage = FirebaseStorage(firebase_project_id)
        firebaseStorage.connect()

        # retrieve user ids from firebase
        if 'bot_notification_id' in config:
            bot_notification_id = config['bot_notification_id']
            
            LOG_INFO(debug_tag, 'Retrieving all users to notify from firebase')
            ids = firebaseStorage.get_all_ids(bot_notification_id)
            if len(ids) == 0:
                LOG_WARNING(debug_tag, 'No users found to notify')
            else:
                LOG_INFO(debug_tag, '{} users found to notify'.format(len(ids)))
        else:
            LOG_INFO(debug_tag, 'No firebase bot_notification_id found in config file')
    else:
        LOG_INFO(debug_tag, 'No firebase project id found in config file')

    global_vars.firebaseMessager = FirebaseMessager()
    global_vars.firebaseMessager.set_ids(ids)
    global_vars.firebaseMessager.push_notification(title="DCA Bot starting", body="Bot started at: {}".format(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')))

    USE_TESTNET = True
    # init trading bot  
    if 'USE_TESTNET' in config:
        USE_TESTNET = config['USE_TESTNET']
    else:
        LOG_ERROR(debug_tag, 'No USE_TESTNET option found in config file')
        raise Exception('No USE_TESTNET option found in config file')

    check_interval = 60 * 30 # 30 minutes
    # retrieve update interval or use default
    if 'check_interval' in config:
        try:
            check_interval = int(config['check_interval'])
        except ValueError:
            LOG_ERROR(debug_tag, 'Check interval in config file is not a number')
            raise Exception('Check interval in config file is not a number')
        
        # check_interval must be at least 30 seconds
        if check_interval < 30:
            LOG_ERROR(debug_tag, 'Check interval in config file is too small. (>=30 seconds)')
            raise Exception('Check interval in config file is too small. (>=30 seconds)')
        LOG_DEBUG(debug_tag, 'Check interval set to {} seconds ({})'.format(check_interval, str(datetime.timedelta(seconds=check_interval))))
    else:
        LOG_INFO(debug_tag, 'No check_interval option found in config file. Using default of 30 minutes')

    bot = TradingBot(use_testnet=USE_TESTNET)
    bot.connect()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    dca_investment_strategies = []
    if os.path.isfile(dca_file_path):
        try:
            with open(dca_file_path) as f:
                dca_investments = json.load(f)
                for dca_investment in dca_investments:
                    dca_investment_strategies.append(DCAInvestmentParameter(dca_investment))
        except Exception as e:
            log_and_raise_exeption(e)
    else:
        LOG_ERROR(debug_tag, 'Failed to load dca investment parameter file at {}'.format(dca_file_path))

    # store every order made, don't retrieve it from binance in case a manuel order is made
    fullfilled_orders = load_last_orders(order_filepath)

    # TODO: outsource this function
    def exists_unfullfilled_order_for_symbol(symbol : str):
        for order in unfullfilled_orders:
            if order.symbol == symbol and order.side == SIDE_BUY:
                return True
        return False

    def on_order_filled(order : BinanceOrder):
        message_body = 'Order filled: {}\n'.format(order.orderId) + \
                          'Symbol: {}\n'.format(order.symbol) + \
                            'Side: {}\n'.format(order.side) + \
                            'Price: {}\n'.format(order.price) + \
                            'Quantity: {}\n'.format(order.origQty) + \
                            'Type: {}\n'.format(order.type) + \
                            'Status: {}\n'.format(order.status) + \
                            'Money spend: {}\n'.format(Decimal(order.price) * Decimal(order.origQty))
        global_vars.firebaseMessager.push_notification(title="Order filled!", body=message_body)

    # TODO: outsource this function
    def THREAD_check_if_orders_are_fully_filled():
        debug_tag = '[Thread - Fullfilled Order Checker]'

        # check continuously unfullfilled orders and wait for them to be fullfilled
        try:
            while True:
                time.sleep(5)
                if global_vars.stop_threads:
                    break
                for order in unfullfilled_orders:
                    try:
                        binance_order = bot.get_order_status(order.symbol, order.orderId)
                    except requests.exceptions.ReadTimeout as e:
                        LOG_WARNING(debug_tag, 'Timeout while checking order status for order {} {}'.format(order.symbol, order.orderId))
                        continue
                    except requests.exceptions.ConnectionError as e:
                        LOG_WARNING(debug_tag, 'Connection error while checking order status for order {} {}'.format(order.symbol,order.orderId))
                        continue

                    if binance_order.status == ORDER_STATUS_FILLED:
                        unfullfilled_orders.remove(order)
                        fullfilled_orders.append(binance_order)
                        LOG_INFO(debug_tag, 'Order fully filled:', binance_order)
                        on_order_filled(binance_order)
                        # store fullfilled orders in file
                        with open(order_filepath, 'w') as f:
                            orders = [o.asDict() for o in fullfilled_orders]
                            json.dump(orders, f, indent=4, ensure_ascii=False)
        except (KillProcessException, KeyboardInterrupt) as e:
            # this should not happen since it is called in a seperate thread but just in case
            LOG_CRITICAL(debug_tag, e)
            LOG_CRITICAL(debug_tag, 'KillProcessException received, stopping thread forcefully')
            pass
        except Exception as e:
            LOG_ERROR(debug_tag, 'Error while checking unfullfilled orders:', e)
            LOG_ERROR(debug_tag, 'Order listener stopped')
            log_and_raise_exeption(e, debug_tag)
        LOG_DEBUG(debug_tag, 'Order listener stopped')

    order_fullfill_checker_thread = threading.Thread(target=THREAD_check_if_orders_are_fully_filled)
    LOG_DEBUG(debug_tag, 'Starting order fullfill checker thread (order_fullfill_checker_thread)')
    order_fullfill_checker_thread.start()

    debug_tag = '[MainLoop]'

    # TODO: Make this more organized
    try:
        running = True
        while running:
            try:
                LOG_INFO('----Checking if DCA investment is neccessary----')
                for investment_strategy in dca_investment_strategies:
                    '''
                    A symbol is composed of a base asset and a quote asset.
                    Given a symbol BTCUSDT, BTC stands for the base asset and USDT stands for the quote asset.
                    '''
                    symbol = investment_strategy.symbol
                    #print current asset balance for BTC and USDT
                    info     = bot.get_symbol_info(symbol)
                    base_asset = info['baseAsset']
                    quote_asset = info['quoteAsset']
                    now = datetime.datetime.now() 
                    LOG_INFO('------------------------------------------------')
                    LOG_INFO("Time: ",now.strftime('%d.%m.%Y %H:%M:%S'))
                    LOG_INFO('Symbol: {}'.format(symbol))
                    LOG_INFO('Current average price for {}: {}'.format(symbol, bot.get_avg_price(symbol)))
                    LOG_INFO('Balance base asset {}: {}'.format(base_asset, bot.get_asset_balance(base_asset)))
                    LOG_INFO('Balance quote asset {}: {}'.format(quote_asset, bot.get_asset_balance(quote_asset)))              

                    # interval to add to last investment time
                    investment_interval_timedelta = datetime.timedelta(seconds=investment_strategy.interval)

                    # get hours and minute from investment time
                    hours =  investment_strategy.investment_time // 3600
                    minutes = (investment_strategy.investment_time % 3600) // 60

                    investment_start = datetime.datetime.fromtimestamp(investment_strategy.start_date + investment_strategy.investment_time)
                    if now >= investment_start:
                        # get last order for symbol
                        last_order = None    
                        for order in fullfilled_orders:
                            if order.symbol == symbol and order.side == SIDE_BUY:
                                last_order = order

                        if last_order != None:
                            time_of_last_investment = datetime.datetime.fromtimestamp(last_order.time / 1000)
                            LOG_INFO('Last investment time:', time_of_last_investment.strftime('%d.%m.%Y %H:%M:%S'))
                            
                            time_diff_today = datetime.datetime.now() - time_of_last_investment
                            LOG_INFO('Time since last investment:', str(datetime.timedelta(seconds=time_diff_today.total_seconds())))

                            time_of_last_investment_midnight = time_of_last_investment.replace(hour=0, minute=0, second=0, microsecond=0)

                            # next investment should happen last investment time + interval at defined time
                            next_investment_timestamp = (time_of_last_investment_midnight + investment_interval_timedelta).replace(hour=hours, minute=minutes, second=0, microsecond=0)
                            LOG_INFO('Time for next investment:', next_investment_timestamp.strftime('%d.%m.%Y %H:%M:%S'))

                            # check if last investment is older than interval
                            if now >= next_investment_timestamp:
                                LOG_INFO('Last investment is older than interval of {}, invest again'.format(str(datetime.timedelta(seconds=investment_strategy.interval))))
                                if not exists_unfullfilled_order_for_symbol(symbol):
                                    invest_at_current_price(bot, investment_strategy)
                                else:
                                    LOG_INFO('Investment order is in place, wait for it to be filled')
                        else:
                            if not exists_unfullfilled_order_for_symbol(symbol):
                                LOG_INFO('No previous investment found, invest now')
                                invest_at_current_price(bot, investment_strategy)
                            else:
                                LOG_INFO('Investment order is in place, wait for it to be filled')

                        LOG_INFO('------------------------------------------------')
                        # print orders
                        LOG_INFO('Current open orders:')
                        bot.print_orders(bot.get_orders(investment_strategy.symbol))

                        LOG_INFO('Unfullfilled orders:')
                        bot.print_orders(unfullfilled_orders)

                        LOG_INFO('Fullfilled orders:')
                        bot.print_orders(fullfilled_orders)
                    else:
                        LOG_INFO('Investment starts at {}'.format(investment_start.strftime('%d.%m.%Y %H:%M:%S')))
                time.sleep(check_interval)
            except KillProcessException as e:
                LOG_INFO(debug_tag, 'Process killed from outside')
                running = False
                break
            except KeyboardInterrupt:
                LOG_INFO(debug_tag, 'Exiting...')
                running = False
            except requests.exceptions.ReadTimeout as e:
                LOG_WARNING(debug_tag, "No Internet connection... retrying...")
                time.sleep(15)
            except requests.exceptions.ConnectionError as e:
                LOG_WARNING(debug_tag, "No Internet connection... retrying...")
                time.sleep(15)
            except Exception as e:
                log_and_raise_exeption(e, raise_exception=False)
                LOG_ERROR(debug_tag, "Error while checking if DCA investment is neccessary. Aborting program")
                running = False
                break
    finally:
            try:
                # store fullfilled orders in file
                with open(order_filepath, 'w') as f:
                    orders = [o.asDict() for o in fullfilled_orders]
                    json.dump(orders, f, indent=4, ensure_ascii=False)

                bot.close_all()
                global_vars.stop_threads = True

                LOG_INFO("Waiting for threads to finish, this can take a few seconds...")
                order_fullfill_checker_thread.join()
                LOG_DEBUG('Order listener thread stopped (order_fullfill_checker_thread)')
                
                # make sure to cancel all unfullfilled orders before closing the bot
                canceled = False
                while not canceled:
                    try:
                        # TODO: Store to file and load on next start
                        LOG_INFO('Canceling all unfullfilled orders')
                        for order in unfullfilled_orders:
                            try:
                                bot.cancel_order(order.symbol, order.orderId)
                            except BinanceAPIException as e:
                                LOG_ERROR('Order {} could not be canceled'.format(order.orderId))
                                LOG_ERROR(e)
                                continue
                        canceled = True
                    except requests.exceptions.ReadTimeout:
                        LOG_WARNING("[Deleting all current orders] No Internet connection... retrying...")
                        time.sleep(15)
                    except requests.exceptions.ConnectionError as e:
                        LOG_WARNING("[Deleting all current orders] No Internet connection... retrying...")
                        time.sleep(15)

                LOG_INFO("Process exited")
                global_vars.firebaseMessager.push_notification(title="Bot shut down", body="Bot shut down at: {}".format(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')))
            except KillProcessException:
                LOG_CRITICAL(debug_tag, "Process killed from outside again... just wait a god damn moment!")
            except Exception as e:
                log_and_raise_exeption(e)

if __name__ == "__main__":
    main()

