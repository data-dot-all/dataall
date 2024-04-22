from dataall.modules.feed.api.registry import FeedRegistry
from dataall.modules.datasets_base.db.dataset_models import DatasetTable


def test_dataset_registered():
    model = FeedRegistry.find_model('DatasetTable')
    assert model == DatasetTable

    model = DatasetTable()
    assert 'DatasetTable' == FeedRegistry.find_target(model)
