import typing
import json
from ariadne import graphql_sync
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify, Response
from munch import DefaultMunch
from dataall.base.api import get_executable_schema
from dataall.base.context import set_context, dispose_context, RequestContext
from dataall.base.config import config

config.set_property("cdk_proxy_url", "mock_url")


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
        response: Response = self.client.post(
            '/graphql',
            json={'query': f""" {query} """, 'variables': variables},
            headers={'groups': json.dumps(groups), 'username': username},
        )
        return DefaultMunch.fromDict(response.get_json())


def create_app(db):
    app = Flask('tests')
    schema = get_executable_schema()

    @app.route('/', methods=['OPTIONS'])
    def opt():
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

    @app.route('/graphql', methods=['POST'])
    def graphql_server():
        # GraphQL queries are always sent as POST
        # Note: Passing the request to the context is optional.
        # In Flask, the current request is always accessible as flask.request
        data = request.get_json()

        username = request.headers.get('Username', 'anonym')
        user_id = request.headers.get('Username', 'anonym_id')
        groups = json.loads(request.headers.get('Groups', '[]'))

        set_context(RequestContext(db, username, groups, user_id))

        success, result = graphql_sync(
            schema,
            data,
            context_value={
                'schema': None,
                'engine': db,
                'username': username,
                'groups': groups,
                'user_id': user_id
            },
            debug=app.debug,
        )

        dispose_context()
        status_code = 200 if success else 400
        return jsonify(result), status_code

    return app
