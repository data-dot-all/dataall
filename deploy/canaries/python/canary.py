import asyncio
import json
import os
import uuid

from aws_synthetics.selenium import synthetics_webdriver as syn_webdriver
from aws_synthetics.common import synthetics_logger as logger, synthetics_configuration
import boto3
from botocore.exceptions import ClientError

TIMEOUT = 10
ENVNAME = os.getenv('envname')
RESOURCE_PREFIX = os.getenv('resource_prefix')
INTERNET_FACING = os.getenv('internet_facing')

ORG_NAME = f'CanaryOrg-{str(uuid.uuid4())[:8]}'
ENV_NAME = f'CanaryENV-{str(uuid.uuid4())[:8]}'


def get_console_url():
    url = None
    if INTERNET_FACING == 'True':
        ssm = boto3.client('ssm', region_name='us-east-1')
    else:
        ssm = boto3.client('ssm')
    try:
        url = ssm.get_parameter(Name=f'/dataall/{ENVNAME}/frontend/custom_domain_name')['Parameter']['Value']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            try:
                url = ssm.get_parameter(Name=f'/dataall/{ENVNAME}/CloudfrontDistributionDomainName')['Parameter'][
                    'Value'
                ]
            except ClientError as e:
                if e.response['Error']['Code'] == 'ParameterNotFound':
                    raise e
    if not url:
        raise Exception('Application URL not found')
    return f'https://{url}'


def get_canary_onboarded_environment():
    try:
        ssm = boto3.client('ssm')
        env_account = ssm.get_parameter(Name=f'/dataall/{ENVNAME}/canary/environment_account')['Parameter']['Value']

        env_region = ssm.get_parameter(Name=f'/dataall/{ENVNAME}/canary/environment_region')['Parameter']['Value']

    except ClientError as e:
        raise e

    return env_account, env_region


def signout(browser):
    browser.find_element_by_xpath('/html/body/div[1]/div/header/div/div[5]/button').click()
    browser.implicitly_wait(5)
    browser.find_element_by_xpath('/html/body/div[2]/div[3]/div[3]/button').click()


def get_canary_user_credentials():
    sm = boto3.client('secretsmanager')
    secret = sm.get_secret_value(SecretId=f'{RESOURCE_PREFIX}-{ENVNAME}-cognito-canary-user')
    creds = json.loads(secret['SecretString'])
    return creds


