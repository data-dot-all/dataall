import os

import boto3
from botocore.exceptions import ClientError


def setup_rum_domain(resource_prefix, envname, custom_domain, region):
    try:
        if custom_domain == 'False':
            ssm = boto3.client('ssm', region_name='us-east-1')
            webapp_domain = ssm.get_parameter(Name=f'/dataall/{envname}/CloudfrontDistributionDomainName')['Parameter'][
                'Value'
            ]
            rum = boto3.client('rum', region_name=region)
            rum.get_app_monitor(Name=f'{resource_prefix}-{envname}-monitor')
            print('Updating RUM Monitor')
            response = rum.update_app_monitor(Domain=f'*.{webapp_domain}', Name=f'{resource_prefix}-{envname}-monitor')
            print(f'RUM updated successfully {response}')
        else:
            print('RUM domain is already configured. Nothing to do here...')

    except ClientError as e:
        print('Error updating app monitor', e)
        raise e


if __name__ == '__main__':
    print('Starting RUM Configuration...')
    envname = os.environ.get('envname', 'prod')
    custom_domain = os.environ.get('custom_domain', 'False')
    region = os.environ.get('deployment_region', 'eu-west-1')
    resource_prefix = os.environ.get('resource_prefix', 'dataall')
    setup_rum_domain(resource_prefix, envname, custom_domain, region)
    print('RUM Configuration Finished Successfully')
