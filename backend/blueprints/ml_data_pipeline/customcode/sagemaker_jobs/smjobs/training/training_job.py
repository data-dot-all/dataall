import pandas as pd

from smjobs.helpers.printer import print_message


def process_data(data: pd.DataFrame) -> pd.DataFrame:
    print('DataFrame', data)
    return data


if __name__ == '__main__':
    # Example read data from S3 into a dataframe
    # df = pd.read_csv(S3_PREFIX)

    # Processing Data
    # df_new = process_data(df)

    # Write data back to S3
    # write_df_in_s3(df_new, S3_PREFIX)
    df = pd.DataFrame()
    process_data(df)
    print_message()
    print('Processing Data Job Completed Successfully')
