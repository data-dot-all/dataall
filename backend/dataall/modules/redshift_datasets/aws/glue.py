import logging
from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper

log = logging.getLogger(__name__)


class Glue:
    def __init__(self, account_id: str, region: str) -> None:
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self.client = session.client(service_name='glue', region_name=region)

    def create_database_from_redshift_datashare(self, name: str, datashare_arn: str, account: str):
        try:
            log.info(f'Creating database from Redshift {datashare_arn=}')
            self.client.create_database(
                CatalogId=account,
                DatabaseInput={
                    'Name': name,
                    'FederatedDatabase': {'Identifier': datashare_arn, 'ConnectionName': 'aws:redshift'},
                },
                Tags={'Application': 'dataall'},
            )
        except ClientError as e:
            log.error(e)
            raise e


    def get_database_from_redshift_datashare(self, name: str):
        try:
            log.info(f'Getting database {name=}')
            response = self.client.get_database(
                Name=name,
            )
            return response
        except ClientError as e:
            log.info(f'Database {name=} does not exist.')
            return None
