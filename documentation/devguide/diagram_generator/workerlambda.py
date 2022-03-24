from diagrams import Diagram
from diagrams.programming.framework import React
from diagrams.aws.compute import Fargate, ApplicationAutoScaling, Lambda
from diagrams.aws.database import Aurora
from diagrams.aws.analytics import KinesisDataStreams
from diagrams.aws.network import ELB, CloudFront
from diagrams.aws.security import WAF, Cognito
from diagrams.aws.mobile import APIGateway


with Diagram(
    'Short Running Tasks Async Handler',
    show=False,
    filename='../docs/assets/worker-lambda',
):
    Lambda('API Handler') >> KinesisDataStreams('Queue') >> Lambda('Worker')
