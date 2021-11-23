from decimal import Decimal

# CURRENTLY NOT USED
class CalculationDetails:
    '''
    Used to calculate a limit and stop loss with a limited risk
    '''
    def __init__(self, risk, distance_stop_loss, shares, price, sell_price,
                total_sold, potential_win_before_fee, fee_cost, potential_win_after_fee, tax_cost, potential_win_after_tax,
                capital, buy_price, stop_loss_price, risk_percent, win_percent, sell_fee, tax_fee):

        self.risk = risk
        self.distance_stop_loss = distance_stop_loss
        self.shares = shares
        self.price = price
        self.sell_price = sell_price
        self.total_sold = total_sold
        self.potential_win_before_fee = potential_win_before_fee
        self.fee_cost = fee_cost
        self.potential_win_after_fee = potential_win_after_fee
        self.tax_cost = tax_cost
        self.potential_win_after_tax = potential_win_after_tax
        self.capital = capital
        self.buy_price = buy_price
        self.stop_loss_price = stop_loss_price
        self.risk_percent = risk_percent
        self.win_percent = win_percent
        self.sell_fee = sell_fee
        self.tax_fee = tax_fee


def calculate_stop_loss_order(self, capital : Decimal, buy_price : Decimal, stop_loss_price : Decimal,
                                risk_percent : Decimal=Decimal(0.02), win_percent: Decimal=Decimal(0.01), sell_fee: Decimal=Decimal(0.00), tax_fee: Decimal=Decimal(0.00)):
    '''
    Calculates the limit and stop loss order with a given risk
    '''
    risk = 11 #capital * risk_percent
    distance_stop_loss = (buy_price - stop_loss_price) / buy_price
    shares = risk / (buy_price - stop_loss_price)
    price = buy_price * shares
    sell_price = ((shares * buy_price) * (1 + win_percent)) / shares
    total_sold = shares * sell_price
    potential_win_before_fee = (shares * (sell_price - buy_price))
    fee_cost = sell_fee * potential_win_before_fee
    potential_win_after_fee = potential_win_before_fee - fee_cost
    tax_cost = potential_win_after_fee * sell_fee
    potential_win_after_tax = potential_win_after_fee * (1 - tax_fee)

    #print("Capital: {0}\nRisk: {1}\nBuy Price: {2}\nStop Loss Price: {3}\nPercent to Win: {4}\nSell fee: {5}\nTax Rate: {6}\n\n".format(capital, risk_percent, buy_price, stop_loss_price, win_percent, sell_fee, tax_fee))
    #print("Risk in baseAsset: {0}\nDistance Entry-StopLoss: {1}\nNo of shares: {2}\nPrice: {3}\nSell Price: {4}\nTotal Sold: {5}\nPotential Win without fee: {6}\n".format(risk, distance_stop_loss, shares, price, sell_price, total_sold, potential_win_before_fee))

    return (
        {
            'limit': buy_price,
            'quantity': shares
        },
        {
            'price' : sell_price,
            'stop' : stop_loss_price,
            'limit' : stop_loss_price,
            'quantity' : shares
        },
        CalculationDetails(
            risk = risk,
            distance_stop_loss = distance_stop_loss,
            shares = shares,
            price = price,
            sell_price = sell_price,
            total_sold = total_sold,
            potential_win_before_fee = potential_win_before_fee,
            fee_cost = fee_cost,
            potential_win_after_fee = potential_win_after_fee,
            tax_cost = tax_cost,
            potential_win_after_tax = potential_win_after_tax,
            capital = capital,
            buy_price = buy_price,
            stop_loss_price = stop_loss_price,
            risk_percent = risk_percent,
            win_percent = win_percent,
            sell_fee = sell_fee,
            tax_fee = tax_fee
        ))

