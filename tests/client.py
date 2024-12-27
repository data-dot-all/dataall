import json
import typing

from ariadne import graphql_sync
from ariadne.constants import PLAYGROUND_HTML
from fastapi import FastAPI
from munch import DefaultMunch
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse

from dataall.base.api import get_executable_schema
from dataall.base.config import config
from dataall.base.context import set_context, dispose_context, RequestContext

config.set_property('cdk_proxy_url', 'mock_url')


class ClientWrapper:
    def __init__(self, cli):
        self.client = cli

    def query(
        self,
        query: str,
        username: str = 'test',
        groups: typing.List[str] = ['-'],
        **variables,
    ):
        if not isinstance(username, str):
            username = username.username
        response = self.client.post(
            '/graphql',
            json={'query': f""" {query} """, 'variables': variables},
            headers={'groups': json.dumps(groups), 'username': username},
        )
        return DefaultMunch.fromDict(json.loads(response.text))


def create_app(db):
    app = FastAPI(debug=True)
    schema = get_executable_schema()

    @app.options('/')
    def opt():
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

    @app.post('/graphql')
    async def graphql_server(request: Request):
        # GraphQL queries are always sent as POST
        # Note: Passing the request to the context is optional.
        data = await request.json()

        username = request.headers.get('Username', 'anonym')
        user_id = request.headers.get('Username', 'anonym_id')
        groups = json.loads(request.headers.get('Groups', '[]'))

        set_context(RequestContext(db, username, groups, user_id))

        success, result = graphql_sync(
            schema,
            data,
            context_value={'schema': None, 'engine': db, 'username': username, 'groups': groups, 'user_id': user_id},
            debug=app.debug,
        )

        dispose_context()
        status_code = 200 if success else 400
        return JSONResponse(result, status_code)

    return app
