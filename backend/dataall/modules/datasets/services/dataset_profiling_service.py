from sqlalchemy import and_

from dataall.db import paginate, models
from dataall.db.exceptions import ObjectNotFound
from dataall.modules.datasets.db.models import DatasetProfilingRun, DatasetTable, Dataset


class DatasetProfilingService:
    def __init__(self):
        pass

    @staticmethod
    def start_profiling(
        session, datasetUri, tableUri=None, GlueTableName=None, GlueJobRunId=None
    ):
        dataset: Dataset = session.query(Dataset).get(datasetUri)
        if not dataset:
            raise ObjectNotFound('Dataset', datasetUri)

        if tableUri and not GlueTableName:
            table: DatasetTable = session.query(DatasetTable).get(
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

        run = DatasetProfilingRun(
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
        run = DatasetProfilingService.get_profiling_run(
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
            run: DatasetProfilingRun = session.query(
                DatasetProfilingRun
            ).get(profilingRunUri)
        else:
            run: DatasetProfilingRun = (
                session.query(DatasetProfilingRun)
                .filter(DatasetProfilingRun.GlueJobRunId == GlueJobRunId)
                .filter(DatasetProfilingRun.GlueTableName == GlueTableName)
                .first()
            )
        return run

    @staticmethod
    def list_profiling_runs(session, datasetUri, filter: dict = None):
        if not filter:
            filter = {}
        q = (
            session.query(DatasetProfilingRun)
            .filter(DatasetProfilingRun.datasetUri == datasetUri)
            .order_by(DatasetProfilingRun.created.desc())
        )
        return paginate(
            q, page=filter.get('page', 1), page_size=filter.get('pageSize', 20)
        ).to_dict()

    @staticmethod
    def list_table_profiling_runs(session, tableUri, filter):
        if not filter:
            filter = {}
        q = (
            session.query(DatasetProfilingRun)
            .join(
                DatasetTable,
                DatasetTable.datasetUri == DatasetProfilingRun.datasetUri,
            )
            .filter(
                and_(
                    DatasetTable.tableUri == tableUri,
                    DatasetTable.GlueTableName
                    == DatasetProfilingRun.GlueTableName,
                )
            )
            .order_by(DatasetProfilingRun.created.desc())
        )
        return paginate(
            q, page=filter.get('page', 1), page_size=filter.get('pageSize', 20)
        ).to_dict()

    @staticmethod
    def get_table_last_profiling_run(session, tableUri):
        return (
            session.query(DatasetProfilingRun)
            .join(
                DatasetTable,
                DatasetTable.datasetUri == DatasetProfilingRun.datasetUri,
            )
            .filter(DatasetTable.tableUri == tableUri)
            .filter(
                DatasetTable.GlueTableName
                == DatasetProfilingRun.GlueTableName
            )
            .order_by(DatasetProfilingRun.created.desc())
            .first()
        )

    @staticmethod
    def get_table_last_profiling_run_with_results(session, tableUri):
        return (
            session.query(DatasetProfilingRun)
            .join(
                DatasetTable,
                DatasetTable.datasetUri == DatasetProfilingRun.datasetUri,
            )
            .filter(DatasetTable.tableUri == tableUri)
            .filter(
                DatasetTable.GlueTableName
                == DatasetProfilingRun.GlueTableName
            )
            .filter(DatasetProfilingRun.results.isnot(None))
            .order_by(DatasetProfilingRun.created.desc())
            .first()
        )
