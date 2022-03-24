import pandas as pd

from smjobs.training.training_job import process_data


def test_training_job():
    df = pd.DataFrame()
    assert process_data(df).empty
