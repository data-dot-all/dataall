import logging
from typing import Any, Dict
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)


class RedshiftClient:
    def __init__(self, session, region):
        self._client = session.client('redshift', region_name=region)
        self._region = region

    def deauthorize_datashare(self, datashare_arn: str, target_account: str) -> Dict[str, Any]:
        log.info('Deauthorizing Redshift datashare...')
        try:
            response = self._client.deauthorize_data_share(
                DataShareArn=datashare_arn, ConsumerIdentifier=target_account
            )
            log.info(f'Datashare deauthorized successfully: {datashare_arn}')
            return response
        except ClientError as e:
            log.exception('Error deauthorizing datashare')
            raise e
