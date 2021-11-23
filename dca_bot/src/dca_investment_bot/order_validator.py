from decimal import Decimal
from logger import LOG_DEBUG, LOG_ERROR_AND_NOTIFY, LOG_INFO, LOG_WARNING
'''
Validates if a given order is valid.
Uses the symbol filters to determine if the order is valid.
'''
class OrderValidator:
    debug_tag = '[Order Validation]'
    
    @staticmethod
    def check_order_possible(symbol_info : dict, quote_balance : Decimal, symbol : str, amount : Decimal, price : Decimal):
        symbol_filter_info = symbol_info['filters']
        
        LOG_DEBUG(OrderValidator.debug_tag, symbol, 'Filter Info: \n', symbol_filter_info)

        if not OrderValidator.__account_has_enough_balance(quote_asset=symbol_info['quoteAsset'], quote_balance=quote_balance, amount=amount):
            return False

        # check if price is in filter
        if not OrderValidator.__price_is_in_filter(symbol_filter_info=symbol_filter_info, symbol=symbol , price=price):
            return False

        # check if amount/quantity is in filter
        if not OrderValidator.__amount_is_in_filter(symbol_filter_info=symbol_filter_info, symbol=symbol, amount=amount, price=price):
            return False

        return True

    @staticmethod
    def __account_has_enough_balance(quote_asset, quote_balance, amount) -> bool:
        # check if account has enough balance
        if quote_balance is None:
            LOG_ERROR_AND_NOTIFY(OrderValidator.debug_tag, 'No balance found for {}'.format(quote_asset))
            return False
        else:
            if quote_balance < amount:
                LOG_ERROR_AND_NOTIFY(OrderValidator.debug_tag, 'Not enough {} in account to complete order'.format(quote_asset))
                return False
        return True

    @staticmethod
    def __price_is_in_filter(symbol_filter_info : dict, symbol : str, price : Decimal) -> bool:
        price_filter = [f for f in symbol_filter_info if f['filterType'] == 'PRICE_FILTER'][0]
        if price_filter is None:
            LOG_ERROR_AND_NOTIFY(OrderValidator.debug_tag, 'No price filter found for symbol {}'.format(symbol))
            return False
        else:
            if price < Decimal(price_filter['minPrice']) or price > Decimal(price_filter['maxPrice']):
                LOG_ERROR_AND_NOTIFY(OrderValidator.debug_tag, 'Price {} is not in price filter for symbol {} [{}-{}]'.format(price, symbol, price_filter['minPrice'], price_filter['maxPrice']))
                return False
            
            # check if price matches step size
            price_step_size = Decimal(price_filter['tickSize'])
            if price_step_size != 0:
                correct_price = round(price / price_step_size) * price_step_size
                LOG_DEBUG(OrderValidator.debug_tag, 'Rounded price {} with step size {} to: {}'.format(price, price_step_size, correct_price))
                if price != correct_price:
                    LOG_ERROR_AND_NOTIFY(OrderValidator.debug_tag, 'Price {} does not match price filters step size for symbol {} of {}'.format(price, symbol, price_step_size))
                    return False
                else:
                    LOG_DEBUG(OrderValidator.debug_tag, 'Requested order price {} matches rounded price {} with stepsize of {} for symbol {}'.format(price, correct_price, price_step_size, symbol))
        return True

    @staticmethod
    def __amount_is_in_filter(symbol_filter_info : dict, symbol : str, amount : Decimal, price : Decimal) -> bool:
        lot_filter = [f for f in symbol_filter_info if f['filterType'] == 'LOT_SIZE'][0]
        if lot_filter is None:
            LOG_ERROR_AND_NOTIFY(OrderValidator.debug_tag, 'No lot filter found for symbol {}'.format(symbol))
            return False
        else:
            if amount < Decimal(lot_filter['minQty']) or amount > Decimal(lot_filter['maxQty']):
                LOG_ERROR_AND_NOTIFY(OrderValidator.debug_tag, 'Amount {} is not in amount filter for symbol {} [{}-{}]'.format(amount, symbol, lot_filter['minQty'], lot_filter['maxQty']))
                return False
            
            # check if amount matches lot step size
            lot_step_size = Decimal(lot_filter['stepSize'])
            if lot_step_size != 0:
                correct_amount = round(amount / lot_step_size) * lot_step_size
                LOG_DEBUG(OrderValidator.debug_tag, 'Rounded amount {} with lot step size {} to: {}'.format(amount, lot_step_size, correct_amount))
                if amount != correct_amount:
                    LOG_ERROR_AND_NOTIFY(OrderValidator.debug_tag, 'Amount {} does not match amount filters step size for symbol {} of {}'.format(amount, symbol, lot_step_size))
                    return False
                else:
                    LOG_DEBUG(OrderValidator.debug_tag, 'Requested amount {} matches rounded amount {} with step size of {} for symbol {}'.format(amount, correct_amount, lot_step_size, symbol))
            notion_filter = [f for f in symbol_filter_info if f['filterType'] == 'MIN_NOTIONAL'][0]
            if notion_filter is None:
                LOG_ERROR_AND_NOTIFY(OrderValidator.debug_tag, 'No notion filter found for symbol {}'.format(symbol))
                return False
            else:
                # check if notional is bigger or equal to min notional
                notion = amount * price
                min_notional = Decimal(notion_filter['minNotional'])
                if notion < min_notional:
                    LOG_ERROR_AND_NOTIFY(OrderValidator.debug_tag, 'Notion {} is smaller than min notional {} for symbol {}'.format(notion, min_notional, symbol))
                    return False
        
        return True
