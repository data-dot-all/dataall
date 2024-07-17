import math

__version__ = '0.0.2'


class Page(object):
    def __init__(self, items, page, page_size, total):
        self.page_size = page_size
        self.page = page
        self.items = items
        self.previous_page = None
        self.next_page = None
        self.has_previous = page > 1
        if self.has_previous:
            self.previous_page = page - 1
        previous_items = (page - 1) * page_size
        self.has_next = previous_items + len(items) < total
        if self.has_next:
            self.next_page = page + 1
        self.total = total
        self.pages = int(math.ceil(total / float(page_size)))

    def to_dict(self):
        return {
            'count': self.total,
            'pages': self.pages,
            'page': self.page,
            'pageSize': self.page_size,
            'nodes': self.items,
            'hasNext': self.has_next,
            'hasPrevious': self.has_previous,
            'nextPage': self.next_page,
            'previousPage': self.previous_page,
        }


def paginate(query, page, page_size):
    if page <= 0:
        raise AttributeError('page needs to be >= 1')
    if page_size <= 0:
        raise AttributeError('page_size needs to be >= 1')
    items = query.limit(page_size).offset((page - 1) * page_size).all()
    # count doesn't de-duplicate the rows as described here https://tinyurl.com/3f7d8d5a
    # nosemgrep: python.sqlalchemy.performance.performance-improvements.len-all-count
    total = len(query.order_by(None).all())
    return Page(items, page, page_size, total)


def paginate_list(items, page, page_size):
    if page <= 0:
        raise AttributeError('page needs to be >= 1')
    if page_size <= 0:
        raise AttributeError('page_size needs to be >= 1')
    start = (page - 1) * page_size
    end = start + page_size
    total = len(items)
    return Page(items[start:end], page, page_size, total)
