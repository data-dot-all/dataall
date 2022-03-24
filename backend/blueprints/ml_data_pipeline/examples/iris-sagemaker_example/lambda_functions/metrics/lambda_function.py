# lambda_function.py
""" A lambda function that receives a csv file containing the truth vs predicted value """
import pandas as pd
from sklearn import metrics
import boto3
from io import StringIO
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_resource = boto3.resource("s3")

def compute_scores(input_df):
    """ 
    Computes KPIs of model by comparing truth to prediction value.
    :param input_df the input data frame containing two tables, the truth (y) and the predicted one (y_pred)
    """
    y = input_df[0]
    y_pred = input_df[1]

    accuracy = metrics.accuracy_score(y, y_pred)
    precision = metrics.precision_score(y, y_pred, average="macro")
    recall = metrics.recall_score(y, y_pred, average="macro")
    f1 = metrics.f1_score(y, y_pred, average="macro")

    return [accuracy, precision, recall, f1]


def handler(event, context):
    """ 
    Lambda function to measure the KPIs of Iris prediction model, especially accuracy, precision, recall, and F1 score.

    :param event the lambda event
    :context the context of execution.

    """
    logging.info(str(event))

    bucket = event["s3_transform_output_path"]["bucket"]
    key_prefix = event["s3_transform_output_path"]["key_prefix"]
    output_bucket = event["kpi_output_path"]["bucket"] 
    output_key = event["kpi_output_path"]["key_prefix"]
    file_name = event["s3_transform_input"].split("/")[-1]
    if key_prefix[-1] == "/":
        key = "{}{}.out".format(key_prefix.strip(), file_name)
    else:
        key = "{}/{}.out".format(key_prefix.strip(), file_name)
    
    df = read_df(bucket, key, ",", header = None)
    score_list = compute_scores(df)

    scores = {'metric': ["accuracy", "precision", "recall", "f1"], 
              'score': score_list
              }

    logger.info("The resulting scores are {}".format(str(scores)))
    scores_df = pd.DataFrame(data = scores)
    write_df (scores_df, output_bucket, output_key)

    confusion_matrix, multilabel_confusion_matrix = confusion_matrices(df)

    write_confusion_matrices(confusion_matrix, multilabel_confusion_matrix, output_bucket, output_key)
    
    return {
        "metrics": scores, 
        "output_path": {
            "bucket": output_bucket,
            "key": output_key
        } 
    }

def confusion_matrices(df):
    """ 
    Computes confusion matrices of an input data frame.
    :param input_df the input data frame containing two tables, the truth (y) and the predicted one (y_pred)
    
    """
    y = df[0]
    y_pred = df[1]
    confusion_matrix = metrics.confusion_matrix(y, y_pred).tolist()
    multilabel_confusion_matrix =  metrics.multilabel_confusion_matrix(y, y_pred).tolist()
    return [confusion_matrix, multilabel_confusion_matrix]

def write_confusion_matrices(confusion_matrix, multilabel_confusion_matrix, output_bucket, output_key):
    """
    Writes confusion matrices to s3 bucket
    :param confusion_matrix the confusion matrix of size class_number x class_number
    :param multilabel_confusion_matrix the confusion matrix of size class_number x 2 x 2
    """
    s3_resource.Object(output_bucket, "{}/confusion_matrix.json".format(output_key)).put(
        Body=bytes(json.dumps(confusion_matrix), "utf-8")
    )
    s3_resource.Object(output_bucket, "{}/multilabel_confusion_matrix.json".format(output_key)).put(
        Body=bytes(json.dumps(multilabel_confusion_matrix), "utf-8")
    )


def write_df(df, output_bucket, output_key):
    file_buffer = StringIO()
    df.to_csv(file_buffer, sep=",", index=False, header=False)
    s3_resource.Object(output_bucket, "{}/metrics.csv".format(output_key)).put(
        Body=file_buffer.getvalue()
    )


def read_df(bucket, key, sep, header):
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket, Key=key)

    return pd.read_csv(obj["Body"], sep=sep, header=header)