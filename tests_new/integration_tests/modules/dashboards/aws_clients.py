import logging

log = logging.getLogger(__name__)


class QuickSightClient:
    def __init__(self, session, account_id, region):
        self._client = session.client('quicksight', region_name=region)
        self._region = region
        self._account_id = account_id

    def check_enterprise_account_exists(self):
        """
        Check if a QuickSight Account exists in the account.
        :param
        :return: True if the account exists, False otherwise
        """
        try:
            response = self._client.describe_account_subscription(AwsAccountId=self._account_id)
            if not response['AccountInfo']:
                log.info(f'Quicksight Enterprise Subscription not found in Account: {self._account_id}')
                return False
            else:
                if response['AccountInfo']['Edition'] not in ['ENTERPRISE', 'ENTERPRISE_AND_Q']:
                    log.info(
                        f'Quicksight Subscription found in Account: {self._account_id} of incorrect type: {response["AccountInfo"]["Edition"]}'
                    )
                    return False
                else:
                    if response['AccountInfo']['AccountSubscriptionStatus'] == 'ACCOUNT_CREATED':
                        return True
            log.info(
                f'Quicksight Subscription found in Account: {self._account_id} not active. Status = {response["AccountInfo"]["AccountSubscriptionStatus"]}'
            )
            return False
        except self._client.exceptions.ResourceNotFoundException:
            return False
