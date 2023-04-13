
from dataall.core.feed.services.registry import FeedRegistry
from dataall.modules.datasets.db.table_column_model import DatasetTableColumn


def test_dataset_registered():
    model = FeedRegistry.find("DatasetTableColumn")
    assert model == DatasetTableColumn

    model = DatasetTableColumn()
    assert "DatasetTableColumn" == FeedRegistry.find_by_model(model)
