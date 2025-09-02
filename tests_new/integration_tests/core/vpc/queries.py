# TODO: This file will be replaced by using the SDK directly

NETWORK_TYPE = """
VpcId
vpcUri
environment {
  environmentUri
  label
  AwsAccountId
  region
}
label
owner
name
description
tags
AwsAccountId
region
privateSubnetIds
publicSubnetIds
SamlGroupName
default
"""


def create_network(client, name, environment_uri, group, vpc_id, public_subnets=[], private_subnets=[], tags=[]):
    query = {
        'operationName': 'createNetwork',
        'variables': {
            'input': {
                'label': name,
                'environmentUri': environment_uri,
                'vpcId': vpc_id,
                'publicSubnetIds': public_subnets,
                'privateSubnetIds': private_subnets,
                'SamlGroupName': group,
                'description': 'Created for integration testing',
                'tags': tags,
            }
        },
        'query': f"""mutation createNetwork($input: NewVpcInput!) {{
                      createNetwork(input: $input) {{
                        {NETWORK_TYPE}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.createNetwork


def delete_network(client, vpc_uri):
    query = {
        'operationName': 'deleteNetwork',
        'variables': {'vpcUri': vpc_uri},
        'query': """mutation deleteNetwork($vpcUri: String!) {
                  deleteNetwork(vpcUri: $vpcUri)
                }
                """,
    }
    response = client.query(query=query)
    return response.data.deleteNetwork


def list_environment_networks(client, environment_uri, term=''):
    query = {
        'operationName': 'listEnvironmentNetworks',
        'variables': {'environmentUri': environment_uri, 'filter': {'term': term}},
        'query': f"""query listEnvironmentNetworks($environmentUri: String!, $filter: VpcFilter!) {{
                  listEnvironmentNetworks(environmentUri: $environmentUri, filter: $filter) {{
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes {{
                      {NETWORK_TYPE}
                    }}
                  }}
                }}
                """,
    }
    response = client.query(query=query)
    return response.data.listEnvironmentNetworks
