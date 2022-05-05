from ....api.context import Context
from ....db import models, paginate


def list_user_activities(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    print('filter = ', filter)
    with context.engine.scoped_session() as session:
        q = (
            session.query(models.Activity)
            .filter(models.Activity.owner == context.username)
            .order_by(models.Activity.created.desc())
        )
    return paginate(
        q, page=filter.get('page', 1), page_size=filter.get('pageSize', 10)
    ).to_dict()
