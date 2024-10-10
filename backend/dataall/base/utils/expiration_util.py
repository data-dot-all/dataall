import calendar
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from dataall.base.api import GraphQLEnumMapper


class ExpirationUtils:
    @staticmethod
    def calculate_expiry_date(expirationPeriod, expirySetting):
        currentDate = date.today()
        last_week_start_date, last_week_end_date = ExpirationUtils.get_last_week_date_range(
            currentDate.year, currentDate.month
        )
        if expirySetting == Expiration.Quartely.value:
            if last_week_start_date <= currentDate <= last_week_end_date:
                # If in the last week of the month extend x3 months
                quarterlyCalculatedDate = currentDate + relativedelta(months=expirationPeriod * 3)
            else:
                # If the user is not in the last week, consider this month into the calculation
                quarterlyCalculatedDate = currentDate + relativedelta(months=expirationPeriod * 3 - 1)
            monthEndDay = calendar.monthrange(quarterlyCalculatedDate.year, quarterlyCalculatedDate.month)[1]
            shareExpiryDate = datetime(quarterlyCalculatedDate.year, quarterlyCalculatedDate.month, monthEndDay)
        elif expirySetting == Expiration.Monthly.value:
            if last_week_start_date <= currentDate <= last_week_end_date:
                # If in the last week of the month extend "expirationPeriod" number of months
                monthlyCalculatedDate = currentDate + relativedelta(months=expirationPeriod)
            else:
                # If the user is not in the last week, consider this month into the calculation - extend for "expirationPeriod" - 1
                monthlyCalculatedDate = currentDate + relativedelta(months=expirationPeriod - 1)
            monthEndDay = calendar.monthrange(monthlyCalculatedDate.year, monthlyCalculatedDate.month)[1]
            shareExpiryDate = datetime(monthlyCalculatedDate.year, monthlyCalculatedDate.month, monthEndDay)
        else:
            shareExpiryDate = None

        return shareExpiryDate

    @staticmethod
    def get_last_week_date_range(year, month):
        last_day_of_month = calendar.monthrange(year, month)[1]
        last_date = date(year, month, last_day_of_month)
        last_week_day = last_date.weekday()
        start_date = last_date - timedelta(days=last_week_day)

        return start_date, last_date


# Enums used for dataset expiration.
# Could be repurposed for environment, worksheet, etc if need be
# This is defined here instead of the dataset_enums file because this is used in expiration_util.py
class Expiration(GraphQLEnumMapper):
    Monthly = 'Monthly'
    Quartely = 'Quarterly'
