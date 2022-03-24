"""
Glue Job to tranform SAS7BDAT data to Parquet
"""
# AWS data.all step function integration imports
from .base_step import Step
from .observability import StepMetric
from .structured_logging import StructuredLogger

# Generic AWS glue imports
import csv
import datetime
import sys
import re
import math
import boto3
from statistics import stdev
from pyspark.context import SparkContext
from pyspark.conf import SparkConf
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import to_date, to_timestamp


@Step(
    type='convert_to_parquet',
    props_schema={
        'type': 'object',
        'required': [
            'input_format',
            'input_bucket',
            'input_key',
            'output_bucket',
            'output_key',
            'partitions',
        ],
        'properties': {
            'input_format': {'type': 'string'},
            'input_bucket': {'type': 'string'},
            'input_key': {'type': 'string'},
            'output_bucket': {'type': 'string'},
            'output_key': {'type': 'string'},
            'partitions': {'type': 'int'},
        },
    },
)
class ConvertToParquet:
    # Utilities

    def get_size(bucket, path):
        s3 = boto3.resource('s3')
        my_bucket = s3.Bucket(bucket)
        total_size = 0

        for obj in my_bucket.objects.filter(Prefix=path):
            total_size = total_size + obj.size

        return total_size

    def is_dt(cell):
        if len(cell) < 8:
            return False
        if sum(c.isdigit() for c in cell) > len(cell) * 0.6:
            return True
        return False

    def is_double(cell):
        if re.match(r'^-?\d+\.\d+$', cell):
            return True
        return False

    def is_int(cell):
        if re.match(r'^(?:-?[1-9][0-9]*|0)$', cell):
            return True
        return False

    date_patterns = [
        (1, '%Y-%m-%d', 'yyyy-MM-dd'),
        (2, '%Y/%m/%d', 'yyyy/MM/dd'),
        (3, '%d-%m-%Y', 'dd-MM-yyyy'),
        (4, '%d/%m/%Y', 'dd/MM/yyyy'),
        (5, '%m/%d/%Y', 'MM/dd/yyyy'),
        (6, '%Y%m%d', 'yyyyMMdd'),
        (-1, '%Y-%m-%dT%H:%M:%S', 'yyyy-MM-ddTHH:mm:ss'),
        (-2, '%d%b%Y:%H:%M:%S', 'ddMMMyyyy:HH:mm:ss'),
        (-3, '%Y-%m-%d %H:%M:%S', 'yyyy-MM-dd HH:mm:ss'),
    ]

    def parse_dt(cell):
        for i, pattern, _ in date_patterns:
            try:
                dt = datetime.datetime.strptime(cell, pattern)
                return i, str(cell)
            except:
                pass

        return 'string', str(cell)

    def parse_cell(cell):
        cell = cell.strip()
        if cell == '':
            return '', cell

        if is_dt(cell):
            dt = parse_dt(cell)
            if type(dt[0]) == int:
                return dt

        if is_int(cell):
            return 'bigint', cell
        if is_double(cell):
            return 'double', cell

        return 'string', str(cell)

    def pycsv_reader(dialect, csv_rows):
        sep = dialect.delimiter
        qc = dialect.quotechar

        for row in csv_rows:
            if re.match(f'^{sep}', row) is not None:
                row = '""' + row
            cells = re.findall(
                f'(?:{sep}|\r?\n|^)({qc}(?:(?:{qc}{qc})*[^{qc}]*)*{qc}|[^{qc}{sep}\r?\n]*|(?:\r?\n|$))',
                row,
            )
            yield [
                parse_cell(re.sub(f'^{qc}|{qc}$', '', cell).strip()) for cell in cells
            ]

    def multimode(lst):
        counts = [(x, lst.count(x)) for x in set(lst)]
        return [
            j[0] for i, j in enumerate(counts) if j[1] == max([x[1] for x in counts])
        ]

    def majority_selector(options, csv_rows):

        match_count = [[len(re.findall(o, x)) for x in csv_rows] for o in options]

        modes = list(
            zip(
                [max(multimode(x)) for x in match_count],
                [stdev(x) if len(x) > 1 else 0 for x in match_count],
            )
        )
        # allow no variation in the number of columns detected
        sep_modes_no_stdev = [x for x in enumerate(modes) if x[1][0] != 0]
        stdev_list = [x[1][1] for x in sep_modes_no_stdev]
        # find first separator with highest number of columns detected
        option_index = stdev_list.index(min(stdev_list))

        return (
            options[sep_modes_no_stdev[option_index][0]],
            modes[sep_modes_no_stdev[option_index][0]][0],
            modes[sep_modes_no_stdev[option_index][0]][1],
        )

    def detect_quoting(sep, sep_count, quotechars, csv_rows):
        quotechar, quotechar_count, quotechar_stdev = majority_selector(
            [sep + q for q in quotechars], csv_rows
        )
        quoting = csv.QUOTE_NONE
        if quotechar_count == 0:
            quoting = csv.QUOTE_NONE
        elif quotechar_stdev > 0:
            # Only required data entries are quoted
            quoting = csv.QUOTE_MINIMAL
        elif math.abs(quotechar_stdev) < 1e-5 and sep_count - quotechar_count == 1:
            # All fields are quoted
            quoting = csv.QUOTE_ALL
        elif math.abs(quotechar_stdev) < 1e-5 and sep_count - quotechar_count > 1:
            quoting = csv.QUOTE_NONNUMERIC

        return quotechar, quoting

    def pycsv_spark_reader(path, slstep, minPartitions=100):
        sl = StructuredLogger(slstep)

        separators = [',', r'\|', r'\t', r'\t+', ' +']
        quotechars = ['"']

        rdd = sc.textFile(path, int(minPartitions))
        has_header = csv.Sniffer().has_header(rdd.first())

        # Remove any header in the data
        sl.next_step()
        if has_header == True:
            header = rdd.first()
            sl.info('Header: %s', str(header))
            rdd = rdd.filter(lambda row: row != header)

        # Determine CSV dialect
        sl.next_step()
        sample_ratio = 0.1
        sample_rows = 10000
        sample_max_rows = int(sample_rows / sample_ratio * 2)
        nrows = rdd.count()
        if nrows < sample_rows / sample_ratio:
            sample_rows = nrows
        else:
            sample_rows = int(math.ceil(nrows * sample_ratio))
            if sample_rows > sample_max_rows:
                sample_rows = sample_max_rows

        sl.info('Sampling %s rows to detect delimiter and column types.', sample_rows)
        rdd_sample = rdd.takeSample(False, sample_rows)

        sl.next_step()
        sep, sep_count, sep_stdev = majority_selector(separators, rdd_sample)

        sl.info("Detected delimiter: '%s'", sep)

        # replace detected separator regex with a safe one
        sl.next_step()
        dialect = csv.Sniffer().sniff(rdd_sample[0])
        dialect.delimiter = sep
        dialect.quotechar = quotechars[0]  # XXX: Only " for now

        # Parse columns in RDD
        sl.next_step()
        rdd2 = rdd.mapPartitions(lambda x: pycsv_reader(dialect, x))
        ncol = len(rdd2.first())
        rdd2_count_before = rdd2.count()
        rdd2.filter(lambda row: len(row) != ncol).repartition(1).saveAsTextFile(
            input_args['TempDir'] + '/spark-read-errorlines.txt'
        )
        rdd2 = rdd2.filter(lambda row: len(row) == ncol)
        rdd2_count_after = rdd2.count()
        sl.info(
            'Removed %s lines with different number of columns than expected: %s',
            str(rdd2_count_before - rdd2_count_after),
            ncol,
        )
        rdd2_types = rdd2.map(lambda x: [c[0] for c in x]).takeSample(
            False, sample_rows
        )
        rdd2_data = rdd2.map(lambda x: [c[1] for c in x])
        sl.info('Parsed CSV data:')
        sl.info(rdd2_data.take(5))
        sl.info('Detected column types:')
        sl.info(rdd2_types[:5])

        # RDD to DF
        sl.next_step()
        if has_header == True:
            # preserve header
            column_names = re.split(sep, header)
            column_names_clean = [
                re.sub(r'[ ,;{}\(\)\n\t=]', '_', x) for x in column_names
            ]
            df = spark.createDataFrame(
                rdd2_data, [c.strip().lower() for c in column_names_clean]
            )
        else:
            df = spark.createDataFrame(rdd2_data)

        # Cast DF fields to detected type
        sl.next_step()
        for c, col_name in enumerate(df.columns):
            dt_list = [x[c] for x in rdd2_types if x[c]]
            dt_list_set = set(dt_list)

            if len(dt_list_set) == 1:
                ct = dt_list[0]
            elif 'string' in dt_list_set:
                ct = 'string'
            elif all(x == 6 or x == 'bigint' for x in dt_list_set):
                ct = 'bigint'
            elif all(x in dt_list_set for x in ['bigint', 'double']):
                ct = 'double'
            elif all(type(x) == int for x in dt_list_set):
                # Choose the most frequent date fromat, this is especially useful with dates since it is not possible to tell the difference between ddmm and mmdd for 1 <= dd <= 12.
                df_list = multimode(dt_list)
                if len(df_list) > 1:
                    sl.info(
                        'Could not detect date format for column %s, the following formats were equally frequent: %s',
                        col_name,
                        str(df_list),
                    )
                    ct = 'string'
                elif len(df_list) == 1:
                    ct = df_list[0]
                else:
                    ct = 'string'
            else:
                ct = 'string'

            sl.info('Chose type %s for column %s.', str(ct), col_name)

            if type(ct) == str:
                # short forms: https://stackoverflow.com/a/32286450
                df = df.withColumn(col_name, df[col_name].cast(ct))
            elif ct > 0:
                df = df.withColumn(
                    col_name,
                    to_date(
                        col_name,
                        [item for item in date_patterns if item[0] == ct][0][2],
                    ),
                )
            elif ct < 0:
                df = df.withColumn(
                    col_name,
                    to_timestamp(
                        col_name,
                        [item for item in date_patterns if item[0] == ct][0][2],
                    ),
                )

        return df

    def glue_job(
        input_args,
        raw_format,
        s3_source,
        s3_source_size,
        s3_dest_bucket,
        s3_dest_folder,
        slstep,
    ):

        sl = StructuredLogger(slstep)

        # Start job bookmark
        job.init(input_args['JOB_NAME'], input_args)
        loadoptions = dict(map(lambda x: x.split('='), raw_format.split(' ')))

        if loadoptions['format'] == 'csv':
            df = pycsv_spark_reader(
                s3_source, slstep, minPartitions=input_args['PARTITIONS']
            )
            npartitions = math.ceil(s3_source_size * 0.03 / 128e6)
        else:
            df = spark.read.load(s3_source, **loadoptions)
            npartitions = math.ceil(s3_source_size / 128e6)

        sl.info('Making %s partitions', str(npartitions))

        df.repartition(npartitions).write.format('parquet').mode('overwrite').save(
            's3://' + s3_dest_bucket + '/' + s3_dest_folder
        )

        s3 = boto3.resource('s3')
        s3.Object(s3_dest_bucket, s3_dest_folder + '/' + '_READY_TO_PERFORM_QC').put(
            Body=''
        )

        # Submit job bookmark to store job progress
        job.commit()

    def run_step(self, spark, config, context=None, glueContext=None):

        input_args = {
            'JOB_NAME': config.args.get('JOB_NAME'),
            'OUTPUT_BUCKET': self.props.get('output_bucket'),
            'OUTPUT_PREFIX': self.props.get('output_prefix'),
            'INPUT_BUCKET': self.props.get('input_bucket'),
            'INPUT_KEY': self.props.get('input_key'),
            'INPUT_FORMAT': self.props.get('input_format'),
            'PARTITIONS': self.props.get('partitions'),
        }
        sl.info('Input arguments: %s', str(input_args))
        """
        # @params: [JOB_NAME]
        input_args = getResolvedOptions(
            sys.argv,
            [
                "JOB_NAME",
                "OUTPUT_BUCKET",
                "OUTPUT_PREFIX",
                "INPUT_BUCKET",
                "INPUT_KEY",
                "INPUT_FORMAT",
                "PARTITIONS",
            ],
        )

        sc = spark.SparkContext
        hc = sc._jsc.hadoopConfiguration()
        # https://aws.amazon.com/premiumsupport/knowledge-center/emr-timeout-connection-wait/
        hc.setInt("fs.s3.maxConnections", 5000)
        # java.lang.ClassNotFoundException: Class org.apache.hadoop.mapred.DirectOutputCommitter not found
        hc.set("mapred.output.committer.class", "org.apache.hadoop.mapred.FileOutputCommitter")
        """
        sl = StructuredLogger()

        """
        spark_conf = SparkConf().setAll([("spark.hadoop.fs.s3.canned.acl", "BucketOwnerRead")])
        sc = SparkContext(conf=spark_conf)
        hc = sc._jsc.hadoopConfiguration()
        # https://aws.amazon.com/premiumsupport/knowledge-center/emr-timeout-connection-wait/
        hc.setInt("fs.s3.maxConnections", 5000)
        # java.lang.ClassNotFoundException: Class org.apache.hadoop.mapred.DirectOutputCommitter not found
        hc.set("mapred.output.committer.class", "org.apache.hadoop.mapred.FileOutputCommitter")
        glue_context = GlueContext(sc)
        spark = glue_context.spark_session
        job = Job(glue_context)
        """

        # Parse input
        input_key_parts = input_args['INPUT_KEY'].split('/')
        if len(input_key_parts) < 4:
            sl.s3_skip_wrong_key(
                input_args['INPUT_KEY'], 'tonnedl/raw/truven/*', input_args
            )
            quit()

        input_table_key = '/'.join(input_key_parts[0:-1])
        output_table_key = '/'.join(input_key_parts[3:-1])

        sl.next_step()
        sl.function_start(
            'The bucket and key are OK.',
            'Transformation done',
            glue_job,
            input_args=input_args,
            raw_format=input_args['INPUT_FORMAT'],
            s3_source='s3://' + input_args['INPUT_BUCKET'] + '/' + input_table_key,
            s3_source_size=get_size(input_args['INPUT_BUCKET'], input_table_key),
            s3_dest_bucket=input_args['OUTPUT_BUCKET'],
            s3_dest_folder=input_args['OUTPUT_PREFIX'] + '/' + output_table_key,
            slstep=sl.step,
            eventMessage=input_args,
        )

        self.emit_metric(
            StepMetric(
                name=f'{job_name}/{self.name}/count',
                unit='NbRecord',
                value=df.rdd.countApprox(timeout=800, confidence=0.5),
            )
        )


