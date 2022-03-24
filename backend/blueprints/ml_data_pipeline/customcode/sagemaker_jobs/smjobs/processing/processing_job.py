import argparse

import pickle
from io import StringIO

import boto3
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

import os


def create_serialized_label_encoder(
    le, output_bucket, output_prefix, label_encoder_path
):
    s3_resource = boto3.resource('s3')
    le_dump = pickle.dumps(le)
    s3_resource.Object(output_bucket, f'{output_prefix}/{label_encoder_path}').put(
        Body=le_dump
    )


def create_output(df, output_bucket, output_prefix, output_separator, data_path):
    s3_resource = boto3.resource('s3')

    file_buffer = StringIO()
    df.to_csv(file_buffer, sep=output_separator, index=False, header=False)
    s3_resource.Object(output_bucket, f'{output_prefix}/{data_path}').put(
        Body=file_buffer.getvalue()
    )


def read_df(bucket, key, sep=',', header=0):
    print('read_df', bucket, key, sep, header)
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)

    df_all = pd.read_csv(obj['Body'], sep=sep, header=header)

    return df_all


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--bucket', type=str)
    parser.add_argument('--key', type=str)
    parser.add_argument('--sep', type=str, default=',')
    parser.add_argument('--header', type=int, default=None)
    parser.add_argument('--output_bucket', type=str)
    parser.add_argument('--output_prefix', type=str)
    parser.add_argument('--training_data', type=str, default='training_data.csv')
    parser.add_argument('--validation_data', type=str, default='validation_data.csv')
    parser.add_argument('--test_data', type=str, default='test.csv')
    parser.add_argument('--output_separator', type=str, default=',')
    parser.add_argument('--label_encoder', type=str, default='le.p')

    args = parser.parse_args()

    bucket = args.bucket if args.bucket else os.environ.get('bucket')
    key = args.key if args.key else os.environ.get('key')
    sep = args.sep
    header = args.header

    output_bucket = (
        args.output_bucket if args.output_bucket else os.environ.get('output_bucket')
    )
    output_prefix = (
        args.output_prefix if args.output_prefix else os.environ.get('output_prefix')
    )

    training_data = args.training_data
    validation_data = args.validation_data
    test_data = args.test_data
    output_separator = args.output_separator
    label_encoder_key = args.label_encoder

    # Load data
    df_all = read_df(bucket, key, sep)

    # Create new features
    df_all['AgeKnown'] = df_all['Age'].notna().astype(int)
    df_all['Male'] = (df_all['Sex'] == 'male').astype(int)

    # Fill na with mean value
    df_all['Age'].fillna(df_all['Age'].mean(), inplace=True)

    # Encode Embarked column
    label_encoder = LabelEncoder()
    label_encoder.fit(df_all['Embarked'].astype(str))
    df_all['EmbarkedLabelEncoded'] = label_encoder.transform(
        df_all['Embarked'].astype(str)
    )

    # Save the label encoder
    create_serialized_label_encoder(
        label_encoder, output_bucket, output_prefix, label_encoder_key
    )

    # Clean unused columnes
    columns = [
        'Survived',
        'Pclass',
        'Age',
        'SibSp',
        'Parch',
        'Fare',
        'Male',
        'AgeKnown',
        'EmbarkedLabelEncoded',
    ]
    df_all = df_all[columns]

    # Split the dataset into train/test/validataion
    train, test_val = train_test_split(df_all, test_size=0.3)
    validation, test = train_test_split(test_val, test_size=0.5)

    # Save dataset
    create_output(train, output_bucket, output_prefix, output_separator, training_data)
    create_output(test, output_bucket, output_prefix, output_separator, test_data)
    create_output(
        validation, output_bucket, output_prefix, output_separator, validation_data
    )
