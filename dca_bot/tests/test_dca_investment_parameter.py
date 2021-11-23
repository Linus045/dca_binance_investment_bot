import pytest

from dca_investment_bot.dca_investment_parameter import DCAInvestmentParameter
from dca_investment_bot.dca_investment_parameter import InvalidParameterFormat
from dca_investment_bot.dca_investment_parameter import UnknownIntervalException


@pytest.mark.skip("Currently not checking symbol")
@pytest.mark.parametrize("parameter_symbol", [True, 1231, "-5", "0", "", "sasda"])
def test_constructor_invalid_symbol_throws_ValueError(parameter_symbol):
    json_data = {
        "symbol": parameter_symbol,
        "investment_amount_quoteasset": 12,
        "interval": "2d",
        "investment_time": "12:00",
        "start_date": "2021-11-01",
    }
    with pytest.raises(ValueError):
        DCAInvestmentParameter(json_data)


@pytest.mark.skip("Currently not checking quote asset amount")
@pytest.mark.parametrize("parameter_quote_amount", [-5, 0, "asd", "", True])
def test_constructor_invalid_quote_amount_throws_ValueError(parameter_quote_amount):
    json_data = {
        "symbol": "ETHUSDT",
        "investment_amount_quoteasset": parameter_quote_amount,
        "interval": "2d",
        "investment_time": "12:00",
        "start_date": "2021-11-01",
    }
    with pytest.raises(ValueError):
        DCAInvestmentParameter(json_data)


@pytest.mark.parametrize("parameter_interval", ["1h", "1m", "", "asd", "0", "123123w", "5m", "2m", 244, True])
def test_constructor_invalid_interval_throws_UnknownIntervalException(
    parameter_interval,
):
    json_data = {
        "symbol": "ETHUSDT",
        "investment_amount_quoteasset": 12,
        "interval": parameter_interval,
        "investment_time": "12:00",
        "start_date": "2021-11-01",
    }
    with pytest.raises(UnknownIntervalException):
        DCAInvestmentParameter(json_data)


@pytest.mark.parametrize("parameter_time", ["26:00", "test", "", "19:60", "19:72", "121231", 12000, True])
def test_constructor_invalid_time_throws_InvalidParameterFormat(parameter_time):
    json_data = {
        "symbol": "ETHUSDT",
        "investment_amount_quoteasset": 12,
        "interval": "1w",
        "investment_time": parameter_time,
        "start_date": "2021-11-01",
    }
    with pytest.raises(InvalidParameterFormat):
        DCAInvestmentParameter(json_data)


@pytest.mark.parametrize(
    "parameter_start_date",
    [
        True,
        23,
        "test",
        "",
        "19:60",
        "19:72",
        "121231",
        "0000-23-23",
        "2021-12-32",
        "2021-02-29",
    ],
)
def test_constructor_invalid_start_date_throws_InvalidParameterFormat(
    parameter_start_date,
):
    json_data = {
        "symbol": "ETHUSDT",
        "investment_amount_quoteasset": 12,
        "interval": "1w",
        "investment_time": "12:00",
        "start_date": parameter_start_date,
    }
    with pytest.raises(InvalidParameterFormat):
        DCAInvestmentParameter(json_data)
