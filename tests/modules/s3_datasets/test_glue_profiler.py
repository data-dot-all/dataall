from dataall.modules.s3_datasets.cdk.dataset_glue_profiler_extension import DatasetGlueProfilerExtension
from pathlib import Path


def test_glue_profiler_exist():
    path = DatasetGlueProfilerExtension.get_path_to_asset()
    assert Path(path).exists()