async def main():
    url = get_console_url()
    env_account, env_region = get_canary_onboarded_environment()
    browser = syn_webdriver.Chrome()

    # Set synthetics configuration
    synthetics_configuration.set_config(
        {
            'screenshot_on_step_start': True,
            'screenshot_on_step_success': True,
            'screenshot_on_step_failure': True,
        }
    )

    def navigate_to_page():
        browser.implicitly_wait(TIMEOUT)
        browser.get(url)

    await syn_webdriver.execute_step('navigateToUrl', navigate_to_page)

    def go_to_cognito_singin():
        browser.find_element_by_xpath('/html/body/div[1]/div/div/div[2]/div/div[2]/button').click()

    await syn_webdriver.execute_step('click', go_to_cognito_singin)

    try:
        await syn_webdriver.execute_step('click', signout(browser))
    except Exception:
        pass

    def login_cognito():
        creds = get_canary_user_credentials()
        browser.implicitly_wait(TIMEOUT)
        browser.find_element_by_xpath('//div[contains(@class, "visible-lg")]//*[@id="signInFormUsername"]').send_keys(
            creds['username']
        )
        browser.find_element_by_xpath('//div[contains(@class, "visible-lg")]//*[@id="signInFormPassword"]').send_keys(
            creds['password']
        )
        try:
            browser.find_element_by_xpath(
                '/html/body/div[1]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/form/input[3]'
            ).click()
        except Exception as e:
            logger.error(f'Trying Cognito Form input without federation {e}')
            browser.find_element_by_xpath(
                '/html/body/div[1]/div/div[2]/div[2]/div[2]/div[2]/div/div/form/input[3]'
            ).click()

    await syn_webdriver.execute_step('input', login_cognito)

    def go_to_organizations():
        browser.implicitly_wait(TIMEOUT)
        browser.find_element_by_xpath(
            '/html/body/div[1]/div/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[2]/ul[3]/ul/li[1]/a'
        ).click()

    await syn_webdriver.execute_step('click', go_to_organizations)

    def create_organization():
        browser.implicitly_wait(TIMEOUT)
        browser.find_element_by_xpath('/html/body/div[1]/div/div[2]/div/div/div/div/div[1]/div[2]/div/a').click()
        browser.implicitly_wait(TIMEOUT)
        browser.find_element_by_xpath(
            '/html/body/div[1]/div/div[2]/div/div/div/div/div[2]/form/div/div[1]/div/div[2]/div/div/input'
        ).send_keys(ORG_NAME)
        browser.find_element_by_xpath('//*[@id="mui-component-select-SamlGroupName"]').click()
        browser.implicitly_wait(5)
        browser.find_element_by_xpath('//*[@id="menu-SamlGroupName"]/div[3]/ul/li[1]').click()
        browser.find_element_by_xpath(
            '/html/body/div[1]/div/div[2]/div/div/div/div/div[2]/form/div/div[2]/div[2]/button'
        ).click()

    await syn_webdriver.execute_step('click', create_organization)

    def link_environment():
        browser.implicitly_wait(TIMEOUT)
        browser.find_element_by_xpath(
            '//*[@id="root"]/div/div[2]/div/div/div/div/div[2]/div/div[2]/div/button[2]'
        ).click()
        browser.find_element_by_xpath('//*[@id="root"]/div/div[2]/div/div/div/div/div[3]/div/div[2]/div[2]/a').click()
        browser.find_element_by_xpath(
            '/html/body/div[1]/div/div[2]/div/div/div/div/div[3]/form/div/div[1]/div[1]/div[2]/div/div/input'
        ).send_keys(ENV_NAME)
        browser.find_element_by_xpath(
            '//*[@id="root"]/div/div[2]/div/div/div/div/div[3]/form/div/div[2]/div[1]/div/div[2]/div/div/input'
        ).send_keys(env_account)
        browser.find_element_by_xpath('//*[@id="region"]').send_keys(env_region)
        browser.find_element_by_xpath('//*[@id="mui-component-select-SamlGroupName"]').click()
        browser.implicitly_wait(5)
        browser.find_element_by_xpath('//*[@id="menu-SamlGroupName"]/div[3]/ul/li[1]').click()
        browser.find_element_by_xpath(
            '//*[@id="root"]/div/div[2]/div/div/div/div/div[3]/form/div/div[1]/div[2]/div/div[2]/div[1]/div/label/span[1]/span[1]/span[1]'
        ).click()
        browser.find_element_by_xpath(
            '//*[@id="root"]/div/div[2]/div/div/div/div/div[3]/form/div/div[2]/div[2]/button'
        ).click()

    await syn_webdriver.execute_step('click', link_environment)

    def verify_environment_stack_deployment():
        browser.implicitly_wait(TIMEOUT)
        browser.find_element_by_xpath(
            '//*[@id="root"]/div/div[2]/div/div/div/div/div[2]/div/div[2]/div/button[8]'
        ).click()

    await syn_webdriver.execute_step('click', verify_environment_stack_deployment)

    def delete_environment():
        browser.implicitly_wait(TIMEOUT)
        browser.find_element_by_xpath('/html/body/div[1]/div/div[2]/div/div/div/div/div[1]/div[2]/div/button').click()
        browser.find_element_by_xpath('/html/body/div[3]/div[3]/div/div/div[2]/div/label/span[1]/span[1]').click()
        browser.find_element_by_xpath('/html/body/div[3]/div[3]/div/div/div[3]/div[1]/div/div/input').send_keys(
            'permanently delete'
        )
        browser.find_element_by_xpath('/html/body/div[3]/div[3]/div/div/div[3]/div[2]/button').click()

    await syn_webdriver.execute_step('click', delete_environment)

    def delete_organization():
        browser.implicitly_wait(TIMEOUT)
        browser.find_element_by_xpath(
            '/html/body/div[1]/div/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[2]/ul[3]/ul/li[1]/a'
        ).click()
        browser.find_element_by_xpath(
            '/html/body/div[1]/div/div[2]/div/div/div/div/div[2]/div/div/div/div/input'
        ).send_keys('CanaryOrganization')
        browser.find_element_by_xpath(
            '/html/body/div[1]/div/div[2]/div/div/div/div/div[3]/div/div[1]/div/div/div[1]/div/div/div/div[2]/button'
        ).click()
        browser.find_element_by_xpath('/html/body/div[1]/div/div[2]/div/div/div/div/div[1]/div[2]/div/button').click()
        browser.find_element_by_xpath('/html/body/div[3]/div[3]/div/div/div[3]/div/div/input').send_keys(
            'permanently archive'
        )
        browser.find_element_by_xpath('/html/body/div[3]/div[3]/div/div/div[4]/button').click()

    await syn_webdriver.execute_step('click', delete_organization)

    logger.info('Canary successfully executed')


async def handler(event, context):
    # user defined log statements using synthetics_logger
    logger.info('Selenium Python workflow canary')
    return await main()
