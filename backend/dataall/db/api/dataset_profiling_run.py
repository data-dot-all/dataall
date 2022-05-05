from sqlalchemy import and_

from .. import models, paginate
from ..exceptions import ObjectNotFound


class DatasetProfilingRun:
    def __init__(self):
        pass

    @staticmethod
    def start_profiling(
        session, datasetUri, tableUri=None, GlueTableName=None, GlueJobRunId=None
    ):
        dataset: models.Dataset = session.query(models.Dataset).get(datasetUri)
        if not dataset:
            raise ObjectNotFound('Dataset', datasetUri)

        if tableUri and not GlueTableName:
            table: models.DatasetTable = session.query(models.DatasetTable).get(
                tableUri
            )
            if not table:
                raise ObjectNotFound('DatasetTable', tableUri)
            GlueTableName = table.GlueTableName

        environment: models.Environment = session.query(models.Environment).get(
            dataset.environmentUri
        )
        if not environment:
            raise ObjectNotFound('Environment', dataset.environmentUri)

        run = models.DatasetProfilingRun(
            datasetUri=dataset.datasetUri,
            status='RUNNING',
            AwsAccountId=environment.AwsAccountId,
            GlueJobName=dataset.GlueProfilingJobName or 'Unknown',
            GlueTriggerSchedule=dataset.GlueProfilingTriggerSchedule,
            GlueTriggerName=dataset.GlueProfilingTriggerName,
            GlueTableName=GlueTableName,
            GlueJobRunId=GlueJobRunId,
            owner=dataset.owner,
            label=dataset.GlueProfilingJobName or 'Unknown',
        )

        session.add(run)
        session.commit()
        return run

    @staticmethod
    def update_run(
        session,
        profilingRunUri=None,
        GlueJobRunId=None,
        GlueJobRunState=None,
        results=None,
    ):
        run = DatasetProfilingRun.get_profiling_run(
            session, profilingRunUri=profilingRunUri, GlueJobRunId=GlueJobRunId
        )
        if GlueJobRunId:
            run.GlueJobRunId = GlueJobRunId
        if GlueJobRunState:
            run.status = GlueJobRunState
        if results:
            run.results = results
        session.commit()
        return run

    @staticmethod
    def get_profiling_run(
        session, profilingRunUri=None, GlueJobRunId=None, GlueTableName=None
    ):
        if profilingRunUri:
            run: models.DatasetProfilingRun = session.query(
                models.DatasetProfilingRun
            ).get(profilingRunUri)
        else:
            run: models.DatasetProfilingRun = (
                session.query(models.DatasetProfilingRun)
                .filter(models.DatasetProfilingRun.GlueJobRunId == GlueJobRunId)
                .filter(models.DatasetProfilingRun.GlueTableName == GlueTableName)
                .first()
            )
        return run

    @staticmethod
    def list_profiling_runs(session, datasetUri, filter: dict = None):
        if not filter:
            filter = {}
        q = (
            session.query(models.DatasetProfilingRun)
            .filter(models.DatasetProfilingRun.datasetUri == datasetUri)
            .order_by(models.DatasetProfilingRun.created.desc())
        )
        return paginate(
            q, page=filter.get('page', 1), page_size=filter.get('pageSize', 20)
        ).to_dict()

    @staticmethod
    def list_table_profiling_runs(session, tableUri, filter):
        if not filter:
            filter = {}
        q = (
            session.query(models.DatasetProfilingRun)
            .join(
                models.DatasetTable,
                models.DatasetTable.datasetUri == models.DatasetProfilingRun.datasetUri,
            )
            .filter(
                and_(
                    models.DatasetTable.tableUri == tableUri,
                    models.DatasetTable.GlueTableName
                    == models.DatasetProfilingRun.GlueTableName,
                )
            )
            .order_by(models.DatasetProfilingRun.created.desc())
        )
        return paginate(
            q, page=filter.get('page', 1), page_size=filter.get('pageSize', 20)
        ).to_dict()

    @staticmethod
    def get_table_last_profiling_run(session, tableUri):
        return (
            session.query(models.DatasetProfilingRun)
            .join(
                models.DatasetTable,
                models.DatasetTable.datasetUri == models.DatasetProfilingRun.datasetUri,
            )
            .filter(models.DatasetTable.tableUri == tableUri)
            .filter(
                models.DatasetTable.GlueTableName
                == models.DatasetProfilingRun.GlueTableName
            )
            .order_by(models.DatasetProfilingRun.created.desc())
            .first()
        )

    @staticmethod
    def get_table_last_profiling_run_with_results(session, tableUri):
        return (
            session.query(models.DatasetProfilingRun)
            .join(
                models.DatasetTable,
                models.DatasetTable.datasetUri == models.DatasetProfilingRun.datasetUri,
            )
            .filter(models.DatasetTable.tableUri == tableUri)
            .filter(
                models.DatasetTable.GlueTableName
                == models.DatasetProfilingRun.GlueTableName
            )
            .filter(models.DatasetProfilingRun.results.isnot(None))
            .order_by(models.DatasetProfilingRun.created.desc())
            .first()
        )
