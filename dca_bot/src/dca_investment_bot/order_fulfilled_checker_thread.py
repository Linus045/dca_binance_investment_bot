import threading
import time

from binance.enums import ORDER_STATUS_FILLED

import dca_investment_bot.global_vars as global_vars
from dca_investment_bot.exceptions import KillProcessException
from dca_investment_bot.exceptions import NoCallbackDefinedException
from dca_investment_bot.logger import log_and_raise_exeption
from dca_investment_bot.logger import LOG_CRITICAL_AND_NOTIFY
from dca_investment_bot.logger import LOG_DEBUG
from dca_investment_bot.logger import LOG_ERROR_AND_NOTIFY
from dca_investment_bot.logger import LOG_INFO
from dca_investment_bot.logger import LOG_WARNING_AND_NOTIFY
from dca_investment_bot.order_list_manager import OrderListManager

# TODO: maybe implement mutex using threading.Lock()
# mutex = threading.Lock()

"""
This class is responsible for checking if an order is fulfilled.
If it is, it will call the callback function.
"""


class OrderFulfilledChecker(threading.Thread):
    def __init__(
        self,
        order_manager: OrderListManager,
        on_order_filled_callback,
        get_order_status_callback,
    ) -> None:
        super().__init__()

        self._debug_tag = "[Thread - Fullfilled Order Checker]"
        self._order_manager = order_manager
        self._on_order_filled_callback = on_order_filled_callback
        self._get_order_status_callback = get_order_status_callback
        self._thread_running = False

    def stop_and_join(self):
        self._thread_running = False
        self.join()

    def run(self) -> None:
        self._thread_running = True
        # check continuously unfullfilled orders and wait for them to be fullfilled
        try:
            while self._thread_running:
                time.sleep(5)

                for order in self._order_manager.unfulfilled_orders():
                    binance_order = self.__get_order_status(order.symbol, order.orderId)

                    if binance_order is None:
                        continue

                    # TODO: check cases where order is just partially filled
                    if binance_order.status == ORDER_STATUS_FILLED:
                        self.__on_order_filled(binance_order)

                        self._order_manager.unfulfilled_orders().remove(order)
                        self._order_manager.fulfilled_orders().append(binance_order)
                        LOG_INFO(self._debug_tag, "Order fully filled:", binance_order)
                        self._order_manager.store_orders_to_file()

                        if global_vars.firebaseStorage is not None:
                            global_vars.firebaseStorage.set_fulfilled_orders(self._order_manager.fulfilled_orders())
        except (KillProcessException, KeyboardInterrupt) as e:
            # this should not happen since it is called
            # in a seperate thread but just in case
            LOG_CRITICAL_AND_NOTIFY(self._debug_tag, e)
            LOG_CRITICAL_AND_NOTIFY(
                self._debug_tag,
                "KillProcessException received, stopping thread forcefully",
            )
            pass
        except Exception as e:
            LOG_ERROR_AND_NOTIFY(self._debug_tag, "Error while checking unfullfilled orders:", e)
            LOG_ERROR_AND_NOTIFY(self._debug_tag, "Order listener stopped")
            log_and_raise_exeption(e, self._debug_tag)
        LOG_DEBUG(self._debug_tag, "Order listener stopped")

    def __get_order_status(self, symbol, order_id):
        if self._get_order_status_callback is not None:
            return self._get_order_status_callback(symbol, order_id)
        else:
            LOG_WARNING_AND_NOTIFY(self._debug_tag, "No callback defined for get_order_status")
            raise NoCallbackDefinedException("No callback defined for get_order_status_callback")

    def __on_order_filled(self, binance_order):
        if self._on_order_filled_callback is not None:
            self._on_order_filled_callback(binance_order)
        else:
            LOG_WARNING_AND_NOTIFY(self._debug_tag, "No callback defined for on_order_filled")
            raise NoCallbackDefinedException("No callback defined for on_order_filled")
