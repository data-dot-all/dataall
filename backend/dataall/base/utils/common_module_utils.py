import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dataall.base.utils.enums import Expiration


class ShareCommonUtils:
    @staticmethod
    def calculate_expiry_date(expirationPeriod, expirySetting):
        currentDate = date.today()
        if expirySetting == Expiration.Quartely.value:
            quarterlyCalculatedDate = currentDate + relativedelta(months=expirationPeriod * 3 - 1)
            day = calendar.monthrange(quarterlyCalculatedDate.year, quarterlyCalculatedDate.month)[1]
            shareExpiryDate = datetime(quarterlyCalculatedDate.year, quarterlyCalculatedDate.month, day)
        elif expirySetting == Expiration.Monthly.value:
            monthlyCalculatedDate = currentDate + relativedelta(months=expirationPeriod - 1)
            monthEndDay = calendar.monthrange(monthlyCalculatedDate.year, monthlyCalculatedDate.month)[1]
            shareExpiryDate = datetime(monthlyCalculatedDate.year, monthlyCalculatedDate.month, monthEndDay)
        else:
            shareExpiryDate = None

        return shareExpiryDate
