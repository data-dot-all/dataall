import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from engine.glue.glue_utils import ConfigReader, Runner
from pyspark import SparkContext

glueContext = GlueContext(SparkContext.getOrCreate())
spark = glueContext.spark_session
logger = glueContext.get_logger()

args = getResolvedOptions(
    sys.argv, ['JOB_NAME', 'BUCKET_NAME', 'CONFIGPATH', 'ISGLUERUNTIME', 'STAGE']
)

job = Job(glueContext)
job.init(args['JOB_NAME'], args)
job_run_id = args['JOB_RUN_ID']
yamlpath = args.get('CONFIGPATH')
logger.info('Loading configuration files')
config = ConfigReader(path=f'/tmp/{yamlpath}', args=args)
logger.info('Configuration loaded')

runner = Runner(config=config, spark=spark, logger=logger, glueContext=glueContext)
runner.run()

job.commit()
logger.info('Glue job committed')

bucket = args.get('BUCKET_NAME')
key = f'gluejobsreport/{job_run_id}/report.json'
logger.info(f'Saving dag to s3://{bucket}/{key}')
runner.save_dag(bucket=bucket, key=key)
