class BinanceOrder:
    """
    Used to represent a Binance json order object 
    """
    def __init__(self, binance_order_object):
        self.symbol = binance_order_object.get('symbol')                              # "BTCUSDT",
        self.orderId = binance_order_object.get('orderId')                            # 28,
        self.orderListId = binance_order_object.get('orderListId')                    # -1, //Unless OCO, value will be -1
        self.clientOrderId = binance_order_object.get('clientOrderId')                # "6gCrw2kRUAF9CvJDGP16IP",
        self.transactTime = binance_order_object.get('transactTime')                  # 1507725176595,
        self.price = binance_order_object.get('price')                                # "0.00000000",
        self.origQty = binance_order_object.get('origQty')                            # "10.00000000",
        self.executedQty = binance_order_object.get('executedQty')                    # "10.00000000",
        self.cummulativeQuoteQty = binance_order_object.get('cummulativeQuoteQty')    # "10.00000000",
        self.status = binance_order_object.get('status')                              # "FILLED",
        self.timeInForce = binance_order_object.get('timeInForce')                    # "GTC",
        self.type = binance_order_object.get('type')                                  # "MARKET",
        self.side = binance_order_object.get('side')                                  # "SELL"
        self.fills = binance_order_object.get('fills')
        self.stopPrice = binance_order_object.get('stopPrice')                        # "0.00000000",
        self.icebergQty = binance_order_object.get('icebergQty')                      # "0.00000000",
        self.time = binance_order_object.get('time')                                  # 1636591592916,
        self.updateTime = binance_order_object.get('updateTime')                      # 1636591592916,
        self.isWorking = binance_order_object.get('isWorking')                        # true,
        self.origQuoteOrderQty = binance_order_object.get('origQuoteOrderQty')        # "0.00000000"
    

    #TODO: Check if this is a correct override of the hash method
    def __hash__(self):
        return hash((self.symbol, self.orderId, self.orderListId, self.clientOrderId, self.transactTime, 
            self.price, self.origQty, self.executedQty, self.cummulativeQuoteQty, self.status, self.timeInForce, 
            self.type, self.side, self.fills, self.stopPrice, self.icebergQty, self.time, self.updateTime, self.isWorking, self.origQuoteOrderQty))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BinanceOrder):
            return NotImplemented
        return (self.symbol == other.symbol) and \
                (self.orderId == other.orderId) and \
                (self.orderListId == other.orderListId) and \
                (self.clientOrderId == other.clientOrderId) and \
                (self.transactTime == other.transactTime) and \
                (self.price == other.price) and \
                (self.origQty == other.origQty) and \
                (self.executedQty == other.executedQty) and \
                (self.cummulativeQuoteQty == other.cummulativeQuoteQty) and \
                (self.status == other.status) and \
                (self.timeInForce == other.timeInForce) and \
                (self.type == other.type) and \
                (self.side == other.side) and \
                (self.fills == other.fills) and \
                (self.stopPrice == other.stopPrice) and \
                (self.icebergQty == other.icebergQty) and \
                (self.time == other.time) and \
                (self.updateTime == other.updateTime) and \
                (self.isWorking == other.isWorking) and \
                (self.origQuoteOrderQty == other.origQuoteOrderQty)

    def __str__(self) -> str:
        return str(self.asDict())

    def asDict(self):
        return {
            'symbol' : self.symbol,
            'orderId' : self.orderId,
            'orderListId' : self.orderListId,
            'clientOrderId' : self.clientOrderId,
            'transactTime' : self.transactTime,
            'price' : self.price,
            'origQty' : self.origQty,
            'executedQty' : self.executedQty,
            'cummulativeQuoteQty' : self.cummulativeQuoteQty,
            'status' : self.status,
            'timeInForce' : self.timeInForce,
            'type' : self.type,
            'side' : self.side,
            'fills' : self.fills,
            'stopPrice' : self.stopPrice,
            'icebergQty' : self.icebergQty,
            'time' : self.time,
            'updateTime' : self.updateTime,
            'isWorking' : self.isWorking,
            'origQuoteOrderQty' : self.origQuoteOrderQty         
        }