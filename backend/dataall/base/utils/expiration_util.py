import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dataall.base.api import GraphQLEnumMapper


class ExpirationUtils:
    @staticmethod
    def calculate_expiry_date(expirationPeriod, expirySetting):
        currentDate = date.today()
        if expirySetting == Expiration.Quartely.value:
            if currentDate < datetime(currentDate.year, currentDate.month, 15).date():
                # First half of the month - extend 2.X months
                quarterlyCalculatedDate = currentDate + relativedelta(months=expirationPeriod * 3 - 1)
            else:
                # Second half of the month - extend 3.X months
                quarterlyCalculatedDate = currentDate + relativedelta(months=expirationPeriod * 3)
            day = calendar.monthrange(quarterlyCalculatedDate.year, quarterlyCalculatedDate.month)[1]
            shareExpiryDate = datetime(quarterlyCalculatedDate.year, quarterlyCalculatedDate.month, day)
        elif expirySetting == Expiration.Monthly.value:
            if currentDate < datetime(currentDate.year, currentDate.month, 15).date():
                # First half of the month - extend until end of month
                monthlyCalculatedDate = currentDate + relativedelta(months=expirationPeriod - 1)
            else:
                # Second half of the month - extend until end of next month
                monthlyCalculatedDate = currentDate + relativedelta(months=expirationPeriod)
            monthEndDay = calendar.monthrange(monthlyCalculatedDate.year, monthlyCalculatedDate.month)[1]
            shareExpiryDate = datetime(monthlyCalculatedDate.year, monthlyCalculatedDate.month, monthEndDay)
        else:
            shareExpiryDate = None

        return shareExpiryDate


# Enums used for dataset expiration.
# Could be repurposed for environment, worksheet, etc if need be
# This is defined here instead of the dataset_enums file because this is used in expiration_util.py
class Expiration(GraphQLEnumMapper):
    Monthly = 'Monthly'
    Quartely = 'Quarterly'
