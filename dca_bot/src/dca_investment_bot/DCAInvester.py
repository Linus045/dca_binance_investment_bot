import datetime
import json
import os
import signal
import time
from decimal import getcontext
from typing import Union

from binance.enums import SIDE_BUY
from binance.exceptions import BinanceAPIException
from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout

import dca_investment_bot.global_vars as global_vars
from dca_investment_bot.binance_order import BinanceOrder
from dca_investment_bot.config_manager import ConfigManager
from dca_investment_bot.dca_investment_parameter import DCAInvestmentParameter
from dca_investment_bot.exceptions import KillProcessException
from dca_investment_bot.logger import log_and_raise_exeption
from dca_investment_bot.logger import LOG_CRITICAL_AND_NOTIFY
from dca_investment_bot.logger import LOG_DEBUG
from dca_investment_bot.logger import LOG_ERROR_AND_NOTIFY
from dca_investment_bot.logger import LOG_INFO
from dca_investment_bot.logger import LOG_WARNING
from dca_investment_bot.logger import LOG_WARNING_AND_NOTIFY
from dca_investment_bot.order_fulfilled_checker_thread import OrderFulfilledChecker
from dca_investment_bot.order_list_manager import OrderListManager
from dca_investment_bot.paths import Paths
from dca_investment_bot.trading_bot import TradingBot


def signal_handler(signal, frame):
    raise KillProcessException(f"Process killed by signal {signal}")


