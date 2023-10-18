import os

import boto3
import jwt
from ariadne import graphql_sync
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify
from flask_cors import CORS

from dataall.base.api import get_executable_schema
from dataall.core.tasks.service_handlers import Worker
from dataall.core.permissions import permissions
from dataall.core.permissions.db import save_permissions_with_tenant
from dataall.core.permissions.db.tenant_policy_repositories import TenantPolicy
from dataall.base.db import get_engine, Base
from dataall.base.searchproxy import connect, run_query
from dataall.base.loader import load_modules, ImportMode
from dataall.base.config import config
from dataall.base.context import set_context, dispose_context, RequestContext

import logging

logger = logging.getLogger('graphql')
logger.propagate = False
logger.setLevel(logging.INFO)

Worker.queue = Worker.process
ENVNAME = os.getenv('envname', 'local')
logger.warning(f'Connecting to database `{ENVNAME}`')
engine = get_engine(envname=ENVNAME)
es = connect(envname=ENVNAME)
logger.info('Connected')
# create_schema_and_tables(engine, envname=ENVNAME)
load_modules(modes={ImportMode.API, ImportMode.HANDLERS})
Base.metadata.create_all(engine.engine)
CDKPROXY_URL = (
    'http://cdkproxy:2805' if ENVNAME == 'dkrcompose' else 'http://localhost:2805'
)
config.set_property("cdk_proxy_url", CDKPROXY_URL)

save_permissions_with_tenant(engine)


class Context:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


schema = get_executable_schema()
# app = GraphQL(schema, debug=True)

app = Flask(__name__)
CORS(app)


def request_context(headers, mock=False):
    if mock:
        username = headers.get('username', 'anonymous@amazon.com')
        groups = headers.get('groups', ['Scientists', 'DAAdministrators', 'Engineers', 'Other'])
    else:
        if not headers.get('Authorization'):
            raise Exception('Missing Authorization header')
        try:
            decoded = jwt.decode(headers.get('Authorization'), options={"verify_signature": False})
            username = decoded.get('email', 'anonymous')
            groups = []
            saml_groups = decoded.get('custom:saml.groups', [])
            if len(saml_groups):
                groups: list = (
                    saml_groups.replace('[', '')
                    .replace(']', '')
                    .replace(', ', ',')
                    .split(',')
                )
            cognito_groups = decoded.get('cognito:groups', [])
            groups.extend(cognito_groups)
        except Exception as e:
            logger.error(str(e))
            raise e

    for group in groups:
        with engine.scoped_session() as session:
            TenantPolicy.attach_group_tenant_policy(
                session=session,
                group=group,
                permissions=permissions.TENANT_ALL,
                tenant_name='dataall',
            )

    set_context(RequestContext(engine, username, groups))

    # TODO: remove when the migration to a new RequestContext API is complete. Used only for backward compatibility
    context = Context(
        engine=engine,
        schema=schema,
        username=username,
        groups=groups,
    )
    return context.__dict__


@app.route('/graphql', methods=['OPTIONS'])
def opt():
    # On GET request serve GraphQL Playground
    # You don't need to provide Playground if you don't want to
    # but keep on mind this will not prohibit clients from
    # exploring your API using desktop GraphQL Playground app.
    return '<html><body><h1>Hello</h1></body></html>', 200


@app.route('/esproxy', methods=['OPTIONS'])
def esproxyopt():
    # On GET request serve GraphQL Playground
    # You don't need to provide Playground if you don't want to
    # but keep on mind this will not prohibit clients from
    # exploring your API using desktop GraphQL Playground app.
    return '<html><body><h1>Hello</h1></body></html>', 200


@app.route('/graphql', methods=['GET'])
def graphql_playground():
    # On GET request serve GraphQL Playground
    # You don't need to provide Playground if you don't want to
    # but keep on mind this will not prohibit clients from
    # exploring your API using desktop GraphQL Playground app.
    return PLAYGROUND_HTML, 200


@app.route('/esproxy', methods=['POST'])
def esproxy():
    body = request.data.decode('utf-8')
    print(body)
    return run_query(es=es, index='dataall-index', body=body)


@app.route('/graphql', methods=['POST'])
def graphql_server():
    print('.............................')
    # GraphQL queries are always sent as POST
    logger.debug(request.data)
    data = request.get_json()
    print('*** Request ***', request.data)

    context = request_context(request.headers, mock=True)
    logger.debug(context)

    # Note: Passing the request to the context is optional.
    # In Flask, the current request is always accessible as flask.request
    success, result = graphql_sync(
        schema,
        data,
        context_value=context,
        debug=app.debug,
    )

    dispose_context()
    status_code = 200 if success else 400
    return jsonify(result), status_code


if __name__ == '__main__':
    logger.info('Starting dataall flask local application')
    app.run(
        debug=True,  # nosec
        threaded=False,
        host='0.0.0.0',
        port=5000,
    )