#### IN NOVO

# The job
def glue_job(
    input_args,
    raw_format,
    s3_source,
    s3_source_size,
    s3_dest_bucket,
    s3_dest_folder,
    slstep,
):
    sl = StructuredLogger(slstep)

    # Start job bookmark
    job.init(input_args['JOB_NAME'], input_args)

    loadoptions = dict(map(lambda x: x.split('='), raw_format.split(' ')))

    if loadoptions['format'] == 'csv':
        df = pycsv_spark_reader(
            s3_source, slstep, minPartitions=input_args['PARTITIONS']
        )
        npartitions = math.ceil(s3_source_size * 0.03 / 128e6)
    else:
        df = spark.read.load(s3_source, **loadoptions)
        npartitions = math.ceil(s3_source_size / 128e6)

    sl.info('Making %s partitions', str(npartitions))

    df.repartition(npartitions).write.format('parquet').mode('overwrite').save(
        's3://' + s3_dest_bucket + '/' + s3_dest_folder
    )

    s3 = boto3.resource('s3')
    s3.Object(s3_dest_bucket, s3_dest_folder + '/' + '_READY_TO_PERFORM_QC').put(
        Body=''
    )

    # Submit job bookmark to store job progress
    job.commit()


sl = StructuredLogger()

# @params: [JOB_NAME]
input_args = getResolvedOptions(
    sys.argv,
    [
        'JOB_NAME',
        'OUTPUT_BUCKET',
        'OUTPUT_PREFIX',
        'INPUT_BUCKET',
        'INPUT_KEY',
        'INPUT_FORMAT',
        'PARTITIONS',
    ],
)
sl.info('Input arguments: %s', str(input_args))

