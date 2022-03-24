from diagrams import Diagram
from diagrams.programming.framework import React
from diagrams.aws.compute import Fargate, ApplicationAutoScaling, Lambda
from diagrams.aws.database import Aurora
from diagrams.aws.network import ELB, CloudFront
from diagrams.aws.security import WAF, Cognito
from diagrams.aws.mobile import APIGateway


with Diagram('Web Service', show=False, filename='../docs/assets/apigw'):
    (
        CloudFront('dataall')
        >> WAF('Web App Firewall')
        >> APIGateway('dataall API ')
        >> Lambda('Authorizer')
        >> Cognito('Users')
    )
