"""
Main application for cdk deploy.
It creates one or more stacks.
"""

import os
import re

from aws_cdk import core
from stack import DataPipeline
from utils.task_group_reader import TaskGroupReader

app = core.App()

# read configuration file
pipeline = TaskGroupReader(path='config.yaml')
group_len = len(pipeline.definition.get('groups', []))
resources_len = len(pipeline.definition.get('aws_resources', []))

# create the pipeline
pipeline_name = os.environ.get('PIPELINE_NAME', 'SampleDataProcessingPipeline')
default_description = f"""'{pipeline_name}/{pipeline.definition.get("name","")}' pipeline,
                                                {group_len} groups and {resources_len} resources"""
stack = DataPipeline(
    app,
    pipeline_name,
    pipeline,
    description=pipeline.definition.get('description', default_description),
)
if os.path.exists('configs'):
    for fname in os.listdir('configs'):
        if os.path.isfile(fname):
            pipeline = TaskGroupReader(path=f'configs/{fname}')
            group_len = len(pipeline.definition.get('groups', []))
            resources_len = len(pipeline.definition.get('aws_resources', []))

            # create the pipeline
            name = pipeline.definition.get('name', '')
            pipeline_name = (
                os.environ.get('PIPELINE_NAME', 'SampleDataProcessingPipeline')
                + '-'
                + name
            )
            pipeline_name = re.sub('[^A-Za-z0-9-]', '-', pipeline_name)
            default_description = f"""'{pipeline_name}/{pipeline.definition.get("name","")}' pipeline ,
                                                    {group_len} groups and {resources_len} resources"""
            stack = DataPipeline(
                app,
                pipeline_name,
                pipeline,
                description=pipeline.definition.get('description', default_description),
            )


app.synth()
