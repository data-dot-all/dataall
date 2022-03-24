from diagrams import Cluster, Diagram
from diagrams.onprem.network import Nginx
from diagrams.onprem.compute import Server
from diagrams.onprem.client import Client
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.queue import Celery
from diagrams.aws.compute import Fargate, ECS


with Diagram('CDK Service', show=False, filename='../docs/assets/fargate'):
    service = ECS('ECS cluster')
    with Cluster('Task'):
        containers = [Fargate('Container'), Fargate('Container')]
    service >> containers
