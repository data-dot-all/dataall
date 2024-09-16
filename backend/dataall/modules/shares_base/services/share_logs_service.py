import os
import logging

from dataall.base.context import get_context
from dataall.base.utils import Parameter
from dataall.base.db import exceptions
from dataall.base.utils.stack_logs_utils import is_stack_logs_visible
from dataall.core.stacks.aws.cloudwatch import CloudWatch
from dataall.base.config import config

from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository

log = logging.getLogger(__name__)


class ShareLogsService:
    @staticmethod
    @is_stack_logs_visible()
    def check_view_log_permissions(username, groups, shareUri, target_type='shares'):
        with get_context().db_engine.scoped_session() as session:
            share = ShareObjectRepository.get_share_by_uri(session, shareUri)
            ds = DatasetBaseRepository.get_dataset_by_uri(session, share.datasetUri)
            return ds.stewards in groups or ds.SamlAdminGroupName in groups or username == ds.owner

    @staticmethod
    def get_share_logs_name_query(shareUri):
        log.info(f'Get share Logs stream name for share {shareUri}')

        query = f"""fields @logStream
                        |filter  @message like '{shareUri}'
                        | sort @timestamp desc
                        | limit 1
                    """
        return query

    @staticmethod
    def get_share_logs_query(log_stream_name):
        query = f"""fields @timestamp, @message, @logStream, @log as @logGroup
                    | sort @timestamp asc
                    | filter @logStream like "{log_stream_name}"
                    """
        return query

    @staticmethod
    def get_share_logs(shareUri):
        context = get_context()
        if not ShareLogsService.check_view_log_permissions(context.username, context.groups, shareUri):
            raise exceptions.ResourceUnauthorized(
                username=context.username,
                action='View Share Logs',
                resource_uri=shareUri,
            )

        envname = os.getenv('envname', 'local')
        log_query_period_days = config.get_property('core.log_query_period_days', 1)
        log.info(f'log_query_period_days: {log_query_period_days}')
        log_group_name = f"/{Parameter().get_parameter(env=envname, path='resourcePrefix')}/{envname}/ecs/share-manager"

        query_for_name = ShareLogsService.get_share_logs_name_query(shareUri=shareUri)
        name_query_result = CloudWatch.run_query(
            query=query_for_name,
            log_group_name=log_group_name,
            days=log_query_period_days,
        )
        if not name_query_result:
            return []

        name = name_query_result[0]['logStream']

        query = ShareLogsService.get_share_logs_query(log_stream_name=name)
        results = CloudWatch.run_query(
            query=query,
            log_group_name=log_group_name,
            days=log_query_period_days,
        )
        log.info(f'Running Logs query {query} for log_group_name={log_group_name}')
        return results
