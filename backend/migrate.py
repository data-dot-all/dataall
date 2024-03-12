import os
from bisect import insort
from collections import defaultdict
from dataclasses import dataclass
from operator import attrgetter
from pathlib import Path
from typing import Dict, List

from dataall.base.api import bootstrap
from dataall.base.api.gql import Field
from dataall.base.loader import load_modules, ImportMode

PATCH_FILENAME = 'full.patch'


def generate_import_hunk(filename):
    return '''--- a/{filename}
+++ b/{filename}
@@ -0,0 +1 @@
+from dataall.base.api import appSyncResolver
'''.format(filename=filename)


def generate_decorator_hunk(typename, fieldname, oldline, newline):
    return '''@@ -{oldline},0 +{newline} @@
+@appSyncResolver.resolver(type_name='{typename}', field_name='{fieldname}')
'''.format(
        oldline=oldline,
        newline=newline,
        typename=typename,
        fieldname=fieldname,
    )


@dataclass
class HunkData:
    typename: str
    fieldname: str
    lineno: int


hunks: Dict[str, List[HunkData]] = defaultdict(list)


def refactor(typename, field: Field):
    if field.resolver:
        lineno = field.resolver.__code__.co_firstlineno  # 44
        filename = field.resolver.__code__.co_filename  # '/home/ANT.AMAZON.COM/kalosp/projects/dataall/backend/dataall/core/organizations/api/resolvers.py'
        rfilename = os.path.relpath(filename, Path.home().joinpath('projects', 'dataall'))
        if any(map(field.resolver.__code__.co_name.__contains__, ['lambda', 'decorated'])):
            print(f'FIX MANUALLY {typename}.{field.name} : ({filename}:{lineno})')
            return
        hunk = HunkData(typename, field.name, lineno)
        if hunk not in hunks[rfilename]:
            insort(hunks[rfilename], hunk, key=attrgetter('lineno'))


def write_patch():
    with open(PATCH_FILENAME, 'w') as patch_file:
        for rfilename, all_hunks in hunks.items():
            patch_file.write(generate_import_hunk(rfilename))
            for i, hunk in enumerate(all_hunks):
                patch_file.write(generate_decorator_hunk(hunk.typename, hunk.fieldname, hunk.lineno, hunk.lineno + 1 + i))
            patch_file.write('\n')
            print(rfilename)


load_modules(modes={ImportMode.API})
schema = bootstrap()

for _type in schema.types:
    for field in _type.fields:
        if field.resolver:
            refactor(_type.name, field)
write_patch()
