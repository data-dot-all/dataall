import os

import boto3
from bs4 import BeautifulSoup


def create_react_env_file(
    region,
    envname,
    resource_prefix,
    internet_facing='True',
    custom_domain='False',
    cw_rum_enabled='False',
):
    ssm = boto3.client('ssm', region_name=region)
    user_pool_id = ssm.get_parameter(Name=f'/dataall/{envname}/cognito/userpool')[
        'Parameter'
    ]['Value']
    print(f'Cognito Pool ID: {user_pool_id}')
    app_client = ssm.get_parameter(Name=f'/dataall/{envname}/cognito/appclient')[
        'Parameter'
    ]['Value']
    domain = ssm.get_parameter(Name=f'/dataall/{envname}/cognito/domain')['Parameter'][
        'Value'
    ]
    domain = f'{domain}.auth.{region}.amazoncognito.com'
    print(f'Cognito Domain: {domain}')
    api_url = ssm.get_parameter(Name=f'/dataall/{envname}/apiGateway/backendUrl')[
        'Parameter'
    ]['Value']
    graphql_api_url = f'{api_url}graphql/api'
    print(f'GraphQl API: {graphql_api_url}')
    search_api_url = f'{api_url}search/api'
    print(f'Search API: {search_api_url}')

    if internet_facing == 'True':
        print('Switching to us-east-1 region...')
        ssm = boto3.client('ssm', region_name='us-east-1')

    if custom_domain == 'False':
        signin_singout_link = ssm.get_parameter(
            Name=f'/dataall/{envname}/CloudfrontDistributionDomainName'
        )['Parameter']['Value']
        user_guide_link = ssm.get_parameter(
            Name=f'/dataall/{envname}/cloudfront/docs/user/CloudfrontDistributionDomainName'
        )['Parameter']['Value']
    else:
        signin_singout_link = ssm.get_parameter(
            Name=f'/dataall/{envname}/frontend/custom_domain_name'
        )['Parameter']['Value']
        user_guide_link = ssm.get_parameter(
            Name=f'/dataall/{envname}/userguide/custom_domain_name'
        )['Parameter']['Value']

    print(f'UI: {signin_singout_link}')
    print(f'USERGUIDE: {user_guide_link}')

    with open('frontend/.env', 'w') as f:
        file_content = f"""GENERATE_SOURCEMAP=false
REACT_APP_GRAPHQL_API={graphql_api_url}
REACT_APP_SEARCH_API={search_api_url}
REACT_APP_COGNITO_USER_POOL_ID={user_pool_id}
REACT_APP_COGNITO_APP_CLIENT_ID={app_client}
REACT_APP_COGNITO_DOMAIN={domain}
REACT_APP_COGNITO_REDIRECT_SIGNIN=https://{signin_singout_link}
REACT_APP_COGNITO_REDIRECT_SIGNOUT=https://{signin_singout_link}
REACT_APP_USERGUIDE_LINK=https://{user_guide_link}
"""
        print('.env content: \n', file_content)
        f.write(file_content)

    if cw_rum_enabled == 'True':
        rum = boto3.client('rum', region_name=region)
        app_monitor = rum.get_app_monitor(Name=f'{resource_prefix}-{envname}-monitor')[
            'AppMonitor'
        ]
        with open('frontend/public/index.html', 'r') as file:
            index_html = BeautifulSoup(file.read(), 'html.parser')
            print(index_html.prettify())
            head_tag = index_html.head
            script_tag = index_html.new_tag('script')
            script_tag.append(
                """
                (function(n,i,v,r,s,c,x,z){x=window.AwsRumClient={q:[],n:n,i:i,v:v,r:r,c:c};window[n]=function(c,p){x.q.push({c:c,p:p});};z=document.createElement('script');z.async=true;z.src=s;document.head.insertBefore(z,document.getElementsByTagName('script')[0]);})('cwr','%s','1.0.0','%s','https://client.rum.us-east-1.amazonaws.com/1.0.2/cwr.js',{sessionSampleRate:%s,guestRoleArn:"%s",identityPoolId:"%s",endpoint:"https://dataplane.rum.%s.amazonaws.com",telemetries:[%s],allowCookies:%s,enableXRay:%s});
                """
                % (
                    app_monitor['Id'],
                    region,
                    app_monitor['AppMonitorConfiguration']['SessionSampleRate'],
                    app_monitor['AppMonitorConfiguration']['GuestRoleArn'],
                    app_monitor['AppMonitorConfiguration']['IdentityPoolId'],
                    region,
                    ','.join(
                        [
                            f'"{t}"'
                            for t in app_monitor['AppMonitorConfiguration'][
                                'Telemetries'
                            ]
                        ]
                    ),
                    'true'
                    if app_monitor['AppMonitorConfiguration']['AllowCookies']
                    else 'false',
                    'true'
                    if app_monitor['AppMonitorConfiguration']['EnableXRay']
                    else 'false',
                )
            )
            head_tag.append(script_tag)
            print('Updated index_html...')
            print(index_html.prettify())

        with open('frontend/public/index.html', 'w') as file:
            file.write(str(index_html.prettify()))


if __name__ == '__main__':
    envname = os.environ.get('envname', 'prod')
    resource_prefix = os.environ.get('resource_prefix', 'dataall')
    internet_facing = os.environ.get('internet_facing', 'True')
    custom_domain = os.environ.get('custom_domain', 'False')
    region = os.environ.get('deployment_region', 'eu-west-1')
    enable_cw_rum = os.environ.get('enable_cw_rum', 'False')
    print(
        f'Creating React .env file with params: '
        f'(region={region},envname={envname},resource_prefix={resource_prefix}'
        f'internet_facing={internet_facing},custom_domain={custom_domain},'
        f'cw_rum_enabled={enable_cw_rum})'
    )
    create_react_env_file(
        region, envname, resource_prefix, internet_facing, custom_domain, enable_cw_rum
    )
    print(f'React .env created successfully')
