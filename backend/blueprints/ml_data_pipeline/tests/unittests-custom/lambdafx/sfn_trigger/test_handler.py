
from customcode.lambda_functions.example_sfn_trigger import handler
from datetime import datetime
""" For example for the iris pipeline:
def test_make_config():
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    stage = "test"
    bucket = "mybucket"
    model_name = "m1"
    launch_end_point = True
    
    cfg = handler.make_config(timestamp, stage, bucket, model_name, launch_end_point) 
    assert cfg ==  {'bucket': 'mybucket', 
                    'key' : 'data/iris/iris.data',
                    'output_prefix': f'data/output/iris/{stage}/{timestamp}/prepare',
                    'training_input': {'content_type': 'text/csv', 
                                       'train_s3_uri': {'bucket': 'mybucket', 
                                                        'key_prefix': f'data/output/iris/{stage}/{timestamp}/prepare/training_data.csv'}, 
                                       'validation_s3_uri': {'bucket': 'mybucket', 'key_prefix': f'data/output/iris/{stage}/{timestamp}/prepare/validation_data.csv'}
                                      },
                    'training_output': f's3://mybucket/data/output/iris/{stage}/{timestamp}/training/', 
                    'model_name': f'm1-{timestamp}',
                     'launch_end_point': launch_end_point,
                    'hpo_output': f's3://mybucket/data/output/iris/{stage}/{timestamp}/hpo/', 
                    'EndPoint': {'config_name': f'{model_name}-{timestamp}-ep-conf', 'name': 'iris-test'},
                    'timestamp': timestamp,
                    's3_transform_input': f's3://mybucket/data/output/iris/{stage}/{timestamp}/prepare/test.csv',
                    's3_transform_output': f's3://mybucket/data/output/iris/{stage}/{timestamp}/transform/',
                    'transform_job_name': f'transform-{model_name}-{timestamp}',
                    'kpi_output_path': {'bucket': bucket,
                                        'key_prefix': f'data/output/iris/{stage}/{timestamp}/metrics/'},
                    's3_transform_output_path': {'bucket': bucket,
                                                'key_prefix': f'data/output/iris/{stage}/{timestamp}/transform/'}}

"""
