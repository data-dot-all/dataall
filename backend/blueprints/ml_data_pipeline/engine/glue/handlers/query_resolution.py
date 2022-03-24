from jinja2 import Template


def resolve_query(handler, prefix, config):
    if handler.props.get("sql"):
        handler.logger.info("{prefix} READING INLINE SQL")
        query = handler.props.get("sql")

    else:
        handler.logger.info("{prefix} READING SQL FILE")
        query = config.get_query(handler.props.get("file"))

    handler.logger.info("{prefix} RESOLVING TEMPLATE")

    rendering_vars = config.variables

    template = Template(query)
    processed = template.render(rendering_vars)
    return processed
