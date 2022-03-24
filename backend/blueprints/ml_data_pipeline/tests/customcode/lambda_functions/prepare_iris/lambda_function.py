import pickle
from io import StringIO

import boto3
import pandas as pd
from sklearn import preprocessing
from sklearn.model_selection import train_test_split


def handler(event, context):
    print(event)

    bucket = event.get("bucket")
    key = event.get("key")
    sep = event.get("sep", "," )
    header = event.get("header", None)
    
    output_bucket = event.get("output_bucket", bucket)
    output_prefix = event.get("output_prefix")

    training_data = event.get("training", "training_data.csv")
    validation_data = event.get("validation", "validation_data.csv")
    test_data = event.get("test", "test.csv")
    output_separator = event.get("output_sep", ",")

    df_all = read_df(bucket, key, sep, header)

    le = preprocessing.LabelEncoder()
    le.fit(df_all['class_name'])
    df_all["encoded_class"] = le.transform(df_all['class_name'])
    
    # rearrange, so that the class is at the first column
    num_only = df_all.drop("class_name", axis=1).copy()
    cols = num_only.columns.tolist()
    rearranged = num_only[cols[-1:] + cols[:-1]]

    # partition data to train, validation, and test
    train, test_valid = train_test_split(rearranged, test_size = 0.3)
    test, valid = train_test_split(test_valid, test_size = 0.5)

    # provide the training, validation, and test files
    create_output(train, output_bucket, output_prefix, output_separator, training_data)
    create_output(test, output_bucket, output_prefix, output_separator, test_data)
    create_output(valid, output_bucket, output_prefix, output_separator, validation_data)

    #  the serialized label encoder
    label_encoder = event.get("label_encoder", "le.p")
    create_serialized_label_encoder(le, output_bucket, output_prefix, label_encoder)

    preparation_result ={ "prepared_bucket": output_bucket,
                          "training_data": f"{output_prefix}/{training_data}",
                          "validation_data": f"{output_prefix}/{validation_data}",
                          "prepared_separator": output_separator,
                          "test_data": f"{output_prefix}/{test_data}",
                          "content_type": "text/csv",
                          "columns": rearranged.columns.tolist(),
                          "serialized_label_encoder": f"{output_prefix}/{label_encoder}"}
    return preparation_result

def create_serialized_label_encoder(le, output_bucket, output_prefix, label_encoder_path):
    s3_resource = boto3.resource('s3')
    le_dump = pickle.dumps(le)
    s3_resource.Object(output_bucket, f"{output_prefix}/{label_encoder_path}").put(Body=le_dump)

def create_output(df, output_bucket, output_prefix, output_separator, data_path):
    s3_resource = boto3.resource('s3')

    file_buffer = StringIO()
    df.to_csv(file_buffer, sep=output_separator, index=False, header=False)
    s3_resource.Object(output_bucket, f"{output_prefix}/{data_path}").put(Body=file_buffer.getvalue())


def read_df(bucket, key, sep, header):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)

    df_all = pd.read_csv(obj['Body'], sep=sep, header=header)
    if not header:
        df_all.columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'class_name']
    

    return df_all
   
