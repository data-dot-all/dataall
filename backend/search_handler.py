import json
import os

from dataall.base.searchproxy import connect, run_query

ENVNAME = os.getenv('envname', 'local')
es = connect(envname=ENVNAME)


def handler(event, context):
    print('Received event')
    print(event)
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'content-type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*',
            },
        }
    elif event['httpMethod'] == 'POST':
        # If maintenance mode is enabled -> Check Status by using the graphQL Endpoint
        # If groups doesn't contain data.all administrator group
        # Check what is the access mode
        # Return response with error "Maintenance Window is ON"

        body = event.get('body')
        print(body)
        success = True
        try:
            response = run_query(es, 'dataall-index', body)
        except Exception:
            success = False
            response = {}
        return {
            'statusCode': 200 if success else 400,
            'headers': {
                'content-type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps(response),
        }
