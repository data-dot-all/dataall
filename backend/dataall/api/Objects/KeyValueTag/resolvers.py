from .... import db
from ..Stack import stack_helper
from ...context import Context


def list_key_value_tags(
    context: Context, source, targetUri: str = None, targetType: str = None
):
    with context.engine.scoped_session() as session:
        return db.api.KeyValueTag.list_key_value_tags(
            session=session,
            uri=targetUri,
            target_type=targetType,
        )


def update_key_value_tags(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        kv_tags = db.api.KeyValueTag.update_key_value_tags(
            session=session,
            uri=input['targetUri'],
            data=input,
        )
        stack_helper.deploy_stack(targetUri=input['targetUri'])
        return kv_tags
