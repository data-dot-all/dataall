from diagrams import Diagram
from diagrams import Cluster, Diagram
from diagrams.programming.framework import React
from diagrams.aws.compute import Fargate, ApplicationAutoScaling, Lambda, ECS, Fargate
from diagrams.aws.database import Aurora
from diagrams.aws.network import ELB, CloudFront
from diagrams.aws.security import WAF, Cognito
from diagrams.aws.mobile import APIGateway


with Diagram(
    'Graphql Handler', direction='LR', show=False, filename='../docs/assets/db'
):
    service = ECS('ECS cluster')
    with Cluster('Task'):
        containers = [Fargate('Container'), Fargate('Container')]
    service >> containers

    db = Aurora('Shared State')

    auth = Lambda('Authorizer')
    graphql = Lambda('API Handler')
    worker = Lambda('Worker')
    containers >> db
    auth >> db
    worker >> db
    graphql >> db
