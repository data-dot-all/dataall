import logging
import os

import jwt
from ariadne import graphql_sync
from ariadne.constants import PLAYGROUND_HTML
from fastapi import FastAPI, Request
from graphql import parse
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, HTMLResponse

from dataall.base.api import get_executable_schema
from dataall.base.config import config
from dataall.base.context import set_context, dispose_context, RequestContext
from dataall.base.db import get_engine, Base
from dataall.base.loader import load_modules, ImportMode
from dataall.base.searchproxy import connect, run_query
from dataall.core.permissions.services.tenant_permissions import TENANT_ALL
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.tasks.service_handlers import Worker

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
load_modules(modes={ImportMode.API, ImportMode.HANDLERS, ImportMode.SHARES_TASK, ImportMode.CATALOG_INDEXER_TASK})
Base.metadata.create_all(engine.engine)
CDKPROXY_URL = 'http://cdkproxy:2805' if ENVNAME == 'dkrcompose' else 'http://localhost:2805'
config.set_property('cdk_proxy_url', CDKPROXY_URL)

TenantPolicyService.save_permissions_with_tenant(engine)


class Context:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


schema = get_executable_schema()
app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def request_context(headers, mock=False):
    if mock:
        username = headers.get('username', 'anonymous@amazon.com')
        groups = headers.get('groups', ['Scientists', 'DAAdministrators', 'Engineers', 'Other'])
    else:
        if not headers.get('Authorization'):
            raise Exception('Missing Authorization header')
        try:
            decoded = jwt.decode(headers.get('Authorization'), options={'verify_signature': False})
            username = decoded.get('email', 'anonymous')
            groups = []
            saml_groups = decoded.get('custom:saml.groups', [])
            if len(saml_groups):
                groups: list = saml_groups.replace('[', '').replace(']', '').replace(', ', ',').split(',')
            cognito_groups = decoded.get('cognito:groups', [])
            groups.extend(cognito_groups)
        except Exception as e:
            logger.error(str(e))
            raise e

    for group in groups:
        with engine.scoped_session() as session:
            TenantPolicyService.attach_group_tenant_policy(
                session=session,
                group=group,
                permissions=TENANT_ALL,
                tenant_name=TenantPolicyService.TENANT_NAME,
            )

    set_context(RequestContext(db_engine=engine, username=username, groups=groups, user_id=username))

    # TODO: remove when the migration to a new RequestContext API is complete. Used only for backward compatibility
    context = Context(engine=engine, schema=schema, username=username, groups=groups, user_id=username)
    return context.__dict__


@app.options('/graphql')
def opt():
    # On GET request serve GraphQL Playground
    # You don't need to provide Playground if you don't want to
    # but keep on mind this will not prohibit clients from
    # exploring your API using desktop GraphQL Playground app.
    return HTMLResponse('<html><body><h1>Hello</h1></body></html>')


@app.options('/esproxy')
def esproxyopt():
    # On GET request serve GraphQL Playground
    # You don't need to provide Playground if you don't want to
    # but keep on mind this will not prohibit clients from
    # exploring your API using desktop GraphQL Playground app.
    return HTMLResponse('<html><body><h1>Hello</h1></body></html>')


@app.get('/graphql')
def graphql_playground():
    # On GET request serve GraphQL Playground
    # You don't need to provide Playground if you don't want to
    # but keep on mind this will not prohibit clients from
    # exploring your API using desktop GraphQL Playground app.
    return HTMLResponse(PLAYGROUND_HTML)


@app.post('/esproxy')
async def esproxy(request: Request):
    body = (await request.body()).decode('utf-8')
    logger.info('body %s', body)
    return run_query(es=es, index='dataall-index', body=body)


@app.post('/graphql')
async def graphql_server(request: Request):
    logger.info('.............................')
    data = await request.json()
    logger.info('Request payload %s', data)

    # Extract the GraphQL query string from the 'query' key in the data dictionary
    query_string = data.get('query')

    if not query_string:
        return JSONResponse({'error': 'GraphQL query not provided'}, 400)
    try:
        query = parse(query_string)
    except Exception as e:
        return JSONResponse({'error': str(e)}, 400)

    logger.info('Request query %s', query.to_dict())

    context = request_context(request.headers, mock=True)
    logger.debug(context)

    success, result = graphql_sync(
        schema,
        data,
        context_value=context,
        debug=app.debug,
    )

    dispose_context()
    status_code = 200 if success else 400
    return JSONResponse(result, status_code)
