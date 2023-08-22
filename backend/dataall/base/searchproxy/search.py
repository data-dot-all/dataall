import os

import json
from .connect import connect


def run_query(es, index, body):
    if not es:
        print('ES connection is null creating it...')
        es = connect(envname=os.getenv('envname', 'local'))
        if not es:
            raise Exception('Failed to create ES connection')
    search_object = json.loads(body.split('\n')[1])
    res = es.search(index=index, body=search_object)
    return res
