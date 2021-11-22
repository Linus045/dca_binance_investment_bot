import requests
import time
import os
import datetime
import json
import time
import signal
from decimal import getcontext

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
from logger import *
from order_fulfilled_checker_thread import OrderFulfilledChecker
from order_list_manager import OrderListManager
from exceptions import KillProcessException
from paths import Paths

# set precision for Decimal to 8 since most numbers in binance use max 8 digits
getcontext().prec = 8

bot : TradingBot = None
order_list_manager: OrderListManager = None

def signal_handler(signal, frame):
    raise KillProcessException('Process killed by signal {}'.format(signal))

def load_config(config_filepath : str):
    if os.path.exists(config_filepath):
        with open(config_filepath, 'r') as config_file:
            return json.load(config_file)
    else:
        raise Exception('Config file {} does not exist'.format(config_filepath))

def on_order_filled_callback(order : BinanceOrder) -> None:
    debug_tag = '[OrderFulfilledChecker Callback - on_order_filled]'
    message_body = 'Order filled: {}\n'.format(order.to_info_string())
    LOG_DEBUG(debug_tag, 'Sending push notification for filled order', message_body)
    global_vars.firebaseMessager.push_notification(title="Order filled!", body=message_body)

def get_order_status_callback(symbol, order_id):
    debug_tag = '[OrderFulfilledChecker Callback - get_order_status]'
    try:
        return bot.get_order_status(symbol, order_id)
    except requests.exceptions.ReadTimeout as e:
        LOG_WARNING_AND_NOTIFY(debug_tag, 'Timeout while checking order status for order {} {}'.format(symbol, order_id))
        return None
    except requests.exceptions.ConnectionError as e:
        LOG_WARNING_AND_NOTIFY(debug_tag, 'Connection error while checking order status for order {} {}'.format(symbol, order_id))
        return None

def invest(investment_strategy : DCAInvestmentParameter) -> None:
    debug_tag = '[Main - invest]'

    symbol = investment_strategy.symbol
    amount = investment_strategy.investment_amount_quoteasset
    interval = investment_strategy.interval
    LOG_INFO('Defined Investment with interval ({}): {}'.format(str(datetime.timedelta(seconds=interval)), amount))

    new_order = bot.invest_at_current_price(symbol, amount)
    if new_order is not None:
        order_list_manager.add_new_order(new_order)
        LOG_INFO(debug_tag, 'New Investment order created:', new_order)

        # TODO: Move this to a separate function (event handler)
        message_body = 'New Investment order created:\n' +  new_order.to_info_string()
        LOG_DEBUG(debug_tag, 'Sending push notification for created order:', new_order.to_info_string())
        global_vars.firebaseMessager.push_notification(title="New order created", body=message_body)

