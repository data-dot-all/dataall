import enum
import json
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Query

log = logging.getLogger(__name__)


def json_decoder(x):
    if isinstance(x, datetime):
        return x.isoformat()
    if isinstance(x, date):
        return str(x)
    if isinstance(x, enum.Enum):
        return x.name
    if isinstance(x, Decimal):
        return str(x)
    if isinstance(x, timedelta):
        return str(x)
    if hasattr(x, '__table__'):
        return to_json(x)
    if isinstance(x, bytes):
        return str(x)
    if isinstance(x, bytearray):
        return str(x)
    return x


def to_json(record):
    if isinstance(record, type(None)):
        return json.dumps(None)
    if isinstance(record, type(['a', 'list'])):
        return [to_json(r) for r in record]
    elif isinstance(record, type({'a': 'dict'})):
        return json.loads(json.dumps(record, default=json_decoder))
    elif type(record) in [str, 'unicode']:
        return json.dumps(record)
    elif type(record) in [int, float]:
        return json.dumps(record)
    elif isinstance(record, bool):
        return json.dumps(record)
    elif isinstance(record, datetime):
        return json_decoder(record)
    elif isinstance(record, date):
        return json_decoder(record)
    elif isinstance(record, Decimal):
        return json_decoder(record)
    elif '_fields' in dir(record):
        d = {attr: getattr(record, attr) for attr in record._fields}
        return json.loads(json.dumps(d, default=json_decoder))
    elif isinstance(record, Query):
        startquery = datetime.now()
        items = record.all()
        log.debug(
            '[SQL] %s ... | %s',
            str(record).replace('\n', ' ')[0:25],
            (datetime.now() - startquery).total_seconds(),
        )
        return to_json(items)
    elif type(record) in [bytes, bytearray]:
        return json_decoder(record)
    else:
        return json.loads(json.dumps(record.to_dict(), default=json_decoder))


def to_string(record):
    return json.dumps(record, default=json_decoder)


def dict_compare(new_dict, old_dict):
    d1_keys = set(new_dict.keys())
    d2_keys = set(old_dict.keys())
    shared_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {o: (new_dict[o], old_dict[o]) for o in shared_keys if new_dict[o] != old_dict[o]}
    same = set(o for o in shared_keys if new_dict[o] == old_dict[o])
    return added, removed, modified, same
