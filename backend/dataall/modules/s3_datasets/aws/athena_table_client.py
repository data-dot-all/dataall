import json
import logging
from pyathena import connect

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.db.environment_models import Environment
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable
from dataall.base.utils import json_utils, sql_utils

log = logging.getLogger(__name__)


class AthenaTableClient:
    def __init__(self, env: Environment, table: DatasetTable):
        session = SessionHelper.remote_session(accountid=table.AWSAccountId, region=table.region)

        self._client = session.client('athena', region_name=env.region)
        self._creds = session.get_credentials()
        self._env = env
        self._table = table

    def get_table(self):
        try:
            env_workgroup = self._client.get_work_group(WorkGroup=self._env.EnvironmentDefaultAthenaWorkGroup)
        except ClientError as e:
            log.info(f'Workgroup {self._env.EnvironmentDefaultAthenaWorkGroup} can not be found due to: {e}')

        connection = connect(
            aws_access_key_id=self._creds.access_key,
            aws_secret_access_key=self._creds.secret_key,
            aws_session_token=self._creds.token,
            work_group=env_workgroup.get('WorkGroup', {}).get('Name', 'primary'),
            s3_staging_dir=f's3://{self._env.EnvironmentDefaultBucketName}/preview/{self._table.datasetUri}/{self._table.tableUri}',
            region_name=self._table.region,
        )
        cursor = connection.cursor()

        sql = 'select * from {table_identifier} limit 50'.format(
            table_identifier=sql_utils.Identifier(self._table.GlueDatabaseName, self._table.GlueTableName)
        )
        cursor.execute(sql)  # nosemgrep
        # it is not possible to build the query string with the table.X parameters using Pyathena connect
        # to remediate sql injections we built the Identifier class that removes any malicious code from the string
        fields = []
        for f in cursor.description:
            fields.append(json.dumps({'name': f[0]}))
        rows = []
        for row in cursor:
            rows.append(json.dumps(json_utils.to_json(list(row))))

        return {'rows': rows, 'fields': fields}
