import pandas as pd

from smjobs.processing.processing_job import process_data


def test_processing_job():
    df = pd.DataFrame()
    assert process_data(df).empty
