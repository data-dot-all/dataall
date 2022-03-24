from diagrams.aws.mobile import APIGateway
from diagrams.aws.security import Cognito

from diagrams import Diagram, Node, Cluster
from diagrams.azure.identity import ActiveDirectory

with Diagram(
    'Authentication', direction='LR', show=False, filename='../docs/assets/auth'
):

    with Cluster('Corporate Identify Provider'):
        ad = ActiveDirectory('ActiveDirectory')

    with Cluster('Aws'):
        up = Cognito('UserPool')
        api = APIGateway('dataall')

    ad >> up >> api
