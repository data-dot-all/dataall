from datetime import datetime

import nanoid

from dataall.base.utils.slugify import slugify


def uuid(resource_type='undefined', parent_field=''):
    def get_id(context):
        letters = ''.join([chr(i).lower() for i in range(65, 65 + 26)])
        letters += '1234567890'
        identifier = nanoid.generate(letters, 8)
        return identifier

    return get_id


def now():
    return datetime.now().isoformat()


def slugifier(field):
    def slugit(context):
        return slugify(context.get_current_parameters().get(field, 'Untitled'))

    return slugit
