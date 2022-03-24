from diagrams import Diagram, Cluster
from diagrams.aws.mobile import APIGateway
from diagrams.aws.storage import S3
from diagrams.aws.security import IAMRole
from diagrams.aws.analytics import GlueDataCatalog
from diagrams.aws.management import Cloudformation

with Diagram(
    'Environments', direction='LR', show=False, filename='../docs/assets/environments'
):
    with Cluster('dataall Account (999999999999/eu-west-1)'):
        app = APIGateway('APIGateway')

    with Cluster('Environment1 (111111111111/eu-west-1)') as env1:
        role1 = IAMRole('AssumedRole')
        stack = Cloudformation('Stacks')
        bucket = S3('Dataset')
        cat = GlueDataCatalog('Catalog ')
        role1 >> stack >> [cat, bucket]

    with Cluster('Environment2 (222222222222/eu-west-1)') as env2:
        role2 = IAMRole('AssumedRole')
        stack = Cloudformation('Stacks')
        bucket = S3('Dataset')
        cat = GlueDataCatalog('Catalog ')
        role2 >> stack >> [cat, bucket]

    app >> [role1, role2]
