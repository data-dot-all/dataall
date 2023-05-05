
from dataall.api.Objects.Feed.registry import FeedRegistry
from dataall.modules.datasets_base.db.models import DatasetTableColumn


def test_dataset_registered():
    model = FeedRegistry.find_model("DatasetTableColumn")
    assert model == DatasetTableColumn

    model = DatasetTableColumn()
    assert "DatasetTableColumn" == FeedRegistry.find_target(model)
