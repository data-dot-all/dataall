from diagrams import Diagram
from diagrams.programming.framework import React
from diagrams.aws.compute import Fargate, ApplicationAutoScaling, Lambda
from diagrams.aws.database import Aurora
from diagrams.aws.network import ELB, CloudFront
from diagrams.aws.mobile import APIGateway


with Diagram('Frontend', show=False, direction='LR', filename='../docs/assets/db'):
    [Lambda('Graphql'), Lambda('Async Task Runner')] >> Aurora('Shared State ')
