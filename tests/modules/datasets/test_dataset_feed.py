
from dataall.modules.feed.api.registry import FeedRegistry
from dataall.modules.datasets_base.db.dataset_models import DatasetTableColumn


def test_dataset_registered():
    model = FeedRegistry.find_model("DatasetTableColumn")
    assert model == DatasetTableColumn

    model = DatasetTableColumn()
    assert "DatasetTableColumn" == FeedRegistry.find_target(model)
