from datetime import datetime, timedelta
from enum import Enum

import requests
from secured import fred as secured

key = secured.my_key

# The yields stated on the website are in percent, per year: https://www.federalreserve.gov/releases/h15/
# and they assume a 360-day year

fed_days_in_year = 360


# these rates are updated on daily basis
class Period(str, Enum):
    three_mon = "DTB3"
    one_year = "DTB1YR"
    one_mon = "DTB4WK"
    six_mon = "DTB6"
    ten_year = 'DGS10'





class Fetched_Rates:

    def __init__(self):
        self.rates = {Period.three_mon: None, Period.one_mon: None, Period.one_year: None, Period.six_mon: None,
                 Period.ten_year: None}
        for period, rate in self.rates.items():
            self.rates[period] = get_fed_rate(period.value)


def get_fed_rate(period: Period,fetched_rates = None) -> float:
    """
    Get the US fed interest rate for the chosen period

    :param period: the period you want to chose
    :return: the rate in linear format (*not* percent)
    """
    if not fetched_rates is None:
        return fetched_rates.rates[period.value]

    response = requests.get('https://api.stlouisfed.org/fred/series/observations?',
                            params={'series_id': period, 'api_key': key, 'file_type': 'json', 'limit': 1,
                                    'sort_order': 'desc'})
    response.raise_for_status()
    response = response.json()
    return float(response["observations"][0]["value"])


def get_discount_rate(start: datetime, end: datetime, fetched_rates=None) -> float:
    """
    Get the risk free rate for a chosen time assuming zero coupon

    :param start: start time
    :param end: end time
    :return: the adjusted rate
    """
    delta = end - start
    period = None
    if delta.days == 0:
        raise RuntimeWarning()
    if delta.days > 365:
        period = Period.ten_year
    elif delta.days >= 180:
        # next highest is annual
        period = Period.one_year
    elif delta.days >= 90:
        # next highest is semi annual
        period = Period.six_mon
    elif delta.days >= 28:
        period = Period.three_mon
    else:
        period = Period.one_mon

    # they give it ini percent, hence we need to divide by 100
    annual_rate = get_fed_rate(period, fetched_rates)*1e-2

    # make daily
    daily_rate = (1 + annual_rate) ** (1 / fed_days_in_year) - 1

    return (1 + daily_rate) ** delta.days


today = datetime.now()
delta = timedelta(weeks=1)
second = today + delta