spark_conf = SparkConf().setAll([('spark.hadoop.fs.s3.canned.acl', 'BucketOwnerRead')])
sc = SparkContext(conf=spark_conf)
hc = sc._jsc.hadoopConfiguration()
# https://aws.amazon.com/premiumsupport/knowledge-center/emr-timeout-connection-wait/
hc.setInt('fs.s3.maxConnections', 5000)
# java.lang.ClassNotFoundException: Class org.apache.hadoop.mapred.DirectOutputCommitter not found
hc.set('mapred.output.committer.class', 'org.apache.hadoop.mapred.FileOutputCommitter')
glue_context = GlueContext(sc)

spark = glue_context.spark_session
job = Job(glue_context)

# Parse input
input_key_parts = input_args['INPUT_KEY'].split('/')
if len(input_key_parts) < 4:
    sl.s3_skip_wrong_key(input_args['INPUT_KEY'], 'tonnedl/raw/truven/*', input_args)
    quit()

input_table_key = '/'.join(input_key_parts[0:-1])
output_table_key = '/'.join(input_key_parts[3:-1])

sl.next_step()
sl.function_start(
    'The bucket and key are OK.',
    'Transformation done',
    glue_job,
    input_args=input_args,
    raw_format=input_args['INPUT_FORMAT'],
    s3_source='s3://' + input_args['INPUT_BUCKET'] + '/' + input_table_key,
    s3_source_size=get_size(input_args['INPUT_BUCKET'], input_table_key),
    s3_dest_bucket=input_args['OUTPUT_BUCKET'],
    s3_dest_folder=input_args['OUTPUT_PREFIX'] + '/' + output_table_key,
    slstep=sl.step,
    eventMessage=input_args,
)
