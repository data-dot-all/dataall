import os

# workaround: SPARK_VERSION must be already set before import of pydeequ packages
# ruff: noqa: E402
os.environ['SPARK_VERSION'] = '3.3'

import json
import logging
import pprint
import sys
import boto3
from botocore.exceptions import ClientError
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pydeequ.profiles import ColumnProfilerRunner

sc = SparkContext.getOrCreate()
sc._jsc.hadoopConfiguration().set('fs.s3.canned.acl', 'BucketOwnerFullControl')
sc.setLogLevel('INFO')

glueContext = GlueContext(sc)
spark = glueContext.sparkSession

MSG_FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'
DATETIME_FORMAT = '%y/%m/%d %H:%M:%S'
logging.basicConfig(format=MSG_FORMAT, datefmt=DATETIME_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info('Entered Script')
logger.info('Args = %s', pprint.pformat(sys.argv))
list_args = [
    'database',
    'datasetUri',
    'datasetBucket',
    'environmentUri',
    'environmentBucket',
    'dataallRegion',
    'table',
    'SPARK_VERSION',
]
try:
    args = getResolvedOptions(sys.argv, list_args)
    logger.info(f'Table arg passed profiling will run only on specified table >>> {args["table"]}')
except Exception as e:
    logger.info(f'No Table arg passed profiling will run on all dataset tables: {e}')
    list_args.remove('table')
    args = getResolvedOptions(sys.argv, list_args)

os.environ['SPARK_VERSION'] = args.get('SPARK_VERSION', '3.1')

logger.info('Parsed Retrieved parameters')

logger.info('Parsed Args = %s', pprint.pformat(args))

logger.info('Starting Profiling')

glue_client = boto3.client('glue')

s3_client = boto3.client('s3')

s3_resource = boto3.resource('s3')

sts_client = boto3.client('sts')

account_id = sts_client.get_caller_identity()['Account']

role_arn = sts_client.get_caller_identity()['Arn']


def get_database_tables(client, database):
    all_database_tables = []
    try:
        paginator = client.get_paginator('get_tables')
        pages = paginator.paginate(DatabaseName=database, MaxResults=500)
        for page in pages:
            for table in page.get('TableList'):
                all_database_tables.append(table['Name'])
        return all_database_tables
    except ClientError as e:
        logger.error(f'Could not retrieve all database {database} tables ')
        raise e


def run_table_profiling(
    glue,
    s3_client,
    s3_resource,
    dataset_uri,
    database,
    table,
    dataset_bucket,
    results_bucket,
):
    response = glue.get_table(DatabaseName=database, Name=table)
    location = response['Table'].get('StorageDescriptor', {}).get('Location')
    output_directory = f's3://{results_bucket}/profiling/results/{dataset_uri}/{table}/{args["JOB_RUN_ID"]}'

    if location:
        logger.debug('Profiling table for %s %s ', database, table)
        logger.debug('using %s', database)
        spark.sql('use `{}`'.format(database))
        df = spark.sql('select * from `{}`'.format(table))
        total = df.count()
        logger.debug('Retrieved count for %s %s', table, total)

        result = ColumnProfilerRunner(spark).onData(df).run()
        rs = []
        data_types = []
        for col, profile in result.profiles.items():
            logger.info(f'PROFILE OBJECT: {profile}')
            histogram = []
            if profile.histogram:
                for h in profile.histogram:
                    logger.info(f'Building Histogram: {h}')
                    histogram.append(
                        {
                            'value': h.value,
                            'ratio': h.ratio,
                            'count': h.count,
                        }
                    )
            if profile.dataType:
                added = False
                for d in data_types:
                    if d['type'] == profile.dataType:
                        d['count'] = d['count'] + 1
                        added = True
                        break
                if not added:
                    data_types.append({'type': profile.dataType, 'count': 1})

            column_results = {
                'Name': col,
                'Type': getattr(profile, 'dataType', None),
                'Metadata': {
                    'Completeness': getattr(profile, 'completeness', None),
                    'Minimum': getattr(profile, 'minimum', None),
                    'Maximum': getattr(profile, 'maximum', None),
                    'Mean': getattr(profile, 'mean', None),
                    'StdDeviation': getattr(profile, 'stdDev', None),
                    'Histogram': histogram,
                    'Unique': getattr(profile, 'approximateNumDistinctValues', None),
                    'MostCommon': None,
                },
            }
            rs.append(column_results)

        profiling_results = {
            'dataset_uri': dataset_uri,
            'table_name': table,
            'job_run_id': args['JOB_RUN_ID'],
            'table_nb_rows': total,
            'columns': rs,
            'dataTypes': data_types,
        }
        logger.info(f'>>>>> FINAL JSON>>>>>>>>>: {profiling_results}')

        response = s3_client.put_object(
            Bucket=results_bucket,
            Key=f'profiling/results/{dataset_uri}/{table}/{args["JOB_RUN_ID"]}/results.json',
            Body=json.dumps(profiling_results),
        )
        logger.info(f'JSON written to s3: {response}')


def run(
    glue=glue_client,
    s3_client=s3_client,
    s3_resource=s3_resource,
    args=args,
):
    dataset_uri = args['datasetUri']
    database = args['database']
    table = args.get('table')
    dataset_bucket = args['datasetBucket']
    results_bucket = args['environmentBucket']
    tables = [table] if table else get_database_tables(glue, database)
    for table in tables:
        try:
            run_table_profiling(
                glue,
                s3_client,
                s3_resource,
                dataset_uri,
                database,
                table,
                dataset_bucket,
                results_bucket,
            )
        except Exception as e:
            logger.error(f'Failed to profile table {table} due to: {e}')
            raise e


run()
