from diagrams.aws.mobile import APIGateway
from diagrams.aws.security import Cognito, IAMRole
from diagrams.aws.storage import S3
from diagrams.aws.analytics import GlueDataCatalog
from diagrams import Diagram, Node, Cluster
from diagrams.azure.identity import ActiveDirectory

with Diagram(
    'Authentication', direction='LR', show=False, filename='../docs/assets/federation'
):

    with Cluster('Corporate Identify Provider'):
        ad = ActiveDirectory('ActiveDirectory')

    with Cluster('Aws'):
        up = Cognito('UserPool')
        api = APIGateway('dataall')

    with Cluster('Environment'):
        bucket = S3('Dataset Bucket')
        cat = GlueDataCatalog('Dataset Database')
        role = IAMRole('Federated Role')
        role >> [bucket, cat]

    ad >> up >> api >> role
