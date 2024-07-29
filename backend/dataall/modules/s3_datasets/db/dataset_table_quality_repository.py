from dataall.modules.s3_datasets.db.dataset_models import GlueDataQualityRule

class DatasetTableQualityRepository:

    @staticmethod
    def list_glue_quality_rules(session):
        return session.query(GlueDataQualityRule).all()

    @staticmethod
    def list_table_quality_rules(session, table_uri):
        pass
