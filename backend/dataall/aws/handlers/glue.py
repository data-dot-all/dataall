import logging

from botocore.exceptions import ClientError

from .sts import SessionHelper

log = logging.getLogger('aws:glue')


class Glue:
    def __init__(self):
        pass

    @staticmethod
    def table_exists(**data):
        accountid = data['accountid']
        region = data.get('region', 'eu-west-1')
        database = data.get('database', 'UndefinedDatabaseName')
        table_name = data.get('tablename', 'UndefinedTableName')
        try:
            table = (
                SessionHelper.remote_session(accountid)
                .client('glue', region_name=region)
                .get_table(
                    CatalogId=data['accountid'], DatabaseName=database, Name=table_name
                )
            )
            log.info(f'Glue table found: {data}')
            return table
        except ClientError:
            log.info(f'Glue table not found: {data}')
            return None
