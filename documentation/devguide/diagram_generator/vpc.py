from diagrams import Cluster, Diagram
from diagrams.programming.framework import React
from diagrams.aws.compute import Fargate, ApplicationAutoScaling, Lambda
from diagrams.aws.database import Aurora
from diagrams.aws.network import (
    ELB,
    CloudFront,
    VPC,
    PrivateSubnet,
    PublicSubnet,
    NATGateway,
)
from diagrams.aws.security import WAF, Cognito
from diagrams.aws.mobile import APIGateway

with Diagram(
    'Network Settings', direction='TB', show=False, filename='../docs/assets/vpc'
):

    vpc = VPC('dataall VPC)')
    nat = NATGateway('NAT Gateway')
    with Cluster('VPC'):
        with Cluster('AZ1'):
            with Cluster('Public Subnets'):
                az1pub = [PublicSubnet('Pub1'), PublicSubnet('Pub2')]

            with Cluster('Private Subnets'):
                az1prv = [PublicSubnet('Prv1'), PublicSubnet('Prv2')]

        with Cluster('AZ2'):
            with Cluster('Public Subnets'):
                az2pub = [PublicSubnet('Pub1'), PublicSubnet('Pub2')]

            with Cluster('Private Subnets'):
                az2prv = [PublicSubnet('Prv1'), PublicSubnet('Prv2')]

    vpc >> nat
    vpc >> az1prv
    vpc >> az1pub
    vpc >> az2prv
    vpc >> az2pub
    az1prv >> nat
    az2prv >> nat
