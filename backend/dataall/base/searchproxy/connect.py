import os
from urllib.parse import urlparse

import boto3
import opensearchpy
from requests_aws4auth import AWS4Auth

from dataall.base import utils

CREATE_INDEX_REQUEST_BODY = {
    'mappings': {
        'properties': {
            '_indexed': {'type': 'date'},
            'admins': {
                'type': 'text',
                'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}},
            },
            'created': {'type': 'date'},
            'resourceKind': {'type': 'text', 'fielddata': True},
            'datasetUri': {
                'type': 'text',
                'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}},
            },
            'deleted': {'type': 'date'},
            'description': {'type': 'text'},
            'environmentName': {'type': 'text', 'fielddata': True},
            'environmentUri': {'type': 'text'},
            'label': {'type': 'text'},
            'name': {'type': 'text'},
            'organizationName': {'type': 'text', 'fielddata': True},
            'organizationUri': {'type': 'text'},
            'owner': {'type': 'text'},
            'region': {'type': 'text', 'fielddata': True},
            'classification': {'type': 'text', 'fielddata': True},
            'tags': {'type': 'text', 'fielddata': True},
            'topics': {'type': 'text', 'fielddata': True},
            'updated': {'type': 'date'},
            'uri': {
                'type': 'text',
                'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}},
            },
            'glossary': {'type': 'text', 'fielddata': True},
        }
    }
}


def connect(envname='local'):
    if envname in ['local', 'pytest', 'dkrcompose']:
        return connect_dev_environment(envname)
    else:
        session = boto3.session.Session()
        creds = session.get_credentials()
        access_key = creds.access_key
        secret = creds.secret_key
        token = creds.token

        host = utils.Parameter.get_parameter(env=envname, path='elasticsearch/endpoint')
        service = utils.Parameter.get_parameter(env=envname, path='elasticsearch/service') or 'es'

        awsauth = AWS4Auth(
            access_key,
            secret,
            os.getenv('AWS_REGION', 'eu-west-1'),
            service,
            session_token=token,
        )

        es = opensearchpy.OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=opensearchpy.RequestsHttpConnection,
        )

        # Avoid calling GET /info endpoint because it is not available in OpenSearch Serverless
        if service != 'aoss':
            print(es.info())

        if not es.indices.exists(index='dataall-index'):
            es.indices.create(index='dataall-index', body=CREATE_INDEX_REQUEST_BODY)
            print('Create "dataall-index" for dev env')
        return es


def connect_dev_environment(envname):
    hostname = 'elasticsearch' if envname == 'dkrcompose' else 'localhost'
    try:
        url = urlparse(f'http://{hostname}:9200')
        es = opensearchpy.OpenSearch(
            hostname,
            verify_certs=False,
            http_auth=('admin', 'admin'),
            scheme=url.scheme,
            port='9200',
        )
        if not es.indices.exists(index='dataall-index'):
            es.indices.create(index='dataall-index', body=CREATE_INDEX_REQUEST_BODY)
        print('Connected to ES', es.info())
        return es
    except Exception as e:
        print('Waiting for ES to start locally')
        raise e


def get_mappings_indice(es, es_index='dataall-index'):
    mappings = es.indices.get_mapping(index=es_index)
    return mappings.get(es_index)


def get_mappings_properties_indice(es, es_index='dataall-index'):
    mappings = get_mappings_indice(es, es_index)
    return mappings.get('mappings').get('properties').keys()


def add_keyword_mapping(es, new_key, es_index='dataall-index'):
    new_mapping_body = {'properties': {new_key: {'type': 'keyword'}}}
    es.indices.put_mapping(index=es_index, body=new_mapping_body)
