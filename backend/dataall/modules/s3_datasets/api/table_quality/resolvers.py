from dataall.modules.s3_datasets.services.dataset_table_quality_service import DatasetTableQualityService


def list_table_data_quality_rules(tableUri: str):
    # TODO: validate input
    return DatasetTableQualityService.list_table_data_quality_rules(uri=tableUri)