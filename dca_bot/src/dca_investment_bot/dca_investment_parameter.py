import time
import datetime

from dca_investment_bot.logger import LOG_CRITICAL_AND_NOTIFY

class UnknownIntervalException(Exception):
    pass

class InvalidParameterFormat(Exception):
    pass

class DCAInvestmentParameter:
    '''
        Parses parameters for DCA investment from a json object
        Constructor takes an object with the following keys:
        object:
        {
            "symbol": "ETHUSDT",
            "investment_amount_quoteasset": 12,
            "interval": "1w",
            "investment_time": "12:00",
            "start_date": "2021-11-01"
        }
    '''

    def __init__(self, parameter_object):
        self.symbol = None
        self.investment_amount_quoteasset = None
        self.interval = None
        self.investment_time = None
        self.start_date = None
        self.load_from_json(parameter_object)

    def parse_interval_to_seconds(self, interval):
        if interval == '1d':
            return 60 * 60 * 24
        elif interval == '1w':
            return 60 * 60 * 24 * 7
        elif interval == '2w':
            return 60 * 60 * 24 * 7 * 2
        elif interval == '3w':
            return 60 * 60 * 24 * 7 * 3
        elif interval == '4w':
            return 60 * 60 * 24 * 7 * 4
        elif interval == '1M':
            return 60 * 60 * 24 * 30
        elif interval == '2M':
            return 60 * 60 * 24 * 30 * 2
        else:
            raise UnknownIntervalException('Unknown interval "{}"'.format(interval))

    def parse_investment_time_to_seconds(self, investment_time):
        try:
            timedeltaObj = datetime.datetime.strptime(investment_time, "%H:%M") - datetime.datetime(1900,1,1)
            return int(timedeltaObj.total_seconds())
        except (OverflowError, ValueError):
            raise InvalidParameterFormat('Investment time uses invalid format. HH:MM expected but {} was given'.format(investment_time))

    def date_to_seconds(self, date):
        try:
            return time.mktime(datetime.datetime.strptime(date, "%Y-%m-%d").timetuple())
        except (OverflowError, ValueError, TypeError):
            raise InvalidParameterFormat('Start date uses invalid format. YYYY-MM-DD expected but {} was given'.format(date))

    # method to print details
    def print_details(self):
        print('DCA Investment:')
        print('Symbol:', self.symbol)
        print('Investment: ' + str(self.investment_amount_quoteasset))
        print('Interval: ' + str(self.interval))
        print('Investment time: ' + str(self.investment_time))
        print('Start date: ' + str(self.start_date))
        

    # load from object or throw error if keys are missing
    def load_from_json(self, json_object):
        if 'symbol' in json_object:
            self.symbol = json_object['symbol']
        else:
            LOG_CRITICAL_AND_NOTIFY('Missing symbol in investment parameter')
            raise KeyError('symbol')

        if 'investment_amount_quoteasset' in json_object:
            self.investment_amount_quoteasset = json_object['investment_amount_quoteasset']
        else:
            LOG_CRITICAL_AND_NOTIFY('Missing investment_amount_quoteasset in investment parameter')
            raise KeyError('investment_amount_quoteasset')

        if 'interval' in json_object:
            try:
                self.interval = self.parse_interval_to_seconds(json_object['interval'])
            except UnknownIntervalException as e:
                LOG_CRITICAL_AND_NOTIFY(e)
                raise e
        else:
            LOG_CRITICAL_AND_NOTIFY('Missing interval in investment parameter')
            raise KeyError('interval')

        if 'investment_time' in json_object:
            try:
                self.investment_time = self.parse_investment_time_to_seconds(json_object['investment_time'])
            except InvalidParameterFormat as e:
                LOG_CRITICAL_AND_NOTIFY(e)
                raise e
        else:
            LOG_CRITICAL_AND_NOTIFY('Missing investment_time in investment parameter')
            raise KeyError('investment_time')

        if 'start_date' in json_object:
            try:
                self.start_date = self.date_to_seconds(json_object['start_date'])
            except InvalidParameterFormat as e:
                LOG_CRITICAL_AND_NOTIFY(e)
                raise e
        else:
            LOG_CRITICAL_AND_NOTIFY('Missing start_date in investment parameter')
            raise KeyError('start_date')
        
        if 'start_date' in json_object:
            try:
                self.start_date = self.date_to_seconds(json_object['start_date'])
            except InvalidParameterFormat as e:
                LOG_CRITICAL_AND_NOTIFY(e)
                raise e
        else:
            raise KeyError('start_date')
