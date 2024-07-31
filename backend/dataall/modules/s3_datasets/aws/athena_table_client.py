import json
import logging
from pyathena import connect

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable
from dataall.base.utils import json_utils, sql_utils

log = logging.getLogger(__name__)


class AthenaTableClient:
    def __init__(self, env: Environment, table: DatasetTable, env_group: EnvironmentGroup = None):
        session = SessionHelper.remote_session(accountid=env.AwsAccountId, region=env.region)
        if env_group:
            session = SessionHelper.get_session(base_session=session, role_arn=env_group.environmentIAMRoleArn)

        self._client = session.client('athena', region_name=env.region)
        self._creds = session.get_credentials()
        self._env = env
        self._env_group = env_group
        self._table = table

    def get_table(self, database_name: str, resource_link_name: str = None):
        env_workgroup_name = (
            self._env_group.environmentAthenaWorkGroup
            if self._env_group
            else self._env.EnvironmentDefaultAthenaWorkGroup
        )
        connection = connect(
            aws_access_key_id=self._creds.access_key,
            aws_secret_access_key=self._creds.secret_key,
            aws_session_token=self._creds.token,
            work_group=env_workgroup_name,
            s3_staging_dir=f's3://{self._env.EnvironmentDefaultBucketName}/athenaqueries/{env_workgroup_name}/',
            region_name=self._env.region,
        )
        cursor = connection.cursor()

        sql = 'select * from {table_identifier} limit 50'.format(
            table_identifier=sql_utils.Identifier(database_name, resource_link_name or self._table.GlueTableName)
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
