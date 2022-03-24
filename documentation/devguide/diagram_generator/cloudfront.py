from diagrams import Diagram
from diagrams.programming.framework import React
from diagrams.onprem.client import Client
from diagrams.aws.compute import Fargate, ApplicationAutoScaling
from diagrams.aws.storage import S3
from diagrams.aws.database import Aurora
from diagrams.aws.network import ELB, CloudFront
from diagrams.aws.mobile import APIGateway


with Diagram('Frontend', show=False, filename='../docs/assets/cloudfront'):
    distro = CloudFront('dataall')
    content = S3('Static')
    client = Client('Browner')
    app = React('UI')
    client >> distro
    distro >> content
    app >> client
