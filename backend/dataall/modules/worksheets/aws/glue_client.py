import logging

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper

log = logging.getLogger(__name__)


class GlueClient:
    def __init__(self, account_id, region, database):
        aws_session = SessionHelper.remote_session(accountid=account_id, region=region)
        self._client = aws_session.client('glue', region_name=region)
        self._database = database
        self._account_id = account_id
        self._region = region

    def get_metadata(self, table_name):
        table_metadata = self._client.get_table(DatabaseName=self._database, Name=table_name)
        table_name = table_metadata['Table']['Name']
        column_metadata = table_metadata['Table']['StorageDescriptor']['Columns']
        partition_metadata = table_metadata['Table']['PartitionKeys']
        meta_data = f"""
        Database name: {self._database}
        Table name: {table_name} 
        Column Metadata: {column_metadata}
        Partition Metadata: {partition_metadata}
        """
        return meta_data