class DCAInvester:
    def __init__(self, config_manager: ConfigManager) -> None:
        self.bot: TradingBot = None
        self.order_list_manager: OrderListManager = None
        self.config_manager: ConfigManager = config_manager

    def run(self):
        # set precision for Decimal to 8 since most numbers in binance use max 8 digits
        getcontext().prec = 8

        debug_tag = "[Startup]"

        self.order_list_manager = OrderListManager(Paths.order_filepath)
        self.order_list_manager.load_fulfilled_from_file()

        order_fulfilled_checker_thread: OrderFulfilledChecker = OrderFulfilledChecker(
            self.order_list_manager,
            on_order_filled_callback=self.on_order_filled_callback,
            get_order_status_callback=self.get_order_status_callback,
        )

        ids = []
        global_vars.sync_fulfilled_orders_to_firebase = self.config_manager.sync_fulfilled_orders_to_firebase

        if self.config_manager.use_firebase:
            from dca_investment_bot.firebase.firebase_storage import FirebaseStorage
            from dca_investment_bot.firebase.firebase_messager import FirebaseMessager

            LOG_INFO(debug_tag, "Using Firebase")
            firebase_project_id = self.config_manager.firebase_project_id
            global_vars.firebaseStorage = FirebaseStorage(firebase_project_id)
            global_vars.firebaseStorage.connect()

            # retrieve user ids from firebase
            LOG_INFO(debug_tag, "Retrieving all users to notify from firebase")
            ids = global_vars.firebaseStorage.get_all_ids()
            if len(ids) == 0:
                LOG_WARNING(debug_tag, "No users found to notify")
            else:
                LOG_INFO(debug_tag, f"{len(ids)} users found to notify")

            global_vars.firebaseMessager = FirebaseMessager()
            global_vars.firebaseMessager.set_ids(ids)
        else:
            LOG_INFO(debug_tag, "Not using firebase")

        if global_vars.firebaseMessager is not None:
            LOG_DEBUG(debug_tag, "Sending push notification that bot is starting")
            global_vars.firebaseMessager.push_notification(
                title="DCA Bot starting",
                body="Bot started at: {}".format(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")),
            )

        USE_TESTNET = self.config_manager.use_testnet
        check_interval = self.config_manager.check_interval

        # check_interval must be at least 30 seconds
        if check_interval < 30:
            LOG_ERROR_AND_NOTIFY(debug_tag, "Check interval in config file is too small. (>=30 seconds)")
            raise Exception("Check interval in config file is too small. (>=30 seconds)")
        LOG_DEBUG(
            debug_tag,
            f"Check interval set to {check_interval} seconds ({str(datetime.timedelta(seconds=check_interval))})",
        )

        self.bot = TradingBot(use_testnet=USE_TESTNET)
        self.bot.connect()

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
            LOG_ERROR_AND_NOTIFY(
                debug_tag,
                f"Failed to load dca investment parameter file at {Paths.dca_file_path}",
            )

        # store every order made
        # don't retrieve it from binance in case a manuel order is made
        self.order_list_manager.load_fulfilled_from_file()

        if global_vars.firebaseStorage is not None:
            # TODO: add this to the firebase storage class
            global_vars.firebaseStorage.set_fulfilled_orders(self.order_list_manager.fulfilled_orders())

        LOG_DEBUG(
            debug_tag,
            "Starting order fulfill checker thread (order_fulfilled_checker_thread)",
        )
        order_fulfilled_checker_thread.start()

        debug_tag = "[MainLoop]"

        # TODO: Make this more organized
        try:
            running = True
            while running:
                try:
                    LOG_INFO("----Checking if DCA investment is neccessary----")
                    if len(dca_investment_strategies) == 0:
                        LOG_ERROR_AND_NOTIFY(
                            debug_tag,
                            "No DCA investment strategies found. \
                            Please add strategies to the dca_investment_parameter.json file",
                        )
                        running = False
                        continue
                    for investment_strategy in dca_investment_strategies:
                        """
                        A symbol is composed of a base asset and a quote asset.
                        Given a symbol BTCUSDT,
                        BTC stands for the base asset and USDT stands for the quote asset.
                        """
                        symbol = investment_strategy.symbol
                        # print current asset balance for BTC and USDT
                        info = self.bot.get_symbol_info(symbol)
                        base_asset = info["baseAsset"]
                        quote_asset = info["quoteAsset"]
                        now = datetime.datetime.now()
                        LOG_INFO("------------------------------------------------")
                        LOG_INFO("Time: ", now.strftime("%d.%m.%Y %H:%M:%S"))
                        LOG_INFO(f"Symbol: {symbol}")
                        LOG_INFO(f"Current average price for {symbol}: {self.bot.get_avg_price(symbol)}")
                        LOG_INFO(f"Balance base asset {base_asset}: {self.bot.get_asset_balance(base_asset)}")
                        LOG_INFO(f"Balance quote asset {quote_asset}: {self.bot.get_asset_balance(quote_asset)}")

                        # interval to add to last investment time
                        investment_interval_timedelta = datetime.timedelta(seconds=investment_strategy.interval)

                        # get hours and minute from investment time
                        hours = investment_strategy.investment_time // 3600
                        minutes = (investment_strategy.investment_time % 3600) // 60

                        investment_start = datetime.datetime.fromtimestamp(
                            investment_strategy.start_date + investment_strategy.investment_time
                        )
                        if now >= investment_start:
                            # get last order for symbol
                            last_order: Union[BinanceOrder, None] = None

                            # TODO: put this into OrderListManager
                            # -> get_last_order_for_symbol
                            for order in self.order_list_manager.fulfilled_orders():
                                if order.symbol == symbol and order.side == SIDE_BUY:
                                    last_order = order
                            should_invest = False
                            if last_order is not None:
                                time_of_last_investment = datetime.datetime.fromtimestamp(last_order.time / 1000)
                                LOG_INFO(
                                    "Last investment time:",
                                    time_of_last_investment.strftime("%d.%m.%Y %H:%M:%S"),
                                )

                                time_diff_today = datetime.datetime.now() - time_of_last_investment
                                LOG_INFO(
                                    "Time since last investment:",
                                    str(datetime.timedelta(seconds=time_diff_today.total_seconds())),
                                )

                                time_of_last_investment_midnight = time_of_last_investment.replace(
                                    hour=0, minute=0, second=0, microsecond=0
                                )

                                # next investment should happen at
                                # last investment time + interval at defined time
                                next_investment_timestamp = (
                                    time_of_last_investment_midnight + investment_interval_timedelta
                                ).replace(hour=hours, minute=minutes, second=0, microsecond=0)
                                LOG_INFO(
                                    "Time for next investment:",
                                    next_investment_timestamp.strftime("%d.%m.%Y %H:%M:%S"),
                                )

                                # check if last investment is older than interval
                                if now >= next_investment_timestamp:
                                    time_delta = datetime.timedelta(seconds=investment_strategy.interval)
                                    LOG_INFO(f"Last investment is older than interval of {time_delta}, invest again")
                                    if not self.exists_unfulfilled_order_for_symbol(symbol):
                                        should_invest = True
                                    else:
                                        LOG_INFO("Investment order is in place, wait for it to be filled")
                            else:
                                if not self.exists_unfulfilled_order_for_symbol(symbol):
                                    LOG_INFO("No previous investment found, invest now")
                                    should_invest = True
                                else:
                                    LOG_INFO("Investment order is in place, wait for it to be filled")

                            # invest in crypto
                            if should_invest:
                                self.invest(investment_strategy)

                            LOG_INFO("------------------------------------------------")
                            # print orders
                            LOG_INFO("Current open orders:")
                            self.order_list_manager.print_orders(self.bot.get_orders(investment_strategy.symbol))

                            LOG_INFO("Unfulfilled orders:")
                            self.order_list_manager.print_orders(self.order_list_manager.unfulfilled_orders())

                            LOG_INFO("fulfilled orders:")
                            self.order_list_manager.print_orders(self.order_list_manager.fulfilled_orders())
                        else:
                            LOG_INFO("Investment starts at {}".format(investment_start.strftime("%d.%m.%Y %H:%M:%S")))
                    time.sleep(check_interval)

                    # notify user if there are unfulfilled orders
                    if global_vars.firebaseMessager is not None:
                        if len(self.order_list_manager.unfulfilled_orders()) > 0:
                            LOG_DEBUG(
                                debug_tag,
                                "Sending push notifications for unfulfilled orders",
                            )
                            for order in self.order_list_manager.unfulfilled_orders():
                                LOG_DEBUG(debug_tag, "Unfulfilled Order:", order.to_info_string())
                                global_vars.firebaseMessager.push_notification(
                                    f"Unfulfilled Order {order.orderId}",
                                    order.to_info_string(),
                                )

                except KillProcessException:
                    LOG_INFO(debug_tag, "Process killed from outside")
                    running = False
                    break
                except KeyboardInterrupt:
                    LOG_INFO(debug_tag, "Exiting...")
                    running = False
                except ReadTimeout:
                    LOG_WARNING(debug_tag, "No Internet connection... retrying...")
                    time.sleep(15)
                except ConnectionError:
                    LOG_WARNING(debug_tag, "No Internet connection... retrying...")
                    time.sleep(15)
                except Exception as e:
                    log_and_raise_exeption(e, raise_exception=False)
                    LOG_ERROR_AND_NOTIFY(
                        debug_tag,
                        "Error while checking if DCA investment is neccessary. \
                            Aborting program",
                    )
                    running = False
                    raise e
        finally:
            try:
                # store fulfilled orders in file
                self.order_list_manager.store_orders_to_file()
                self.bot.close_all()

                LOG_INFO("Waiting for threads to finish, this can take a few seconds...")
                order_fulfilled_checker_thread.stop_and_join()
                LOG_DEBUG("Order listener thread stopped (order_fulfilled_checker_thread)")

                # make sure to cancel all unfulfilled orders before closing the bot
                canceled = False
                while not canceled:
                    try:
                        # TODO: Store to file and load on next start
                        LOG_INFO("Canceling all unfulfilled orders")
                        for order in self.order_list_manager.unfulfilled_orders():
                            try:
                                self.bot.cancel_order(order.symbol, order.orderId)
                            except BinanceAPIException as e:
                                LOG_ERROR_AND_NOTIFY(f"Order {order.orderId} could not be canceled")
                                LOG_ERROR_AND_NOTIFY(e)
                                continue
                        canceled = True
                    except ReadTimeout:
                        LOG_WARNING(
                            "[Deleting all current orders] No Internet connection... \
                                retrying..."
                        )
                        time.sleep(15)
                    except ConnectionError:
                        LOG_WARNING(
                            "[Deleting all current orders] No Internet connection... \
                                retrying..."
                        )
                        time.sleep(15)

                LOG_INFO("Process exited")
                if global_vars.firebaseMessager is not None:
                    LOG_DEBUG(debug_tag, "Sending push notification that bot shut down")
                    global_vars.firebaseMessager.push_notification(
                        title="Bot shut down",
                        body="Bot shut down at: {}".format(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")),
                    )
            except KillProcessException:
                LOG_CRITICAL_AND_NOTIFY(
                    debug_tag,
                    "Process killed from outside again... just wait a god damn moment!",
                )
            except Exception as e:
                log_and_raise_exeption(e)

    def exists_unfulfilled_order_for_symbol(self, symbol: str) -> bool:
        for order in self.order_list_manager.unfulfilled_orders():
            if order.symbol == symbol and order.side == SIDE_BUY:
                return True
        return False

    def on_order_filled_callback(self, order: BinanceOrder) -> None:
        debug_tag = "[OrderFulfilledChecker Callback - on_order_filled]"
        message_body = f"Order filled: {order.to_info_string()}\n"
        if global_vars.firebaseMessager is not None:
            LOG_DEBUG(debug_tag, "Sending push notification for filled order", message_body)
            global_vars.firebaseMessager.push_notification(title="Order filled!", body=message_body)

    def get_order_status_callback(self, symbol, order_id):
        debug_tag = "[OrderFulfilledChecker Callback - get_order_status]"
        try:
            return self.bot.get_order_status(symbol, order_id)
        except ReadTimeout:
            LOG_WARNING_AND_NOTIFY(
                debug_tag,
                f"Timeout while checking order status for order {symbol} {order_id}",
            )
            return None
        except ConnectionError:
            LOG_WARNING_AND_NOTIFY(
                debug_tag,
                f"Connection error while checking order status for order {symbol} {order_id}",
            )
            return None

    def invest(self, investment_strategy: DCAInvestmentParameter) -> None:
        debug_tag = "[Main - invest]"

        symbol = investment_strategy.symbol
        amount = investment_strategy.investment_amount_quoteasset
        interval = investment_strategy.interval
        LOG_INFO(f"Defined Investment with interval ({str(datetime.timedelta(seconds=interval))}): {amount}")

        new_order = self.bot.invest_at_current_price(symbol, amount)
        if new_order is not None:
            self.order_list_manager.add_new_order(new_order)
            LOG_INFO(debug_tag, "New Investment order created:", new_order)

            # TODO: Move this to a separate function (event handler)
            if global_vars.firebaseMessager is not None:
                message_body = "New Investment order created:\n" + new_order.to_info_string()
                LOG_DEBUG(
                    debug_tag,
                    "Sending push notification for created order:",
                    new_order.to_info_string(),
                )
                global_vars.firebaseMessager.push_notification(title="New order created", body=message_body)