def main():
    global bot, order_list_manager
    debug_tag = '[Startup]'

    order_list_manager = OrderListManager(Paths.order_filepath)
    order_list_manager.load_fulfilled_from_file()

    order_fulfilled_checker_thread : OrderFulfilledChecker = OrderFulfilledChecker(order_list_manager,
        on_order_filled_callback=on_order_filled_callback, get_order_status_callback=get_order_status_callback)

    # load config file
    # TODO: convert to config class for easier access/validation
    config = load_config(Paths.config_filepath)

    # init logger
    if 'LOGGING' in config:
        log_options = config['LOGGING']
        init_logger(log_options)
    else:
        print(debug_tag, 'No logging options found in config file')
        raise Exception('No logging options found in config file')

    # load environment variables
    dotEnvPath = os.path.join(Paths.config_directory, '.env')
    if os.path.exists(dotEnvPath):
        load_dotenv(dotEnvPath)
    else:
        LOG_WARNING_AND_NOTIFY(debug_tag, "No .env file found at {}", dotEnvPath)

    ids = []
    if 'SYNC_FULFILLED_ORDERS_TO_FIREBASE' in config:
        global_vars.sync_fulfilled_orders_to_firebase = config['SYNC_FULFILLED_ORDERS_TO_FIREBASE']
    else:
        LOG_INFO(debug_tag, 'No SYNC_FULFILLED_ORDERS_TO_FIREBASE option found in config file, using default: {}'.format(global_vars.sync_fulfilled_orders_to_firebase))

    if 'firebase_project_id' in config:
        firebase_project_id = config['firebase_project_id']
        global_vars.firebaseStorage = FirebaseStorage(firebase_project_id)
        global_vars.firebaseStorage.connect()

        # retrieve user ids from firebase
        if 'bot_notification_id' in config:
            bot_notification_id = config['bot_notification_id']
            
            LOG_INFO(debug_tag, 'Retrieving all users to notify from firebase')
            ids = global_vars.firebaseStorage.get_all_ids(bot_notification_id)
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

    LOG_DEBUG(debug_tag, 'Sending push notification that bot is starting')
    global_vars.firebaseMessager.push_notification(title="DCA Bot starting", body="Bot started at: {}".format(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')))

    USE_TESTNET = True
    # init trading bot  
    if 'USE_TESTNET' in config:
        USE_TESTNET = config['USE_TESTNET']
    else:
        LOG_ERROR_AND_NOTIFY(debug_tag, 'No USE_TESTNET option found in config file')
        raise Exception('No USE_TESTNET option found in config file')

    check_interval = 60 * 30 # 30 minutes
    # retrieve update interval or use default
    if 'check_interval' in config:
        try:
            check_interval = int(config['check_interval'])
        except ValueError:
            LOG_ERROR_AND_NOTIFY(debug_tag, 'Check interval in config file is not a number')
            raise Exception('Check interval in config file is not a number')
        
        # check_interval must be at least 30 seconds
        if check_interval < 30:
            LOG_ERROR_AND_NOTIFY(debug_tag, 'Check interval in config file is too small. (>=30 seconds)')
            raise Exception('Check interval in config file is too small. (>=30 seconds)')
        LOG_DEBUG(debug_tag, 'Check interval set to {} seconds ({})'.format(check_interval, str(datetime.timedelta(seconds=check_interval))))
    else:
        LOG_INFO(debug_tag, 'No check_interval option found in config file. Using default of 30 minutes')
    
    bot = TradingBot(use_testnet=USE_TESTNET)
    bot.connect()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    dca_investment_strategies = []
    if os.path.isfile(Paths.dca_file_path):
        try:
            with open(Paths.dca_file_path) as f:
                dca_investments = json.load(f)
                for dca_investment in dca_investments:
                    dca_investment_strategies.append(DCAInvestmentParameter(dca_investment))
        except Exception as e:
            log_and_raise_exeption(e)
    else:
        LOG_ERROR_AND_NOTIFY(debug_tag, 'Failed to load dca investment parameter file at {}'.format(Paths.dca_file_path))

    # store every order made, don't retrieve it from binance in case a manuel order is made
    order_list_manager.load_fulfilled_from_file()

    if global_vars.firebaseStorage is not None:
        # TODO: add this to the firebase storage class
        global_vars.firebaseStorage.set_fulfilled_orders(order_list_manager.fulfilled_orders())

    # TODO: outsource this function
    def exists_unfulfilled_order_for_symbol(symbol : str):
        for order in order_list_manager.unfulfilled_orders():
            if order.symbol == symbol and order.side == SIDE_BUY:
                return True
        return False

    LOG_DEBUG(debug_tag, 'Starting order fulfill checker thread (order_fulfilled_checker_thread)')
    order_fulfilled_checker_thread.start()

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
                        
                        # TODO: put this into OrderListManager -> get_last_order_for_symbol
                        for order in order_list_manager.fulfilled_orders():
                            if order.symbol == symbol and order.side == SIDE_BUY:
                                last_order = order
                        should_invest = False
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
                                if not exists_unfulfilled_order_for_symbol(symbol):
                                    should_invest = True
                                else:
                                    LOG_INFO('Investment order is in place, wait for it to be filled')
                        else:
                            if not exists_unfulfilled_order_for_symbol(symbol):
                                LOG_INFO('No previous investment found, invest now')
                                should_invest = True
                            else:
                                LOG_INFO('Investment order is in place, wait for it to be filled')

                        # invest in crypto
                        if should_invest:
                            invest(investment_strategy)

                        LOG_INFO('------------------------------------------------')
                        # print orders
                        LOG_INFO('Current open orders:')
                        order_list_manager.print_orders(bot.get_orders(investment_strategy.symbol))

                        LOG_INFO('Unfulfilled orders:')
                        order_list_manager.print_orders(order_list_manager.unfulfilled_orders())

                        LOG_INFO('fulfilled orders:')
                        order_list_manager.print_orders(order_list_manager.fulfilled_orders())
                    else:
                        LOG_INFO('Investment starts at {}'.format(investment_start.strftime('%d.%m.%Y %H:%M:%S')))
                time.sleep(check_interval)

                # notify user if there are unfulfilled orders
                if len(order_list_manager.unfulfilled_orders()) > 0:
                    LOG_DEBUG(debug_tag, 'Sending push notifications for unfulfilled orders')
                    for order in order_list_manager.unfulfilled_orders():
                        LOG_DEBUG(debug_tag, 'Unfulfilled Order:', order.to_info_string())
                        global_vars.firebaseMessager.push_notification("Unfulfilled Order {}".format(order.orderId), order.to_info_string())

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
                LOG_ERROR_AND_NOTIFY(debug_tag, "Error while checking if DCA investment is neccessary. Aborting program")
                running = False
                raise e
    finally:
            try:
                # store fulfilled orders in file
                order_list_manager.store_orders_to_file()
                bot.close_all()

                LOG_INFO("Waiting for threads to finish, this can take a few seconds...")
                order_fulfilled_checker_thread.stop_and_join()
                LOG_DEBUG('Order listener thread stopped (order_fulfilled_checker_thread)')
                
                # make sure to cancel all unfulfilled orders before closing the bot
                canceled = False
                while not canceled:
                    try:
                        # TODO: Store to file and load on next start
                        LOG_INFO('Canceling all unfulfilled orders')
                        for order in order_list_manager.unfulfilled_orders():
                            try:
                                bot.cancel_order(order.symbol, order.orderId)
                            except BinanceAPIException as e:
                                LOG_ERROR_AND_NOTIFY('Order {} could not be canceled'.format(order.orderId))
                                LOG_ERROR_AND_NOTIFY(e)
                                continue
                        canceled = True
                    except requests.exceptions.ReadTimeout:
                        LOG_WARNING("[Deleting all current orders] No Internet connection... retrying...")
                        time.sleep(15)
                    except requests.exceptions.ConnectionError as e:
                        LOG_WARNING("[Deleting all current orders] No Internet connection... retrying...")
                        time.sleep(15)

                LOG_INFO("Process exited")
                LOG_DEBUG(debug_tag, 'Sending push notification that bot shut down')
                global_vars.firebaseMessager.push_notification(title="Bot shut down", body="Bot shut down at: {}".format(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')))
            except KillProcessException:
                LOG_CRITICAL_AND_NOTIFY(debug_tag, "Process killed from outside again... just wait a god damn moment!")
            except Exception as e:
                log_and_raise_exeption(e)

if __name__ == "__main__":
    main()

