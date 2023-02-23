import random
import typing
import json
import pytest
from ariadne import graphql_sync
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify, Response
from munch import DefaultMunch
import dataall
from dataall.core.context import set_context, RequestContext


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


@pytest.fixture(scope='module', autouse=True)
def app(db, es):
    app = Flask('tests')
    schema = dataall.api.get_executable_schema()

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
        groups = json.loads(request.headers.get('Groups', '[]'))

        set_context(RequestContext(db, username, groups, es))

        success, result = graphql_sync(
            schema,
            data,
            context_value={
                'schema': None,
                'engine': db,
                'username': username,
                'groups': groups,
                'es': es,
            },
            debug=app.debug,
        )

        status_code = 200 if success else 400
        return jsonify(result), status_code

    yield app


@pytest.fixture(scope='module')
def client(app) -> ClientWrapper:
    with app.test_client() as client:
        yield ClientWrapper(client)


def deprecated(fn):
    def wrapper(*args, **kwargs):
        print(fn.__name__, 'is deprecated')

    return wrapper


def random_email():
    names = ['andy', 'bill', 'satya', 'sundar']
    corps = ['google.com', 'amazon.com', 'microsoft.com']
    return f'{random.choice(names)}@{random.choice(corps)}'


def random_emails():
    emails = []
    for i in range(1, 2 + random.choice([2, 3, 4])):
        emails.append(random_email())
    return emails


def random_group():
    prefixes = ['big', 'small', 'pretty', 'shiny']
    names = ['team', 'people', 'group']
    lands = ['snow', 'ice', 'green', 'high']
    return f'{random.choice(prefixes).capitalize()}{random.choice(names).capitalize()}From{random.choice(lands).capitalize()}land'


def random_tag():
    return random.choice(
        ['sales', 'finances', 'sites', 'people', 'products', 'partners', 'operations']
    )


def random_tags():
    return [random_tag() for i in range(1, random.choice([2, 3, 4, 5]))]
